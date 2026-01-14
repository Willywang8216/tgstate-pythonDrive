import logging
import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse

# 导入我们的新生命周期管理器和路由
from .core.http_client import lifespan
from .api import routes as api_routes
from .pages import router as pages_router
from .core.config import get_active_password
from .api.common import error_payload

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

# 使用集成的 lifespan 管理器创建 FastAPI 应用
app = FastAPI(
    lifespan=lifespan,
    title="tgState",
    description="一个基于 Telegram 的私有文件存储系统。",
    version="2.0.0"
)

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """
    一个全局中间件，用于处理所有页面的访问权限。
    """
    active_password = get_active_password()
    request_path = request.url.path

    # 定义公共路径，这些路径永远不拦截
    public_paths = ["/static", "/api", "/d", "/favicon.ico"]
    is_public = any(request_path.startswith(p) for p in public_paths)

    # 情况 1：未设置密码
    if not active_password:
        # 如果是引导页或 API/静态资源，放行
        if request_path == "/welcome" or request_path == "/settings" or is_public:
            return await call_next(request)
        # 否则强制重定向到引导页
        return RedirectResponse(url="/welcome", status_code=307)

    # 情况 2：已设置密码
    # 如果访问引导页，强制跳转到主页
    if request_path == "/welcome":
        return RedirectResponse(url="/", status_code=307)

    # 保护 API
    protected_api_paths = ("/api/upload", "/api/delete")
    if request_path in protected_api_paths:
        session_password = request.cookies.get("password")
        if session_password != active_password:
            return JSONResponse(
                status_code=401,
                content={"detail": error_payload("需要网页登录", code="login_required")},
            )

    # 保护页面
    # 明确列出需要登录才能访问的页面
    protected_pages = ["/", "/image_hosting"]
    # 允许不登录访问的页面：/pwd, /settings
    
    if request_path in protected_pages:
        session_password = request.cookies.get("password")
        if session_password != active_password:
            return RedirectResponse(url="/pwd", status_code=307)

    return await call_next(request)

# 挂载静态文件目录
# 注意：这个路径是相对于项目根目录的
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 设置模板目录
# 注意：这个路径也是相对于项目根目录的
templates = Jinja2Templates(directory="app/templates")

# 包含 API 和页面路由
app.include_router(api_routes.router)
app.include_router(pages_router)
