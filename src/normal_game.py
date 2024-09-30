import dcpaow
import itertools
import random
import discord
from discord.ui import Button
from functions import *
from summoner import Summoner


async def make_normal_game(ctx, message='3판 2선 모이면 바로 시작'):
    # 일반 내전 모집

    # 내전 채팅 로그 기록 시작, 내전을 연 사람을 로그에 추가
    user = Summoner(ctx.author)
    dcpaow.normal_game_log = {user: [ctx.message.id]}
    dcpaow.normal_game_channel = ctx.channel.id

    # 내전 역할 가져오기
    role_name = '내전'
    role = discord.utils.get(ctx.guild.roles, name=role_name)

    dcpaow.normal_game_creator = Summoner(ctx.author)
    await ctx.send(f'{get_nickname(ctx.author.display_name)} 님이 내전을 모집합니다!\n[ {message} ]\n{role.mention}')
    return True


async def close_normal_game(ctx, summoners):
    # 일반 내전 마감
    class GameMember:
        def __init__(self, index, summoner):
            self.index = index + 1
            self.summoner = summoner

    class GameView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=3600)
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
                self.view.members[self.index - 1] = GameMember(self.index - 1, new_summoner)
                summoners[self.index - 1] = new_summoner
                updated_message = "\n".join([f"### {member.index}: <@{member.summoner.id}>"
                                             for member in self.view.members])
                await interaction.response.edit_message(content=updated_message, view=self.view)

    class GameStartButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label=f"명단 확정", style=discord.ButtonStyle.success)

        async def callback(self, interaction: discord.Interaction):
            press_summoner = Summoner(interaction.user)
            if press_summoner != dcpaow.normal_game_creator:
                await ctx.send(f'{get_nickname(dcpaow.normal_game_creator.nickname)}만 확정할 수 있습니다.')
                await interaction.response.defer()
                return
            await interaction.message.delete()
            confirmed_summoners = [member.summoner for member in view.members]

            summoners_result = sort_game_members(confirmed_summoners)
            sorted_summoners_message = get_result_sorted_by_tier(summoners_result)

            await ctx.send(sorted_summoners_message)
            await handle_game_team(ctx, summoners_result, summoners)

    view = GameView()
    game_members_result = "\n".join([f"### {member.index}: <@{member.summoner.id}>" for member in view.members])
    await ctx.send(content=f'내전 모집이 완료되었습니다. 참여 명단을 확인하세요.\n\n{game_members_result}', view=view)


async def end_normal_game(ctx):
    # 일반 내전 쫑

    if dcpaow.normal_game_creator != Summoner(ctx.author):
        return True

    # 내전 역할 가져오기
    role_name = '내전'
    role = discord.utils.get(ctx.guild.roles, name=role_name)

    await ctx.send(f'내전 쫑내겠습니다~\n{role.mention}')

    # 초기화
    dcpaow.normal_game_creator = None

    return False


async def handle_game_team(ctx, summoners, prev_summoners):
    team_head_list = []

    class GameMember:
        def __init__(self, index):
            self.index = index + 1
            self.summoner = summoners[index]

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
            if press_user != dcpaow.normal_game_creator:
                await (interaction.response.edit_message
                       (content=f'## {get_nickname(dcpaow.normal_game_creator.nickname)}님이 누른 것만 인식합니다. '
                                f'{get_nickname(press_user.nickname)}님 누르지 말아주세요.',
                        view=self.view))
                return
            team_head_list.append(self.user.summoner)
            await ctx.send(f'{get_nickname(self.user.summoner.nickname)}님이 팀장입니다.')
            self.view.remove_item(self)
            self.view.users.remove(self.user)
            if len(team_head_list) == 2:
                await interaction.message.delete()
                await choose_blue_red_game(ctx, team_head_list, self.view.users)
                return

            await interaction.response.edit_message(content=f'## 두번째 팀장 닉네임 버튼을 눌러주세요.',
                                                    view=self.view)

    class StopButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label=f"메모장으로 진행", style=discord.ButtonStyle.red)

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user != dcpaow.normal_game_creator:
                await (interaction.response.edit_message
                       (content=f'## {get_nickname(dcpaow.normal_game_creator.nickname)}님이 누른 것만 인식합니다. '
                                f'{get_nickname(press_user.nickname)}님 누르지 말아주세요.',
                        view=self.view))
                return
            await ctx.send(f'메모장으로 진행합니다.')
            await interaction.message.delete()

    class UndoButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label=f"명단 수정하기", style=discord.ButtonStyle.primary)

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user != dcpaow.normal_game_creator:
                await (interaction.response.edit_message
                       (content=f'## {get_nickname(dcpaow.normal_game_creator.nickname)}님이 누른 것만 인식합니다. '
                                f'{get_nickname(press_user.nickname)}님 누르지 말아주세요.',
                        view=self.view))
                return
            await interaction.message.delete()
            await close_normal_game(ctx, prev_summoners)

    handle_team_view = HandleTeamView()
    await ctx.send(content=f'## {get_nickname(dcpaow.normal_game_creator.nickname)}님, '
                           f'팀장 두 분의 닉네임 버튼을 눌러주세요.', view=handle_team_view)


async def choose_blue_red_game(ctx, team_head_list, members):
    await ctx.send(f'=========================================')
    # 블루팀 레드팀 고르기
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
            await choose_order_game(ctx, blue_team, red_team, members)

    blue_red_view = BlueRedView()
    await ctx.send(content=f'## {get_nickname(selected.nickname)}님, 진영을 선택해주세요.', view=blue_red_view)


async def choose_order_game(ctx, blue_team, red_team, members):
    await ctx.send(f'=========================================')
    # 선뽑 후뽑 고르기
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
            await choose_game_team(ctx, teams, order_flag if pick_type else not order_flag, members)
            return

    order_view = OrderView()
    await ctx.send(content=f'## {get_nickname(selected.nickname)}님, 뽑는 순서를 정해주세요.', view=order_view)


async def choose_game_team(ctx, teams, flag, members):
    await ctx.send(f'=========================================')

    pick_order = [flag, not flag, not flag, flag, flag, not flag, not flag, flag]

    def get_team_head(pick_order, teams):
        return teams[0][0] if pick_order[0] else teams[1][0]

    def add_member_to_team(pick_order, teams, summoner):
        if pick_order[0]:
            teams[0].append(summoner)
        else:
            teams[1].append(summoner)

    class RemainMember:
        def __init__(self, index):
            self.summoner = members[index].summoner

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
                await ctx.send(get_game_board(teams))
                await ctx.send(f'https://banpick.kr/')
                await ctx.send(f'밴픽은 위 사이트에서 진행해주시면 됩니다.')
                await ctx.send(f'## 사용자 설정 방 제목 : 롤파크 / 비밀번호 : 0921')
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


def get_game_board(teams):
    board = f'```\n'
    board += f'🟦  블루진영\n\n'
    for blue_member in teams[0]:
        board += f'{blue_member.nickname}\n'
    board += f'\n🟥  레드진영\n\n'
    for red_member in teams[1]:
        board += f'{red_member.nickname}\n'
    board += f'```'
    return board