# -*- coding:utf-8 -*-
import asyncio
import datetime
import json
import random
import string
import time
import warnings
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

from data import schemas
from data.cookie import suno_auth
from process import process_cookies
from suno.suno import SongsGen
from util.config import (SQL_IP, SQL_DK, USER_NAME,
                         SQL_PASSWORD, SQL_NAME, COOKIES_PREFIX,
                         BATCH_SIZE, RETRIES, AUTH_KEY)
from util.logger import logger
from util.sql_uilts import DatabaseManager
from util.utils import generate_music, get_feed

warnings.filterwarnings("ignore")

# 从环境变量中获取配置
db_manager = DatabaseManager(SQL_IP, int(SQL_DK), USER_NAME, SQL_PASSWORD, SQL_NAME)
process_cookie = process_cookies.processCookies(SQL_IP, int(SQL_DK), USER_NAME, SQL_PASSWORD, SQL_NAME)


# 刷新cookies函数
async def cron_refresh_cookies():
    try:
        logger.info(f"==========================================")
        logger.info("开始添加数据库里的 process.........")
        cookies = [item['cookie'] for item in await db_manager.get_invalid_cookies()]
        total_cookies = len(cookies)
        processed_count = 0
        for i in range(0, total_cookies, BATCH_SIZE):
            cookie_batch = cookies[i:i + BATCH_SIZE]
            for result in process_cookie.refresh_add_cookie(cookie_batch, BATCH_SIZE, False):
                if result:
                    processed_count += 1
        success_percentage = (processed_count / total_cookies) * 100 if total_cookies > 0 else 100
        logger.info(f"所有 Cookies 添加完毕。{processed_count}/{total_cookies} 个成功，"
                    f"成功率：({success_percentage:.2f}%)")
        logger.info(f"==========================================")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error({"添加cookies出现错误": str(e)})
        return JSONResponse(status_code=500, content={"添加cookies出现错误": str(e)})


async def cron_delete_cookies():
    try:
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
            {"message": "Invalid process 删除成功。", "成功数量": success_count, "失败数量": fail_count})
        logger.info(f"==========================================")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": e})


# 初始化所有songID
async def init_delete_songID():
    try:
        rows_updated = await db_manager.delete_songIDS()
        logger.info({"message": "Cookies songIDs更新成功！", "rows_updated": rows_updated})
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
    scheduler.add_job(cron_refresh_cookies, IntervalTrigger(minutes=120), id='updateRefresh_run')
    scheduler.add_job(cron_delete_cookies, IntervalTrigger(minutes=90), id='updateDelete_run')
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


async def Delelet_Songid(cookie):
    for attempt in range(RETRIES):
        try:
            await db_manager.delete_song_ids(cookie)
            return
        except Exception as e:
            if attempt > RETRIES - 1:
                logger.info(f"删除音乐songID失败: {e}")


async def generate_data(chat_user_message, chat_id, timeStamp, ModelVersion, tags=None, title=None, continue_at=None,
                        continue_clip_id=None):
    for try_count in range(RETRIES):
        cookie = None
        song_gen = None
        try:
            for attempt in range(RETRIES):
                try:
                    cookie = await db_manager.get_token()
                    if cookie is None:
                        raise RuntimeError("没有可用的cookie")
                    else:
                        song_gen = SongsGen(cookie)
                        remaining_count = song_gen.get_limit_left()
                        if remaining_count == -1:
                            await db_manager.delete_cookies(cookie)
                            raise RuntimeError("该账号剩余次数为 -1，无法使用")
                        break
                except Exception as e:
                    logger.error(f"在请求重试 {try_count} 次中，第 {attempt + 1} 次尝试获取cookie失败，错误为：{str(e)}")
                    if attempt > RETRIES - 1:
                        raise RuntimeError(f"在请求重试 {try_count} 次中，获取cookie全部失败，cookie发生异常: {e}")

            _return_ids = False
            _return_tags = False
            _return_title = False
            _return_prompt = False
            _return_image_url = False
            _return_video_url = False
            _return_audio_url = False
            _return_Forever_url = False
            token, sid = song_gen.get_auth_token(w=1)

            suno_auth.set_session_id(sid)
            suno_auth.load_cookie(cookie)
            Model = "chirp-v3-0"
            if ModelVersion == "suno-v3":
                Model = "chirp-v3-0"
            elif ModelVersion == "suno-v3.5":
                Model = "chirp-v3-5"
            else:
                yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": ModelVersion, "created": timeStamp, "choices": [{"index": 0, "delta": {"content": str("请选择suno-v3 或者 suno-v3.5其中一个")}, "finish_reason": None}]})}\n\n"""
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

            response = await generate_music(data=data, token=token)
            # await asyncio.sleep(3)
            clip_ids = get_clips_ids(response)
            song_id_1 = clip_ids[0]
            song_id_2 = clip_ids[1]
            # await db_manager.update_song_ids_by_cookie(cookie, song_id_1, song_id_2)

            tem_text = "\n### 🤯 Creating\n```suno\n{prompt:" + f"{chat_user_message}" + "}\n```\n"
            yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": ModelVersion, "created": timeStamp, "choices": [{"index": 0, "delta": {"role": "assistant", "content": tem_text}, "finish_reason": None}]})}\n\n"""
            for clip_id in clip_ids:
                count = 0
                while True:
                    # cookie = await db_manager.get_cookie_by_songid(clip_id)
                    token, sid = SongsGen(cookie).get_auth_token(w=1)
                    now_data = await get_feed(ids=clip_id, token=token)
                    try:
                        more_information_ = now_data[0]['metadata']
                    except Exception as e:
                        logger.info(f'more_information_: {e}')
                        continue
                    if _return_Forever_url and _return_ids and _return_tags and _return_title and _return_prompt and _return_image_url and _return_audio_url:
                        break
                    if not _return_Forever_url:
                        try:
                            if check_status_complete(now_data):
                                await Delelet_Songid(cookie)
                                Aideo_Markdown_Conetent = (f""
                                                           f"\n### 🎷 CDN音乐链接\n"
                                                           f"- **🎧 音乐1️⃣**：{'https://cdn1.suno.ai/' + clip_id + '.mp3'} \n"
                                                           f"- **🎧 音乐2️⃣**：{'https://cdn1.suno.ai/' + song_id_2 + '.mp3'} \n")
                                Video_Markdown_Conetent = (f""
                                                           f"\n### 📺 CDN视频链接\n"
                                                           f"- **📽️ 视频1️⃣**：{'https://cdn1.suno.ai/' + song_id_1 + '.mp4'} \n"
                                                           f"- **📽️ 视频2️⃣**：{'https://cdn1.suno.ai/' + song_id_2 + '.mp4'} \n"
                                                           f"\n### 👀 更多\n"
                                                           f"**🤗还想听更多歌吗，快来告诉我**🎶✨\n")
                                yield str(
                                    f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": ModelVersion, "created": timeStamp, "choices": [{"index": 0, "delta": {"content": Aideo_Markdown_Conetent}, "finish_reason": None}]})}\n\n""")
                                yield str(
                                    f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": ModelVersion, "created": timeStamp, "choices": [{"index": 0, "delta": {"content": Video_Markdown_Conetent}, "finish_reason": None}]})}\n\n""")
                                _return_Forever_url = True
                                break
                        except Exception as e:
                            logger.info('CDN音乐链接出错', e)
                            pass

                    if not _return_ids:
                        try:
                            song_id_text = (f""
                                            f"### ⭐ 歌曲信息\n"
                                            f"- **🧩 ID1️⃣**：{song_id_1}\n"
                                            f"- **🧩 ID2️⃣**：{song_id_2}\n")
                            yield str(
                                f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": ModelVersion, "created": timeStamp, "choices": [{"index": 0, "delta": {"content": song_id_text}, "finish_reason": None}]})}\n\n""")
                            _return_ids = True
                        except:
                            pass

                    if not _return_title:
                        try:
                            title = now_data[0]["title"]
                            if title != '':
                                title_data = f"- **🤖 歌名**：{title} \n"
                                yield """data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": ModelVersion, "created": timeStamp, "choices": [{"index": 0, "delta": {"content": title_data}, "finish_reason": None}]})}\n\n"""
                                _return_title = True
                        except:
                            pass

                    if not _return_tags:
                        try:
                            tags = more_information_["tags"]
                            if tags is not None and tags != "":
                                tags_data = f"- **💄 类型**：{tags} \n"
                                yield str(
                                    f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": ModelVersion, "created": timeStamp, "choices": [{"index": 0, "delta": {"content": tags_data}, "finish_reason": None}]})}\n\n""")
                                _return_tags = True
                        except:
                            pass

                    if not _return_prompt:
                        try:
                            prompt = more_information_["prompt"]
                            if prompt is not None and prompt != '':
                                prompt_data = f"### 📖 完整歌词\n```\n{prompt}\n```\n"
                                yield str(
                                    f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": ModelVersion, "created": timeStamp, "choices": [{"index": 0, "delta": {"content": prompt_data}, "finish_reason": None}]})}\n\n""")
                                _return_prompt = True
                        except:
                            pass

                    if not _return_image_url:
                        if now_data[0].get('image_url') is not None:
                            image_url_small_data = f"### 🖼️ 歌曲图片\n"
                            image_url_lager_data = f"![image_large_url]({now_data[0]['image_large_url']}) \n### 🤩 即刻享受"
                            yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": ModelVersion, "created": timeStamp, "choices": [{"index": 0, "delta": {"content": image_url_small_data}, "finish_reason": None}]})}\n\n"""
                            yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": ModelVersion, "created": timeStamp, "choices": [{"index": 0, "delta": {"content": image_url_lager_data}, "finish_reason": None}]})}\n\n"""
                            _return_image_url = True

                    if not _return_audio_url:
                        if 'audio_url' in now_data[0]:
                            audio_url_ = now_data[0]['audio_url']
                            if audio_url_ != '':
                                audio_url_1 = f'https://audiopipe.suno.ai/?item_id={song_id_1}'
                                audio_url_2 = f'https://audiopipe.suno.ai/?item_id={song_id_2}'

                                audio_url_data_1 = f"\n- **🔗 实时音乐1️⃣**：{audio_url_1}"
                                audio_url_data_2 = f"\n- **🔗 实时音乐2️⃣**：{audio_url_2}\n### 🚀 生成CDN链接中（2min~）\n"
                                yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": ModelVersion, "created": timeStamp, "choices": [{"index": 0, "delta": {"content": audio_url_data_1}, "finish_reason": None}]})}\n\n"""
                                yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": ModelVersion, "created": timeStamp, "choices": [{"index": 0, "delta": {"content": audio_url_data_2}, "finish_reason": None}]})}\n\n"""
                                _return_audio_url = True
                    if _return_ids and _return_tags and _return_title and _return_prompt and _return_image_url and _return_audio_url:
                        count += 1
                        if count % 34 == 0:
                            content_wait = "🎵\n"
                        else:
                            content_wait = "🎵"
                        yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": ModelVersion, "created": timeStamp, "choices": [{"index": 0, "delta": {"content": content_wait}, "finish_reason": None}]})}\n\n"""
                        await asyncio.sleep(3)

            yield f"""data:""" + ' ' + f"""[DONE]\n\n"""
            break
        except Exception as e:
            if cookie is not None:
                await Delelet_Songid(cookie)
            if try_count < RETRIES - 1:
                logger.error(f"第 {try_count + 1} 次尝试歌曲失败，错误为：{str(e)}")
                continue
            else:
                yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": ModelVersion, "created": timeStamp, "choices": [{"index": 0, "delta": {"content": str("生成歌曲失败: 请打开日志或数据库查看报错信息......")}, "finish_reason": None}]})}\n\n"""
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
            "model": data.model,
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
            data_generator = generate_data(last_user_content, chat_id, timeStamp, data.model)
            return StreamingResponse(data_generator, headers=headers, media_type="text/event-stream")
        except Exception as e:
            return JSONResponse(status_code=500, content={"detail": f"生成流式响应时出错: {str(e)}"})


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


@app.put(f"{COOKIES_PREFIX}/cookies")
async def add_cookies(data: schemas.Cookies, authorization: str = Header(...)):
    try:
        await verify_auth_header(authorization)
        logger.info(f"==========================================")
        logger.info("开始添加数据库里的 process.........")
        cookies = data.cookies
        total_cookies = len(cookies)

        async def stream_results():
            processed_count = 0
            for i in range(0, total_cookies, BATCH_SIZE):
                cookie_batch = cookies[i:i + BATCH_SIZE]
                for result in process_cookie.refresh_add_cookie(cookie_batch, BATCH_SIZE, False):
                    if result:
                        processed_count += 1
                        yield f"data: Cookie {processed_count}/{total_cookies} 添加成功!\n\n"
                    else:
                        yield f"data: Cookie {processed_count}/{total_cookies} 添加失败!\n\n"

            success_percentage = (processed_count / total_cookies) * 100 if total_cookies > 0 else 100
            logger.info(f"所有 Cookies 添加完毕。{processed_count}/{total_cookies} 个成功，"
                        f"成功率：({success_percentage:.2f}%)")
            logger.info(f"==========================================")
            yield f"data: 所有 Cookies 添加完毕。{processed_count}/{total_cookies} 个成功，成功率：({success_percentage:.2f}%)\n\n"
            yield f"""data:""" + ' ' + f"""[DONE]\n\n"""

        return StreamingResponse(stream_results(), media_type="text/event-stream")

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error({"添加cookies出现错误": str(e)})
        return JSONResponse(status_code=500, content={"添加cookies出现错误": str(e)})


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
            content={"message": "Cookies delete successfully.", "success_count": success_count,
                     "fail_count": fail_count})
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": e})


# 请求刷新cookies
@app.get(f"{COOKIES_PREFIX}/refresh/cookies")
async def refresh_cookies(authorization: str = Header(...)):
    try:
        await verify_auth_header(authorization)
        logger.info(f"==========================================")
        logger.info("开始刷新数据库里的 process.........")
        cookies = [item['cookie'] for item in await db_manager.get_cookies()]
        total_cookies = len(cookies)

        async def stream_results():
            processed_count = 0
            for i in range(0, total_cookies, BATCH_SIZE):
                cookie_batch = cookies[i:i + BATCH_SIZE]
                for result in process_cookie.refresh_add_cookie(cookie_batch, BATCH_SIZE, False):
                    if result:
                        processed_count += 1
                        yield f"data: Cookie {processed_count}/{total_cookies} 刷新成功!\n\n"
                    else:
                        yield f"data: Cookie {processed_count}/{total_cookies} 刷新失败!\n\n"

            success_percentage = (processed_count / total_cookies) * 100 if total_cookies > 0 else 100
            logger.info(f"所有 Cookies 添加完毕。{processed_count}/{total_cookies} 个成功，"
                        f"成功率：({success_percentage:.2f}%)")
            logger.info(f"==========================================")
            yield f"data: 所有 Cookies 刷新完毕。{processed_count}/{total_cookies} 个成功，成功率：({success_percentage:.2f}%)\n\n"
            yield f"""data:""" + ' ' + f"""[DONE]\n\n"""

        return StreamingResponse(stream_results(), media_type="text/event-stream")

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error({"刷新cookies出现错误": str(e)})
        return JSONResponse(status_code=500, content={"刷新cookies出现错误": str(e)})


# 删除cookie
@app.delete(f"{COOKIES_PREFIX}/refresh/cookies")
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
            {"message": "Invalid process 删除成功。", "成功数量": success_count, "失败数量": fail_count})
        logger.info(f"==========================================")
        return JSONResponse(
            content={"message": "Invalid process deleted successfully.", "success_count": success_count,
                     "fail_count": fail_count})
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": e})


# 获取cookies的详细详细
@app.delete(f"{COOKIES_PREFIX}/songID/cookies")
async def delete_songID(authorization: str = Header(...)):
    try:
        await verify_auth_header(authorization)
        rows_updated = await db_manager.delete_songIDS()
        return JSONResponse(
            content={"message": "Cookies songIDs更新成功！", "rows_updated": rows_updated}
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# 添加cookie的函数
async def fetch_limit_left(cookie, is_insert: bool = False):
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
