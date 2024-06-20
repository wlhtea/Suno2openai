import contextlib
import json
import os
import random
import re
import time
from http.cookies import SimpleCookie
from typing import Tuple
from typing import Union

from curl_cffi import requests
from curl_cffi.requests import Cookies
from dotenv import load_dotenv, find_dotenv
from fake_useragent import UserAgent
from requests import get as rget

from util.logger import logger

_ = load_dotenv(find_dotenv())

ua = UserAgent(browsers=["edge"])

get_session_url = "https://clerk.suno.com/v1/client?_clerk_js_version=4.73.2"
exchange_token_url = (
    "https://clerk.suno.com/v1/client/sessions/{sid}/tokens?_client?_clerk_js_version=4.73.2"
)

base_url = "https://studio-api.suno.ai"
browser_version = "edge101"

HEADERS = {
    "Accept-Encoding": "gzip, deflate, br",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) \
        Gecko/20100101 Firefox/117.0",
}

MUSIC_GENRE_LIST = [
    "African",
    "Asian",
    "South and southeast Asian",
    "Avant-garde",
    "Blues",
    "Caribbean and Caribbean-influenced",
    "Comedy",
    "Country",
    "Easy listening",
    "Electronic",
    "Folk",
    "Hip hop",
    "Jazz",
    "Latin",
    "Pop",
    "R&B and soul",
    "Rock",
]


class SongsGen:
    def __init__(self, cookie: str) -> None:
        try:
            self.session: requests.Session = requests.Session()
            HEADERS["user-agent"] = ua.random
            self.cookie = cookie
            self.session.cookies = self.parse_cookie_string(self.cookie)
            auth_token = self.get_auth_token()
            HEADERS["Authorization"] = f"Bearer {auth_token}"
            self.session.headers = HEADERS
            self.sid = None
            self.retry_time = 0
            self.song_info_dict = {}
            self.now_data = {}
        except Exception as e:
            raise Exception(f"初始化失败,请检查cookie是否有效: {e}")

    def get_auth_token(self, w=None):
        try:
            response = self.session.get(get_session_url, impersonate=browser_version)
            data = response.json()

            r = data.get("response")
            if not r or not r.get('sessions'):
                raise Exception("No session data in response")

            sid = r['sessions'][0].get('id')
            if not sid:
                raise Exception("Failed to get session id")

            self.sid = sid

            response = self.session.post(
                exchange_token_url.format(sid=sid), impersonate=browser_version
            )
            data = response.json()
            jwt_token = data.get('jwt')
            if not jwt_token:
                raise Exception("Failed to get JWT token")

            if w is not None:
                return jwt_token, sid
            return jwt_token

        except Exception as e:
            raise Exception(f"获取get_auth_token失败: {e}")

    def _renew_auth_token(self):
        auth_token = self.get_auth_token()
        HEADERS["Authorization"] = f"Bearer {auth_token}"
        self.session.headers = HEADERS

    @staticmethod
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

    def get_song_library(self):
        try:
            self._renew_auth_token()
            page_number = 1
            result = []
            while 1:
                logger.info(f"Getting page {page_number} data.")
                url = f"https://studio-api.suno.ai/api/feed/?page={page_number}"
                response = self.session.get(url, impersonate=browser_version)
                data = response.json()
                if page_number == 3:
                    break
                if len(data) < 20:
                    result.extend(data)
                    break
                # spider rule
                time.sleep(2)
                if page_number % 3 == 0:
                    self._renew_auth_token()
                page_number += 1
                result.extend(data)
            return result
        except Exception as e:
            raise Exception(f"获取get_song_library失败: {e}")

    def get_limit_left(self) -> int:
        try:
            r = self.session.get(
                "https://studio-api.suno.ai/api/billing/info/",
                headers={"Impersonate": "browser_version"}
            )
            try:
                r.raise_for_status()
                return int(r.json()["total_credits_left"] / 10)
            except Exception as e:
                logger.error(f"获取剩余次数失败: {e}")
                return -1
        except Exception as e:
            logger.error(f"获取get_limit_left失败: {e}")
            return -1

    @staticmethod
    def _parse_lyrics(data: dict) -> Tuple[str, str]:
        try:
            song_name = data.get("title", "")
            mt = data.get("metadata")
            if (
                    not mt
            ):  # Remove checking for title because custom songs have no title if not specified
                return "", ""
            lyrics = re.sub(r"\[.*?]", "", mt.get("prompt"))
            return song_name, lyrics

        except Exception as e:
            raise Exception(f"获取_parse_lyrics失败: {e}")

    def _fetch_songs_metadata(self, ids):
        id1, id2 = ids[:2]
        url = f"https://studio-api.suno.ai/api/feed/?ids={id1}%2C{id2}"
        response = self.session.get(url, impersonate=browser_version)
        data = response.json()
        if type(data) == dict:
            if data.get("detail", "") == "Unauthorized":
                song_name, lyric = self._parse_lyrics(self.now_data[0])
                self.song_info_dict["song_name"] = song_name
                self.song_info_dict["lyric"] = lyric
                self.song_info_dict["song_url"] = (
                    f"https://audiopipe.suno.ai/?item_id={id1}"
                )
                logger.info("Token expired, will sleep 30 seconds and try to download")
                time.sleep(30)
                # Done here
                return True
            else:
                data = [data]
        # renew now data
        self.now_data = data
        try:
            for d in data:
                # only get one url for now TODO: See if possible for both urls
                # and early return
                if audio_url := d.get("audio_url"):
                    song_name, lyric = self._parse_lyrics(d)
                    self.song_info_dict["song_name"] = song_name
                    self.song_info_dict["lyric"] = lyric
                    self.song_info_dict["song_url"] = audio_url
                    return True
            return False
        except Exception as e:
            logger.info(e)
            # since we only get the music_id is ok
            # so we can make the id here and sleep some time
            logger.info("Will sleep 30s and get the music url")
            time.sleep(30)
            song_name, lyric = self._parse_lyrics(self.now_data[0])
            self.song_info_dict["song_name"] = song_name
            self.song_info_dict["lyric"] = lyric
            self.song_info_dict["song_url"] = (
                f"https://audiopipe.suno.ai/?item_id={id1}"
            )
            # Done here
            return True

    def get_songs(
            self,
            prompt: str,
            tags: Union[str, None] = None,
            title: str = "",
            make_instrumental: bool = False,
            is_custom: bool = False,
    ) -> dict:
        try:
            url = f"{base_url}/api/generate/v2/"
            self.session.headers["user-agent"] = ua.random
            payload = {
                "gpt_description_prompt": prompt,
                # chirp-v3-5
                "mv": "chirp-v3-0",
                "prompt": "",
                "make_instrumental": make_instrumental,
            }
            if is_custom:
                payload["prompt"] = prompt
                payload["gpt_description_prompt"] = ""
                payload["title"] = title
                if not tags:
                    payload["tags"] = random.choice(MUSIC_GENRE_LIST)
                else:
                    payload["tags"] = tags
                logger.info(payload)
            response = self.session.post(
                url,
                data=json.dumps(payload),
                impersonate=browser_version,
            )
            if not response.ok:
                logger.info(response.text)
                raise Exception(f"Error response {str(response)}")
            response_body = response.json()
            songs_meta_info = response_body["clips"]
            request_ids = [i["id"] for i in songs_meta_info]
            start_wait = time.time()
            logger.info("Waiting for results...")
            logger.info(".", end="", flush=True)
            sleep_time = 10
            while True:
                if int(time.time() - start_wait) > 600:
                    raise Exception("Request timeout")
                # TODOs support all mp3 here
                song_info = self._fetch_songs_metadata(request_ids)
                # spider rule
                if sleep_time > 2:
                    time.sleep(sleep_time)
                    sleep_time -= 1
                else:
                    time.sleep(2)

                if not song_info:
                    logger.info(".", end="", flush=True)
                else:
                    break
            # keep the song info dict as old api
            return self.song_info_dict
        except Exception as e:
            raise Exception(f"获取get_songs失败: {e}")

    def save_songs(
            self,
            prompt: str,
            output_dir: str = "./output",
            tags: Union[str, None] = None,
            title: Union[str, None] = None,
            make_instrumental: bool = False,
            is_custom: bool = False,
    ) -> None:
        mp3_index = 0
        try:
            self.get_songs(
                prompt,
                tags=tags,
                title=title,
                is_custom=is_custom,
                make_instrumental=make_instrumental,
            )  # make the info dict
            song_name = self.song_info_dict["song_name"]
            lyric = self.song_info_dict["lyric"]
            link = self.song_info_dict["song_url"]
        except Exception as e:
            raise Exception(f"save_songs失败: {e}")
        with contextlib.suppress(FileExistsError):
            os.mkdir(output_dir)
        logger.info()
        while os.path.exists(os.path.join(output_dir, f"suno_{mp3_index}.mp3")):
            mp3_index += 1
        logger.info(link)
        response = rget(link, allow_redirects=False, stream=True)
        if response.status_code != 200:
            raise Exception("Could not download song")
        # save response to file
        with open(
                os.path.join(output_dir, f"suno_{mp3_index + 1}.mp3"), "wb"
        ) as output_file:
            for chunk in response.iter_content(chunk_size=1024):
                # If the chunk is not empty, write it to the file.
                if chunk:
                    output_file.write(chunk)
        if not song_name:
            song_name = "Untitled"
        with open(
                os.path.join(output_dir, f"{song_name.replace(' ', '_')}.lrc"),
                "w",
                encoding="utf-8",
        ) as lyric_file:
            lyric_file.write(f"{song_name}\n\n{lyric}")
