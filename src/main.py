import os
import sqlite3

import discord

import lolpark
import channels
import managers
from discord.ext import commands
from normal_game import make_normal_game, close_normal_game, end_normal_game
from summoner import Summoner
from database import (add_summoner, add_normal_game_win_count,
                      add_normal_game_lose_count, create_table, get_summoner_record_message,
                      record_normal_game)
from bot import bot

# GitHub Secrets에서 가져오는 값
TOKEN = os.getenv('DISCORD_TOKEN')


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')


@bot.command(name='내전')
async def make_game(ctx, *, message='모이면 바로 시작'):
    # await ctx.send("현재 수습 마술사 작업중 입니다. 수동으로 내전 진행해주시면 감사하겠습니다.")
    # return None

    channel_id = ctx.channel.id
    normal_channel_id_list = [channels.GAME_A_RECRUIT_CHANNEL_ID, channels.GAME_B_RECRUIT_CHANNEL_ID,
                              channels.GAME_C_RECRUIT_CHANNEL_ID, channels.GAME_D_RECRUIT_CHANNEL_ID]

    if channel_id in normal_channel_id_list and not lolpark.is_normal_game:
        lolpark.is_normal_game = await make_normal_game(ctx, message)


@bot.command(name='마감')
async def close_game(ctx):
    channel_id = ctx.channel.id


@bot.command(name='쫑')
async def end_game(ctx):
    channel_id = ctx.channel.id
    normal_channel_id_list = [channels.GAME_A_RECRUIT_CHANNEL_ID, channels.GAME_B_RECRUIT_CHANNEL_ID,
                              channels.GAME_C_RECRUIT_CHANNEL_ID, channels.GAME_D_RECRUIT_CHANNEL_ID]

    if channel_id in normal_channel_id_list and lolpark.is_normal_game:
        lolpark.normal_game_log = None
        lolpark.normal_game_channel = None
        lolpark.is_normal_game = await end_normal_game(ctx)


# 메세지 입력 시 마다 수행
@bot.event
async def on_message(message):
    channel_id = message.channel.id

    # 봇 메세지는 메세지로 인식 X
    if message.author == bot.user:
        return

    # 내전이 열려 있을 경우, 손 든 사람 모집
    if lolpark.is_normal_game and channel_id == lolpark.normal_game_channel:
        user = Summoner(message.author)
        if user in lolpark.normal_game_log:
            lolpark.normal_game_log[user].append(message.id)
        else:
            lolpark.normal_game_log[user] = [message.id]
            print(user.nickname)
        # 참여자 수가 10명이면 내전 자동 마감
        if len(lolpark.normal_game_log) == 10:
            await close_normal_game(message.channel, list(lolpark.normal_game_log.keys()), lolpark.normal_game_creator)

            # 내전 변수 초기화, 명단 확정 후에 진행
            lolpark.normal_game_log = None
            lolpark.normal_game_channel = None
            lolpark.normal_game_creator = None
            lolpark.is_normal_game = False

    await bot.process_commands(message)


# 메세지 삭제 시 마다 수행
@bot.event
async def on_message_delete(message):
    channel_id = message.channel.id
    user = Summoner(message.author)

    # 내전 모집에서 채팅 지우면 로그에서 삭제
    if lolpark.is_normal_game and channel_id == lolpark.normal_game_channel:
        lolpark.normal_game_log[user] = [mid for mid in lolpark.normal_game_log[user] if mid != message.id]
        # 만약 채팅이 더 남아 있지 않으면 로그에서 유저 삭제
        if not lolpark.normal_game_log[user]:
            del lolpark.normal_game_log[user]


@bot.command(name='비상탈출')
@commands.is_owner()
async def shutdown(ctx):
    # 디스코드에서 봇 종료를 위한 명령어
    await ctx.send("봇을 강제로 종료합니다")
    await bot.close()


@bot.command(name='경매')
async def twenty_auction(ctx):
    return None


@bot.command(name='수동경매')
async def twenty_auction_by_own(ctx):
    return None


@bot.command(name='테스트')
async def test_only_def(ctx):
    # create_table()
    return None


@bot.command(name='테스트종료')
async def test_end_def(ctx):
    return None


@bot.command(name='승리')
async def update_win_count(ctx, member: discord.Member):
    summoner = Summoner(member)
    if ctx.channel.id == channels.RECORD_UPDATE_SERVER_ID:
        await add_normal_game_win_count(summoner)


@bot.command(name='패배')
async def update_lose_count(ctx, member: discord.Member):
    summoner = Summoner(member)
    if ctx.channel.id == channels.RECORD_UPDATE_SERVER_ID:
        await add_normal_game_lose_count(summoner)


@bot.command(name='전적')
async def show_summoner_record(ctx, member: discord.Member = None):
    channel_id = ctx.channel.id
    # 멘션이 없으면 자기 자신의 정보로 설정, 있으면 멘션된 사용자로 설정
    if member is None:
        summoner = Summoner(ctx.author)
    else:
        summoner = Summoner(member)

    if channel_id == channels.RECORD_SERVER_ID:
        record_message = await get_summoner_record_message(summoner)
        await ctx.send(record_message)


@bot.command(name='기록')
async def record_normal_game(ctx):
    channel_id = ctx.channel.id

    if channel_id != channels.RECORD_UPDATE_SERVER_ID:
        return None

    if lolpark.finalized_normal_game_team_list is None:
        await ctx.send('모집된 내전이 없습니다.')
        return None

    teams = lolpark.finalized_normal_game_team_list[0]

    class RecordUpdateView(discord.ui.View):
        def __init__(self, ctx, teams):
            super().__init__(timeout=3600)
            self.ctx = ctx
            self.teams = teams
            self.blue_win_count = 0
            self.red_win_count = 0

        @discord.ui.button(label='블루팀 승리 : 0', style=discord.ButtonStyle.primary)
        async def blue_win_button(self, button: discord.ui.Button, interaction: discord.Interaction):
            self.blue_win_count += 1
            button.label = f"블루팀 승리: {self.blue_win_count}"
            await interaction.response.edit_message(view=self)

        @discord.ui.button(label='레드팀 승리 : 0', style=discord.ButtonStyle.red)
        async def red_win_button(self, button: discord.ui.Button, interaction: discord.Interaction):
            self.red_win_count += 1
            button.label = f"레드팀 승리: {self.red_win_count}"
            await interaction.response.edit_message(view=self)

        @discord.ui.button(label='이대로 확정', style=discord.ButtonStyle.green)
        async def finalize_button(self, button: discord.ui.Button, interaction: discord.Interaction):
            await record_normal_game(self.teams, self.blue_win_count, self.red_win_count)
            await interaction.message.delete()
            await self.ctx.send(f'내전 승/패가 기록되었습니다.')

        @discord.ui.button(label='초기화', style=discord.ButtonStyle.gray)
        async def reset_button(self, button: discord.ui.Button, interaction: discord.Interaction):
            # 승리 횟수 초기화
            self.blue_win_count = 0
            self.red_win_count = 0

            # 각 버튼 라벨 초기화
            for child in self.children:
                if isinstance(child, discord.ui.Button):
                    if '블루팀' in child.label:
                        child.label = '블루팀 승리 : 0'
                    elif '레드팀' in child.label:
                        child.label = '레드팀 승리 : 0'

            # 메시지 업데이트
            await interaction.response.edit_message(view=self)

    view = RecordUpdateView(ctx=ctx, teams=teams)
    await ctx.send(content='승패기록하기', view=view)

    lolpark.finalized_normal_game_team_list.pop(0)
    if not lolpark.finalized_normal_game_team_list:
        lolpark.finalized_normal_game_team_list = None


@bot.command(name='초기화')
async def reset_game(ctx):
    channel_id = ctx.channel.id
    user_id = ctx.author.id

    normal_channel_id_list = [channels.GAME_A_RECRUIT_CHANNEL_ID, channels.GAME_B_RECRUIT_CHANNEL_ID,
                              channels.GAME_C_RECRUIT_CHANNEL_ID, channels.GAME_D_RECRUIT_CHANNEL_ID]

    if user_id != managers.MASULSA:
        await ctx.send('개발자만 가능해요~ 안돼요~ 돌아가요~')
        return None

    if channel_id in normal_channel_id_list:
        lolpark.is_normal_game = False
        lolpark.normal_game_log = None
        lolpark.normal_game_channel = None
        await ctx.send("일반 내전을 초기화했습니다.")


def main() -> None:
    # create_table()
    bot.run(token=TOKEN)


if __name__ == '__main__':
    main()
