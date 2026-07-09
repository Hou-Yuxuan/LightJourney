# -*- coding: utf-8 -*-
"""鉴权服务 — 密码哈希 / JWT 签发与验证"""
from datetime import datetime, timedelta

import bcrypt
import jwt
from jwt import PyJWTError

from config import settings


def hash_password(password: str) -> str:
    """使用 bcrypt 对明文密码进行哈希"""
    hashed = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    )
    return hashed.decode("utf-8")


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
    """验证明文密码与哈希值是否匹配"""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(user_id: int, username: str) -> str:
    """
    签发 JWT access token。
    payload 包含 user_id、username 及过期时间。
    """
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.utcnow() + timedelta(hours=settings.jwt_expire_hours),
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict | None:
    """
    验证并解析 JWT token。
    - 成功 → 返回 payload dict
    - 过期 / 无效 / 解析失败 → 返回 None，不抛异常
    """
    try:
        payload: dict = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except PyJWTError:
        return None
