from __future__ import annotations

import asyncio
import mimetypes
import logging
from typing import List
from urllib.parse import quote

import httpx
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .. import database
from ..core.http_client import get_http_client
from ..services.telegram_service import TelegramService, get_telegram_service
from .common import http_error


router = APIRouter()
logger = logging.getLogger(__name__)

async def serve_file(
    file_id: str,
    filename: str,
    telegram_service: TelegramService,
    client: httpx.AsyncClient
):
    """
    Common logic to serve a file given its file_id (composite) and filename.
    """
    try:
        _, real_file_id = file_id.split(":", 1)
    except ValueError:
        real_file_id = file_id

    download_url = await telegram_service.get_download_url(real_file_id)
    if not download_url:
        raise http_error(404, "文件未找到或下载链接已过期。", code="file_not_found")

    range_headers = {"Range": "bytes=0-127"}
    try:
        head_resp = await client.get(download_url, headers=range_headers)
        head_resp.raise_for_status()
        first_bytes = head_resp.content
    except httpx.RequestError as e:
        raise http_error(503, "无法连接到 Telegram 服务器。", code="tg_unreachable", details=str(e))

    # Check for manifest (large file split)
    if first_bytes.startswith(b"tgstate-blob\n"):
        manifest_resp = await client.get(download_url)
        manifest_resp.raise_for_status()
        manifest_content = manifest_resp.content

        lines = manifest_content.decode("utf-8").strip().split("\n")
        if len(lines) < 3:
            raise http_error(500, "清单文件格式错误。", code="manifest_invalid")
        original_filename = lines[1]
        chunk_file_ids = [cid for cid in lines[2:] if cid.strip()]

        # Use the original filename from manifest if available, though we passed one in.
        # Usually they match. We'll use the one passed in for Content-Disposition if provided,
        # but manifest's filename is the source of truth for the content.
        # Let's stick to the one passed in for the header.
        
        filename_encoded = quote(str(filename))
        response_headers = {"Content-Disposition": f"attachment; filename*=UTF-8''{filename_encoded}"}
        return StreamingResponse(stream_chunks(chunk_file_ids, telegram_service, client), headers=response_headers)

    # Standard single file
    image_extensions = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp")
    is_image = filename.lower().endswith(image_extensions)

    filename_encoded = quote(str(filename))

    content_type, _ = mimetypes.guess_type(filename)
    if content_type is None:
        content_type = "application/octet-stream"

    disposition_type = "inline" if is_image else "attachment"
    response_headers = {
        "Content-Disposition": f"{disposition_type}; filename*=UTF-8''{filename_encoded}",
        "Content-Type": content_type,
    }

    async def single_file_streamer():
        async with client.stream("GET", download_url) as resp:
            resp.raise_for_status()
            async for chunk in resp.aiter_bytes():
                yield chunk

    return StreamingResponse(single_file_streamer(), headers=response_headers)


@router.get("/d/{file_id}/{filename}")
async def download_file_legacy(
    file_id: str,
    filename: str,
    client: httpx.AsyncClient = Depends(get_http_client),
):
    """
    Legacy route for downloading files using explicit file_id and filename.
    """
    try:
        telegram_service = get_telegram_service()
    except Exception:
        raise http_error(503, "未配置 BOT_TOKEN/CHANNEL_NAME，下载不可用", code="cfg_missing")

    return await serve_file(file_id, filename, telegram_service, client)


@router.get("/d/{identifier}")
async def download_file_short(
    identifier: str,
    client: httpx.AsyncClient = Depends(get_http_client),
):
    """
    New route for downloading files using short_id (or checking file_id).
    """
    try:
        telegram_service = get_telegram_service()
    except Exception:
        raise http_error(503, "未配置 BOT_TOKEN/CHANNEL_NAME，下载不可用", code="cfg_missing")

    # Lookup metadata
    meta = database.get_file_by_id(identifier)
    if not meta:
         raise http_error(404, "文件不存在", code="file_not_found")

    return await serve_file(meta['file_id'], meta['filename'], telegram_service, client)


@router.get("/api/files")
async def get_files_list():
    return database.get_all_files()


@router.delete("/api/files/{file_id}")
async def delete_file(
    file_id: str,
):
    try:
        telegram_service = get_telegram_service()
    except Exception:
        raise http_error(503, "未配置 BOT_TOKEN/CHANNEL_NAME，删除不可用", code="cfg_missing")

    logger.info("请求删除文件: %s", file_id)
    delete_result = await telegram_service.delete_file_with_chunks(file_id)

    if delete_result.get("main_message_deleted"):
        was_deleted_from_db = database.delete_file_metadata(file_id)
        delete_result["db_status"] = "deleted" if was_deleted_from_db else "not_found_in_db"
    else:
        delete_result["db_status"] = "skipped_due_to_tg_error"

    if delete_result.get("status") == "success":
        logger.info("删除成功: %s", file_id)
        return {"status": "ok", "message": f"文件 {file_id} 已成功处理。", "details": delete_result}

    if delete_result.get("status") == "partial_failure":
        logger.warning("删除部分失败: %s", file_id)
        raise http_error(500, f"文件 {file_id} 删除部分失败。", code="delete_partial_failure", details=delete_result)

    logger.warning("删除失败: %s", file_id)
    raise http_error(400, f"删除文件 {file_id} 时出错。", code="delete_failed", details=delete_result)


class BatchDeleteRequest(BaseModel):
    file_ids: List[str]


@router.post("/api/batch_delete")
async def batch_delete_files(
    request_data: BatchDeleteRequest,
    telegram_service: TelegramService = Depends(get_telegram_service),
):
    successful_deletions = []
    failed_deletions = []

    for file_id in request_data.file_ids:
        try:
            response = await delete_file(file_id)
            successful_deletions.append(response)
        except Exception as e:
            if hasattr(e, "detail"):
                failed_deletions.append(e.detail)
            else:
                failed_deletions.append({"file_id": file_id, "error": str(e)})

    return {"status": "completed", "deleted": successful_deletions, "failed": failed_deletions}


async def stream_chunks(chunk_composite_ids, telegram_service: TelegramService, client: httpx.AsyncClient):
    for chunk_id in chunk_composite_ids:
        try:
            _, actual_chunk_id = chunk_id.split(":", 1)
        except (ValueError, IndexError):
            continue

        chunk_url = await telegram_service.get_download_url(actual_chunk_id)
        if not chunk_url:
            continue

        try:
            async with client.stream("GET", chunk_url) as chunk_resp:
                if chunk_resp.status_code != 200:
                    await asyncio.sleep(1)
                    chunk_url = await telegram_service.get_download_url(actual_chunk_id)
                    if not chunk_url:
                        break
                    async with client.stream("GET", chunk_url) as retry_resp:
                        retry_resp.raise_for_status()
                        async for chunk_data in retry_resp.aiter_bytes():
                            yield chunk_data
                else:
                    async for chunk_data in chunk_resp.aiter_bytes():
                        yield chunk_data
        except httpx.RequestError:
            break
