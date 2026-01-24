from __future__ import annotations

import logging
import os
import shutil
import tempfile
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Header, Request, UploadFile

from ..core.config import Settings, get_app_settings, get_settings
from ..core.channels import get_primary_channel, split_channel_config
from ..services.telegram_service import get_telegram_service, get_telegram_service_for_channel
from .common import ensure_upload_auth, http_error


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/api/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    key: Optional[str] = Form(None),
    channel_name: Optional[str] = Form(None),
    settings: Settings = Depends(get_settings),
    x_api_key: Optional[str] = Header(None),
):
    """
    上传文件到 Telegram 对应的频道/群组。

    - 支持通过 `channel_name` 指定上传目标频道/群组；
    - 如未指定则使用配置中的第一个频道作为默认目标；
    - TelegramService 会负责写入数据库元数据并返回 short_id。
    """
    app_settings = get_app_settings()
    bot_token = (app_settings.get("BOT_TOKEN") or "").strip()
    channel_cfg = (app_settings.get("CHANNEL_NAME") or "").strip()
    if not bot_token or not channel_cfg:
        raise http_error(503, "缺少 BOT_TOKEN 或 CHANNEL_NAME，无法上传", code="cfg_missing")

    channels = split_channel_config(channel_cfg)
    if not channels:
        raise http_error(503, "缺少可用的频道配置，无法上传", code="cfg_missing")

    # 上传鉴权（密码 / API Key）
    ensure_upload_auth(request, app_settings, x_api_key or key)

    # 解析上传目标频道：如未指定则使用默认频道
    target_channel: Optional[str] = None
    if channel_name:
        requested = channel_name.strip()
        if requested:
            # 与配置中的频道做宽松匹配（忽略大小写和前导 @）
            req_norm = requested.lower().lstrip("@")
            for c in channels:
                if c.lower().lstrip("@") == req_norm:
                    target_channel = c
                    break
            if not target_channel:
                raise http_error(400, "目标频道不在配置列表中", code="invalid_upload_channel")
    if not target_channel:
        target_channel = get_primary_channel(channel_cfg) or channels[0]

    temp_file_path: Optional[str] = None
    try:
        # 将上传内容落地到临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            temp_file_path = temp_file.name
            shutil.copyfileobj(file.file, temp_file)

        # 基于目标频道创建 TelegramService
        try:
            telegram_service = get_telegram_service_for_channel(target_channel)
        except Exception:
            # 理论上不应触发，仅作兜底，回退到默认频道
            telegram_service = get_telegram_service()

        short_id = await telegram_service.upload_file(temp_file_path, file.filename)
    except Exception as e:
        logger.error("上传失败: %s: %s", file.filename, e)
        raise http_error(500, "文件上传失败。", code="upload_failed", details=str(e))
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass

    if not short_id:
        logger.error("上传失败（未返回 short_id）: %s", file.filename)
        raise http_error(500, "文件上传失败。", code="upload_failed")

    # 构造短链 URL: /d/{short_id}
    file_path = f"/d/{short_id}"

    # 始终返回相对路径，前端负责拼接 origin
    full_url = file_path

    logger.info("上传成功: %s -> %s (channel=%s)", file.filename, short_id, target_channel)
    return {
        "file_id": short_id,          # 用于分享的 ID (即 short_id)
        "short_id": short_id,         # 兼容旧字段
        "download_path": file_path,   # 用户要求的字段
        "path": file_path,            # 兼容旧字段
        "url": str(full_url),         # 兼容旧字段
    }

