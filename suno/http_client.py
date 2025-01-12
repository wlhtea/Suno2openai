import aiohttp
from typing import Optional, Dict, Any, Callable
from util.logger import logger

class HttpClient:
    def __init__(self, base_headers: Dict[str, str], cookies: Dict[str, str], proxy: str = None):
        self.base_headers = base_headers
        self.cookies = cookies
        self.proxy = proxy
        self.captcha_handler: Optional[Callable] = None
        
    def set_captcha_handler(self, handler: Callable):
        """设置处理验证码的回调函数"""
        self.captcha_handler = handler
        
    async def close(self):
        """关闭客户端"""
        # 由于我们使用的是每次请求创建新session的方式，这里不需要实际的清理操作
        pass
            
    async def handle_401_response(self, url: str) -> Optional[Dict]:
        """处理401响应，尝试获取captcha token并重试请求"""
        if not self.captcha_handler:
            logger.error("No captcha handler set")
            return None
            
        try:
            # 获取验证码token
            logger.info("Getting captcha token...")
            captcha_token = await self.captcha_handler(0, self.cookies)
            if not captcha_token:
                logger.error("Failed to get captcha token")
                return None
                
            logger.info(f"Got captcha token: {captcha_token[:20]}...")
            
            # 准备请求数据
            headers = {
                "accept": "*/*",
                "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
                "cache-control": "no-cache",
                "content-type": "application/x-www-form-urlencoded",
                "origin": "https://suno.com",
                "pragma": "no-cache",
                "referer": "https://suno.com/",
                "sec-ch-ua": '"Chromium";v="130", "Microsoft Edge";v="130", "Not?A_Brand";v="99"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0"
            }
            
            # 表单数据需要作为原始字符串发送
            form_data = f'captcha_token={captcha_token}&captcha_widget_type=invisible'
            
            # 记录请求详情
            logger.info("=== Request Details ===")
            logger.info(f"URL: {url}")
            logger.info(f"Headers: {headers}")
            logger.info(f"Cookies: {self.cookies}")
            logger.info(f"Form Data (raw): {form_data}")
            logger.info("=== End Request Details ===")
            
            # 发送请求，使用data而不是json
            async with aiohttp.ClientSession(cookies=self.cookies) as session:
                async with session.post(
                    url,
                    headers=headers,
                    data=form_data,  # 直接发送原始字符串
                    params={
                        "__clerk_api_version": "2024-10-01",
                        "_clerk_js_version": "5.43.6"
                    }
                ) as response:
                    response_text = await response.text()
                    
                    # 记录响应详情
                    logger.info("=== Response Details ===")
                    logger.info(f"Status: {response.status}")
                    logger.info(f"Headers: {dict(response.headers)}")
                    logger.info(f"Body: {response_text}")
                    logger.info("=== End Response Details ===")
                    
                    if response.status >= 400:
                        logger.error(f"Request failed with status {response.status}")
                        return None
                        
                    try:
                        return await response.json()
                    except Exception as e:
                        logger.error(f"Failed to parse response: {e}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error during request: {e}")
            return None
            
    async def request(self, method: str, url: str, **kwargs) -> Optional[Dict]:
        """发送HTTP请求"""
        try:
            # 合并headers，但从kwargs中移除headers以避免冲突
            headers = {**self.base_headers}
            if 'headers' in kwargs:
                headers.update(kwargs.pop('headers'))
            
            async with aiohttp.ClientSession(cookies=self.cookies) as session:
                async with session.request(method, url, headers=headers, **kwargs) as response:
                    if response.status == 401:
                        logger.info("Got 401, trying with captcha...")
                        return await self.handle_401_response(url)
                        
                    if response.status >= 400:
                        logger.error(f"Request failed with status {response.status}")
                        return None
                        
                    return await response.json()
                    
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return None 