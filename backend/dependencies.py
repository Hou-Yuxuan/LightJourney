# -*- coding: utf-8 -*-
"""FastAPI 依赖注入 — JWT 鉴权 / 数据库会话"""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from config import JWT_SECRET, JWT_ALGORITHM
from database import SessionLocal

security = HTTPBearer()


def get_db():
    """
    数据库会话生成器。

    每个请求获取一个独立的数据库会话，请求结束时自动关闭。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    """
    从请求头的 Bearer token 解析 JWT，返回当前登录用户的 user_id。

    用于所有需要鉴权的接口，注入方式：
        user_id: int = Depends(get_current_user)
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="无效的认证令牌")
        return int(user_id)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
