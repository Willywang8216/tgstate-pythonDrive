from __future__ import annotations

import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .common import http_error
from .. import database
from ..core.config import get_app_settings
from ..core.http_client import apply_runtime_settings


router = APIRouter()
logger = logging.getLogger(__name__)


class PasswordRequest(BaseModel):
    password: str


class AppConfigRequest(BaseModel):
    BOT_TOKEN: str | None = None
    CHANNEL_NAME: str | None = None
    PASS_WORD: str | None = None
    BASE_URL: str | None = None
    PICGO_API_KEY: str | None = None


def _validate_config(cfg: dict) -> None:
    token = (cfg.get("BOT_TOKEN") or "").strip()
    if not token or ":" not in token or len(token) < 20:
        raise http_error(400, "BOT_TOKEN 格式不正确", code="invalid_bot_token")

    channel = (cfg.get("CHANNEL_NAME") or "").strip()
    if not channel or not (channel.startswith("@") or channel.startswith("-100")):
        raise http_error(400, "CHANNEL_NAME 格式不正确（@username 或 -100...）", code="invalid_channel")

    password = (cfg.get("PASS_WORD") or "").strip()
    if not password:
        raise http_error(400, "PASS_WORD 不能为空", code="invalid_password")

    base_url = (cfg.get("BASE_URL") or "").strip()
    if not base_url.startswith("http://") and not base_url.startswith("https://"):
        raise http_error(400, "BASE_URL 必须以 http:// 或 https:// 开头", code="invalid_base_url")


@router.get("/api/app-config")
async def get_app_config(request: Request):
    cfg = get_app_settings()
    return {
        "status": "ok",
        "data": {
            "BOT_TOKEN_SET": bool((cfg.get("BOT_TOKEN") or "").strip()),
            "CHANNEL_NAME": cfg.get("CHANNEL_NAME") or "",
            "PASS_WORD_SET": bool((cfg.get("PASS_WORD") or "").strip()),
            "BASE_URL": cfg.get("BASE_URL") or "http://127.0.0.1:8000",
            "PICGO_API_KEY_SET": bool((cfg.get("PICGO_API_KEY") or "").strip()),
        },
        "setup_required": bool(getattr(request.app.state, "setup_required", True)),
        "bot_running": bool(getattr(request.app.state, "bot_app", None)),
    }


@router.post("/api/app-config")
async def save_app_config(payload: AppConfigRequest, request: Request):
    existing = database.get_app_settings_from_db()
    incoming = payload.model_dump()

    merged = dict(existing)
    for k, v in incoming.items():
        if v is None:
            continue
        if isinstance(v, str) and not v.strip():
            continue
        merged[k] = v

    if not (merged.get("BASE_URL") or "").strip():
        merged["BASE_URL"] = "http://127.0.0.1:8000"

    _validate_config(merged)
    database.save_app_settings_to_db(merged)
    await apply_runtime_settings(request.app)
    logger.info("应用配置已更新并生效")
    resp = JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "message": "配置已保存并生效",
            "setup_required": bool(getattr(request.app.state, "setup_required", True)),
            "bot_running": bool(getattr(request.app.state, "bot_app", None)),
        },
    )
    if merged.get("PASS_WORD"):
        resp.set_cookie(key="password", value=merged["PASS_WORD"], httponly=True, samesite="Lax")
    return resp


@router.post("/api/reset-config")
async def reset_config(request: Request):
    database.reset_app_settings_in_db()
    await apply_runtime_settings(request.app)
    logger.warning("应用配置已重置")
    resp = JSONResponse(status_code=200, content={"status": "ok", "message": "配置已重置", "setup_required": True})
    resp.delete_cookie("password")
    return resp


@router.post("/api/set-password")
async def set_password(payload: PasswordRequest, request: Request):
    try:
        current = get_app_settings()
        database.save_app_settings_to_db({**current, "PASS_WORD": payload.password})
        await apply_runtime_settings(request.app)
        logger.info("密码已更新")
        return {"status": "ok", "message": "密码已成功设置。"}
    except Exception as e:
        logger.error("写入密码失败: %s", e)
        raise http_error(500, "无法写入密码。", code="write_password_failed", details=str(e))

