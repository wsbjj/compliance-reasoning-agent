"""
LLM 服务封装 (LLM Service)
业务逻辑层 — OpenAI 格式调用，支持硅基流动等平台
"""
from __future__ import annotations

import logging
from typing import Any

from langchain_openai import ChatOpenAI

from app.core.config import get_settings, get_yaml_config

logger = logging.getLogger(__name__)


class LLMService:
    """LLM 调用封装 — 兼容 OpenAI 格式的平台"""

    def __init__(self):
        self.settings = get_settings()
        self.yaml_config = get_yaml_config()
        self._llm: ChatOpenAI | None = None

    @property
    def llm(self) -> ChatOpenAI:
        """懒加载 LLM 实例"""
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self.settings.llm_model or "gpt-4o-mini",
                api_key=self.settings.llm_api_key or "sk-placeholder",
                base_url=self.settings.llm_api_base or None,
                temperature=self.yaml_config.llm.temperature,
                max_tokens=self.yaml_config.llm.max_tokens,
            )
        return self._llm

    async def chat(self, messages: list[dict[str, str]]) -> str:
        """
        通用对话调用
        messages: [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
        """
        try:
            from langchain_core.messages import HumanMessage, SystemMessage

            lc_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    lc_messages.append(SystemMessage(content=msg["content"]))
                else:
                    lc_messages.append(HumanMessage(content=msg["content"]))

            response = await self.llm.ainvoke(lc_messages)
            return response.content

        except Exception as e:
            logger.error(f"LLM chat failed: {e}")
            return f"[LLM Error] {str(e)}"

    async def analyze_patents(
        self, patents_data: list[dict], query: str
    ) -> dict[str, Any]:
        """
        分析专利数据 — 提取核心技术点 + 竞品分类
        返回: {"tech_analysis": str, "categories": dict}
        """
        patents_text = "\n".join(
            [
                f"- Title: {p.get('title', '')}\n  Assignee: {p.get('assignee', '')}\n  Abstract: {p.get('abstract', '')[:200]}"
                for p in patents_data[:30]
            ]
        )

        prompt = f"""你是一位专利分析专家。请分析以下与 "{query}" 相关的专利数据：

{patents_text}

请完成以下任务：
1. 提取每篇专利的核心技术点（关键技术方向）
2. 将这些专利按竞品公司和技术方向进行分类
3. 识别主要的专利壁垒区域
4. 给出专利布局分析摘要

请以 JSON 格式返回，包含以下字段：
- tech_points: 列表，每个元素包含 patent_title, assignee, key_technologies (列表)
- categories: 字典，key 是类别名, value 是对应的专利标题列表
- barriers: 列表，主要的专利壁垒描述
- summary: 总体分析摘要
"""
        result = await self.chat(
            [
                {"role": "system", "content": "你是专利分析专家，总是以 JSON 格式回复。"},
                {"role": "user", "content": prompt},
            ]
        )

        return {"tech_analysis": result, "query": query}

    async def generate_report(
        self,
        patent_analysis: str,
        trend_data: str,
        extra_context: str = "",
    ) -> str:
        """
        生成窗口期预警简报 — Markdown 格式
        """
        prompt = f"""你是一位市场策略分析师。基于以下数据，生成一份《窗口期预警简报》。

## 专利壁垒分析
{patent_analysis}

## 市场增长率数据
{trend_data}

## 外部补充信息
{extra_context or "无额外信息"}

请输出一份 Markdown 格式的深度分析报告，包含：

1. **执行摘要** — 一句话总结结论
2. **专利格局分析** — 当前专利壁垒情况，哪些公司占据主导
3. **市场趋势解读** — 增长率分析，热词趋势
4. **窗口期判断** — "为什么是现在" 的逻辑论证
5. **风险评估** — 进入该赛道的主要风险
6. **行动建议** — 具体可执行的下一步建议

报告需要专业、数据驱动、有说服力。
"""
        return await self.chat(
            [
                {
                    "role": "system",
                    "content": "你是资深市场策略分析师，擅长撰写专业的市场分析报告，以 Markdown 格式输出。",
                },
                {"role": "user", "content": prompt},
            ]
        )

    async def review_report(self, report: str) -> dict[str, Any]:
        """
        审核报告质量 — Node_Review 使用
        返回: {"passed": bool, "feedback": str}
        """
        prompt = f"""请审核以下市场分析报告的质量：

{report}

审核标准：
1. 是否包含执行摘要？
2. 是否有专利分析数据支撑？
3. 是否包含增长率/趋势图表引用？
4. "为什么是现在" 的论证是否有说服力？
5. 是否有具体可执行的行动建议？
6. Markdown 格式是否正确？

请以 JSON 格式返回：
- passed: true/false
- score: 1-10 整体质量评分
- feedback: 改进建议（如果 passed=false）
"""
        result = await self.chat(
            [
                {"role": "system", "content": "你是报告质量审核专家，始终以 JSON 格式回复。"},
                {"role": "user", "content": prompt},
            ]
        )

        # 简单解析：如果包含 "passed": true 则通过
        passed = '"passed": true' in result.lower() or '"passed":true' in result.lower()
        return {"passed": passed, "feedback": result}

    async def summarize_for_memory(self, context: str) -> str:
        """为 Mem0 记忆存储生成摘要"""
        prompt = f"""请将以下对话/分析上下文压缩为简洁的摘要（不超过 200 字）：

{context}

摘要需保留：关键查询词、主要结论、重要数据点。
"""
        return await self.chat(
            [
                {"role": "system", "content": "你是信息压缩专家，请输出简短摘要。"},
                {"role": "user", "content": prompt},
            ]
        )
