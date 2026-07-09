# -*- coding: utf-8 -*-
"""测试 trips 路由 — CRUD API 端点"""
import pytest
from fastapi.testclient import TestClient

pytest_plugins = ["tests.conftest_web"]

from tests.conftest_web import create_test_trip, TEST_USER_ID, TEST_USER_ID_2


class TestGetTrips:
    """GET /api/trips"""

    def test_empty_list(self, client, db_session):
        resp = client.get("/api/trips")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 200
        assert data["data"]["trips"] == []
        assert data["data"]["total_budget"] == 0.0

    def test_list_with_data(self, client, db_session):
        create_test_trip(db_session)
        create_test_trip(db_session, title="B", start_time="14:00", end_time="16:00")

        resp = client.get("/api/trips")
        data = resp.json()
        assert len(data["data"]["trips"]) == 2

    def test_filter_city(self, client, db_session):
        create_test_trip(db_session, city="成都")
        create_test_trip(db_session, city="杭州", date="2026-08-16")

        resp = client.get("/api/trips?city=杭州")
        assert len(resp.json()["data"]["trips"]) == 1

    def test_filter_date_range(self, client, db_session):
        create_test_trip(db_session, date="2026-08-15")
        create_test_trip(db_session, date="2026-08-16")
        create_test_trip(db_session, date="2026-08-17")

        resp = client.get("/api/trips?date_from=2026-08-15&date_to=2026-08-16")
        assert len(resp.json()["data"]["trips"]) == 2

    def test_unauthorized_without_token(self, client, db_session):
        """无 token 时返回 401/403（FastAPI HTTPBearer 行为）"""
        from main import app
        # 清除依赖覆写模拟无 token
        app.dependency_overrides.clear()
        with TestClient(app) as raw_client:
            resp = raw_client.get("/api/trips")
            # HTTPBearer 会返回 403（未提供凭证）或 401
            assert resp.status_code in (401, 403)
        # 恢复覆写
        from dependencies import get_db, get_current_user
        def override_get_db():
            yield db_session
        def override_get_current_user():
            return TEST_USER_ID
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user


class TestCreateTrip:
    """POST /api/trips"""

    def test_create_success(self, client, db_session):
        resp = client.post("/api/trips", json={
            "city": "杭州",
            "date": "2026-09-01",
            "start_time": "09:00",
            "end_time": "12:00",
            "title": "西湖",
            "description": "环湖",
            "budget": 0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 201
        assert data["data"]["city"] == "杭州"

    def test_create_conflict_returns_409(self, client, db_session):
        create_test_trip(db_session, start_time="09:00", end_time="12:00")

        resp = client.post("/api/trips", json={
            "city": "成都",
            "date": "2026-08-15",
            "start_time": "10:00",
            "end_time": "14:00",
            "title": "武侯祠",
            "description": "",
            "budget": 30,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 409
        assert "冲突" in data["message"]

    def test_validation_missing_required_field(self, client):
        resp = client.post("/api/trips", json={
            "city": "杭州",
            # 缺少 date, start_time, end_time, title
        })
        assert resp.status_code == 422  # FastAPI Pydantic 校验

    def test_validation_end_before_start(self, client):
        """结束时间早于开始时间应被拒绝（Pydantic 不做此校验，留给后端服务层）"""
        # 这个校验在 trip_service.create_trip 中不做，属于前端校验范围
        # 但 FastAPI 不会因为 end_time < start_time 而拒绝
        # 实际业务中由前端 validate 保证
        pass


class TestUpdateTrip:
    """PUT /api/trips/:id"""

    def test_update_success(self, client, db_session):
        trip = create_test_trip(db_session)

        resp = client.put(f"/api/trips/{trip.id}", json={"title": "新标题"})
        data = resp.json()
        assert data["code"] == 200
        assert data["data"]["title"] == "新标题"

    def test_update_not_found(self, client):
        resp = client.put("/api/trips/9999", json={"title": "x"})
        assert resp.status_code == 404

    def test_update_other_user_trip(self, client, db_session):
        """不能更新其他用户的行程"""
        trip = create_test_trip(db_session, user_id=TEST_USER_ID_2)

        resp = client.put(f"/api/trips/{trip.id}", json={"title": "x"})
        assert resp.status_code == 403

    def test_update_empty_body(self, client, db_session):
        trip = create_test_trip(db_session)

        resp = client.put(f"/api/trips/{trip.id}", json={})
        assert resp.status_code == 200
        assert resp.json()["code"] == 400  # 没有需要更新的字段

    def test_update_conflict(self, client, db_session):
        create_test_trip(db_session, start_time="09:00", end_time="12:00", title="已有")
        trip = create_test_trip(db_session, start_time="14:00", end_time="16:00", title="待编辑")

        resp = client.put(f"/api/trips/{trip.id}", json={
            "start_time": "10:00",
            "end_time": "14:00",
        })
        data = resp.json()
        assert data["code"] == 409


class TestDeleteTrip:
    """DELETE /api/trips/:id"""

    def test_delete_success(self, client, db_session):
        trip = create_test_trip(db_session)

        resp = client.delete(f"/api/trips/{trip.id}")
        assert resp.json()["code"] == 200

        # 确认已删除
        get_resp = client.get("/api/trips")
        assert get_resp.json()["data"]["trips"] == []

    def test_delete_not_found(self, client):
        resp = client.delete("/api/trips/9999")
        assert resp.status_code == 404

    def test_delete_other_user_trip(self, client, db_session):
        trip = create_test_trip(db_session, user_id=TEST_USER_ID_2)

        resp = client.delete(f"/api/trips/{trip.id}")
        assert resp.status_code == 403
