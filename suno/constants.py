"""
常量配置文件
包含API版本、URL端点、站点密钥等配置信息
"""

from typing import Dict, List

# API 版本
CLERK_API_VERSION = "2024-10-01"
CLERK_JS_VERSION = "5.43.6"

# 重试配置
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
TOKEN_REFRESH_STATUS_CODES = [401, 403]  # 需要刷新token的状态码
RETRIABLE_STATUS_CODES = [408, 429, 500, 502, 503, 504]  # 可以重试的状态码

# 任务状态
class TaskStatus:
    """任务状态常量"""
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"
    ERROR = "error"
    
    # 终态状态列表
    FINAL_STATES = [COMPLETE, FAILED, ERROR]
    # 可以重试的状态
    RETRIABLE_STATES = [FAILED, ERROR]

# API 端点
class URLs:
    """所有API端点的URL常量"""
    CLERK_BASE = "https://clerk.suno.com"
    SUNO_BASE = "https://studio-api.prod.suno.com"
    
    # Clerk认证相关
    VERIFY = f"{CLERK_BASE}/v1/client/verify"
    EXCHANGE_TOKEN = f"{CLERK_BASE}/v1/client/sessions/{{sid}}/tokens"
    
    # Suno API
    BILLING_INFO = f"{SUNO_BASE}/api/billing/info/"
    PLAYLIST = f"{SUNO_BASE}/api/playlist/{{playlist_id}}/"
    FEED = f"{SUNO_BASE}/api/feed/v2"
    
    # Captcha相关
    CAPSOLVER_CREATE = "https://api.capsolver.com/createTask"
    CAPSOLVER_RESULT = "https://api.capsolver.com/getTaskResult"
    
    # Check
    CHECK = f"{SUNO_BASE}/api/c/check"

# Captcha配置
class CaptchaConfig:
    """Captcha相关配置"""
    SITE_KEYS: List[str] = [
        "0x4AAAAAAAFV93qQdS0ycilX"
    ]
    
    SITE_URLS: List[str] = [
        f"{URLs.CLERK_BASE}/cloudflare/turnstile/v0/api.js?"
        f"render=explicit&"
        f"__clerk_api_version={CLERK_API_VERSION}&"
        f"_clerk_js_version={CLERK_JS_VERSION}"
    ]

# 默认请求头
DEFAULT_HEADERS: Dict[str, str] = {
    "accept": "*/*",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
    "content-type": "application/x-www-form-urlencoded",
    "origin": "https://suno.com",
    "referer": "https://suno.com/",
    "sec-ch-ua": '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A_Brand";v="24"',
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site"
}

# 音乐类型列表
MUSIC_GENRES: List[str] = [
    "African", "Asian", "South and southeast Asian", "Avant-garde",
    "Blues", "Caribbean and Caribbean-influenced", "Comedy", "Country",
    "Easy listening", "Electronic", "Folk", "Hip hop", "Jazz",
    "Latin", "Pop", "R&B and soul", "Rock",
] 