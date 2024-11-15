from datetime import datetime
from discord.ui import Button, View
import discord
from summoner import Summoner
import lolpark
import functions
import database


# 20인 내전 모집
async def make_twenty_game(ctx, message):

    def create_callback(line_name, button):
        # 버튼 상호작용 함수

        async def callback(interaction: discord.Interaction):
            user = Summoner(interaction.user)
            is_valid_push = True

            # 내전 3회 이상인지 체크, 내전 3회 미만이라면 버튼 처리 X
            if not database.is_valid_twenty(user):
                twenty_recruit_channel = bot.get_channel(channels.TWENTY_RECRUIT_CHANNEL_ID)
                await twenty_recruit_channel.send(f'내전 3회 미만 서버원은 20인 내전 참여가 불가능합니다.')
                is_valid_push = False

            # 같은 라인에 이미 등록했는지 체크, 등록했다면 유저 삭제
            for summoner in lolpark.twenty_summoner_list[line_name]:
                if summoner == user:
                    lolpark.twenty_summoner_list[line_name].remove(summoner)
                    is_valid_push = False
                    break

            # 다른 라인에 등록했는지 체크, 등록되어 있으면 상호작용 무시
            for (_, line_summoners) in lolpark.twenty_summoner_list.items():
                for summoner in line_summoners:
                    if user == summoner:
                        is_valid_push = False
                        break

            # 위 두 사항에 해당되지 않는 경우, 해당 라인에 참여시키고 메세지 출력
            if is_valid_push:
                lolpark.twenty_summoner_list[line_name].append(user)
            button.label = f"{line_name} : {len(lolpark.twenty_summoner_list[line_name])}"
            # 4표 이상이면 버튼 색 빨간색으로 설정
            button.style = discord.ButtonStyle.red \
                if len(lolpark.twenty_summoner_list[line_name]) >= 4 else discord.ButtonStyle.gray

            await interaction.response.edit_message(content=f'{get_twenty_recruit_board(message)}\n',
                                                    view=lolpark.twenty_view)

        return callback

    class TwentyView(View):
        def __init__(self):
            # 투표 제한 시간 설정, 20인 내전은 12시간으로 설정
            super().__init__(timeout=43200)

            self.buttons = [
                Button(label=f'{line_name} : 0', style=discord.ButtonStyle.gray)
                for line_name in lolpark.line_names
            ]

            for line_number, button in enumerate(self.buttons):
                button.callback = create_callback(lolpark.line_names[line_number], button)
                self.add_item(button)

    if lolpark.is_twenty_game:
        await ctx.send(f'20인 내전이 현재 진행 중입니다. 20인 내전 종료 후 다시 열어주세요.')
        return

    # 변수 초기화, 새 내전 생성
    lolpark.twenty_summoner_list = {line_name: [] for line_name in lolpark.line_names}
    lolpark.twenty_view = TwentyView()
    lolpark.twenty_host = Summoner(ctx.author)
    lolpark.is_twenty_game = True

    # 내전 역할 가져오기
    role_name = '내전'
    role = discord.utils.get(ctx.guild.roles, name=role_name)

    lolpark.twenty_view_message = await ctx.send(content=f'{get_twenty_recruit_board(message)}\n',
                                                 view=lolpark.twenty_view)
    await ctx.send(f'20인 내전 {message}\n{role.mention}\n'
                   f'이미 모집된 라인(버튼이 빨간색인 경우)에 참여를 원하는 경우, '
                   f'버튼을 누르시면 자동으로 대기 목록에 추가됩니다.\n'
                   f'## 20인 내전은 최대 6게임이 진행될 수 있습니다. 시간이 안되시는 분은 참여 지양해주시길 바랍니다.\n'
                   f'## 20인 내전 노쇼의 경우, 일반 내전 노쇼보다 경고가 강하게 들어갑니다. '
                   f'신청 이후 참여가 어려워진 경우, 반드시 시작 전에 버튼으로 취소 혹은 말씀을 반드시 해주시길 바랍니다.')


async def close_twenty_game(ctx):
    # 20인 내전 마감

    if lolpark.twenty_host != Summoner(ctx.author):
        return

    game_members = 20

    # 팀장 라인 번호 찾기
    team_head_line_number = get_team_head_number(game_members)
    # 대기자 리스트 추출
    waiting_people_list = get_waiting_list(game_members)
    # 팀장 텍스트
    team_head_lineup = get_team_head_lineup(team_head_line_number, game_members)
    # 팀원 텍스트
    team_user_lineup = get_user_lineup(team_head_line_number, game_members)

    lineup_board = team_head_lineup
    lineup_board += team_user_lineup

    await ctx.send(lineup_board)
    if waiting_people_list != '':
        await ctx.send(f'{waiting_people_list}')

    await ctx.send(f'{game_members}인 내전 모집이 완료되었습니다. 결과를 확인해주세요')
    await ctx.send(f'<#1287070975640211557> 채널에서 !경매 를 통해 경매를 시작할 수 있습니다.')

    for line, summoners in lolpark.twenty_summoner_list.items():
        lolpark.twenty_summoner_list[line] = summoners[:4]

    # 초기화
    lolpark.twenty_view = None
    if lolpark.twenty_view_message:
        await lolpark.twenty_view_message.delete()
        lolpark.twenty_view_message = None


async def end_twenty_game(ctx):
    # 20인 내전 쫑

    if lolpark.twenty_host != Summoner(ctx.author):
        return

    # 내전 역할 가져오기
    role_name = '내전'
    role = discord.utils.get(ctx.guild.roles, name=role_name)

    await ctx.send(f'20인 내전 쫑내겠습니다~\n{role.mention}')

    # 초기화
    lolpark.twenty_summoner_list = None
    lolpark.twenty_host = None
    lolpark.twenty_view = None
    lolpark.is_twenty_game = False
    if lolpark.twenty_view_message:
        await lolpark.twenty_view_message.delete()
        lolpark.twenty_view_message = None


def get_team_head_number(game_members: int):
    # 팀장 찾기
    # 각 라인별 최대 점수, 최소 점수를 구해서 차이가 가장 적은 라인 반환

    min_diff = float('inf')
    line_number = -1

    for index, (line_name, user_list) in enumerate(lolpark.twenty_summoner_list.items()):
        if len(user_list) < (game_members // 5):
            continue
        scores = [functions.get_user_tier_score(user.nickname) for user in user_list[:(game_members // 5)]]

        if scores:
            diff = max(scores) - min(scores)

            if 0 <= diff < min_diff:
                min_diff = diff
                line_number = index

    return line_number


def get_team_head_lineup(head_line_number: int, game_members: int):
    # 팀장 결과 반환

    line_name = lolpark.line_names[head_line_number]

    result = ''
    result += f'팀장 : {line_name}\n'
    result += f'=========================================\n\n'

    participants = [user for user in lolpark.twenty_summoner_list[line_name][:(game_members // 5)]]

    users = functions.sort_game_members(participants)

    for i, user in enumerate(users):
        result += f'{i + 1}팀\n'
        result += f'<@{user.id}> : {user.score}\n\n'

    result += f'=========================================\n\n\n'

    return result


def get_user_lineup(head_line_number: int, game_members: int):
    # 팀원 결과 반환

    result = ''
    result += f'팀원\n'
    result += f'=========================================\n\n'

    for line_number, (line_name, users) in enumerate(lolpark.twenty_summoner_list.items()):
        if line_number == head_line_number:
            continue

        participants = []

        for i in range(0, game_members // 5):
            participants.append(users[i])

        sorted_participants = functions.sort_game_members(participants)

        result += f'### {line_name}\n\n'

        for user in sorted_participants:
            result += f'<@{user.id}>\n'

        result += f' \n'

    result += f'========================================='

    return result


def get_waiting_list(game_members: int):
    # 대기자 명단 반환

    waiting_list = ''

    for (line_name, user_list) in lolpark.twenty_summoner_list.items():
        for i in range(len(user_list)):
            if i == (game_members // 5):
                waiting_list += f'{line_name}\n'

            if i >= (game_members // 5):
                waiting_list += f'{user_list[i].nickname}\n'

    if waiting_list == '':
        return waiting_list

    result = ''
    result += f'대기 명단\n'
    result += f'=========================================\n'
    result += waiting_list
    result += f'========================================='

    return result


def get_twenty_recruit_board(message):
    team_head_number = get_team_head_number(20)

    twenty_recruit_board = ''

    twenty_recruit_board += f'```\n'

    today_text = datetime.now().strftime("%m월 %d일 20인 내전")

    twenty_recruit_board += f'{today_text} {message}\n\n'

    for i, (line_name, user_list) in enumerate(lolpark.twenty_summoner_list.items()):
        twenty_recruit_board += f'{line_name}'
        if i == team_head_number:
            twenty_recruit_board += f' (팀장)'
        twenty_recruit_board += f'\n'
        for number, user in enumerate(user_list):
            if number >= 4:
                twenty_recruit_board += f'(대기) '
            else:
                twenty_recruit_board += f'{number + 1}. '
            twenty_recruit_board += f'{user.nickname}\n'
        twenty_recruit_board += f'\n'

    twenty_recruit_board += f'```'

    return twenty_recruit_board


async def reset_twenty_game(ctx):
    lolpark.twenty_summoner_list = None
    lolpark.twenty_host = None
    lolpark.twenty_view = None
    lolpark.is_twenty_game = False
    if lolpark.twenty_view_message:
        await lolpark.twenty_view_message.delete()
        lolpark.twenty_view_message = None
    await ctx.send('20인 내전을 초기화했습니다.')


def get_twenty_game_board(team_1, team_2):
    board = f'```\n'
    board += f'{team_1}\n\n'
    for line, (summoner, score) in lolpark.auction_dict[team_1].items():
        board += f'{line} : {summoner.nickname} > {score if score != -1 else "팀장"}\n'
    board += f'\n{team_2}\n\n'
    for line, (summoner, score) in lolpark.auction_dict[team_2].items():
        board += f'{line} : {summoner.nickname} > {score if score != -1 else "팀장"}\n'
    board += f'```'
    return board


def get_result_board(teams, team_1, team_2, team_1_win_count, team_2_win_count, is_record=True):
    team_1_result = '승' if team_1_win_count > team_2_win_count else '패'
    team_2_result = '승' if team_1_win_count < team_2_win_count else '패'
    board = f'[기록완료]' if is_record else f'[기록대기]\n'
    board += f'```\n'
    board += f'{team_1} ({team_1_result}) {team_1_win_count}승 {team_2_win_count}패\n\n'
    for line, (summoner, score) in lolpark.auction_dict[team_1].items():
        board += f'{line} : {summoner.nickname} > {score if score != -1 else "팀장"}\n'
    board += f'\n{team_2} ({team_2_result}) {team_2_win_count}승 {team_1_win_count}패\n\n'
    for line, (summoner, score) in lolpark.auction_dict[team_2].items():
        board += f'{line} : {summoner.nickname} > {score if score != -1 else "팀장"}\n'
    board += f'```'
    return board
