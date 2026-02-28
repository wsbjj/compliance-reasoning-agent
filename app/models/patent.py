"""
专利数据模型 (Patent Model)
存储从 SerpApi / USPTO 拉取的专利信息
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Patent(Base):
    """专利数据表"""
    __tablename__ = "patents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # 专利标题
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    # 申请人 / 权利人
    assignee: Mapped[str | None] = mapped_column(String(300), nullable=True)
    # 摘要 / snippet
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 专利号 (patent_id)
    patent_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    # 公开号 (publication_number)
    publication_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 申请日期
    filing_date: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # 优先权日
    priority_date: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # 公开日
    publication_date: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # 发明人
    inventor: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # PDF 原文链接
    pdf_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 缩略图 URL
    thumbnail_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 图表链接列表 (JSON 数组)
    figures: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    # 各国有效性状态 (JSON map)
    country_status: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # 搜索关键词 (关联到哪个查询)
    search_query: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    # 数据来源: serpapi | uspto
    source: Mapped[str] = mapped_column(String(20), default="serpapi")
    # LLM 提取的核心技术点 (JSON 数组)
    tech_points: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # 竞品分类
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 原始 JSON 数据备份
    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
