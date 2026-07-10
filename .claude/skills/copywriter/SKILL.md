---
name: copywriter
description: Use when the user asks to generate social media copy, WeChat Moments text, or travel diary posts based on trip itinerary data. Triggers on "生成文案", "朋友圈文案", "行程分享", "帮我写一段旅行文字", or any request to turn trip details into shareable narrative text.
triggers: [生成文案, 朋友圈, 行程文案, 旅行分享, 社交文案, copywriting]
---

# 行程文案生成 `copywriter`

## Overview

LightJourney 项目的 Skill2，接收行程数据 → 调用 DeepSeek API → 生成 4-6 句口语化朋友圈文案 → 质量评分。

文案风格：真实旅行博主语气，口语化、有情绪、生活感，带 1-2 个 emoji，适合直接发布到社交平台。

## 输入格式

### 行程 JSON（标准格式）

```json
{
  "title": "大熊猫繁育研究基地",
  "description": "清晨前往熊猫基地，此时大熊猫最活跃…",
  "city": "成都",
  "date": "2026-08-15",
  "start_time": "09:00",
  "end_time": "12:00"
}
```

### 同天上下文（可选）

```json
[
  {"title": "宽窄巷子", "description": "下午钻进老茶馆…"},
  {"title": "火锅店", "description": "晚上来一顿地道麻辣火锅…"}
]
```

> 若传入纯文本，skill 会将其作为 `title` 处理。

## 输出示例

```
今天在成都暴走两万步🐼 早起去熊猫基地，看到滚滚趴在树上睡觉简直萌化了。
下午钻进宽窄巷子的茶馆喝了杯盖碗茶，那种慢悠悠的市井烟火气太治愈了。
晚上火锅店阿姨看我们辣得直喝水，偷偷给加了份冰粉。成都，下次还来。
```

## 执行步骤

```
校验输入（非空、格式正确？）
    │  ERROR → 终止
    │
    ▼
构建目标行程 + 同天上下文
    │
    ▼
调用 DeepSeek API（temperature=0.8，增加创意性）
    │ 失败 → 返回 error
    │
    ▼
质量评分（score_copy）
    ├── 句数 4-6？
    ├── 字数 30-300？
    ├── emoji 1-2 个？
    ├── 词汇重复度？
    └── 套话检测？
    │
    ▼
返回 { copywriting, score, passed, issues }
```

## 质量门控

| 评分 | 判定 | 行为 |
|------|------|------|
| ≥ 80 且无 ERROR | ✅ 通过 | 文案可直接使用 |
| 60-79 且无 ERROR | ⚠️ 有条件通过 | 文案可用但建议微调 |
| < 60 或 含 ERROR | ❌ 拒绝 | 需重新生成或修改输入 |

**扣分规则：**
- **ERROR**（扣 30 分，触发即拒绝）：输入为空 / AI 调用失败
- **WARNING**（扣 10 分）：句数 < 3、字数 < 30、emoji > 3、词汇重复 > 50%
- **INFO**（扣 3 分）：句数 > 8、字数 > 300、无 emoji、含常见套话

## 使用示例

```python
from writer import run

result = run({
    "title": "大熊猫繁育研究基地",
    "description": "清晨前往熊猫基地，此时大熊猫最活跃",
    "city": "成都",
    "date": "2026-08-15",
})

if result["passed"]:
    print(result["copywriting"])
else:
    print(f"生成失败: {result['verdict']}")
```

命令行：
```bash
cd .claude/skills/copywriter
python writer.py --trip '{"title":"熊猫基地","city":"成都","date":"2026-08-15","description":"看大熊猫"}'
```
