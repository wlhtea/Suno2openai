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
import aiohttp
import uuid
import json

class SongsGen:
    def __init__(self, cookie: str, capsolver_apikey: str, device_id: str = None) -> None:
        if not cookie or not capsolver_apikey:
            raise ValueError("Cookie and capsolver_apikey are required")
            
        self.ua = UserAgent(browsers=["edge"])
        self.base_headers = {
            **DEFAULT_HEADERS,
            "user-agent": self.ua.edge,
        }
        
        self.capsolver_apikey = capsolver_apikey
        
        # 设置私有的设备ID
        self._device_id = device_id or "5ee4b1c9-c17e-4e25-b913-8ce57ba43a54"
        
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
        
        # Clerk认证相关的实例变量
        self.auth_token: Optional[str] = None
        self.clerk_session_id: Optional[str] = None  # 用于URL的session id
        self.user_id: Optional[str] = None
        self.session_expire_at: Optional[int] = None
        
        # 通知相关的实例变量
        self.notification_session_id: Optional[str] = None  # 用于请求头的session id
        
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
            self.clerk_session_id = session_id
            self.user_id = user_id
            self.session_expire_at = expire_at
            
            return jwt  # 返回JWT token而不是整个response
            
        except Exception as e:
            logger.error(f"Failed to get auth token: {e}")
            return None

    async def verify(self) -> Optional[Dict]:
        """Verify session by touching the session endpoint"""
        if self._closed:
            raise RuntimeError("SongsGen instance is closed")
            
        if not self.clerk_session_id:
            logger.error("No session ID available")
            return None
            
        try:
            params = {
                "__clerk_api_version": CLERK_API_VERSION,
                "_clerk_js_version": CLERK_JS_VERSION,
            }
            
            url = f"{URLs.CLERK_BASE}/v1/client/sessions/{self.clerk_session_id}/touch"
            
            response = await self.request_client.request(
                "POST",
                url,
                params=params,
                headers={
                    "accept": "*/*",
                    "accept-language": "en-US,en;q=0.9",
                    "content-type": "application/x-www-form-urlencoded",
                    "origin": "https://suno.com",
                    "referer": "https://suno.com/",
                }
            )
            
            if not isinstance(response, dict):
                logger.error(f"Unexpected response type: {type(response)}")
                return None
                
            return response
            
        except Exception as e:
            logger.error(f"Failed to verify session: {e}")
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

    async def generate_music(
        self,
        prompt: str,
        title: str,
        tags: str = "",
        negative_tags: str = "",
        mv: str = "chirp-v4",
        generation_type: str = "TEXT",
        continue_clip_id: str = None,
        continue_at: int = None,
        infill_start_s: int = None,
        infill_end_s: int = None,
        task: str = None,
        artist_clip_id: str = None,
        artist_start_s: int = None,
        artist_end_s: int = None,
        metadata: dict = None
    ) -> Optional[Dict]:
        """
        Generate music using the Suno API
        
        Args:
            prompt: The lyrics or text prompt for the music
            title: The title of the song
            tags: Comma-separated list of music style tags
            negative_tags: Comma-separated list of tags to avoid
            mv: Model version to use
            generation_type: Type of generation (TEXT, CONTINUE, etc)
            continue_clip_id: ID of clip to continue from
            continue_at: Timestamp to continue from
            infill_start_s: Start time for infill
            infill_end_s: End time for infill
            task: Task type
            artist_clip_id: Artist clip ID
            artist_start_s: Artist clip start time
            artist_end_s: Artist clip end time
            metadata: Additional metadata
            
        Returns:
            Response data dictionary or None if failed
        """
        if self._closed:
            raise RuntimeError("SongsGen instance is closed")
            
        if not self.auth_token:
            logger.error("No auth token available")
            return None
            
        try:
            # Prepare request data
            data = {
                "token": None,
                "prompt": prompt,
                "generation_type": generation_type,
                "tags": tags,
                "negative_tags": negative_tags,
                "mv": mv,
                "title": title,
                "continue_clip_id": continue_clip_id,
                "continue_at": continue_at,
                "continued_aligned_prompt": None,
                "infill_start_s": infill_start_s,
                "infill_end_s": infill_end_s,
                "task": task,
                "artist_clip_id": artist_clip_id,
                "artist_start_s": artist_start_s,
                "artist_end_s": artist_end_s,
                "metadata": metadata or {}
            }
            
            # Get headers and add content-type
            headers = self._get_common_headers()
            headers["content-type"] = "text/plain;charset=UTF-8"
            
            logger.info("Making request with headers:")
            for key, value in headers.items():
                logger.info(f"{key}: {value}")
                
            logger.info("Request data:")
            logger.info(data)
            
            # Make request
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(
                        f"{URLs.SUNO_BASE}/api/generate/v2/",
                        headers=headers,
                        json=data
                    ) as response:
                        # Log response headers
                        logger.info("Response headers:")
                        for key, value in response.headers.items():
                            logger.info(f"{key}: {value}")
                            
                        # Get response content
                        content_type = response.headers.get('content-type', '')
                        logger.info(f"Response content type: {content_type}")
                        
                        # Read raw response text first
                        text = await response.text()
                        logger.info("Raw response text:")
                        logger.info(text)
                        
                        # Check status code
                        if response.status != 200:
                            logger.error("-" * 50)
                            logger.error(f"Request failed with status {response.status} ({response.reason})")
                            logger.error("-" * 50)
                            logger.error("Response headers:")
                            for key, value in response.headers.items():
                                logger.error(f"{key}: {value}")
                            logger.error("-" * 50)
                            logger.error("Response text:")
                            logger.error(text)
                            logger.error("-" * 50)
                            logger.error("Request URL:")
                            logger.error(f"{URLs.SUNO_BASE}/api/generate/v2/")
                            logger.error("-" * 50)
                            logger.error("Request headers:")
                            for key, value in headers.items():
                                logger.error(f"{key}: {value}")
                            logger.error("-" * 50)
                            logger.error("Request data:")
                            logger.error(json.dumps(data, indent=2))
                            logger.error("-" * 50)
                            return None
                        
                        # Try to parse as JSON if it looks like JSON
                        try:
                            if 'application/json' in content_type or text.strip().startswith('{'):
                                response_data = await response.json()
                                logger.info("Parsed JSON response:")
                                logger.info(response_data)
                                
                                if not isinstance(response_data, dict):
                                    logger.error(f"Unexpected response type: {type(response_data)}")
                                    return None
                                    
                                return response_data
                            else:
                                logger.error(f"Unexpected content type: {content_type}")
                                logger.error(f"Response text: {text}")
                                return None
                                
                        except Exception as e:
                            logger.error(f"Failed to parse response: {e}")
                            logger.error(f"Response text: {text}")
                            return None
                except aiohttp.ClientError as e:
                    logger.error(f"HTTP request failed: {e}")
                    logger.error(f"Request URL: {URLs.SUNO_BASE}/api/generate/v2/")
                    logger.error("Request headers:")
                    for key, value in headers.items():
                        logger.error(f"{key}: {value}")
                    logger.error("Request data:")
                    logger.error(json.dumps(data, indent=2))
                    return None
            
        except Exception as e:
            logger.error(f"Failed to generate music: {e}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

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

    async def get_playlist(self, playlist_id: str, page: int = 0) -> Optional[str]:
        """
        Get playlist information and store notification session-id from response headers
        
        Args:
            playlist_id: The ID of the playlist
            page: Page number for pagination (default: 0)
            
        Returns:
            notification_session_id string or None if failed
        """
        if self._closed:
            raise RuntimeError("SongsGen instance is closed")
            
        if not self.auth_token:
            logger.error("No auth token available")
            return None
            
        try:
            # Make request
            url = URLs.PLAYLIST.format(playlist_id=playlist_id)
            params = {"page": page}
            
            result = await self.request_client.request_with_headers(
                "GET",
                url,
                headers=self._get_common_headers(),
                params=params
            )
            
            if not result:
                return None
                
            _, response_headers = result
            
            # Get and store session-id from headers
            session_id = response_headers.get('session-id')
            if session_id:
                self.notification_session_id = session_id  # 保存到实例变量
                return session_id
            else:
                logger.error("No session-id in response headers")
                return None
            
        except Exception as e:
            logger.error(f"Failed to get playlist: {e}")
            return None

    async def get_feed(self, ids: list[str], page: int = 5000) -> Optional[Dict]:
        """
        Get feed information for one or more songs
        
        Args:
            ids: List of song IDs to get status for
            page: Page size (default: 5000)
            
        Returns:
            Feed data dictionary or None if failed
        """
        if self._closed:
            raise RuntimeError("SongsGen instance is closed")
            
        if not self.auth_token:
            logger.error("No auth token available")
            return None
            
        if not self.notification_session_id:
            logger.error("No notification session ID available")
            return None
            
        try:
            # Prepare query parameters
            params = {
                "ids": ",".join(ids),
                "page": page
            }
            
            # Make request
            response = await self.request_client.request(
                "GET",
                URLs.FEED,
                headers=self._get_common_headers(),
                params=params
            )
            
            if not isinstance(response, dict):
                logger.error(f"Unexpected response type: {type(response)}")
                return None
                
            return response
            
        except Exception as e:
            logger.error(f"Failed to get feed: {e}")
            return None

    def extract_clip_ids(self, generation_response: Dict) -> list[str]:
        """
        从生成音乐的响应中提取歌曲ID
        
        Args:
            generation_response: 生成音乐的响应数据
            
        Returns:
            包含歌曲ID的列表，如果提取失败则返回空列表
        """
        try:
            clips = generation_response.get('clips', [])
            clip_ids = [clip['id'] for clip in clips if 'id' in clip]
            
            if not clip_ids:
                logger.error("No clip IDs found in generation response")
                return []
                
            logger.info(f"Extracted {len(clip_ids)} clip IDs: {clip_ids}")
            return clip_ids
            
        except Exception as e:
            logger.error(f"Failed to extract clip IDs: {e}")
            return []

    def _get_common_headers(self) -> Dict[str, str]:
        """获取通用请求头"""
        headers = {
            "accept": "*/*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "affiliate-id": "undefined",
            "authorization": f"Bearer {self.auth_token}" if self.auth_token else None,
            "device-id": self._device_id,
            "origin": "https://suno.com",
            "priority": "u=1, i",
            "referer": "https://suno.com/",
            "sec-ch-ua": '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
        }
        
        # 如果有notification_session_id，添加到请求头
        if self.notification_session_id:
            headers["session-id"] = self.notification_session_id
            
        return {k: v for k, v in headers.items() if v is not None}
