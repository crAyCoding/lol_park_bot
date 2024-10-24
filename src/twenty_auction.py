from datetime import datetime
import random
import discord
import discord.ui
import twenty_game
import record
import lolpark
import functions
from discord.ui import Button, View, Modal
from bot import bot

import channels
from summoner import Summoner


async def confirm_twenty_recruit(ctx):
    class LineView(discord.ui.View):
        def __init__(self, line_name, next_line_callback):
            super().__init__(timeout=3600)
            self.line_name = line_name
            self.next_line_callback = next_line_callback  # 다음 라인을 출력하는 콜백 함수
            for i, summoner in enumerate(lolpark.twenty_summoner_list[line_name]):
                self.add_item(EditButton(line_name, summoner.nickname, i))
            self.add_item(ConfirmButton(self))  # ConfirmButton을 View에 추가

    class EditButton(discord.ui.Button):
        def __init__(self, line_name, summoner, index):
            super().__init__(label=f"{summoner}", style=discord.ButtonStyle.gray)
            self.line_name = line_name
            self.summoner = summoner
            self.index = index

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)

            # 이미 명단에 있는지 확인
            if any(press_user in summoners for summoners in lolpark.twenty_summoner_list.values()):
                await interaction.response.defer()
                return

            # 현재 버튼에 해당하는 소환사를 press_user로 교체
            origin_summoner = lolpark.twenty_summoner_list[self.line_name][self.index]
            await interaction.followup.send(f'{functions.get_nickname(origin_summoner.nickname)}님이 '
                                            f'{functions.get_nickname(press_user.nickname)}님으로 변경되었습니다.')
            lolpark.twenty_summoner_list[self.line_name][self.index] = press_user
            updated_summoners_text = get_line_summoners_text(self.line_name)
            self.label = f"{press_user.nickname}"
            await interaction.response.edit_message(content=updated_summoners_text, view=self.view)

    class ConfirmButton(discord.ui.Button):
        def __init__(self, view):
            super().__init__(label="이대로 확정", style=discord.ButtonStyle.green)

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user != lolpark.twenty_host:
                await interaction.response.edit_message(
                    content=f'{get_line_summoners_text(self.view.line_name)}\n'
                            f'{functions.get_nickname(lolpark.twenty_host.nickname)}님만 확정할 수 있습니다. '
                            f'{functions.get_nickname(press_user.nickname)}님은 누를 수 없습니다.',
                    view=self.view)
                return

            # 현재 메시지를 삭제
            await interaction.message.delete()

            # Confirm 버튼이 눌리면 다음 라인 출력
            if self.view.next_line_callback:
                await self.view.next_line_callback()

    async def show_line(line_name, next_line_callback):
        # 특정 라인의 정보를 보여주는 함수
        view = LineView(line_name, next_line_callback=next_line_callback)
        summoners_text = get_line_summoners_text(line_name)
        await ctx.send(content=summoners_text, view=view)

    if lolpark.twenty_summoner_list is None:
        return

    line_names = lolpark.line_names

    async def show_next_line(index):
        if index < len(line_names):
            await show_line(line_names[index], next_line_callback=lambda: show_next_line(index + 1))
        else:
            await run_twenty_auction(ctx)

    # 첫 번째 라인을 출력
    await show_next_line(0)


def get_line_summoners_text(line_name):
    members_text = f'{line_name} 명단\n=========================================\n'
    for index in range(0, 4):
        members_text += f'{lolpark.twenty_summoner_list[line_name][index].nickname}\n'
    return members_text


async def run_twenty_auction(ctx):
    game_members = 20

    # 팀장 라인 번호 찾기
    team_head_line_number = twenty_game.get_team_head_number(game_members)
    # 팀장 텍스트
    team_head_lineup = twenty_game.get_team_head_lineup(team_head_line_number, game_members)
    # 팀원 텍스트
    team_user_lineup = twenty_game.get_user_lineup(team_head_line_number, game_members)

    today_title = datetime.now().strftime("%m월 %d일 20인 내전")
    auction_warning = get_auction_warning()
    warning_message = None

    class NoteView(View):
        def __init__(self, title=f'{today_title}', initial_content=team_head_lineup + team_user_lineup):
            super().__init__(timeout=21600)
            self.title = title
            self.content = initial_content

        @discord.ui.button(label="경매 시작", style=discord.ButtonStyle.green)
        async def auction_start_button(self, interaction: discord.Interaction, button: Button):
            host = Summoner(interaction.user)
            await interaction.message.delete()
            if warning_message is not None:
                await warning_message.delete()
            await twenty_auction(host, team_head_line_number, ctx)

        @discord.ui.button(label="명단 수정", style=discord.ButtonStyle.primary)
        async def edit_note_button(self, interaction: discord.Interaction, button: Button):
            await interaction.message.delete()
            if warning_message is not None:
                await warning_message.delete()
            await confirm_twenty_recruit(ctx)

    view = NoteView()
    embed = discord.Embed(title=view.title, description=view.content)
    await ctx.send(embed=embed, view=view)
    warning_message = await ctx.send(auction_warning)


async def twenty_auction(host, team_head_line_number, ctx):
    await ctx.send(f'경매를 시작합니다. 경매 진행자는 {functions.get_nickname(host.nickname)}입니다.')
    auction_summoners = lolpark.twenty_summoner_list
    for (line_name, summoners) in auction_summoners.items():
        auction_summoners[line_name] = functions.sort_game_members(summoners)

    # 경매 dict
    auction_dict = {f'{i}팀': {line: None for line in lolpark.line_names} for i in range(1, 5)}

    # 유찰 목록
    remain_summoners = {line: [] for line in lolpark.line_names}

    # 팀장 추가
    team_head_line_name = lolpark.line_names[team_head_line_number]
    # 팀장의 score는 -1로 설정
    for i, (team, _) in enumerate(auction_dict.items(), 1):
        auction_dict[team][team_head_line_name] = ((auction_summoners[team_head_line_name][i - 1]), -1)

    # 팀 남은 점수
    remain_scores = [summoner.score for summoner in auction_summoners[team_head_line_name]]

    # 경매 인원에서 팀장 삭제
    del auction_summoners[team_head_line_name]

    # 강제 종료 플래그
    end_flag = False

    # 경매 로테이션.
    while auction_summoners and not end_flag:
        available_lines = [line for line, summoners in auction_summoners.items() if summoners]

        # 경매 인원이 비어있을 경우 유찰 목록에서 다시 진행
        if not available_lines:
            auction_summoners = remain_summoners
            # 유찰 목록도 비어있을 경우 경매 종료
            if all(not v for v in remain_summoners.values()):
                break
            remain_summoners = {line: [] for line in lolpark.line_names}
            continue

        auction_result_message = await ctx.send(get_auction_result(auction_dict, remain_scores))
        auction_remain_message = await ctx.send(get_auction_remain_user(auction_summoners, remain_summoners))

        # 랜덤으로 라인을 선택
        chosen_line = random.choice(available_lines)

        # 해당 라인에서 랜덤으로 소환사 선택
        chosen_summoner = random.choice(auction_summoners[chosen_line])

        # 해당 소환사를 라인에서 삭제
        auction_summoners[chosen_line].remove(chosen_summoner)

        await ctx.send(f'### 현재 경매 대상 : [{chosen_line}] {chosen_summoner.nickname}')

        def check(message):
            if message.author.id != host.id or message.channel != ctx.channel:
                return False

            msg_content = message.content

            # 유찰 또는 종료 조건
            if msg_content in {'유찰', '종료'}:
                return True

            # 팀 번호와 점수 조건
            msg_info = msg_content.split(' ')
            if len(msg_info) == 2 and msg_info[0][0] in {'1', '2', '3', '4'}:
                score = msg_info[1]
                return score.isdigit() and int(score) >= 0 and int(score) % 10 == 0

            return False

        user_message = await ctx.bot.wait_for('message', check=check)

        if user_message.content == '유찰':
            remain_summoners[chosen_line].append(chosen_summoner)
        elif user_message.content == '종료':
            end_flag = True
        else:
            team_number = int(user_message.content.split(' ')[0][0])
            auction_score = int(user_message.content.split(' ')[1])

            auction_dict[f'{team_number}팀'][chosen_line] = (chosen_summoner, auction_score)
            remain_scores[team_number - 1] -= auction_score

            # 라인에 남은 인원이 한 명뿐인 경우
            if len(auction_summoners[chosen_line]) + len(remain_summoners[chosen_line]) == 1:
                last_summoner = (auction_summoners[chosen_line] or remain_summoners[chosen_line])[0]
                auction_summoners[chosen_line] = []
                remain_summoners[chosen_line] = []
                for team_info in auction_dict.values():
                    if team_info.get(chosen_line) is None:
                        team_info[chosen_line] = (last_summoner, 0)

        await auction_result_message.delete()
        await auction_remain_message.delete()

    if end_flag:
        await ctx.send(f'경매를 강제 종료하였습니다. !경매를 통해 재시작할 수 있습니다.')
    else:
        await ctx.send(get_auction_result(auction_dict, remain_scores))
        team_max_score = max(remain_scores)
        max_score_teams = []
        dice_winner_team = ''
        for i, score in enumerate(remain_scores):
            if score == team_max_score:
                max_score_teams.append(f'{i + 1}팀')
        if len(max_score_teams) > 1:
            is_same = True
            while is_same:
                dice_result = ''
                max_dice = -1
                for team in max_score_teams:
                    if dice_result:
                        dice_result += ', '
                    dice = random.randint(1, 6)
                    dice_result += f'{team} : {dice}'
                    if max_dice < dice:
                        max_dice = dice
                        is_same = False
                        dice_winner_team = team
                    elif max_dice == dice:
                        is_same = True
                await ctx.send(dice_result)
        else:
            dice_winner_team = max_score_teams[0]
        # 러시안 룰렛 집행
        await send_random_record_update_person(ctx, auction_dict)
        # 사람들 각자 팀 채널로 강제 이동
        await move_summoners_in_twenty(ctx, auction_dict)
        # 어디랑 붙을지 정하기
        await send_select_team_message(ctx, auction_dict, dice_winner_team)
        # 초기화
        lolpark.twenty_summoner_list = None
        lolpark.twenty_host = None


def add_auction_team_head(auction_list, team_head_line_number):
    team_head_line_name = lolpark.line_names[team_head_line_number]
    team_names = ['1팀', '2팀', '3팀', '4팀']
    sorted_team_head = functions.sort_game_members(lolpark.twenty_summoner_list[team_head_line_name])
    auction_list.update(dict(zip(team_names, sorted_team_head)))


def get_auction_result(auction_dict, remain_scores):
    auction_result = f'```\n'
    for (i, (team_number, team_info)) in enumerate(auction_dict.items()):
        auction_result += f'{team_number} ( 남은 점수 : {remain_scores[i]}점 )\n'
        for (line_name, summoner) in team_info.items():
            if summoner is None:
                auction_result += f'{line_name} : \n'
            elif summoner[1] == -1:
                auction_result += f'{line_name} : {summoner[0].nickname} [팀장]\n'
            else:
                auction_result += f'{line_name} : {summoner[0].nickname} > {summoner[1]}\n'
        auction_result += f'\n'
    auction_result += f'```'

    return auction_result


def get_auction_remain_user(auction_summoners, remain_summoners):
    remain_result = '```\n남은 유저 목록\n\n'
    for line_name in auction_summoners.keys():
        if not auction_summoners[line_name] and not remain_summoners[line_name]:
            continue
        remain_result += f'{line_name}\n'
        for auction_summoner in auction_summoners[line_name]:
            remain_result += f'{auction_summoner.nickname}\n'
        for remain_summoner in remain_summoners[line_name]:
            remain_result += f'{remain_summoner.nickname} (유찰)\n'
        remain_result += '\n'
    remain_result += '```'

    return remain_result


def get_auction_warning():
    warning_text = ''

    warning_text += (f'## 경매 시작을 누른 사람이 진행자가 됩니다. '
                     f'진행자가 아닌 경우 장난으로 경매 시작 버튼 누르지 마시길 바랍니다.\n')
    warning_text += f'진행자 및 팀장을 제외한 모든 인원은 마이크를 꺼주시길 바랍니다.\n'
    warning_text += f'경매가 시작되면 랜덤으로 한명씩 출력되며, 그 사람에 대하여 경매를 진행해주시면 됩니다.\n'
    warning_text += f'경매가 완료되면, 진행자는 채팅에 팀 번호와 경매 점수를 입력해주시면 됩니다. ex) 1팀 80\n'
    warning_text += f'라인에 남은 인원이 한 명인경우, 해당 인원은 해당 라인이 공석인 팀에 자동으로 편입됩니다.\n'
    warning_text += (f'예를 들어, 서폿 3명이 모두 뽑히고 `쓰레기` 상현 님만 남았다면 남은 팀에 상현님이 들어갑니다. '
                     f'(해당 팀에게 X를 눌러 조의를 표하십시오)\n')
    warning_text += f'유찰의 경우 자동으로 유찰 대기열에 추가되며, 경매가 종료된 이후 유찰 대기열로 경매를 추가 진행합니다.\n'
    warning_text += (f'혹여 오류가 발생했거나 입력을 잘못한 경우, `!종료`를 통해 강제 종료할 수 있습니다. '
                     f'이후 다시 `!경매`를 통해 경매를 재진행할 수 있습니다.\n')
    warning_text += f'경매를 방해하는 행위 및 장난으로 버튼을 누르는 행위에는 경고가 부여될 수 있습니다.'

    return warning_text


async def move_summoners_in_twenty(ctx, auction_dict):
    twenty_team_channel_list = [channels.AUCTION_TEAM_1_CHANNEL_ID, channels.AUCTION_TEAM_2_CHANNEL_ID,
                                channels.AUCTION_TEAM_3_CHANNEL_ID, channels.AUCTION_TEAM_4_CHANNEL_ID]
    guild = ctx.guild

    for i, (team_number, team_info) in enumerate(auction_dict.items()):
        discord_channel = bot.get_channel(twenty_team_channel_list[i])
        for (line_name, twenty_summoner) in team_info.items():
            summoner = twenty_summoner[0]
            member = guild.get_member(summoner.id)
            if member.voice is not None:
                await member.move_to(discord_channel)


async def send_random_record_update_person(ctx, auction_dict):
    team_1 = list(auction_dict['1팀'].values())
    team_2 = list(auction_dict['2팀'].values())
    team_3 = list(auction_dict['3팀'].values())
    team_4 = list(auction_dict['4팀'].values())

    team_1_person = random.choice(team_1)
    team_2_person = random.choice(team_2)
    team_3_person = random.choice(team_3)
    team_4_person = random.choice(team_4)

    await ctx.send(f'## 각 팀으로 자동 이동됩니다. 봇 오류 방지를 위해 미리 움직이지 마시길 바랍니다.'
                   f'### 이번 20인 내전 4강 결과의 스크린샷을 <#1295312942459523112> 에 첨부할 서버원입니다.\n\n'
                   f'1팀 승리 시 : <@{team_1_person[0].id}>\n'
                   f'2팀 승리 시 : <@{team_2_person[0].id}>\n'
                   f'3팀 승리 시 : <@{team_3_person[0].id}>\n'
                   f'4팀 승리 시 : <@{team_4_person[0].id}>\n'
                   f'스크린샷 업로드 후, `몇팀 vs 몇팀, 몇승 몇패` 라고 꼭 남겨주세요.\n'
                   f'### 결승 전적 기록을 위해 4강 결과는 4강 종료 직후에 올려주시길 바랍니다.'
                   f'ex) 1팀 vs 2팀, 2승 1패\n')


async def send_select_team_message(ctx, auction_dict, dice_winner_team):
    class TeamSelectionView(discord.ui.View):
        def __init__(self, auction_dict, dice_winner_team):
            super().__init__(timeout=3600)  # View의 시간 제한을 두지 않음
            dice_winner_team_head = None
            for summoner in auction_dict[dice_winner_team]:
                if summoner[1] == -1:
                    dice_winner_team_head = summoner[0]

            # dice_winner_team을 제외한 나머지 팀들의 버튼을 생성
            for team in auction_dict.keys():
                if team != dice_winner_team:
                    self.add_item(TeamButton(team, dice_winner_team, dice_winner_team_head, auction_dict))

    class TeamButton(discord.ui.Button):
        def __init__(self, team_name, dice_winner_team, dice_winner_team_head, auction_dict):
            super().__init__(label=team_name, style=discord.ButtonStyle.primary)
            self.dice_winner_team_head = dice_winner_team_head
            self.dice_winner_team = dice_winner_team
            self.auction_dict = auction_dict

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user.id != self.dice_winner_team_head:
                await interaction.response.defer()
                return
            await interaction.message.delete()
            teams_list = ['1팀', '2팀', '3팀', '4팀']
            remain_teams_list = [team for team in teams_list if team not in [dice_winner_team, self.label]]

            await interaction.response.send_message(
                f'{dice_winner_team}이 {self.label}을 선택했습니다.\n'
                f'# {dice_winner_team} vs {self.label}\n\n'
                f'# {remain_teams_list[0]} vs {remain_teams_list[1]}'
            )
            await record.record_twenty_game(self.auction_dict,
                                            self.dice_winner_team, self.label,
                                            remain_teams_list[0], remain_teams_list[1])

    team_selection_view = TeamSelectionView(auction_dict, dice_winner_team)
    await ctx.send(content=f'{dice_winner_team} 팀장님, 상대할 팀을 선택해주세요.', view=team_selection_view)
