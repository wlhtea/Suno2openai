# -*- coding:utf-8 -*-
import asyncio
import datetime
import json
import logging
import os
import random
import string
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import tiktoken
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI, HTTPException
from fastapi import Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.responses import StreamingResponse

import schemas
from cookie import suno_auth
from sql_uilts import DatabaseManager
from suno.suno import SongsGen
from utils import generate_music, get_feed

log_level_dict = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

# 配置日志记录器
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# 从环境变量中获取配置
BASE_URL = os.getenv('BASE_URL', 'https://studio-api.suno.ai')
SESSION_ID = os.getenv('SESSION_ID')
USER_NAME = os.getenv('USER_NAME', '')
SQL_NAME = os.getenv('SQL_NAME', '')
SQL_PASSWORD = os.getenv('SQL_PASSWORD', '')
SQL_IP = os.getenv('SQL_IP', '')
SQL_DK = os.getenv('SQL_DK', 3306)
COOKIES_PREFIX = os.getenv('COOKIES_PREFIX', "")
AUTH_KEY = os.getenv('AUTH_KEY', str(time.time()))
retries = int(os.getenv('RETRIES', 3))
db_manager = DatabaseManager(SQL_IP, int(SQL_DK), USER_NAME, SQL_PASSWORD, SQL_NAME)

# 记录配置信息
logging.info("==========================================")
logging.info(f"BASE_URL: {BASE_URL}")
logging.info(f"SESSION_ID: {SESSION_ID}")
logging.info(f"USER_NAME: {USER_NAME}")
logging.info(f"SQL_NAME: {SQL_NAME}")
logging.info(f"SQL_PASSWORD: {SQL_PASSWORD}")
logging.info(f"SQL_IP: {SQL_IP}")
logging.info(f"SQL_DK: {SQL_DK}")
logging.info(f"COOKIES_PREFIX: {COOKIES_PREFIX}")
logging.info(f"AUTH_KEY: {AUTH_KEY}")
logging.info(f"RETRIES: {retries}")
logging.info("==========================================")


# 刷新cookies函数
async def cron_refresh_cookies():
    try:
        logging.info(f"==========================================")
        logging.info("开始更新数据库里的 cookies.........")
        cookies = [item['cookie'] for item in await db_manager.get_cookies()]
        semaphore = asyncio.Semaphore(20)
        add_tasks = []

        async def refresh_cookie(simple_cookie):
            async with semaphore:
                return await fetch_limit_left(simple_cookie, False)

        # 使用 asyncio.create_task 而不是直接 await
        for cookie in cookies:
            add_tasks.append(refresh_cookie(cookie))

        results = await asyncio.gather(*add_tasks, return_exceptions=True)
        success_count = sum(1 for result in results if result is True)
        fail_count = len(cookies) - success_count

        logging.info({"message": "Cookies 更新成功。", "成功数量": success_count, "失败数量": fail_count})
        logging.info(f"==========================================")

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logging.error(f"刷新 cookies 时发生错误: {str(e)}")
        raise e


# 生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    global db_manager
    try:
        await db_manager.create_pool()
        await db_manager.create_database_and_table()
        logging.info("初始化 SQL 成功！")
    except Exception as e:
        logging.error(f"初始化 SQL 失败: {str(e)}")
        raise

    # 初始化并启动 APScheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(cron_refresh_cookies, IntervalTrigger(minutes=30), id='updateRefresh_run')
    scheduler.start()
    yield

    # 停止调度器
    scheduler.shutdown()


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


def generate_random_string_async(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_timestamp_async():
    return int(time.time())


def calculate_token_costs(input_prompt: str, output_prompt: str, model_name: str) -> (int, int):
    encoding = tiktoken.encoding_for_model(model_name)

    # Encode the prompts
    input_tokens = encoding.encode(input_prompt)
    output_tokens = encoding.encode(output_prompt)

    # Count the tokens
    input_token_count = len(input_tokens)
    output_token_count = len(output_tokens)

    return input_token_count, output_token_count


def check_status_complete(response):
    if not isinstance(response, list):
        raise ValueError("Invalid response format: expected a list")

    for item in response:
        if item.get("status") == "complete":
            return True
    return False


def get_clips_ids(response: json):
    try:
        if 'clips' in response and isinstance(response['clips'], list):
            clip_ids = [clip['id'] for clip in response['clips']]
            return clip_ids
        else:
            raise ValueError("Invalid response format: 'clips' key not found or is not a list.")
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON response")


# async def get_token():
#     cookieSelected = await db_manager.get_token()
#     return cookieSelected


async def Delelet_Songid(songid):
    return await db_manager.delete_song_ids(songid)


async def generate_data(chat_user_message, chat_id, timeStamp, ModelVersion, tags=None, title=None, continue_at=None,
                        continue_clip_id=None):
    cookie = None
    for attempt in range(retries):
        try:
            cookie = await db_manager.get_token()
            if cookie is None:
                raise RuntimeError("没有可用的cookie")
            logging.info(f"本次请求获取到cookie:{cookie}")
            break
        except Exception as e:
            logging.error(f"第 {attempt + 1} 次尝试获取cookie失败，错误为：{str(e)}")
            if attempt < retries - 1:
                continue
            else:
                raise RuntimeError(f"获取cookie失败cookie发生异常: {e}")

    try:
        _return_ids = False
        _return_tags = False
        _return_title = False
        _return_prompt = False
        _return_image_url = False
        _return_video_url = False
        _return_audio_url = False
        _return_Forever_url = False
        token, sid = SongsGen(cookie)._get_auth_token(w=1)

        suno_auth.set_session_id(sid)
        suno_auth.load_cookie(cookie)
        Model = "chirp-v3-0"
        if ModelVersion == "suno-v3":
            Model = "chirp-v3-0"
        elif ModelVersion == "suno-v3.5":
            Model = "chirp-v3-5"
        else:
            yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": str("请选择suno-v3 或者 suno-v3.5其中一个")}, "finish_reason": None}]})}\n\n"""
            yield f"""data:""" + ' ' + f"""[DONE]\n\n"""

        data = {
            "gpt_description_prompt": f"{chat_user_message}",
            "prompt": "",
            "mv": Model,
            "title": "",
            "tags": ""
        }

        if continue_clip_id is not None:
            data = {
                "prompt": chat_user_message,
                "mv": Model,
                "title": title,
                "tags": tags,
                "continue_at": continue_at,
                "continue_clip_id": continue_clip_id
            }

        yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"role": "assistant", "content": ""}, "finish_reason": None}]})}\n\n"""

        response = await generate_music(data=data, token=token)
        await asyncio.sleep(3)
        clip_ids = get_clips_ids(response)
        song_id_1 = clip_ids[0]
        song_id_2 = clip_ids[1]
        await db_manager.update_song_ids_by_cookie(cookie, song_id_1, song_id_2)
        await db_manager.decrement_cookie_count(cookie)

        for clip_id in clip_ids:
            # attempts = 2
            count = 0
            while True:
                # if attempts // 2 == 0:
                cookie = await db_manager.get_cookie_by_songid(clip_id)
                token, sid = SongsGen(cookie)._get_auth_token(w=1)
                now_data = await get_feed(ids=clip_id, token=token)
                try:
                    more_information_ = now_data[0]['metadata']
                except Exception as e:
                    logging.info('more_information_', e)
                    continue
                if _return_Forever_url and _return_ids and _return_tags and _return_title and _return_prompt and _return_image_url and _return_audio_url:
                    break
                if not _return_Forever_url:
                    try:
                        if check_status_complete(now_data):
                            await Delelet_Songid(clip_id)
                            Aideo_Markdown_Conetent = (f""
                                                       f"\n## 🎷 永久音乐链接\n"
                                                       f"- **🎵 歌曲1️⃣**：{'https://cdn1.suno.ai/' + clip_id + '.mp3'} \n"
                                                       f"- **🎵 歌曲2️⃣**：{'https://cdn1.suno.ai/' + song_id_2 + '.mp3'} \n")
                            Video_Markdown_Conetent = (f""
                                                       f"\n## 📺 永久视频链接\n"
                                                       f"- **🎵 视频1️⃣**：{'https://cdn1.suno.ai/' + song_id_1 + '.mp4'} \n"
                                                       f"- **🎵 视频2️⃣**：{'https://cdn1.suno.ai/' + song_id_2 + '.mp4'} \n")
                            yield str(
                                f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": Video_Markdown_Conetent}, "finish_reason": None}]})}\n\n""")
                            yield str(
                                f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": Aideo_Markdown_Conetent}, "finish_reason": None}]})}\n\n""")
                            _return_Forever_url = True
                            break
                    except Exception as e:
                        logging.info('CDN音乐链接出错', e)
                        pass

                if not _return_ids:
                    try:
                        song_id_text = (f""
                                        f"## ⭐ 歌曲ID\n"
                                        f"- **🎵 歌曲id1️⃣**：{song_id_1}\n"
                                        f"- **🎵 歌曲id2️⃣**：{song_id_2}\n")
                        yield str(
                            f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": song_id_text}, "finish_reason": None}]})}\n\n""")
                        _return_ids = True
                    except:
                        pass

                if not _return_title:
                    try:
                        title = now_data[0]["title"]
                        if title != '':
                            title_data = f"## 🧩 歌曲信息\n- **🔎 歌名**：{title} \n"
                            yield """data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": title_data}, "finish_reason": None}]})}\n\n"""
                            _return_title = True
                    except:
                        pass

                if not _return_tags:
                    try:
                        tags = more_information_["tags"]
                        if tags is not None:
                            tags_data = f"- **💄 类型**：{tags} \n"
                            yield str(
                                f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": tags_data}, "finish_reason": None}]})}\n\n""")
                            _return_tags = True
                    except:
                        pass

                if not _return_prompt:
                    try:
                        prompt = more_information_["prompt"]
                        if prompt is not None and prompt != '':
                            prompt_data = f"## 🎼 完整歌词\n```\n{prompt}\n```\n"
                            yield str(
                                f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": prompt_data}, "finish_reason": None}]})}\n\n""")
                            _return_prompt = True
                    except:
                        pass

                if not _return_image_url:
                    if now_data[0].get('image_url') is not None:
                        image_url_small_data = f"## ✨ 歌曲图片\n"
                        image_url_lager_data = f"![封面图片_大]({now_data[0]['image_large_url']}) \n## 🤩即刻享受"
                        yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": image_url_small_data}, "finish_reason": None}]})}\n\n"""
                        yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": image_url_lager_data}, "finish_reason": None}]})}\n\n"""
                        _return_image_url = True

                if not _return_audio_url:
                    if 'audio_url' in now_data[0]:
                        audio_url_ = now_data[0]['audio_url']
                        if audio_url_ != '':
                            audio_url_1 = f'https://audiopipe.suno.ai/?item_id={song_id_1}'
                            audio_url_2 = f'https://audiopipe.suno.ai/?item_id={song_id_2}'

                            audio_url_data_1 = f"\n- **📌 音乐链接1️⃣(实时)**：{audio_url_1}"
                            audio_url_data_2 = f"\n- **📌 音乐链接2️⃣(实时)**：{audio_url_2}\n## 🚀正在火速生成CDN链接（预计2-3分钟~）\n"
                            yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": audio_url_data_1}, "finish_reason": None}]})}\n\n"""
                            yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": audio_url_data_2}, "finish_reason": None}]})}\n\n"""
                            _return_audio_url = True
                if _return_ids and _return_tags and _return_title and _return_prompt and _return_image_url and _return_audio_url:
                    count += 1
                    if count % 34 == 0:
                        content_wait = "🎵\n"
                    else:
                        content_wait = "🎵"
                    yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": content_wait}, "finish_reason": None}]})}\n\n"""
                    await asyncio.sleep(2)
                # attempts += 1

        yield f"""data:""" + ' ' + f"""[DONE]\n\n"""
    except Exception as e:
        yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": str(e)}, "finish_reason": None}]})}\n\n"""
        yield f"""data:""" + ' ' + f"""[DONE]\n\n"""


@app.post("/v1/chat/completions")
async def get_last_user_message(data: schemas.Data, authorization: str = Header(...)):
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

    if not data.stream:
        try:
            async for data_string in generate_data(last_user_content, chat_id, timeStamp, data.model):
                try:
                    json_data = data_string.split('data: ')[1].strip()

                    parsed_data = json.loads(json_data)
                    content = parsed_data['choices'][0]['delta']['content']
                    content_all += content
                except:
                    pass
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"生成数据时出错: {str(e)}")

        try:
            input_tokens, output_tokens = calculate_token_costs(last_user_content, content_all, 'gpt-3.5-turbo')
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"计算 token 成本时出错: {str(e)}")

        json_string = {
            "id": f"chatcmpl-{chat_id}",
            "object": "chat.completion",
            "created": timeStamp,
            "model": "suno-v3",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content_all
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
            }
        }

        return json_string
    else:
        try:
            return StreamingResponse(generate_data(last_user_content, chat_id, timeStamp, data.model),
                                     headers=headers, media_type="text/event-stream")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"生成流式响应时出错: {str(e)}")


# 授权检查
async def verify_auth_header(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")
    if authorization.strip() != f"Bearer {AUTH_KEY}":
        raise HTTPException(status_code=403, detail="Invalid authorization key")


# 获取cookies的详细详细
@app.post(f"{COOKIES_PREFIX}/cookies")
async def get_cookies(authorization: str = Header(...)):
    try:
        await verify_auth_header(authorization)

        cookies = await db_manager.get_all_cookies()
        cookies_json = json.loads(cookies)
        valid_cookie_count = int(await db_manager.get_valid_cookies_count())
        invalid_cookie_count = len(cookies_json) - valid_cookie_count
        remaining_count = int(await db_manager.get_cookies_count())

        if remaining_count is None:
            remaining_count = 0

        logging.info({"message": "Cookies 获取成功。", "数量": len(cookies_json)})
        logging.info("有效数量: " + str(valid_cookie_count))
        logging.info("无效数量: " + str(invalid_cookie_count))
        logging.info("剩余创作音乐次数: " + str(remaining_count))

        return JSONResponse(
            content={
                "cookie_count": len(cookies_json),
                "valid_cookie_count": valid_cookie_count,
                "invalid_cookie_count": invalid_cookie_count,
                "remaining_count": remaining_count,
                "cookies": cookies_json
            }
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# 添加cookies
@app.put(f"{COOKIES_PREFIX}/cookies")
async def add_cookies(data: schemas.Cookies, authorization: str = Header(...)):
    try:
        await verify_auth_header(authorization)
        cookies = data.cookies

        if not cookies:
            raise HTTPException(status_code=400, detail="Cookies 列表为空")
        
        semaphore = asyncio.Semaphore(20)
        add_tasks = []

        async def add_cookie(simple_cookie):
            async with semaphore:
                return await fetch_limit_left(simple_cookie, True)

        # 使用 asyncio.create_task 而不是直接 await
        for cookie in cookies:
            add_tasks.append(add_cookie(cookie))

        results = await asyncio.gather(*add_tasks, return_exceptions=True)
        success_count = sum(1 for result in results if result is True)
        fail_count = len(cookies) - success_count
        
        logging.info({"message": "Cookies 更新成功。", "成功数量": success_count, "失败数量": fail_count})

        return JSONResponse(
            content={"message": "Cookies add successfully.", "success_count": success_count, "fail_count": fail_count})

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logging.error({"error": str(e)})
        return JSONResponse(status_code=500, content={"error": str(e)})


# 删除cookie
@app.delete(f"{COOKIES_PREFIX}/cookies")
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
            content={"message": "Cookies delete successfully.", "success_count": success_count, "fail_count": fail_count})
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": e})


# 请求刷新cookies
@app.get(f"{COOKIES_PREFIX}/refresh/cookies")
async def refresh_cookies(authorization: str = Header(...)):
    try:
        await verify_auth_header(authorization)
        logging.info(f"==========================================")
        logging.info("开始更新数据库里的 cookies.........")
        cookies = [item['cookie'] for item in await db_manager.get_cookies()]
        semaphore = asyncio.Semaphore(20)
        add_tasks = []

        async def refresh_cookie(simple_cookie):
            async with semaphore:
                return await fetch_limit_left(simple_cookie, False)

        # 使用 asyncio.create_task 而不是直接 await
        for cookie in cookies:
            add_tasks.append(refresh_cookie(cookie))

        results = await asyncio.gather(*add_tasks, return_exceptions=True)
        success_count = sum(1 for result in results if result is True)
        fail_count = len(cookies) - success_count

        logging.info({"message": "Cookies 更新成功。", "成功数量": success_count, "失败数量": fail_count})
        logging.info(f"==========================================")

        return JSONResponse(
            content={"message": "Cookies refresh successfully.", "success_count": success_count, "fail_count": fail_count})

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logging.error({"error": str(e)})
        return JSONResponse(status_code=500, content={"error": str(e)})


# 删除cookie
@app.delete(f"{COOKIES_PREFIX}/refresh/cookies")
async def delete_invalid_cookies(authorization: str = Header(...)):
    try:
        await verify_auth_header(authorization)
        logging.info(f"==========================================")
        logging.info("开始删除数据库里的 cookies.........")
        cookies = [item['cookie'] for item in await db_manager.get_invalid_cookies()]
        delete_tasks = []
        for cookie in cookies:
            delete_tasks.append(db_manager.delete_cookies(cookie))

        results = await asyncio.gather(*delete_tasks, return_exceptions=True)
        success_count = sum(1 for result in results if result is True)
        fail_count = len(cookies) - success_count

        logging.info({"message": "Invalid cookies 删除成功。", "成功数量": success_count, "失败数量": fail_count})
        logging.info(f"==========================================")
        return JSONResponse(
            content={"message": "Invalid cookies deleted successfully.", "success_count": success_count,
                     "fail_count": fail_count})
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": e})


# 添加cookie的函数
async def fetch_limit_left(cookie, is_insert: bool = False):
    try:
        song_gen = SongsGen(cookie)
        remaining_count = song_gen.get_limit_left()
        if remaining_count == -1 and is_insert:
            logging.info(f"该账号剩余次数: {remaining_count}，添加或刷新失败！")
            return False
        await db_manager.insert_or_update_cookie(cookie=cookie, count=remaining_count)
        logging.info(f"该账号剩余次数: {remaining_count}，添加或刷新成功！")
        return True
    except Exception as e:
        logging.error(cookie + f"，添加失败：{e}")
        return False

