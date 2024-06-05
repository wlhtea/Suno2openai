import asyncio
import os
from suno.suno import SongsGen
from sql_uilts import DatabaseManager
BASE_URL = os.getenv('BASE_URL','https://studio-api.suno.ai')
SESSION_ID = os.getenv('SESSION_ID','')
username_name = os.getenv('USER_Name','')
SQL_name = os.getenv('SQL_name','')
SQL_password = os.getenv('SQL_password','')
SQL_IP = os.getenv('SQL_IP','')
SQL_dk = os.getenv('SQL_dk',3306)
cookies = \
    ['cookie填这里英文逗号分开','②','③']

async def fetch_limit_left(cookie,db_manager):
    song_gen = SongsGen(cookie)

    try:
        remaining_count = song_gen.get_limit_left()
        print(f"Remaining count: {remaining_count}")

        await db_manager.insert_cookie(cookie, remaining_count, False)
    except:
        print(cookie)

async def main():
    if SQL_IP == '' or SQL_password == '' or SQL_name == '':
        raise ValueError("BASE_URL is not set")
    else:
        db_manager = DatabaseManager(SQL_IP, int(SQL_dk), username_name, SQL_password, SQL_name)
        await db_manager.create_pool()
        tasks = [fetch_limit_left(cookie,db_manager) for cookie in cookies if cookie]
        await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())