# -*- coding:utf-8 -*-

from typing import Any
from typing import List, Optional

from pydantic import BaseModel
from pydantic import Field


class Response(BaseModel):
    code: Optional[int] = 0
    msg: Optional[str] = "success"
    data: Optional[Any] = None


class GenerateBase(BaseModel):
    token: str = ""
    cookie: str = ""
    session_id: str = ""
    gpt_description_prompt: str = ""
    prompt: str = ""
    mv: str = ""
    title: str = ""
    tags: str = ""
    continue_at: Optional[str] = None
    continue_clip_id: Optional[str] = None


class Message(BaseModel):
    role: str
    content: str


class Data(BaseModel):
    model: str
    messages: List[Message]
    stream: Optional[bool] = None
    title: str = Field(None, description="song title")
    tags: str = Field(None, description="style of music")
    continue_at: Optional[int] = Field(
        default=None,
        description="continue a new clip from a previous song, format number",
        examples=[120],
    )
    continue_clip_id: Optional[str] = None


class Cookies(BaseModel):
    cookies: List[str]
