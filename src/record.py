import discord
import channels
import database
import lolpark
import normal_game
import managers
from summoner import Summoner


async def record_normal_game_in_main(ctx):
    channel_id = ctx.channel.id

    if channel_id != channels.RECORD_UPDATE_SERVER_ID:
        return None

    if lolpark.finalized_normal_game_team_list is None:
        await ctx.send('모집된 내전이 없습니다.')
        return None

    teams = lolpark.finalized_normal_game_team_list[0]

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
            self.record_view.red_win_count += 1
            self.label = f"레드팀 승리 : {self.record_view.red_win_count}"
            await interaction.response.edit_message(content=normal_game.get_game_board(teams), view=self.view)

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
            await interaction.message.delete()
            await database.record_normal_game(self.teams, self.record_view.blue_win_count, self.record_view.red_win_count)
            await self.ctx.send(f'내전 승/패가 기록되었습니다.')

    class ResetButton(discord.ui.Button):
        def __init__(self, record_view):
            super().__init__(label=f"초기화", style=discord.ButtonStyle.gray)
            self.record_view = record_view

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user.id not in managers.ID_LIST:
                await interaction.response.defer()
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

    view = RecordUpdateView(ctx=ctx, teams=teams)
    await ctx.send(content=normal_game.get_game_board(teams), view=view)

    lolpark.finalized_normal_game_team_list.pop(0)
    if not lolpark.finalized_normal_game_team_list:
        lolpark.finalized_normal_game_team_list = None


async def manually_add_summoner_win(ctx, members):
    if ctx.author.id != managers.MASULSA:
        return

    for member in members:
        summoner = Summoner(member)
        await database.add_normal_game_win_count(summoner, 1)


async def manually_add_summoner_lose(ctx, members):
    if ctx.author.id != managers.MASULSA:
        return

    for member in members:
        summoner = Summoner(member)
        await database.add_normal_game_lose_count(summoner, 1)
