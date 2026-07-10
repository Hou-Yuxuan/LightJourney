# -*- coding: utf-8 -*-
"""LightJourney Skill1 — 行程智能规划

复用项目已有的 DeepSeek API 封装和 Prompt 模板，
增加合理性校验和质量评分层。

用法：
    from planner import run
    result = run(city="成都", days=3, preferences=["美食", "自然风光"], budget=3000)
    print(result["plan"])       # AI 生成的行程列表
    print(result["score"])      # 质量评分
    print(result["passed"])     # 是否通过门控
"""

import sys
import os
import json

# 确保能导入 backend 模块
_skill_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_skill_dir, "..", "..", ".."))
_backend_dir = os.path.join(_project_root, "backend")
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from datetime import datetime, timedelta
from services.ai_service import call_deepseek, extract_json_from_text
from prompts.planning import SKILL1_SYSTEM_PROMPT

# ---- 中国主要城市列表（用于合理性校验）----
KNOWN_CITIES = {
    "北京", "上海", "广州", "深圳", "成都", "重庆", "杭州", "南京", "武汉",
    "西安", "苏州", "长沙", "郑州", "天津", "青岛", "大连", "厦门", "昆明",
    "丽江", "大理", "哈尔滨", "长春", "沈阳", "济南", "合肥", "南昌", "福州",
    "贵阳", "南宁", "海口", "三亚", "拉萨", "兰州", "乌鲁木齐", "呼和浩特",
    "西宁", "银川", "桂林", "张家界", "黄山", "拉萨", "敦煌", "洛阳", "开封",
}

# ---- 常见景点季节性开放参考 ----
SEASONAL_ATTRACTIONS = {
    "冬季": ["冰雪大世界", "雪乡", "亚布力滑雪场", "长白山"],
    "夏季": ["水上乐园", "漂流", "海滨浴场"],
}

# ---- 质量评分 ----

def _score_plan(plan: list, params: dict, issues: list) -> dict:
    """
    质量评分：100 分起扣。

    扣分规则：
    - ERROR: 扣 30 分，一旦出现评分立即终止（最高 69 分）
    - WARNING: 扣 10 分
    - INFO: 扣 3 分
    """
    score = 100
    errors = []
    warnings = []
    infos = []

    for issue in issues:
        if issue["level"] == "ERROR":
            errors.append(issue)
            score -= 30
        elif issue["level"] == "WARNING":
            warnings.append(issue)
            score -= 10
        elif issue["level"] == "INFO":
            infos.append(issue)
            score -= 3

    score = max(0, score)
    has_error = len(errors) > 0
    passed = score >= 80 and not has_error
    conditional = 60 <= score <= 79 and not has_error

    return {
        "score": score,
        "passed": passed,
        "conditional": conditional,
        "errors": errors,
        "warnings": warnings,
        "infos": infos,
        "verdict": (
            "通过" if passed
            else (f"有条件通过 — {len(warnings)} 项建议需关注" if conditional
            else "拒绝 — 存在严重问题需修正")
        ),
    }


def validate_plan(plan: list, params: dict) -> list[dict]:
    """
    对 AI 生成的行程做合理性校验，返回问题列表。

    每条问题格式：{"level": "ERROR|WARNING|INFO", "item": "...", "detail": "..."}

    校验项：
    1. 天数匹配
    2. 每天 2-3 条
    3. 时段是否在 06:00-23:00 之间
    4. 每条行程时长 ≥ 2 小时
    5. 相邻行程间隔 ≥ 1 小时
    6. 预算汇总检查
    """
    issues = []

    # --- ERROR 级 ---
    # 1. 城市校验
    city = params.get("city", "")
    if not city or city.strip() == "":
        issues.append({"level": "ERROR", "item": "城市为空", "detail": "未指定目的地城市"})
    elif city not in KNOWN_CITIES:
        issues.append({"level": "WARNING", "item": "城市不在已知列表",
                        "detail": f"'{city}' 不在中国主要城市列表中，AI 仍会生成但可能不准确"})

    # 2. 天数校验
    days = params.get("days", 0)
    if days <= 0:
        issues.append({"level": "ERROR", "item": "天数≤0", "detail": f"出行天数必须 ≥1，当前为 {days}"})

    # 3. 结果为空
    if not plan or not isinstance(plan, list) or len(plan) == 0:
        issues.append({"level": "ERROR", "item": "生成为空", "detail": "AI 未能生成任何行程"})
        return issues  # 后续校验无意义

    # --- WARNING / INFO 级 ---
    # 4. 按日期分组
    dates = {}
    for item in plan:
        d = item.get("date", "unknown")
        dates.setdefault(d, []).append(item)

    actual_days = len(dates)
    if actual_days < days:
        issues.append({"level": "WARNING", "item": "天数不足",
                        "detail": f"要求 {days} 天，实际生成了 {actual_days} 天的行程"})
    elif actual_days > days:
        issues.append({"level": "INFO", "item": "天数超出",
                        "detail": f"要求 {days} 天，实际生成了 {actual_days} 天的行程"})

    # 5. 每天行程数量检查
    for d, items in dates.items():
        if len(items) < 2:
            issues.append({"level": "WARNING", "item": f"{d} 行程偏少",
                            "detail": f"当天仅有 {len(items)} 条行程，建议每天 2-3 条"})
        elif len(items) > 3:
            issues.append({"level": "INFO", "item": f"{d} 行程偏多",
                            "detail": f"当天有 {len(items)} 条行程，可能过于紧凑"})

    # 6. 时段合理性 & 时长检查 & 相邻间隔
    for d, items in dates.items():
        sorted_items = sorted(items, key=lambda x: x.get("start_time", "00:00"))
        for i, item in enumerate(sorted_items):
            start = item.get("start_time", "00:00")
            end = item.get("end_time", "00:00")
            title = item.get("title", "未知行程")

            # 时间格式校验
            try:
                sh, sm = int(start.split(":")[0]), int(start.split(":")[1])
                eh, em = int(end.split(":")[0]), int(end.split(":")[1])
            except (ValueError, IndexError):
                issues.append({"level": "WARNING", "item": title, "detail": f"时间格式异常: {start}-{end}"})
                continue

            # 太早或太晚
            if sh < 6:
                issues.append({"level": "WARNING", "item": title,
                                "detail": f"开始时间 {start} 过早，多数景点 08:00 后才开放"})
            if eh > 23 or (eh == 23 and em > 0):
                issues.append({"level": "WARNING", "item": title,
                                "detail": f"结束时间 {end} 过晚，注意安全和交通"})

            # 时长 ≥ 2 小时
            duration_min = (eh * 60 + em) - (sh * 60 + sm)
            if duration_min < 120:
                issues.append({"level": "WARNING", "item": title,
                                "detail": f"行程时长仅 {duration_min} 分钟，不足 2 小时"})

            # 相邻间隔 ≥ 1 小时
            if i > 0:
                prev = sorted_items[i - 1]
                prev_end = prev.get("end_time", "00:00")
                try:
                    peh, pem = int(prev_end.split(":")[0]), int(prev_end.split(":")[1])
                    gap = (sh * 60 + sm) - (peh * 60 + pem)
                    if gap < 60:
                        issues.append({"level": "INFO", "item": f"{prev.get('title', '?')} → {title}",
                                        "detail": f"相邻行程间隔仅 {gap} 分钟，建议 ≥1 小时用于交通、休息"})
                except (ValueError, IndexError):
                    pass

    # 7. 预算汇总
    if params.get("budget"):
        total_budget_cents = 0
        for item in plan:
            b = item.get("budget", 0)
            if isinstance(b, (int, float)):
                total_budget_cents += b
        if total_budget_cents > params["budget"] * 1.2:
            issues.append({"level": "WARNING", "item": "预算超支",
                            "detail": f"行程总计 ¥{total_budget_cents:.0f}，超出预算 ¥{params['budget']:.0f} 的 20%"})
        elif total_budget_cents > params["budget"]:
            issues.append({"level": "INFO", "item": "预算紧张",
                            "detail": f"行程总计 ¥{total_budget_cents:.0f}，略超预算 ¥{params['budget']:.0f}"})

    return issues


def plan_trip(city: str, days: int, preferences: list[str] | None = None,
              budget: float | None = None) -> dict:
    """
    调用 AI 生成行程 JSON 列表。

    Args:
        city: 目的地城市（必填）
        days: 出行天数（必填, ≥1）
        preferences: 偏好列表，如 ["美食", "自然风光", "人文历史"]
        budget: 总预算上限（可选）

    Returns:
        {
            "plan": [...],       # AI 返回的行程 JSON 数组
            "score": 85,         # 质量评分
            "passed": True,      # 是否通过门控
            "verdict": "通过",
            "issues": [...]      # 校验问题详情
        }
    """
    prefs = preferences or []
    params = {"city": city, "days": days, "preferences": prefs, "budget": budget}

    pref_text = "、".join(prefs) if prefs else "综合体验"
    budget_text = f"，总预算控制在 {budget} 元以内" if budget else "，预算不限"

    user_message = (
        f"请为我规划一趟 {city} 的 {days} 天旅行行程。\n"
        f"偏好方向：{pref_text}{budget_text}。"
    )

    try:
        raw_text = call_deepseek(SKILL1_SYSTEM_PROMPT, user_message)
        plan = extract_json_from_text(raw_text)
    except Exception as e:
        issues = [{"level": "ERROR", "item": "AI 调用失败", "detail": str(e)}]
        return {
            "plan": [],
            "score": 0,
            "passed": False,
            "conditional": False,
            "verdict": f"拒绝 — AI 调用失败: {str(e)[:100]}",
            "errors": issues,
            "warnings": [],
            "infos": [],
        }

    if not isinstance(plan, list):
        plan = []

    issues = validate_plan(plan, params)
    score_result = _score_plan(plan, params, issues)

    return {
        "plan": plan,
        **score_result,
    }


# ---- 便捷入口 ----
def run(city: str, days: int, preferences: list[str] | None = None,
        budget: float | None = None) -> dict:
    """规划行程便捷入口，与 plan_trip 相同。"""
    return plan_trip(city, days, preferences, budget)


# ---- 命令行入口 ----
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="LightJourney 行程智能规划")
    parser.add_argument("--city", required=True, help="目的地城市")
    parser.add_argument("--days", type=int, required=True, help="出行天数")
    parser.add_argument("--prefs", nargs="*", default=[], help="偏好标签（可选多个）")
    parser.add_argument("--budget", type=float, default=None, help="总预算上限")
    args = parser.parse_args()

    result = run(city=args.city, days=args.days,
                 preferences=args.prefs, budget=args.budget)

    print(f"\n{'='*50}")
    print(f"目的地: {args.city} | 天数: {args.days}")
    print(f"评分: {result['score']}/100 | 判定: {result['verdict']}")
    print(f"{'='*50}")
    for item in result.get("plan", []):
        print(f"  {item.get('date','?')} {item.get('start_time','?')}-{item.get('end_time','?')}"
          f"  {item.get('title','?')}  {item.get('budget',0)}元")
    if result.get("errors"):
        print(f"\n❌ 错误: ")
        for e in result["errors"]:
            print(f"  - {e['item']}: {e['detail']}")
    if result.get("warnings"):
        print(f"\n⚠️ 警告: ")
        for w in result["warnings"]:
            print(f"  - {w['item']}: {w['detail']}")
    if result.get("infos"):
        print(f"\n💡 建议: ")
        for i in result["infos"]:
            print(f"  - {i['item']}: {i['detail']}")
