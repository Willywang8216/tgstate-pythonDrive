import logging
import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI
import asyncio

# 导入应用所需的其他模块
from .. import database
from ..bot_handler import create_bot_app
from ..core.config import get_app_settings

logger = logging.getLogger(__name__)

# 这个变量将持有我们全局共享的客户端实例
http_client: httpx.AsyncClient | None = None

def _is_setup_required(app_settings: dict) -> bool:
    return not (
        (app_settings.get("BOT_TOKEN") or "").strip()
        and (app_settings.get("CHANNEL_NAME") or "").strip()
        and (app_settings.get("PASS_WORD") or "").strip()
    )

async def _stop_bot(app: FastAPI) -> None:
    if hasattr(app.state, "bot_app") and app.state.bot_app:
        try:
            await app.state.bot_app.updater.stop()
        except Exception:
            pass
        try:
            await app.state.bot_app.stop()
        except Exception:
            pass
        try:
            await app.state.bot_app.shutdown()
        except Exception:
            pass
        app.state.bot_app = None
        logger.info("机器人已停止")

async def _start_bot(app: FastAPI, app_settings: dict) -> None:
    await _stop_bot(app)
    bot_app = create_bot_app(app_settings)
    app.state.bot_app = bot_app
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling(drop_pending_updates=True)
    logger.info("机器人已在后台启动")

async def apply_runtime_settings(app: FastAPI) -> None:
    async with app.state.settings_lock:
        current = get_app_settings()
        app.state.app_settings = current
        setup_required = _is_setup_required(current)
        app.state.setup_required = setup_required

        if setup_required:
            await _stop_bot(app)
            return

        await _start_bot(app, current)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理器。
    在应用启动时：
    1. 初始化数据库。
    2. 创建并启动 Telegram Bot。
    3. 创建一个共享的、支持高并发的 httpx.AsyncClient。
    在应用关闭时：
    1. 优雅地关闭 httpx.AsyncClient。
    2. 优雅地停止 Telegram Bot。
    """
    # --- 启动逻辑 ---
    logger.info("应用启动")
    
    # 1. 初始化数据库
    database.init_db()
    logger.info("数据库已初始化")

    app.state.settings_lock = asyncio.Lock()
    app.state.app_settings = get_app_settings()
    app.state.setup_required = _is_setup_required(app.state.app_settings)

    # 2. 创建共享的 httpx.AsyncClient
    global http_client
    limits = httpx.Limits(max_connections=200, max_keepalive_connections=50)
    http_client = httpx.AsyncClient(timeout=300.0, limits=limits)
    logger.info("共享的 HTTP 客户端已创建")

    # 3. 启动 Telegram Bot（仅在配置完成后）
    if not app.state.setup_required:
        try:
            await _start_bot(app, app.state.app_settings)
        except Exception as e:
            logger.error("启动机器人失败: %s", e)
            app.state.bot_app = None
            app.state.setup_required = True

    yield # 应用在此处运行

    # --- 关闭逻辑 ---
    logger.info("应用关闭")

    # 1. 关闭共享的 httpx.AsyncClient
    if http_client:
        await http_client.aclose()
        logger.info("共享的 HTTP 客户端已关闭")

    # 2. 停止 Telegram Bot
    await _stop_bot(app)


def get_http_client() -> httpx.AsyncClient:
    """
    一个 FastAPI 依赖项，用于获取共享的 httpx 客户端实例。
    """
    if http_client is None:
        raise RuntimeError("HTTP client is not initialized. Is the app lifespan configured correctly?")
    return http_client
