import os
import sqlite3
from dotenv import load_dotenv
import discord

import lolpark
import channels
from discord.ext import commands
from normal_game import close_normal_game
from summoner import Summoner
import database
from bot import bot
import main_functions
import record

# 테스트 할때 아래 사용
# load_dotenv()
# GitHub Secrets에서 가져오는 값
TOKEN = os.getenv('DISCORD_TOKEN')


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')


@bot.command(name='내전')
async def command_start(ctx, *, message='3판 2선 모이면 바로 시작'):
    await main_functions.make_game(ctx, message)


@bot.command(name='쫑')
async def command_end(ctx):
    await main_functions.end_game(ctx)


# 메세지 입력 시 마다 수행
@bot.event
async def on_message(message):
    channel_id = message.channel.id

    recognize_message_list = ['ㅅ', 't', 'T', '손', '발']

    # 봇 메세지는 메세지로 인식 X
    if message.author == bot.user:
        return

    # 내전이 열려 있을 경우, 손 든 사람 모집
    if lolpark.is_normal_game and channel_id == lolpark.normal_game_channel:
        if message.content not in recognize_message_list:
            return
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

    # 봇 메세지는 메세지로 인식 X
    if message.author == bot.user:
        return

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
    database.add_summoner(Summoner(ctx.author))
    return None


@bot.command(name='테스트종료')
async def test_end_def(ctx):
    return None


@bot.command(name='전적')
async def command_record(ctx, member: discord.Member = None):
    await main_functions.show_summoner_record(ctx, member)


@bot.command(name='내전악귀')
async def show_summoner_most_normal_game(ctx):
    channel_id = ctx.channel.id

    if channel_id == channels.RECORD_SERVER_ID:
        most_normal_game_message = await database.get_summoner_most_normal_game_message()
        await ctx.send(most_normal_game_message)


@bot.command(name='기록')
async def command_record(ctx):
    await record.record_normal_game_in_main(ctx)


@bot.command(name='초기화')
async def command_reset(ctx):
    await main_functions.reset_game(ctx)


def main() -> None:
    database.create_table()
    bot.run(token=TOKEN)


if __name__ == '__main__':
    main()
