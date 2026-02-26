"""
健康检查端点
"""
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "compliance-reasoning-agent",
        "version": "0.1.0",
    }
