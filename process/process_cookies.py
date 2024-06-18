import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from sql_uilts import DatabaseManager
from suno import SongsGen


async def cookies_task(db_manage, cookie, is_insert):
    try:
        song_gen = SongsGen(cookie)
        remaining_count = song_gen.get_limit_left()
        if remaining_count == -1 and is_insert:
            logging.info(f"该账号剩余次数: {remaining_count}，添加或刷新失败！")
            return False
        await db_manage.insert_or_update_cookie(cookie=cookie, count=remaining_count)
        return True
    except Exception as e:
        logging.error(cookie + f"，添加或刷新失败：{e}")
        return False


def fetch_limit_left_async(cookie, is_insert, sql_IP, sql_dk, user_name, sql_password, sql_name):
    result = False
    tem_db_manage = DatabaseManager(sql_IP, sql_dk, user_name, sql_password, sql_name)
    # 在当前线程的事件循环中运行任务
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(tem_db_manage.create_pool())
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(cookies_task(tem_db_manage, cookie, is_insert))
    except Exception as e:
        logging.error(cookie + f"，添加或刷新失败：{e}")
        return False
    finally:
        loop.run_until_complete(tem_db_manage.close_db_pool())
        loop.close()
        return result


def refresh_add_cookie(cookies, batch_size, is_insert, sql_IP, sql_dk, user_name, sql_password, sql_name):
    # 使用 ThreadPoolExecutor 管理多线程
    try:
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            # 提交任务到线程池
            futures = [
                executor.submit(fetch_limit_left_async, cookie, is_insert, sql_IP, sql_dk, user_name, sql_password,
                                sql_name) for cookie in cookies]
            results = []
            # 获取并处理结果
            for future in as_completed(futures):
                results.append(future.result())
            return results
    except Exception as e:
        logging.error(f"添加或刷新失败：{e}")
        return None
