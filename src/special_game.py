import discord
from summoner import Summoner

async def tier_limited_game_init(ctx):

    class TierSelectView(discord.ui.View):
        def __init__(self, author):
            super().__init__()
            self.author = author  # 명령어 실행자 저장
            self.result = None  # 결과 저장
            for tier in ['M', 'D', 'E', 'P', 'G', 'S']:
                self.add_item(SelectButton(tier))

    class SelectButton(discord.ui.Button):
        def __init__(self, tier):
            tier_name = '마스터' if tier == 'M' \
                         else '다이아몬드' if tier == 'D' \
                         else '에메랄드' if tier == 'E' \
                         else '플레티넘' if tier == 'P' \
                         else '골드' if tier == 'G' \
                         else '실버'
            super().__init__(label=f"{tier_name}", style=discord.ButtonStyle.primary)
            self.tier = tier

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user != Summoner(self.view.author):
                await interaction.response.send_message(
                    "내전 연 사람만 누를 수 있습니다.", ephemeral=True
                )
                return
            
            # 결과 저장 및 View 종료
            self.view.result = self.tier
            self.view.stop()
            await interaction.message.delete()

    view = TierSelectView(ctx.author)
    await ctx.send('## 제한할 티어를 선택해주세요.', view=view)

    await view.wait()

    return view.result
