# -*- coding: utf-8 -*-
"""FastAPI 应用入口 — 路由注册、CORS、启动建表"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base

# ─── ORM 模型导入（确保建表前模型被 SQLAlchemy 发现）───
from models.user import User  # noqa: F401
from models.trip import Trip  # noqa: F401

app = FastAPI(
    title="LightJourney API",
    description="AI 驱动的旅行行程管理系统",
    version="1.0.0",
)

# ─── CORS 中间件 ─────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── 启动事件：自动建表 ──────────────────────────────────
@app.on_event("startup")
def startup():
    """应用启动时自动创建数据库表（已有表不重复创建）"""
    Base.metadata.create_all(bind=engine)


# ─── 路由注册 ────────────────────────────────────────────
# P1：鉴权路由（正式注册）
from routers import auth  # noqa: E402
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])

# P2：行程路由（队友取消注释即可启用）
# from routers import trips
# app.include_router(trips.router, prefix="/api/trips", tags=["trips"])

# P2：AI 路由（队友取消注释即可启用）
# from routers import ai
# app.include_router(ai.router, prefix="/api/ai", tags=["ai"])


# ─── 健康检查 ────────────────────────────────────────────
@app.get("/")
def health_check():
    """根路径健康检查"""
    return {"status": "ok", "version": "1.0.0"}
