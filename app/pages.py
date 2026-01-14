from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates
from urllib.parse import quote

from . import database
from .core.config import get_active_password, get_app_settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _page_cfg(request: Request) -> dict:
    cfg = get_app_settings()
    bot_token = (cfg.get("BOT_TOKEN") or "").strip()
    channel = (cfg.get("CHANNEL_NAME") or "").strip()
    bot_ready = bool(bot_token and channel)
    missing = []
    if not bot_token:
        missing.append("BOT_TOKEN")
    if not channel:
        missing.append("CHANNEL_NAME")

    bot_running = bool(getattr(request.app.state, "bot_app", None))
    return {"bot_ready": bot_ready, "bot_running": bot_running, "missing": missing}


@router.get("/welcome", response_class=HTMLResponse)
async def welcome_page(request: Request):
    return templates.TemplateResponse("welcome.html", {"request": request})


@router.get("/", response_class=HTMLResponse)
async def main_page(request: Request):
    """
    提供主页。鉴权由中间件处理。
    """
    files = database.get_all_files()
    return templates.TemplateResponse("index.html", {"request": request, "files": files, "cfg": _page_cfg(request)})



@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """
    提供设置页面，用于更改密码。
    权限验证已移至全局中间件。
    """
    return templates.TemplateResponse("settings.html", {"request": request, "cfg": _page_cfg(request)})

@router.get("/pwd", response_class=HTMLResponse)
async def get_password_page(request: Request):
    """
    提供密码输入页面。
    """
    return templates.TemplateResponse("pwd.html", {"request": request})

@router.post("/pwd")
async def submit_password(password: str = Form(...)):
    """
    处理密码提交，设置 cookie 并重定向。
    """
    active_password = get_active_password()
    if password == active_password:
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(key="password", value=password, httponly=True, samesite="Lax")
        return response
    else:
        return RedirectResponse(url="/pwd?error=1", status_code=303)

@router.get("/image_hosting", response_class=HTMLResponse)
async def image_hosting_page(request: Request):
    """
    提供图床页面，并展示所有已上传的图片。
    权限验证已移至全局中间件。
    """
    all_files = database.get_all_files()
    # 定义图片文件后缀
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')
    # 为模板准备图片数据，只筛选图片文件
    files = [
        file for file in all_files 
        if file["filename"].lower().endswith(image_extensions)
    ]
    return templates.TemplateResponse(
        "image_hosting.html",
        {"request": request, "files": files, "cfg": _page_cfg(request)},
    )


@router.get("/share/{file_id}", response_class=HTMLResponse)
async def share_page(request: Request, file_id: str):
    """
    提供文件分享页面，生成多种格式的下载链接。
    """
    file_info = database.get_file_by_id(file_id)
    if not file_info:
        return templates.TemplateResponse("error.html", {"request": request, "message": "File not found!"}, status_code=404)

    # 构建完整的文件URL
    cfg = get_app_settings()
    base_url = (cfg.get("BASE_URL") or "").strip() or str(request.base_url).rstrip("/")
    encoded_filename = quote(file_info["filename"])
    file_url = f"{base_url}/d/{file_id}/{encoded_filename}"

    # 准备传递给模板的数据
    file_data = {
        "filename": file_info["filename"],
        "filesize": file_info["filesize"],
        "upload_date": file_info["upload_date"],
        "file_url": file_url,
        "html_code": f'<a href="{file_url}">Download {file_info["filename"]}</a>',
        "markdown_code": f'[{file_info["filename"]}]({file_url})'
    }
    return templates.TemplateResponse("download.html", {"request": request, "file": file_data})
