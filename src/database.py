import sqlite3
import channels
import functions
import lolpark
from summoner import Summoner
from bot import bot


async def add_normal_game_win_count(summoner, count):
    if count == 0:
        return None

    conn = sqlite3.connect(lolpark.summoners_db)
    db = conn.cursor()

    try:
        # id가 일치하는 행의 game_count를 1 증가
        db.execute('''
        UPDATE summoners
        SET normal_game_win = normal_game_win + ?
        WHERE id = ?
        ''', (count, summoner.id,))

        # 변경사항 저장
        conn.commit()
        update_log_channel = bot.get_channel(channels.RECORD_UPDATE_LOG_SERVER_ID)

        # 업데이트된 행이 있는지 확인
        if db.rowcount == 0:
            await update_log_channel.send(f"{summoner.nickname} 님을 찾을 수 없습니다.")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()
        conn.close()


# 내전 패배 수 증가
async def add_normal_game_lose_count(summoner, count):
    if count == 0:
        return None

    conn = sqlite3.connect(lolpark.summoners_db)
    db = conn.cursor()

    try:
        # id가 일치하는 행의 game_count를 1 증가
        db.execute('''
        UPDATE summoners
        SET normal_game_lose = normal_game_lose + ?
        WHERE id = ?
        ''', (count, summoner.id,))

        # 변경사항 저장
        conn.commit()
        update_log_channel = bot.get_channel(channels.RECORD_UPDATE_LOG_SERVER_ID)

        # 업데이트된 행이 있는지 확인
        if db.rowcount == 0:
            await update_log_channel.send(f"{summoner.nickname} 님을 찾을 수 없습니다.")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()
        conn.close()


def add_summoner(summoner):
    conn = sqlite3.connect(lolpark.summoners_db)
    db = conn.cursor()
    try:
        # 해당 id가 존재하는지 확인
        db.execute('SELECT id FROM summoners WHERE id = ?', (summoner.id,))
        result = db.fetchone()

        # id가 존재하지 않으면 삽입
        if result is None:
            db.execute('''
            INSERT INTO summoners (id, display_name, score, rank, normal_game_count, normal_game_win, 
            normal_game_lose, twenty_game_count, twenty_game_win, twenty_game_final) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (summoner.id, summoner.nickname, summoner.score, summoner.rank, 0, 0, 0, 0, 0, 0))
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
def update_summoner(summoner):
    conn = sqlite3.connect(lolpark.summoners_db)
    db = conn.cursor()

    try:
        # id가 일치하는 행의 game_count를 1 증가
        db.execute('''
        UPDATE summoners
        SET display_name = ?, score = ?, rank = ?
        WHERE id = ?
        ''', (summoner.nickname, summoner.score, summoner.rank, summoner.id,))

        # 변경사항 저장
        conn.commit()

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()
        conn.close()


# 일반 내전 횟수 증가
async def add_normal_game_count(summoner):
    conn = sqlite3.connect(lolpark.summoners_db)
    db = conn.cursor()

    try:
        # id가 일치하는 행의 game_count를 1 증가
        db.execute('''
        UPDATE summoners
        SET normal_game_count = normal_game_count + 1
        WHERE id = ?
        ''', (summoner.id,))

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
        twenty_game_win INTEGER NOT NULL,
        twenty_game_final INTEGER NOT NULL
    )
    ''')

    conn.commit()
    db.close()
    conn.close()


# 일반 내전 승리 수 가져오기
async def get_normal_game_win_count(summoner):
    conn = sqlite3.connect(lolpark.summoners_db)
    db = conn.cursor()
    try:
        # id에 따른 game_count 조회
        db.execute('SELECT normal_game_win FROM summoners WHERE id = ?', (summoner.id,))
        result = db.fetchone()

        # 결과 확인
        if result:
            win_count = result[0]
            return win_count
        else:
            return 0

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return None
    finally:
        # 커서 및 연결 닫기
        db.close()
        conn.close()


# 일반 내전 패배 수 가져오기
async def get_normal_game_lose_count(summoner):
    conn = sqlite3.connect(lolpark.summoners_db)
    db = conn.cursor()
    try:
        # id에 따른 game_count 조회
        db.execute('SELECT normal_game_lose FROM summoners WHERE id = ?', (summoner.id,))
        result = db.fetchone()

        # 결과 확인
        if result:
            win_count = result[0]
            return win_count
        else:
            return 0

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return None
    finally:
        # 커서 및 연결 닫기
        db.close()
        conn.close()


async def get_normal_game_count(summoner):
    conn = sqlite3.connect(lolpark.summoners_db)
    db = conn.cursor()
    try:
        # id에 따른 game_count 조회
        db.execute('SELECT normal_game_count FROM summoners WHERE id = ?', (summoner.id,))
        result = db.fetchone()

        # 결과 확인
        if result:
            normal_game_count = result[0]
            return normal_game_count
        else:
            update_log_channel = bot.get_channel(channels.RECORD_UPDATE_LOG_SERVER_ID)
            await update_log_channel.send(f'{summoner.nickname} 소환사를 찾을 수 없습니다.')
            return 0

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return None
    finally:
        # 커서 및 연결 닫기
        db.close()
        conn.close()


# 내전 전적 메세지 가져오기
async def get_summoner_record_message(summoner):
    normal_game_count = await get_normal_game_count(summoner)
    normal_game_win_count = await get_normal_game_win_count(summoner)
    normal_game_lose_count = await get_normal_game_lose_count(summoner)
    is_joint, normal_game_count_rank = await get_summoner_game_count_rank(summoner)

    if normal_game_count < 5:
        return (f'### {functions.get_nickname(summoner.nickname)}\n\n'
                f'일반 내전 참여 횟수 : {normal_game_count}회\n'
                f'내전 횟수 5회 미만인 소환사는 전적 검색 기능을 제공하지 않습니다.')

    record_message = f''
    record_message += f'### {functions.get_nickname(summoner.nickname)}\n\n'
    record_message += f'일반 내전 참여 횟수 : {normal_game_count}회\n'
    record_message += (f'일반 내전 전적 : {normal_game_win_count + normal_game_lose_count}전 '
                       f'({"공동 " if is_joint else ""}{normal_game_count_rank}등) '
                       f'{normal_game_win_count}승 {normal_game_lose_count}패, '
                       f'승률 : {functions.calculate_win_rate(normal_game_win_count, normal_game_lose_count)}')

    return record_message


# 일반 내전 승/패 기록
async def record_normal_game(teams, blue_win_count, red_win_count):
    for summoner in teams[0]:
        await add_normal_game_win_count(summoner, blue_win_count)
        await add_normal_game_lose_count(summoner, red_win_count)
    for summoner in teams[1]:
        await add_normal_game_lose_count(summoner, blue_win_count)
        await add_normal_game_win_count(summoner, red_win_count)


# 내전 횟수 TOP 10 가져오기
def get_top_ten_normal_game_players():
    conn = sqlite3.connect(lolpark.summoners_db)
    db = conn.cursor()

    try:
        # normal_game_count가 가장 높은 10명 가져오기
        db.execute('''
        SELECT display_name, normal_game_count, normal_game_win, normal_game_lose
        FROM summoners
        ORDER BY (normal_game_win + normal_game_lose) DESC
        LIMIT 10
        ''')

        top_players = db.fetchall()

        return top_players
    finally:
        conn.close()


# 일반 내전 탑 텐 가져오기
async def get_summoner_most_normal_game_message():
    most_normal_game_message = f'## 내전 악귀 명단\n\n'
    top_ten = get_top_ten_normal_game_players()
    for index, result in enumerate(top_ten, 1):
        if index == 1:
            most_normal_game_message += (f'# 🥇 : {functions.get_nickname(result[0])}, '
                                         f'{result[1]}회 {result[2] + result[3]}게임\n\n')
        elif index == 2:
            most_normal_game_message += (f'## 🥈 : {functions.get_nickname(result[0])}, '
                                         f'{result[1]}회 {result[2] + result[3]}게임\n\n')
        elif index == 3:
            most_normal_game_message += (f'## 🥉 : {functions.get_nickname(result[0])}, '
                                         f'{result[1]}회 {result[2] + result[3]}게임\n\n')
        else:
            most_normal_game_message += (f'### {index}위 : {functions.get_nickname(result[0])}, '
                                         f'{result[1]}회 {result[2] + result[3]}게임\n\n')

    return most_normal_game_message


async def get_summoner_game_count_rank(summoner):
    conn = sqlite3.connect(lolpark.summoners_db)
    db = conn.cursor()

    try:
        # 현재 소환사의 총 게임 수
        db.execute('''
        SELECT normal_game_win + normal_game_lose AS total_games
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
        WHERE normal_game_win + normal_game_lose > ?''', (total_games,))

        higher_rank_count = db.fetchone()[0]

        # 나와 동일한 게임 수를 가진 소환사 수 계산
        db.execute('''
        SELECT COUNT(*)
        FROM summoners
        WHERE normal_game_win + normal_game_lose = ?''', (total_games,))

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

