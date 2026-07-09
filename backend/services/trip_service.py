# -*- coding: utf-8 -*-
"""行程服务 — CRUD / 冲突检测 / 预算统计"""
from datetime import time, date

from sqlalchemy.orm import Session

from models.trip import Trip


# ===== 工具函数 =====

def _parse_time(t: str | time) -> time:
    """将字符串 'HH:MM' 或 time 对象统一转为 time 对象"""
    if isinstance(t, time):
        return t
    parts = t.strip().split(":")
    return time(hour=int(parts[0]), minute=int(parts[1]))


def _parse_date(d: str | date) -> date:
    """将字符串 'YYYY-MM-DD' 或 date 对象统一转为 date 对象"""
    if isinstance(d, date):
        return d
    parts = d.strip().split("-")
    return date(year=int(parts[0]), month=int(parts[1]), day=int(parts[2]))


def _trip_to_dict(trip: Trip) -> dict:
    """将 Trip ORM 对象转为字典"""
    return {
        "id": trip.id,
        "city": trip.city,
        "date": trip.date.isoformat() if isinstance(trip.date, date) else str(trip.date),
        "start_time": trip.start_time.isoformat() if isinstance(trip.start_time, time) else str(trip.start_time),
        "end_time": trip.end_time.isoformat() if isinstance(trip.end_time, time) else str(trip.end_time),
        "title": trip.title,
        "description": trip.description or "",
        "budget": float(trip.budget) if trip.budget else 0.00,
        "created_at": trip.created_at.isoformat() if trip.created_at else None,
        "updated_at": trip.updated_at.isoformat() if trip.updated_at else None,
    }


def _parse_time(t: str | time) -> time:
    """将字符串 'HH:MM' 或 time 对象统一转为 time 对象"""
    if isinstance(t, time):
        return t
    parts = t.strip().split(":")
    return time(hour=int(parts[0]), minute=int(parts[1]))


# ===== 业务函数 =====

def check_conflict(
    db: Session,
    user_id: int,
    trip_date: str,
    start_time: str,
    end_time: str,
    exclude_trip_id: int | None = None,
) -> list[dict]:
    """
    时段冲突检测。

    算法：A和B重叠 ⟺ A.start < B.end AND A.end > B.start
    注意：12:00 结束 vs 12:00 开始 → 不冲突（等于不算重叠）

    Args:
        db: 数据库会话
        user_id: 当前用户 ID
        trip_date: 行程日期 YYYY-MM-DD
        start_time: 开始时间 HH:MM
        end_time: 结束时间 HH:MM
        exclude_trip_id: 编辑时排除自身行程 ID

    Returns:
        冲突的行程列表（每项为 dict，含 id, title, start_time, end_time）
    """
    new_start = _parse_time(start_time)
    new_end = _parse_time(end_time)

    query = db.query(Trip).filter(
        Trip.user_id == user_id,
        Trip.date == trip_date,
    )

    # 编辑时排除自身
    if exclude_trip_id is not None:
        query = query.filter(Trip.id != exclude_trip_id)

    existing_trips = query.all()

    conflicts = []
    for trip in existing_trips:
        # A和B重叠 ⟺ A.start < B.end AND A.end > B.start
        if new_start < trip.end_time and new_end > trip.start_time:
            conflicts.append({
                "id": trip.id,
                "title": trip.title,
                "start_time": trip.start_time.isoformat() if isinstance(trip.start_time, time) else str(trip.start_time),
                "end_time": trip.end_time.isoformat() if isinstance(trip.end_time, time) else str(trip.end_time),
            })

    return conflicts


def create_trip(db: Session, user_id: int, data: dict) -> dict:
    """
    创建单条行程。

    流程：
    1. 检测时段冲突
    2. 有冲突 → 返回包含 _conflict 标记的 dict
    3. 无冲突 → 写入数据库，返回行程 dict

    Args:
        db: 数据库会话
        user_id: 当前用户 ID
        data: 行程字段 dict

    Returns:
        行程 dict，若有冲突则含 _conflict 字段
    """
    conflicts = check_conflict(
        db=db,
        user_id=user_id,
        trip_date=data["date"],
        start_time=data["start_time"],
        end_time=data["end_time"],
    )

    if conflicts:
        return {
            "_conflict": True,
            "conflicts": conflicts,
            "message": "该时段与已有行程冲突",
        }

    trip = Trip(
        user_id=user_id,
        city=data["city"],
        date=_parse_date(data["date"]),
        start_time=_parse_time(data["start_time"]),
        end_time=_parse_time(data["end_time"]),
        title=data["title"],
        description=data.get("description", ""),
        budget=data.get("budget", 0.00),
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return _trip_to_dict(trip)


def get_trips(
    db: Session,
    user_id: int,
    city: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    """
    查询行程列表（含筛选 + 预算统计）。

    筛选条件可独立或组合使用。

    Args:
        db: 数据库会话
        user_id: 当前用户 ID
        city: 城市筛选（可选）
        date_from: 开始日期 YYYY-MM-DD（可选）
        date_to: 结束日期 YYYY-MM-DD（可选）

    Returns:
        {
            "trips": [...],
            "total_budget": float,
            "daily_budgets": {"YYYY-MM-DD": float, ...}
        }
    """
    query = db.query(Trip).filter(Trip.user_id == user_id)

    if city:
        query = query.filter(Trip.city == city)
    if date_from:
        query = query.filter(Trip.date >= date_from)
    if date_to:
        query = query.filter(Trip.date <= date_to)

    trips = query.order_by(Trip.date.asc(), Trip.start_time.asc()).all()

    trip_list = [_trip_to_dict(t) for t in trips]

    # 预算统计
    total_budget = sum(t.budget for t in trips) if trips else 0.00

    daily_budgets = {}
    for t in trips:
        date_key = t.date.isoformat() if isinstance(t.date, date) else str(t.date)
        daily_budgets[date_key] = daily_budgets.get(date_key, 0.0) + float(t.budget or 0)

    return {
        "trips": trip_list,
        "total_budget": float(total_budget),
        "daily_budgets": daily_budgets,
    }


def get_trip_by_id(db: Session, trip_id: int) -> Trip | None:
    """按 ID 查询单条行程"""
    return db.query(Trip).filter(Trip.id == trip_id).first()


def update_trip(db: Session, trip_id: int, user_id: int, data: dict) -> dict:
    """
    更新行程。

    流程：
    1. 查询行程，校验存在性
    2. 校验数据归属（user_id 匹配）
    3. 如果时间变更，检测冲突（排除自身）
    4. 更新字段并提交

    Args:
        db: 数据库会话
        trip_id: 行程 ID
        user_id: 当前用户 ID
        data: 要更新的字段 dict（所有字段可选，传入即更新）

    Returns:
        更新后的行程 dict

    Raises:
        ValueError: 行程不存在
        PermissionError: 无权操作他人行程
    """
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        raise ValueError("行程不存在")

    if trip.user_id != user_id:
        raise PermissionError("无权操作该行程")

    # 如果修改了日期或时间，需要重新检测冲突
    new_date = data.get("date", trip.date.isoformat() if isinstance(trip.date, date) else str(trip.date))
    new_start = data.get("start_time",
                          trip.start_time.isoformat() if isinstance(trip.start_time, time) else str(trip.start_time))
    new_end = data.get("end_time",
                        trip.end_time.isoformat() if isinstance(trip.end_time, time) else str(trip.end_time))

    has_time_change = (
        new_date != (trip.date.isoformat() if isinstance(trip.date, date) else str(trip.date))
        or new_start != (trip.start_time.isoformat() if isinstance(trip.start_time, time) else str(trip.start_time))
        or new_end != (trip.end_time.isoformat() if isinstance(trip.end_time, time) else str(trip.end_time))
    )

    if has_time_change:
        conflicts = check_conflict(
            db=db,
            user_id=user_id,
            trip_date=new_date,
            start_time=new_start,
            end_time=new_end,
            exclude_trip_id=trip_id,
        )
        if conflicts:
            return {
                "_conflict": True,
                "conflicts": conflicts,
                "message": "该时段与已有行程冲突",
            }

    # 逐字段更新
    updatable_fields = ["city", "date", "start_time", "end_time", "title", "description", "budget"]
    for field in updatable_fields:
        if field in data:
            value = data[field]
            if field == "date":
                value = _parse_date(value)
            elif field in ("start_time", "end_time"):
                value = _parse_time(value)
            setattr(trip, field, value)

    db.commit()
    db.refresh(trip)
    return _trip_to_dict(trip)


def delete_trip(db: Session, trip_id: int, user_id: int) -> None:
    """
    删除行程。

    Args:
        db: 数据库会话
        trip_id: 行程 ID
        user_id: 当前用户 ID

    Raises:
        ValueError: 行程不存在
        PermissionError: 无权操作他人行程
    """
    trip = get_trip_by_id(db, trip_id)
    if not trip:
        raise ValueError("行程不存在")

    if trip.user_id != user_id:
        raise PermissionError("无权操作该行程")

    db.delete(trip)
    db.commit()
