from itertools import combinations
import random
import discord
from summoner import Summoner

async def tier_limited_game_init(ctx):
    limited_tier = await choose_limit_tier(ctx)
    up_and_down = await choose_up_and_down(ctx, limited_tier)

    return (limited_tier, up_and_down)


async def choose_limit_tier(ctx):

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


async def choose_up_and_down(ctx, limited_tier):
    class UpAndDownView(discord.ui.View):
        def __init__(self, author):
            super().__init__()
            self.author = author  # 명령어 실행자 저장
            self.result = None  # 결과 저장
            self.add_item(SelectButton('이상'))
            self.add_item(SelectButton('이하'))

    class SelectButton(discord.ui.Button):
        def __init__(self, name):
            super().__init__(label=f"{name}", style=discord.ButtonStyle.primary)
            self.selected = name

        async def callback(self, interaction: discord.Interaction):
            press_user = Summoner(interaction.user)
            if press_user != Summoner(self.view.author):
                await interaction.response.send_message(
                    "내전 연 사람만 누를 수 있습니다.", ephemeral=True
                )
                return
            
            # 결과 저장 및 View 종료
            self.view.result = True if self.selected == '이상' else False
            self.view.stop()
            await interaction.message.delete()

    view = UpAndDownView(ctx.author)
    tier_name = '마스터' if limited_tier == 'M' \
                 else '다이아몬드' if limited_tier == 'D' \
                 else '에메랄드' if limited_tier == 'E' \
                 else '플레티넘' if limited_tier == 'P' \
                 else '골드' if limited_tier == 'G' \
                 else '실버'
    await ctx.send(f'## {tier_name} 티어 기준으로 티어 제한 범위를 선택해주세요.', view=view)

    await view.wait()

    return view.result


def calculate_standard_score(limited_tier, up_and_down):
    tier_values = {
        'M': 300,
        'D': 340,
        'E': 380,
        'P': 420,
        'G': 460,
        'S': 500
    }
    if limited_tier == 'M' and not up_and_down:
        return 230
        
    return tier_values.get(limited_tier)


async def get_aram_game_team(ctx, summoners, sorted_message):

    await ctx.send(f'{sorted_message}')

    n = len(summoners)
    half_size = n // 2
    min_diff = float("inf")  # 초기값: 무한대
    best_group1, best_group2 = None, None

    # 모든 조합 탐색
    for group1_indices in combinations(range(n), half_size):
        group1 = [summoners[i] for i in group1_indices]
        group2 = [summoners[i] for i in range(n) if i not in group1_indices]

        # 두 그룹의 점수 합 계산
        group1_score = sum(s.score for s in group1)
        group2_score = sum(s.score for s in group2)
        diff = abs(group1_score - group2_score)

        # 최소 차이 업데이트
        if diff < min_diff:
            min_diff = diff
            best_group1, best_group2 = group1, group2

    return random.choice([[best_group1, best_group2], [best_group2, best_group1]])