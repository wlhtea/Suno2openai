import json

import aiomysql
from fastapi import HTTPException
from tenacity import retry, stop_after_attempt, wait_random

from util.config import RETRIES
from util.logger import logger


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
            if self.pool is None:
                # 用于root账户密码新建数据库
                if self.user == 'root':
                    connection = None
                    try:
                        connection = await aiomysql.connect(
                            host=self.host,
                            port=self.port,
                            user=self.user,
                            password=self.password,
                            autocommit=True
                        )
                        async with connection.cursor() as cursor:
                            # 检查数据库是否存在
                            await cursor.execute(f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA "
                                                 f"WHERE SCHEMA_NAME = '{self.db_name}'")
                            result = await cursor.fetchone()
                            # 如果不存在则创建数据库
                            if not result:
                                await cursor.execute(f"CREATE DATABASE {self.db_name}")
                                logger.info(f"数据库 {self.db_name} 已创建.")
                    except Exception as e:
                        logger.error(f"发生错误: {e}")
                    finally:
                        if connection:
                            connection.close()

                self.pool = await aiomysql.create_pool(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    db=self.db_name,
                    maxsize=200,
                    minsize=5,
                    connect_timeout=10,
                    pool_recycle=1800
                )

                if self.pool is None:
                    logger.error("连接池创建失败，返回值为 None。")
        except Exception as e:
            logger.error(f"创建连接池时发生错误: {e}")

    # 关闭连接池
    async def close_db_pool(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()

    # 创建数据库和表
    async def create_database_and_table(self):
        await self.create_pool()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    # await cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{self.db_name}`")
                    # logger.info(f"Database `{self.db_name}` created or already exists.")
                    # await cursor.execute(f"USE `{self.user}`")
                    await cursor.execute(f"""
                        CREATE TABLE IF NOT EXISTS suno2openai (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            cookie TEXT NOT NULL,
                            songID VARCHAR(255),
                            songID2 VARCHAR(255),
                            count INT,
                            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            add_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(cookie(191))
                        )
                    """)
                    # 查询表结构，检查是否存在 add_time 列
                    await cursor.execute('''
                        SHOW COLUMNS FROM suno2openai LIKE 'add_time';
                    ''')
                    column = await cursor.fetchone()

                    if not column:
                        # 如果 add_time 列不存在，添加该列
                        await cursor.execute('''
                            ALTER TABLE suno2openai
                            ADD COLUMN add_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                        ''')
                        logger.info("成功添加 'add_time' 列。")
                    else:
                        logger.info("'add_time' 列已存在，跳过添加。")

                    await conn.commit()
                except Exception as e:
                    await conn.rollback()
                    raise HTTPException(status_code=500, detail=f"{str(e)}")

    # 获得cookie
    @retry(stop=stop_after_attempt(RETRIES + 2), wait=wait_random(min=0.10, max=0.3))
    async def get_request_cookie(self):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                try:
                    # 先查询一个不被锁定且可用的cookie
                    await cursor.execute('''
                            SELECT cookie FROM suno2openai
                            WHERE songID IS NULL AND songID2 IS NULL AND count > 0
                            ORDER BY RAND() LIMIT 1
                            LOCK IN SHARE MODE;
                        ''')
                    row = await cursor.fetchone()
                    if not row:
                        raise HTTPException(status_code=429, detail="未找到可用的suno cookie")

                    cookie = row['cookie']
                    # 开始事务
                    await conn.begin()
                    try:
                        # 第二个查询，锁定获取的cookie
                        await cursor.execute('''
                                SELECT cookie FROM suno2openai 
                                WHERE cookie = %s AND songID IS NULL AND songID2 IS NULL AND count > 0
                                LIMIT 1 FOR UPDATE;
                            ''', (cookie,))
                        row = await cursor.fetchone()
                        if not row:
                            raise HTTPException(status_code=429, detail="并发更新cookie时发生并发冲突，重试中...")

                        cookie = row['cookie']
                        # 然后更新选中的cookie
                        await cursor.execute('''
                                UPDATE suno2openai
                                SET count = count - 1, songID = %s, songID2 = %s, time = CURRENT_TIMESTAMP
                                WHERE cookie = %s AND songID IS NULL AND songID2 IS NULL AND count > 0;
                            ''', ("tmp", "tmp", cookie))
                        await conn.commit()
                        return cookie
                    except Exception as update_error:
                        raise update_error

                except aiomysql.MySQLError as mysql_error:
                    await conn.rollback()
                    if '锁等待超时' in str(mysql_error):
                        raise HTTPException(status_code=504, detail="数据库锁等待超时，请稍后再试")
                    else:
                        raise HTTPException(status_code=429, detail=f"数据库错误：{str(mysql_error)}")

                except Exception as e:
                    await conn.rollback()
                    raise HTTPException(status_code=429, detail=f"发生未知错误：{str(e)}")

    @retry(stop=stop_after_attempt(RETRIES + 2), wait=wait_random(min=0.10, max=0.3))
    async def insert_or_update_cookie(self, cookie, songID=None, songID2=None, count=0):
        await self.create_pool()
        async with self.pool.acquire() as conn:
            try:
                async with conn.cursor() as cur:
                    sql = """
                        INSERT INTO suno2openai (cookie, songID, songID2, count, add_time)
                        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                        ON DUPLICATE KEY UPDATE count = VALUES(count)
                    """
                    await cur.execute(sql, (cookie, songID, songID2, count))
                    await conn.commit()
            except Exception as e:
                await conn.rollback()
                raise HTTPException(status_code=500, detail=f"{str(e)}")

    # 删除单个cookie的songID
    @retry(stop=stop_after_attempt(RETRIES + 2), wait=wait_random(min=0.10, max=0.3))
    async def delete_song_ids(self, cookie):
        await self.create_pool()
        async with self.pool.acquire() as conn:
            try:
                # 开始事务
                await conn.begin()
                async with conn.cursor() as cur:
                    # 锁定目标行以防止其他事务修改
                    await cur.execute('''
                        SELECT cookie FROM suno2openai WHERE cookie = %s FOR UPDATE;
                    ''', (cookie,))
                    await cur.execute('''
                        UPDATE suno2openai
                        SET songID = NULL, songID2 = NULL
                        WHERE cookie = %s
                    ''', cookie)
                    await conn.commit()
            except Exception as e:
                await conn.rollback()
                raise HTTPException(status_code=500, detail=f"{str(e)}")

    # 删除所有的songID
    @retry(stop=stop_after_attempt(RETRIES + 2), wait=wait_random(min=0.10, max=0.3))
    async def delete_songIDS(self):
        await self.create_pool()
        async with self.pool.acquire() as conn:
            try:
                # 开始事务
                await conn.begin()
                async with conn.cursor() as cur:
                    # 锁定目标行以防止其他事务修改
                    await cur.execute('''
                        SELECT cookie FROM suno2openai FOR UPDATE;
                    ''')
                    await cur.execute('''
                        UPDATE suno2openai
                        SET songID = NULL, songID2 = NULL;
                    ''')
                    await conn.commit()
                    rows_updated = cur.rowcount
                    return rows_updated
            except Exception as e:
                await conn.rollback()
                raise HTTPException(status_code=500, detail=f"{str(e)}")

    # 更新cookie的count
    async def update_cookie_count(self, cookie, count_increment, update=None):
        await self.create_pool()
        async with self.pool.acquire() as conn:
            try:
                # 开始事务
                await conn.begin()
                async with conn.cursor() as cur:
                    # 锁定目标行以防止其他事务修改
                    await cur.execute('''
                        SELECT cookie FROM suno2openai WHERE cookie = %s FOR UPDATE;
                    ''', (cookie,))
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
                    await conn.commit()
            except Exception as e:
                await conn.rollback()
                raise HTTPException(status_code=500, detail=f"{str(e)}")

    async def query_cookies(self):
        await self.create_pool()
        async with self.pool.acquire() as conn:
            try:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute('SELECT * FROM suno2openai')
                    await conn.commit()
                    return await cur.fetchall()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"{str(e)}")

    async def update_song_ids_by_cookie(self, cookie, songID1, songID2):
        await self.create_pool()
        async with self.pool.acquire() as conn:
            try:
                async with conn.cursor() as cur:
                    await cur.execute('''
                        UPDATE suno2openai
                        SET count = count - 1, songID = %s, songID2 = %s, time = CURRENT_TIMESTAMP
                        WHERE cookie = %s
                    ''', (songID1, songID2, cookie))
                    await conn.commit()
            except Exception as e:
                await conn.rollback()
                raise HTTPException(status_code=500, detail=f"{str(e)}")

    # 获取所有 process 的count总和
    @retry(stop=stop_after_attempt(RETRIES + 2), wait=wait_random(min=0.10, max=0.3))
    async def get_cookies_count(self):
        await self.create_pool()
        try:
            async with self.pool.acquire() as conn:
                try:
                    async with conn.cursor(aiomysql.DictCursor) as cur:
                        await cur.execute("SELECT SUM(count) AS total_count FROM suno2openai")
                        result = await cur.fetchone()
                        await conn.commit()
                        return result['total_count'] if result['total_count'] is not None else 0
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"{str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return 0

    # 获取有效的 process 的count总和
    @retry(stop=stop_after_attempt(RETRIES + 2), wait=wait_random(min=0.10, max=0.3))
    async def get_valid_cookies_count(self):
        await self.create_pool()
        try:
            async with self.pool.acquire() as conn:
                try:
                    async with conn.cursor(aiomysql.DictCursor) as cur:
                        await cur.execute("SELECT COUNT(cookie) AS total_count FROM suno2openai WHERE count >= 0")
                        result = await cur.fetchone()
                        await conn.commit()
                        return result['total_count'] if result['total_count'] is not None else 0
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"{str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return 0

    # 获取 process
    @retry(stop=stop_after_attempt(RETRIES + 2), wait=wait_random(min=0.10, max=0.3))
    async def get_cookies(self):
        await self.create_pool()
        async with self.pool.acquire() as conn:
            try:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute("SELECT cookie FROM suno2openai")
                    await conn.commit()
                    return await cur.fetchall()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"{str(e)}")

    # 获取无效的cookies
    @retry(stop=stop_after_attempt(RETRIES + 2), wait=wait_random(min=0.10, max=0.3))
    async def get_invalid_cookies(self):
        await self.create_pool()
        async with self.pool.acquire() as conn:
            try:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute("SELECT cookie FROM suno2openai WHERE count < 0")
                    await conn.commit()
                    return await cur.fetchall()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"{str(e)}")

    # 获取 process 和 count
    @retry(stop=stop_after_attempt(RETRIES + 2), wait=wait_random(min=0.10, max=0.3))
    async def get_all_cookies(self):
        await self.create_pool()
        async with self.pool.acquire() as conn:
            try:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute("SELECT cookie, songID, songID2, count, time, add_time FROM suno2openai")
                    result = await cur.fetchall()
                    # 将所有字段转化为字符串
                    for row in result:
                        for key in row:
                            row[key] = str(row[key])
                    await conn.commit()
                    return json.dumps(result)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"{str(e)}")

    @retry(stop=stop_after_attempt(RETRIES + 2), wait=wait_random(min=0.10, max=0.3))
    async def get_row_cookies(self):
        try:
            await self.create_pool()
            async with self.pool.acquire() as conn:
                try:
                    async with conn.cursor(aiomysql.DictCursor) as cur:
                        await cur.execute("SELECT cookie FROM suno2openai")
                        results = await cur.fetchall()
                        cookies = []
                        for row in results:
                            cookies.append(row['cookie'])
                        await conn.commit()
                        return cookies
                except Exception as e:
                    logger.error(f"Database operation failed: {e}")
                    raise HTTPException(status_code=500, detail=f"Database operation failed: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to acquire connection pool: {e}")  # Improved logging
            raise HTTPException(status_code=500, detail=f"Failed to acquire connection pool: {str(e)}")

    # 删除相应的cookies
    @retry(stop=stop_after_attempt(RETRIES + 2), wait=wait_random(min=0.10, max=0.3))
    async def delete_cookies(self, cookie: str):
        await self.create_pool()
        async with self.pool.acquire() as conn:
            try:
                # 开始事务
                await conn.begin()
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    # 锁定目标行以防止其他事务修改
                    await cur.execute('''
                        SELECT cookie FROM suno2openai WHERE cookie = %s FOR UPDATE;
                    ''', (cookie,))
                    await cur.execute("DELETE FROM suno2openai WHERE cookie = %s", cookie)
                    await conn.commit()
                    return True
            except Exception as e:
                await conn.rollback()
                raise HTTPException(status_code=500, detail=f"{str(e)}")

# async def main():
#     db_manager = DatabaseManager('127.0.0.1', 3306, 'root', '12345678', 'WSunoAPI')
#     await db_manager.create_pool()
#     # await db_manager.create_database_and_table()
#     await db_manager.insert_cookie('example_cookie', 1, True)
#     await db_manager.update_cookie_count('example_cookie', 5)
#     await db_manager.update_cookie_working('example_cookie', False)
#     process = await db_manager.query_cookies()
#     cookie = await db_manager.get_non_working_cookie()
#
# if __name__ == "__main__":
#     asyncio.run(main())
