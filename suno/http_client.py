"""
HTTP客户端模块
处理所有HTTP请求、验证码和会话管理
"""

import aiohttp
from typing import Optional, Dict, Any, Callable
from util.logger import logger
from .constants import URLs, CLERK_API_VERSION, CLERK_JS_VERSION

class HttpClient:
    """
    异步HTTP客户端
    处理请求、验证码和会话管理
    """
    
    def __init__(
        self, 
        base_headers: Dict[str, str],
        cookies: Dict[str, str],
        proxy: Optional[str] = None
    ):
        """
        初始化HTTP客户端
        
        Args:
            base_headers: 基础请求头
            cookies: Cookie字典
            proxy: 代理服务器URL(可选)
        """
        self.base_headers = base_headers
        self.cookies = cookies
        self.proxy = proxy
        self.captcha_handler: Optional[Callable] = None
        
    def set_captcha_handler(self, handler: Callable) -> None:
        """
        设置验证码处理器
        
        Args:
            handler: 处理验证码的回调函数
        """
        self.captcha_handler = handler
        
    async def close(self) -> None:
        """关闭客户端会话"""
        pass
            
    async def handle_401_response(self, url: str) -> Optional[Dict[str, Any]]:
        """
        处理401响应，获取验证码token并重试请求
        
        Args:
            url: 请求URL
            
        Returns:
            响应数据字典或None(失败时)
        """
        if not self.captcha_handler:
            logger.error("No captcha handler set")
            return None
            
        try:
            captcha_token = await self.captcha_handler(0, self.cookies)
            if not captcha_token:
                logger.error("Failed to get captcha token")
                return None
            
            # 准备验证码请求
            headers = {
                **self.base_headers,
                "accept": "*/*",
                "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
                "content-type": "application/x-www-form-urlencoded",
            }
            
            form_data = f'captcha_token={captcha_token}&captcha_widget_type=invisible'
            
            async with aiohttp.ClientSession(cookies=self.cookies) as session:
                async with session.post(
                    url,
                    headers=headers,
                    data=form_data,
                    params={
                        "__clerk_api_version": CLERK_API_VERSION,
                        "_clerk_js_version": CLERK_JS_VERSION
                    }
                ) as response:
                    if response.status >= 400:
                        logger.error(f"Captcha request failed with status {response.status}")
                        return None
                        
                    try:
                        return await response.json()
                    except Exception as e:
                        logger.error(f"Failed to parse captcha response: {e}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error during captcha request: {e}")
            return None
            
    async def request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法
            url: 请求URL
            **kwargs: 传递给aiohttp的其他参数
            
        Returns:
            响应数据字典或None(失败时)
        """
        try:
            headers = {**self.base_headers}
            if 'headers' in kwargs:
                headers.update(kwargs.pop('headers'))
            
            async with aiohttp.ClientSession(cookies=self.cookies) as session:
                async with session.request(
                    method,
                    url,
                    headers=headers,
                    **kwargs
                ) as response:
                    if response.status == 401:
                        logger.info("Got 401, trying with captcha...")
                        result = await self.handle_401_response(url)
                        if result:
                            return result
                        logger.error("Failed to handle 401 response")
                        return None
                        
                    if response.status >= 400:
                        logger.error(f"Request failed with status {response.status}")
                        return None
                        
                    return await response.json()
                    
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return None
            
    async def request_with_headers(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> Optional[tuple[Dict[str, Any], Dict[str, str]]]:
        """
        发送HTTP请求并返回响应数据和头信息
        
        Args:
            method: HTTP方法
            url: 请求URL
            **kwargs: 传递给aiohttp的其他参数
            
        Returns:
            (响应数据字典, 响应头字典)元组或None(失败时)
        """
        try:
            headers = {**self.base_headers}
            if 'headers' in kwargs:
                headers.update(kwargs.pop('headers'))
            
            async with aiohttp.ClientSession(cookies=self.cookies) as session:
                async with session.request(
                    method,
                    url,
                    headers=headers,
                    **kwargs
                ) as response:
                    if response.status == 401:
                        logger.info("Got 401, trying with captcha...")
                        result = await self.handle_401_response(url)
                        if result:
                            return result, dict(response.headers)
                        logger.error("Failed to handle 401 response")
                        return None
                        
                    if response.status >= 400:
                        logger.error(f"Request failed with status {response.status}")
                        return None
                        
                    return await response.json(), dict(response.headers)
                    
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return None 