# -*- coding: utf-8 -*-
"""数据库连接 — SQLAlchemy 2.0 引擎、会话工厂、依赖注入"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config import settings

# SQLite 引擎（check_same_thread=False 允许跨线程访问）
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    echo=False,
)

# 会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# ORM 基类
Base = declarative_base()


def get_db() -> Generator:
    """
    FastAPI 依赖注入：获取数据库会话。
    请求结束时自动关闭会话，防止连接泄漏。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
