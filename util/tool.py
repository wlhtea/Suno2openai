import json
import random
import string
import time

import tiktoken

from util.config import RETRIES, MAX_TIME
from util.logger import logger


def generate_random_string_async(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_timestamp_async():
    return int(time.time())


def calculate_token_costs(input_prompt: str, output_prompt: str, model_name: str) -> (int, int):
    encoding = tiktoken.encoding_for_model(model_name)

    # Encode the prompts
    input_tokens = encoding.encode(input_prompt)
    output_tokens = encoding.encode(output_prompt)

    # Count the tokens
    input_token_count = len(input_tokens)
    output_token_count = len(output_tokens)

    return input_token_count, output_token_count


def check_status_complete(response, start_time):
    try:
        if not isinstance(response, list):
            raise ValueError("Invalid response format: expected a list")

        if time.time() - start_time > 60 * MAX_TIME:
            return True

        for item in response:
            if item.get("status", None) == "complete":
                return True

        return False
    except Exception as e:
        raise ValueError(f"Invalid JSON response: {e}")


async def get_clips_ids(response: json):
    try:
        if 'clips' in response and isinstance(response['clips'], list):
            clip_ids = [clip['id'] for clip in response['clips']]
            return clip_ids
        else:
            raise ValueError("Invalid response format: 'clips' key not found or is not a list.")
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON response")


# async def get_token():
#     cookieSelected = await db_manager.get_token()
#     return cookieSelected


async def deleteSongID(db_manager, cookie):
    for attempt in range(RETRIES):
        try:
            await db_manager.delete_song_ids(cookie)
            return
        except Exception as e:
            if attempt > RETRIES - 1:
                logger.info(f"删除音乐songID失败: {e}")
