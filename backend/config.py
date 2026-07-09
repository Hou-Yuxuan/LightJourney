# -*- coding: utf-8 -*-
"""应用配置 — 基于 pydantic-settings 的环境变量管理"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置单例，自动读取 .env 文件与环境变量"""

    # ── 数据库 ──
    database_url: str = "sqlite:///./lightjourney.db"

    # ── JWT 鉴权 ──
    jwt_secret_key: str = "lightjourney-dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    # ── DeepSeek API（P2 使用）──
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # 环境变量名全大写，与字段名自动映射
        extra="ignore",
    )


# 全局单例
settings = Settings()
