import asyncio
from util import utils
import sys
import os
from dotenv import load_dotenv
from contextlib import suppress
import aiohttp

load_dotenv('/root/Suno2openai/test.env')
# 添加父目录到系统路径以导入模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from suno import SongsGen
from util.logger import logger
from aiohttp import ClientSession

# 在这里填写你的cookie
COOKIE = os.getenv('COOKIE')
CAPSOLVER_APIKEY = os.getenv('capsolver_apikey')

async def test_auth():
    """测试认证相关功能"""
    async with SongsGen(COOKIE, CAPSOLVER_APIKEY) as songs_gen:
        try:
            logger.info("Starting authentication test...")
            # 不需要再次调用get_auth_token，因为在__aenter__中已经调用过了
            if songs_gen.auth_token:
                logger.info(f"Authentication successful!")
                logger.info(f"JWT Token (first 20 chars): {songs_gen.auth_token[:20]}...")
                
                # 验证实例变量是否正确设置
                logger.info(f"Session ID: {songs_gen.session_id}")
                logger.info(f"User ID: {songs_gen.user_id}")
                logger.info(f"Session Expires: {songs_gen.session_expire_at}")
                
                return songs_gen.auth_token
            else:
                logger.error("Failed to get authentication token")
                return None
                
        except Exception as e:
            logger.error(f"Auth test failed with error: {str(e)}")
            return None

async def test_limit_left(songs_gen):
    """测试获取剩余次数"""
    try:
        limit = await songs_gen.get_limit_left()
        logger.info(f"Remaining credits: {limit}")
        return limit
    except Exception as e:
        logger.error(f"Get limit test failed: {e}")
        return -1

async def main():
    songs_gen = None
    try:
        async with SongsGen(COOKIE, CAPSOLVER_APIKEY) as songs_gen:
            auth_result = await test_auth()
            if not auth_result:
                logger.error("Authentication test failed")
                return
                
            # 测试获取剩余次数
            limit_result = await test_limit_left(songs_gen)
            if limit_result < 0:
                logger.error("Failed to get remaining credits")
                return
                
            logger.info("All tests completed successfully")
            
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
    finally:
        if songs_gen:
            await songs_gen.close()

if __name__ == "__main__":
    asyncio.run(main())