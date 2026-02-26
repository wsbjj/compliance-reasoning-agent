"""
FastAPI API 路由 — 分析任务端点
Controller 层
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agent.graph import run_agent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analysis", tags=["analysis"])


# ---- 请求/响应模型 ----
class AnalysisRequest(BaseModel):
    """分析请求"""
    query: str = Field(..., description="产品核心关键词，如 'Smart Ring'")
    extra_context: str = Field(
        default="",
        description="额外上下文信息，如 '近期 AI API 成本下降 80%'",
    )
    user_id: str = Field(default="default", description="用户 ID")


class AnalysisResponse(BaseModel):
    """分析响应"""
    report_id: str
    query: str
    status: str
    final_report: str | None = None
    patent_count: int = 0
    trend_keywords: int = 0
    iterations: int = 0
    plan: str | None = None
    patent_analysis: str | None = None
    trend_analysis: str | None = None
    error: str | None = None


class AnalysisHistoryItem(BaseModel):
    """历史分析条目"""
    report_id: str
    query: str
    status: str
    created_at: str


# ---- 内存中的报告存储 (开发阶段) ----
_reports: dict[str, dict[str, Any]] = {}


@router.post("/run", response_model=AnalysisResponse)
async def run_analysis(request: AnalysisRequest):
    """
    触发完整的合规推理智能体工作流

    接收产品关键词，执行：
    1. 任务规划 → 2. 专利搜索 → 3. 趋势分析 → 4. 报告生成 → 5. 质量审核
    """
    report_id = str(uuid.uuid4())

    logger.info(
        f"[API] Starting analysis: query='{request.query}', report_id={report_id}"
    )

    try:
        # 执行智能体工作流
        final_state = await run_agent(
            query=request.query,
            extra_context=request.extra_context,
            user_id=request.user_id,
        )

        # 构建响应
        response = AnalysisResponse(
            report_id=report_id,
            query=request.query,
            status="completed" if not final_state.get("error") else "failed",
            final_report=final_state.get("final_report")
            or final_state.get("draft_report"),
            patent_count=len(final_state.get("patents", [])),
            trend_keywords=len(final_state.get("trend_summaries", [])),
            iterations=final_state.get("iteration_count", 0),
            plan=final_state.get("plan"),
            patent_analysis=final_state.get("patent_analysis"),
            trend_analysis=final_state.get("trend_analysis"),
            error=final_state.get("error"),
        )

        # 存储报告
        _reports[report_id] = {
            "response": response.model_dump(),
            "state": {
                k: v
                for k, v in final_state.items()
                if isinstance(v, (str, int, float, bool, list, dict, type(None)))
            },
        }

        return response

    except Exception as e:
        logger.error(f"[API] Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{report_id}", response_model=AnalysisResponse)
async def get_report(report_id: str):
    """获取分析报告"""
    if report_id not in _reports:
        raise HTTPException(status_code=404, detail="Report not found")

    return AnalysisResponse(**_reports[report_id]["response"])


@router.get("/", response_model=list[AnalysisHistoryItem])
async def list_reports():
    """获取历史分析列表"""
    from datetime import datetime

    items = []
    for rid, data in _reports.items():
        resp = data["response"]
        items.append(
            AnalysisHistoryItem(
                report_id=rid,
                query=resp.get("query", ""),
                status=resp.get("status", "unknown"),
                created_at=datetime.now().isoformat(),
            )
        )
    return items
