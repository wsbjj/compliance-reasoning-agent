"""
趋势数据模型 (Trend Model)
存储 Google Trends / Rainforest / Keepa 的趋势数据
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TrendData(Base):
    """趋势数据表"""
    __tablename__ = "trend_data"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # 关键词
    keyword: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    # 数据日期
    date: Mapped[str] = mapped_column(String(30), nullable=False)
    # 搜索指数 / 搜索量
    value: Mapped[float] = mapped_column(Float, nullable=True)
    # 数据来源: pytrends | rainforest | keepa
    source: Mapped[str] = mapped_column(String(20), default="pytrends")
    # 搜索查询 (关联到哪个分析任务)
    search_query: Mapped[str] = mapped_column(String(200), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class TrendSummary(Base):
    """趋势摘要表 — 存储计算后的增长率"""
    __tablename__ = "trend_summaries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    keyword: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    search_query: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    # 复合年均增长率
    cagr: Mapped[float | None] = mapped_column(Float, nullable=True)
    # 复合月均增长率
    cmgr: Mapped[float | None] = mapped_column(Float, nullable=True)
    # 起始值
    beginning_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    # 结束值
    ending_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    # 数据源
    source: Mapped[str] = mapped_column(String(20), default="pytrends")
    # 时间范围 (月)
    timeframe_months: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
