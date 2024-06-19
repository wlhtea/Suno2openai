import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

from suno.suno import SongsGen
from util.logger import logger
from util.sql_uilts import DatabaseManager


class processCookies:
    def __init__(self, sql_IP, sql_dk, user_name, sql_password, sql_name):
        self.host = sql_IP
        self.port = sql_dk
        self.user = user_name
        self.password = sql_password
        self.db_name = sql_name

    @staticmethod
    # 异步任务, 添加或刷新cookie
    async def cookies_task(db_manage, cookie, is_insert):
        try:
            song_gen = SongsGen(cookie)
            remaining_count = song_gen.get_limit_left()
            if remaining_count == -1 and is_insert:
                logger.info(f"该账号剩余次数: {remaining_count}，添加或刷新失败！")
                return False
            await db_manage.insert_or_update_cookie(cookie=cookie, count=remaining_count)
            return True
        except Exception as e:
            logger.error(cookie + f"，添加或刷新失败：{e}")
            return False

    # 在当前线程的事件循环中运行任务添加或刷新cookie
    def fetch_limit_left_async(self, cookie, is_insert):
        db_manage = DatabaseManager(self.host, self.port, self.user, self.password, self.db_name)
        result = False
        #
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.cookies_task(db_manage, cookie, is_insert))
        except Exception as e:
            logger.error(cookie + f"，添加或刷新失败：{e}")
            return False
        finally:
            loop.run_until_complete(db_manage.close_db_pool())
            loop.close()
            return result

    # 添加或刷新cookie，多线程
    def refresh_add_cookie(self, cookies, batch_size, is_insert):
        # 使用 ThreadPoolExecutor 管理多线程
        try:
            with ThreadPoolExecutor(max_workers=batch_size) as executor:
                # 提交任务到线程池
                futures = [
                    executor.submit(self.fetch_limit_left_async, str(cookie).strip(), is_insert) for cookie in cookies]
                results = []
                # 获取并处理结果
                for future in as_completed(futures):
                    results.append(future.result())
                return results
        except Exception as e:
            logger.error(f"添加或刷新失败：{e}")
            return None

    # 添加cookie的函数
    @staticmethod
    async def fetch_limit_left(db_manager, cookie, is_insert: bool = False):
        try:
            song_gen = SongsGen(cookie)
            remaining_count = song_gen.get_limit_left()
            if remaining_count == -1 and is_insert:
                logger.info(f"该账号剩余次数: {remaining_count}，添加或刷新失败！")
                return False
            logger.info(f"该账号剩余次数: {remaining_count}，添加或刷新成功！")
            await db_manager.insert_or_update_cookie(cookie=cookie, count=remaining_count)
            return True
        except Exception as e:
            logger.error(cookie + f"，添加失败：{e}")
            return False

