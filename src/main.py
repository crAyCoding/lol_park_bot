import os
import sqlite3

import discord

import dcpaow
import channels
import managers
from discord import Intents
from discord.ext import commands
from normal_game import make_normal_game, close_normal_game, end_normal_game
from summoner import Summoner
from database import add_summoner, add_normal_game_win_count, add_normal_game_lose_count, create_table

# GitHub Secrets에서 가져오는 값
TOKEN = os.getenv('DISCORD_TOKEN')

# 디스코드 봇 설정
intents: Intents = Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')


@bot.command(name='내전')
async def make_game(ctx, *, message='모이면 바로 시작'):
    # await ctx.send("현재 수습 마술사 작업중 입니다. 수동으로 내전 진행해주시면 감사하겠습니다.")
    # return None

    channel_id = ctx.channel.id
    normal_channel_id_list = [channels.GAME_1_RECRUIT_CHANNEL_ID, channels.GAME_2_RECRUIT_CHANNEL_ID]

    if channel_id in normal_channel_id_list and not dcpaow.is_normal_game:
        dcpaow.is_normal_game = await make_normal_game(ctx, message)


@bot.command(name='마감')
async def close_game(ctx):
    channel_id = ctx.channel.id


@bot.command(name='쫑')
async def end_game(ctx):
    channel_id = ctx.channel.id
    normal_channel_id_list = [channels.GAME_1_RECRUIT_CHANNEL_ID, channels.GAME_2_RECRUIT_CHANNEL_ID]

    if channel_id in normal_channel_id_list and dcpaow.is_normal_game:
        dcpaow.normal_game_log = None
        dcpaow.normal_game_channel = None
        dcpaow.is_normal_game = await end_normal_game(ctx)


# 메세지 입력 시 마다 수행
@bot.event
async def on_message(message):
    channel_id = message.channel.id

    # 봇 메세지는 메세지로 인식 X
    if message.author == bot.user:
        return

    # 내전이 열려 있을 경우, 손 든 사람 모집
    if dcpaow.is_normal_game and channel_id == dcpaow.normal_game_channel:
        user = Summoner(message.author)
        if user in dcpaow.normal_game_log:
            dcpaow.normal_game_log[user].append(message.id)
        else:
            dcpaow.normal_game_log[user] = [message.id]
            print(user.nickname)
        # 참여자 수가 10명이면 내전 자동 마감
        if len(dcpaow.normal_game_log) == 10:
            await close_normal_game(message.channel, list(dcpaow.normal_game_log.keys()))

            # 내전 변수 초기화, 명단 확정 후에 진행
            dcpaow.normal_game_log = None
            dcpaow.normal_game_channel = None
            dcpaow.is_normal_game = False

    await bot.process_commands(message)


# 메세지 삭제 시 마다 수행
@bot.event
async def on_message_delete(message):
    channel_id = message.channel.id
    user = Summoner(message.author)

    # 내전 모집에서 채팅 지우면 로그에서 삭제
    if dcpaow.is_normal_game and channel_id == dcpaow.normal_game_channel:
        dcpaow.normal_game_log[user] = [mid for mid in dcpaow.normal_game_log[user] if mid != message.id]
        # 만약 채팅이 더 남아 있지 않으면 로그에서 유저 삭제
        if not dcpaow.normal_game_log[user]:
            del dcpaow.normal_game_log[user]


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
    add_summoner(Summoner(ctx.author))
    return None


@bot.command(name='테스트종료')
async def test_end_def(ctx):
    return None


@bot.command(name='승리')
async def update_win_count(ctx, member: discord.Member):
    summoner = Summoner(member)
    if ctx.channel.id == channels.RECORD_UPDATE_SERVER_ID:
        await add_normal_game_win_count(bot, summoner)


@bot.command(name='패배')
async def update_lose_count(ctx, member: discord.Member):
    summoner = Summoner(member)
    if ctx.channel.id == channels.RECORD_UPDATE_SERVER_ID:
        await add_normal_game_lose_count(bot, summoner)


@bot.command(name='등록')
async def enroll_summoner_to_database(ctx, member: discord.Member):
    summoner = Summoner(member)
    manager_list = [managers.MASULSA, managers.YUUMI, managers.JUYE, managers.FERRERO]
    if ctx.channel.id == channels.SUMMONER_ENROLL_ID and ctx.author.id in manager_list:
        is_enrolled = add_summoner(summoner)
        if is_enrolled:
            await ctx.send(f'{summoner.nickname} 님이 등록되었습니다.')
        else:
            await ctx.send(f'이미 등록된 소환사입니다.')


@bot.command(name='초기화')
async def reset_game(ctx):
    channel_id = ctx.channel.id
    user_id = ctx.author.id

    normal_channel_id_list = [channels.GAME_1_RECRUIT_CHANNEL_ID, channels.GAME_2_RECRUIT_CHANNEL_ID]

    if user_id != managers.MASULSA:
        await ctx.send('개발자만 가능해요~ 안돼요~ 돌아가요~')
        return None

    if channel_id in normal_channel_id_list:
        dcpaow.is_normal_game = False
        dcpaow.normal_game_log = None
        dcpaow.normal_game_channel = None
        await ctx.send("일반 내전을 초기화했습니다.")


def main() -> None:
    create_table()
    bot.run(token=TOKEN)


if __name__ == '__main__':
    main()
