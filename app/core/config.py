"""
核心配置模块 (Core Configuration)
- Settings: 从 .env 加载敏感配置 (API Keys, DB URLs)
- YamlConfig: 从 config.yaml 加载业务配置 (数据源选择, Agent 参数)
- 工厂模式: 根据 config.yaml 中的 provider 选择对应实现
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# ============================================================
# 1. 环境变量配置 (.env)
# ============================================================
class Settings(BaseSettings):
    """从 .env 文件加载的环境变量配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- 应用 ---
    app_name: str = "compliance-reasoning-agent"
    app_env: str = "development"
    debug: bool = True

    # --- LLM ---
    llm_api_key: str = ""
    llm_api_base: str = ""
    llm_model: str = ""

    # --- SerpApi ---
    serpapi_api_key: str = ""

    # --- USPTO ---
    uspto_api_key: str = ""

    # --- 亚马逊关键词 ---
    rainforest_api_key: str = ""
    keepa_api_key: str = ""

    # --- PostgreSQL ---
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/compliance_agent"

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- Mem0 ---
    mem0_api_key: str = ""


# ============================================================
# 2. 业务配置 (config.yaml)
# ============================================================
class DataSourcesConfig:
    """数据源配置"""

    def __init__(self, data: dict):
        self.patent_provider: str = data.get("patent_provider", "serpapi")
        self.trend_provider: str = data.get("trend_provider", "pytrends")


class LLMConfig:
    """LLM 业务参数"""

    def __init__(self, data: dict):
        self.provider: str = data.get("provider", "openai_compatible")
        self.temperature: float = data.get("temperature", 0.3)
        self.max_tokens: int = data.get("max_tokens", 4096)


class AgentConfig:
    """Agent 行为参数"""

    def __init__(self, data: dict):
        self.max_review_iterations: int = data.get("max_review_iterations", 3)
        self.patent_search_limit: int = data.get("patent_search_limit", 50)
        self.trend_timeframe_months: int = data.get("trend_timeframe_months", 36)


class MemoryConfig:
    """记忆双通道配置"""

    def __init__(self, data: dict):
        # 通用
        self.memory_provider: str = data.get("memory_provider", "ollama")
        self.short_term_max_length: int = data.get("short_term_max_length", 500)
        self.long_term_max_length: int = data.get("long_term_max_length", 100)
        self.retention_days: int = data.get("retention_days", 90)

        # 本地通道（ollama + Qdrant）
        self.qdrant_host: str = data.get("qdrant_host", "localhost")
        self.qdrant_port: int = data.get("qdrant_port", 6333)
        self.ollama_base_url: str = data.get("ollama_base_url", "http://localhost:11434")
        self.ollama_llm_model: str = data.get("ollama_llm_model", "llama3.1:latest")
        self.ollama_embed_model: str = data.get("ollama_embed_model", "nomic-embed-text:latest")
        self.ollama_embed_dims: int = data.get("ollama_embed_dims", 768)

        # 云端通道（Mem0 Platform API）
        self.mem0_api_user_prefix: str = data.get("mem0_api_user_prefix", "")


class YamlConfig:
    """从 config.yaml 加载的业务配置"""

    def __init__(self, config_path: str | Path | None = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config.yaml"
        config_path = Path(config_path)

        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                raw: dict = yaml.safe_load(f) or {}
        else:
            raw = {}

        self.data_sources = DataSourcesConfig(raw.get("data_sources", {}))
        self.llm = LLMConfig(raw.get("llm", {}))
        self.agent = AgentConfig(raw.get("agent", {}))
        self.memory = MemoryConfig(raw.get("memory", {}))


# ============================================================
# 3. 全局单例获取
# ============================================================
@lru_cache()
def get_settings() -> Settings:
    """获取环境变量配置单例"""
    return Settings()


@lru_cache()
def get_yaml_config() -> YamlConfig:
    """获取业务配置单例"""
    return YamlConfig()
