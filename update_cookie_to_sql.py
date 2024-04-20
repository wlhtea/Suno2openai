import asyncio
import os

from sql_uilts import DatabaseManager

BASE_URL = os.getenv('BASE_URL', 'https://studio-api.suno.ai')
SESSION_ID = os.getenv('SESSION_ID', '')
SQL_name = os.getenv('SQL_name', '')
SQL_password = os.getenv('SQL_password', '')
SQL_IP = os.getenv('SQL_IP', '')
SQL_dk = os.getenv('SQL_dk', 3306)

# 从环境变量获取 cookies
COOKIE1 = os.getenv('COOKIE1', '')
COOKIE2 = os.getenv('COOKIE2', '')

# 使用列表来组织多个 cookies
COOKIES = [COOKIE1, COOKIE2]


async def fetch_limit_left(cookie, db_manager):
    # song_gen = SongsGen(cookie)

    try:
        # remaining_count = song_gen.get_limit_left()
        # print(f"Remaining count: {remaining_count}")

        await db_manager.insert_cookie(cookie, 0, False)
    except:
        print(cookie)


async def main():
    if SQL_IP == '' or SQL_password == '' or SQL_name == '':
        raise ValueError("BASE_URL is not set")
    else:
        db_manager = DatabaseManager(SQL_IP, int(SQL_dk), SQL_name, SQL_password, SQL_name)
        await db_manager.create_pool()
        tasks = [fetch_limit_left(cookie, db_manager) for cookie in cookies if cookie]
        await asyncio.gather(*tasks)
