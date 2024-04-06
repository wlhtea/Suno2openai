import asyncio
from suno.suno import SongsGen
from sql_uilts import DatabaseManager

cookies = \
    ['cookie','cookie']

async def fetch_limit_left(cookie,db_manager):
    song_gen = SongsGen(cookie)

    try:
        remaining_count = song_gen.get_limit_left()
        print(f"Remaining count: {remaining_count}")

        await db_manager.insert_cookie(cookie, remaining_count, False)
    except:
        print(cookie)

async def main():
    db_manager = DatabaseManager('127.0.0.1', 3306, 'root', '12345678', 'WSunoAPI')
    await db_manager.create_pool()
    tasks = [fetch_limit_left(cookie,db_manager) for cookie in cookies if cookie]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())