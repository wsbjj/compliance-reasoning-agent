"""
FastAPI API 路由 — 分析任务端点
Controller 层
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import run_agent
from app.core.database import get_db_session
from app.models.report import AnalysisReport
from app.repositories.report_repo import ReportRepository

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
    countries: list[str] = Field(
        default_factory=list,
        description="国家筛选列表，如 ['US', 'CN']；空列表表示全部",
    )


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
    patent_summary: str | None = None
    trend_summary: str | None = None


@router.post("/run", response_model=AnalysisResponse)
async def run_analysis(
    request: AnalysisRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """
    触发完整的合规推理智能体工作流

    接收产品关键词，执行：
    1. 任务规划 → 2. 专利搜索 → 3. 趋势分析 → 4. 报告生成 → 5. 质量审核 → 6. DB 持久化
    """
    # 1. 在 DB 中创建 "pending" 状态的报告记录
    report_id = uuid.uuid4()
    repo = ReportRepository(session)
    db_report = AnalysisReport(
        id=report_id,
        query=request.query[:200],
        extra_context=request.extra_context,
        status="running",
    )
    await repo.create(db_report)

    report_id_str = str(report_id)
    logger.info(
        f"[API] Starting analysis: query='{request.query}', report_id={report_id_str}"
    )

    try:
        # 2. 执行智能体工作流（将 report_id 注入 state，供 memory_node 使用）
        final_state = await run_agent(
            query=request.query,
            extra_context=request.extra_context,
            user_id=request.user_id,
            report_id=report_id_str,
            countries=request.countries,
        )

        # 3. 若 agent 出错，更新状态为 failed
        if final_state.get("error"):
            await repo.update_status(report_id, "failed")

        # 4. 构建响应
        response = AnalysisResponse(
            report_id=report_id_str,
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

        return response

    except Exception as e:
        logger.error(f"[API] Analysis failed: {e}")
        # 标记数据库记录为失败
        try:
            await repo.update_status(report_id, "failed")
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run_stream")
async def run_analysis_stream(request: AnalysisRequest):
    """
    SSE 流式分析端点 — 实时推送节点执行进度

    前端通过 HTTP Streaming 消费 Server-Sent Events:
      data: {"type":"node_complete","node":"plan","elapsed":2.3,"summary":"..."}
      data: {"type":"result","data":{...}}
    """
    from app.core.database import get_session_factory

    factory = get_session_factory()
    report_id = uuid.uuid4()
    report_id_str = str(report_id)

    # 1. 在 DB 中创建 "running" 状态的报告记录
    async with factory() as session:
        repo = ReportRepository(session)
        db_report = AnalysisReport(
            id=report_id,
            query=request.query[:200],
            extra_context=request.extra_context,
            status="running",
        )
        await repo.create(db_report)

    logger.info(
        f"[API/Stream] Starting analysis: query='{request.query}', "
        f"report_id={report_id_str}"
    )

    # 2. 异步队列：agent 写入进度事件 → SSE 生成器读取
    queue: asyncio.Queue[dict | None] = asyncio.Queue()

    async def _progress_callback(event: dict) -> None:
        await queue.put(event)

    async def _run_agent_task() -> None:
        """后台任务：运行 agent 并将结果/错误推入队列"""
        try:
            final_state = await run_agent(
                query=request.query,
                extra_context=request.extra_context,
                user_id=request.user_id,
                report_id=report_id_str,
                countries=request.countries,
                progress_callback=_progress_callback,
            )

            # 若 agent 出错，更新 DB 状态
            if final_state.get("error"):
                async with factory() as session:
                    repo = ReportRepository(session)
                    await repo.update_status(report_id, "failed")

            # 构建最终结果
            result = {
                "report_id": report_id_str,
                "query": request.query,
                "status": "completed" if not final_state.get("error") else "failed",
                "final_report": final_state.get("final_report")
                or final_state.get("draft_report"),
                "patent_count": len(final_state.get("patents", [])),
                "trend_keywords": len(final_state.get("trend_summaries", [])),
                "iterations": final_state.get("iteration_count", 0),
                "plan": final_state.get("plan"),
                "patent_analysis": final_state.get("patent_analysis"),
                "trend_analysis": final_state.get("trend_analysis"),
                "error": final_state.get("error"),
            }
            await queue.put({"type": "result", "data": result})

        except Exception as e:
            logger.error(f"[API/Stream] Agent failed: {e}")
            try:
                async with factory() as session:
                    repo = ReportRepository(session)
                    await repo.update_status(report_id, "failed")
            except Exception:
                pass
            await queue.put({"type": "error", "message": str(e)})
        finally:
            await queue.put(None)  # 哨兵：通知生成器结束

    async def _event_generator():
        """SSE 事件生成器"""
        task = asyncio.create_task(_run_agent_task())
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except asyncio.CancelledError:
            task.cancel()
            raise

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/", response_model=list[AnalysisHistoryItem])
async def list_reports(
    limit: int = 50,
    session: AsyncSession = Depends(get_db_session),
):
    """获取历史分析列表（从数据库读取，重启后依然保留）"""
    repo = ReportRepository(session)
    reports = await repo.get_recent(limit=limit)

    return [
        AnalysisHistoryItem(
            report_id=str(r.id),
            query=r.query,
            status=r.status,
            created_at=r.created_at.isoformat() if r.created_at else "",
            patent_summary=r.patent_summary,
            trend_summary=r.trend_summary,
        )
        for r in reports
    ]


@router.get("/{report_id}", response_model=AnalysisResponse)
async def get_report(
    report_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """获取单个分析报告（从数据库读取）"""
    try:
        rid = uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report_id format")

    repo = ReportRepository(session)
    report = await repo.get_by_id(rid)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    meta = report.metadata_json or {}
    return AnalysisResponse(
        report_id=str(report.id),
        query=report.query,
        status=report.status,
        final_report=report.full_report,
        patent_count=meta.get("patent_count", 0),
        trend_keywords=meta.get("trend_count", 0),
        iterations=meta.get("iteration_count", 0),
        patent_analysis=report.patent_summary,
        trend_analysis=report.trend_summary,
    )
