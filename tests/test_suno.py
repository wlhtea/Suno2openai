import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime
import uuid
# 加载环境变量
load_dotenv('test.env')

from suno import SongsGen, CLERK_API_VERSION, CLERK_JS_VERSION, URLs
from util.logger import logger

# 在这里填写你的cookie
COOKIE = os.getenv('COOKIE')
CAPSOLVER_APIKEY = os.getenv('capsolver_apikey')

async def test_auth(songs_gen: SongsGen):
    """测试认证相关功能"""
    try:
        logger.info("Starting authentication test...")
        if songs_gen.auth_token:
            logger.info(f"Authentication successful!")
            logger.info(f"JWT Token (first 20 chars): {songs_gen.auth_token[:20]}...")
            
            # 验证实例变量是否正确设置
            logger.info(f"Clerk Session ID: {songs_gen.clerk_session_id}")
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

async def test_verify(songs_gen):
    """测试验证"""
    try:
        result = await songs_gen.verify()
        logger.info(f"Verify result: {result}")
        return result
    except Exception as e:
        logger.error(f"Verify test failed: {e}")
        return None

async def test_get_playlist(songs_gen):
    """测试获取播放列表notification session-id"""
    try:
        playlist_id = "0b9f43a6-7754-4069-9e3b-93b061be361d"
        notification_session_id = await songs_gen.get_playlist(playlist_id)
        if notification_session_id:
            logger.info(f"Got notification session-id: {notification_session_id}")
            return notification_session_id
        else:
            logger.error("Failed to get notification session-id")
            return None
    except Exception as e:
        logger.error(f"Get playlist test failed: {e}")
        return None

async def generate_music(songs_gen):
    """测试生成音乐"""
    try:
        prompt = "A beautiful sunset over a calm ocean"
        title = "Sunset at the Beach"
        result = await songs_gen.generate_music(prompt, title)
        if not result:
            logger.error("Failed to generate music")
            return None
            
        logger.info(f"Generate music result: {result}")
        
        # 提取歌曲ID
        clip_ids = songs_gen.extract_clip_ids(result)
        if clip_ids:
            logger.info(f"Successfully extracted {len(clip_ids)} clip IDs")
            for i, clip_id in enumerate(clip_ids, 1):
                logger.info(f"Clip {i}: {clip_id}")
        else:
            logger.error("Failed to extract clip IDs")
            return None
            
        return result, clip_ids
        
    except Exception as e:
        logger.error(f"Generate music test failed: {e}")
        return None

async def test_get_feed(songs_gen,ids=None):
    """测试获取歌曲任务状态"""
    try:
        feed_data = await songs_gen.get_feed(ids)
        if feed_data:
            logger.info(f"Got feed data for {len(ids)} songs")
            return feed_data
        else:
            logger.error("Failed to get feed data")
            return None
    except Exception as e:
        logger.error(f"Get feed test failed: {e}")
        return None

async def main():
    songs_gen = None
    try:
        device_id = str(uuid.uuid4())
        async with SongsGen(COOKIE, CAPSOLVER_APIKEY, device_id=device_id) as songs_gen:
            # 使用同一个songs_gen实例进行测试
            auth_result = await test_auth(songs_gen)
            if not auth_result:
                logger.error("Authentication test failed")
                return
                
            # 测试获取剩余次数
            limit_result = await test_limit_left(songs_gen)
            if limit_result < 0:
                logger.error("Failed to get remaining credits")
                return
            pass
            # 测试获取播放列表
            playlist_result = await test_get_playlist(songs_gen)
            if not playlist_result:
                logger.error("Failed to get playlist")
                return

            # 测试生成音乐
            music_result,ids = await generate_music(songs_gen)
            if not music_result:
                logger.error("Failed to generate music")
                return
            
            # 测试获取歌曲任务状态
            if ids is None:
                ids = ['9425da8a-ad79-455a-af54-70e5df52c7e7', 'e3ec7b95-e390-40dc-bb33-fa789aadca37']
            feed_result = await test_get_feed(songs_gen,ids)
            logger.info(f"Feed result: {feed_result}")
            if not feed_result:
                logger.error("Failed to get feed data")
                return
            logger.info("All tests completed successfully")
            
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
    finally:
        if songs_gen:
            await songs_gen.close()

if __name__ == "__main__":
    asyncio.run(main())
