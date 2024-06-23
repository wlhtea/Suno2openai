# -*- coding:utf-8 -*-
import asyncio
import json

from fastapi import HTTPException
from starlette.responses import StreamingResponse, JSONResponse

from data.PromptException import PromptException
from suno.suno import SongsGen
from util.config import RETRIES
from util.logger import logger
from util.tool import get_clips_ids, check_status_complete, deleteSongID, calculate_token_costs
from util.utils import generate_music, get_feed


# 流式请求
async def generate_data(start_time, db_manager, chat_user_message, chat_id,
                        timeStamp, ModelVersion, tags=None, title=None,
                        continue_at=None, continue_clip_id=None):
    if ModelVersion == "suno-v3":
        Model = "chirp-v3-0"
    elif ModelVersion == "suno-v3.5":
        Model = "chirp-v3-5"
    else:
        yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": ModelVersion, "created": timeStamp, "choices": [{"index": 0, "delta": {"content": str("请选择suno-v3 或者 suno-v3.5其中一个")}, "finish_reason": None}]})}\n\n"""
        yield f"""data:""" + ' ' + f"""[DONE]\n\n"""
        return

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

    for try_count in range(RETRIES):
        cookie = None
        song_gen = None
        try:
            cookie = str(await db_manager.get_request_cookie()).strip()
            if cookie is None:
                raise RuntimeError("没有可用的cookie")
            else:
                song_gen = SongsGen(cookie)
                remaining_count = await song_gen.get_limit_left()
                if remaining_count == -1:
                    await db_manager.delete_cookies(cookie)
                    raise RuntimeError("该账号剩余次数为 -1，无法使用")

                # 测试并发集
                # yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object":
                # "chat.completion.chunk", "model": ModelVersion, "created": timeStamp, "choices": [{"index": 0,
                # "delta": {"content": str(cookie)}, "finish_reason": None}]})}\n\n"""
                # yield f"""data:""" + ' ' + f"""[DONE]\n\n"""
                # return

            _return_ids = False
            _return_tags = False
            _return_title = False
            _return_prompt = False
            _return_image_url = False
            _return_video_url = False
            _return_audio_url = False
            _return_Forever_url = False

            token, sid = await song_gen.get_auth_token(w=1)

            # suno_auth.set_session_id(sid)
            # suno_auth.load_cookie(cookie)

            response = await generate_music(data=data, token=token)
            # await asyncio.sleep(3)
            clip_ids = await get_clips_ids(response)
            song_id_1 = clip_ids[0]
            song_id_2 = clip_ids[1]
            if not song_id_1 and not song_id_2:
                raise Exception("生成clip_ids为空")

            tem_text = "\n### 🤯 Creating\n\n```suno\n{prompt:" + f"{chat_user_message}" + "}\n```\n\n"
            yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": ModelVersion, "created": timeStamp, "choices": [{"index": 0, "delta": {"role": "assistant", "content": tem_text}, "finish_reason": None}]})}\n\n"""
            for clip_id in clip_ids:
                count = 0
                while True:
                    # 全部任务达成
                    # if (_return_Forever_url and _return_ids and _return_tags and
                    #         _return_title and _return_prompt and _return_image_url and _return_audio_url):
                    #     break

                    token, sid = await song_gen.get_auth_token(w=1)

                    try:
                        now_data = await get_feed(ids=clip_id, token=token)
                        more_information_ = now_data[0]['metadata']
                    except:
                        continue

                    if (now_data and
                            isinstance(now_data, list) and
                            len(now_data) > 0 and
                            isinstance(now_data[0], dict) and
                            'audio_url' in now_data[0] and
                            now_data[0]['audio_url'] == "https://cdn1.suno.ai/None.mp3"):
                        raise PromptException(f"### 🚨 违规\n\n- **歌曲提示词**：`{chat_user_message}`，"
                                              f"存在违规词，歌曲创作失败😭\n\n### "
                                              f"👀 更多\n\n**🤗请更换提示词，我会为你重新创作**🎶✨\n")

                    # 第一步：拿歌曲IDs
                    if not _return_ids:
                        try:
                            song_id_text = (f""
                                            f"### ⭐ 歌曲信息\n\n"
                                            f"- **🧩 ID1️⃣**：{song_id_1}\n"
                                            f"- **🧩 ID2️⃣**：{song_id_2}\n")
                            yield str(
                                f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": ModelVersion, "created": timeStamp, "choices": [{"index": 0, "delta": {"content": song_id_text}, "finish_reason": None}]})}\n\n""")
                            _return_ids = True
                            continue
                        except:
                            pass

                    # 第二步：拿歌曲歌名
                    elif not _return_title:
                        try:
                            title = now_data[0]["title"]
                            if title != '':
                                title_data = f"- **🤖 歌名**：{title} \n\n"
                                yield """data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": ModelVersion, "created": timeStamp, "choices": [{"index": 0, "delta": {"content": title_data}, "finish_reason": None}]})}\n\n"""
                                _return_title = True
                                continue
                        except:
                            pass

                    # 第三步：拿歌曲类型
                    elif not _return_tags:
                        try:
                            tags = more_information_["tags"]
                            if tags is not None and tags != "":
                                tags_data = f"- **💄 类型**：{tags} \n\n"
                                yield str(
                                    f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": ModelVersion, "created": timeStamp, "choices": [{"index": 0, "delta": {"content": tags_data}, "finish_reason": None}]})}\n\n""")
                                _return_tags = True
                                continue
                        except:
                            pass

                    # 第四步：拿歌曲歌词
                    elif not _return_prompt:
                        try:
                            prompt = more_information_["prompt"]
                            if prompt is not None and prompt != '':
                                prompt_data = f"### 📖 完整歌词\n\n```\n{prompt}\n```\n\n"
                                yield str(
                                    f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": ModelVersion, "created": timeStamp, "choices": [{"index": 0, "delta": {"content": prompt_data}, "finish_reason": None}]})}\n\n""")
                                _return_prompt = True
                                continue
                        except:
                            pass

                    # 第五步：拿歌曲图片
                    elif not _return_image_url:
                        try:
                            if now_data[0].get('image_url') is not None:
                                image_url_small_data = f"### 🖼️ 歌曲图片\n\n"
                                image_url_lager_data = f"![image_large_url]({now_data[0]['image_large_url']}) \n\n### 🤩 即刻享受\n"
                                yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": ModelVersion, "created": timeStamp, "choices": [{"index": 0, "delta": {"content": image_url_small_data}, "finish_reason": None}]})}\n\n"""
                                yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": ModelVersion, "created": timeStamp, "choices": [{"index": 0, "delta": {"content": image_url_lager_data}, "finish_reason": None}]})}\n\n"""
                                _return_image_url = True
                                continue
                        except:
                            pass

                    # 第六步：拿歌曲实时链接
                    elif not _return_audio_url:
                        try:
                            if 'audio_url' in now_data[0]:
                                audio_url_ = now_data[0]['audio_url']
                                if audio_url_ != '':
                                    audio_url_1 = f'https://audiopipe.suno.ai/?item_id={song_id_1}'
                                    audio_url_2 = f'https://audiopipe.suno.ai/?item_id={song_id_2}'

                                    audio_url_data_1 = f"\n- **🔗 实时音乐1️⃣**：{audio_url_1}"
                                    audio_url_data_2 = f"\n- **🔗 实时音乐2️⃣**：{audio_url_2}\n\n### 🚀 生成CDN链接中（2min~）\n\n"
                                    yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": ModelVersion, "created": timeStamp, "choices": [{"index": 0, "delta": {"content": audio_url_data_1}, "finish_reason": None}]})}\n\n"""
                                    yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": ModelVersion, "created": timeStamp, "choices": [{"index": 0, "delta": {"content": audio_url_data_2}, "finish_reason": None}]})}\n\n"""
                                    _return_audio_url = True
                                    continue
                        except:
                            pass

                    # 第六步：拿歌曲CDN链接，没有获取到，则
                    if (_return_ids and _return_tags and _return_title and _return_prompt and
                            _return_image_url and _return_audio_url):
                        if not _return_Forever_url:
                            try:
                                if check_status_complete(now_data, start_time):
                                    Aideo_Markdown_Conetent = (f""
                                                               f"\n\n### 🎷 CDN音乐链接\n\n"
                                                               f"- **🎧 音乐1️⃣**：{'https://cdn1.suno.ai/' + clip_id + '.mp3'} \n"
                                                               f"- **🎧 音乐2️⃣**：{'https://cdn1.suno.ai/' + song_id_2 + '.mp3'} \n")
                                    Video_Markdown_Conetent = (f""
                                                               f"\n### 📺 CDN视频链接\n\n"
                                                               f"- **📽️ 视频1️⃣**：{'https://cdn1.suno.ai/' + song_id_1 + '.mp4'} \n"
                                                               f"- **📽️ 视频2️⃣**：{'https://cdn1.suno.ai/' + song_id_2 + '.mp4'} \n"
                                                               f"\n### 👀 更多\n\n"
                                                               f"**🤗还想听更多歌吗，快来告诉我**🎶✨\n")
                                    yield str(
                                        f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": ModelVersion, "created": timeStamp, "choices": [{"index": 0, "delta": {"content": Aideo_Markdown_Conetent}, "finish_reason": None}]})}\n\n""")
                                    yield str(
                                        f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": ModelVersion, "created": timeStamp, "choices": [{"index": 0, "delta": {"content": Video_Markdown_Conetent}, "finish_reason": None}]})}\n\n""")
                                    yield f"""data:""" + ' ' + f"""[DONE]\n\n"""
                                    _return_Forever_url = True
                                    break

                                else:
                                    count += 1
                                    if count % 34 == 0:
                                        content_wait = "🎵\n"
                                    else:
                                        content_wait = "🎵"
                                    yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": ModelVersion, "created": timeStamp, "choices": [{"index": 0, "delta": {"content": content_wait}, "finish_reason": None}]})}\n\n"""
                                    await asyncio.sleep(3)
                                    continue
                            except:
                                pass
                # 结束while
                break
            # 结束对songid的for重试
            break

        except PromptException as e:
            yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": ModelVersion, "created": timeStamp, "choices": [{"index": 0, "delta": {"content": str(e)}, "finish_reason": None}]})}\n\n"""
            yield f"""data:""" + ' ' + f"""[DONE]\n\n"""
            # 结束请求重试
            break

        except Exception as e:
            if try_count < RETRIES:
                logger.error(f"第 {try_count + 1} 次尝试歌曲失败，错误为：{str(e)}，重试中......")
                continue
            else:
                logger.error(f"生成歌曲错误，尝试歌曲到达最大次数，错误为：{str(e)}")
                yield f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": ModelVersion, "created": timeStamp, "choices": [{"index": 0, "delta": {"content": str(e)}, "finish_reason": None}]})}\n\n"""
                yield f"""data:""" + ' ' + f"""[DONE]\n\n"""

        finally:
            if song_gen is not None:
                await song_gen.close_session()
            if cookie is not None:
                await deleteSongID(db_manager, cookie)


# 返回消息，使用协程
async def response_async(start_time, db_manager, data, content_all, chat_id, timeStamp, last_user_content, headers):
    if not data.stream:
        try:
            async for data_string in generate_data(start_time, db_manager, last_user_content,
                                                   chat_id, timeStamp, data.model):
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
            data_generator = generate_data(start_time, db_manager, last_user_content, chat_id, timeStamp, data.model)
            return StreamingResponse(data_generator, headers=headers, media_type="text/event-stream")
        except Exception as e:
            return JSONResponse(status_code=500, content={"detail": f"生成流式响应时出错: {str(e)}"})


# 线程用于请求
def request_chat(start_time, db_manager, data, content_all, chat_id, timeStamp, last_user_content, headers):
    loop = asyncio.new_event_loop()
    result = None
    try:
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            response_async(start_time, db_manager, data, content_all, chat_id, timeStamp, last_user_content, headers))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"请求聊天时出错: {str(e)}")
    finally:
        loop.close()
        return result
