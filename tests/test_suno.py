import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime
import uuid
import json
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
        prompt = """[Intro]
                    Hey hey

                    [Chorus: Elton John type]
                    Long time no see
                    I've been finally 20
                    You came to see how the view works
                    And I love you like a new word

                    [Post-Chorus]
                    Wow

                    [Chorus: MJ type]
                    Where have you been?
                    I got my air dirty now
                    Past that dying bird
                    You look like you can't believe it

                    [Verse: Paul McCartney type]
                    And I hate it when you call me
                    I hate it when you miss me
                    Come home to your new world
                    I love you like a songbird

                    [Verse 3]
                    Maybe if you get yourself a little closer
                    You'd see the best part of me
                    Darling there's more than words to
                    Everything that's shitty in the air again"""
        title = "Long Time No See"
        result, error_message = await songs_gen.generate_music(prompt=prompt, title=title, mv="chirp-v3-5")
        
        if error_message:
            logger.error(f"Failed to generate music: {error_message}")
            if "Insufficient credits" in error_message:
                logger.error("No credits available to generate music")
                return None, None
            return None, None
            
        if not result:
            logger.error("Failed to generate music with no error message")
            return None, None
            
        logger.info(f"Generate music result: {result}")
        
        # 提取歌曲ID
        clip_ids = songs_gen.extract_clip_ids(result)
        if clip_ids:
            logger.info(f"Successfully extracted {len(clip_ids)} clip IDs")
            for i, clip_id in enumerate(clip_ids, 1):
                logger.info(f"Clip {i}: {clip_id}")
        else:
            logger.error("Failed to extract clip IDs")
            return None, None
            
        return result, clip_ids
        
    except Exception as e:
        logger.error(f"Generate music test failed: {e}")
        return None, None

async def test_get_feed(songs_gen, ids=None):
    """测试获取歌曲任务状态"""
    try:
        if ids is None or not ids:
            ids = ['9425da8a-ad79-455a-af54-70e5df52c7e7', 'e3ec7b95-e390-40dc-bb33-fa789aadca37']
            
        logger.info(f"Checking status for clips: {ids}")
            
        # 获取初始状态
        feed_data = await songs_gen.get_feed(ids)
        if not feed_data:
            logger.error("Failed to get initial feed data")
            return None
            
        logger.info("\nInitial Feed Response:")
        logger.info("-" * 50)
        # 记录完整的响应数据
        logger.info(json.dumps(feed_data, indent=2))
        logger.info("-" * 50)
        
        # 持续检查任务状态
        final_status = await songs_gen.check_task_status(
            ids,
            interval=2,  # 每2秒检查一次
            timeout=300  # 最多等待5分钟
        )
        
        if final_status:
            logger.info("\nFinal Feed Response:")
            logger.info("-" * 50)
            # 记录完整的最终响应数据
            logger.info(json.dumps(final_status, indent=2))
            logger.info("-" * 50)
            return final_status
        else:
            logger.error("Failed to get final task status")
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

            # 测试获取播放列表
            playlist_result = await test_get_playlist(songs_gen)
            if not playlist_result:
                logger.error("Failed to get playlist")
                return

            # 测试生成音乐
            music_result, clip_ids = await generate_music(songs_gen)
            if not music_result:
                logger.error("Failed to generate music")
                return
                
            # 测试获取歌曲任务状态
            if clip_ids:
                feed_result = await test_get_feed(songs_gen, clip_ids)
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
