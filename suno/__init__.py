"""
Suno AI API Client
"""

from .suno import SongsGen
from .constants import CLERK_API_VERSION, CLERK_JS_VERSION, URLs, CaptchaConfig, DEFAULT_HEADERS

__version__ = "0.2.1"
__all__ = ["SongsGen", "CLERK_API_VERSION", "CLERK_JS_VERSION", "URLs", "CaptchaConfig", "DEFAULT_HEADERS"] 