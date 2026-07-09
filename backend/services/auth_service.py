# -*- coding: utf-8 -*-
"""鉴权服务 — 密码哈希 / JWT 签发与验证"""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_HOURS


def hash_password(password: str) -> str:
    """TODO: P1 实现 — 密码 bcrypt 哈希"""
    raise NotImplementedError("P1 需要实现密码哈希逻辑")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """TODO: P1 实现 — 验证密码"""
    raise NotImplementedError("P1 需要实现密码验证逻辑")


def create_access_token(user_id: int) -> str:
    """TODO: P1 实现 — 签发 JWT access token"""
    raise NotImplementedError("P1 需要实现 JWT 签发逻辑")


def decode_access_token(token: str) -> int:
    """
    验证并解析 JWT access token，返回 user_id。

    由 P2 补实现（P1 未完成 BE-07 时临时承担）。

    Args:
        token: JWT token 字符串

    Returns:
        解析出的 user_id

    Raises:
        jwt.ExpiredSignatureError: token 已过期
        jwt.InvalidTokenError: token 无效
    """
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    user_id = payload.get("sub")
    if user_id is None:
        raise jwt.InvalidTokenError("Token 中缺少 user_id")
    return int(user_id)
