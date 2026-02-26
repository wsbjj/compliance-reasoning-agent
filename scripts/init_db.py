"""
数据库初始化脚本

使用方法:
    python scripts/init_db.py

功能:
    - 连接 PostgreSQL
    - 创建所有 ORM 模型对应的表
"""
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """初始化数据库"""
    logger.info("Initializing database...")

    try:
        from app.core.database import init_db, close_db

        await init_db()
        logger.info("✅ Database tables created successfully")

        await close_db()
        logger.info("Database connection closed")

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        logger.info("请确保 PostgreSQL 正在运行，且 .env 中 DATABASE_URL 配置正确")
        raise


if __name__ == "__main__":
    asyncio.run(main())
