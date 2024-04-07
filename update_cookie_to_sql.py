import asyncio
import os
from suno.suno import SongsGen
from sql_uilts import DatabaseManager
BASE_URL = os.getenv('BASE_URL')
SESSION_ID = os.getenv('SESSION_ID')
SQL_name = os.getenv('SQL_name')
SQL_password = os.getenv('SQL_password')
SQL_IP = os.getenv('SQL_IP')
SQL_dk = os.getenv('SQL_dk')
cookies = \
    ['cookie1','cookie2']

async def fetch_limit_left(cookie,db_manager):
    song_gen = SongsGen(cookie)

    try:
        remaining_count = song_gen.get_limit_left()
        print(f"Remaining count: {remaining_count}")

        await db_manager.insert_cookie(cookie, remaining_count, False)
    except:
        print(cookie)

async def main():
    db_manager = DatabaseManager(SQL_IP, SQL_dk, SQL_name, SQL_password, SQL_name)
    await db_manager.create_pool()
    tasks = [fetch_limit_left(cookie,db_manager) for cookie in cookies if cookie]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())