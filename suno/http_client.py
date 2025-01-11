from aiohttp import ClientSession, ClientError, ClientResponse
import asyncio
from typing import Optional, Dict, Any, Callable
from util.logger import logger
from constants import SITE_KEYS, SITE_URLS, URLS
import aiohttp
from urllib.parse import urlencode

class HttpClient:
    def __init__(self, base_headers: Dict[str, str], cookies: Dict[str, str], proxy: str = None):
        self.base_headers = base_headers
        self.cookies = cookies
        self.proxy = proxy
        self.session: Optional[ClientSession] = None
        self.captcha_handler: Optional[Callable] = None
        self._closed = False
        
    def set_captcha_handler(self, handler: Callable):
        """设置处理验证码的回调函数"""
        self.captcha_handler = handler
        
    async def ensure_session(self):
        if self._closed:
            raise RuntimeError("HttpClient is closed")
        if self.session is None or self.session.closed:
            connector = None
            try:
                connector = aiohttp.TCPConnector(ssl=False)
                self.session = ClientSession(connector=connector)
                self.session.cookie_jar.update_cookies(self.cookies)
            except Exception as e:
                if connector:
                    await connector.close()
                raise RuntimeError(f"Failed to create session: {e}")
    
    async def close(self):
        """Properly close the client and all its resources"""
        self._closed = True
        if self.session:
            if not self.session.closed:
                try:
                    await self.session.close()
                except Exception as e:
                    logger.error(f"Error closing session: {e}")
            self.session = None
            
    async def handle_401_response(self, response: ClientResponse, url: str, method: str, **kwargs) -> Optional[Dict]:
        """处理401响应，尝试获取captcha token并重试请求"""
        if not self.captcha_handler:
            logger.error("No captcha handler set for handling 401 response")
            return None
            
        try:
            logger.info("Attempting to get captcha token...")
            captcha_token = await self.captcha_handler(0)
            if not captcha_token:
                logger.error("Failed to get captcha token")
                return None
                
            logger.info(f"Got captcha token: {captcha_token[:20]}...")
            
            # 保持原始请求的所有参数
            params = kwargs.get('params', {}).copy() if kwargs.get('params') else {}
            if not params and '?' in url:
                # 如果URL中包含参数，解析它们
                query_string = url.split('?')[1]
                for param in query_string.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        params[key] = value
            
            # 将验证码token添加到form data中
            form_data = {
                'captcha_token': captcha_token,
                'captcha_widget_type': 'invisible'
            }
            
            # 使用完整的headers，确保与curl请求一致
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
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0"
            }
            kwargs['headers'] = headers
            
            # 设置form data
            encoded_data = urlencode(form_data)
            kwargs['data'] = encoded_data
            
            # 确保使用原始参数
            if params:
                kwargs['params'] = params
            
            logger.info("=== Request Details ===")
            logger.info(f"Method: {method}")
            logger.info(f"URL: {url}")
            logger.info("Headers:")
            for key, value in headers.items():
                logger.info(f"  {key}: {value}")
            logger.info("Cookies:")
            if self.session and self.session.cookie_jar:
                for cookie in self.session.cookie_jar:
                    logger.info(f"  {cookie.key}: {cookie.value}")
            logger.info(f"Query Params: {params}")
            logger.info(f"Form Data: {encoded_data}")
            logger.info("=== End Request Details ===")
            
            # 重试请求
            async with self.session.request(method, url, **kwargs) as retry_response:
                # 首先读取响应内容
                response_text = await retry_response.text()
                
                logger.info("=== Response Details ===")
                logger.info(f"Status: {retry_response.status}")
                logger.info("Response Headers:")
                for key, value in retry_response.headers.items():
                    logger.info(f"  {key}: {value}")
                logger.info(f"Response Body: {response_text}")
                logger.info("=== End Response Details ===")
                
                if retry_response.status >= 400:
                    logger.warning(f"Retry with captcha token failed: {retry_response.status}")
                    logger.warning(f"Response text: {response_text}")
                    return None
                    
                try:
                    response_data = await retry_response.json()
                    logger.info(f"Successful response after captcha: {list(response_data.keys())}")
                    return response_data
                except Exception as e:
                    logger.error(f"Failed to parse JSON response after captcha: {e}")
                    logger.error(f"Response text: {response_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error during captcha attempt: {e}")
            return None
            
    async def request(self, method: str, url: str, retry_count: int = 1, **kwargs) -> Dict[str, Any]:
        if self._closed:
            raise RuntimeError("HttpClient is closed")
            
        await self.ensure_session()
        
        headers = {**self.base_headers, **kwargs.get('headers', {})}
        kwargs['headers'] = headers
        if self.proxy:
            kwargs['proxy'] = self.proxy
            
        last_error = None
        for attempt in range(retry_count):
            try:
                async with self.session.request(method, url, **kwargs) as response:
                    # 首先尝试读取响应内容
                    response_text = await response.text()
                    
                    # 如果是401错误，尝试处理验证码
                    if response.status == 401:
                        logger.info("Received 401, attempting to handle with captcha...")
                        result = await self.handle_401_response(response, url, method, **kwargs)
                        if result:
                            return result
                        # 如果处理401失败，继续重试
                        raise ClientError(f"401 Unauthorized after captcha attempts")
                    
                    # 对于其他错误状态码
                    if response.status >= 400:
                        error_msg = f"{response.status}, message='{response_text}', url={response.url}"
                        raise ClientError(error_msg)
                    
                    # 尝试解析JSON响应
                    try:
                        return await response.json()
                    except Exception as e:
                        logger.error(f"Failed to parse JSON response: {e}")
                        logger.error(f"Response text: {response_text}")
                        raise ClientError(f"Invalid JSON response: {response_text}")
                    
            except (ClientError, asyncio.TimeoutError) as e:
                last_error = e
                if attempt == retry_count - 1:
                    break
                logger.warning(f"Request failed (attempt {attempt + 1}/{retry_count}): {str(e)}")
                await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
            except Exception as e:
                logger.error(f"Unexpected error during request: {e}")
                raise
                
        raise last_error or ClientError("Request failed after all retries") 