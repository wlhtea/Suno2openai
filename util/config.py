import os
import time

from dotenv import load_dotenv

from util.logger import logger

load_dotenv(encoding="ascii")

# 版本号
VERSION = "0.2.0"

BASE_URL = os.getenv('BASE_URL', 'https://studio-api.suno.ai')
SESSION_ID = os.getenv('SESSION_ID')
USER_NAME = os.getenv('USER_NAME', '')
SQL_NAME = os.getenv('SQL_NAME', '')
SQL_PASSWORD = os.getenv('SQL_PASSWORD', '')
SQL_IP = os.getenv('SQL_IP', '')
SQL_DK = os.getenv('SQL_DK', 3306)
COOKIES_PREFIX = os.getenv('COOKIES_PREFIX', "")
AUTH_KEY = os.getenv('AUTH_KEY', str(time.time()))
RETRIES = int(os.getenv('RETRIES', 3))
BATCH_SIZE = int(os.getenv('BATCH_SIZE', 10))

# 记录配置信息
logger.info("==========================================")
logger.info(f"VERSION: {VERSION}")
logger.info(f"BASE_URL: {BASE_URL}")
logger.info(f"SESSION_ID: {SESSION_ID}")
logger.info(f"USER_NAME: {USER_NAME}")
logger.info(f"SQL_NAME: {SQL_NAME}")
logger.info(f"SQL_PASSWORD: {SQL_PASSWORD}")
logger.info(f"SQL_IP: {SQL_IP}")
logger.info(f"SQL_DK: {SQL_DK}")
logger.info(f"COOKIES_PREFIX: {COOKIES_PREFIX}")
logger.info(f"AUTH_KEY: {AUTH_KEY}")
logger.info(f"RETRIES: {RETRIES}")
logger.info(f"BATCH_SIZE: {BATCH_SIZE}")
logger.info("==========================================")
