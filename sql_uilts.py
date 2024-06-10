import logging

import aiomysql
from fastapi import HTTPException


class DatabaseManager:
    def __init__(self, host, port, user, password, db_name):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db_name = db_name
        self.pool = None

    # 创建连接池 
    async def create_pool(self):
        try:
            if not self.pool:
                self.pool = await aiomysql.create_pool(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    db=self.db_name,
                    autocommit=True,
                    maxsize=20,
                )
        except Exception as e:
            if self.user == 'root':
                connection = await aiomysql.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    autocommit=True
                )
                # 用于root账户密码新建数据库
                async with connection.cursor() as cursor:
                    await cursor.execute("CREATE DATABASE IF NOT EXISTS {}".format(self.db_name))
                await connection.close()

                self.pool = await aiomysql.create_pool(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    db=self.db_name,
                    autocommit=True,
                    maxsize=20,
                )
            else:
                logging.error(f"An error occurred: {e}")

    # 创建数据库和表
    async def create_database_and_table(self):
        await self.create_pool()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    # await cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{self.db_name}`")
                    # logging.info(f"Database `{self.db_name}` created or already exists.")
                    # await cursor.execute(f"USE `{self.user}`")
                    await cursor.execute(f"""
                        CREATE TABLE IF NOT EXISTS suno2openai (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            cookie TEXT NOT NULL,
                            songID VARCHAR(255),
                            songID2 VARCHAR(255),
                            count INT,
                            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(cookie(255))
                        )
                    """)
                    logging.info("Table `suno2openai` created or already exists.")
                except Exception as e:
                    logging.error(f"An error occurred: {e}")

    async def get_token(self):
        await self.create_pool()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute('''
                    SELECT cookie FROM suno2openai
                    WHERE songID IS NULL AND songID2 IS NULL AND count > 0
                    ORDER BY time DESC LIMIT 1
                ''')
                row = await cursor.fetchone()
        if row:
            return row[0]
        else:
            raise HTTPException(status_code=404, detail="Token not found")

    async def insert_or_update_cookie(self, cookie, songID=None, songID2=None, count=0):
        await self.create_pool()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                sql = """
                    INSERT INTO suno2openai (cookie, songID, songID2, count)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE count = VALUES(count), songID = VALUES(songID), songID2 = VALUES(songID2), 
                    time = CURRENT_TIMESTAMP
                """
                await cur.execute(sql, (cookie, songID, songID2, count))

    async def get_cookie_by_songid(self, songid):
        await self.create_pool()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute('''
                    SELECT cookie FROM suno2openai WHERE songID = %s OR songID2 = %s
                ''', (songid, songid))
                row = await cur.fetchone()
        if row:
            return row[0]
        else:
            return await self.get_token()

    async def delete_song_ids(self, songid):
        await self.create_pool()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute('''
                    UPDATE suno2openai
                    SET songID = NULL, songID2 = NULL
                    WHERE songID = %s OR songID2 = %s
                ''', (songid, songid))

    async def update_cookie_count(self, cookie, count_increment, update=None):
        await self.create_pool()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                if update is not None:
                    await cur.execute('''
                        UPDATE suno2openai
                        SET count = %s
                        WHERE cookie = %s
                    ''', (count_increment, cookie))
                else:
                    await cur.execute('''
                        UPDATE suno2openai
                        SET count = count + %s
                        WHERE cookie = %s
                    ''', (count_increment, cookie))

    async def decrement_cookie_count(self, cookie):
        await self.create_pool()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute('''
                    UPDATE suno2openai
                    SET count = count - 1
                    WHERE cookie = %s AND count > 0
                ''', (cookie,))

    async def query_cookies(self):
        await self.create_pool()
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute('SELECT * FROM suno2openai')
                return await cur.fetchall()

    async def update_song_ids_by_cookie(self, cookie, songID1, songID2):
        await self.create_pool()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute('''
                    UPDATE suno2openai
                    SET songID = %s, songID2 = %s, time = CURRENT_TIMESTAMP
                    WHERE cookie = %s
                ''', (songID1, songID2, cookie))

    # 获取所有cookies
    async def get_cookies(self):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT id, cookie, songID, songID2, count, time FROM suno2openai")
                return await cur.fetchall()

    # 删除相应的cookies
    async def delete_cookies(self, cookie: str):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("DELETE FROM suno2openai WHERE cookie = %s", cookie)
                return True

# async def main():
#     db_manager = DatabaseManager('127.0.0.1', 3306, 'root', '12345678', 'WSunoAPI')
#     await db_manager.create_pool()
#     # await db_manager.create_database_and_table()
#     await db_manager.insert_cookie('example_cookie', 1, True)
#     await db_manager.update_cookie_count('example_cookie', 5)
#     await db_manager.update_cookie_working('example_cookie', False)
#     cookies = await db_manager.query_cookies()
#     cookie = await db_manager.get_non_working_cookie()
#
# if __name__ == "__main__":
#     asyncio.run(main())
