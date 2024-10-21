import discord
import channels
import database
import lolpark
import normal_game
import managers
import functions
from summoner import Summoner
from bot import bot


async def record_normal_game_in_main(teams):

    class RecordUpdateView(discord.ui.View):
        def __init__(self, ctx, teams):
            super().__init__(timeout=86400)
            self.blue_win_count = 0
            self.red_win_count = 0
            self.add_item(BlueWinButton(self))
            self.add_item(RedWinButton(self))
            self.add_item(FinalizeButton(self, ctx, teams))
            self.add_item(ResetButton(self))

    class BlueWinButton(discord.ui.Button):
        def __init__(self, record_view):
            super().__init__(label=f"블루팀 승리 : 0", style=discord.ButtonStyle.primary)
            self.record_view = record_view

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user.id not in managers.ID_LIST:
                await interaction.response.defer()
                return
            self.record_view.blue_win_count += 1
            self.label = f"블루팀 승리 : {self.record_view.blue_win_count}"
            await interaction.response.edit_message(content=normal_game.get_game_board(teams), view=self.view)

    class RedWinButton(discord.ui.Button):
        def __init__(self, record_view):
            super().__init__(label=f"레드팀 승리 : 0", style=discord.ButtonStyle.red)
            self.record_view = record_view

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user.id not in managers.ID_LIST:
                await interaction.response.defer()
                return
            self.disabled = True
            self.record_view.red_win_count += 1
            self.label = f"레드팀 승리 : {self.record_view.red_win_count}"
            await interaction.response.edit_message(content=normal_game.get_game_board(teams), view=self.view)
            self.disabled = False

    class FinalizeButton(discord.ui.Button):
        def __init__(self, record_view, ctx, teams):
            super().__init__(label=f"이대로 확정", style=discord.ButtonStyle.green)
            self.record_view = record_view
            self.teams = teams
            self.ctx = ctx

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user.id not in managers.ID_LIST:
                await interaction.response.defer()
                return
            await interaction.message.delete()
            await database.record_normal_game(self.teams,
                                              self.record_view.blue_win_count, self.record_view.red_win_count)
            await self.ctx.send(f'내전 승/패가 기록되었습니다.')

    class ResetButton(discord.ui.Button):
        def __init__(self, record_view):
            super().__init__(label=f"초기화", style=discord.ButtonStyle.gray)
            self.record_view = record_view

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user.id not in managers.ID_LIST:
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

            # 메시지 업데이트
            await interaction.response.edit_message(content=normal_game.get_game_board(teams), view=self.view)

    normal_game_update_channel = bot.get_channel(channels.RECORD_UPDATE_SERVER_ID)
    view = RecordUpdateView(ctx=normal_game_update_channel, teams=teams)
    await normal_game_update_channel.send(content=normal_game.get_game_board(teams), view=view)


async def manually_add_summoner_win(ctx, members):
    if not (ctx.author.id == managers.MASULSA or ctx.author.id == managers.JUYE):
        return

    for member in members:
        summoner = Summoner(member)
        await database.add_normal_game_win_count(summoner, 1)
        print(f'{functions.get_nickname(summoner.nickname)}님의 승리가 추가되었습니다.')


async def manually_add_summoner_lose(ctx, members):
    if not (ctx.author.id == managers.MASULSA or ctx.author.id == managers.JUYE):
        return

    for member in members:
        summoner = Summoner(member)
        await database.add_normal_game_lose_count(summoner, 1)
        print(f'{functions.get_nickname(summoner.nickname)}님의 패배가 추가되었습니다.')


async def manually_add_teams_record(ctx, members):
    if not (ctx.author.id == managers.MASULSA or ctx.author.id == managers.JUYE):
        return

    teams = [[], []]
    for index, member in enumerate(members, 1):
        if index <= 5:
            teams[0].append(member)
        else:
            teams[1].append(member)

    await record_normal_game_in_main(teams)
