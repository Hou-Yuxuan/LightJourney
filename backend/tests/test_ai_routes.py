# -*- coding: utf-8 -*-
"""测试 AI 路由 — Skill1 / Skill2 端点"""
from unittest.mock import patch

import pytest

pytest_plugins = ["tests.conftest_web"]

from tests.conftest_web import create_test_trip, TEST_USER_ID, TEST_USER_ID_2


AI_PLAN_RESPONSE = [
    {
        "date": "2026-09-01",
        "start_time": "09:00",
        "end_time": "12:00",
        "title": "西湖环湖漫步",
        "description": "清晨沿苏堤漫步，湖光山色尽收眼底，建议租一辆自行车慢慢骑行。",
        "budget": 30,
    },
    {
        "date": "2026-09-01",
        "start_time": "13:00",
        "end_time": "15:30",
        "title": "灵隐寺",
        "description": "下午前往灵隐寺，感受千年古刹的静谧，飞来峰石刻值得细看。",
        "budget": 75,
    },
]


class TestAIPlan:
    """POST /api/ai/plan"""

    @patch("routers.ai.call_deepseek_json")
    def test_plan_success(self, mock_deepseek, client, db_session):
        mock_deepseek.return_value = AI_PLAN_RESPONSE

        resp = client.post("/api/ai/plan", json={
            "city": "杭州",
            "days": 1,
            "preferences": ["自然风光", "人文历史"],
            "budget": 200,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 200
        assert len(data["data"]["plan"]) == 2
        assert data["data"]["conflicts"] == []  # 无已有行程 → 无冲突
        assert data["data"]["plan"][0]["title"] == "西湖环湖漫步"

    @patch("routers.ai.call_deepseek_json")
    def test_plan_with_existing_conflicts(self, mock_deepseek, client, db_session):
        """已有行程与 AI 生成的时段冲突时，conflicts 中有记录"""
        # 创建一条与 AI 生成的第一条重叠的已有行程
        create_test_trip(
            db_session,
            city="杭州",
            date="2026-09-01",
            start_time="09:00",
            end_time="12:00",
            title="已有西湖行程",
        )
        mock_deepseek.return_value = AI_PLAN_RESPONSE

        resp = client.post("/api/ai/plan", json={
            "city": "杭州",
            "days": 1,
            "preferences": ["自然风光"],
        })
        data = resp.json()
        assert data["code"] == 200
        assert len(data["data"]["conflicts"]) >= 1
        # 冲突的 plan item 应标记 _conflict
        conflicted_items = [p for p in data["data"]["plan"] if p["_conflict"]]
        assert len(conflicted_items) >= 1

    @patch("routers.ai.call_deepseek_json")
    def test_plan_validation_invalid_days(self, mock_deepseek, client):
        resp = client.post("/api/ai/plan", json={
            "city": "杭州",
            "days": 0,  # 无效：days < 1
            "preferences": [],
        })
        assert resp.status_code == 422  # Pydantic 校验拦截

    @patch("routers.ai.call_deepseek_json")
    def test_plan_deepseek_timeout(self, mock_deepseek, client):
        mock_deepseek.side_effect = RuntimeError("AI 服务响应超时，请稍后重试")

        resp = client.post("/api/ai/plan", json={
            "city": "杭州",
            "days": 2,
            "preferences": [],
        })
        assert resp.status_code == 502

    @patch("routers.ai.call_deepseek_json")
    def test_plan_deepseek_invalid_json(self, mock_deepseek, client):
        mock_deepseek.side_effect = ValueError("AI 返回格式异常")

        resp = client.post("/api/ai/plan", json={
            "city": "杭州",
            "days": 2,
            "preferences": [],
        })
        assert resp.status_code == 502

    @patch("routers.ai.call_deepseek_json")
    def test_plan_returns_object_not_array(self, mock_deepseek, client):
        """DeepSeek 返回了对象而非数组"""
        mock_deepseek.return_value = {"error": "something"}

        resp = client.post("/api/ai/plan", json={
            "city": "杭州",
            "days": 1,
            "preferences": [],
        })
        assert resp.status_code == 502
        assert "非预期" in resp.json()["detail"]


class TestAICopywriting:
    """POST /api/ai/copywriting"""

    @patch("routers.ai.call_deepseek")
    def test_copywriting_success(self, mock_deepseek, client, db_session):
        mock_deepseek.return_value = "今天在杭州太开心了🌸 西湖边的晨光美得像画一样..."

        trip = create_test_trip(db_session, city="杭州", date="2026-09-01")

        resp = client.post("/api/ai/copywriting", json={"trip_id": trip.id})
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 200
        assert "杭州" in data["data"]["copywriting"]
        assert data["data"]["trip_title"] == "大熊猫繁育研究基地"
        assert data["data"]["trip_date"] == "2026-09-01"

    @patch("routers.ai.call_deepseek")
    def test_copywriting_with_context(self, mock_deepseek, client, db_session):
        """验证文案接口会传入当天同城其他行程作为上下文"""
        mock_deepseek.return_value = "串联多段行程的文案..."

        create_test_trip(db_session, city="成都", date="2026-08-15",
                         start_time="09:00", end_time="12:00", title="熊猫基地")
        target = create_test_trip(db_session, city="成都", date="2026-08-15",
                                   start_time="14:00", end_time="16:00", title="宽窄巷子")

        resp = client.post("/api/ai/copywriting", json={"trip_id": target.id})
        assert resp.status_code == 200

        # 验证 call_deepseek 被调用时用户消息包含了上下文行程
        call_args = mock_deepseek.call_args
        user_message = call_args[0][1]  # 第二个位置参数是 user_message
        assert "熊猫基地" in user_message
        assert "宽窄巷子" in user_message

    def test_copywriting_trip_not_found(self, client):
        resp = client.post("/api/ai/copywriting", json={"trip_id": 9999})
        assert resp.status_code == 404

    def test_copywriting_other_user_trip(self, client, db_session):
        trip = create_test_trip(db_session, user_id=TEST_USER_ID_2)

        resp = client.post("/api/ai/copywriting", json={"trip_id": trip.id})
        assert resp.status_code == 403

    @patch("routers.ai.call_deepseek")
    def test_copywriting_deepseek_error(self, mock_deepseek, client, db_session):
        mock_deepseek.side_effect = RuntimeError("AI 服务调用失败")

        trip = create_test_trip(db_session)

        resp = client.post("/api/ai/copywriting", json={"trip_id": trip.id})
        assert resp.status_code == 502
