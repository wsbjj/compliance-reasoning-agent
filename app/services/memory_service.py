"""
记忆服务 (Memory Service) — 双通道架构
================================================================
通道 A: ollama  — 本地 Qdrant 向量库 + Ollama LLM/Embedder
通道 B: mem0_api — Mem0 Platform 云端 API (需要 MEM0_API_KEY)

切换方式：config.yaml  memory.memory_provider: "ollama" | "mem0_api"

记忆衰减策略：
  - 短期上下文: 长摘要 (≤ short_term_max_length 字符)
  - 远期上下文: 短摘要 (≤ long_term_max_length 字符，超过 30 天)
  - 超过 retention_days 的记忆自动淘汰
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from app.core.config import get_settings, get_yaml_config

logger = logging.getLogger(__name__)


# ============================================================
# 工厂函数：根据 config 构建 mem0 实例
# ============================================================

def _build_ollama_mem0(mem_cfg, collection: str = "compliance_agent_memory"):
    """
    构建本地通道 mem0 实例
    向量存储: Qdrant (localhost)
    LLM:      Ollama llama3.1
    Embedder: Ollama nomic-embed-text
    """
    from mem0 import Memory

    config = {
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "collection_name": collection,
                "host": mem_cfg.qdrant_host,
                "port": mem_cfg.qdrant_port,
                "embedding_model_dims": mem_cfg.ollama_embed_dims,
            },
        },
        "llm": {
            "provider": "ollama",
            "config": {
                "model": mem_cfg.ollama_llm_model,
                "temperature": 0,
                "max_tokens": 2000,
                "ollama_base_url": mem_cfg.ollama_base_url,
            },
        },
        "embedder": {
            "provider": "ollama",
            "config": {
                "model": mem_cfg.ollama_embed_model,
                "ollama_base_url": mem_cfg.ollama_base_url,
            },
        },
    }
    return Memory.from_config(config)


def _build_api_mem0(api_key: str):
    """
    构建云端通道 mem0 实例
    使用 Mem0 Platform API（托管服务，无需本地向量库）
    """
    from mem0 import MemoryClient

    client = MemoryClient(api_key=api_key)
    return _Mem0ApiAdapter(client)


# ============================================================
# API 通道适配器（统一 add / search / get_all 接口）
# ============================================================

class _Mem0ApiAdapter:
    """
    将 MemoryClient（云端 SDK）适配为与 Memory（本地 SDK）相同的接口，
    使上层 MemoryService 代码无感知差异。
    """

    def __init__(self, client):
        self._client = client

    def add(self, content: str, user_id: str = "default", metadata: dict | None = None):
        messages = [{"role": "user", "content": content}]
        return self._client.add(messages, user_id=user_id, metadata=metadata or {})

    def search(self, query: str, user_id: str = "default", limit: int = 10) -> list[dict]:
        results = self._client.search(query, user_id=user_id, limit=limit)
        # 统一格式：确保每条结果都有 "memory" 字段
        normalized = []
        for item in results:
            if isinstance(item, dict):
                if "memory" not in item and "text" in item:
                    item = {**item, "memory": item["text"]}
                normalized.append(item)
        return normalized

    def get_all(self, user_id: str = "default") -> list[dict]:
        return self._client.get_all(user_id=user_id)


# ============================================================
# 主服务
# ============================================================

class MemoryService:
    """
    双通道 Mem0 记忆管理服务

    - channel "ollama"   : 本地 Qdrant + Ollama，零成本，需本地服务运行
    - channel "mem0_api" : Mem0 Platform 云端，需 MEM0_API_KEY
    """

    def __init__(self):
        self.settings = get_settings()
        self.yaml_config = get_yaml_config()
        self._mem0 = None
        self._active_channel: str = ""

    # ------------------------------------------------------------------
    # 懒加载：首次访问时根据 memory_provider 初始化对应通道
    # ------------------------------------------------------------------
    @property
    def mem0(self):
        if self._mem0 is None:
            self._mem0 = self._init_mem0()
        return self._mem0

    def _init_mem0(self):
        mem_cfg = self.yaml_config.memory
        provider = mem_cfg.memory_provider

        # ── 通道 A: 本地 Ollama + Qdrant ──────────────────────────────
        if provider == "ollama":
            # 先检测 ollama Python 包是否已安装
            import importlib.util
            if importlib.util.find_spec("ollama") is None:
                self._log_ollama_unavailable(
                    "❌ 'ollama' Python 包未安装",
                    fix="请执行: uv add ollama",
                )
                self._active_channel = "fallback"
                return FallbackMemory()
            try:
                instance = _build_ollama_mem0(mem_cfg)
                self._active_channel = "ollama"
                logger.info(
                    "Mem0 [本地通道] 初始化成功 "
                    f"(Qdrant={mem_cfg.qdrant_host}:{mem_cfg.qdrant_port}, "
                    f"LLM={mem_cfg.ollama_llm_model}, "
                    f"Embedder={mem_cfg.ollama_embed_model})"
                )
                return instance
            except Exception as e:
                self._diagnose_ollama_error(e, mem_cfg)
                self._active_channel = "fallback"
                return FallbackMemory()


        # ── 通道 B: Mem0 Platform 云端 API ───────────────────────────
        elif provider == "mem0_api":
            api_key = self.settings.mem0_api_key
            if not api_key:
                logger.warning(
                    "Mem0 云端通道: MEM0_API_KEY 未配置，降级为 FallbackMemory。"
                    "请在 .env 中设置 MEM0_API_KEY=..."
                )
                self._active_channel = "fallback"
                return FallbackMemory()
            try:
                instance = _build_api_mem0(api_key)
                self._active_channel = "mem0_api"
                logger.info("Mem0 [云端通道] 初始化成功 (Mem0 Platform API)")
                return instance
            except Exception as e:
                logger.warning(f"Mem0 云端通道初始化失败: {e}，降级为 FallbackMemory")
                self._active_channel = "fallback"
                return FallbackMemory()

        else:
            logger.error(
                f"未知的 memory_provider: '{provider}'，"
                "请在 config.yaml 中设置 ollama 或 mem0_api"
            )
            self._active_channel = "fallback"
            return FallbackMemory()

    # ------------------------------------------------------------------
    # Ollama 通道诊断工具方法
    # ------------------------------------------------------------------
    @staticmethod
    def _log_ollama_unavailable(reason: str, fix: str) -> None:
        """输出结构化的 Ollama 不可用告警，并提示修复方法。"""
        logger.warning(
            "\n"
            "╔══════════════════════════════════════════════════════════╗\n"
            "║        ⚠️  Mem0 本地通道 (Ollama) 不可用                 ║\n"
            "╠══════════════════════════════════════════════════════════╣\n"
            f"║  原因: {reason:<52}║\n"
            f"║  修复: {fix:<52}║\n"
            "╠══════════════════════════════════════════════════════════╣\n"
            "║  系统已自动降级为内存字典 (FallbackMemory)               ║\n"
            "║  本次会话记忆在程序重启后将不会保留                      ║\n"
            "╚══════════════════════════════════════════════════════════╝"
        )

    def _diagnose_ollama_error(self, e: Exception, mem_cfg) -> None:
        """根据异常内容诊断 Ollama/Qdrant 失败的具体原因，输出可操作的修复建议。"""
        err_str = str(e).lower()

        # 1. Qdrant 连接被拒绝
        if "connection refused" in err_str and str(mem_cfg.qdrant_port) in err_str:
            self._log_ollama_unavailable(
                f"❌ Qdrant 服务未运行 ({mem_cfg.qdrant_host}:{mem_cfg.qdrant_port})",
                fix="请启动 Qdrant: docker run -p 6333:6333 qdrant/qdrant",
            )
        # 2. Ollama 服务未运行（API 连接失败）
        elif ("connection refused" in err_str or "connection error" in err_str) and "11434" in err_str:
            self._log_ollama_unavailable(
                "❌ Ollama 服务未运行 (localhost:11434)",
                fix="请启动 Ollama: ollama serve",
            )
        # 3. 模型未拉取（404 或 model not found）
        elif "404" in err_str or "model not found" in err_str or "pull" in err_str:
            self._log_ollama_unavailable(
                f"❌ 模型未下载: {mem_cfg.ollama_llm_model} / {mem_cfg.ollama_embed_model}",
                fix=f"请执行: ollama pull {mem_cfg.ollama_embed_model}",
            )
        # 4. 通用连接超时
        elif "timeout" in err_str or "timed out" in err_str:
            self._log_ollama_unavailable(
                "❌ 连接超时，Ollama/Qdrant 服务响应缓慢或不可达",
                fix="请检查 Ollama 和 Qdrant 服务是否正常运行",
            )
        # 5. 其他未知错误
        else:
            self._log_ollama_unavailable(
                f"❌ 初始化失败: {str(e)[:45]}",
                fix="请检查 Ollama 和 Qdrant 服务状态及配置",
            )

    @property
    def active_channel(self) -> str:
        """返回当前激活的通道名称（供日志/调试使用）"""
        _ = self.mem0  # 触发懒加载
        return self._active_channel

    # ------------------------------------------------------------------
    # 公开业务方法
    # ------------------------------------------------------------------
    async def add_memory(
        self, content: str, user_id: str = "default", metadata: dict | None = None
    ) -> Any:
        """
        添加记忆

        根据记忆衰减策略，内容超过 short_term_max_length 时截断。
        """
        try:
            max_len = self.yaml_config.memory.short_term_max_length
            if len(content) > max_len:
                content = content[:max_len] + "..."

            result = self.mem0.add(
                content,
                user_id=user_id,
                metadata=metadata or {"timestamp": datetime.now().isoformat()},
            )
            logger.info(
                f"[{self.active_channel}] Memory added for user '{user_id}' "
                f"({len(content)} chars)"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            return None

    async def search_memory(
        self, query: str, user_id: str = "default", limit: int = 10
    ) -> list[dict]:
        """搜索相关记忆（含记忆衰减过滤）"""
        try:
            results = self.mem0.search(query, user_id=user_id, limit=limit)

            processed = []
            max_short = self.yaml_config.memory.long_term_max_length
            retention_days = self.yaml_config.memory.retention_days
            cutoff = datetime.now() - timedelta(days=retention_days)

            for item in results:
                mem_data = item if isinstance(item, dict) else {"memory": str(item)}
                timestamp_str = (
                    mem_data.get("metadata", {}).get("timestamp", "")
                    if isinstance(mem_data.get("metadata"), dict)
                    else ""
                )

                # 过期记忆跳过
                if timestamp_str:
                    try:
                        ts = datetime.fromisoformat(timestamp_str)
                        if ts < cutoff:
                            continue
                    except (ValueError, TypeError):
                        pass

                # 远期记忆压缩为短摘要
                memory_text = mem_data.get("memory", "")
                if timestamp_str:
                    try:
                        ts = datetime.fromisoformat(timestamp_str)
                        days_age = (datetime.now() - ts).days
                        if days_age > 30 and len(memory_text) > max_short:
                            memory_text = memory_text[:max_short] + "..."
                    except (ValueError, TypeError):
                        pass

                processed.append(
                    {
                        "memory": memory_text,
                        "metadata": mem_data.get("metadata", {}),
                    }
                )

            return processed

        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            return []

    async def get_context_for_agent(
        self, query: str, user_id: str = "default"
    ) -> str:
        """获取格式化的记忆上下文字符串 — 供 Agent 节点使用"""
        memories = await self.search_memory(query, user_id)

        if not memories:
            return "无历史记忆。"

        context_parts = [f"### 历史记忆上下文 [{self.active_channel}]"]
        for i, mem in enumerate(memories, 1):
            context_parts.append(f"{i}. {mem['memory']}")

        return "\n".join(context_parts)

    def get_channel_info(self) -> dict:
        """返回当前通道信息（供健康检查 / 调试接口使用）"""
        mem_cfg = self.yaml_config.memory
        return {
            "active_channel": self.active_channel,
            "configured_provider": mem_cfg.memory_provider,
            "ollama": {
                "base_url": mem_cfg.ollama_base_url,
                "llm_model": mem_cfg.ollama_llm_model,
                "embed_model": mem_cfg.ollama_embed_model,
                "qdrant": f"{mem_cfg.qdrant_host}:{mem_cfg.qdrant_port}",
            },
            "mem0_api": {
                "api_key_configured": bool(self.settings.mem0_api_key),
            },
        }


# ============================================================
# 降级实现（内存字典）
# ============================================================

class FallbackMemory:
    """降级记忆实现 — 当任何通道均无法初始化时使用内存字典"""

    def __init__(self):
        self._store: dict[str, list[dict]] = {}

    def add(
        self, content: str, user_id: str = "default", metadata: dict | None = None
    ):
        if user_id not in self._store:
            self._store[user_id] = []
        self._store[user_id].append(
            {
                "memory": content,
                "metadata": metadata or {},
            }
        )
        return {"status": "ok", "channel": "fallback"}

    def search(
        self, query: str, user_id: str = "default", limit: int = 10
    ) -> list[dict]:
        entries = self._store.get(user_id, [])
        matched = [e for e in entries if query.lower() in e["memory"].lower()]
        if not matched:
            matched = entries
        return matched[-limit:]

    def get_all(self, user_id: str = "default") -> list[dict]:
        return self._store.get(user_id, [])
