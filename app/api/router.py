"""
API 路由聚合
"""
from fastapi import APIRouter

from app.api.analysis import router as analysis_router
from app.api.health import router as health_router
from app.api.patents import router as patents_router
from app.api.trends import router as trends_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(analysis_router)
api_router.include_router(patents_router)
api_router.include_router(trends_router)
