from datetime import datetime
from discord.ui import Button, View
import discord
from summoner import Summoner
import lolpark
import functions


async def make_twenty_game(ctx, message):
    # 20인 내전 모집

    def create_callback(line_name, button):
        # 버튼 상호작용 함수

        async def callback(interaction: discord.Interaction):
            user = Summoner(interaction.user)
            is_valid_push = True

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

            await interaction.response.edit_message(content=get_twenty_recruit_board(message),
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

    # 변수 초기화, 새 내전 생성
    lolpark.twenty_summoner_list = {line_name: [] for line_name in lolpark.line_names}
    lolpark.twenty_view = TwentyView()
    lolpark.twenty_host = ctx.author

    # 내전 역할 가져오기
    role_name = '내전'
    role = discord.utils.get(ctx.guild.roles, name=role_name)

    await ctx.send(content=get_twenty_recruit_board(message), view=lolpark.twenty_view)
    await ctx.send(f'20인 내전 {message}\n{role.mention}')
    await ctx.send(f'이미 모집된 라인(버튼이 빨간색인 경우)에 참여를 원하는 경우, 버튼을 누르시면 자동으로 대기 목록에 추가됩니다.')


async def close_twenty_game(ctx):
    # 20인 내전 마감

    if lolpark.twenty_host != ctx.author:
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
    await ctx.send(f'20인내전경매 채널에서 !경매 를 통해 경매를 시작할 수 있습니다.')

    # 초기화
    lolpark.twenty_host = None
    lolpark.twenty_view = None


async def end_twenty_game(ctx):
    # 20인 내전 쫑

    if lolpark.twenty_host != ctx.author:
        return

    # 내전 역할 가져오기
    role_name = '내전'
    role = discord.utils.get(ctx.guild.roles, name=role_name)

    await ctx.send(f'20인 내전 쫑내겠습니다~\n{role.mention}')

    # 초기화
    lolpark.twenty_summoner_list = None
    lolpark.twenty_host = None
    lolpark.twenty_view = None

    return False


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
    lolpark.twenty_view = None
    lolpark.twenty_host = None
    await ctx.send('20인 내전을 초기화했습니다.')
