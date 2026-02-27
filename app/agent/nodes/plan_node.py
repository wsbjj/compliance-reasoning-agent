"""
Node_Plan — 任务规划节点 (Reflect 1)

接收用户查询，调用 LLM 分析需要哪些数据、制定执行计划。
结合历史记忆上下文进行智能规划。
"""
from __future__ import annotations

import logging

from app.agent.state import AgentState
from app.services.llm_service import LLMService
from app.services.memory_service import MemoryService

logger = logging.getLogger(__name__)


async def plan_node(state: AgentState) -> AgentState:
    """
    Reflect 1: 任务规划
    - 分析用户查询意图
    - 确定需要搜索的关键词
    - 制定数据采集和分析计划
    """
    query = state.get("query", "")
    extra_context = state.get("extra_context", "")
    user_id = state.get("user_id", "default")

    logger.info(f"[Node_Plan] Starting plan for query: '{query}'")

    # 1. 获取历史记忆上下文
    memory_service = MemoryService()
    memory_context = await memory_service.get_context_for_agent(query, user_id)

    # 2. 调用 LLM 制定计划
    llm_service = LLMService()
    plan_prompt = f"""你是一位合规分析智能体的规划模块。请根据以下信息制定数据采集和分析计划。

## 用户查询
{query}

## 额外上下文
{extra_context or "无"}

## 历史记忆
{memory_context}

请输出：
1. **分析目标**: 针对该产品/类目的合规分析重点
2. **搜索关键词**: 列出 3-5 个用于专利搜索和趋势分析的关键词（JSON 数组格式）
3. **数据采集计划**: 需要从哪些数据源获取什么类型的数据
4. **预期输出**: 最终报告应包含哪些模块

请在关键词部分使用如下格式: ["keyword1", "keyword2", "keyword3"]
"""

    plan = await llm_service.chat(
        [
            {
                "role": "system",
                "content": "你是合规推理智能体的规划模块，负责制定详细的数据采集和分析计划。",
            },
            {"role": "user", "content": plan_prompt},
        ]
    )

    # 3. 从计划中提取关键词
    search_keywords = _extract_keywords(plan, query)

    logger.info(
        f"[Node_Plan] Plan created. Keywords: {search_keywords}"
    )

    return {
        "plan": plan,
        "search_keywords": search_keywords,
        "memory_context": memory_context,
        "iteration_count": 0,
    }


def _extract_keywords(plan: str, fallback_query: str) -> list[str]:
    """从计划文本中提取关键词列表"""
    import json
    import re

    # 尝试从计划中提取 JSON 数组
    patterns = [
        r'\[(["\'].*?["\'](?:\s*,\s*["\'].*?["\'])*)\]',
    ]

    for pattern in patterns:
        match = re.search(pattern, plan)
        if match:
            try:
                keywords = json.loads(f"[{match.group(1)}]")
                if keywords:
                    return keywords
            except (json.JSONDecodeError, TypeError):
                continue

    # 如果提取失败，使用原始查询拆分
    return [fallback_query] + [
        w for w in fallback_query.split() if len(w) > 2
    ]
