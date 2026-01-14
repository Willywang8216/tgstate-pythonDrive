from __future__ import annotations

import logging
from fastapi import HTTPException, Request
from typing import Any

from ..core.config import get_active_password

logger = logging.getLogger(__name__)


def error_payload(message: str, *, code: str = "error", details: Any | None = None) -> dict:
    payload = {"status": "error", "code": code, "message": message}
    if details is not None:
        payload["details"] = details
    return payload


def http_error(status_code: int, message: str, *, code: str = "error", details: Any | None = None) -> HTTPException:
    return HTTPException(status_code=status_code, detail=error_payload(message, code=code, details=details))


def is_web_upload_request(request: Request) -> bool:
    return "referer" in request.headers


import re
from pypinyin import lazy_pinyin

COOKIE_NAME = "tgstate_session"

def generate_slug(filename: str) -> str:
    # 1. 转换为拼音
    pinyin_list = lazy_pinyin(filename)
    slug_raw = "".join(pinyin_list)
    # 2. 只保留字母数字和连字符，且转小写
    slug = re.sub(r'[^a-z0-9\-\.]', '', slug_raw.lower())
    # 3. 如果 slug 太长，截断；如果太短或为空，用 default
    if not slug:
        slug = "file"
    if len(slug) > 50:
        slug = slug[:50]
    return slug

def ensure_upload_auth(request: Request, app_settings: dict, submitted_key: str | None) -> None:
    picgo_api_key = app_settings.get("PICGO_API_KEY")
    active_password = app_settings.get("PASS_WORD") or get_active_password()
    web_request = is_web_upload_request(request)

    if not active_password and not picgo_api_key:
        return

    if picgo_api_key and not active_password:
        if web_request:
            return
        if picgo_api_key == submitted_key:
            return
        logger.warning("API 上传鉴权失败：无效 API Key")
        raise http_error(401, "无效的 API 密钥", code="invalid_api_key")

    if not picgo_api_key and active_password:
        if not web_request:
            return
        # Fix: use correct cookie name
        session_password = request.cookies.get(COOKIE_NAME)
        if active_password == session_password:
            return
        logger.warning("Web 上传鉴权失败：需要登录")
        raise http_error(401, "需要网页登录", code="login_required")

    if web_request:
        session_password = request.cookies.get(COOKIE_NAME)
        if active_password == session_password:
            return
        logger.warning("Web 上传鉴权失败：需要登录")
        raise http_error(401, "需要网页登录", code="login_required")

    if picgo_api_key == submitted_key:
        return
    logger.warning("API 上传鉴权失败：无效 API Key")
    raise http_error(401, "无效的 API 密钥", code="invalid_api_key")

