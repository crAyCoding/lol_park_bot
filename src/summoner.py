from functions import get_user_tier_score, get_user_rank


class Summoner:
    def __init__(self, summoner):
        self.id = summoner.id
        self.nickname = summoner.display_name
        self.score = get_user_tier_score(summoner.display_name)
        self.rank = get_user_rank(summoner.display_name)

    def __eq__(self, other):
        return isinstance(other, Summoner) and self.id == other.id

    def __hash__(self):
        return hash(self.id)
