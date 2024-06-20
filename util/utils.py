import json
import os
from http.cookies import SimpleCookie

import aiohttp
from curl_cffi.requests import Cookies
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL")

COMMON_HEADERS = {
    'Content-Type': 'text/plain;charset=UTF-8',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/123.0.0.0 Safari/537.36',
    "Referer": "https://app.suno.ai/",
    "Origin": "https://app.suno.ai",
}


async def fetch(url, headers=None, data=None, method="POST"):
    try:
        if headers is None:
            headers = {}
        headers.update(COMMON_HEADERS)
        if data is not None:
            data = json.dumps(data)

        async with aiohttp.ClientSession() as session:
            async with session.request(method=method, url=url, data=data, headers=headers) as resp:
                return await resp.json()
    except Exception as e:
        raise ValueError(f"Error fetching data: {e}")


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
            "Authorization": f"Bearer {token}"
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
