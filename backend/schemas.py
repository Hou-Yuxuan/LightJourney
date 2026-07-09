# -*- coding: utf-8 -*-
"""统一响应格式与请求体模型（Pydantic v2）"""
from typing import Any

from pydantic import BaseModel, Field


# ─── 统一响应 ─────────────────────────────────────────────

class ResponseModel(BaseModel):
    """统一响应结构"""
    code: int
    message: str
    data: Any | None = None


def success_response(
    data: Any = None,
    message: str = "success",
    code: int = 200,
) -> dict:
    """构建成功响应"""
    return {"code": code, "message": message, "data": data}


def error_response(
    message: str,
    code: int,
    data: Any = None,
) -> dict:
    """构建错误响应"""
    return {"code": code, "message": message, "data": data}


# ─── 鉴权请求体 ───────────────────────────────────────────

class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str
