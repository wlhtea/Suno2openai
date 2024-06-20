from aiohttp import ClientSession
from fake_useragent import UserAgent

from util import utils
from util.logger import logger

ua = UserAgent(browsers=["edge"])

get_session_url = "https://clerk.suno.com/v1/client?_clerk_js_version=4.73.2"

exchange_token_url = (
    "https://clerk.suno.com/v1/client/sessions/{sid}/tokens?_client?_clerk_js_version=4.73.2"
)

base_url = "https://studio-api.suno.ai"

browser_version = "edge101"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) \
        Gecko/20100101 Firefox/117.0",
    "Impersonate": browser_version,
    # "Accept-Encoding": "gzip, deflate, br",
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
        self.headers = {
            "Accept-Encoding": "gzip, deflate, br",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) \
                Gecko/20100101 Firefox/117.0",
            "Impersonate": browser_version,
        }
        self.cookie = cookie
        self.request_session = ClientSession()
        self.request_session.cookie_jar.update_cookies(utils.parse_cookie_string(self.cookie))

        self.token_session = ClientSession()
        self.token_session.cookie_jar.update_cookies(utils.parse_cookie_string(self.cookie))

    async def init_limit_session(self) -> None:
        try:
            auth_token = await self.get_auth_token()
            self.headers["Authorization"] = f"Bearer {auth_token}"
            self.headers["user-agent"] = ua.random
            self.request_session.headers.update(self.headers)
        except Exception as e:
            raise Exception(f"初始化失败,请检查cookie是否有效: {e}")

    async def close_session(self):
        if self.request_session is not None:
            await self.request_session.close()
            self.request_session = None
        if self.token_session is not None:
            await self.token_session.close()
            self.token_session = None

    async def get_auth_token(self, w=None):
        try:
            async with self.token_session.get(get_session_url, headers=HEADERS) as response_sid:
                data_sid = await response_sid.json()
                r = data_sid.get("response")
                if not r or not r.get('sessions'):
                    raise Exception("No session data in response")
                sid = r['sessions'][0].get('id')
                if not sid:
                    raise Exception("Failed to get session id")
            async with self.token_session.post(exchange_token_url.format(sid=sid), headers=HEADERS) as response_jwt:
                data_jwt = await response_jwt.json()
                jwt_token = data_jwt.get('jwt')
                if not jwt_token:
                    raise Exception("Failed to get JWT token")
            if w is not None:
                return jwt_token, sid
            return jwt_token
        except Exception as e:
            raise Exception(f"获取get_auth_token失败: {e}")

    async def get_limit_left(self) -> int:
        await self.init_limit_session()
        try:
            async with self.request_session.get("https://studio-api.suno.ai/api/billing/info/") as r:
                try:
                    r.raise_for_status()
                    data = await r.json()
                    return int(data["total_credits_left"] / 10)
                except Exception as e:
                    logger.error(f"获取剩余次数失败: {e}")
                    return -1
        except Exception as e:
            logger.error(f"获取get_limit_left失败: {e}")
            return -1
