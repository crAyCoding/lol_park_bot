import channels
import lolpark
import normal_game
import database
import managers
from summoner import Summoner


async def make_game(ctx, message):
    # await ctx.send("현재 수습 마술사 작업중 입니다. 수동으로 내전 진행해주시면 감사하겠습니다.")
    # return None

    channel_id = ctx.channel.id
    normal_channel_id_list = [channels.GAME_A_RECRUIT_CHANNEL_ID, channels.GAME_B_RECRUIT_CHANNEL_ID,
                              channels.GAME_C_RECRUIT_CHANNEL_ID, channels.GAME_D_RECRUIT_CHANNEL_ID]

    if channel_id in normal_channel_id_list and not lolpark.is_normal_game:
        lolpark.is_normal_game = await normal_game.make_normal_game(ctx, message)


async def end_game(ctx):
    channel_id = ctx.channel.id
    normal_channel_id_list = [channels.GAME_A_RECRUIT_CHANNEL_ID, channels.GAME_B_RECRUIT_CHANNEL_ID,
                              channels.GAME_C_RECRUIT_CHANNEL_ID, channels.GAME_D_RECRUIT_CHANNEL_ID]

    if channel_id in normal_channel_id_list and lolpark.is_normal_game:
        lolpark.normal_game_log = None
        lolpark.normal_game_channel = None
        lolpark.is_normal_game = await normal_game.end_normal_game(ctx)


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