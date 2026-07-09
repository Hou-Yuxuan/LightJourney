# -*- coding: utf-8 -*-
"""Trip ORM 模型"""
from sqlalchemy import Column, Integer, String, Date, Time, Text, Numeric, DateTime, ForeignKey, Index, func

from database import Base


class Trip(Base):
    """行程表"""

    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    city = Column(String(50), nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    budget = Column(Numeric(10, 2), default=0.00)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_trips_user_date", "user_id", "date"),
    )
