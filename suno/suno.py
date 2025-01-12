"""
Suno AI API Client
主要类实现
"""

from typing import Optional, Dict
from fake_useragent import UserAgent
from util.logger import logger
from util import utils
from util.config import PROXY
from .constants import URLs, DEFAULT_HEADERS, CaptchaConfig, CLERK_API_VERSION, CLERK_JS_VERSION
from .http_client import HttpClient
import asyncio

class SongsGen:
    def __init__(self, cookie: str, capsolver_apikey: str) -> None:
        if not cookie or not capsolver_apikey:
            raise ValueError("Cookie and capsolver_apikey are required")
            
        self.ua = UserAgent(browsers=["edge"])
        self.base_headers = {
            **DEFAULT_HEADERS,
            "user-agent": self.ua.edge,
        }
        
        self.capsolver_apikey = capsolver_apikey
        
        # 解析并设置cookie
        if isinstance(cookie, str):
            self.cookie_dict = utils.parse_cookie_string(cookie)
        elif isinstance(cookie, dict):
            self.cookie_dict = cookie
        else:
            raise ValueError("Cookie must be a string or dictionary")
            
        if not self.cookie_dict:
            raise ValueError("Invalid cookie format")
        
        # Initialize HTTP clients
        self.token_client = HttpClient(self.base_headers, self.cookie_dict, PROXY)
        self.request_client = HttpClient(self.base_headers, self.cookie_dict, PROXY)
        
        # 设置验证码处理器
        self.token_client.set_captcha_handler(self.get_captcha_token)
        self.request_client.set_captcha_handler(self.get_captcha_token)
        
        # 认证相关的实例变量
        self.auth_token: Optional[str] = None
        self.session_id: Optional[str] = None
        self.user_id: Optional[str] = None
        self.session_expire_at: Optional[int] = None
        
        self._closed = False
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        if self._closed:
            raise RuntimeError("SongsGen instance is closed")
            
        try:
            await self.init_clients()
            return self
        except Exception as e:
            logger.error(f"Failed to initialize SongsGen: {e}")
            await self.close()
            raise
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        try:
            await self.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            raise
        
    async def init_clients(self):
        """Initialize HTTP clients and get auth token"""
        if self._closed:
            raise RuntimeError("SongsGen instance is closed")
            
        try:
            # 只在auth_token为None时获取token
            if self.auth_token is None:
                self.auth_token = await self.get_auth_token()
                if self.auth_token:
                    self.request_client.base_headers["Authorization"] = f"Bearer {self.auth_token}"
                else:
                    raise RuntimeError("Failed to obtain auth token")
            else:
                logger.info("Auth token already exists, skipping token request")
        except Exception as e:
            logger.error(f"Failed to initialize clients: {e}")
            raise
            
    async def close(self):
        """Close all HTTP clients"""
        self._closed = True
        try:
            await asyncio.gather(
                self.token_client.close(),
                self.request_client.close(),
                return_exceptions=True
            )
        except Exception as e:
            logger.error(f"Error during close: {e}")
            raise

    async def get_auth_token(self) -> Optional[str]:
        """Get authentication token with retry and CAPTCHA handling"""
        if self._closed:
            raise RuntimeError("SongsGen instance is closed")
            
        try:
            params = {
                "__clerk_api_version": CLERK_API_VERSION,
                "_clerk_js_version": CLERK_JS_VERSION,
            }
            
            # 现在请求会自动处理401和验证码
            response = await self.token_client.request(
                "POST", 
                URLs.VERIFY, 
                params=params,
                headers={
                    "accept": "*/*",
                    "accept-language": "en-US,en;q=0.9",
                    "content-type": "application/x-www-form-urlencoded",
                    "origin": "https://suno.com",
                    "referer": "https://suno.com/",
                    "sec-ch-ua": '"Microsoft Edge";v="131", "Chromium";v="131";v="24"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"Windows"',
                    "sec-fetch-dest": "empty",
                    "sec-fetch-mode": "cors",
                    "sec-fetch-site": "same-site"
                }
            )
            
            # 检查响应结构
            if not response:
                logger.error("Empty response received from token request")
                return None
                
            # 验证响应中是否包含必要的字段
            if not isinstance(response, dict):
                logger.error(f"Unexpected response type: {type(response)}")
                return None
                
            # 提取会话信息
            sessions = response.get('sessions', [])
            if not sessions:
                logger.error("No sessions found in response")
                return None
                
            session = sessions[0]  # 获取第一个会话
            session_id = session.get('id')
            session_status = session.get('status')
            expire_at = session.get('expire_at')
            
            # 提取用户信息
            user = session.get('user', {})
            user_id = user.get('id')
            email = user.get('email_addresses', [{}])[0].get('email_address')
            name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
            
            # 记录重要信息
            logger.info(f"Session ID: {session_id}")
            logger.info(f"Session Status: {session_status}")
            logger.info(f"Session Expires: {expire_at}")
            logger.info(f"User ID: {user_id}")
            logger.info(f"User Email: {email}")
            logger.info(f"User Name: {name}")
            
            # 获取JWT令牌
            last_active_token = session.get('last_active_token', {})
            if not isinstance(last_active_token, dict):
                logger.error("Invalid token format in response")
                return None
                
            jwt = last_active_token.get('jwt')
            if not jwt:
                logger.error("No JWT token found in response")
                return None
            
            # 保存重要信息到实例变量
            self.session_id = session_id
            self.user_id = user_id
            self.session_expire_at = expire_at
            
            return jwt  # 返回JWT token而不是整个response
            
        except Exception as e:
            logger.error(f"Failed to get auth token: {e}")
            return None

    async def get_limit_left(self) -> int:
        """Get remaining credits with retry"""
        if self._closed:
            raise RuntimeError("SongsGen instance is closed")
            
        try:
            response = await self.request_client.request("GET", URLs.BILLING_INFO)
            if not isinstance(response, dict):
                logger.error(f"Unexpected response type: {type(response)}")
                return -1
                
            credits = response.get("total_credits_left", 0)
            if not isinstance(credits, (int, float)):
                logger.error(f"Invalid credits value: {credits}")
                return -1
                
            return int(credits / 10)
        except Exception as e:
            logger.error(f"Failed to get remaining credits: {e}")
            return -1
            
    async def get_captcha_token(self, combination_index: int, cookies: Optional[Dict] = None) -> Optional[str]:
        """Get CAPTCHA token with improved error handling and cookie support"""
        try:
            site_key_index = combination_index // len(CaptchaConfig.SITE_URLS)
            site_url_index = combination_index % len(CaptchaConfig.SITE_URLS)
            
            if site_key_index >= len(CaptchaConfig.SITE_KEYS):
                return None
                
            site_key = CaptchaConfig.SITE_KEYS[site_key_index]
            site_url = CaptchaConfig.SITE_URLS[site_url_index]
            
            logger.info(f"Getting captcha token with site_key: {site_key}")
            logger.info(f"Site URL: {site_url}")
            
            # 构建payload，添加cookies
            payload = {
                "clientKey": self.capsolver_apikey,
                "task": {
                    "type": "AntiTurnstileTaskProxyLess",
                    "websiteURL": site_url,
                    "websiteKey": site_key,
                    "metadata": {
                        "action": "invisible",
                    },
                    # 添加cookies支持
                    "cookies": [
                        {"name": name, "value": value}
                        for name, value in (cookies or {}).items()
                    ] if cookies else []
                }
            }
            
            logger.info("Sending captcha request with cookies...")
            
            # Create task
            response = await self.request_client.request(
                "POST",
                URLs.CAPSOLVER_CREATE,
                json=payload
            )
            
            task_id = response.get("taskId")
            if not task_id:
                logger.error("No taskId in response")
                return None
                
            logger.info(f"Created captcha task with ID: {task_id}")
            
            # Poll for result
            max_attempts = 30
            for attempt in range(max_attempts):
                await asyncio.sleep(2)  # Wait between checks
                
                status_response = await self.request_client.request(
                    "POST",
                    URLs.CAPSOLVER_RESULT,
                    json={"clientKey": self.capsolver_apikey, "taskId": task_id}
                )
                
                status = status_response.get("status")
                logger.info(f"Captcha status check {attempt + 1}: {status}")
                
                if status == "ready":
                    solution = status_response.get("solution", {})
                    token = solution.get("token")
                    logger.info(f"Solution: {status_response}")
                    if token:
                        logger.info(f"Got captcha token (first 20 chars): {token[:20]}...")
                        return token
                    else:
                        logger.error("No token in solution")
                        return None
                elif status == "failed":
                    error = status_response.get("error")
                    logger.error(f"Captcha task failed: {error}")
                    break
                    
            logger.error("Max attempts reached waiting for captcha")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get CAPTCHA token: {e}")
            return None
