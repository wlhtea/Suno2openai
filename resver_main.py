import asyncio

from cookie import suno_auth
from suno import SongsGen
from utils import generate_music, get_feed


@app.post("/generate_music/")
async def main():
    cookie = "__cf_bm=J_TeFDJ20kW77entz7z535PZGIh.1J7ehgg.PcpkSPE-1711631551-1.0.1.1-4yDIcyhFDQBIG_ccJj9KvKXyPVT9lFYdUebBlBPOAKiH8cDL6_bpJUZ3fiTmWCYdvrRVJy6A6fSvNFrlS7Z.Ew; _cfuvid=8bI.ian3k6hV.vOoRX9.Bllnwf8aj4VfRG.PgthQTP4-1711631551283-0.0.1.1-604800000; __client=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImNsaWVudF8yZUpuVVFyODB0c05tTlVHeU1PNVRtQzM3cFUiLCJyb3RhdGluZ190b2tlbiI6InZtZDhndG13andqdHd0dW5mcG43ZHFnbjMwNzdtMmM5MmVyNWF3OXIifQ.RGOMUGyqmlwcnpUSm8KL9uan4f5EN1OuhjIUL60BOOqDqofRQLP2iCkHnhML1DsdmHrNJt_PMGoaLp05AIh0kUpbXUt4UNMiuEL3pjr448QK4MPTGaVbgLTxA17UbXLHK9We-FZkOIBCscW6c_faWaN_NSgycVJaxUtQ7ofNk-50dLLUfYsNZbgcI9xJkWZJ9BeiTg6dCDC_3_WRDPOUtmJlXgfLOCEyuyN52YvkdDAWRL3bOuqZ5MJWcCqlrqOh_yUSWS-k0PpDhjZ0Q10XZ54450AMQACCqY918h1vblYAbfWL2VOFMOQAV0FUqci_5prVLUtlXY10Bwv1OHk9tg; __client_uat=1711631590; mp_26ced217328f4737497bd6ba6641ca1c_mixpanel=%7B%22distinct_id%22%3A%20%22%24device%3A18e8530c03214a3-06015671c2a5bc-745d5774-154ac4-18e8530c03214a3%22%2C%22%24device_id%22%3A%20%2218e8530c03214a3-06015671c2a5bc-745d5774-154ac4-18e8530c03214a3%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%7D"
    token, sid = SongsGen(cookie)._get_auth_token(w=1)
    suno_auth.set_session_id(sid)
    suno_auth.load_cookie(cookie)
    data = {
        "token": "",
        "cookie": "",
        "session_id": "",
        "gpt_description_prompt": "写一首rap",
        "prompt": "",
        "mv": "chirp-v3-0",
        "title": "",
        "tags": ""
    }
    response = await generate_music(data=data, token=token)
    while 1:
        try:
            clip_ids = [clip["id"] for clip in response["clips"]]
            id_1 = clip_ids[0]
            id_2 = clip_ids[1]
            break
        except:
            print(response)

    while True:
        now_data = await get_feed(ids=id_1, token=token)
        if type(now_data) == dict:
            if now_data.get('detail') == 'Unauthorized':
                print(f'https://audiopipe.suno.ai/?item_id={id_1}')
                print(f'https://audiopipe.suno.ai/?item_id={id_2}')
                break
        # 这里添加逻辑处理获取到的数据，例如检查audio_url等
        await asyncio.sleep(5)  # 使用异步版本的sleep
        try:
            link_audio = now_data[0]['audio_url']
            if link_audio:
                print(link_audio)
                break
        except:
            print('wait。。。。')


# 启动主函数
asyncio.run(main())
