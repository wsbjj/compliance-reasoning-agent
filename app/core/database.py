"""
PostgreSQL 数据库连接管理
- 使用 SQLAlchemy 2.0 异步引擎 (asyncpg 驱动)
- 提供 async session 工厂
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

# 异步引擎 — 延迟初始化
_engine = None
_async_session_factory = None


def get_engine():
    """获取或创建异步数据库引擎"""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            pool_size=10,
            max_overflow=20,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """获取异步 Session 工厂"""
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_factory


async def get_db_session() -> AsyncSession:
    """FastAPI 依赖注入: 获取数据库会话"""
    factory = get_session_factory()
    async with factory() as session:
        yield session


async def init_db():
    """初始化数据库 — 创建所有表 (开发环境用)"""
    from app.models.base import Base

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """关闭数据库连接"""
    global _engine, _async_session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_factory = None
