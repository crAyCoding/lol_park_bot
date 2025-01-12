import asyncio
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
import random

from PIL import Image, UnidentifiedImageError
import discord
import channels
import lolpark
import normal_game
import database
import twenty_game
import twenty_auction
import functions
from summoner import Summoner
from bot import bot


# '!내전' 입력 시 동작
async def make_game(ctx, message):
    # await ctx.send("현재 수습 마술사 작업중 입니다. 수동으로 내전 진행해주시면 감사하겠습니다.")
    # return None

    channel_id = ctx.channel.id

    if channel_id in channels.NORMAL_GAME_CHANNEL_ID_LIST and not lolpark.is_normal_game:
        lolpark.is_normal_game = await normal_game.make_normal_game(ctx, message)

    if channel_id == channels.GAME_FEARLESS_A_RECRUIT_CHANNEL_ID and lolpark.fearless_game_log is None:
        await normal_game.make_special_game(ctx, message, 'FEARLESS')
    
    if channel_id == channels.TIER_LIMITED_RECRUIT_CHANNEL_ID and lolpark.tier_limited_game_log is None:
        await normal_game.make_special_game(ctx, message, 'TIER_LIMIT')
    
    if channel_id == channels.ARAM_RECRUIT_CHANNEL_ID and lolpark.aram_game_log is None:
        await normal_game.make_special_game(ctx, message, 'ARAM')

    if channel_id == channels.TWENTY_RECRUIT_CHANNEL_ID:
        await twenty_game.make_twenty_game(ctx, message)


# '!쫑' 입력 시 동작
async def end_game(ctx):
    channel_id = ctx.channel.id

    if channel_id == lolpark.normal_game_channel and lolpark.is_normal_game:
        lolpark.is_normal_game = await normal_game.end_normal_game(ctx)

    if channel_id == channels.GAME_FEARLESS_A_RECRUIT_CHANNEL_ID and lolpark.fearless_game_log is not None:
        await normal_game.end_special_game(ctx, 'FEARLESS')

    if channel_id == channels.TIER_LIMITED_RECRUIT_CHANNEL_ID and lolpark.tier_limited_game_log is not None:
        await normal_game.end_special_game(ctx, 'TIER_LIMIT')

    if channel_id == channels.ARAM_RECRUIT_CHANNEL_ID and lolpark.aram_game_log is not None:
        await normal_game.end_special_game(ctx, 'ARAM')

    if channel_id == channels.TWENTY_RECRUIT_CHANNEL_ID:
        await twenty_game.end_twenty_game(ctx)


# '!전적', '!통산전적' 입력 시 동작
async def show_summoner_record(ctx, member, is_total=False):
    channel_id = ctx.channel.id
    # 멘션이 없으면 자기 자신의 정보로 설정, 있으면 멘션된 사용자로 설정
    if member is None:
        summoner = Summoner(ctx.author)
    else:
        summoner = Summoner(member)

    if channel_id == channels.RECORD_SERVER_ID:
        await database.add_summoner(summoner, is_total=True)
        await database.add_summoner(summoner)
        record_message = await database.get_summoner_record_message(summoner, is_total)
        await ctx.send(record_message)


# '!초기화' 입력 시 동작
async def reset_game(ctx):
    channel_id = ctx.channel.id

    if channel_id in channels.NORMAL_GAME_CHANNEL_ID_LIST:
        await normal_game.reset_normal_game(ctx)

    if channel_id == channels.GAME_FEARLESS_A_RECRUIT_CHANNEL_ID:
        await normal_game.reset_special_game(ctx, 'FEARLESS')

    if channel_id == channels.TIER_LIMITED_RECRUIT_CHANNEL_ID:
        await normal_game.reset_special_game(ctx, 'TIER_LIMIT')

    if channel_id == channels.ARAM_RECRUIT_CHANNEL_ID:
        await normal_game.reset_special_game(ctx, 'ARAM')

    if channel_id == channels.TWENTY_RECRUIT_CHANNEL_ID:
        await twenty_game.reset_twenty_game(ctx)


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
    morning_time = datetime.combine(now.date(), datetime.strptime("23:00", "%H:%M").time())
    evening_time = datetime.combine(now.date(), datetime.strptime("11:00", "%H:%M").time())

    # 현재 시간이 오전 8시를 지났고 오후 8시를 안 지났다면 evening_time까지 대기, 그렇지 않으면 morning_time으로 대기
    if now > morning_time:
        # 만약 오후 8시가 지났다면 다음날 오전 8시로 설정
        morning_time += timedelta(days=1)
        evening_time += timedelta(days=1)

    if now < evening_time:
        target_time = evening_time
    else:
        target_time = morning_time

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
        await recommend_channel.send(f'좋은 저녁입니다! `/추천` 한번씩 부탁드립니다!!\n{role.mention}')

    # 다음 실행을 위해 다시 태스크 생성 (오전 8시, 오후 8시 중 가장 가까운 시간에 맞추기)
    bot.loop.create_task(recommend_discord())


async def start_auction(ctx):
    channel_id = ctx.channel.id

    if channel_id != channels.TWENTY_AUCTION_CHANNEL_ID:
        return

    await twenty_auction.confirm_twenty_recruit(ctx)


async def start_test(ctx, members):
    return


async def finalize_game(ctx):
    await twenty_game.close_twenty_game(ctx)


async def recruit_game_members(message):
    channel_id = message.channel.id
    recognize_message_list = ['ㅅ', 't', 'T', '손']

    # 내전이 열려 있을 경우, 손 든 사람 모집
    if (lolpark.is_normal_game and channel_id == lolpark.normal_game_channel
            and message.content in recognize_message_list):
        user = Summoner(message.author)
        if user in lolpark.normal_game_log:
            lolpark.normal_game_log[user].append(message.id)
        else:
            lolpark.normal_game_log[user] = [message.id]
        # 참여자 수가 10명이면 내전 자동 마감
        if len(lolpark.normal_game_log) == 10:
            await normal_game.close_normal_game(message.channel, list(lolpark.normal_game_log.keys()),
                                                lolpark.normal_game_creator)

            # 내전 변수 초기화, 명단 확정 후에 진행
            lolpark.normal_game_log = None
            lolpark.normal_game_channel = None
            lolpark.normal_game_creator = None
            lolpark.is_normal_game = False

    # 피어리스 내전이 열려 있을 경우, 손 든 사람 모집
    if (lolpark.fearless_game_log is not None and channel_id == channels.GAME_FEARLESS_A_RECRUIT_CHANNEL_ID):
        await recruit_special_game(message, 'FEARLESS')
    
    # 티어 제한 내전이 열려 있을 경우, 손 든 사람 모집
    if (lolpark.tier_limited_game_log is not None and channel_id == channels.TIER_LIMITED_RECRUIT_CHANNEL_ID):
        await recruit_special_game(message, 'TIER_LIMIT')

    # 칼바람 내전이 열려 있을 경우, 손 든 사람 모집
    if (lolpark.aram_game_log and channel_id == channels.ARAM_RECRUIT_CHANNEL_ID):
        await recruit_special_game(message, 'ARAM')


def delete_member_in_log(message):
    channel_id = message.channel.id

    # 내전 모집에서 채팅 지우면 로그에서 삭제
    if lolpark.is_normal_game and channel_id == lolpark.normal_game_channel:
        delete_log_message(message, 'NORMAL')

    # 피어리스 내전 모집에서 채팅 지우면 로그에서 삭제
    if lolpark.fearless_game_log is not None and channel_id == channels.GAME_FEARLESS_A_RECRUIT_CHANNEL_ID:
        delete_log_message(message, 'FEARLESS')
    
    # 티어 제한 내전 모집에서 채팅 지우면 로그에서 삭제
    if lolpark.tier_limited_game_log is not None and channel_id == channels.TIER_LIMITED_RECRUIT_CHANNEL_ID:
        delete_log_message(message, 'TIER_LIMIT')

    # 칼바람 내전 모집에서 채팅 지우면 로그에서 삭제
    if lolpark.aram_game_log is not None and channel_id == channels.ARAM_RECRUIT_CHANNEL_ID:
        delete_log_message(message, 'ARAM')



async def recruit_special_game(message, game_type):
    game_log = lolpark.fearless_game_log if game_type == 'FEARLESS' \
                else lolpark.aram_game_log if game_type == 'ARAM' \
                    else lolpark.tier_limited_game_log
    game_creator = lolpark.fearless_game_creator if game_type == 'FEARLESS' \
                else lolpark.aram_game_creator if game_type == 'ARAM' \
                    else lolpark.tier_limited_game_creator
    if message.content not in ['ㅅ', 't', 'T', '손']:
        return
    user = Summoner(message.author)
    if game_type == 'TIER_LIMIT':
        if lolpark.up_and_down:
            if user.score > lolpark.tier_limit_standard_score:
                await message.delete()
                await message.channel.send(f'<@{user.id}> \n'
                                           f'## <:sad_bee:1287073499634208911> 기준에 부합하는 서버원만 참여할 수 있어요 <:sad_bee:1287073499634208911>')
                return
        else:
            if user.score < lolpark.tier_limit_standard_score:
                await message.delete()
                await message.channel.send(f'<@{user.id}> \n'
                                           f'## <:sad_bee:1287073499634208911> 기준에 부합하는 서버원만 참여할 수 있어요 <:sad_bee:1287073499634208911>')
                return

    if user in game_log:
        game_log[user].append(message.id)
    else:
        game_log[user] = [message.id]
    # 참여자 수가 10명이면 내전 자동 마감
    if len(game_log) == 10:
        await normal_game.close_normal_game(message.channel, list(game_log.keys()), game_creator)

        # 내전 변수 초기화, 명단 확정 후에 진행
        if game_type == 'FEARLESS':
            lolpark.fearless_game_log = None
            lolpark.fearless_game_creator = None
        if game_type == 'TIER_LIMIT':
            lolpark.tier_limited_game_log = None
            lolpark.tier_limited_game_creator = None
            lolpark.tier_limit_standard_score = None
            lolpark.up_and_down = None
        if game_type == 'ARAM':
            lolpark.aram_game_log = None
            lolpark.aram_game_creator = None


def delete_log_message(message, game_type):
    game_log = lolpark.normal_game_log if game_type == 'NORMAL' \
                else lolpark.fearless_game_log if game_type == 'FEARLESS' \
                else lolpark.tier_limited_game_log if game_type == 'TIER_LIMIT' \
                else lolpark.aram_game_log

    user = Summoner(message.author)
    if user not in game_log:
        return
    game_log[user] = [mid for mid in game_log[user] if mid != message.id]
    # 만약 채팅이 더 남아 있지 않으면 로그에서 유저 삭제
    if not game_log[user]:
        del game_log[user]


# !점검 입력 시 동작
async def notice_update():
    notice_channels = [channels.RECORD_SERVER_ID, channels.GAME_A_RECRUIT_CHANNEL_ID, channels.GAME_B_RECRUIT_CHANNEL_ID,
                       channels.GAME_C_RECRUIT_CHANNEL_ID, channels.GAME_D_RECRUIT_CHANNEL_ID, channels.GAME_E_RECRUIT_CHANNEL_ID,
                       channels.GAME_F_RECRUIT_CHANNEL_ID, channels.TIER_LIMITED_RECRUIT_CHANNEL_ID, channels.ARAM_RECRUIT_CHANNEL_ID,
                       channels.GAME_FEARLESS_A_RECRUIT_CHANNEL_ID]
    
    for channel in notice_channels:
        await bot.get_channel(channel).send(f'# 현재 롤파크 노예 점검 중입니다. 점검 종료 전까지 명령어 사용 시 경고가 부여될 수 있음을 알려드립니다.')


# !점검종료 입력 시 동작
async def end_update():
    try:
        notice_channels = [channels.RECORD_SERVER_ID, channels.GAME_A_RECRUIT_CHANNEL_ID, channels.GAME_B_RECRUIT_CHANNEL_ID,
                       channels.GAME_C_RECRUIT_CHANNEL_ID, channels.GAME_D_RECRUIT_CHANNEL_ID, channels.GAME_E_RECRUIT_CHANNEL_ID,
                       channels.GAME_F_RECRUIT_CHANNEL_ID, channels.TIER_LIMITED_RECRUIT_CHANNEL_ID, channels.ARAM_RECRUIT_CHANNEL_ID,
                       channels.GAME_FEARLESS_A_RECRUIT_CHANNEL_ID]
        # 최신 메시지 불러오기
        messages = []
        for channel_id in notice_channels:
            channel = bot.get_channel(channel_id)
            async for message in channel.history(limit=1):
                messages.append(message)

        if len(messages) > 1:
            last_message = messages[1]  # 명령어 메시지 이후의 메시지를 선택
            await last_message.delete()
        else:
            print("ERROR")
    except discord.Forbidden:
        print("권한없음")
    except discord.HTTPException as e:
        print("메세지 삭제 오류")


# !주사위 입력 시 동작
async def roll_dice(ctx):
    current_path = Path.cwd()

    random_number = random.randint(1, 6)

    # 주사위 에셋 경로
    file_path = f"{current_path}/assets/dice_image/dice_{random_number}.jpg"
    
    # 이미지 파일을 열어서 첨부
    file = discord.File(file_path, filename="lolpark_dice.png")

    user_name = ctx.author.display_name
    user_avatar = ctx.author.avatar.url

    embed = discord.Embed()

    embed.set_footer(text=f"{functions.get_nickname(user_name)}", icon_url=user_avatar)  # 하단에 사용자 정보 추가
    
    # Embed에 파일 첨부
    embed.set_image(url="attachment://lolpark_dice.png")

    # 파일과 Embed 전송
    await ctx.send(file=file, embed=embed)