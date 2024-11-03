import random

import discord
import channels
import database
import lolpark
import normal_game
import twenty_game
import twenty_auction
import managers
import functions
import asyncio
from summoner import Summoner
from bot import bot


async def record_normal_game(ctx, summoners, teams):
    class RecordUpdateView(discord.ui.View):
        def __init__(self, ctx, summoners, teams):
            super().__init__(timeout=86400)
            self.blue_win_count = 0
            self.red_win_count = 0
            self.summoners = summoners
            self.ctx = ctx
            self.teams = teams
            self.add_item(BlueWinButton(self))
            self.add_item(RedWinButton(self))
            self.add_item(FinalizeButton(self, ctx, teams))
            self.add_item(ResetButton(self))
            self.message = None

        async def on_timeout(self):
            # 타임아웃 시 버튼을 삭제
            self.clear_items()
            if self.message:
                await self.message.edit(
                    content=f'[기록취소]\n{normal_game.get_game_board(teams)}',
                    view=view)

    class BlueWinButton(discord.ui.Button):
        def __init__(self, record_view):
            super().__init__(label=f"블루팀 승리 : 0", style=discord.ButtonStyle.primary)
            self.record_view = record_view

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user not in self.record_view.summoners:
                await self.record_view.ctx.send(f'내전에 참여한 사람만 누를 수 있습니다. '
                                                f'{functions.get_nickname(press_user.nickname)}님 누르지 말아주세요.')
                await interaction.response.defer()
                return
            self.record_view.blue_win_count += 1
            self.label = f"블루팀 승리 : {self.record_view.blue_win_count}"
            await self.record_view.ctx.send(f'{functions.get_nickname(press_user.nickname)}님이 '
                                            f'블루팀 승리 +1 버튼을 눌렀습니다.')
            await interaction.response.edit_message(content=normal_game.get_game_board(teams), view=self.view)

    class RedWinButton(discord.ui.Button):
        def __init__(self, record_view):
            super().__init__(label=f"레드팀 승리 : 0", style=discord.ButtonStyle.red)
            self.record_view = record_view

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user not in self.record_view.summoners:
                await self.record_view.ctx.send(f'내전에 참여한 사람만 누를 수 있습니다. '
                                                f'{functions.get_nickname(press_user.nickname)}님 누르지 말아주세요.')
                await interaction.response.defer()
                return
            self.record_view.red_win_count += 1
            self.label = f"레드팀 승리 : {self.record_view.red_win_count}"
            await self.record_view.ctx.send(f'{functions.get_nickname(press_user.nickname)}님이 '
                                            f'레드팀 승리 +1 버튼을 눌렀습니다.')
            await interaction.response.edit_message(content=normal_game.get_game_board(teams), view=self.view)

    class FinalizeButton(discord.ui.Button):
        def __init__(self, record_view, ctx, teams):
            super().__init__(label=f"이대로 확정", style=discord.ButtonStyle.green)
            self.record_view = record_view
            self.teams = teams
            self.ctx = ctx

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user not in self.record_view.summoners:
                await self.record_view.ctx.send(f'내전에 참여한 사람만 누를 수 있습니다. '
                                                f'{functions.get_nickname(press_user.nickname)}님 누르지 말아주세요.')
                await interaction.response.defer()
                return
            await interaction.message.delete()
            await self.record_view.ctx.send(f'{functions.get_nickname(press_user.nickname)}님이 '
                                            f'확정 버튼을 눌렀습니다.')
            await finalize_normal_game_record(self.record_view.ctx, self.record_view.blue_win_count,
                                              self.record_view.red_win_count, self.record_view.summoners,
                                              self.record_view.teams)

    class ResetButton(discord.ui.Button):
        def __init__(self, record_view):
            super().__init__(label=f"초기화", style=discord.ButtonStyle.gray)
            self.record_view = record_view

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user not in self.record_view.summoners:
                await self.record_view.ctx.send(f'내전에 참여한 사람만 누를 수 있습니다. '
                                                f'{functions.get_nickname(press_user.nickname)}님 누르지 말아주세요.')
                await interaction.response.defer()
                return
            self.record_view.blue_win_count = 0
            self.record_view.red_win_count = 0

            # 각 버튼 라벨 초기화
            for child in self.record_view.children:
                if isinstance(child, discord.ui.Button):
                    if '블루팀' in child.label:
                        child.label = '블루팀 승리 : 0'
                    elif '레드팀' in child.label:
                        child.label = '레드팀 승리 : 0'

            await self.record_view.ctx.send(f'{functions.get_nickname(press_user.nickname)}님이 '
                                            f'초기화 버튼을 눌렀습니다.')
            # 메시지 업데이트
            await interaction.response.edit_message(content=normal_game.get_game_board(teams), view=self.view)

    view = RecordUpdateView(ctx=ctx, summoners=summoners, teams=teams)
    view.message = await ctx.send(content=normal_game.get_game_board(teams), view=view)


# 일반 내전 전적 기록 최종
async def finalize_normal_game_record(ctx, blue_win_count, red_win_count, summoners, teams):
    class RecordFinalizeView(discord.ui.View):
        def __init__(self, ctx, blue_win_count, red_win_count, summoners, teams, timeout=60):
            super().__init__(timeout=timeout)
            self.ctx = ctx
            self.blue_win_count = blue_win_count
            self.red_win_count = red_win_count
            self.summoners = summoners
            self.teams = teams
            self.remaining_time = timeout
            self.undo_button = UndoButton(self)
            self.add_item(self.undo_button)
            self.message = None

        async def start_timer(self):
            # 타이머 시작
            while self.remaining_time > 0:
                self.undo_button.label = f"결과 수정하기 (남은 시간: {self.remaining_time}초)"
                if self.message:
                    await self.message.edit(view=self)  # 버튼의 라벨 업데이트
                await asyncio.sleep(1)
                self.remaining_time -= 1
            await self.on_timeout()

        async def on_timeout(self):
            # 타임아웃 시 버튼을 삭제
            self.clear_items()
            if self.message:
                await self.message.edit(
                    content=normal_game.get_result_board(teams, blue_win_count, red_win_count, is_record=True),
                    view=self)
            for team in self.teams:
                for summoner in team:
                    await database.add_database_count(summoner, 'normal_game_count')
            await database.record_game_win_lose(self.teams, 'normal_game', self.blue_win_count, self.red_win_count)
            await record_undo_for_manager(self.teams, self.blue_win_count, self.red_win_count)
            self.stop()

    class UndoButton(discord.ui.Button):
        def __init__(self, finalize_view):
            super().__init__(label=f"결과 수정하기 (남은 시간: {finalize_view.remaining_time}초)",
                             style=discord.ButtonStyle.primary)
            self.finalize_view = finalize_view

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user not in self.finalize_view.summoners:
                await self.finalize_view.ctx.send(
                    f'내전에 참여한 사람만 누를 수 있습니다. {functions.get_nickname(press_user.nickname)}님 누르지 말아주세요.'
                )
                await interaction.response.defer()
                return
            await self.finalize_view.ctx.send(f'{functions.get_nickname(press_user.nickname)}님이 결과 수정 버튼을 눌렀습니다.')
            await interaction.message.delete()
            await record_normal_game(self.finalize_view.ctx, self.finalize_view.summoners, self.finalize_view.teams)

    finalize_view = RecordFinalizeView(ctx, blue_win_count, red_win_count, summoners, teams)
    finalize_view.message = await ctx.send(
        content=normal_game.get_result_board(teams, blue_win_count, red_win_count), view=finalize_view
    )
    await finalize_view.start_timer()  # 타이머 시작


async def manually_add_summoner_win_lose(ctx, members, is_win):
    if not (ctx.author.id == managers.MASULSA or ctx.author.id == managers.JUYE):
        return

    for member in members:
        summoner = Summoner(member)
        result_type = 'normal_game_win' if is_win else 'normal_game_lose'
        result_text = '승리' if is_win else '패배'

        await database.add_database_count(summoner, result_type)
        await ctx.send(f'{functions.get_nickname(summoner.nickname)}님의 {result_text}가 추가되었습니다.')


# 일반 내전 기록 수동 추가
async def manually_add_teams_record(ctx, members):
    if not (ctx.author.id == managers.MASULSA or ctx.author.id == managers.JUYE):
        return

    guild = ctx.guild
    masulsa = Summoner(guild.get_member(managers.MASULSA))
    juye = Summoner(guild.get_member(managers.JUYE))

    teams = [[], []]
    summoners = [masulsa, juye]
    for index, member in enumerate(members, 1):
        summoner = Summoner(member)
        summoners.append(summoner)
        if index <= 5:
            teams[0].append(summoner)
        else:
            teams[1].append(summoner)
    await record_normal_game(ctx, summoners, teams)


# 일반 내전 전적 기록 수정용(관리자용)
async def record_undo_for_manager(teams, prev_blue_win_count, prev_red_win_count):
    class RecordUndoView(discord.ui.View):
        def __init__(self, ctx, teams, prev_blue_win_count, prev_red_win_count):
            super().__init__(timeout=43200)
            self.blue_win_count = 0
            self.red_win_count = 0
            self.prev_blue_win_count = prev_blue_win_count
            self.prev_red_win_count = prev_red_win_count
            self.ctx = ctx
            self.teams = teams
            self.add_item(BlueWinButton(self))
            self.add_item(RedWinButton(self))
            self.add_item(FinalizeButton(self, ctx, teams))
            self.add_item(ResetButton(self))
            self.message = None

        async def on_timeout(self):
            # 타임아웃 시 버튼을 삭제
            self.clear_items()
            if self.message:
                await self.message.edit(
                    content=f'{normal_game.get_result_board(self.teams, self.prev_blue_win_count, self.prev_red_win_count, is_record=True)}',
                    view=self)

    class BlueWinButton(discord.ui.Button):
        def __init__(self, undo_view):
            super().__init__(label=f"블루팀 승리 : 0", style=discord.ButtonStyle.primary)
            self.undo_view = undo_view

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            self.undo_view.blue_win_count += 1
            self.label = f"블루팀 승리 : {self.undo_view.blue_win_count}"
            await self.undo_view.ctx.send(f'{functions.get_nickname(press_user.nickname)}님이 '
                                          f'블루팀 승리 +1 버튼을 눌렀습니다.')
            await interaction.response.edit_message(
                content=f'{normal_game.get_result_board(self.undo_view.teams, self.undo_view.prev_blue_win_count, self.undo_view.prev_red_win_count, is_record=True)}',
                view=self.view)

    class RedWinButton(discord.ui.Button):
        def __init__(self, undo_view):
            super().__init__(label=f"레드팀 승리 : 0", style=discord.ButtonStyle.red)
            self.undo_view = undo_view

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            self.undo_view.red_win_count += 1
            self.label = f"레드팀 승리 : {self.undo_view.red_win_count}"
            await self.undo_view.ctx.send(f'{functions.get_nickname(press_user.nickname)}님이 '
                                          f'레드팀 승리 +1 버튼을 눌렀습니다.')
            await interaction.response.edit_message(
                content=f'{normal_game.get_result_board(self.undo_view.teams, self.undo_view.prev_blue_win_count, self.undo_view.prev_red_win_count, is_record=True)}',
                view=self.view)

    class FinalizeButton(discord.ui.Button):
        def __init__(self, undo_view, ctx, teams):
            super().__init__(label=f"이대로 수정", style=discord.ButtonStyle.green)
            self.undo_view = undo_view
            self.teams = teams
            self.ctx = ctx

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            self.view.clear_items()
            await self.undo_view.ctx.send(f'{functions.get_nickname(press_user.nickname)}님이 '
                                          f'이대로 수정 버튼을 눌렀습니다.')
            await interaction.response.edit_message(
                content=f'{normal_game.get_result_board(self.undo_view.teams, self.undo_view.blue_win_count, self.undo_view.red_win_count, is_record=True)}',
                view=self.view)
            for team, win_count, lose_count in zip(self.teams,
                                                   [self.undo_view.blue_win_count, self.undo_view.red_win_count],
                                                   [self.undo_view.red_win_count, self.undo_view.blue_win_count]):
                prev_win_count = -self.undo_view.prev_blue_win_count if team == self.teams[
                    0] else -self.undo_view.prev_red_win_count
                prev_lose_count = -self.undo_view.prev_red_win_count if team == self.teams[
                    0] else -self.undo_view.prev_blue_win_count

                for summoner in team:
                    await database.add_database_count(summoner, 'normal_game_win', prev_win_count)
                    await database.add_database_count(summoner, 'normal_game_win', win_count)
                    await database.add_database_count(summoner, 'normal_game_lose', prev_lose_count)
                    await database.add_database_count(summoner, 'normal_game_lose', lose_count)

            await self.undo_view.ctx.send(f'내전 기록이 수정되었습니다.')

    class ResetButton(discord.ui.Button):
        def __init__(self, undo_view):
            super().__init__(label=f"초기화", style=discord.ButtonStyle.gray)
            self.undo_view = undo_view

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            self.undo_view.blue_win_count = 0
            self.undo_view.red_win_count = 0

            # 각 버튼 라벨 초기화
            for child in self.undo_view.children:
                if isinstance(child, discord.ui.Button):
                    if '블루팀' in child.label:
                        child.label = '블루팀 승리 : 0'
                    elif '레드팀' in child.label:
                        child.label = '레드팀 승리 : 0'

            await self.undo_view.ctx.send(f'{functions.get_nickname(press_user.nickname)}님이 '
                                          f'초기화 버튼을 눌렀습니다.')
            # 메시지 업데이트
            await interaction.response.edit_message(
                content=f'{normal_game.get_result_board(self.undo_view.teams, self.undo_view.prev_blue_win_count, self.undo_view.prev_red_win_count, is_record=True)}',
                view=self.view)

    record_undo_channel = bot.get_channel(channels.RECORD_UNDO_SERVER_ID)
    view = RecordUndoView(ctx=record_undo_channel, teams=teams,
                          prev_blue_win_count=prev_blue_win_count, prev_red_win_count=prev_red_win_count)
    view.message = await record_undo_channel.send(
        content=f'{normal_game.get_result_board(teams, prev_blue_win_count, prev_red_win_count, is_record=True)}',
        view=view)


# 20인 내전 4강 기록
async def record_twenty_semi_final(ctx, team_1, team_2):
    class RecordUpdateView(discord.ui.View):
        def __init__(self, ctx, team_1, team_2, teams):
            super().__init__(timeout=86400)
            self.team_1_win_count = 0
            self.team_2_win_count = 0
            self.add_item(Team1WinButton(self, team_1, team_2))
            self.add_item(Team2WinButton(self, team_1, team_2))
            self.add_item(FinalizeButton(self, ctx, teams, team_1, team_2))
            self.add_item(ResetButton(self, team_1, team_2))

    class Team1WinButton(discord.ui.Button):
        def __init__(self, record_view, team_1, team_2):
            super().__init__(label=f"{team_1} 승 : 0", style=discord.ButtonStyle.primary)
            self.record_view = record_view
            self.team_1 = team_1
            self.team_2 = team_2

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user not in self.record_view.teams[0] and press_user not in self.record_view.teams[1]:
                await self.record_view.ctx.send(
                    f'20인 내전의 해당 게임에 참여한 사람만 누를 수 있습니다. '
                    f'{functions.get_nickname(press_user.nickname)}님 누르지 말아주세요.')
                await interaction.response.defer()
                return
            self.record_view.team_1_win_count += 1
            self.label = f"{self.team_1} 승 : {self.record_view.team_1_win_count}"
            await self.record_view.ctx.send(f'{functions.get_nickname(press_user.nickname)}님이 '
                                            f'{self.team_1}승 +1 버튼을 누르셨습니다.')
            await interaction.response.edit_message(content=twenty_game.get_twenty_game_board(self.team_1, self.team_2),
                                                    view=self.view)

    class Team2WinButton(discord.ui.Button):
        def __init__(self, record_view, team_1, team_2):
            super().__init__(label=f"{team_2} 승 : 0", style=discord.ButtonStyle.red)
            self.record_view = record_view
            self.team_1 = team_1
            self.team_2 = team_2

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user not in self.record_view.teams[0] and press_user not in self.record_view.teams[1]:
                await self.record_view.ctx.send(
                    f'20인 내전의 해당 게임에 참여한 사람만 누를 수 있습니다. '
                    f'{functions.get_nickname(press_user.nickname)}님 누르지 말아주세요.')
                await interaction.response.defer()
                return
            self.record_view.team_2_win_count += 1
            self.label = f"{self.team_2} 승 : {self.record_view.team_2_win_count}"
            await self.record_view.ctx.send(f'{functions.get_nickname(press_user.nickname)}님이 '
                                            f'{self.team_2}승 +1 버튼을 누르셨습니다.')
            await interaction.response.edit_message(content=twenty_game.get_twenty_game_board(self.team_1, self.team_2),
                                                    view=self.view)

    class FinalizeButton(discord.ui.Button):
        def __init__(self, record_view, ctx, teams, team_1, team_2):
            super().__init__(label=f"이대로 확정", style=discord.ButtonStyle.green)
            self.record_view = record_view
            self.teams = teams
            self.ctx = ctx
            self.team_1 = team_1
            self.team_2 = team_2

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user not in self.record_view.teams[0] and press_user not in self.record_view.teams[1]:
                await self.record_view.ctx.send(
                    f'20인 내전의 해당 게임에 참여한 사람만 누를 수 있습니다. '
                    f'{functions.get_nickname(press_user.nickname)}님 누르지 말아주세요.')
                await interaction.response.defer()
                return
            await interaction.message.delete()
            await self.record_view.ctx.send(f'{functions.get_nickname(press_user.nickname)}님이 '
                                            f'{self.team_1}승 +1 버튼을 누르셨습니다.')
            await finalize_twenty_game_semi_final(self.ctx, self.team_1, self.team_2, self.teams,
                                                  self.record_view.team_1_win_count, self.record_view.team_2_win_count)

    class ResetButton(discord.ui.Button):
        def __init__(self, record_view, team_1, team_2):
            super().__init__(label=f"초기화", style=discord.ButtonStyle.gray)
            self.record_view = record_view
            self.team_1 = team_1
            self.team_2 = team_2

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user not in self.record_view.teams[0] and press_user not in self.record_view.teams[1]:
                await self.record_view.ctx.send(
                    f'20인 내전의 해당 게임에 참여한 사람만 누를 수 있습니다. '
                    f'{functions.get_nickname(press_user.nickname)}님 누르지 말아주세요.')
                await interaction.response.defer()
                return
            self.record_view.team_1_win_count = 0
            self.record_view.team_2_win_count = 0

            # 각 버튼 라벨 초기화
            for child in self.record_view.children:
                if isinstance(child, discord.ui.Button):
                    if team_1 in child.label:
                        child.label = f'{team_1} 승 : 0'
                    elif team_2 in child.label:
                        child.label = f'{team_2} 승 : 0'

            # 메시지 업데이트
            await interaction.response.edit_message(content=twenty_game.get_twenty_game_board(self.team_1, self.team_2),
                                                    view=self.view)

    teams = [[summoner[0] for summoner in lolpark.auction_dict[team_1].values()],
             [summoner[0] for summoner in lolpark.auction_dict[team_2].values()]]
    semi_final_view = RecordUpdateView(ctx, team_1, team_2, teams)
    await ctx.send(content=twenty_game.get_twenty_game_board(team_1, team_2),
                   view=semi_final_view)


# 20인 4강 기록 확정
async def finalize_twenty_game_semi_final(ctx, team_1, team_2, teams, team_1_win_count, team_2_win_count):
    class RecordFinalizeView(discord.ui.View):
        def __init__(self, ctx, teams, team_1, team_2, team_1_win_count, team_2_win_count, timeout=30):
            super().__init__(timeout=timeout)
            self.ctx = ctx
            self.team_1 = team_1
            self.team_2 = team_2
            self.team_1_win_count = team_1_win_count
            self.team_2_win_count = team_2_win_count
            self.teams = teams
            self.remaining_time = timeout
            self.undo_button = UndoButton(self)
            self.add_item(self.undo_button)
            self.message = None

        async def start_timer(self):
            # 타이머 시작
            while self.remaining_time > 0:
                self.undo_button.label = f"결과 수정하기 (남은 시간: {self.remaining_time}초)"
                if self.message:
                    await self.message.edit(view=self)  # 버튼의 라벨 업데이트
                await asyncio.sleep(1)
                self.remaining_time -= 1
            await self.on_timeout()

        async def on_timeout(self):
            # 타임아웃 시 버튼을 삭제
            self.clear_items()
            if self.message:
                await self.message.edit(
                    content=twenty_game.get_result_board(self.teams, self.team_1, self.team_2,
                                                         self.team_1_win_count, self.team_2_win_count, is_record=True),
                    view=finalize_view)
            await database.record_game_win_lose(self.teams, 'twenty_game',
                                                self.team_1_win_count, self.team_2_win_count)
            if self.team_1_win_count > self.team_2_win_count:
                lolpark.twenty_final_teams.append(self.team_1)
            else:
                lolpark.twenty_final_teams.append(self.team_2)
            for team in self.teams:
                for summoner in team:
                    await database.add_database_count(summoner, 'twenty_game_count')
            if len(lolpark.twenty_final_teams) == 2:
                final_team_1 = lolpark.twenty_final_teams[0]
                final_team_2 = lolpark.twenty_final_teams[1]
                lolpark.twenty_final_teams = None
                # 20인 경매 채널에 결승 진영 선택 알림
                await twenty_auction.send_twenty_final_message(final_team_1, final_team_2)
                # 결승 기록지 출력
                await record_twenty_final(self.ctx, final_team_1, final_team_2)
            self.stop()

    class UndoButton(discord.ui.Button):
        def __init__(self, finalize_view):
            super().__init__(label=f"결과 수정하기 (남은 시간: {finalize_view.remaining_time}초)",
                             style=discord.ButtonStyle.primary)
            self.finalize_view = finalize_view

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user not in self.finalize_view.teams[0] and press_user not in self.finalize_view.teams[1]:
                await self.finalize_view.ctx.send(
                    f'20인 내전의 해당 게임에 참여한 사람만 누를 수 있습니다. '
                    f'{functions.get_nickname(press_user.nickname)}님 누르지 말아주세요.'
                )
                await interaction.response.defer()
                return
            await self.finalize_view.ctx.send(f'{functions.get_nickname(press_user.nickname)}님이 결과 수정 버튼을 눌렀습니다.')
            await interaction.message.delete()
            await record_twenty_semi_final(self.finalize_view.ctx, self.finalize_view.team_1, self.finalize_view.team_2)

    finalize_view = RecordFinalizeView(ctx, teams, team_1, team_2, team_1_win_count, team_2_win_count)
    finalize_view.message = await ctx.send(
        content=twenty_game.get_result_board(teams, team_1, team_2, team_1_win_count, team_2_win_count),
        view=finalize_view)
    await finalize_view.start_timer()  # 타이머 시작


# 20인 내전 결승 기록
async def record_twenty_final(ctx, team_1, team_2):
    class RecordUpdateView(discord.ui.View):
        def __init__(self, ctx, team_1, team_2, teams):
            super().__init__(timeout=86400)
            self.team_1_win_count = 0
            self.team_2_win_count = 0
            self.add_item(Team1WinButton(self, team_1, team_2))
            self.add_item(Team2WinButton(self, team_1, team_2))
            self.add_item(FinalizeButton(self, ctx, teams, team_1, team_2))
            self.add_item(ResetButton(self, team_1, team_2))

    class Team1WinButton(discord.ui.Button):
        def __init__(self, record_view, team_1, team_2):
            super().__init__(label=f"{team_1} 승 : 0", style=discord.ButtonStyle.primary)
            self.record_view = record_view
            self.team_1 = team_1
            self.team_2 = team_2

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user not in self.record_view.teams[0] and press_user not in self.record_view.teams[1]:
                await self.record_view.ctx.send(
                    f'20인 내전의 해당 게임에 참여한 사람만 누를 수 있습니다. '
                    f'{functions.get_nickname(press_user.nickname)}님 누르지 말아주세요.')
                await interaction.response.defer()
                return
            self.record_view.team_1_win_count += 1
            self.label = f"{self.team_1} 승 : {self.record_view.team_1_win_count}"
            await interaction.response.edit_message(content=twenty_game.get_twenty_game_board(self.team_1, self.team_2),
                                                    view=self.view)

    class Team2WinButton(discord.ui.Button):
        def __init__(self, record_view, team_1, team_2):
            super().__init__(label=f"{team_2} 승 : 0", style=discord.ButtonStyle.red)
            self.record_view = record_view
            self.team_1 = team_1
            self.team_2 = team_2

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user not in self.record_view.teams[0] and press_user not in self.record_view.teams[1]:
                await self.record_view.ctx.send(
                    f'20인 내전의 해당 게임에 참여한 사람만 누를 수 있습니다. '
                    f'{functions.get_nickname(press_user.nickname)}님 누르지 말아주세요.')
                await interaction.response.defer()
                return
            self.record_view.team_2_win_count += 1
            self.label = f"{self.team_2} 승 : {self.record_view.team_2_win_count}"
            await interaction.response.edit_message(content=twenty_game.get_twenty_game_board(self.team_1, self.team_2),
                                                    view=self.view)

    class FinalizeButton(discord.ui.Button):
        def __init__(self, record_view, ctx, teams, team_1, team_2):
            super().__init__(label=f"이대로 확정", style=discord.ButtonStyle.green)
            self.record_view = record_view
            self.teams = teams
            self.ctx = ctx
            self.team_1 = team_1
            self.team_2 = team_2

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user not in self.record_view.teams[0] and press_user not in self.record_view.teams[1]:
                await self.record_view.ctx.send(
                    f'20인 내전의 해당 게임에 참여한 사람만 누를 수 있습니다. '
                    f'{functions.get_nickname(press_user.nickname)}님 누르지 말아주세요.')
                await interaction.response.defer()
                return
            await interaction.message.delete()
            await finalize_twenty_game_final(self.record_view.ctx, self.record_view.teams, self.record_view.team_1,
                                             self.record_view.team_2, self.record_view.team_1_win_count, self.record_view.team_2_win_count)

    class ResetButton(discord.ui.Button):
        def __init__(self, record_view, team_1, team_2):
            super().__init__(label=f"초기화", style=discord.ButtonStyle.gray)
            self.record_view = record_view
            self.team_1 = team_1
            self.team_2 = team_2

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user not in self.record_view.teams[0] and press_user not in self.record_view.teams[1]:
                await self.record_view.ctx.send(
                    f'20인 내전의 해당 게임에 참여한 사람만 누를 수 있습니다. '
                    f'{functions.get_nickname(press_user.nickname)}님 누르지 말아주세요.')
                await interaction.response.defer()
                return
            self.record_view.team_1_win_count = 0
            self.record_view.team_2_win_count = 0

            # 각 버튼 라벨 초기화
            for child in self.record_view.children:
                if isinstance(child, discord.ui.Button):
                    if self.team_1 in child.label:
                        child.label = f'{self.team_1} 승 : 0'
                    elif self.team_2 in child.label:
                        child.label = f'{self.team_2} 승 : 0'

            # 메시지 업데이트
            await interaction.response.edit_message(content=twenty_game.get_twenty_game_board(self.team_1, self.team_2),
                                                    view=self.view)

    teams = [[summoner[0] for summoner in lolpark.auction_dict[team_1].values()],
             [summoner[0] for summoner in lolpark.auction_dict[team_2].values()]]

    team_1_summoners = [summoner[0] for summoner in lolpark.auction_dict[team_1].values()]
    team_2_summoners = [summoner[0] for summoner in lolpark.auction_dict[team_2].values()]

    # 결승 진출자들 결승 진출 횟수 1 증가
    for summoner in team_1_summoners:
        await database.add_database_count(summoner, 'twenty_game_final')
    for summoner in team_2_summoners:
        await database.add_database_count(summoner, 'twenty_game_final')

    final_game_view = RecordUpdateView(ctx, team_1, team_2, teams)
    await ctx.send(content=twenty_game.get_twenty_game_board(team_1, team_2),
                   view=final_game_view)


# 20인 내전 결승 기록 확정
async def finalize_twenty_game_final(ctx, teams, team_1, team_2, team_1_win_count, team_2_win_count):
    class RecordFinalizeView(discord.ui.View):
        def __init__(self, ctx, teams, team_1, team_2, team_1_win_count, team_2_win_count, timeout=60):
            super().__init__(timeout=timeout)
            self.ctx = ctx
            self.team_1 = team_1
            self.team_2 = team_2
            self.team_1_win_count = team_1_win_count
            self.team_2_win_count = team_2_win_count
            self.teams = teams
            self.remaining_time = timeout
            self.undo_button = UndoButton(self)
            self.add_item(self.undo_button)
            self.message = None

        async def start_timer(self):
            # 타이머 시작
            while self.remaining_time > 0:
                self.undo_button.label = f"결과 수정하기 (남은 시간: {self.remaining_time}초)"
                if self.message:
                    await self.message.edit(view=self)  # 버튼의 라벨 업데이트
                await asyncio.sleep(1)
                self.remaining_time -= 1
            await self.on_timeout()

        async def on_timeout(self):
            # 타임아웃 시 버튼을 삭제
            self.clear_items()
            if self.message:
                await self.message.edit(
                    content=twenty_game.get_result_board(self.teams, self.team_1, self.team_2,
                                                         self.team_1_win_count, self.team_2_win_count, is_record=True),
                    view=finalize_view)
            await database.record_game_win_lose(self.teams, 'twenty_game',
                                                self.team_1_win_count, self.team_2_win_count)
            if self.team_1_win_count > self.team_2_win_count:
                for summoner in [summoner[0] for summoner in lolpark.auction_dict[team_1].values()]:
                    await database.add_database_count(summoner, 'twenty_game_winner')
                await self.ctx.send(f'{self.team_1} 우승이 기록되었습니다. '
                                    f'{self.team_1} {self.team_1_win_count} : '
                                    f'{self.team_2_win_count} {self.team_2}')
                await twenty_auction.send_twenty_winner_message(self.team_1)
            else:
                for summoner in [summoner[0] for summoner in lolpark.auction_dict[team_2].values()]:
                    await database.add_database_count(summoner, 'twenty_game_winner')
                await self.ctx.send(f'{self.team_2} 우승이 기록되었습니다.'
                                    f'{self.team_2} {self.team_2_win_count} : '
                                    f'{self.team_1_win_count} {self.team_1}')
                await twenty_auction.send_twenty_winner_message(self.team_2)
            lolpark.auction_dict = None
            lolpark.is_twenty_game = False
            self.stop()

    class UndoButton(discord.ui.Button):
        def __init__(self, finalize_view):
            super().__init__(label=f"결과 수정하기 (남은 시간: {finalize_view.remaining_time}초)",
                             style=discord.ButtonStyle.primary)
            self.finalize_view = finalize_view

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user not in self.finalize_view.teams[0] and press_user not in self.finalize_view.teams[1]:
                await self.finalize_view.ctx.send(
                    f'20인 내전의 해당 게임에 참여한 사람만 누를 수 있습니다. '
                    f'{functions.get_nickname(press_user.nickname)}님 누르지 말아주세요.'
                )
                await interaction.response.defer()
                return
            await self.finalize_view.ctx.send(f'{functions.get_nickname(press_user.nickname)}님이 결과 수정 버튼을 눌렀습니다.')
            await interaction.message.delete()
            await record_twenty_semi_final(self.finalize_view.ctx, self.finalize_view.team_1, self.finalize_view.team_2)

    finalize_view = RecordFinalizeView(ctx, teams, team_1, team_2, team_1_win_count, team_2_win_count)
    finalize_view.message = await ctx.send(
        content=twenty_game.get_result_board(teams, team_1, team_2, team_1_win_count, team_2_win_count),
        view=finalize_view)
    await finalize_view.start_timer()  # 타이머 시작


async def manually_add_summoner_normal_game_count(ctx, members):
    if not (ctx.author.id == managers.MASULSA or ctx.author.id == managers.JUYE):
        return

    for member in members:
        summoner = Summoner(member)
        await database.add_database_count(summoner, 'normal_game_count', 1)
        print(f'{functions.get_nickname(summoner.nickname)}님의 내전 횟수가 추가되었습니다.')
