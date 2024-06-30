# -*- coding:utf-8 -*-
import asyncio
import datetime
import json
import time
import warnings
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI, HTTPException, Query
from fastapi import Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.responses import StreamingResponse

from data import schemas
from data.message import response_async
from process import process_cookies
from util.config import (SQL_IP, SQL_DK, USER_NAME,
                         SQL_PASSWORD, SQL_NAME, COOKIES_PREFIX,
                         BATCH_SIZE, AUTH_KEY)
from util.logger import logger
from util.sql_uilts import DatabaseManager
from util.tool import generate_random_string_async, generate_timestamp_async

warnings.filterwarnings("ignore")

# 从环境变量中获取配置
db_manager = DatabaseManager(SQL_IP, int(SQL_DK), USER_NAME, SQL_PASSWORD, SQL_NAME)
process_cookie = process_cookies.processCookies(SQL_IP, int(SQL_DK), USER_NAME, SQL_PASSWORD, SQL_NAME)


# executor = ThreadPoolExecutor(max_workers=300, thread_name_prefix="Music_thread")


# 刷新cookies函数
async def cron_refresh_cookies():
    try:
        logger.info(f"==========================================")
        logger.info("开始刷新数据库里的 cookies.........")
        cookies = [item['cookie'] for item in await db_manager.get_cookies()]
        total_cookies = len(cookies)

        processed_count = 0
        for i in range(0, total_cookies, BATCH_SIZE):
            cookie_batch = cookies[i:i + BATCH_SIZE]
            for result in process_cookie.refresh_add_cookie(cookie_batch, BATCH_SIZE, False):
                if result:
                    processed_count += 1

        success_percentage = (processed_count / total_cookies) * 100 if total_cookies > 0 else 100
        logger.info(f"所有 Cookies 刷新完毕。{processed_count}/{total_cookies} 个成功，"
                    f"成功率：({success_percentage:.2f}%)")

    except Exception as e:
        logger.error({"刷新 cookies 出现错误": str(e)})


# 删除无效cookies
async def cron_delete_cookies():
    try:
        logger.info("开始删除数据库里的无效cookies.........")
        cookies = [item['cookie'] for item in await db_manager.get_invalid_cookies()]
        delete_tasks = []
        for cookie in cookies:
            delete_tasks.append(db_manager.delete_cookies(cookie))

        results = await asyncio.gather(*delete_tasks, return_exceptions=True)
        success_count = sum(1 for result in results if result is True)
        fail_count = len(cookies) - success_count

        logger.info(
            {"message": "无效的 Cookies 删除成功。", "成功数量": success_count, "失败数量": fail_count})
        logger.info(f"==========================================")

    except Exception as e:
        logger.error({"删除无效 cookies 出现错误": e})


# 先刷新在删除cookies
async def cron_optimize_cookies():
    await cron_refresh_cookies()
    await cron_delete_cookies()


# 初始化所有songID
async def init_delete_songID():
    try:
        rows_updated = await db_manager.delete_songIDS()
        logger.info({"message": "Cookies songIDs 更新成功！", "rows_updated": rows_updated})
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


# 生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    global db_manager
    try:
        await db_manager.create_pool()
        await db_manager.create_database_and_table()
        await init_delete_songID()
        logger.info("初始化 SQL 和 songID 成功！")
    except Exception as e:
        logger.error(f"初始化 SQL 或者 songID 失败: {str(e)}")
        raise

    # 初始化并启动 APScheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(cron_optimize_cookies, IntervalTrigger(minutes=60), id='Refresh_and_delete_run')
    scheduler.start()

    try:
        yield
    finally:
        # 停止调度器
        scheduler.shutdown(wait=True)
        # 关闭数据库连接池
        await db_manager.close_db_pool()


# FastAPI 应用初始化
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def get_root():
    return schemas.Response()


@app.post("/v1/chat/completions")
async def get_last_user_message(data: schemas.Data, authorization: str = Header(...)):
    start_time = time.time()
    content_all = ''
    if SQL_IP == '' or SQL_PASSWORD == '' or SQL_NAME == '':
        raise ValueError("BASE_URL is not set")

    try:
        await verify_auth_header(authorization)
    except HTTPException as http_exc:
        raise http_exc

    try:
        chat_id = generate_random_string_async(29)
        timeStamp = generate_timestamp_async()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"生成聊天 ID 或时间戳时出错: {str(e)}")

    last_user_content = None
    for message in reversed(data.messages):
        if message.role == "user":
            last_user_content = message.content
            break

    if last_user_content is None:
        raise HTTPException(status_code=400, detail="No user message found")

    headers = {
        'Cache-Control': 'no-cache',
        'Content-Type': 'text/event-stream',
        'Date': datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT'),
        'Server': 'uvicorn',
        'X-Accel-Buffering': 'no',
        'Transfer-Encoding': 'chunked'
    }

    try:
        # 协程处理
        return await response_async(start_time, db_manager, data, content_all,
                                    chat_id, timeStamp, last_user_content, headers)
    except HTTPException as http_exc:
        raise http_exc

    # 线程处理
    # try:
    #     future = executor.submit(start_time, request_chat, db_manager, data, content_all, chat_id, timeStamp,
    #                              last_user_content, headers)
    #     return future.result()
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=str(e))


# 授权检查
async def verify_auth_header(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")
    if authorization.strip() != f"Bearer {AUTH_KEY}":
        raise HTTPException(status_code=403, detail="Invalid authorization key")


# 获取cookies的详细详细
@app.post(f"/{COOKIES_PREFIX}/cookies")
async def get_cookies(authorization: str = Header(...), cookies_type: str = Query(None)):
    try:
        await verify_auth_header(authorization)

        if cookies_type == "list":
            cookies = await db_manager.get_row_cookies()
            return JSONResponse(
                content={
                    "cookies": cookies
                }
            )
        else:
            cookies = await db_manager.get_all_cookies()
            cookies_json = json.loads(cookies)
            valid_cookie_count = int(await db_manager.get_valid_cookies_count())
            invalid_cookie_count = len(cookies_json) - valid_cookie_count
            remaining_count = int(await db_manager.get_cookies_count())

            if remaining_count is None:
                remaining_count = 0

            logger.info({"message": "Cookies 获取成功。", "数量": len(cookies_json)})
            logger.info("有效数量: " + str(valid_cookie_count))
            logger.info("无效数量: " + str(invalid_cookie_count))
            logger.info("剩余创作音乐次数: " + str(remaining_count))

            return JSONResponse(
                content={
                    "cookie_count": len(cookies_json),
                    "valid_cookie_count": valid_cookie_count,
                    "invalid_cookie_count": invalid_cookie_count,
                    "remaining_count": remaining_count,
                    "process": cookies_json
                }
            )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.put(f"/{COOKIES_PREFIX}/cookies")
async def add_cookies(data: schemas.Cookies, authorization: str = Header(...)):
    try:
        await verify_auth_header(authorization)
        logger.info(f"==========================================")
        logger.info("开始添加数据库里的 cookies.........")
        cookies = data.cookies
        total_cookies = len(cookies)

        async def stream_results(cookies,total_cookies):
            processed_count = 0
            for i in range(0, total_cookies, BATCH_SIZE):
                cookie_batch = cookies[i:i + BATCH_SIZE]
                for result in process_cookie.refresh_add_cookie(cookie_batch, BATCH_SIZE, False):
                    if result:
                        processed_count += 1
                        # yield f"data: Cookie {processed_count}/{total_cookies} 添加成功!\n\n"
                    else:
                        logger.info(f"data: Cookie {processed_count}/{total_cookies} 添加失败!\n\n")
                        # yield f"data: Cookie {processed_count}/{total_cookies} 添加失败!\n\n"

            success_percentage = (processed_count / total_cookies) * 100 if total_cookies > 0 else 100
            logger.info(f"所有 Cookies 添加完毕。{processed_count}/{total_cookies} 个成功，"
                        f"成功率：({success_percentage:.2f}%)")
            logger.info(f"==========================================")
            # yield f"data: 所有 Cookies 添加完毕。{processed_count}/{total_cookies} 个成功，成功率：({success_percentage:.2f}%)\n\n"
            # yield f"""data:""" + ' ' + f"""[DONE]\n\n"""
            return f"所有 Cookies 添加完毕。{processed_count}/{total_cookies} 个成功，成功率：({success_percentage:.2f}%)"

        # return StreamingResponse(stream_results(cookies,total_cookies), media_type="text/event-stream")
        # return JSONResponse({"message":stream_results(cookies,total_cookies)},status_code=200)
        messageResult = await stream_results(cookies, total_cookies)
        return JSONResponse({"messages":messageResult},status_code=200)

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error({"添加cookies出现错误": str(e)})
        return JSONResponse(status_code=500, content={"添加cookies出现错误": str(e)})


# 删除cookie
@app.delete(f"/{COOKIES_PREFIX}/cookies")
async def delete_cookies(data: schemas.Cookies, authorization: str = Header(...)):
    try:
        await verify_auth_header(authorization)
        cookies = data.cookies
        delete_tasks = []
        for cookie in cookies:
            delete_tasks.append(db_manager.delete_cookies(cookie))

        results = await asyncio.gather(*delete_tasks, return_exceptions=True)
        success_count = sum(1 for result in results if result is True)
        fail_count = len(cookies) - success_count

        return JSONResponse(
            content={"message": "Cookies 成功删除！", "success_count": success_count,
                     "fail_count": fail_count})
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": e})


# 请求刷新cookies
@app.get(f"/{COOKIES_PREFIX}/refresh/cookies")
async def refresh_cookies(authorization: str = Header(...)):
    try:
        await verify_auth_header(authorization)
        logger.info(f"==========================================")
        logger.info("开始刷新数据库里的 cookies.........")
        cookies = [item['cookie'] for item in await db_manager.get_cookies()]
        total_cookies = len(cookies)

        async def stream_results():
            processed_count = 0
            for i in range(0, total_cookies, BATCH_SIZE):
                cookie_batch = cookies[i:i + BATCH_SIZE]
                for result in process_cookie.refresh_add_cookie(cookie_batch, BATCH_SIZE, False):
                    if result:
                        processed_count += 1
                        # yield f"data: Cookie {processed_count}/{total_cookies} 刷新成功!\n\n"
                    else:
                        # yield f"data: Cookie {processed_count}/{total_cookies} 刷新失败!\n\n"
                        logger.info(f"data: Cookie {processed_count}/{total_cookies} 刷新失败!\n\n")
            success_percentage = (processed_count / total_cookies) * 100 if total_cookies > 0 else 100
            logger.info(f"所有 Cookies 刷新完毕。{processed_count}/{total_cookies} 个成功，"
                        f"成功率：({success_percentage:.2f}%)")
            logger.info(f"==========================================")
            # yield f"data: 所有 Cookies 刷新完毕。{processed_count}/{total_cookies} 个成功，成功率：({success_percentage:.2f}%)\n\n"
            # yield f"""data:""" + ' ' + f"""[DONE]\n\n"""
            return f"data: 所有 Cookies 刷新完毕。{processed_count}/{total_cookies} 个成功，成功率：({success_percentage:.2f}%)\n\n"


        messgaesResultRefresh = await stream_results()
        # return StreamingResponse(stream_results(), media_type="text/event-stream")
        return JSONResponse({"messages":messgaesResultRefresh},status_code=200)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error({"刷新cookies出现错误": str(e)})
        return JSONResponse(status_code=500, content={"刷新cookies出现错误": str(e)})


# 删除cookie
@app.delete(f"/{COOKIES_PREFIX}/refresh/cookies")
async def delete_invalid_cookies(authorization: str = Header(...)):
    try:
        await verify_auth_header(authorization)
        logger.info(f"==========================================")
        logger.info("开始删除数据库里的无效cookies.........")
        cookies = [item['cookie'] for item in await db_manager.get_invalid_cookies()]
        delete_tasks = []
        for cookie in cookies:
            delete_tasks.append(db_manager.delete_cookies(cookie))

        results = await asyncio.gather(*delete_tasks, return_exceptions=True)
        success_count = sum(1 for result in results if result is True)
        fail_count = len(cookies) - success_count

        logger.info(
            {"message": "Invalid cookies 删除成功。", "成功数量": success_count, "失败数量": fail_count})
        logger.info(f"==========================================")
        return JSONResponse(
            content={"message": "无效的cookies删除成功！", "success_count": success_count,
                     "fail_count": fail_count})
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": e})


# 获取cookies的详细详细
@app.delete(f"/{COOKIES_PREFIX}/songID/cookies")
async def delete_songID(authorization: str = Header(...)):
    try:
        await verify_auth_header(authorization)
        rows_updated = await db_manager.delete_songIDS()
        return JSONResponse(
            content={"message": "Cookies songIDs 更新成功！", "rows_updated": rows_updated}
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
