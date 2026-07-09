# -*- coding: utf-8 -*-
"""AI 路由 — Skill1 行程规划 / Skill2 文案生成"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from dependencies import get_current_user, get_db
from services import trip_service
from services.ai_service import call_deepseek_json, call_deepseek
from prompts.planning import SKILL1_SYSTEM_PROMPT, build_planning_user_message
from prompts.copywriting import SKILL2_SYSTEM_PROMPT, build_copywriting_user_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["AI"])


# ===== Pydantic Schema =====

class PlanRequest(BaseModel):
    """Skill1 行程规划请求"""
    city: str = Field(..., min_length=1, max_length=50, description="目的地城市")
    days: int = Field(..., ge=1, le=30, description="出行天数")
    preferences: list[str] = Field(default=[], description="偏好标签，如 美食、自然风光、人文历史")
    budget: float | None = Field(None, ge=0, description="总预算上限（可选）")


class CopywritingRequest(BaseModel):
    """Skill2 文案生成请求"""
    trip_id: int = Field(..., description="目标行程 ID")


# ===== 辅助函数 =====

def _ok(data=None, message: str = "success", code: int = 200) -> dict:
    """统一成功响应"""
    return {"code": code, "message": message, "data": data}


# ===== 路由端点 =====

@router.post("/plan")
async def plan_trip(
    body: PlanRequest,
    user_id: int = Depends(get_current_user),
    db = Depends(get_db),
):
    """
    Skill1 — AI 行程智能规划。

    流程：
    1. 查询用户已有行程的日期，传给 Prompt 供 AI 参考
    2. 调用 DeepSeek 生成行程 JSON 数组
    3. 逐条检测与已有行程的时段冲突
    4. 返回 plan（含冲突标记）和 conflicts 摘要

    注意：此接口只返回预览数据，不写入数据库。
    保存由前端逐条调用 POST /api/trips 完成。
    """
    # 1. 查询已有行程的日期
    existing = trip_service.get_trips(db=db, user_id=user_id, city=body.city)
    existing_dates = list(existing.get("daily_budgets", {}).keys()) if existing else []

    # 2. 构建 Prompt 并调用 DeepSeek
    user_message = build_planning_user_message(
        city=body.city,
        days=body.days,
        preferences=body.preferences,
        budget=body.budget,
        existing_dates=existing_dates,
    )

    try:
        plan_data = call_deepseek_json(SKILL1_SYSTEM_PROMPT, user_message, temperature=0.7)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # 确保是列表
    if not isinstance(plan_data, list):
        raise HTTPException(
            status_code=502,
            detail=f"AI 返回了非预期的数据格式（期望数组，实际为 {type(plan_data).__name__}），请重试"
        )

    # 3. 逐条检测冲突（只标记，不写入）
    conflicts = []
    enriched_plan = []
    for idx, item in enumerate(plan_data):
        enriched_item = {**item, "_index": idx, "_conflict": False, "_conflict_detail": None}
        try:
            item_conflicts = trip_service.check_conflict(
                db=db,
                user_id=user_id,
                trip_date=item.get("date", ""),
                start_time=item.get("start_time", ""),
                end_time=item.get("end_time", ""),
            )
        except (ValueError, KeyError):
            # 日期/时间格式异常时跳过冲突检测
            item_conflicts = []

        if item_conflicts:
            enriched_item["_conflict"] = True
            enriched_item["_conflict_detail"] = (
                f"时段与已有行程「{item_conflicts[0]['title']}」冲突"
                f"（{item_conflicts[0]['start_time']}-{item_conflicts[0]['end_time']}）"
            )
            conflicts.append({
                "plan_index": idx,
                "conflict_trip": item_conflicts[0],
                "overlap": enriched_item["_conflict_detail"],
            })

        enriched_plan.append(enriched_item)

    return _ok({
        "plan": enriched_plan,
        "conflicts": conflicts,
    })


@router.post("/copywriting")
async def generate_copywriting(
    body: CopywritingRequest,
    user_id: int = Depends(get_current_user),
    db = Depends(get_db),
):
    """
    Skill2 — AI 行程文案生成。

    流程：
    1. 查询目标行程，校验存在性和归属
    2. 查询当天同城市所有行程作为上下文
    3. 调用 DeepSeek 生成口语化朋友圈文案
    4. 返回文案 + 行程摘要

    文案只返回文本，不写入数据库。
    """
    # 1. 查询目标行程
    target_trip = trip_service.get_trip_by_id(db, trip_id=body.trip_id)
    if not target_trip:
        raise HTTPException(status_code=404, detail="行程不存在")
    if target_trip.user_id != user_id:
        raise HTTPException(status_code=403, detail="无权操作该行程")

    # 2. 查询当天同城所有行程
    trip_date = target_trip.date.isoformat() if hasattr(target_trip.date, 'isoformat') else str(target_trip.date)
    all_trips_result = trip_service.get_trips(
        db=db,
        user_id=user_id,
        city=target_trip.city,
        date_from=trip_date,
        date_to=trip_date,
    )
    same_day_trips = all_trips_result.get("trips", [])

    # 3. 构建 Prompt 并调用 DeepSeek
    target_dict = {
        "city": target_trip.city,
        "date": trip_date,
        "title": target_trip.title,
        "description": target_trip.description or "",
        "start_time": target_trip.start_time.isoformat() if hasattr(target_trip.start_time, 'isoformat') else str(target_trip.start_time),
        "end_time": target_trip.end_time.isoformat() if hasattr(target_trip.end_time, 'isoformat') else str(target_trip.end_time),
    }

    user_message = build_copywriting_user_message(
        target_trip=target_dict,
        same_day_trips=same_day_trips,
    )

    try:
        copywriting_text = call_deepseek(SKILL2_SYSTEM_PROMPT, user_message, temperature=0.8)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return _ok({
        "copywriting": copywriting_text,
        "trip_title": target_trip.title,
        "trip_date": trip_date,
    })
