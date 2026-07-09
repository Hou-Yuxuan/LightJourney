# -*- coding: utf-8 -*-
"""FastAPI 应用入口"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from models.user import User  # noqa: F401  确保模型被导入以便建表
from models.trip import Trip  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动时自动建表"""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="LightJourney API",
    description="AI驱动的旅行行程管理系统",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 路由注册 ---
from routers.auth import router as auth_router
from routers.trips import router as trips_router
from routers.ai import router as ai_router

app.include_router(auth_router)
app.include_router(trips_router)
app.include_router(ai_router)


@app.get("/api/health")
def health_check():
    """健康检查端点"""
    return {"status": "ok", "message": "LightJourney API is running"}
