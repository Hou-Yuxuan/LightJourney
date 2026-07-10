---
name: travel-planner
description: Use when the user asks to generate a travel itinerary, plan a trip, or create a day-by-day travel schedule. Triggers on requests like "帮我规划行程", "去XX玩几天", "生成旅行计划", or any trip-planning intent with a destination city and number of days.
triggers: [行程规划, 旅游计划, 去XX玩, 旅行规划, 生成行程, itinerary, trip plan]
---

# 行程智能规划 `travel-planner`

## Overview

LightJourney 项目的 Skill1，接收出行参数 → 调用 DeepSeek API → 生成结构化行程 JSON → 质量自检评分。

核心原则：AI 生成内容绝不直接入库，必须经过质量门控后才可交付用户预览。

## 输入参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `city` | string | ✅ | 目的地城市（需在中国主要城市列表中） |
| `days` | int | ✅ | 出行天数，≥1，≤30 |
| `preferences` | string[] | 否 | 偏好标签，如 `["美食", "自然风光", "人文历史"]` |
| `budget` | float | 否 | 总预算上限（人民币元） |

## 输出格式

```json
{
  "plan": [
    {
      "date": "2026-08-15",
      "start_time": "09:00",
      "end_time": "12:00",
      "title": "大熊猫繁育研究基地",
      "description": "清晨前往熊猫基地…",
      "budget": 55
    }
  ],
  "score": 85,
  "passed": true,
  "verdict": "通过",
  "errors": [],
  "warnings": [{"item": "成都", "detail": "不在已知城市列表"}],
  "infos": [{"item": "熊猫基地 → 宽窄巷子", "detail": "间隔仅 30 分钟"}]
}
```

## 执行步骤

```
解析输入参数
    │
    ▼
参数预检（城市/天数合法？）
    │  ERROR → 终止
    │
    ▼
构建 Prompt 并调用 DeepSeek API
    │ 失败 → 返回 error
    │
    ▼
从响应中提取 JSON 数组
    │
    ▼
运行质量校验（validate_plan）
    ├── 天数匹配？
    ├── 每天 2-3 条？
    ├── 时段 06:00-23:00？
    ├── 每条 ≥ 2 小时？
    ├── 相邻间隔 ≥ 1 小时？
    └── 预算汇总检查？
    │
    ▼
质量评分（_score_plan）
    │
    ▼
返回结构化结果 { plan, score, passed, issues }
```

## 质量门控

| 评分 | 判定 | 行为 |
|------|------|------|
| ≥ 80 且无 ERROR | ✅ 通过 | 输出结果供用户预览 |
| 60-79 且无 ERROR | ⚠️ 有条件通过 | 输出结果但附带警告建议 |
| < 60 或 含 ERROR | ❌ 拒绝 | 提示用户修正参数后重试 |

**扣分规则：**
- **ERROR**（扣 30 分，触发即拒绝）：城市为空 / 天数 ≤ 0 / AI 返回为空 / API 调用失败
- **WARNING**（扣 10 分）：天数不足、单日 < 2 条、时段过早过晚、时长不足 2h、预算超支 20%
- **INFO**（扣 3 分）：天数超出、单日 > 3 条、相邻间隔 < 1h、预算略超

## 使用示例

```python
from planner import run

result = run(city="成都", days=3,
             preferences=["美食", "自然风光"],
             budget=3000)

if result["passed"]:
    for item in result["plan"]:
        print(f"{item['date']} {item['title']}")
else:
    print(f"规划失败: {result['verdict']}")
```

命令行：
```bash
cd .claude/skills/travel-planner
python planner.py --city 成都 --days 3 --prefs 美食 自然风光 --budget 3000
```
