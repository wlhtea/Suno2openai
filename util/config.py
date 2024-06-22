import os
import time

from dotenv import load_dotenv

from util.logger import logger

load_dotenv(encoding="ascii")

# 版本号
VERSION = "0.2.1"

# BASE_URL
BASE_URL = os.getenv('BASE_URL', 'https://studio-api.suno.ai')
# SESSION_ID
SESSION_ID = os.getenv('SESSION_ID')
# 代理
PROXY = os.getenv('PROXY', None)
# 用户名
USER_NAME = os.getenv('USER_NAME', '')
# 数据库名
SQL_NAME = os.getenv('SQL_NAME', '')
# 数据库密码
SQL_PASSWORD = os.getenv('SQL_PASSWORD', '')
# 数据库IP
SQL_IP = os.getenv('SQL_IP', '')
# 数据库端口
SQL_DK = os.getenv('SQL_DK', 3306)
# cookies前缀
COOKIES_PREFIX = os.getenv('COOKIES_PREFIX', "")
# 鉴权key
AUTH_KEY = os.getenv('AUTH_KEY', str(time.time()))
# 重试次数
RETRIES = int(os.getenv('RETRIES', 5))
# 添加刷新cookies时的批处理数量（默认10）
BATCH_SIZE = int(os.getenv('BATCH_SIZE', 10))
# 最大等待时间（分钟）
MAX_TIME = int(os.getenv('MAX_TIME', 5))

# 处理措施
if not PROXY:
    PROXY = None

# 记录配置信息
logger.info("==========================================")
logger.info(f"VERSION: {VERSION}")
logger.info(f"BASE_URL: {BASE_URL}")
logger.info(f"SESSION_ID: {SESSION_ID}")
logger.info(f"PROXY: {PROXY}")
logger.info(f"USER_NAME: {USER_NAME}")
logger.info(f"SQL_NAME: {SQL_NAME}")
logger.info(f"SQL_PASSWORD: {SQL_PASSWORD}")
logger.info(f"SQL_IP: {SQL_IP}")
logger.info(f"SQL_DK: {SQL_DK}")
logger.info(f"COOKIES_PREFIX: {COOKIES_PREFIX}")
logger.info(f"AUTH_KEY: {AUTH_KEY}")
logger.info(f"RETRIES: {RETRIES}")
logger.info(f"MAX_TIME: {MAX_TIME}")
logger.info(f"BATCH_SIZE: {BATCH_SIZE}")
logger.info("==========================================")
