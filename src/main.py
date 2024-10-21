import os
import discord
from dotenv import load_dotenv

import lolpark
import database
from discord.ext import commands
from normal_game import close_normal_game
from summoner import Summoner
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
    bot.loop.create_task(main_functions.recommend_discord())


@bot.command(name='내전')
async def command_start(ctx, *, message='모이면 바로 시작'):
    await main_functions.make_game(ctx, message)


@bot.command(name='마감')
async def command_finalize(ctx, *, message='모이면 바로 시작'):
    await main_functions.finalize_game(ctx)


@bot.command(name='쫑')
async def command_end(ctx):
    await main_functions.end_game(ctx)


# 메세지 입력 시 마다 수행
@bot.event
async def on_message(message):

    # 봇 메세지는 메세지로 인식 X
    if message.author == bot.user:
        return

    await main_functions.recruit_game_members(message)

    await bot.process_commands(message)


# 메세지 삭제 시 마다 수행
@bot.event
async def on_message_delete(message):

    # 봇 메세지는 메세지로 인식 X
    if message.author == bot.user:
        return

    main_functions.delete_member_in_log(message)


@bot.command(name='비상탈출')
@commands.is_owner()
async def shutdown(ctx):
    # 디스코드에서 봇 종료를 위한 명령어
    await ctx.send("봇을 강제로 종료합니다")
    await bot.close()


@bot.command(name='경매')
async def command_auction(ctx):
    await main_functions.start_auction(ctx)


@bot.command(name='경매테스트')
async def command_auction_test(ctx):
    await main_functions.start_test_auction(ctx)
    return None


@bot.command(name='전적')
async def command_record(ctx, member: discord.Member = None):
    await main_functions.show_summoner_record(ctx, member)


@bot.command(name='내전악귀')
async def command_game_ghost(ctx):
    await main_functions.show_summoner_most_normal_game(ctx)


@bot.command(name='기록')
async def command_record(ctx, *members: discord.Member):
    await record.manually_add_teams_record(ctx, members)


@bot.command(name='승리')
async def command_win_manual(ctx, *members: discord.Member):
    await record.manually_add_summoner_win(ctx, members)


@bot.command(name='패배')
async def command_lose_manual(ctx, *members: discord.Member):
    await record.manually_add_summoner_lose(ctx, members)


@bot.command(name='초기화')
async def command_reset(ctx):
    await main_functions.reset_game(ctx)


def main() -> None:
    database.create_table()
    bot.run(token=TOKEN)


if __name__ == '__main__':
    main()
