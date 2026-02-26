"""
Compliance Reasoning Agent — FastAPI 应用入口

启动命令:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings

# ---- 日志配置 ----
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ---- 生命周期管理 ----
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动 / 关闭时的资源管理"""
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} ({settings.app_env})")

    # 启动: 初始化数据库
    try:
        from app.core.database import init_db
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Database init skipped: {e}")

    # 启动: 初始化 Redis
    try:
        from app.core.redis import get_redis
        await get_redis()
        logger.info("Redis connected")
    except Exception as e:
        logger.warning(f"Redis init skipped: {e}")

    yield

    # 关闭: 清理资源
    try:
        from app.core.database import close_db
        from app.core.redis import close_redis
        await close_db()
        await close_redis()
        logger.info("Resources cleaned up")
    except Exception as e:
        logger.warning(f"Cleanup error: {e}")


# ---- 创建 FastAPI 应用 ----
app = FastAPI(
    title="Compliance Reasoning Agent API",
    description="基于 LangGraph 的合规推理智能体 — 专利排查、趋势分析、窗口期预警",
    version="0.1.0",
    lifespan=lifespan,
)

# ---- CORS 中间件 ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- 挂载路由 ----
app.include_router(api_router)


# ---- 根端点 ----
@app.get("/")
async def root():
    """API 根端点"""
    return {
        "service": "compliance-reasoning-agent",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }
