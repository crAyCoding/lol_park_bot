import sqlite3
import channels
import functions
import lolpark
from summoner import Summoner
from bot import bot

summoners_table = 'summoners'
total_summoners_table = 'total_summoners'
aram_table = 'aram_summoners'

# 소환사 등록
async def add_summoner(summoner, is_total=False):
    conn = sqlite3.connect(lolpark.summoners_db)
    db = conn.cursor()
    try:
        table = f'total_summoners' if is_total else f'summoners'

        query = f'SELECT id FROM {table} WHERE id = ?'
        # 해당 id가 존재하는지 확인
        db.execute(query, (summoner.id,))
        result = db.fetchone()

        # id가 존재하지 않으면 삽입
        if result is None:
            insert_query = f'''
            INSERT INTO {table} (id, display_name, score, rank, normal_game_count, normal_game_win, 
            normal_game_lose, twenty_game_count, twenty_game_winner, twenty_game_final, twenty_game_win, twenty_game_lose) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            db.execute(insert_query,
                       (summoner.id, summoner.nickname, summoner.score, summoner.rank, 0, 0, 0, 0, 0, 0, 0, 0, 0))
            conn.commit()
            return True
        else:
            return False
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()
        conn.close()


# id를 통해 display_name, score, rank 값 업데이트
async def update_summoner(summoner):
    conn = sqlite3.connect(lolpark.summoners_db)
    db = conn.cursor()
    try:
        query = 'UPDATE summoners SET display_name = ?, score = ?, rank = ? WHERE id = ?'
        # display_name, score, rank 등 변경 사항 기록
        db.execute(query, (summoner.nickname, summoner.score, summoner.rank, summoner.id,))
        # 변경사항 저장
        conn.commit()
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()
        conn.close()


# 데이터베이스의 특정 컬럼 값 1 증가
async def add_database_count(summoner, value: str, count=1):
    conn = sqlite3.connect(lolpark.summoners_db)
    db = conn.cursor()
    try:
        query = f'UPDATE summoners SET {value} = {value} + {count} WHERE id = ?'
        # id가 일치하는 행의 value를 1 증가
        db.execute(query, (summoner.id,))
        # 변경사항 저장
        conn.commit()
        # 업데이트된 행이 있는지 확인
        if db.rowcount == 0:
            update_log_channel = bot.get_channel(channels.RECORD_UPDATE_LOG_SERVER_ID)
            await update_log_channel.send(f"{summoner.nickname} 님을 찾을 수 없습니다.")
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()
        conn.close()


# 테이블 생성, db 파일 바꾸고 1회만 진행
def create_table():
    conn = sqlite3.connect(lolpark.summoners_db)
    db = conn.cursor()
    # users 테이블 생성
    db.execute('''
    CREATE TABLE IF NOT EXISTS summoners (
        id INTEGER NOT NULL,
        display_name TEXT NOT NULL,
        score INTEGER NOT NULL,
        rank TEXT NOT NULL,
        normal_game_count INTEGER NOT NULL,
        normal_game_win INTEGER NOT NULL,
        normal_game_lose INTEGER NOT NULL,
        twenty_game_count INTEGER NOT NULL,
        twenty_game_winner INTEGER NOT NULL,
        twenty_game_final INTEGER NOT NULL,
        twenty_game_win INTEGER NOT NULL,
        twenty_game_lose INTEGER NOT NULL
    )
    ''')
    conn.commit()
    db.close()
    conn.close()


# 데이터베이스 값 가져오기
async def get_database_value(summoner, value, is_total=False):
    conn = sqlite3.connect(lolpark.summoners_db)
    db = conn.cursor()
    try:
        if is_total:
            total_query = f'SELECT COALESCE(s.{value}, 0) + t.{value} AS total_value FROM total_summoners AS t LEFT JOIN summoners AS s ON s.id = t.id WHERE t.id = ?;'
            db.execute(total_query, (summoner.id,))
            total_result = db.fetchone()
            if total_result:
                return total_result[0]
            else:
                return 0

        query = f'SELECT {value} FROM summoners WHERE id = ?'
        # id에 따른 game_count 조회
        db.execute(query, (summoner.id,))
        result = db.fetchone()

        # 결과 확인
        if result:
            return result[0]
        else:
            return 0

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return None
    finally:
        # 커서 및 연결 닫기
        db.close()
        conn.close()


# 내전 전적 메세지 가져오기
async def get_summoner_record_message(summoner, is_total=False):
    normal_game_count = await get_database_value(summoner, 'normal_game_count', is_total)
    normal_game_win = await get_database_value(summoner, 'normal_game_win', is_total)
    normal_game_lose = await get_database_value(summoner, 'normal_game_lose', is_total)
    twenty_game_count = await get_database_value(summoner, 'twenty_game_count', is_total)
    twenty_game_win = await get_database_value(summoner, 'twenty_game_win', is_total)
    twenty_game_lose = await get_database_value(summoner, 'twenty_game_lose', is_total)
    twenty_game_winner = await get_database_value(summoner, 'twenty_game_winner', is_total)
    twenty_game_final = await get_database_value(summoner, 'twenty_game_final', is_total)
    is_joint, game_rank = await get_summoner_game_count_rank(summoner)

    aram_count = await get_aram_value(summoner, 'count')
    aram_win = await get_aram_value(summoner, 'win')
    aram_lose = await get_aram_value(summoner, 'lose')
    is_aram_joint, aram_rank = await get_summoner_aram_count_rank(summoner)


    if not is_valid_twenty(summoner):
        return (f'### {functions.get_nickname(summoner.nickname)}\n\n'
                f'일반 내전 참여 횟수 : {normal_game_count}회\n\n'
                f'내전 횟수 3회 미만인 소환사는 전적 검색 기능을 제공하지 않습니다.')

    record_message = f''
    if is_total:
        record_message += f'## [통산 전적]\n\n'
    record_message += (f'## {functions.get_nickname(summoner.nickname)}\n\n'
                       f'### 전체 내전 참여 횟수 : {normal_game_count + twenty_game_count}회, '
                       f'{normal_game_win + normal_game_lose + twenty_game_win + twenty_game_lose}전 ')
    if not is_total:
        record_message += f"({'공동 ' if is_joint else ''}{game_rank}등) "
    record_message += f'{normal_game_win + twenty_game_win}승 {normal_game_lose + twenty_game_lose}패\n\n'
    record_message += f'일반 내전 참여 횟수 : {normal_game_count}회\n'
    record_message += (f'일반 내전 전적 : {normal_game_win + normal_game_lose}전 '
                       f'{normal_game_win}승 {normal_game_lose}패, '
                       f'승률 : {functions.calculate_win_rate(normal_game_win, normal_game_lose)}\n\n')
    if twenty_game_count > 0:
        record_message += (f'20인 내전 참여 횟수 : {twenty_game_count}회\n'
                           f'20인 내전 우승 횟수 : {twenty_game_winner}회, '
                           f'우승 확률 : '
                           f'{functions.calculate_win_rate(twenty_game_winner, twenty_game_count - twenty_game_winner)}'
                           f'\n'
                           f'20인 내전 결승 진출 횟수 : {twenty_game_final}회, '
                           f'결승 진출 확률 : '
                           f'{functions.calculate_win_rate(twenty_game_final, twenty_game_count - twenty_game_final)}'
                           f'\n'
                           f'20인 내전 전적 : {twenty_game_win + twenty_game_lose}전 '
                           f'{twenty_game_win}승 {twenty_game_lose}패,'
                           f'승률 : {functions.calculate_win_rate(twenty_game_win, twenty_game_lose)}\n\n')
    if aram_count > 0:
        record_message += (f'### 칼바람 내전 참여 횟수 : {aram_count}회\n'
                           f'칼바람 내전 전적 : {aram_win + aram_lose}전 '
                           f'({"공동 " if is_aram_joint else ""}{aram_rank}등), '
                           f'{aram_win}승 {aram_lose}패 '
                           f'승률 : {functions.calculate_win_rate(aram_win, aram_lose)}\n\n')

    return record_message


# 내전 승/패 기록
async def record_game_win_lose(teams, value, team_1_win_count, team_2_win_count):
    for summoner in teams[0]:
        await add_database_count(summoner, f'{value}_win', team_1_win_count)
        await add_database_count(summoner, f'{value}_lose', team_2_win_count)
    for summoner in teams[1]:
        await add_database_count(summoner, f'{value}_lose', team_1_win_count)
        await add_database_count(summoner, f'{value}_win', team_2_win_count)


# 내전 횟수 TOP 15 가져오기
def get_top_normal_game_players():
    conn = sqlite3.connect(lolpark.summoners_db)
    db = conn.cursor()

    try:
        # normal_game_count가 가장 높은 15명 가져오기
        db.execute('''
        SELECT display_name, normal_game_count, normal_game_win, normal_game_lose, twenty_game_win, twenty_game_lose
        FROM summoners
        ORDER BY (normal_game_win + normal_game_lose + twenty_game_win + twenty_game_lose) DESC
        LIMIT 15
        ''')

        top_players = db.fetchall()

        return top_players
    finally:
        conn.close()


# 일반 내전 TOP 15 메세지 가져오기
async def get_summoner_most_normal_game_message():
    most_normal_game_message = f'## 내전 악귀 명단\n\n'
    top_ten = get_top_normal_game_players()
    for index, result in enumerate(top_ten, 1):
        if index == 1:
            most_normal_game_message += (f'# 🥇 : {functions.get_nickname(result[0])}, '
                                         f'{result[1]}회 {result[2] + result[3] + result[4] + result[5]}게임\n\n')
        elif index == 2:
            most_normal_game_message += (f'## 🥈 : {functions.get_nickname(result[0])}, '
                                         f'{result[1]}회 {result[2] + result[3] + result[4] + result[5]}게임\n\n')
        elif index == 3:
            most_normal_game_message += (f'## 🥉 : {functions.get_nickname(result[0])}, '
                                         f'{result[1]}회 {result[2] + result[3] + result[4] + result[5]}게임\n\n')
        else:
            most_normal_game_message += (f'### {index}위 : {functions.get_nickname(result[0])}, '
                                         f'{result[1]}회 {result[2] + result[3] + result[4] + result[5]}게임\n\n')

    return most_normal_game_message


# 등수 가져오기 (개인용)
async def get_summoner_game_count_rank(summoner):
    conn = sqlite3.connect(lolpark.summoners_db)
    db = conn.cursor()

    try:
        db.execute('''
        SELECT normal_game_win + normal_game_lose + twenty_game_win + twenty_game_lose AS total_games
        FROM summoners
        WHERE id = ?''', (summoner.id,))

        result = db.fetchone()

        if result is None:
            print(f"No result found for summoner with ID: {summoner.id}")
            return False, 0

        total_games = result[0]

        # 나보다 게임 수가 많은 소환사 수 계산
        db.execute('''
        SELECT COUNT(*)
        FROM summoners
        WHERE normal_game_win + normal_game_lose + twenty_game_win + twenty_game_lose > ?''', (total_games,))

        higher_rank_count = db.fetchone()[0]

        # 나와 동일한 게임 수를 가진 소환사 수 계산
        db.execute('''
        SELECT COUNT(*)
        FROM summoners
        WHERE normal_game_win + normal_game_lose + twenty_game_win + twenty_game_lose = ?''', (total_games,))

        same_rank_count = db.fetchone()[0]

        # 공동 등수 계산
        rank = higher_rank_count + 1  # 더 높은 사람 수 + 1로 등수 계산
        if same_rank_count > 1:
            return True, rank  # 공동 등수가 있는 경우
        else:
            return False, rank  # 공동 등수가 없는 경우

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return False, 0
    finally:
        # 커서 및 연결 닫기
        db.close()
        conn.close()


# 20인 내전 참여 가능한지 확인 (내전 3회 이상)
def is_valid_twenty(summoner):
    conn = sqlite3.connect(lolpark.summoners_db)
    db = conn.cursor()

    try:

        pre_query = f'SELECT COALESCE(s.twenty_game_count, 0) + t.twenty_game_count AS total_value FROM total_summoners AS t LEFT JOIN summoners AS s ON s.id = t.id WHERE t.id = ?;'
        # id에 따른 game_count 조회
        db.execute(pre_query, (summoner.id,))
        pre_result = db.fetchone()

        if pre_result:
            game_count = int(pre_result[0])
            if game_count > 0:
                return True

        query = f'SELECT COALESCE(s.normal_game_count, 0) + t.normal_game_count AS total_value FROM total_summoners AS t LEFT JOIN summoners AS s ON s.id = t.id WHERE t.id = ?;'
        # id에 따른 game_count 조회
        db.execute(query, (summoner.id,))
        result = db.fetchone()

        # 결과 확인, 내전 횟수 3 이상이면 True
        if result:
            game_count = int(result[0])
            if game_count >= 3:
                return True
            else:
                return False
        else:
            return False

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return False
    finally:
        # 커서 및 연결 닫기
        db.close()
        conn.close()


# 내전 전적 메세지 가져오기
async def get_total_summoner_record_message(summoner):
    normal_game_count = await get_database_value(summoner, 'normal_game_count')
    normal_game_win = await get_database_value(summoner, 'normal_game_win')
    normal_game_lose = await get_database_value(summoner, 'normal_game_lose')
    twenty_game_count = await get_database_value(summoner, 'twenty_game_count')
    twenty_game_win = await get_database_value(summoner, 'twenty_game_win')
    twenty_game_lose = await get_database_value(summoner, 'twenty_game_lose')
    twenty_game_winner = await get_database_value(summoner, 'twenty_game_winner')
    twenty_game_final = await get_database_value(summoner, 'twenty_game_final')

    aram_count = await get_aram_value(summoner, 'count')
    aram_win = await get_aram_value(summoner, 'win')
    aram_lose = await get_aram_value(summoner, 'lose')
    is_aram_joint, aram_rank = await get_summoner_aram_count_rank(summoner)

    is_joint, game_rank = await get_summoner_game_count_rank(summoner)

    if normal_game_count < 3 and twenty_game_count == 0:
        return (f'### {functions.get_nickname(summoner.nickname)}\n\n'
                f'일반 내전 참여 횟수 : {normal_game_count}회\n\n'
                f'내전 횟수 3회 미만인 소환사는 전적 검색 기능을 제공하지 않습니다.')

    record_message = f''
    record_message += (f'## {functions.get_nickname(summoner.nickname)}\n\n'
                       f'### 전체 내전 참여 횟수 : {normal_game_count + twenty_game_count}회, '
                       f'{normal_game_win + normal_game_lose + twenty_game_win + twenty_game_lose}전 '
                       f"({'공동 ' if is_joint else ''}{game_rank}등) "
                       f'{normal_game_win + twenty_game_win}승 {normal_game_lose + twenty_game_lose}패\n\n')
    record_message += f'일반 내전 참여 횟수 : {normal_game_count}회\n'
    record_message += (f'일반 내전 전적 : {normal_game_win + normal_game_lose}전 '
                       f'{normal_game_win}승 {normal_game_lose}패, '
                       f'승률 : {functions.calculate_win_rate(normal_game_win, normal_game_lose)}\n\n')
    if twenty_game_count > 0:
        record_message += (f'20인 내전 참여 횟수 : {twenty_game_count}회\n'
                           f'20인 내전 우승 횟수 : {twenty_game_winner}회, '
                           f'우승 확률 : '
                           f'{functions.calculate_win_rate(twenty_game_winner, twenty_game_count - twenty_game_winner)}'
                           f'\n'
                           f'20인 내전 결승 진출 횟수 : {twenty_game_final}회, '
                           f'결승 진출 확률 : '
                           f'{functions.calculate_win_rate(twenty_game_final, twenty_game_count - twenty_game_final)}'
                           f'\n'
                           f'20인 내전 전적 : {twenty_game_win + twenty_game_lose}전 '
                           f'{twenty_game_win}승 {twenty_game_lose}패,'
                           f'승률 : {functions.calculate_win_rate(twenty_game_win, twenty_game_lose)}\n\n')
    if aram_count > 0:
        record_message += (f'칼바람 내전 참여 횟수 : {aram_count}회\n'
                           f'칼바람 내전 전적 : {aram_win + aram_lose}전 '
                           f'({"공동 " if is_aram_joint else ""}{aram_rank}등), '
                           f'{aram_win}승 {aram_lose}패 '
                           f'승률 : {functions.calculate_win_rate(aram_win, aram_lose)}\n\n')

    return record_message


#################################  칼바람 전용  #############################################


# 칼바람 소환사 등록
async def add_aram_summoner(summoner):
    conn = sqlite3.connect(lolpark.summoners_db)
    db = conn.cursor()
    try:
        table = aram_table

        query = f'SELECT id FROM {table} WHERE id = ?'
        # 해당 id가 존재하는지 확인
        db.execute(query, (summoner.id,))
        result = db.fetchone()

        # id가 존재하지 않으면 삽입
        if result is None:
            insert_query = f'''
            INSERT INTO {table} (id, nickname, count, win, lose) 
            VALUES (?, ?, ?, ?, ?)
            '''
            db.execute(insert_query,
                       (summoner.id, summoner.nickname, 0, 0, 0))
            conn.commit()
            return True
        else:
            return False
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()
        conn.close()


# id를 통해 display_name, score, rank 값 업데이트
async def update_aram_summoner(summoner):
    conn = sqlite3.connect(lolpark.summoners_db)
    db = conn.cursor()
    try:
        query = 'UPDATE aram_summoners SET nickname = ? WHERE id = ?'
        # display_name 변경 사항 기록
        db.execute(query, (summoner.nickname, summoner.id,))
        # 변경사항 저장
        conn.commit()
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()
        conn.close()


# 데이터베이스의 특정 컬럼 값 1 증가
async def add_aram_count(summoner, value: str, count=1):
    conn = sqlite3.connect(lolpark.summoners_db)
    db = conn.cursor()
    try:
        query = f'UPDATE aram_summoners SET {value} = {value} + {count} WHERE id = ?'
        # id가 일치하는 행의 value를 1 증가
        db.execute(query, (summoner.id,))
        # 변경사항 저장
        conn.commit()
        # 업데이트된 행이 있는지 확인
        if db.rowcount == 0:
            update_log_channel = bot.get_channel(channels.RECORD_UPDATE_LOG_SERVER_ID)
            await update_log_channel.send(f"{summoner.nickname} 님을 찾을 수 없습니다.")
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()
        conn.close()


# 칼바람 승/패 기록
async def record_aram_win_lose(teams, team_1_win_count, team_2_win_count):
    for summoner in teams[0]:
        await add_aram_count(summoner, f'win', team_1_win_count)
        await add_aram_count(summoner, f'lose', team_2_win_count)
    for summoner in teams[1]:
        await add_aram_count(summoner, f'lose', team_1_win_count)
        await add_aram_count(summoner, f'win', team_2_win_count)


# 칼바람 데이터 값 가져오기
async def get_aram_value(summoner, value):
    conn = sqlite3.connect(lolpark.summoners_db)
    db = conn.cursor()
    try:
        query = f'SELECT {value} FROM aram_summoners WHERE id = ?'
        # id에 따른 game_count 조회
        db.execute(query, (summoner.id,))
        result = db.fetchone()

        # 결과 확인
        if result:
            return result[0]
        else:
            return 0

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return None
    finally:
        # 커서 및 연결 닫기
        db.close()
        conn.close()


# 칼바람 등수 가져오기 (개인용)
async def get_summoner_aram_count_rank(summoner):
    conn = sqlite3.connect(lolpark.summoners_db)
    db = conn.cursor()

    try:
        db.execute('''
        SELECT win + lose AS total_games
        FROM aram_summoners
        WHERE id = ?''', (summoner.id,))

        result = db.fetchone()

        if result is None:
            print(f"No result found for summoner with ID: {summoner.id}")
            return False, 0

        total_games = result[0]

        # 나보다 게임 수가 많은 소환사 수 계산
        db.execute('''
        SELECT COUNT(*)
        FROM aram_summoners
        WHERE win + lose > ?''', (total_games,))

        higher_rank_count = db.fetchone()[0]

        # 나와 동일한 게임 수를 가진 소환사 수 계산
        db.execute('''
        SELECT COUNT(*)
        FROM aram_summoners
        WHERE win + lose = ?''', (total_games,))

        same_rank_count = db.fetchone()[0]

        # 공동 등수 계산
        rank = higher_rank_count + 1  # 더 높은 사람 수 + 1로 등수 계산
        if same_rank_count > 1:
            return True, rank  # 공동 등수가 있는 경우
        else:
            return False, rank  # 공동 등수가 없는 경우

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return False, 0
    finally:
        # 커서 및 연결 닫기
        db.close()
        conn.close()