# from time import sleep
# from suno import SongsGen
# import requests
# import json
# from utils import generate_music
#
# async def test_generate_music():
#     headers = {'Content-Type': 'application/json'}
#     cookie = "__cf_bm=i3sHy2TPuISxCLdmwkI0R5puBJY2j4QTOTCg_2kDJOU-1711702648-1.0.1.1-pFK4ilr0C4Qqx3Z4ZAkRfkkNhS5O0nKcc1RxOj8_RT_eQv0v3KXjsZ2nKboYVS4C3GD8mtxcwi9JDqMk2e1pnw; _cfuvid=aVgBFWw4IgNNoz8V8mzxTttlMBafpVcdhcqCS8W8lUs-1711702648239-0.0.1.1-604800000; __client=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImNsaWVudF8yZU03Ylh4M0ZGNFJTNWwySkZWR1F5bWh5M2QiLCJyb3RhdGluZ190b2tlbiI6IjljN2p5c2VtamZwZDdvcnQ4eHg3OTBuMDY2bjh0Z3R5bG5ncWszdzcifQ.xJ6KtgrmAowM3BshBVWl0y5f-9KiY8JP2GiuxEOSnm4BNQYF6L4UEnHnTkJp4D-tXndzjUAvcQn1osytZMnaWVdxHO9ti5T0166OmJjAB-Saimik1H20mQyReAbCex8Lup4fIE9cilSA-2bXLNNymGIEEcQ23skSoxjaj0tY6ezmrJask1GZRxjWCYCE6qXX_q91IkbUlDsf46Zq7-1E1hSvJ3BjDFrChUlhY8W-h997YNeSq-mTbF9owz8xVRRJoS6opDSSSrw1Cry98Be_LavBsayjD1TY9LkjDTYbgnPo8J17I_ggEnlTOFPiLcYo_PLQezVaHL_7Kf-BCBGE2A; __client_uat=1711702694; mp_26ced217328f4737497bd6ba6641ca1c_mixpanel=%7B%22distinct_id%22%3A%20%22%24device%3A18e896da0e1c03-0591c9835cdf2a-745d5774-154ac4-18e896da0e1c03%22%2C%22%24device_id%22%3A%20%2218e896da0e1c03-0591c9835cdf2a-745d5774-154ac4-18e896da0e1c03%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%7D"
#     token,session_id = SongsGen(cookie)._get_auth_token(w=1)
#
#     data = {
#         "gpt_description_prompt" : "写一首rap",
#         # "prompt": "[Verse]\nWake up in the morning, feeling brand new\nGonna shake off the worries, leave 'em in the rearview\nStep outside, feeling the warmth on my face\nThere's something 'bout the sunshine that puts me in my place\n\n[Verse 2]\nWalking down the street, got a spring in my step\nThe rhythm in my heart, it just won't forget\nEverywhere I go, people smiling at me\nThey can feel the joy, it's contagious, can't you see?\n\n[Chorus]\nI got sunshine in my pocket, happiness in my soul\nA skip in my stride, and I'm ready to go\nNothing gonna bring me down, gonna keep on shining bright\nI got sunshine in my pocket, this world feels so right",
#         # "tags": "heartfelt anime",
#         "mv": "chirp-v3-0",
#         # "title": "Sunshine in your Pocket",
#         # "continue_clip_id": None,
#         # "continue_at": None
#         # "cookie":cookie,
#         # "session_id" : session_id,
#         # "token" : token
#     }
#     # cookies = {'cookie': cookie}
#     r = requests.post("http://127.0.0.1:8000/generate",headers=headers, data=json.dumps(data))
#     # r = await generate_music(data,token)
#     try:
#         print("json",r.json())
#         return r.json()
#     except:
#         print("text",r.text)
#         return r.text
#
#
#
# # def test_generate_lyrics():
# #     data = {
# #         "prompt":  ""
# #     }
# #
#     r = requests.post("http://127.0.0.1:8000/generate/lyrics/", data=json.dumps(data))
#     return r.json()
#
# #
# # def get_lyrics(lid):
# #     r = requests.get(f"http://127.0.0.1:8000/lyrics/{lid}")
# #     return r.json()
#
# def get_feed(aid):
#     r = requests.get(f"http://127.0.0.1:8000/feed/{aid}")
#     return r.json()
#
#
# # respones = {"id":"2fa032b6-41d5-420f-a4e2-fd8c8c944edd","clips":[{"id":"31c73f34-4d01-4389-b364-f2199987a582","video_url":"","audio_url":"","image_url":None,"image_large_url":None,"major_model_version":"v3","model_name":"chirp-v3","metadata":{"tags":"","prompt":"","gpt_description_prompt":"写一首rap","audio_prompt_id":None,"history":None,"concat_history":None,"type":"gen","duration":None,"refund_credits":None,"stream":True,"error_type":None,"error_message":None},"is_liked":False,"user_id":"b69a62ba-a301-465b-b8df-a7c3c00df909","display_name":None,"is_trashed":False,"reaction":None,"created_at":"2024-03-31T11:41:12.143Z","status":"submitted","title":"","play_count":0,"upvote_count":0,"is_public":False},{"id":"ed226e35-94a0-4938-8158-0eaf69a32f78","video_url":"","audio_url":"","image_url":None,"image_large_url":None,"major_model_version":"v3","model_name":"chirp-v3","metadata":{"tags":"","prompt":"","gpt_description_prompt":"写一首rap","audio_prompt_id":None,"history":None,"concat_history":None,"type":"gen","duration":None,"refund_credits":None,"stream":True,"error_type":None,"error_message":None},"is_liked":False,"user_id":"b69a62ba-a301-465b-b8df-a7c3c00df909","display_name":None,"is_trashed":False,"reaction":None,"created_at":"2024-03-31T11:41:12.143Z","status":"submitted","title":"","play_count":0,"upvote_count":0,"is_public":False}],"metadata":{"tags":"","prompt":"","gpt_description_prompt":"写一首rap","audio_prompt_id":None,"history":None,"concat_history":None,"type":"gen","duration":None,"refund_credits":None,"stream":True,"error_type":None,"error_message":None},"major_model_version":"v3","status":"running","created_at":"2024-03-31T11:41:12.130Z","batch_size":2}
#
# # {"id":"72daea49-81a2-41a8-802d-e9c7ad84b961","clips":[{"id":"9add873e-00c8-45fc-8a58-cecc419f2108","video_url":"","audio_url":"","image_url":None,"image_large_url":None,"major_model_version":"v2","model_name":"chirp-v2-xxl-alpha","metadata":{"tags":"","prompt":"","gpt_description_prompt":"写一首rap","audio_prompt_id":None,"history":None,"concat_history":None,"type":"gen","duration":None,"refund_credits":None,"stream":True,"error_type":None,"error_message":None},"is_liked":False,"user_id":"b69a62ba-a301-465b-b8df-a7c3c00df909","display_name":None,"is_trashed":False,"reaction":None,"created_at":"2024-03-31T11:21:12.999Z","status":"submitted","title":"","play_count":0,"upvote_count":0,"is_public":False},{"id":"2e0bed6d-0b70-4094-8d1a-98cbbb382863","video_url":"","audio_url":"","image_url":None,"image_large_url":None,"major_model_version":"v2","model_name":"chirp-v2-xxl-alpha","metadata":{"tags":"","prompt":"","gpt_description_prompt":"写一首rap","audio_prompt_id":None,"history":None,"concat_history":None,"type":"gen","duration":None,"refund_credits":None,"stream":True,"error_type":None,"error_message":None},"is_liked":False,"user_id":"b69a62ba-a301-465b-b8df-a7c3c00df909","display_name":None,"is_trashed":False,"reaction":None,"created_at":"2024-03-31T11:21:13.000Z","status":"submitted","title":"","play_count":0,"upvote_count":0,"is_public":False}],"metadata":{"tags":"","prompt":"","gpt_description_prompt":"写一首rap","audio_prompt_id":None,"history":None,"concat_history":None,"type":"gen","duration":None,"refund_credits":None,"stream":True,"error_type":None,"error_message":None},"major_model_version":"v2","status":"running","created_at":"2024-03-31T11:21:12.975Z","batch_size":2}
# respones = test_generate_music()
# id_1= ''
# id_2 = ""
# link_audio = ""
#
# clip_ids = ""
# try:
#     clip_ids = [clip["id"] for clip in respones["clips"]]
#     id_1 = clip_ids[0]
#     id_2 = clip_ids[1]
# except:
#     pass
#
# while 1:
#     if id_1 is not None:
#         now_data = get_feed(aid=id_1)
#         print(now_data)
#         sleep(5)
#         try:
#             link_audio = now_data[0]['audio_url']
#         except:
#             pass
#         if link_audio:
#             print(link_audio)
#             now_data_id2 = get_feed(id_2)
#             print(now_data_id2[0]['audio_url'])
#             break
#     print("wait.....")
# import requests
#
# r = requests.post("http://127.0.0.1:8000/v1/chat/completions")
# for i in r:
#     print(i)

import requests


def stream_response(url):
    data = {
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": "rap"},
        ],
        "stream": True
    }
    with requests.post(url, stream=True, json=data) as response:
        response.raise_for_status()  # 确保请求成功
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:  # 过滤掉“keep-alive”新的块
                print(chunk)  # 处理每个块（例如打印或保存）


# 使用函数
stream_response('https://suno.w-l-h.xyz/v1/chat/completions/')
