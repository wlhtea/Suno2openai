import aiomysql

class DatabaseManager:
    def __init__(self, host, port, user, password, db_name):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db_name = db_name
        self.pool = None

    async def create_pool(self):
        self.pool = await aiomysql.create_pool(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            db=self.db_name,
            autocommit=True
        )

    async def create_database_and_table(self):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.db_name}")
                await cursor.execute(f"USE {self.db_name}")
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cookies (
                        cookie VARCHAR(255) PRIMARY KEY,
                        count INT NOT NULL,
                        working BOOLEAN NOT NULL
                    )
                """)

    async def insert_cookie(self, cookie, count, working):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    INSERT INTO cookies (cookie, count, working)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE count = count + 1, working = %s
                """, (cookie, count, working, working))

    async def update_cookie(self, cookie, count_increment, working):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    UPDATE cookies
                    SET count = count + %s, working = %s
                    WHERE cookie = %s
                """, (count_increment, working, cookie))

    async def update_cookie_count(self, cookie, count_increment,update=None):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                if update is not None:
                    await cur.execute("""
                        UPDATE cookies
                        SET count = %s
                        WHERE cookie = %s
                    """, (count_increment, cookie))
                else:
                    await cur.execute("""
                        UPDATE cookies
                        SET count = count - %s
                        WHERE cookie = %s
                    """, (count_increment, cookie))

    async def update_cookie_working(self, cookie, working):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    UPDATE cookies
                    SET working = %s
                    WHERE cookie = %s
                """, (working, cookie))

    async def query_cookies(self):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT * FROM cookies WHERE working = TRUE")
                return await cur.fetchall()

    async def get_non_working_cookie(self):
        await self.create_pool()  # 确保连接池已创建
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT cookie FROM cookies WHERE working = FALSE LIMIT 1")
                result = await cur.fetchone()
                if result:
                    return result[0]
                else:
                    return None
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
