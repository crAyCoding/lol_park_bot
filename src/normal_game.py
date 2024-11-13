import lolpark
import channels
import random
import discord
import record
from discord.ui import Button
from functions import *
from summoner import Summoner
from database import add_summoner, update_summoner, add_database_count
from bot import bot


# 일반 내전 모집
async def make_normal_game(ctx, message='3판 2선 모이면 바로 시작'):

    # 내전 채팅 로그 기록 시작, 내전을 연 사람을 로그에 추가
    user = Summoner(ctx.author)
    lolpark.normal_game_log = {user: [ctx.message.id]}
    lolpark.normal_game_channel = ctx.channel.id

    # 내전 역할 가져오기
    role_name = '내전'
    role = discord.utils.get(ctx.guild.roles, name=role_name)

    lolpark.normal_game_creator = Summoner(ctx.author)
    await ctx.send(f'{get_nickname(ctx.author.display_name)} 님이 내전을 모집합니다!\n'
                   f'[ {message} ]\n{role.mention}')
    return True


# 피어리스 내전 모집
async def make_fearless_game(ctx, message='3판 2선 모이면 바로 시작'):

    user = Summoner(ctx.author)
    lolpark.fearless_game_log = {user: [ctx.message.id]}

    # 내전 역할 가져오기
    role_name = '내전'
    role = discord.utils.get(ctx.guild.roles, name=role_name)

    lolpark.fearless_game_creator = Summoner(ctx.author)
    await ctx.send(f'{get_nickname(ctx.author.display_name)} 님이 피어리스 내전을 모집합니다!\n'
                   f'[ {message} ]\n{role.mention}')


# 일반 내전 마감
async def close_normal_game(ctx, summoners, host):
    class GameMember:
        def __init__(self, index, summoner):
            self.index = index + 1
            self.summoner = summoner

    class GameView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=14400)
            self.members = [GameMember(i, summoners[i]) for i in range(0, 10)]
            for member in self.members:
                self.add_item(EditButton(member))
            self.add_item(GameStartButton())

        async def update_message(self, interaction: discord.Interaction):
            updated_message = "\n".join([f"### {member.index}: <@{member.summoner.id}>" for member in self.members])
            await interaction.response.edit_message(content=updated_message, view=self)

    class EditButton(discord.ui.Button):
        def __init__(self, member):
            super().__init__(label=f"{member.index}번 소환사 변경")
            self.member = member
            self.index = member.index

        async def callback(self, interaction: discord.Interaction):
            new_summoner = Summoner(interaction.user)
            if new_summoner in summoners:
                await interaction.response.defer()
            else:
                prev_summoner = summoners[self.index - 1]
                self.view.members[self.index - 1] = GameMember(self.index - 1, new_summoner)
                summoners[self.index - 1] = new_summoner
                await ctx.send(f'{self.index}번 소환사가 {get_nickname(prev_summoner.nickname)}에서 '
                               f'{get_nickname(new_summoner.nickname)}으로 변경되었습니다.')
                updated_message = "\n".join([f"### {member.index}: <@{member.summoner.id}>"
                                             for member in self.view.members])
                await interaction.response.edit_message(content=updated_message, view=self.view)

    class GameStartButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label=f"명단 확정", style=discord.ButtonStyle.success)

        async def callback(self, interaction: discord.Interaction):
            press_summoner = Summoner(interaction.user)
            if press_summoner != host:
                await ctx.send(f'{get_nickname(host.nickname)}님만 확정할 수 있습니다.'
                               f'{get_nickname(press_summoner.nickname)}님 누르지 말아주세요.')
                await interaction.response.defer()
                return
            await interaction.message.delete()
            confirmed_summoners = [member.summoner for member in view.members]

            sorted_summoners = sort_game_members(confirmed_summoners)
            sorted_summoners_message = get_result_sorted_by_tier(sorted_summoners)

            await ctx.send(sorted_summoners_message)
            await handle_game_team(ctx, sorted_summoners, summoners, host)

    view = GameView()
    game_members_result = "\n".join([f"### {member.index}: <@{member.summoner.id}>" for member in view.members])
    await ctx.send(content=f'내전 모집이 완료되었습니다. 참여 명단을 확인하세요.\n\n{game_members_result}', view=view)


# 일반 내전 쫑
async def end_normal_game(ctx):

    if lolpark.normal_game_creator != Summoner(ctx.author):
        return True

    # 내전 역할 가져오기
    role_name = '내전'
    role = discord.utils.get(ctx.guild.roles, name=role_name)

    await ctx.send(f'내전 쫑내겠습니다~\n{role.mention}')

    # 초기화
    lolpark.normal_game_log = None
    lolpark.normal_game_channel = None
    lolpark.normal_game_creator = None

    return False


# 피어리스 내전 쫑
async def end_fearless_game(ctx):

    if lolpark.fearless_game_creator != Summoner(ctx.author):
        return

    # 내전 역할 가져오기
    role_name = '내전'
    role = discord.utils.get(ctx.guild.roles, name=role_name)

    await ctx.send(f'피어리스 내전 쫑내겠습니다~\n{role.mention}')

    # 초기화
    lolpark.fearless_game_log = None
    lolpark.fearless_game_creator = None


# 팀장 정하기, 메모장으로 진행, 명단 수정
async def handle_game_team(ctx, sorted_summoners, summoners, host):
    team_head_list = []

    class GameMember:
        def __init__(self, index):
            self.index = index + 1
            self.summoner = sorted_summoners[index]

    class HandleTeamView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=3600)
            self.users = [GameMember(i) for i in range(0, 10)]
            for user in self.users:
                self.add_item(TeamHeadButton(user))
            self.add_item(StopButton())
            self.add_item(UndoButton())

    class TeamHeadButton(discord.ui.Button):
        def __init__(self, user):
            super().__init__(label=f"{user.index}.{user.summoner.nickname}")
            self.user = user

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user != host:
                await (interaction.response.edit_message
                       (content=f'## {get_nickname(host.nickname)}님이 누른 것만 인식합니다. '
                                f'{get_nickname(press_user.nickname)}님 누르지 말아주세요.',
                        view=self.view))
                return
            team_head_list.append(self.user.summoner)
            await ctx.send(f'{get_nickname(self.user.summoner.nickname)}님이 팀장입니다.')
            self.view.remove_item(self)
            self.view.users.remove(self.user)
            if len(team_head_list) == 2:
                await interaction.message.delete()
                await choose_blue_red_game(ctx, team_head_list, self.view.users, summoners, host)
                return

            await interaction.response.edit_message(content=f'## 두번째 팀장 닉네임 버튼을 눌러주세요.',
                                                    view=self.view)

    class StopButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label=f"메모장으로 진행", style=discord.ButtonStyle.red)

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user != host:
                await (interaction.response.edit_message
                       (content=f'## {get_nickname(host.nickname)}님이 누른 것만 인식합니다. '
                                f'{get_nickname(press_user.nickname)}님 누르지 말아주세요.',
                        view=self.view))
                return
            await ctx.send(f'메모장으로 진행합니다.')
            await interaction.message.delete()
            await finalize_with_notepad(ctx, sorted_summoners, summoners, host)

    class UndoButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label=f"명단 수정하기", style=discord.ButtonStyle.primary)

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user != host:
                await (interaction.response.edit_message
                       (content=f'## {get_nickname(host.nickname)}님이 누른 것만 인식합니다. '
                                f'{get_nickname(press_user.nickname)}님 누르지 말아주세요.',
                        view=self.view))
                return
            await interaction.message.delete()
            await close_normal_game(ctx, summoners, host)

    handle_team_view = HandleTeamView()
    await ctx.send(content=f'## {get_nickname(host.nickname)}님, '
                           f'팀장 두 분의 닉네임 버튼을 눌러주세요.', view=handle_team_view)


# 메모장으로 진행 시
async def finalize_with_notepad(ctx, sorted_summoners, summoners, host):

    class NotepadView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=3600)
            for summoner in sorted_summoners:
                self.add_item(SummonerButton(summoner))
            self.add_item(UndoButton())
            self.summoners = sorted_summoners
            self.blue_team = []

    class SummonerButton(discord.ui.Button):
        def __init__(self, summoner):
            super().__init__(label=f"{summoner.nickname}")
            self.summoner = summoner

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user != host:
                await (interaction.response.edit_message
                       (content=f'## {get_nickname(host.nickname)}님이 누른 것만 인식합니다. '
                                f'{get_nickname(press_user.nickname)}님 누르지 말아주세요.',
                        view=self.view))
                return
            self.style = discord.ButtonStyle.primary
            self.disabled = True
            self.view.blue_team.append(self.summoner)
            self.view.summoners.remove(self.summoner)
            if len(self.view.blue_team) == 5:
                teams = [self.view.blue_team,self.view.summoners]
                board_message = get_game_board(teams)
                await interaction.message.delete()
                await finalize_team(ctx, teams, board_message, summoners, host)
                return
            await (interaction.response.edit_message
                   (content=f'## {get_nickname(host.nickname)}님, '
                            f'블루팀 {5 - len(self.view.blue_team)}명의 닉네임 버튼을 눌러주세요.',
                    view=self.view))

    class UndoButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label=f"팀장 선택으로 돌아가기", style=discord.ButtonStyle.red)

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user != host:
                await (interaction.response.edit_message
                       (content=f'## {get_nickname(host.nickname)}님이 누른 것만 인식합니다. '
                                f'{get_nickname(press_user.nickname)}님 누르지 말아주세요.',
                        view=self.view))
                return
            await interaction.message.delete()
            await handle_game_team(ctx, sorted_summoners, summoners, host)

    notepad_view = NotepadView()
    await ctx.send(content=f'## {get_nickname(host.nickname)}님, '
                           f'블루팀 5명의 닉네임 버튼을 눌러주세요.', view=notepad_view)


# 블루팀 레드팀 고르기
async def choose_blue_red_game(ctx, team_head_list, members, summoners, host):
    await ctx.send(f'=========================================')
    blue_team = []
    red_team = []

    team_head1 = team_head_list[0]
    team_head2 = team_head_list[1]

    while True:
        random_number1, random_number2 = random.randint(1, 6), random.randint(1, 6)

        await ctx.send(f'{get_nickname(team_head1.nickname)} > {random_number1} :'
                       f' {random_number2} < {get_nickname(team_head2.nickname)}')

        if random_number1 != random_number2:
            selected = team_head1 if random_number1 > random_number2 else team_head2
            not_selected = team_head2 if selected == team_head_list[0] else team_head1
            break

    class BlueRedView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=3600)

            blue_button = Button(label=f'블루팀', style=discord.ButtonStyle.primary)
            red_button = Button(label=f"레드팀", style=discord.ButtonStyle.red)

            blue_button.callback = lambda interaction: self.button_callback(interaction, team_type=True)
            red_button.callback = lambda interaction: self.button_callback(interaction, team_type=False)

            self.add_item(blue_button)
            self.add_item(red_button)

        async def button_callback(self, interaction: discord.Interaction, team_type: bool):
            press_user = Summoner(interaction.user)
            if press_user != selected:
                warning_message = (f'## {get_nickname(selected.nickname)}님이 누른 것만 인식합니다. '
                                   f'{get_nickname(press_user.nickname)}님 누르지 말아주세요.')
                await interaction.response.edit_message(content=warning_message, view=blue_red_view)
                return
            (blue_team if team_type else red_team).append(selected)
            (red_team if team_type else blue_team).append(not_selected)
            selected_team = '블루팀' if team_type else '레드팀'
            await ctx.send(f'{get_nickname(selected.nickname)}님이 {selected_team}을 선택하셨습니다.')
            await interaction.message.delete()
            await choose_order_game(ctx, blue_team, red_team, members, summoners, host)

    blue_red_view = BlueRedView()
    await ctx.send(content=f'## {get_nickname(selected.nickname)}님, 진영을 선택해주세요.', view=blue_red_view)


# 선뽑, 후뽑 정하기
async def choose_order_game(ctx, blue_team, red_team, members, summoners, host):
    await ctx.send(f'=========================================')
    teams = [blue_team, red_team]
    order_flag = True

    while True:
        random_number1, random_number2 = random.randint(1, 6), random.randint(1, 6)

        await ctx.send(f'{get_nickname(blue_team[0].nickname)} > {random_number1} :'
                       f' {random_number2} < {get_nickname(red_team[0].nickname)}')

        if random_number1 != random_number2:
            selected = blue_team[0] if random_number1 > random_number2 else red_team[0]
            order_flag = True if selected == blue_team[0] else False
            not_selected = red_team[0] if selected == blue_team[0] else blue_team[0]
            break

    class OrderView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=3600)

            first_pick_button = Button(label=f"선뽑(먼저 한명 뽑기)", style=discord.ButtonStyle.primary)
            second_pick_button = Button(label=f"후뽑(나중에 두명 뽑기)", style=discord.ButtonStyle.red)

            first_pick_button.callback = lambda interaction: self.button_callback(interaction, pick_type=True)
            second_pick_button.callback = lambda interaction: self.button_callback(interaction, pick_type=False)

            self.add_item(first_pick_button)
            self.add_item(second_pick_button)

        async def button_callback(self, interaction: discord.Interaction, pick_type):
            press_user = Summoner(interaction.user)
            if press_user != selected:
                warning_message = (f'## {get_nickname(selected.nickname)}님이 누른 것만 인식합니다. '
                                   f'{get_nickname(press_user.nickname)}님 누르지 말아주세요.')
                await interaction.response.edit_message(content=warning_message, view=order_view)
                return
            order_type = '선뽑' if pick_type else '후뽑'
            await ctx.send(f'{get_nickname(selected.nickname)}님이 {order_type}입니다.')
            await interaction.message.delete()
            await choose_game_team(ctx, teams, order_flag if pick_type else not order_flag, members, summoners, host)
            return

    order_view = OrderView()
    await ctx.send(content=f'## {get_nickname(selected.nickname)}님, 뽑는 순서를 정해주세요.', view=order_view)


# 팀뽑 진행 (선뽑 한명, 후뽑 두명, 선뽑 두명, 후뽑 두명 뽑기)
async def choose_game_team(ctx, teams, flag, members, summoners, host):
    await ctx.send(f'=========================================')

    pick_order = [flag, not flag, not flag, flag, flag, not flag, not flag, flag]

    def get_team_head(pick_order, teams):
        return teams[0][0] if pick_order[0] else teams[1][0]

    def add_member_to_team(pick_order, teams, summoner):
        if pick_order[0]:
            teams[0].append(summoner)
        else:
            teams[1].append(summoner)

    class ChooseGameView(discord.ui.View):
        def __init__(self):
            super().__init__()
            self.members = [members[i].summoner for i in range(0, 8)]
            for member in self.members:
                self.add_item(MemberButton(member))

    class MemberButton(discord.ui.Button):
        def __init__(self, member):
            super().__init__(label=f"{member.nickname}")
            self.member = member

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            team_head = get_team_head(pick_order, teams)

            if press_user != team_head:
                await interaction.response.edit_message(
                    content=f'{get_game_board(teams)}\n## '
                            f'{get_nickname(team_head.nickname)}님이 누른 것만 인식합니다. '
                            f'{get_nickname(press_user.nickname)}님 누르지 말아주세요.',
                    view=self.view)
                return

            self.view.remove_item(self)
            self.view.members.remove(self.member)
            add_member_to_team(pick_order, teams, self.member)
            pick_order.pop(0)

            await ctx.send(f'{get_nickname(press_user.nickname)}님이 '
                           f'{get_nickname(self.member.nickname)}님을 '
                           f'뽑았습니다.')

            if len(pick_order) == 1:
                add_member_to_team(pick_order, teams, self.view.members[0])
                await interaction.message.delete()
                board_message = get_game_board(teams)
                await finalize_team(ctx, teams, board_message, summoners, host)
                return

            team_head = get_team_head(pick_order, teams)
            await interaction.response.edit_message(content=f'{get_game_board(teams)}\n## '
                                                            f'{get_nickname(team_head.nickname)}님, 팀원을 뽑아주세요.',
                                                    view=self.view)

    choose_game_view = ChooseGameView()
    await ctx.send(content=f'{get_game_board(teams)}\n## '
                           f'{get_nickname(get_team_head(pick_order, teams).nickname)}님, 팀원을 뽑아주세요.',
                   view=choose_game_view)

    # await ctx.send(get_game_board(teams))


# 이대로 확정 , 명단 수정 (내전 시작 최종 확인)
async def finalize_team(ctx, teams, board_message, summoners, host):

    class FinalTeamView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=3600)
            self.add_item(FinalizeButton())
            self.add_item(EditButton())

    class FinalizeButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label=f"이대로 확정", style=discord.ButtonStyle.green)

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user != host:
                await (interaction.response.edit_message
                       (content=f'{board_message}\n## {get_nickname(host.nickname)}님이 누른 것만 인식합니다. '
                                f'{get_nickname(press_user.nickname)}님 누르지 말아주세요.',
                        view=self.view))
                return
            self.view.clear_items()

            await interaction.message.delete()
            # 내전 모집 완료 후 메세지 출력
            await send_normal_game_message(ctx)
            # 맞는 음성 채널로 이동
            await move_summoners(ctx, teams)
            # 기록 보드 자동 출력
            await add_normal_game_to_database(ctx, summoners, teams)

    class EditButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label=f"명단 수정", style=discord.ButtonStyle.primary)

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user != host:
                await (interaction.response.edit_message
                       (content=f'{board_message}\n## {get_nickname(host.nickname)}님이 누른 것만 인식합니다. '
                                f'{get_nickname(press_user.nickname)}님 누르지 말아주세요.',
                        view=self.view))
                return
            await interaction.message.delete()
            await close_normal_game(ctx, summoners, host)

    final_team_view = FinalTeamView()
    await ctx.send(content=f'{board_message}',
                   view=final_team_view)


# 내전 전적 기록용 보드 출력
async def add_normal_game_to_database(ctx, summoners, teams):
    for summoner in summoners:
        await add_summoner(summoner)
        await update_summoner(summoner)
    await ctx.send(f'내전 종료 이후 결과를 직접 기입해 주세요. 가급적 꼬이지 않게 대표로 한 명만 진행해 주시길 바랍니다.\n'
                   f'24시간 내에 아무도 기록하지 않을 경우, 내전 전적에 반영되지 않습니다. 이 점 참고 바랍니다.')
    await record.record_normal_game(ctx, summoners, teams)


# 서버원 내전 팀 채널로 이동
async def move_summoners(channel, teams):
    channel_id = channel.id
    guild = channel.guild
    normal_game_recruit_channel_id_list = channels.NORMAL_GAME_CHANNEL_ID_LIST
    blue_team_channel_id_list = channels.NORMAL_GAME_TEAM_1_CHANNEL_ID_LIST
    red_team_channel_id_list = channels.NORMAL_GAME_TEAM_2_CHANNEL_ID_LIST

    blue_team_channel = None
    red_team_channel = None

    if channel_id == channels.GAME_FEARLESS_A_RECRUIT_CHANNEL_ID:
        blue_team_channel = bot.get_channel(channels.GAME_FEARLESS_A_TEAM_1_CHANNEL_ID)
        red_team_channel = bot.get_channel(channels.GAME_FEARLESS_A_TEAM_2_CHANNEL_ID)

    for i, recruit_channel_id in enumerate(normal_game_recruit_channel_id_list):
        if channel_id == recruit_channel_id:
            blue_team_channel = bot.get_channel(blue_team_channel_id_list[i])
            red_team_channel = bot.get_channel(red_team_channel_id_list[i])

    for summoner in teams[0]:
        member = guild.get_member(summoner.id)
        if member.voice is not None and blue_team_channel is not None:
            await member.move_to(blue_team_channel)

    for summoner in teams[1]:
        member = guild.get_member(summoner.id)
        if member.voice is not None and red_team_channel is not None:
            await member.move_to(red_team_channel)


async def send_normal_game_message(ctx):

    await ctx.send(f'## https://banpick.kr/ \n'
                   f'밴픽은 위 사이트에서 진행해주시면 됩니다.\n'
                   f'## 해당 메세지 출력 이후 각 팀 디스코드로 자동 이동됩니다. 오류가 나지 않게 가만히 계셔주시면 감사하겠습니다.\n'
                   f'혹여 30초 내에 이동되지 않는 경우 수동으로 옮겨주시고 개발자에게 DM 부탁드립니다.\n'
                   f'## 사용자 설정 방 제목 : 롤파크 / 비밀번호 : 0921\n')


def get_game_board(teams):
    board = f'```\n'
    board += f'🟦  블루팀\n\n'
    for blue_member in teams[0]:
        board += f'{blue_member.nickname}\n'
    board += f'\n🟥  레드팀\n\n'
    for red_member in teams[1]:
        board += f'{red_member.nickname}\n'
    board += f'```'
    return board


def get_result_board(teams, blue_win_count, red_win_count, is_record=False):
    blue_result = '승' if blue_win_count > red_win_count else '패' if blue_win_count < red_win_count else '무'
    red_result = '승' if blue_win_count < red_win_count else '패' if blue_win_count > red_win_count else '무'
    board = f'```\n'
    board += f'🟦  블루팀 ({blue_result}) {blue_win_count}승 {red_win_count}패\n\n'
    for blue_member in teams[0]:
        board += f'{blue_member.nickname}\n'
    board += f'\n🟥  레드팀 ({red_result}) {red_win_count}승 {blue_win_count}패\n\n'
    for red_member in teams[1]:
        board += f'{red_member.nickname}\n'
    board += f'```\n\n'
    board += f'## [기록완료]' if is_record else f'## [기록대기]\n'
    return board


async def reset_normal_game(ctx):
    lolpark.is_normal_game = False
    lolpark.normal_game_log = None
    lolpark.normal_game_channel = None
    await ctx.send("일반 내전을 초기화했습니다.")


async def reset_fearless_game(ctx):
    lolpark.fearless_game_creator = False
    lolpark.fearless_game_log = None
    await ctx.send("피어리스 내전을 초기화했습니다.")
