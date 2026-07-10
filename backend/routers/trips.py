# -*- coding: utf-8 -*-
"""行程路由 — CRUD"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional

from dependencies import get_current_user, get_db
from services import trip_service

router = APIRouter(prefix="/api/trips", tags=["行程"])


# ===== Pydantic Schema =====

class TripCreate(BaseModel):
    """创建行程请求体"""
    city: str = Field(..., min_length=1, max_length=50, description="目的地城市")
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="行程日期 YYYY-MM-DD")
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="开始时间 HH:MM")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="结束时间 HH:MM")
    title: str = Field(..., min_length=1, max_length=200, description="行程标题")
    description: str = Field(default="", max_length=500, description="行程描述")
    image_url: str = Field(default="", description="图片（base64 或 URL）")
    budget: float = Field(default=0.00, ge=0, description="人均预算（元）")


class TripUpdate(BaseModel):
    """更新行程请求体（所有字段可选）"""
    city: Optional[str] = Field(None, min_length=1, max_length=50, description="目的地城市")
    date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="行程日期")
    start_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$", description="开始时间")
    end_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$", description="结束时间")
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="行程标题")
    description: Optional[str] = Field(None, max_length=500, description="行程描述")
    image_url: Optional[str] = Field(None, description="图片（base64 或 URL）")
    budget: Optional[float] = Field(None, ge=0, description="人均预算（元）")


def _ok(data=None, message: str = "success", code: int = 200) -> dict:
    """统一成功响应"""
    return {"code": code, "message": message, "data": data}


def _error(code: int, message: str) -> dict:
    """统一错误响应"""
    return {"code": code, "message": message, "data": None}


# ===== 路由端点 =====

@router.get("")
async def get_trips(
    city: str | None = Query(None, description="筛选城市"),
    date_from: str | None = Query(None, description="开始日期 YYYY-MM-DD"),
    date_to: str | None = Query(None, description="结束日期 YYYY-MM-DD"),
    user: dict = Depends(get_current_user),
    db = Depends(get_db),
):
    """
    获取当前用户的行程列表。

    支持按城市、日期范围筛选。返回 trips 数组、总预算、每日预算小计。
    """
    result = trip_service.get_trips(
        db=db,
        user_id=user["user_id"],
        city=city,
        date_from=date_from,
        date_to=date_to,
    )
    return _ok(result)


@router.post("")
async def create_trip(
    body: TripCreate,
    user: dict = Depends(get_current_user),
    db = Depends(get_db),
):
    """
    创建单条行程。

    会自动检测时段冲突，若冲突返回 409。
    """
    result = trip_service.create_trip(db=db, user_id=user["user_id"], data=body.model_dump())

    # 检查冲突标记
    if result.get("_conflict"):
        return _error(409, result.get("message", "该时段与已有行程冲突"))

    return _ok(result, "创建成功", 201)


@router.put("/{trip_id}")
async def update_trip(
    trip_id: int,
    body: TripUpdate,
    user: dict = Depends(get_current_user),
    db = Depends(get_db),
):
    """
    更新行程。

    仅更新传入的字段。会自动校验数据归属和时段冲突。
    """
    # 只传入非 None 的字段
    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not update_data:
        return _error(400, "没有需要更新的字段")

    try:
        result = trip_service.update_trip(db=db, trip_id=trip_id, user_id=user["user_id"], data=update_data)
    except ValueError:
        raise HTTPException(status_code=404, detail="行程不存在")
    except PermissionError:
        raise HTTPException(status_code=403, detail="无权操作该行程")

    if result.get("_conflict"):
        return _error(409, result.get("message", "该时段与已有行程冲突"))

    return _ok(result, "更新成功")


@router.delete("/{trip_id}")
async def delete_trip(
    trip_id: int,
    user: dict = Depends(get_current_user),
    db = Depends(get_db),
):
    """
    删除行程。

    会校验数据归属，不能删除他人的行程。
    """
    try:
        trip_service.delete_trip(db=db, trip_id=trip_id, user_id=user["user_id"])
    except ValueError:
        raise HTTPException(status_code=404, detail="行程不存在")
    except PermissionError:
        raise HTTPException(status_code=403, detail="无权操作该行程")

    return _ok(None, "删除成功")
