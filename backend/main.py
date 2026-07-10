# -*- coding: utf-8 -*-
"""FastAPI 应用入口 — 路由注册、CORS、启动建表"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import engine, Base
from models.user import User  # noqa: F401
from models.trip import Trip  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动时自动建表"""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="LightJourney API",
    description="AI 驱动的旅行行程管理系统",
    version="1.0.0",
    lifespan=lifespan,
)

# ─── CORS 中间件 ─────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── 路由注册 ────────────────────────────────────────────
from routers.auth import router as auth_router
from routers.trips import router as trips_router
from routers.ai import router as ai_router
from routers.upload import router as upload_router

app.include_router(auth_router, prefix="/api/auth")
app.include_router(trips_router)
app.include_router(ai_router)
app.include_router(upload_router)

# 静态文件：上传的图片
import os
uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


# ─── 健康检查 ────────────────────────────────────────────
@app.get("/")
def health_check():
    return {"status": "ok", "version": "1.0.0"}
