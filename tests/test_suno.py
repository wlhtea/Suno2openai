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
        # 检查生成权限
        check_result = await songs_gen.check_generation_permission()
        if check_result is None:
            logger.error("Failed to check generation permission")
            return None, None
            
        # 获取通知连接
        notification_data = await songs_gen.get_notification()
        if notification_data is None:
            logger.error("Failed to establish notification connection")
            return None, None

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
        token = "P1_eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.hadwYXNza2V5xQWl4F9ZWvTC4PKjA9_7UaEUvAGavE7TUZFXqRE5Gqy9zBjYxg84Z_rZMMpKEjwcl1wQ2RTZr6-0hi2vB30pHD82wHPsGe3-986iOT-zFOiMDW4PSWu38XuobMQNDjhX_EeEHRh1sgFS8baPQBYMAMmpGLhfutQk7J284CdhlCEuVe6c_VAWfvmQ_MVFRxQNVsIN_32_Du4N54vFFt0SPE-4hiLfiMNedvBe4vlAxPmdGoIgpNttYpxJbhkfNI2pBlwgCdltLir--jwT5o9kD2cu4WEXqjEhVUCWXMPqQahG4-onQ5FkG7VAEcymJ3Xp78OhmdzS_4WO_tw3T5vlnX2oPFFY_XH3lccNwPFoQExjPqrrtoGD6i1FtbVW294BmcgyEIqKMrb4m97gCqsnqROUDpnE_vvm0q3__AGj33szloiWH92Vn4-zL0BUOkJwR65OqUFN4ZlRNSD7mVxUM9h9-afPuPQPK7PF-WkAT0AugMQdbkYkHecSZ9XVKVaLI-EXp3lM6J5avr5YwTa5yt7iIkLCbHNtV7b_kDEDcfojkB3FCBYcd5pah9Jyh_LIIo4rAoLoC074LomvkuvuVdkKuFdi7ZJeqj5hG8tPV7b4WF84ylP95A7vAA4cTnjWtKciJ94SIMKcAwIloath4omzPIkBoSOO81nzwzrCq080fVLi6yxVnnhAq4kqa_84skMT_ryaUv3dGvxtKO48IT3pzq-dzjDf1zBkhqvxG7I8y4bZfHn5aq_BtDAYjn5GejD6BvOc57-pNIKwhVh6aqvVrLOHK54TGGkZX1m0yL67Z4jeR32PkDZMa0WQ7XBMznLn4dv1ad6E3EPYwvX302MXFSQTIcHckhBzjqYlJNluk7CmJ0rqbZ442OcW1V4clcE_tWqKd2oitE5yIBM-UHAejMdlE8_6MyLHOYKqXEF5aEgFsChr8ff68yuTaJj1Bd5xQugm7NNB0-kKuoFYr1zDvwwOdPX3R2i1lS5koogf8g2zY8pROMRb47Gubhqx5LSX7rWgr-6xr4J44AOEWkPkgMacUHNmblzbZz_LE2Z390JoyuVtVPnHRZrvQsGcZhTpAVVDHnUxd4sP7zKoMnkCBK5ww5u8LP3pzKMXe0MWfS0mQPZcails-KJNqKibax6wZA7Vu7GA5r8d6GktS2lwjETOunAvEaXRHpZ8yDWsAm3po_kjjYmPDHZezS9eMVmB45Wiasa2__Gp-awFNXaY1mkpQhlKZOQ4PU3c_uVG2QVYQKe2ovsJGV15aN3SsWExb-0rt6d4OjIF7gR_uqh4vYcFGSq0nOsIXeazV7MwVjq7xusVMyjJCVJB9YglU9rk2XFOdd0I1RWBACUB30QhgiW8-T3EusLY587d6y8BtqUgTjgObMi64GgUg9QT4qUPFZnDiglnsIEORUXzHevbH3ss0UKOtMJ7gTZHFtie9ACbIXIfVQ1TD8y8kIAFFf5_nhJD74gUK8EwtdxgpL6N8g-kf_0P_Y8X40s0j_0W5v_bOnhaXFQBImUymnTtqG2ggEjnfoOHwzgQEWb1AhBLyCex-vXLHEForPv4oW8oLAYUbfuOXgOsOEUn_bm0L-9auIYO8Vit2sx-BSvSNt7WqzQrABJG4obR35ToXxEeLfmIZ6kWAb2TE9PaFNAMsaRabUY5I0DNDyDeOmVxwqsXxbuxZFIVpqttT9-28xEjFo4pGP0aYmbdkj2MJHVMJ4xo7vxfPRD01M9hIAE6sWlJhnRPSSguwEZRXpOuN0Ud7Kho1HzFhzqRFi7V3vnX2JdiwTyJUMP-ACZntgSzKmwroxWoRE4WK2usDfZTtj1Db7vjTquARPTJvyVjWs5Xm7J9yfUksfWxvbO6uszAmgDl4kbm5QvSVlcS6p9y-cDBhzNZ3hEMgTCDMKg-FdOlwRs8XaPZmIKjZXhwzmeMya-oc2hhcmRfaWTODTtkKaJrcqg0N2ZjZTdlMqJwZAA.oKjo4bHJHmyoDXgUmvqRkD66aXv8moqPp3fq5ihS3SU"
        result, error_message = await songs_gen.generate_music(token=token, prompt=prompt, title=title, mv="chirp-v3-5")
        
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
