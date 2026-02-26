"""
Redis 连接管理
- 连接池管理
- 供 Mem0 长期记忆存储和通用缓存使用
"""
from __future__ import annotations

import redis.asyncio as aioredis

from app.core.config import get_settings

_redis_pool: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """获取或创建 Redis 异步连接"""
    global _redis_pool
    if _redis_pool is None:
        settings = get_settings()
        _redis_pool = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
    return _redis_pool


async def close_redis():
    """关闭 Redis 连接池"""
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.close()
        _redis_pool = None
