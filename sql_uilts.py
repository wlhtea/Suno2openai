import random

import aiomysql


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
        if self.pool is None:
            self.pool = await aiomysql.create_pool(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                db=self.db_name,
                autocommit=True
            )

    # 创建数据库和表 
    async def create_database_and_table(self):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.db_name}")
                await cursor.execute(f"USE {self.db_name}")
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cookies (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        cookie TEXT NOT NULL,
                        count INT NOT NULL,
                        working BOOLEAN NOT NULL,
                        UNIQUE(cookie(255))
                        )
                """)

    # 插入cookie，如果存在相应的cookie，则更新count
    async def insert_cookie(self, cookie, count, working):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                sql = """
                    INSERT INTO cookies (cookie, count, working)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE count = VALUES(count)
                """
                result = await cur.execute(sql, (cookie, count, working))
                await conn.commit()
                print(f"Affected rows: {result}")

    # 更新cookie的count和working状态
    async def update_cookie(self, cookie, count_increment, working):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    UPDATE cookies
                    SET count = count + %s, working = %s
                    WHERE cookie = %s
                """, (count_increment, working, cookie))

    # 更新cookie的count，如果update为True，则更新为count_increment，否则更新为count - count_increment 
    async def update_cookie_count(self, cookie, count_increment, update=None):
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

    # 更新cookie的工作状态
    async def update_cookie_working(self, cookie, working):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    UPDATE cookies
                    SET working = %s
                    WHERE cookie = %s
                """, (working, cookie))

    # 获取工作状态的cookies   
    async def query_cookies(self):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT * FROM cookies WHERE working = TRUE")
                return await cur.fetchall()

    # 获取非工作状态且有空次数的cookies    
    async def get_non_working_cookie(self):
        await self.create_pool()  # 确保连接池已创建
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT cookie FROM cookies WHERE working = FALSE AND count > 0")
                cookies = await cur.fetchall()
                # 如果有符合条件的记录，则随机选择一个
                if cookies:
                    selected_cookie = random.choice(cookies)['cookie']
                    return selected_cookie
                else:
                    selected_cookie = None
                    print(f"出现了异常，可能是因为没有合适的cookies了......")
                    return None

    # 获取所有cookies
    async def get_cookies(self):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT cookie, count, working FROM cookies")
                return await cur.fetchall()

    # 删除相应的cookies
    async def delete_cookies(self, cookie: str):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("DELETE FROM cookies WHERE cookie = %s", cookie)
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
