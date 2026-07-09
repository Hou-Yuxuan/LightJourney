# -*- coding: utf-8 -*-
"""测试 trip_service — 冲突检测 / CRUD / 预算统计"""
import pytest

pytest_plugins = ["tests.conftest_service"]

from services.trip_service import (
    check_conflict,
    create_trip,
    get_trips,
    update_trip,
    delete_trip,
)
from tests.conftest_service import create_test_trip, TEST_USER_ID, TEST_USER_ID_2


class TestCheckConflict:
    """时段冲突检测"""

    def test_no_conflict_when_adjacent(self, db_session):
        """12:00 结束 vs 12:00 开始 → 不冲突"""
        create_test_trip(db_session, start_time="09:00", end_time="12:00")

        conflicts = check_conflict(
            db_session, TEST_USER_ID,
            trip_date="2026-08-15",
            start_time="12:00", end_time="14:00",
        )
        assert conflicts == []

    def test_no_conflict_when_separated(self, db_session):
        """完全不重叠的时段"""
        create_test_trip(db_session, start_time="09:00", end_time="10:00")

        conflicts = check_conflict(
            db_session, TEST_USER_ID,
            trip_date="2026-08-15",
            start_time="14:00", end_time="16:00",
        )
        assert conflicts == []

    def test_conflict_when_overlapping(self, db_session):
        """09:00-12:00 vs 10:00-14:00 → 冲突"""
        create_test_trip(db_session, start_time="09:00", end_time="12:00")

        conflicts = check_conflict(
            db_session, TEST_USER_ID,
            trip_date="2026-08-15",
            start_time="10:00", end_time="14:00",
        )
        assert len(conflicts) == 1
        assert conflicts[0]["title"] == "大熊猫繁育研究基地"

    def test_conflict_when_contained(self, db_session):
        """09:00-12:00 vs 09:30-11:00 → 冲突（被包含）"""
        create_test_trip(db_session, start_time="09:00", end_time="12:00")

        conflicts = check_conflict(
            db_session, TEST_USER_ID,
            trip_date="2026-08-15",
            start_time="09:30", end_time="11:00",
        )
        assert len(conflicts) == 1

    def test_no_conflict_different_date(self, db_session):
        """不同日期不检测冲突"""
        create_test_trip(db_session, date="2026-08-15", start_time="09:00", end_time="12:00")

        conflicts = check_conflict(
            db_session, TEST_USER_ID,
            trip_date="2026-08-16",
            start_time="09:00", end_time="12:00",
        )
        assert conflicts == []

    def test_no_conflict_different_user(self, db_session):
        """不同用户不检测冲突（数据隔离）"""
        create_test_trip(db_session, user_id=TEST_USER_ID, start_time="09:00", end_time="12:00")

        conflicts = check_conflict(
            db_session, TEST_USER_ID_2,
            trip_date="2026-08-15",
            start_time="09:00", end_time="12:00",
        )
        assert conflicts == []

    def test_exclude_trip_id(self, db_session):
        """编辑时排除自身 ID"""
        trip = create_test_trip(db_session, start_time="09:00", end_time="12:00")

        conflicts = check_conflict(
            db_session, TEST_USER_ID,
            trip_date="2026-08-15",
            start_time="10:00", end_time="14:00",
            exclude_trip_id=trip.id,
        )
        assert conflicts == []

    def test_multiple_conflicts(self, db_session):
        """返回所有冲突的行程"""
        create_test_trip(db_session, start_time="09:00", end_time="10:30", title="行程A")
        create_test_trip(db_session, start_time="10:00", end_time="11:00", title="行程B")

        conflicts = check_conflict(
            db_session, TEST_USER_ID,
            trip_date="2026-08-15",
            start_time="09:30", end_time="11:00",
        )
        assert len(conflicts) == 2


class TestCreateTrip:
    """创建行程"""

    def test_create_success(self, db_session):
        result = create_trip(db_session, TEST_USER_ID, {
            "city": "杭州",
            "date": "2026-09-01",
            "start_time": "09:00",
            "end_time": "12:00",
            "title": "西湖",
            "description": "环湖漫步",
            "budget": 0,
        })
        assert "_conflict" not in result
        assert result["city"] == "杭州"
        assert result["title"] == "西湖"
        assert result["id"] is not None

    def test_create_with_conflict(self, db_session):
        create_test_trip(db_session, start_time="09:00", end_time="12:00")

        result = create_trip(db_session, TEST_USER_ID, {
            "city": "成都",
            "date": "2026-08-15",
            "start_time": "10:00",
            "end_time": "14:00",
            "title": "武侯祠",
            "description": "",
            "budget": 30,
        })
        assert result["_conflict"] is True
        assert "冲突" in result["message"]

    def test_create_adjacent_no_conflict(self, db_session):
        """首尾相接不冲突"""
        create_test_trip(db_session, start_time="09:00", end_time="12:00")

        result = create_trip(db_session, TEST_USER_ID, {
            "city": "成都",
            "date": "2026-08-15",
            "start_time": "12:00",
            "end_time": "14:00",
            "title": "午餐",
            "description": "",
            "budget": 50,
        })
        assert "_conflict" not in result


class TestGetTrips:
    """行程列表查询"""

    def test_empty_list(self, db_session):
        result = get_trips(db_session, TEST_USER_ID)
        assert result["trips"] == []
        assert result["total_budget"] == 0.0
        assert result["daily_budgets"] == {}

    def test_list_all(self, db_session):
        create_test_trip(db_session, title="行程A")
        create_test_trip(db_session, title="行程B", start_time="14:00", end_time="16:00")

        result = get_trips(db_session, TEST_USER_ID)
        assert len(result["trips"]) == 2

    def test_filter_by_city(self, db_session):
        create_test_trip(db_session, city="成都")
        create_test_trip(db_session, city="杭州", date="2026-08-16")

        result = get_trips(db_session, TEST_USER_ID, city="杭州")
        assert len(result["trips"]) == 1
        assert result["trips"][0]["city"] == "杭州"

    def test_filter_by_date_range(self, db_session):
        create_test_trip(db_session, date="2026-08-15", title="Day1")
        create_test_trip(db_session, date="2026-08-16", title="Day2")
        create_test_trip(db_session, date="2026-08-17", title="Day3")

        result = get_trips(db_session, TEST_USER_ID, date_from="2026-08-15", date_to="2026-08-16")
        assert len(result["trips"]) == 2

    def test_data_isolation(self, db_session):
        """用户A看不到用户B的行程"""
        create_test_trip(db_session, user_id=TEST_USER_ID, title="A的行程")
        create_test_trip(db_session, user_id=TEST_USER_ID_2, title="B的行程")

        result = get_trips(db_session, TEST_USER_ID)
        assert len(result["trips"]) == 1
        assert result["trips"][0]["title"] == "A的行程"

    def test_order_by_date_and_time(self, db_session):
        create_test_trip(db_session, date="2026-08-16", start_time="09:00", title="Day2-Morning")
        create_test_trip(db_session, date="2026-08-15", start_time="14:00", title="Day1-Noon")
        create_test_trip(db_session, date="2026-08-15", start_time="09:00", title="Day1-Morning")

        result = get_trips(db_session, TEST_USER_ID)
        titles = [t["title"] for t in result["trips"]]
        assert titles == ["Day1-Morning", "Day1-Noon", "Day2-Morning"]


class TestBudgetStats:
    """预算统计"""

    def test_total_budget(self, db_session):
        create_test_trip(db_session, budget=100, title="A")
        create_test_trip(db_session, budget=50, title="B", start_time="14:00", end_time="16:00")

        result = get_trips(db_session, TEST_USER_ID)
        assert result["total_budget"] == 150.0

    def test_daily_budgets(self, db_session):
        create_test_trip(db_session, date="2026-08-15", budget=100)
        create_test_trip(db_session, date="2026-08-15", budget=50, start_time="14:00", end_time="16:00")
        create_test_trip(db_session, date="2026-08-16", budget=200)

        result = get_trips(db_session, TEST_USER_ID)
        assert result["daily_budgets"]["2026-08-15"] == 150.0
        assert result["daily_budgets"]["2026-08-16"] == 200.0

    def test_filtered_stats_update(self, db_session):
        """筛选后预算统计随筛选结果变化"""
        create_test_trip(db_session, city="成都", budget=100)
        create_test_trip(db_session, city="杭州", budget=200, date="2026-08-16")

        result = get_trips(db_session, TEST_USER_ID, city="成都")
        assert result["total_budget"] == 100.0


class TestUpdateTrip:
    """更新行程"""

    def test_update_success(self, db_session):
        trip = create_test_trip(db_session)

        result = update_trip(db_session, trip.id, TEST_USER_ID, {"title": "新标题", "budget": 99.0})
        assert result["title"] == "新标题"
        assert result["budget"] == 99.0

    def test_update_with_conflict(self, db_session):
        create_test_trip(db_session, start_time="09:00", end_time="12:00", title="已有行程")
        trip = create_test_trip(db_session, start_time="14:00", end_time="16:00", title="待编辑")

        result = update_trip(db_session, trip.id, TEST_USER_ID,
                             {"start_time": "10:00", "end_time": "14:00"})
        assert result["_conflict"] is True

    def test_update_partial_fields(self, db_session):
        trip = create_test_trip(db_session)

        result = update_trip(db_session, trip.id, TEST_USER_ID, {"description": "新描述"})
        assert result["description"] == "新描述"
        assert result["title"] == "大熊猫繁育研究基地"  # 未修改的字段不变

    def test_update_trip_not_found(self, db_session):
        with pytest.raises(ValueError, match="行程不存在"):
            update_trip(db_session, 9999, TEST_USER_ID, {"title": "x"})

    def test_update_permission_denied(self, db_session):
        trip = create_test_trip(db_session, user_id=TEST_USER_ID)

        with pytest.raises(PermissionError, match="无权操作"):
            update_trip(db_session, trip.id, TEST_USER_ID_2, {"title": "x"})


class TestDeleteTrip:
    """删除行程"""

    def test_delete_success(self, db_session):
        trip = create_test_trip(db_session)
        delete_trip(db_session, trip.id, TEST_USER_ID)

        result = get_trips(db_session, TEST_USER_ID)
        assert result["trips"] == []

    def test_delete_trip_not_found(self, db_session):
        with pytest.raises(ValueError, match="行程不存在"):
            delete_trip(db_session, 9999, TEST_USER_ID)

    def test_delete_permission_denied(self, db_session):
        trip = create_test_trip(db_session, user_id=TEST_USER_ID)

        with pytest.raises(PermissionError, match="无权操作"):
            delete_trip(db_session, trip.id, TEST_USER_ID_2)

    def test_delete_only_target_trip(self, db_session):
        trip_a = create_test_trip(db_session, title="A")
        trip_b = create_test_trip(db_session, title="B", start_time="14:00", end_time="16:00")

        delete_trip(db_session, trip_a.id, TEST_USER_ID)

        result = get_trips(db_session, TEST_USER_ID)
        assert len(result["trips"]) == 1
        assert result["trips"][0]["id"] == trip_b.id
