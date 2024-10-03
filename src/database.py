import sqlite3
import channels
import functions
from summoner import Summoner
from bot import bot


async def add_normal_game_win_count(summoner, count):
    if count == 0:
        return None

    conn = sqlite3.connect('/app/src/summoners.db')
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
        if db.rowcount > 0:
            # 정상적으로 업데이트된 경우에만 메시지 전송
            win_count = await get_normal_game_win_count(summoner)
            await update_log_channel.send(f'{functions.get_nickname(summoner.nickname)} '
                                          f'님의 일반 내전 승리 수가 업데이트 되었습니다. '
                                          f'현재 내전 승리 수 : {win_count}')
        else:
            # id를 찾을 수 없는 경우에 대한 처리 (선택 사항)
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

    conn = sqlite3.connect('/app/src/summoners.db')
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
        if db.rowcount > 0:
            # 정상적으로 업데이트된 경우에만 메시지 전송
            lose_count = await get_normal_game_lose_count(summoner)
            await update_log_channel.send(f'{functions.get_nickname(summoner.nickname)} '
                                          f'님의 일반 내전 패배 수가 업데이트 되었습니다. '
                                          f'현재 내전 승리 수 : {lose_count}')
        else:
            # id를 찾을 수 없는 경우에 대한 처리 (선택 사항)
            await update_log_channel.send(f"{summoner.nickname} 님을 찾을 수 없습니다.")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()
        conn.close()


def add_summoner(summoner):
    conn = sqlite3.connect('/app/src/summoners.db')
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
    conn = sqlite3.connect('/app/src/summoners.db')
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
    conn = sqlite3.connect('/app/src/summoners.db')
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
        update_log_channel = bot.get_channel(channels.RECORD_UPDATE_LOG_SERVER_ID)

        # 업데이트된 행이 있는지 확인
        if db.rowcount > 0:
            # 정상적으로 업데이트된 경우에만 메시지 전송
            normal_game_count = await get_normal_game_count(summoner)
            await update_log_channel.send(f'{functions.get_nickname(summoner.nickname)} '
                                          f'님의 일반 내전 횟수가 업데이트 되었습니다. '
                                          f'현재 내전 횟수 : {normal_game_count}')
        else:
            # id를 찾을 수 없는 경우에 대한 처리 (선택 사항)
            await update_log_channel.send(f"{summoner.nickname} 님을 찾을 수 없습니다.")
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()
        conn.close()


def create_table():
    conn = sqlite3.connect('/app/src/summoners.db')
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
    conn = sqlite3.connect('/app/src/summoners.db')
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


# 일반 내전 패배 수 가져오기
async def get_normal_game_lose_count(summoner):
    conn = sqlite3.connect('/app/src/summoners.db')
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


async def get_normal_game_count(summoner):
    conn = sqlite3.connect('/app/src/summoners.db')
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

    record_message = f''
    record_message += f'### {functions.get_nickname(summoner.nickname)}\n\n'
    record_message += f'일반 내전 참여 횟수 : {normal_game_count}회\n'
    record_message += (f'일반 내전 전적 : {normal_game_win_count}승 {normal_game_lose_count}패, '
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
    conn = sqlite3.connect('/app/src/summoners.db')
    db = conn.cursor()

    try:
        # normal_game_count가 가장 높은 10명 가져오기
        db.execute('''
        SELECT display_name, normal_game_count
        FROM summoners
        ORDER BY normal_game_count DESC
        LIMIT 10
        ''')

        top_players = db.fetchall()
        return top_players  # [(display_name, normal_game_count), ...]
    finally:
        conn.close()


# 일반 내전 탑 텐 가져오기
async def get_summoner_most_normal_game_message():
    most_normal_game_message = f'## 내전 악귀 명단\n\n'
    top_ten = get_top_ten_normal_game_players()
    for index, result in enumerate(top_ten):
        most_normal_game_message += f'{index + 1}위 : {result[0]}, {result[1]}회\n'

    return most_normal_game_message

