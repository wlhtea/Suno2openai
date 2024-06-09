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
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.responses import StreamingResponse

import schemas
from cookie import suno_auth
from init_sql import create_database_and_table
from sql_uilts import DatabaseManager
from suno.suno import SongsGen
from utils import generate_music, get_feed


# 刷新cookies
async def refresh_cookies():
    try:
        logging.info(f"==========================================")
        logging.info("开始更新数据库里的 cookies.........")
        cookies = await db_manager.get_cookies()
        add_tasks = []
        for cookie in cookies:
            add_tasks.append(fetch_limit_left(cookie))
        results = await asyncio.gather(*add_tasks, return_exceptions=True)
        success_count = sum(1 for result in results if result is True)
        fail_count = len(cookies) - success_count

        logging.info({"message": "Cookies 更新成功。", "成功数量": success_count, "失败数量": fail_count})
    except Exception as e:
        logging.error({"错误": str(e)})


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    # 创建数据库
    global db_manager
    try:
        db_manager = DatabaseManager(SQL_IP, int(SQL_dk), username_name, SQL_password, SQL_name)
        await db_manager.create_pool()
        await create_database_and_table()
        logging.info(f"初始化sql成功！")
    except Exception as e:
        logging.error(f"初始化sql失败: {str(e)}")
        raise

    # 初始化并启动 APScheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(refresh_cookies, CronTrigger(hour=3, minute=0), id='updateRefresh_run')
    scheduler.start()
    yield

    # 停止调度器
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.get("/")
async def get_root():
    return schemas.Response()


# @app.post("/generate")
# async def generate(data: schemas.GenerateBase):
#     cookie = data.dict().get('cookie')
#     session_id = data.dict().get('session_id')
#     token = data.dict().get('token')
#     try:
#         suno_auth.set_session_id(session_id)
#         suno_auth.load_cookie(cookie)
#         resp = await generate_music(data.dict(), token)
#         return resp
#     except Exception as e:
#         raise HTTPException(detail=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#
# @app.get("/feed/{aid}")
# async def fetch_feed(aid: str, token: str = Depends(get_token)):
#     try:
#         resp = await get_feed(aid, token)
#         return resp
#     except Exception as e:
#         raise HTTPException(detail=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#
# @app.post("/generate/lyrics/")
# async def generate_lyrics_post(request: Request, token: str = Depends(get_token)):
#     req = await request.json()
#     prompt = req.get("prompt")
#     if prompt is None:
#         raise HTTPException(detail="prompt is required", status_code=status.HTTP_400_BAD_REQUEST)
#
#     try:
#         resp = await generate_lyrics(prompt, token)
#         return resp
#     except Exception as e:
#         raise HTTPException(detail=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#
# @app.get("/lyrics/{lid}")
# async def fetch_lyrics(lid: str, token: str = Depends(get_token)):
#     try:
#         resp = await get_lyrics(lid, token)
#         return resp
#     except Exception as e:
#         raise HTTPException(detail=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


BASE_URL = os.getenv('BASE_URL', 'https://studio-api.suno.ai')
SESSION_ID = os.getenv('SESSION_ID')
username_name = os.getenv('USER_Name', '')
SQL_name = os.getenv('SQL_name', '')
SQL_password = os.getenv('SQL_password', '')
SQL_IP = os.getenv('SQL_IP', '')
SQL_dk = os.getenv('SQL_dk', 3306)
cookies_prefix = os.getenv('COOKIES_PREFIX', "")
auth_key = os.getenv('AUTH_KEY', str(time.time()))
db_manager = DatabaseManager(SQL_IP, int(SQL_dk), username_name, SQL_password, SQL_name)

logging.info(f"==========================================")
logging.info(f"BASE_URL: {BASE_URL}")
logging.info(f"SESSION_ID: {SESSION_ID}")
logging.info(f"USER_Name: {username_name}")
logging.info(f"SQL_name: {SQL_name}")
logging.info(f"SQL_password: {SQL_password}")
logging.info(f"SQL_IP: {SQL_IP}")
logging.info(f"SQL_dk: {SQL_dk}")
logging.info(f"COOKIES_PREFIX: {cookies_prefix}")
logging.info(f"AUTH_KEY: {auth_key}")
logging.info(f"==========================================")


def generate_random_string_async(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_timestamp_async():
    return int(time.time())


def calculate_token_costs(input_prompt: str, output_prompt: str, model_name: str) -> (int, int):
    """
    Calculate the number of tokens for the input and output prompts based on the specified model.

    Parameters:
    input_prompt (str): The input prompt string.
    output_prompt (str): The output prompt string.
    model_name (str): The model name to determine the encoding.

    Returns:
    tuple: A tuple containing the number of tokens for the input prompt and the output prompt.
    """
    # Load the correct encoding for the given model
    encoding = tiktoken.encoding_for_model(model_name)

    # Encode the prompts
    input_tokens = encoding.encode(input_prompt)
    output_tokens = encoding.encode(output_prompt)

    # Count the tokens
    input_token_count = len(input_tokens)
    output_token_count = len(output_tokens)

    return input_token_count, output_token_count


async def generate_data(chat_user_message, chat_id, timeStamp, ModelVersion):
    retries = 5
    cookie = None
    for attempt in range(retries):
        try:
            cookie = await db_manager.get_non_working_cookie()
            if cookie is None:
                raise RuntimeError("没有可用的cookie")
            logging.info(f"获取到cookie:{cookie}")
            break
        except Exception as e:
            logging.error(f"第 {attempt + 1} 次尝试获取cookie失败，错误为：{str(e)}")
            if attempt < retries - 1:
                await asyncio.sleep(0.1)
            else:
                raise RuntimeError(f"获取cookie失败cookie发生异常: {e}")

    try:
        _return_ids = False
        _return_tags = False
        _return_title = False
        _return_prompt = False
        _return_image_url = False
        _return_video_url = False

        await db_manager.update_cookie_working(cookie, True)
        await db_manager.update_cookie_count(cookie, 1)

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
        yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"role": "assistant", "content": ""}, "finish_reason": None}]})}\n\n"""
        response = await generate_music(data=data, token=token)
        if isinstance(response, str):
            raise RuntimeError(f"{response}，请检查cookie是否有效")
        await asyncio.sleep(3)
        while True:
            try:
                response_clips = response["clips"]
                clip_ids = [clip["id"] for clip in response_clips]
                if not clip_ids:
                    return
                break
            except:
                pass

        # 使用 clip_ids 查询音频链接
        for clip_id in clip_ids:
            attempts = 0
            while attempts < 120:  # 限制尝试次数以避免无限循环
                now_data = await get_feed(ids=clip_id, token=token)
                more_information_ = now_data[0]['metadata']
                if type(now_data) == dict:
                    if now_data.get('detail') == 'Unauthorized':
                        link = f'https://audiopipe.suno.ai/?item_id={clip_id}'
                        link_data = f"\n **音乐链接**:{link}\n"
                        yield """data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": link_data}, "finish_reason": None}]})}\n\n"""
                        break

                elif not _return_ids:
                    try:
                        song_id_1 = clip_ids[0]
                        song_id_2 = clip_ids[1]
                        song_id_text = (f""
                                        f"## ⭐ 歌曲ID\n"
                                        f"- **🎵 歌曲id1️⃣**：{song_id_1}\n"
                                        f"- **🎵 歌曲id2️⃣**：{song_id_2}\n"
                                        f"## 🎖️ 歌曲链接: \n"
                                        f"- 🎵 歌曲链接1️⃣：{'https://cdn1.suno.ai/' + song_id_1 + '.mp3'} \n"
                                        f"- 🎵 歌曲链接2️⃣：{'https://cdn1.suno.ai/' + song_id_2 + '.mp3'} \n"
                                        f"- ⚠️ 歌曲链接至少要两分钟才生效哦🥰  \n")
                        yield str(
                            f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": song_id_text}, "finish_reason": None}]})}\n\n""")

                        _return_ids = True
                    except:
                        pass

                elif not _return_title:
                    try:
                        title = now_data[0]["title"]
                        if title != '':
                            title_data = f"## 🧩 歌曲信息\n- **🔎 歌名**：{title} \n"
                            yield """data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": title_data}, "finish_reason": None}]})}\n\n"""
                            _return_title = True
                    except:
                        pass
                elif not _return_tags:
                    try:
                        tags = more_information_["tags"]
                        if tags is not None:
                            tags_data = f"- **💄 类型**：{tags} \n"
                            yield str(
                                f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": tags_data}, "finish_reason": None}]})}\n\n""")
                            _return_tags = True
                    except:
                        pass
                elif not _return_prompt:
                    try:
                        prompt = more_information_["prompt"]
                        if prompt is not None:
                            prompt_data = f"## 🔎 完整歌词\n```\n{prompt}\n```\n"
                            yield str(
                                f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": prompt_data}, "finish_reason": None}]})}\n\n""")
                            _return_prompt = True
                    except:
                        pass


                elif not _return_image_url:
                    if now_data[0].get('image_url') is not None:
                        # image_url_small_data = f"## ✨ 歌曲图片\n**🖼️ 图片链接** ![封面图片_小]({now_data[0]['image_url']}) \n"
                        image_url_lager_data = f"## ✨ 歌曲图片\n ![封面图片_大]({now_data[0]['image_large_url']})\n## 🤩 即刻享受\n"
                        # yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": image_url_small_data}, "finish_reason": None}]})}\n\n"""
                        yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": image_url_lager_data}, "finish_reason": None}]})}\n\n"""
                        _return_image_url = True
                elif 'audio_url' in now_data[0]:
                    audio_url_ = now_data[0]['audio_url']
                    if audio_url_ != '':
                        audio_url_data = f"\n **📌 音乐链接(临时)**：{audio_url_}"
                        yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": audio_url_data}, "finish_reason": None}]})}\n\n"""
                        break
                else:
                    content_wait = "."
                    yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": content_wait}, "finish_reason": None}]})}\n\n"""
                    logging.info(attempts)
                    logging.info(now_data)
                    time.sleep(5)  # 等待5秒再次尝试
                    attempts += 1
        yield f"""data:""" + ' ' + f"""[DONE]\n\n"""
    except Exception as e:
        yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": str(e)}, "finish_reason": None}]})}\n\n"""
        yield f"""data:""" + ' ' + f"""[DONE]\n\n"""
    finally:
        try:
            await db_manager.update_cookie_working(cookie, False)
        except Exception as e:
            raise RuntimeError(f"解锁cookie发生异常: {e}")


@app.post("/v1/chat/completions")
async def get_last_user_message(data: schemas.Data, authorization: str = Header(...)):
    content_all = ''
    if SQL_IP == '' or SQL_password == '' or SQL_name == '':
        raise HTTPException(status_code=400, detail="BASE_URL is not set")
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
            return StreamingResponse(generate_data(last_user_content, chat_id, timeStamp, data.model), headers=headers,
                                     media_type="text/event-stream")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"生成流式响应时出错: {str(e)}")


# 授权检查
async def verify_auth_header(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")
    if authorization.strip() != f"Bearer {auth_key}":
        raise HTTPException(status_code=403, detail="Invalid authorization key")


# 获取cookie
@app.post(f"{cookies_prefix}/cookies")
async def get_last_user_message(authorization: str = Header(...)):
    try:
        await verify_auth_header(authorization)
        cookies = await db_manager.get_cookies()
        return JSONResponse(content={"count": len(cookies), "cookies": cookies})
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": e})


# 添加cookies
@app.put(f"{cookies_prefix}/cookies")
async def add_cookies(data: schemas.Cookies, authorization: str = Header(...)):
    try:
        await verify_auth_header(authorization)
        cookies = data.cookies
        add_tasks = []
        for cookie in cookies:
            add_tasks.append(fetch_limit_left(cookie))

        results = await asyncio.gather(*add_tasks, return_exceptions=True)
        success_count = sum(1 for result in results if result is True)
        fail_count = len(cookies) - success_count

        return JSONResponse(
            content={"message": "Cookies add successfully.", "success_count": success_count, "fail_count": fail_count})
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": e})


# 删除cookie
@app.delete(f"{cookies_prefix}/cookies")
async def get_last_user_message(data: schemas.Cookies, authorization: str = Header(...)):
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
            content={"message": "Cookies add successfully.", "success_count": success_count, "fail_count": fail_count})
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": e})


# 请求刷新cookies
@app.get(f"{cookies_prefix}/refresh/cookies")
async def get_refresh_cookies():
    try:
        logging.info(f"==========================================")
        logging.info("开始更新数据库里的 cookies.........")
        cookies = await db_manager.get_cookies()
        add_tasks = []
        for cookie in cookies:
            add_tasks.append(fetch_limit_left(cookie))
        results = await asyncio.gather(*add_tasks, return_exceptions=True)
        success_count = sum(1 for result in results if result is True)
        fail_count = len(cookies) - success_count
        logging.info({"message": "Cookies 更新成功。", "成功数量": success_count, "失败数量": fail_count})
        return JSONResponse(
            content={"message": "Cookies add successfully.", "success_count": success_count, "fail_count": fail_count})
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": e})


# 添加cookie的函数
async def fetch_limit_left(cookie):
    song_gen = SongsGen(cookie)
    try:
        remaining_count = song_gen.get_limit_left()
        logging.info(f"该账号剩余次数: {remaining_count}")
        await db_manager.insert_cookie(cookie, remaining_count, False)
        return True
    except Exception as e:
        logging.error(cookie + f"，添加失败：{e}")
        return False
