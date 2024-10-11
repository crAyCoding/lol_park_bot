import asyncio
from datetime import datetime, timedelta

import discord

import channels
import lolpark
import normal_game
import twenty_game
import database
import managers
from summoner import Summoner
from bot import bot


# '!내전' 입력 시 동작
async def make_game(ctx, message):
    # await ctx.send("현재 수습 마술사 작업중 입니다. 수동으로 내전 진행해주시면 감사하겠습니다.")
    # return None

    channel_id = ctx.channel.id
    normal_channel_id_list = [channels.GAME_A_RECRUIT_CHANNEL_ID, channels.GAME_B_RECRUIT_CHANNEL_ID,
                              channels.GAME_C_RECRUIT_CHANNEL_ID, channels.GAME_D_RECRUIT_CHANNEL_ID]

    if channel_id in normal_channel_id_list and not lolpark.is_normal_game:
        lolpark.is_normal_game = await normal_game.make_normal_game(ctx, message)

    if channel_id == channels.TWENTY_RECRUIT_CHANNEL_ID:
        await twenty_game.make_twenty_game(ctx, message)


# '!쫑' 입력 시 동작
async def end_game(ctx):
    channel_id = ctx.channel.id
    normal_channel_id_list = [channels.GAME_A_RECRUIT_CHANNEL_ID, channels.GAME_B_RECRUIT_CHANNEL_ID,
                              channels.GAME_C_RECRUIT_CHANNEL_ID, channels.GAME_D_RECRUIT_CHANNEL_ID]

    if channel_id in normal_channel_id_list and lolpark.is_normal_game:
        lolpark.normal_game_log = None
        lolpark.normal_game_channel = None
        lolpark.is_normal_game = await normal_game.end_normal_game(ctx)


# '!전적' 입력 시 동작
async def show_summoner_record(ctx, member):
    channel_id = ctx.channel.id
    # 멘션이 없으면 자기 자신의 정보로 설정, 있으면 멘션된 사용자로 설정
    if member is None:
        summoner = Summoner(ctx.author)
    else:
        summoner = Summoner(member)

    if channel_id == channels.RECORD_SERVER_ID:
        record_message = await database.get_summoner_record_message(summoner)
        await ctx.send(record_message)


# '!초기화' 입력 시 동작
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


# '!내전악귀' 입력 시 동작
async def show_summoner_most_normal_game(ctx):
    channel_id = ctx.channel.id

    if channel_id == channels.RECORD_SERVER_ID:
        most_normal_game_message = await database.get_summoner_most_normal_game_message()
        await ctx.send(most_normal_game_message)


# 특정 시간에 함수를 실행하는 Task
async def recommend_discord():
    now = datetime.now()

    # 오전 8시와 오후 8시 타겟 시간 설정
    morning_time = datetime.combine(now.date(), datetime.strptime("08:00", "%H:%M").time())
    evening_time = datetime.combine(now.date(), datetime.strptime("20:00", "%H:%M").time())

    # 현재 시간이 오전 8시를 지났고 오후 8시를 안 지났다면 evening_time까지 대기, 그렇지 않으면 morning_time으로 대기
    if now > evening_time:
        # 만약 오후 8시가 지났다면 다음날 오전 8시로 설정
        morning_time += timedelta(days=1)
        evening_time += timedelta(days=1)

    if now < morning_time:
        target_time = morning_time
    else:
        target_time = evening_time

    time_to_wait = (target_time - now).total_seconds()  # 초 단위로 기다릴 시간 계산
    await asyncio.sleep(time_to_wait)  # 해당 시간까지 대기

    # 인증 역할 가져오기
    role_name = '인증'
    guild = bot.get_guild(channels.LOLPARK_SERVER_ID)
    role = discord.utils.get(guild.roles, name=role_name)

    # 매일 오전 8시 혹은 오후 8시에 실행할 코드
    recommend_channel = bot.get_channel(channels.RECOMMEND_ID)
    if target_time.time() == morning_time.time():
        await recommend_channel.send(f'좋은 아침입니다! `/추천` 한번씩 부탁드립니다!!\n{role.mention}')
    else:
        await recommend_channel.send(f'저녁은 맛있게 드셨나요? 아직 안하셨다면 `/추천` 한번씩 부탁드립니다!!\n{role.mention}')

    # 다음 실행을 위해 다시 태스크 생성 (오전 8시, 오후 8시 중 가장 가까운 시간에 맞추기)
    bot.loop.create_task(recommend_discord())
