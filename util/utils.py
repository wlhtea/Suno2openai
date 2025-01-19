import json
import os
from http.cookies import SimpleCookie

import aiohttp
from curl_cffi.requests import Cookies
from dotenv import load_dotenv

from util.config import PROXY

load_dotenv()

BASE_URL = os.getenv("BASE_URL")

COMMON_HEADERS = {
    'Content-Type': 'text/plain;charset=UTF-8',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/123.0.0.0 Safari/537.36',
    "Referer": "https://app.suno.ai/",
    "Origin": "https://app.suno.ai",
}


async def fetch(url, headers=None, data=None, method="POST", captcha_token=None):
    try:
        if headers is None:
            headers = {}
        headers.update(COMMON_HEADERS)
        
        # 如果提供了captcha_token，添加到请求头中
        if captcha_token:
            headers['X-Captcha-Token'] = captcha_token
            
        if data is not None:
            data = json.dumps(data)

        async with aiohttp.ClientSession() as session:
            async with session.request(method=method, url=url, data=data, headers=headers, proxy=PROXY) as resp:
                if resp.status != 200:
                    raise ValueError(f"请求状态码：{resp.status}，请求报错：{await resp.text()}")
                return await resp.json()
    except Exception as e:
        raise ValueError(f"Error fetching data:{e}")


async def get_feed(ids, token):
    try:
        headers = {
            "Authorization": f"Bearer {token}"
        }
        api_url = f"{BASE_URL}/api/feed/?ids={ids}"
        response = await fetch(api_url, headers, method="GET")
        return response
    except Exception as e:
        raise ValueError(f"Error fetching feed: {e}")


async def generate_music(data, token):
    try:
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Access-Control-Request-Headers": "affiliate-id,authorization",
            "Access-Control-Request-Method": "POST",
            "Origin": "https://suno.com",
            "Priority": "u=1, i",
            "Referer": "https://suno.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
        }
        api_url = f"{BASE_URL}/api/generate/v2/"
        response = await fetch(api_url, headers, data)
        return response
    except Exception as e:
        raise ValueError(f"Error generating music: {e}")


async def generate_lyrics(prompt, token):
    try:
        headers = {
            "Authorization": f"Bearer {token}"
        }
        api_url = f"{BASE_URL}/api/generate/lyrics/"
        data = {"prompt": prompt}
        return await fetch(api_url, headers, data)
    except Exception as e:
        raise ValueError(f"Error generating lyrics: {e}")


async def get_lyrics(lid, token):
    try:
        headers = {
            "Authorization": f"Bearer {token}"
        }
        api_url = f"{BASE_URL}/api/generate/lyrics/{lid}"
        return await fetch(api_url, headers, method="GET")
    except Exception as e:
        raise ValueError(f"Error getting lyrics: {e}")


def parse_cookie_string(cookie_string: str) -> Cookies:
    cookie = SimpleCookie()
    cookie.load(cookie_string)
    cookies_dict = {}
    try:
        for key, morsel in cookie.items():
            cookies_dict[key] = morsel.value
    except (IndexError, AttributeError) as e:
        raise Exception(f"解析cookie时出错: {e}")
    return Cookies(cookies_dict)
