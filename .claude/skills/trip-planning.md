---
name: trip-planning
description: AI 智能规划行程 — 输入天数+城市+偏好+预算，DeepSeek 生成每日 2-3 条行程，三步确认后保存
---

# Skill1 — 行程智能规划

## 触发场景

用户描述出行意图时触发，例如：
- "帮我规划一趟成都 3 天游"
- "想去杭州玩两天，喜欢美食和自然风光"
- "规划一个北京 5 天历史人文之旅，预算 3000"

## API 端点

**规划（生成预览）：** `POST /api/ai/plan`
```
Authorization: Bearer <token>
Content-Type: application/json

{
  "city": "成都",           // 必填，目的地城市
  "days": 3,                // 必填，出行天数 1-30
  "preferences": ["美食", "自然风光"],  // 必填，至少选一个
  "budget": 2000            // 可选，总预算上限（元）
}
```

**响应：**
```json
{
  "code": 200,
  "data": {
    "plan": [
      {
        "_index": 0,
        "date": "2026-08-15",
        "start_time": "09:00",
        "end_time": "12:00",
        "title": "大熊猫繁育研究基地",
        "description": "清晨前往熊猫基地...",
        "budget": 55,
        "_conflict": false,
        "_conflict_detail": null
      }
    ],
    "conflicts": []
  }
}
```

**保存单条行程：** `POST /api/trips`
```json
{
  "city": "成都",
  "date": "2026-08-15",
  "start_time": "09:00",
  "end_time": "12:00",
  "title": "大熊猫繁育研究基地",
  "description": "清晨前往熊猫基地...",
  "budget": 55
}
```

## Agent 工作流（三步）

### Step 0: 收集参数
与用户确认以下信息：
1. **目的地城市** — 必填
2. **出行天数** — 1-30 天
3. **偏好标签** — 美食 / 自然风光 / 人文历史（至少选一个）
4. **预算上限** — 可选，单位元

### Step 1: 生成预览
- 调用 `POST /api/ai/plan`，传入收集的参数
- 解析返回的 `plan` 数组，按日期分组展示
- 标记冲突项：`_conflict: true` 的行程高亮显示冲突原因
- 展示 AI 生成的每日行程（日期、时段、标题、描述、预算）
- 允许用户编辑每条行程的所有字段（日期、时间、标题、描述、预算）
- 允许用户删除不满意的行程

### Step 2: 确认保存
- 列出将被保存的行程清单
- 展示将被跳过的冲突行程及原因
- 用户确认后，逐条调用 `POST /api/trips` 保存无冲突行程
- 冲突行程自动跳过，有冲突原因说明
- 返回保存结果：成功 N 条，跳过 M 条

## 关键约束

1. **AI 生成内容绝不直接写库** — 必须经过用户预览确认
2. **时段冲突由后端检测** — 前端提交时后端二次校验（12:00 结束 vs 12:00 开始 = 不冲突）
3. **用户需要登录** — 所有 API 调用需要 JWT token（未登录引导到 /login）
4. **DeepSeek 超时 30 秒** — 超时提示用户重试

## 后端实现位置

| 文件 | 作用 |
|------|------|
| `backend/routers/ai.py` | POST /api/ai/plan 路由 |
| `backend/prompts/planning.py` | Skill1 System Prompt 模板 |
| `backend/services/ai_service.py` | DeepSeek API 调用封装 |
| `frontend/src/components/AIPlanDialog.vue` | 前端三步弹窗 UI |

## 偏好标签可用值

`美食` `自然风光` `人文历史` `购物` `摄影` `探险` `亲子` `夜生活`

## 示例对话

**用户：** 帮我规划一趟成都 3 天游，喜欢美食和自然风光，预算 2000
**Agent：** 好的，我来为你规划成都 3 天游 🐼
→ 调用 API → 展示按日期分组的行程预览
→ "共生成 8 条行程，其中 1 条与已有行程冲突将被跳过。请预览编辑后确认保存。"
