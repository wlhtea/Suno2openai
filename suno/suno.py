# -*- coding:utf-8 -*-
from aiohttp import ClientSession
from fake_useragent import UserAgent
from util.logger import logger
from util import utils
from util.config import PROXY
from util.logger import logger
import asyncio

ua = UserAgent(browsers=["edge"])

get_session_url = "https://clerk.suno.com/v1/client?__clerk_api_version=2024-10-01&_clerk_js_version=5.43.2&_method=PATCH"

exchange_token_url = (
    "https://clerk.suno.com/v1/client/sessions/{sid}/tokens?_client??__clerk_api_version=2024-10-01&_clerk_js_version=5.43.2"
)

base_url = "https://studio-api.suno.ai"

browser_version = "edge101"

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
    # 初始化
    def __init__(self, cookie: str) -> None:
        try:
            self.token_headers = {
                "accept": "*/*",
                "accept-encoding": "gzip, deflate, br, zstd",
                "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
                "cache-control": "no-cache",
                "content-type": "application/x-www-form-urlencoded",
                "origin": "https://suno.com",
                "pragma": "no-cache",
                "priority": "u=1, i",
                "referer": "https://suno.com/",
                "sec-ch-ua": '"Chromium";v="130", "Microsoft Edge";v="130", "Not?A_Brand";v="99"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0"
            }
            
            self.request_headers = self.token_headers.copy()
            self.cookie_string = utils.parse_cookie_string(cookie)
            self.request_session = None
            self.token_session = ClientSession()
            self.token_session.cookie_jar.update_cookies(self.cookie_string)
            self.site_keys = ["0x4AAAAAAAFV93qQdS0ycilX", "0x4AAAAAAAWXJGBD7bONzLBd"]
            self.site_urls = [
                "https://clerk.suno.com/cloudflare/turnstile/v0/api.js?render=explicit&__clerk_api_version=2024-10-01&_clerk_js_version=5.43.2",
                "https://suno.com/",
                "https://clerk.suno.com/v1/client?__clerk_api_version=2024-10-01&_clerk_js_version=5.43.2&_method=PATCH"
            ]
        except Exception as e:
            raise Exception(f"初始化失败,请检查cookie是否有效: {e}")

    # 初始化request_session会话
    async def init_limit_session(self) -> None:
        try:
            self.request_session = ClientSession()
            self.request_session.cookie_jar.update_cookies(self.cookie_string)
            auth_token = await self.get_auth_token()
            self.request_headers["Authorization"] = f"Bearer {auth_token}"
            self.request_headers["user-agent"] = ua.edge
            self.request_session.headers.update(self.request_headers)
        except Exception as e:
            raise Exception(f"初始化获取get_auth_token失败,请检查cookie是否有效: {e}")

    # 关闭会话
    async def close_session(self):
        if self.request_session is not None:
            try:
                await self.request_session.close()
            except Exception as e:
                logger.error(f"Error closing request session: {e}")
            finally:
                self.request_session = None
        if self.token_session is not None:
            try:
                await self.token_session.close()
            except Exception as e:
                logger.error(f"Error closing token session: {e}")
            finally:
                self.token_session = None
        if hasattr(self, 'hcaptcha_session'):
            try:
                await self.hcaptcha_session.close()
            except Exception as e:
                logger.error(f"Error closing hcaptcha session: {e}")
            finally:
                delattr(self, 'hcaptcha_session')

    # 获取token
    async def get_auth_token(self, w=None):
        try:
            logger.info("Starting get_auth_token process...")
            
            # 构建完整的URL
            url = "https://clerk.suno.com/v1/client"
            params = {
                "__clerk_api_version": "2024-10-01",
                "_clerk_js_version": "5.43.2",
                "_method": "PATCH"
            }
            
            # 设置请求头
            headers = {
                "accept": "*/*",
                "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
                "cache-control": "no-cache",
                "content-type": "application/x-www-form-urlencoded",
                "origin": "https://suno.com",
                "pragma": "no-cache",
                "priority": "u=1, i",
                "referer": "https://suno.com/",
                "sec-ch-ua": '"Chromium";v="130", "Microsoft Edge";v="130", "Not?A_Brand";v="99"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
                "cookie": self.cookie_string
            }
            
            logger.info(f"Using URL: {url}")
            logger.info(f"With params: {params}")
            logger.info(f"With headers: {headers}")
            
            async with self.token_session.post(url, 
                                             params=params,
                                             headers=headers, 
                                             proxy=PROXY) as response_sid:
                status = response_sid.status
                logger.info(f"Initial response status: {status}")
                text = await response_sid.text()
                logger.info(f"Initial response text: {text}")
                
                if status == 401:
                    logger.warning("Received 401 Unauthorized, attempting to solve CAPTCHA...")
                    
                    # 尝试不同的组合
                    total_combinations = len(self.site_keys) * len(self.site_urls)
                    for combination_index in range(total_combinations):
                        logger.info(f"Trying combination index: {combination_index}")
                        captcha_token = await self.get_captcha_token(combination_index)
                        if not captcha_token:
                            logger.error(f"Failed to get captcha token for combination index: {combination_index}")
                            continue
                        
                        # 构建带有captcha token的请求数据
                        data = {
                            'captcha_token': captcha_token,
                            'captcha_widget_type': 'invisible'
                        }
                        
                        logger.info(f"Retrying with CAPTCHA token: {captcha_token[:50]}...")
                        
                        # 重新发送请求
                        async with self.token_session.post(url,
                                                         params=params,
                                                         headers=headers,
                                                         data=data,
                                                         proxy=PROXY) as retry_response:
                            status = retry_response.status
                            logger.info(f"Retry response status: {status}")
                            text = await retry_response.text()
                            logger.info(f"Retry response text: {text}")
                            
                            if status == 200:
                                logger.info(f"Successful response with combination index: {combination_index}")
                                data_sid = await retry_response.json()
                                return data_sid
                            else:
                                logger.error(f"Retry with combination index {combination_index} failed: {text}")
                else:
                    data_sid = await response_sid.json()
                    return data_sid
                
            logger.error("Failed to authenticate after trying all combinations.")
            return None
        except Exception as e:
            logger.error(f"获取get_auth_token失败: {str(e)}")
            raise

    # 获取剩余次数
    async def get_limit_left(self) -> int:
        if self.request_session is None:
            await self.init_limit_session()
        try:
            response = await self.request_session.get("https://studio-api.suno.ai/api/billing/info/", proxy=PROXY)
            try:
                response.raise_for_status()
                data = await response.json()
                return int(data["total_credits_left"] / 10)
            except Exception as e:
                logger.error(f"获取剩余次数失败: {e}")
                return -1
        except Exception as e:
            logger.error(f"获取get_limit_left失败: {e}")
            return -1

    async def get_hcaptcha_config(self) -> str:
        """获取hcaptcha配置"""
        try:
            url = "https://api.hcaptcha.com/checksiteconfig"
            params = {
                "v": "b4956db",
                "host": "suno.com",
                "sitekey": "d65453de-3f1a-4aac-9366-a0f06e52b2ce",
                "sc": "1",
                "swa": "1",
                "spst": "1"
            }
            
            headers = {
                "accept": "application/json",
                "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
                "cache-control": "no-cache",
                "content-type": "text/plain",
                "origin": "https://newassets.hcaptcha.com",
                "pragma": "no-cache",
                "priority": "u=1, i",
                "referer": "https://newassets.hcaptcha.com/",
                "sec-ch-ua": '"Chromium";v="130", "Microsoft Edge";v="130", "Not?A_Brand";v="99"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "user-agent": ua.edge
            }

            if not hasattr(self, 'hcaptcha_session'):
                self.hcaptcha_session = ClientSession()

            async with self.hcaptcha_session.post(url, params=params, headers=headers, proxy=PROXY) as response:
                logger.info(f"Response from hcaptcha_session: {response}")
                if response.status == 200:
                    data = await response.json()
                    logger.info("Successfully got hcaptcha config")
                    if 'c' in data and 'req' in data['c']:
                        req = data['c']['req']
                        logger.info(f"Got hcaptcha req: {req}")
                        return req
                    else:
                        logger.error("No req found in response")
                        return ""
                else:
                    logger.error(f"Failed to get hcaptcha config, status: {response.status}")
                    return ""
        except Exception as e:
            logger.error(f"Error getting hcaptcha config: {e}")
            return ""
        finally:
            if hasattr(self, 'hcaptcha_session'):
                await self.hcaptcha_session.close()
                delattr(self, 'hcaptcha_session')

    async def get_captcha_token(self, combination_index: int) -> str:
        """获取 captcha token"""
        try:
            api_key = ""
            site_keys = ["0x4AAAAAAAFV93qQdS0ycilX", "0x4AAAAAAAWXJGBD7bONzLBd"]
            site_urls = [
                "https://clerk.suno.com/cloudflare/turnstile/v0/api.js?render=explicit&__clerk_api_version=2024-10-01&_clerk_js_version=5.43.2",
                "https://suno.com/",
                "https://clerk.suno.com/v1/client?__clerk_api_version=2024-10-01&_clerk_js_version=5.43.2&_method=PATCH"
            ]

            # 计算组合总数
            total_combinations = len(site_keys) * len(site_urls)
            
            if combination_index < 0 or combination_index >= total_combinations:
                logger.error(f"Invalid combination index: {combination_index}")
                return ""

            # 计算当前组合的 site_key 和 site_url
            site_key_index = combination_index // len(site_urls)
            site_url_index = combination_index % len(site_urls)
            
            site_key = site_keys[site_key_index]
            site_url = site_urls[site_url_index]
            
            logger.info(f"Trying combination index {combination_index}: site_key: {site_key}, site_url: {site_url}")
            
            # 创建任务
            payload = {
                "clientKey": api_key,
                "task": {
                    "type": "AntiTurnstileTaskProxyLess",
                    "websiteURL": site_url,
                    "websiteKey": site_key,
                    "metadata": {
                        "action": "invisible"  # 设置为 invisible，因为 widgetType 是 'invisible'
                    }
                }
            }
            
            if not hasattr(self, 'captcha_session'):
                self.captcha_session = ClientSession()
                
            # 创建任务
            async with self.captcha_session.post(
                "https://api.capsolver.com/createTask",
                json=payload
            ) as response:
                data = await response.json()
                
                if data.get("errorId", 0) != 0:
                    logger.error(f"Failed to create task with site_key: {site_key} and site_url: {site_url}, error: {data}")
                    return ""
                    
                task_id = data.get("taskId")
                if not task_id:
                    logger.error(f"No taskId in response with site_key: {site_key} and site_url: {site_url}")
                    return ""
                    
                logger.info(f"Got taskId: {task_id} / Getting result...")
                
                # 轮询获取结果
                while True:
                    await asyncio.sleep(1)  # 每秒检查一次
                    
                    status_payload = {
                        "clientKey": api_key,
                        "taskId": task_id
                    }
                    
                    async with self.captcha_session.post(
                        "https://api.capsolver.com/getTaskResult",
                        json=status_payload
                    ) as status_response:
                        status_data = await status_response.json()
                        
                        if status_data.get("errorId", 0) != 0:
                            logger.error(f"Error getting result with site_key: {site_key} and site_url: {site_url}, error: {status_data}")
                            return ""
                            
                        status = status_data.get("status")
                        if status == "ready":
                            token = status_data.get("solution", {}).get("token")
                            if token:
                                logger.info(f"Got token with site_key: {site_key} and site_url: {site_url}: {token[:50]}...")
                                return token
                            else:
                                logger.error(f"No token in solution with site_key: {site_key} and site_url: {site_url}")
                                return ""
                        elif status == "failed":
                            logger.error(f"Solve failed with site_key: {site_key} and site_url: {site_url}, error: {status_data}")
                            return ""
                        
        except Exception as e:
            logger.error(f"Error in get_captcha_token: {e}")
            return ""
        finally:
            if hasattr(self, 'captcha_session'):
                await self.captcha_session.close()
                delattr(self, 'captcha_session')
