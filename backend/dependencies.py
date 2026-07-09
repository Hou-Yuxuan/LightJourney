# -*- coding: utf-8 -*-
"""JWT 鉴权依赖注入"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from services.auth_service import decode_access_token

# HTTP Bearer 鉴权方案
security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> dict:
    """
    从请求头 Authorization: Bearer <token> 中解析 JWT，
    返回 payload dict = {"user_id": int, "username": str}。
    token 无效或过期时抛出 401。
    """
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token无效或已过期",
        )
    return payload
