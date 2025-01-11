# 新建constants.py文件存放所有常量
CLERK_API_VERSION = "2024-10-01"
CLERK_JS_VERSION = "5.43.6"

URLS = {
    "GET_SESSION": "https://clerk.suno.com/v1/client/verify",
    "EXCHANGE_TOKEN": "https://clerk.suno.com/v1/client/sessions/{sid}/tokens",
    "BASE_URL": "https://studio-api.suno.ai",
    "BILLING_INFO": "https://studio-api.suno.ai/api/billing/info/",
    "HCAPTCHA_CONFIG": "https://api.hcaptcha.com/checksiteconfig",
    "CAPSOLVER_CREATE": "https://api.capsolver.com/createTask",
    "CAPSOLVER_RESULT": "https://api.capsolver.com/getTaskResult"
}

SITE_KEYS = [
    "0x4AAAAAAAFV93qQdS0ycilX",
    "0x4AAAAAAAWXJGBD7bONzLBd"
]

SITE_URLS = [
    "https://clerk.suno.com/cloudflare/turnstile/v0/api.js?render=explicit&__clerk_api_version=2024-10-01&_clerk_js_version=5.43.6",
    "https://suno.com/",
    "https://clerk.suno.com/v1/client?__clerk_api_version=2024-10-01&_clerk_js_version=5.43.2&_method=PATCH"
]

MUSIC_GENRE_LIST = [
    "African", "Asian", "South and southeast Asian", "Avant-garde",
    "Blues", "Caribbean and Caribbean-influenced", "Comedy", "Country",
    "Easy listening", "Electronic", "Folk", "Hip hop", "Jazz",
    "Latin", "Pop", "R&B and soul", "Rock",
] 