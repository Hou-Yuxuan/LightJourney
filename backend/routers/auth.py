# -*- coding: utf-8 -*-
"""鉴权路由 — 注册 / 登录"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas import RegisterRequest, LoginRequest, success_response, error_response
from services.auth_service import hash_password, verify_password, create_access_token

router = APIRouter()


@router.post("/register")
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    用户注册。
    - 用户名已存在 → 409
    - 密码 bcrypt 哈希后存储
    """
    # 检查用户名是否已注册
    existing = db.query(User).filter(User.username == request.username).first()
    if existing:
        return error_response("用户名已被注册", 409)

    try:
        user = User(
            username=request.username,
            password_hash=hash_password(request.password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return success_response(
            data={"id": user.id, "username": user.username},
            message="注册成功",
            code=201,
        )
    except Exception as e:
        db.rollback()
        return error_response(str(e), 500)


@router.post("/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    用户登录。
    - 用户名不存在或密码错误 → 统一返回 401（防用户名枚举）
    - 成功 → 返回 JWT access token
    """
    user = db.query(User).filter(User.username == request.username).first()

    # 用户不存在或密码错误，统一错误信息
    if user is None or not verify_password(request.password, user.password_hash):
        return error_response("用户名或密码错误", 401)

    token = create_access_token(user.id, user.username)
    return success_response(
        data={
            "access_token": token,
            "token_type": "bearer",
            "username": user.username,
        },
        message="登录成功",
    )
