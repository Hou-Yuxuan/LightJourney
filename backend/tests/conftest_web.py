# -*- coding: utf-8 -*-
"""P2 测试配置 — pytest fixtures"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base
from main import app
from dependencies import get_db, get_current_user


# ===== 内存数据库 =====

@pytest.fixture(scope="function")
def engine():
    """每个测试函数独立的 SQLite 内存数据库"""
    e = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=e)
    yield e
    Base.metadata.drop_all(bind=e)


@pytest.fixture(scope="function")
def db_session(engine):
    """数据库会话 fixture"""
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


# ===== 测试用户 =====

TEST_USER_ID = 1
TEST_USER_ID_2 = 2  # 另一个用户，用于测试数据隔离


# ===== FastAPI TestClient =====

@pytest.fixture(scope="function")
def client(db_session):
    """带依赖注入覆写的 TestClient"""
    def override_get_db():
        yield db_session

    def override_get_current_user():
        return TEST_USER_ID

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# ===== 辅助函数 =====

def create_test_trip(db_session, user_id=TEST_USER_ID, **overrides):
    """快速创建测试行程"""
    from datetime import date as date_type, time as time_type
    from models.trip import Trip

    def _parse_date(d):
        if isinstance(d, str):
            parts = d.split("-")
            return date_type(int(parts[0]), int(parts[1]), int(parts[2]))
        return d

    def _parse_time(t):
        if isinstance(t, str):
            parts = t.split(":")
            return time_type(int(parts[0]), int(parts[1]))
        return t

    defaults = {
        "user_id": user_id,
        "city": "成都",
        "date": date_type(2026, 8, 15),
        "start_time": time_type(9, 0),
        "end_time": time_type(12, 0),
        "title": "大熊猫繁育研究基地",
        "description": "上午参观熊猫基地",
        "budget": 55.00,
    }
    defaults.update(overrides)
    if "date" in defaults and isinstance(defaults["date"], str):
        defaults["date"] = _parse_date(defaults["date"])
    if "start_time" in defaults and isinstance(defaults["start_time"], str):
        defaults["start_time"] = _parse_time(defaults["start_time"])
    if "end_time" in defaults and isinstance(defaults["end_time"], str):
        defaults["end_time"] = _parse_time(defaults["end_time"])

    trip = Trip(**defaults)
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)
    return trip
