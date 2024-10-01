def get_user_tier_score(display_name: str):
    level, score = get_user_tier(display_name)

    def get_editted_score(tier_score):
        return (tier_score // 100) * 10

    score_by_tier = {
        'C': -get_editted_score(score),
        'GM': -get_editted_score(score),
        'M': -get_editted_score(score),
        'D': score * 10,
        'E': (score * 10) + 40,
        'P': (score * 10) + 80,
        'G': (score * 10) + 120,
        'S': (score * 10) + 160,
        'B': (score * 10) + 200,
        'I': (score * 10) + 240
    }

    default_score = 300

    if level in score_by_tier:
        return default_score + score_by_tier[level]
    else:
        return 99999999


def get_user_rank(display_name: str):
    level, score = get_user_tier(display_name)
    return level


def get_user_tier(display_name: str):
    splitted_display_name = display_name.split('/')
    user_tier = splitted_display_name[1].strip()
    if user_tier[0] == '🔻' or user_tier[0] == '🔺':
        user_tier = user_tier[1:]

    user_level = user_tier[0].upper()

    if user_level == 'G' and user_tier[1].upper() == 'M':
        user_score = int(user_tier[2:])
        user_level = 'GM'
    else:
        user_score = int(user_tier[1:])

    return user_level, user_score


def get_nickname(display_name: str):
    return display_name.split('/')[0].strip()


def get_nickname_without_tag(display_name: str):
    return display_name.split('/')[0].split('#')[0].strip()


def sort_game_members(user_list: list):
    # 티어별로 정리

    challenger_users = list()
    grandmaster_users = list()
    master_users = list()
    diamond_users = list()
    emerald_users = list()
    platinum_users = list()
    gold_users = list()
    silver_users = list()
    bronze_users = list()
    iron_users = list()
    unranked_users = list()

    for user in user_list:
        id = user.id
        nickname = user.nickname
        splitted_user_profile = nickname.split('/')
        user_tier = splitted_user_profile[1].strip()
        if user_tier[0] == '🔻' or user_tier[0] == '🔺':
            user_tier = user_tier[1:]

        user_level = user_tier[0].upper()

        if user_level == 'C':
            user_score = int(user_tier[1:])
            challenger_users.append((user_score, user))

        if user_level == 'G' and user_tier[1].upper() == 'M':
            user_score = int(user_tier[2:])
            grandmaster_users.append((user_score, user))

        if user_level == 'M':
            user_score = int(user_tier[1:])
            master_users.append((user_score, user))

        if user_level == 'D':
            user_score = int(user_tier[1:])
            diamond_users.append((user_score, user))

        if user_level == 'E':
            user_score = int(user_tier[1:])
            emerald_users.append((user_score, user))

        if user_level == 'P':
            user_score = int(user_tier[1:])
            platinum_users.append((user_score, user))

        if user_level == 'G' and user_tier[1].upper() != 'M':
            user_score = int(user_tier[1:])
            gold_users.append((user_score, user))

        if user_level == 'S':
            user_score = int(user_tier[1:])
            silver_users.append((user_score, user))

        if user_level == 'B':
            user_score = int(user_tier[1:])
            bronze_users.append((user_score, user))

        if user_level == 'I':
            user_score = int(user_tier[1:])
            iron_users.append((user_score, user))

        if user_level == 'U':
            user_score = 0
            unranked_users.append((user_score, user))

    user_result = list()

    if challenger_users:
        challenger_users.sort(key=lambda pair: pair[0], reverse=True)
        for user in challenger_users:
            user_result.append(user[1])

    if grandmaster_users:
        grandmaster_users.sort(key=lambda pair: pair[0], reverse=True)
        for user in grandmaster_users:
            user_result.append(user[1])

    if master_users:
        master_users.sort(key=lambda pair: pair[0], reverse=True)
        for user in master_users:
            user_result.append(user[1])

    if diamond_users:
        diamond_users.sort(key=lambda pair: pair[0])
        for user in diamond_users:
            user_result.append(user[1])

    if emerald_users:
        emerald_users.sort(key=lambda pair: pair[0])
        for user in emerald_users:
            user_result.append(user[1])

    if platinum_users:
        platinum_users.sort(key=lambda pair: pair[0])
        for user in platinum_users:
            user_result.append(user[1])

    if gold_users:
        gold_users.sort(key=lambda pair: pair[0])
        for user in gold_users:
            user_result.append(user[1])

    if silver_users:
        silver_users.sort(key=lambda pair: pair[0])
        for user in silver_users:
            user_result.append(user[1])

    if bronze_users:
        bronze_users.sort(key=lambda pair: pair[0])
        for user in bronze_users:
            user_result.append(user[1])

    if iron_users:
        iron_users.sort(key=lambda pair: pair[0])
        for user in iron_users:
            user_result.append(user[1])

    if unranked_users:
        for user in unranked_users:
            user_result.append(user[1])

    return user_result


def get_result_sorted_by_tier(user_result: list):
    now_tier = ''
    result = ''
    result += f'=========================================\n\n'
    for user in user_result:
        nickname = user.nickname
        splitted_user_profile = nickname.split('/')
        user_tier = splitted_user_profile[1].strip()
        if user_tier[0] == '🔻' or user_tier[0] == '🔺':
            user_tier = user_tier[1:]
        user_level = user_tier[0].upper()
        if now_tier == '':
            now_tier = user_level
        elif now_tier != user_level:
            now_tier = user_level
            result += f'\n'
        result += f'{user.nickname}\n'
    result += f'\n=========================================\n'

    return result
