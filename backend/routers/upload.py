# -*- coding: utf-8 -*-
"""图片上传路由"""
import os
import uuid

from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.staticfiles import StaticFiles

from dependencies import get_current_user

router = APIRouter(prefix="/api/upload", tags=["上传"])

# 上传目录（与 main.py 中 StaticFiles 挂载保持一致）
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 允许的图片类型
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}


@router.post("")
async def upload_image(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user),
):
    """上传图片，返回可访问的 URL"""
    if file.content_type not in ALLOWED_TYPES:
        return {"code": 400, "message": "仅支持 JPEG/PNG/GIF/WebP 格式", "data": None}

    # 限制 10MB
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        return {"code": 400, "message": "图片大小不能超过 10MB", "data": None}

    # 生成唯一文件名
    ext = os.path.splitext(file.filename or "image.jpg")[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(content)

    url = f"/uploads/{filename}"
    return {"code": 200, "message": "上传成功", "data": {"url": url}}
