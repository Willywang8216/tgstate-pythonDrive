from __future__ import annotations

import os
import shutil
import tempfile
import logging
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, Header, UploadFile, Request

from ..core.config import Settings, get_app_settings, get_settings
from ..services.telegram_service import TelegramService, get_telegram_service
from .common import ensure_upload_auth, http_error


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/api/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    key: Optional[str] = Form(None),
    settings: Settings = Depends(get_settings),
    telegram_service: TelegramService = Depends(get_telegram_service),
    x_api_key: Optional[str] = Header(None),
):
    app_settings = get_app_settings()
    ensure_upload_auth(request, app_settings, x_api_key or key)
    logger.info("开始上传: %s", file.filename)

    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            temp_file_path = temp_file.name
            shutil.copyfileobj(file.file, temp_file)

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

    encoded_filename = quote(file.filename)
    file_path = f"/d/{file_id}/{encoded_filename}"
    base_url = (app_settings.get("BASE_URL") or settings.BASE_URL).strip("/")
    full_url = f"{base_url}{file_path}"
    logger.info("上传成功: %s -> %s", file.filename, file_id)
    return {"path": file_path, "url": str(full_url)}

