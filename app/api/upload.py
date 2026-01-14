from __future__ import annotations

import os
import shutil
import tempfile
import logging
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, Header, UploadFile, Request

from ..core.config import Settings, get_app_settings, get_settings
from ..services.telegram_service import get_telegram_service
from .common import ensure_upload_auth, http_error


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/api/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    key: Optional[str] = Form(None),
    settings: Settings = Depends(get_settings),
    x_api_key: Optional[str] = Header(None),
):
    app_settings = get_app_settings()
    if not (app_settings.get("BOT_TOKEN") or "").strip() or not (app_settings.get("CHANNEL_NAME") or "").strip():
        raise http_error(503, "缺少 BOT_TOKEN 或 CHANNEL_NAME，无法上传", code="cfg_missing")
    ensure_upload_auth(request, app_settings, x_api_key or key)
    logger.info("开始上传: %s", file.filename)

    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            temp_file_path = temp_file.name
            shutil.copyfileobj(file.file, temp_file)

        telegram_service = get_telegram_service()
        file_id = await telegram_service.upload_file(temp_file_path, file.filename)
    except Exception as e:
        logger.error("上传失败: %s: %s", file.filename, e)
        raise http_error(500, "文件上传失败。", code="upload_failed", details=str(e))
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass

    if not file_id:
        logger.error("上传失败（未返回 file_id）: %s", file.filename)
        raise http_error(500, "文件上传失败。", code="upload_failed")

    # file_id 可能是 short_id (如果 add_file_metadata 返回了 short_id)
    # 或者如果 upload_file 还是返回 composite_id，我们需要确认 telegram_service 的修改
    # 假设 telegram_service 已经修改为返回 short_id
    
    # 构造短链 URL
    # 不再在 URL 中包含文件名
    file_path = f"/d/{file_id}"
    base_url = (app_settings.get("BASE_URL") or settings.BASE_URL).strip("/")
    
    # 如果配置了 BASE_URL，则使用它；否则返回相对路径让前端处理
    if base_url:
        full_url = f"{base_url}{file_path}"
    else:
        # 如果没有 BASE_URL，我们也返回相对路径，前端会拼接 origin
        full_url = file_path

    logger.info("上传成功: %s -> %s", file.filename, file_id)
    # 返回 short_id 方便前端使用
    return {"path": file_path, "url": str(full_url), "short_id": file_id}

