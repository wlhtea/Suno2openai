# -*- coding:utf-8 -*-
import datetime
import json
import os
import schemas
from cookie import suno_auth
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from init_sql import create_database_and_table
from starlette.responses import StreamingResponse
from suno.suno import SongsGen
from utils import generate_music, get_feed

app = FastAPI()

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

import asyncio
import random
import string
import time
from sql_uilts import DatabaseManager

BASE_URL = os.getenv('BASE_URL', 'https://studio-api.suno.ai')
SESSION_ID = os.getenv('SESSION_ID')
username_name = os.getenv('USER_name','')
SQL_name = os.getenv('SQL_name', '')
SQL_password = os.getenv('SQL_password', '')
SQL_IP = os.getenv('SQL_IP', '')
SQL_dk = os.getenv('SQL_dk', 3306)

db_manager = DatabaseManager(SQL_IP, int(SQL_dk), username_name, SQL_password, SQL_name)

@app.on_event("startup")
async def on_startup():
    await db_manager.create_database_and_table()
def generate_random_string_async(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_timestamp_async():
    return int(time.time())


import tiktoken


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


async def generate_data(chat_user_message, chat_id, timeStamp, ModelVersion, tags=None, title=None, continue_at=None, continue_clip_id=None):
    while True:
        try:
            await db_manager.create_pool()
            cookie = await db_manager.get_token()
            break
        except:
            await create_database_and_table()

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
            while True:
                # if attempts // 2 == 0:
                cookie = await db_manager.get_cookie_by_songid(clip_id)
                token, sid = SongsGen(cookie)._get_auth_token(w=1)
                now_data = await get_feed(ids=clip_id, token=token)
                try:
                    more_information_ = now_data[0]['metadata']
                except Exception as e:
                    print('more_information_',e)
                if _return_Forever_url and _return_ids and _return_tags and _return_title and _return_prompt and _return_image_url and _return_audio_url:
                    break
                if not _return_Forever_url:
                    try:
                        if check_status_complete(now_data):
                            await Delelet_Songid(clip_id)
                            Aideo_Markdown_Conetent = (f""
                                                       f"\n## 🎷 永久音乐链接\n"
                                                       f"- 🎵 歌曲1️⃣：{'https://cdn1.suno.ai/' + clip_id + '.mp3'} \n"
                                                       f"- 🎵 歌曲2️⃣：{'https://cdn1.suno.ai/' + song_id_2 + '.mp3'} \n")
                            Video_Markdown_Conetent = (f""
                                                       f"\n## 📺 永久视频链接\n"
                                                       f"- 🎵 视频1️⃣：{'https://cdn1.suno.ai/' + song_id_1 + '.mp4'} \n"
                                                       f"- 🎵 视频2️⃣：{'https://cdn1.suno.ai/' + song_id_2 + '.mp4'} \n")
                            yield str(
                                f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": Video_Markdown_Conetent}, "finish_reason": None}]})}\n\n""")
                            yield str(
                                f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": Aideo_Markdown_Conetent}, "finish_reason": None}]})}\n\n""")
                            _return_Forever_url = True
                            break
                    except:
                        await Delelet_Songid(clip_id)
                        Aideo_Markdown_Conetent = (f""
                                                   f"\n## 🎷 永久音乐链接\n"
                                                   f"- 🎵 歌曲1️⃣：{'https://cdn1.suno.ai/' + clip_id + '.mp3'} \n"
                                                   f"- 🎵 歌曲2️⃣：{'https://cdn1.suno.ai/' + song_id_2 + '.mp3'} \n")
                        Video_Markdown_Conetent = (f""
                                                   f"\n## 📺 永久视频链接\n"
                                                   f"- 🎵 视频1️⃣：{'https://cdn1.suno.ai/' + song_id_1 + '.mp4'} \n"
                                                   f"- 🎵 视频2️⃣：{'https://cdn1.suno.ai/' + song_id_2 + '.mp4'} \n")
                        yield str(
                            f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": Video_Markdown_Conetent}, "finish_reason": None}]})}\n\n""")
                        yield str(
                            f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": Aideo_Markdown_Conetent}, "finish_reason": None}]})}\n\n""")
                        _return_Forever_url = True
                        break

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
                        image_url_lager_data = f"**🖼️ 图片链接** ![封面图片_大]({now_data[0]['image_large_url']}) \n"
                        yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": image_url_small_data}, "finish_reason": None}]})}\n\n"""
                        yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": image_url_lager_data}, "finish_reason": None}]})}\n\n"""
                        _return_image_url = True

                if not _return_audio_url:
                    if 'audio_url' in now_data[0]:
                        audio_url_ = now_data[0]['audio_url']
                        if audio_url_ != '':
                            audio_url_1 = f'https://audiopipe.suno.ai/?item_id={song_id_1}'
                            audio_url_2 = f'https://audiopipe.suno.ai/?item_id={song_id_2}'

                            audio_url_data_1 = f"\n **📌 音乐链接(实时)**：{audio_url_1}"
                            audio_url_data_2 = f"\n **📌 音乐链接(实时)**：{audio_url_2}\n"
                            yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": audio_url_data_1}, "finish_reason": None}]})}\n\n"""
                            yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": audio_url_data_2}, "finish_reason": None}]})}\n\n"""
                            _return_audio_url = True
                if _return_ids and _return_tags and _return_title and _return_prompt and _return_image_url and _return_audio_url:
                    content_wait = "🎵"
                    yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": content_wait}, "finish_reason": None}]})}\n\n"""
                    await asyncio.sleep(2)
                # attempts += 1

        yield f"""data:""" + ' ' + f"""[DONE]\n\n"""
    except Exception as e:
        yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": str(e)}, "finish_reason": None}]})}\n\n"""
        yield f"""data:""" + ' ' + f"""[DONE]\n\n"""


@app.post("/v1/chat/completions")
async def get_last_user_message(data: schemas.Data):
    content_all = ''
    if SQL_IP == '' or SQL_password == '' or SQL_name == '':
        raise ValueError("BASE_URL is not set")
    else:
        chat_id = generate_random_string_async(29)
        timeStamp = generate_timestamp_async()
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
            async for data_string in generate_data(last_user_content, chat_id, timeStamp, data.model):
                try:
                    json_data = data_string.split('data: ')[1].strip()
                    parsed_data = json.loads(json_data)
                    content = parsed_data['choices'][0]['delta']['content']
                    content_all += content
                except:
                    pass

            input_tokens, output_tokens = calculate_token_costs(last_user_content, content_all, 'gpt-3.5-turbo')
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
            return StreamingResponse(generate_data(last_user_content, chat_id, timeStamp, data.model), headers=headers, media_type="text/event-stream")
