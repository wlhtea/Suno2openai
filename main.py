# -*- coding:utf-8 -*-
import json
import os

from fastapi import FastAPI, HTTPException, status, Depends, Request, Cookie
from fastapi.middleware.cors import CORSMiddleware

from init_sql import create_database_and_table
from utils import generate_music, get_feed, generate_lyrics, get_lyrics
from deps import get_token
import schemas
from cookie import suno_auth
from utils import generate_music,get_feed
import asyncio
from suno.suno import SongsGen
from starlette.responses import StreamingResponse



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

import asyncio
import random
import string
import time
from sql_uilts import DatabaseManager
BASE_URL = os.getenv('BASE_URL','https://studio-api.suno.ai')
SESSION_ID = os.getenv('SESSION_ID')
SQL_name = os.getenv('SQL_name','')
SQL_password = os.getenv('SQL_password','')
SQL_IP = os.getenv('SQL_IP','')
SQL_dk = os.getenv('SQL_dk',3306)

def generate_random_string_async(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_timestamp_async():
    return int(time.time())

async def generate_data(chat_user_message):
    db_manager = DatabaseManager(SQL_IP, int(SQL_dk), SQL_name, SQL_password, SQL_name)
    chat_id = generate_random_string_async(29)
    timeStamp = generate_timestamp_async()
    while True:
        try:
            await db_manager.create_pool()
            cookie = await db_manager.get_non_working_cookie()
            break
        except:
            await create_database_and_table()
    try:
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
        data = {
            "gpt_description_prompt": f"{chat_user_message}",
            "prompt": "",
            "mv": "chirp-v3-0",
            "title": "",
            "tags": ""
        }
        yield f"""data:{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created" : timeStamp, "choices": [{"index": 0, "delta": {"role":"assistant","content":" "}, "finish_reason": None}]})}\n\n"""
        response = await generate_music(data=data, token=token)
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
            while attempts < 60:  # 限制尝试次数以避免无限循环
                now_data = await get_feed(ids=clip_id, token=token)
                more_information_ = now_data[0]['metadata']
                if type(now_data) == dict:
                    if now_data.get('detail') == 'Unauthorized':
                        link = f'https://audiopipe.suno.ai/?item_id={clip_id}'
                        link_data = f"\n **音乐链接**:{link}\n"
                        yield str(f"""data:{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": link_data}, "finish_reason": None}]})}\n\n""")
                        break
                elif not _return_title:
                    try:
                        title = now_data[0]["title"]
                        if title != '':
                            title_data = f"**歌名**:{title} \n"
                            print(title)
                            yield str(f"""data:{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": title_data}, "finish_reason": None}]})}\n\n""")
                            _return_title = True
                    except:
                        pass
                elif not _return_tags:
                    try:
                        tags = more_information_["tags"]
                        if tags is not None:
                            tags_data = f"**类型**:{tags} \n"
                            print(tags)
                            yield str(f"""data:{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": tags_data}, "finish_reason": None}]})}\n\n""")
                            _return_tags = True
                    except:
                        pass
                elif not _return_prompt:
                    try:
                        prompt = more_information_["prompt"]
                        if prompt is not None:
                            print(prompt)
                            prompt_data = f"**歌词**:{prompt} \n"
                            yield str(f"""data:{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": prompt_data}, "finish_reason": None}]})}\n\n""")
                            _return_prompt = True
                    except:
                        pass


                elif not _return_image_url:
                    if now_data[0].get('image_url') is not None:

                        image_url_small_data = f"**图片链接:** ![封面图片_小]({now_data[0]['image_url']}) \n"
                        image_url_lager_data = f"**图片链接:** ![封面图片_大]({now_data[0]['image_large_url']}) \n"
                        print(image_url_lager_data)
                        print(image_url_small_data)
                        yield f"""data:{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": image_url_small_data}, "finish_reason": None}]})}\n\n"""
                        yield f"""data:{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": image_url_lager_data}, "finish_reason": None}]})}\n\n"""
                        _return_image_url = True
                elif 'audio_url' in now_data[0]:
                    print(response)
                    audio_url_ = now_data[0]['audio_url']
                    if audio_url_ != '':
                        audio_url_data = f"\n **音乐链接**:{audio_url_}"
                        yield f"""data:{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": audio_url_data}, "finish_reason": None}]})}\n\n"""
                        break
                else:
                    content_wait = "."
                    yield f"""data:{json.dumps({"id":f"chatcmpl-{chat_id}","object":"chat.completion.chunk","model":"suno-v3","created":timeStamp,"choices":[{"index":0,"delta":{"content":content_wait},"finish_reason":None}]})}\n\n"""
                    await asyncio.sleep(5)  # 等待5秒再次尝试
                    attempts += 1
        yield f"""data:{[str('DONE')]}\n\n"""
    except Exception as e:
        yield f"""data:{json.dumps({"id":f"chatcmpl-{chat_id}","object":"chat.completion.chunk","model":"suno-v3","created":timeStamp,"choices":[{"index":0,"delta":{"content":str(e)},"finish_reason":None}]})}\n\n"""
        yield f"""data:[DONE]\n\n"""
    finally:
        try:
            await db_manager.update_cookie_working(cookie, False)
        except:
            print('No sql')

@app.post("/v1/chat/completions")
async def get_last_user_message(data: schemas.Data):
    if SQL_IP == '' or SQL_password == '' or SQL_name == '':
        raise ValueError("BASE_URL is not set")
    else:
        last_user_content = None
        for message in reversed(data.messages):
            if message.role == "user":
                last_user_content = message.content
                break

        if last_user_content is None:
            raise HTTPException(status_code=400, detail="No user message found")

        return StreamingResponse(generate_data(last_user_content), media_type="text/event-stream")