# 旅行行程管理系统 — 概要设计文档

> 版本：v1.0 | 日期：2026-07-08
> 团队规模：5人 | 开发周期：1天（MVP）

---

## 一、文档说明

### 1.1 文档目的

本文档在需求分析文档（REQUIREMENTS.md）的基础上，完成系统的概要设计，包括：

- 系统架构与模块划分
- 模块间接口定义（API契约）
- 数据库设计
- 关键流程设计
- 5人团队分工方案

### 1.2 前置阅读

本文档依赖 [REQUIREMENTS.md](REQUIREMENTS.md) 中定义的功能需求（F-01 ~ F-12），设计决策参见项目根目录的 [CLAUDE.md](../CLAUDE.md)。

---

## 二、系统架构

### 2.1 架构总览

```
┌─────────────────────────────────────────────────────────┐
│                      前端 (Vue 3 SPA)                     │
│                                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐ │
│  │ 登录注册  │ │ 行程列表  │ │ 行程编辑  │ │  AI交互弹窗 │ │
│  │ 页面     │ │ 页面     │ │ 弹窗     │ │  弹窗      │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └─────┬──────┘ │
│       │             │            │              │        │
│  ┌────┴─────────────┴────────────┴──────────────┴──────┐ │
│  │              api/ 层 (axios 实例 + 拦截器)           │ │
│  └────────────────────────┬────────────────────────────┘ │
└───────────────────────────┼──────────────────────────────┘
                            │ HTTP + JSON
                            │ Authorization: Bearer <JWT>
┌───────────────────────────┼──────────────────────────────┐
│                      后端 (FastAPI)                       │
│                           │                               │
│  ┌────────────────────────┴──────────────────────────┐  │
│  │                  routers/ 路由层                    │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │  │
│  │  │ auth.py  │  │ trips.py │  │    ai.py         │ │  │
│  │  │ 注册登录  │  │ 行程CRUD │  │  AI Skill接口    │ │  │
│  │  └────┬─────┘  └────┬─────┘  └────────┬─────────┘ │  │
│  └───────┼─────────────┼─────────────────┼───────────┘  │
│          │             │                  │              │
│  ┌───────┼─────────────┼──────────────────┼───────────┐  │
│  │       └─────────────┴──────────────────┘           │  │
│  │                  services/ 服务层                    │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌────────────┐ │  │
│  │  │auth_service  │ │trip_service  │ │ai_service  │ │  │
│  │  │ 密码加密     │ │ 冲突校验     │ │DeepSeek调用│ │  │
│  │  │ JWT签发验证  │ │ 预算统计     │ │Prompt管理  │ │  │
│  │  └──────┬───────┘ └──────┬───────┘ └─────┬──────┘ │  │
│  └─────────┼────────────────┼───────────────┼────────┘  │
│            │                │                │           │
│  ┌─────────┼────────────────┼────────────────┼────────┐  │
│  │         └────────────────┴────────────────┘        │  │
│  │                  models/ 数据访问层                   │  │
│  │  ┌──────────────────────────────────────────────┐   │  │
│  │  │         SQLAlchemy ORM + SQLite               │   │  │
│  │  └──────────────────────────────────────────────┘   │  │
│  └─────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────┘
```

### 2.2 技术栈明细

| 层 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 前端框架 | Vue 3 | ^3.4 | Composition API |
| 构建工具 | Vite | ^5 | 开发服务器 + 打包 |
| UI组件库 | Element Plus | ^2.5 | 全局注册 |
| 状态管理 | Pinia | ^2.1 | 仅存储用户token信息 |
| HTTP客户端 | Axios | ^1.7 | 拦截器统一处理token和错误 |
| 前端路由 | Vue Router | ^4.3 | history模式 |
| 后端框架 | FastAPI | ^0.111 | Python异步 |
| ORM | SQLAlchemy | ^2.0 | 模型定义 + 查询 |
| 鉴权 | PyJWT + bcrypt | — | access token 24h |
| LLM SDK | openai | ^1.30 | DeepSeek兼容OpenAI格式 |
| 数据库 | SQLite | — | 文件存储，零配置 |
| 后端服务器 | Uvicorn | ^0.30 | ASGI |

---

## 三、模块划分

### 3.1 后端模块

| 模块 | 文件 | 职责 | 依赖 |
|------|------|------|------|
| 应用入口 | `main.py` | FastAPI实例创建、路由注册、CORS中间件、启动事件（建表） | 全部router |
| 配置 | `config.py` | 环境变量读取（DB路径、JWT密钥、DeepSeek API Key/Base URL） | 无 |
| 数据库 | `database.py` | SQLite引擎创建、Session管理、Base定义 | config |
| 用户模型 | `models/user.py` | User ORM模型 | database |
| 行程模型 | `models/trip.py` | Trip ORM模型 | database |
| 鉴权路由 | `routers/auth.py` | POST /api/auth/register、POST /api/auth/login | auth_service |
| 行程路由 | `routers/trips.py` | GET/POST/PUT/DELETE /api/trips | trip_service、auth依赖 |
| AI路由 | `routers/ai.py` | POST /api/ai/plan、POST /api/ai/copywriting | ai_service、auth依赖 |
| 鉴权服务 | `services/auth_service.py` | 密码哈希、密码验证、JWT签发、JWT验证、从token提取user_id | config |
| 行程服务 | `services/trip_service.py` | 行程CRUD、时段冲突算法、预算统计算法、用户数据隔离校验 | models/trip |
| AI服务 | `services/ai_service.py` | DeepSeek客户端初始化、通用API调用封装、JSON解析容错 | config |
| 规划Prompt | `prompts/planning.py` | Skill1系统提示词 + 用户消息模板 | 无 |
| 文案Prompt | `prompts/copywriting.py` | Skill2系统提示词 + 用户消息模板 | 无 |
| 依赖工具 | `dependencies.py` | get_current_user() 依赖注入函数，解析JWT并返回user_id | auth_service |

### 3.2 前端模块

| 模块 | 文件/目录 | 职责 | 依赖 |
|------|------|------|------|
| 入口 | `main.js` | 创建Vue应用、注册插件（Router/Pinia/Element Plus） | 全部 |
| 样式变量 | `styles/variables.css` | CSS变量：颜色、字体、间距、圆角、阴影 | 全部组件 |
| 路由 | `router/index.js` | 路由表定义、beforeEach守卫（鉴权拦截） | store/user |
| API实例 | `api/index.js` | axios实例创建、请求拦截器（注入token）、响应拦截器（统一错误处理） | store/user |
| 鉴权API | `api/auth.js` | login()、register() | api/index |
| 行程API | `api/trips.js` | getTrips()、getTrip()、createTrip()、updateTrip()、deleteTrip() | api/index |
| AI API | `api/ai.js` | planTrip()、generateCopywriting() | api/index |
| 用户Store | `stores/user.js` | token存储/读取/清除、登录状态判断 | 无 |
| 登录页 | `views/Login.vue` | 登录表单、跳转注册页链接 | api/auth、stores/user |
| 注册页 | `views/Register.vue` | 注册表单、跳转登录页链接 | api/auth |
| 行程列表页 | `views/TripList.vue` | 筛选栏、日期分组、行程卡片列表、预算统计、空状态、新建按钮 | api/trips、api/ai |
| 行程卡片 | `components/TripCard.vue` | 单条行程信息展示、编辑/删除/文案按钮（hover显示） | 无（纯展示+emit） |
| 行程编辑弹窗 | `components/TripFormDialog.vue` | 新建/编辑表单、前端校验、提交 | api/trips |
| AI规划弹窗 | `components/AIPlanDialog.vue` | 三步式：参数填写→预览编辑表格→确认保存 | api/ai、api/trips |
| AI文案弹窗 | `components/AICopywritingDialog.vue` | 文案展示、编辑、复制 | api/ai |

---

## 四、接口设计（API契约）

### 4.1 统一规范

**Base URL：** `http://localhost:8000/api`

**请求头：**
```
Content-Type: application/json
Authorization: Bearer <jwt_token>   （除注册/登录外的所有接口）
```

**统一响应格式：**
```json
{
  "code": 200,
  "message": "success",
  "data": { }
}
```

**错误码约定：**

| code | 含义 |
|------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未登录或token过期 |
| 403 | 无权限（操作他人数据） |
| 409 | 冲突（时段重叠） |
| 422 | 请求体验证失败（FastAPI自动返回） |
| 500 | 服务器内部错误 |
| 502 | AI服务调用失败 |

### 4.2 接口详表

#### 4.2.1 POST /api/auth/register

```
请求：
{
  "username": "zhangsan",
  "password": "123456"
}

成功响应 (201)：
{
  "code": 201,
  "message": "注册成功",
  "data": { "id": 1, "username": "zhangsan" }
}

失败响应 (409)：
{
  "code": 409,
  "message": "用户名已被注册",
  "data": null
}
```

#### 4.2.2 POST /api/auth/login

```
请求：
{
  "username": "zhangsan",
  "password": "123456"
}

成功响应：
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGci...",
    "token_type": "bearer",
    "username": "zhangsan"
  }
}

失败响应 (401)：
{
  "code": 401,
  "message": "用户名或密码错误",
  "data": null
}
```

#### 4.2.3 GET /api/trips

```
Query参数：
  city      | string | 可选，筛选城市
  date_from | string | 可选，开始日期 YYYY-MM-DD
  date_to   | string | 可选，结束日期 YYYY-MM-DD

响应：
{
  "code": 200,
  "message": "success",
  "data": {
    "trips": [
      {
        "id": 1,
        "city": "成都",
        "date": "2026-08-15",
        "start_time": "09:00",
        "end_time": "12:00",
        "title": "大熊猫繁育研究基地",
        "description": "上午参观熊猫基地...",
        "budget": 55.00,
        "created_at": "2026-07-08T10:00:00",
        "updated_at": "2026-07-08T10:00:00"
      }
    ],
    "total_budget": 155.00,
    "daily_budgets": {
      "2026-08-15": 110.00,
      "2026-08-16": 45.00
    }
  }
}
```

#### 4.2.4 POST /api/trips

```
请求：
{
  "city": "成都",
  "date": "2026-08-15",
  "start_time": "09:00",
  "end_time": "12:00",
  "title": "大熊猫繁育研究基地",
  "description": "上午参观熊猫基地...",
  "budget": 55.00
}

成功响应 (201)：
{
  "code": 201,
  "message": "创建成功",
  "data": { /* 完整trip对象，含id */ }
}

失败响应 (409)：
{
  "code": 409,
  "message": "该时段与已有行程冲突",
  "data": { "conflict_trip_id": 3 }
}
```

#### 4.2.5 PUT /api/trips/:id

```
请求：同 POST /api/trips（所有字段可选，传入即更新）

成功响应：
{
  "code": 200,
  "message": "更新成功",
  "data": { /* 更新后的trip对象 */ }
}

失败响应 (403)：
{
  "code": 403,
  "message": "无权操作该行程",
  "data": null
}
```

#### 4.2.6 DELETE /api/trips/:id

```
成功响应：
{
  "code": 200,
  "message": "删除成功",
  "data": null
}
```

#### 4.2.7 POST /api/ai/plan

```
请求：
{
  "city": "成都",
  "days": 3,
  "preferences": ["美食", "自然风光"],
  "budget": 1500
}

成功响应：
{
  "code": 200,
  "message": "success",
  "data": {
    "plan": [
      {
        "date": "2026-08-15",
        "start_time": "09:00",
        "end_time": "12:00",
        "title": "大熊猫繁育研究基地",
        "description": "上午参观熊猫基地...",
        "budget": 55
      }
    ],
    "conflicts": [
      {
        "plan_index": 2,
        "conflict_trip": { "id": 3, "title": "已有行程名" },
        "overlap": "时段重叠 09:00-12:00"
      }
    ]
  }
}
```

#### 4.2.8 POST /api/ai/copywriting

```
请求：
{
  "trip_id": 1
}

响应：
{
  "code": 200,
  "message": "success",
  "data": {
    "copywriting": "今天在成都暴走两万步...",
    "trip_title": "大熊猫繁育研究基地",
    "trip_date": "2026-08-15"
  }
}
```

---

## 五、数据库设计

### 5.1 ER图（文字版）

```
┌──────────────┐       ┌──────────────────┐
│    users     │       │      trips       │
├──────────────┤       ├──────────────────┤
│ id (PK)      │──┐    │ id (PK)          │
│ username     │  │    │ user_id (FK)     │──┐
│ password_hash│  ├───>│ city             │  │
│ created_at   │       │ date             │  │
└──────────────┘       │ start_time       │
                       │ end_time         │
                       │ title            │
                       │ description      │
                       │ budget           │
                       │ created_at       │
                       │ updated_at       │
                       └──────────────────┘

一个用户 → 多条行程
（每个用户数据完全隔离）
```

### 5.2 建表SQL

```sql
-- 用户表
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 行程表
CREATE TABLE trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    city VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT DEFAULT '',
    budget DECIMAL(10,2) DEFAULT 0.00,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 索引：加速按用户+日期的行程查询（列表页、冲突检测都需要）
CREATE INDEX idx_trips_user_date ON trips(user_id, date);
```

---

## 六、关键算法设计

### 6.1 时段冲突检测算法

```
输入：user_id, date, new_start, new_end, exclude_trip_id(编辑时排除自身)
输出：冲突的行程列表 / 无冲突

算法（伪代码）：

def check_conflict(user_id, date, new_start, new_end, exclude_trip_id=None):
    查询 trips WHERE user_id = ? AND date = ? AND (exclude时排除自身id)
    
    for each existing_trip in 查询结果:
        # 两个时段重叠的充要条件：A开始 < B结束 AND A结束 > B开始
        if new_start < existing_trip.end_time AND new_end > existing_trip.start_time:
            冲突，加入冲突列表
    
    return 冲突列表

边界处理：
- 12:00 结束 vs 12:00 开始 → 不冲突（等于不算重叠）
- 09:00-10:00 vs 09:30-11:00 → 冲突（中间时段被覆盖）
- 09:00-12:00 vs 12:00-14:00 → 不冲突（首尾相接可接受）
```

### 6.2 AI规划批量保存的冲突处理

```
输入：user_id, plan_json (AI生成的N条行程数组)
输出：{ saved: [...], failed: [...] }

算法：

saved = []
failed = []

遍历 plan_json 的每一条行程item：
    冲突列表 = check_conflict(user_id, item.date, item.start_time, item.end_time)
    
    if 冲突列表 为空：
        写入数据库
        saved.append(item)
    else：
        item.conflict_reason = "时段与已有行程冲突"
        failed.append(item)

返回 { saved_count: len(saved), failed_count: len(failed), failed_items: failed }
```

### 6.3 预算统计算法

```
输入：user_id, 筛选条件(可选)
输出：{ total_budget, daily_budgets: { "日期": 金额 } }

算法：

查询 trips WHERE user_id = ? AND 城市匹配 AND 日期范围匹配

total = sum(所有查询结果的 budget)
daily = {}
for trip in 结果:
    daily[trip.date] = daily.get(trip.date, 0) + trip.budget

返回 { total_budget: total, daily_budgets: daily }
```

---

## 七、关键流程时序

### 7.1 AI行程规划流程

```
用户                前端                    后端                     DeepSeek
 │                   │                       │                         │
 │ 点击"AI规划"      │                       │                         │
 │──────────────────>│                       │                         │
 │                   │                       │                         │
 │ 填写参数并提交    │                       │                         │
 │──────────────────>│                       │                         │
 │                   │ POST /api/ai/plan     │                         │
 │                   │──────────────────────>│                         │
 │                   │                       │ 查询已有行程日期范围    │
 │                   │                       │─────────┐               │
 │                   │                       │<────────┘               │
 │                   │                       │                         │
 │                   │                       │ 拼装Prompt，调用API     │
 │                   │                       │────────────────────────>│
 │                   │                       │                         │
 │                   │                       │      JSON响应           │
 │                   │                       │<────────────────────────│
 │                   │                       │                         │
 │                   │                       │ 解析JSON，检测冲突      │
 │                   │                       │─────────┐               │
 │                   │                       │<────────┘               │
 │                   │                       │                         │
 │                   │   返回plan + conflicts │                         │
 │                   │<──────────────────────│                         │
 │                   │                       │                         │
 │ 展示预览表格      │                       │                         │
 │<──────────────────│                       │                         │
 │                   │                       │                         │
 │ 编辑/修改/删除    │                       │                         │
 │──────────────────>│                       │                         │
 │                   │                       │                         │
 │ 确认保存          │                       │                         │
 │──────────────────>│                       │                         │
 │                   │ POST /api/trips (批量)│                         │
 │                   │──────────────────────>│                         │
 │                   │                       │ 逐条冲突检测 + 写入     │
 │                   │                       │─────────┐               │
 │                   │                       │<────────┘               │
 │                   │                       │                         │
 │                   │   返回保存结果        │                         │
 │                   │<──────────────────────│                         │
 │                   │                       │                         │
 │ 显示保存结果提示  │                       │                         │
 │<──────────────────│                       │                         │
```

### 7.2 文案生成流程

```
用户                前端                    后端                     DeepSeek
 │                   │                       │                         │
 │ 点击"生成文案"    │                       │                         │
 │──────────────────>│                       │                         │
 │                   │ POST /api/ai/copywriting                      │
 │                   │──────────────────────>│                         │
 │                   │                       │ 查询目标行程            │
 │                   │                       │ 查询当天同城所有行程    │
 │                   │                       │─────────┐               │
 │                   │                       │<────────┘               │
 │                   │                       │                         │
 │                   │                       │ 拼装Prompt（含上下文）  │
 │                   │                       │────────────────────────>│
 │                   │                       │                         │
 │                   │                       │     文案文本            │
 │                   │                       │<────────────────────────│
 │                   │                       │                         │
 │                   │   返回文案+行程摘要   │                         │
 │                   │<──────────────────────│                         │
 │                   │                       │                         │
 │ 弹窗展示文案      │                       │                         │
 │<──────────────────│                       │                         │
 │                   │                       │                         │
 │ 微调文字/复制     │                       │                         │
 │<─────────────────>│                       │                         │
```

---

## 八、5人团队分工

### 8.1 角色分配

| 编号 | 角色 | 代号 | 核心职责 |
|------|------|------|------|
| P1 | 后端负责人 | **BE-Lead** | 项目初始化、数据库、鉴权模块 |
| P2 | 后端开发 | **BE-AI** | 行程业务逻辑、AI服务封装、Prompt |
| P3 | 前端负责人 | **FE-Lead** | 项目初始化、路由架构、基础组件 |
| P4 | 前端开发 | **FE-Trip** | 行程列表页、编辑弹窗、筛选统计 |
| P5 | 前端开发 | **FE-AI** | AI规划弹窗、AI文案弹窗 |

### 8.2 详细任务拆分

#### P1 — 后端负责人（BE-Lead）

| 任务ID | 任务 | 产出文件 | 预计耗时 | 前置依赖 |
|------|------|------|------|------|
| BE-01 | FastAPI项目初始化、目录结构创建 | `main.py`, `config.py`, `database.py`, `requirements.txt` | 15min | 无 |
| BE-02 | User模型定义 + 数据库建表 | `models/user.py`, 建表逻辑 | 15min | BE-01 |
| BE-03 | Trip模型定义 | `models/trip.py` | 15min | BE-01 |
| BE-04 | 密码加密 + JWT签发/验证 | `services/auth_service.py` | 30min | BE-02 |
| BE-05 | 注册接口 POST /api/auth/register | `routers/auth.py` (注册部分) | 20min | BE-04 |
| BE-06 | 登录接口 POST /api/auth/login | `routers/auth.py` (登录部分) | 20min | BE-04 |
| BE-07 | JWT依赖注入 get_current_user | `dependencies.py` | 15min | BE-04 |
| BE-08 | 统一响应格式工具函数 | 在 `main.py` 或独立 `schemas.py` 中定义 | 10min | BE-01 |
| BE-09 | CORS中间件配置 | `main.py` | 5min | BE-01 |
| BE-10 | 联调支持：与P3对接鉴权接口 | — | 20min | BE-05/06/07 |

**P1 总耗时：约 2.5 小时**

#### P2 — 后端开发（BE-AI）

| 任务ID | 任务 | 产出文件 | 预计耗时 | 前置依赖 |
|------|------|------|------|------|
| BE-11 | 行程CRUD服务层（含冲突检测、预算统计） | `services/trip_service.py` | 45min | P1完成BE-03 |
| BE-12 | 行程CRUD路由 GET/POST/PUT/DELETE /api/trips | `routers/trips.py` | 45min | BE-11, BE-07 |
| BE-13 | DeepSeek客户端封装（通用调用+JSON解析容错） | `services/ai_service.py` | 30min | BE-01 |
| BE-14 | Skill1 Prompt模板编写 | `prompts/planning.py` | 30min | 无 |
| BE-15 | Skill2 Prompt模板编写 | `prompts/copywriting.py` | 20min | 无 |
| BE-16 | AI规划接口 POST /api/ai/plan | `routers/ai.py` (plan部分) | 30min | BE-13, BE-14, BE-11 |
| BE-17 | AI文案接口 POST /api/ai/copywriting | `routers/ai.py` (copywriting部分) | 20min | BE-13, BE-15 |
| BE-18 | 联调支持：与P5对接AI接口 | — | 20min | BE-16/17 |

**P2 总耗时：约 3.5 小时**

#### P3 — 前端负责人（FE-Lead）

| 任务ID | 任务 | 产出文件 | 预计耗时 | 前置依赖 |
|------|------|------|------|------|
| FE-01 | Vue 3 + Vite项目初始化 | `package.json`, `vite.config.js`, `index.html`, `main.js` | 15min | 无 |
| FE-02 | Element Plus安装与全局配置 | `main.js` 中注册 | 10min | FE-01 |
| FE-03 | CSS变量文件（颜色/字体/间距） | `styles/variables.css` | 20min | 无 |
| FE-04 | Vue Router路由表 + beforeEach守卫 | `router/index.js` | 25min | FE-01 |
| FE-05 | Pinia用户Store（token管理） | `stores/user.js` | 15min | FE-01 |
| FE-06 | Axios实例 + 请求/响应拦截器 | `api/index.js` | 25min | FE-05 |
| FE-07 | Auth API封装（login/register） | `api/auth.js` | 10min | FE-06 |
| FE-08 | 登录页面 | `views/Login.vue` | 30min | FE-04, FE-07 |
| FE-09 | 注册页面 | `views/Register.vue` | 20min | FE-04, FE-07 |
| FE-10 | App.vue根组件（router-view布局） | `App.vue` | 10min | FE-04 |
| FE-11 | 联调支持：与P1对接鉴权流程 | — | 20min | FE-08/09 |

**P3 总耗时：约 3 小时**

#### P4 — 前端开发（FE-Trip）

| 任务ID | 任务 | 产出文件 | 预计耗时 | 前置依赖 |
|------|------|------|------|------|
| FE-12 | 行程API封装（CRUD） | `api/trips.js` | 15min | P3完成FE-06 |
| FE-13 | 行程卡片组件 | `components/TripCard.vue` | 30min | FE-03 |
| FE-14 | 行程编辑弹窗组件（新建+编辑复用） | `components/TripFormDialog.vue` | 45min | FE-12 |
| FE-15 | 行程列表页—筛选栏 | `views/TripList.vue` (筛选部分) | 20min | FE-12 |
| FE-16 | 行程列表页—日期分组+卡片列表 | `views/TripList.vue` (列表部分) | 40min | FE-13, FE-14 |
| FE-17 | 行程列表页—预算统计展示 | `views/TripList.vue` (统计部分) | 15min | FE-12 |
| FE-18 | 行程列表页—空状态引导 | `views/TripList.vue` (空状态) | 15min | 无 |
| FE-19 | 删除二次确认 + 全局消息提示 | — | 10min | FE-12 |
| FE-20 | 联调支持：与P2对接行程CRUD接口 | — | 20min | FE-15/16/17 |

**P4 总耗时：约 3.5 小时**

#### P5 — 前端开发（FE-AI）

| 任务ID | 任务 | 产出文件 | 预计耗时 | 前置依赖 |
|------|------|------|------|------|
| FE-21 | AI API封装（planTrip/copywriting） | `api/ai.js` | 10min | P3完成FE-06 |
| FE-22 | AI规划弹窗—步骤① 参数填写 | `components/AIPlanDialog.vue` (步骤1) | 30min | FE-21 |
| FE-23 | AI规划弹窗—步骤② 预览编辑表格（行展开编辑） | `components/AIPlanDialog.vue` (步骤2) | 60min | FE-22 |
| FE-24 | AI规划弹窗—步骤③ 冲突标记 + 批量保存结果 | `components/AIPlanDialog.vue` (步骤3) | 30min | FE-23, FE-12 |
| FE-25 | AI规划弹窗—步骤进度条 + 步骤切换 | `components/AIPlanDialog.vue` (步骤控制) | 15min | FE-22/23/24 |
| FE-26 | AI文案弹窗（展示+编辑+复制） | `components/AICopywritingDialog.vue` | 30min | FE-21 |
| FE-27 | 文案复制到剪贴板功能 | 同上文件 | 10min | FE-26 |
| FE-28 | 联调支持：与P2对接AI接口 + 与P4对接（列表页集成弹窗入口） | — | 20min | FE-25/26 |

**P5 总耗时：约 3.5 小时**

### 8.3 依赖关系与协作图

```
时间线 →

P1(BE-Lead)  ██ BE-01~03 ██ BE-04 ██ BE-05~06 ██ BE-07~09 ██ BE-10(联调P3)
              ▲                      ▲
              │                      │
P3(FE-Lead)   │  FE-01~03  FE-04~06 │ FE-08~09 ██ FE-11(联调P1)
              │            ▲        │
              │            │        │
P2(BE-AI)   等待P1 ██ BE-11 ██ BE-13~15 ██ BE-16~17 ██ BE-18(联调P5)
              │     BE-03  ▲                     ▲
              │            │                     │
P4(FE-Trip)   │  等待P3 ██ FE-12~14 ██ FE-15~19 ██ FE-20(联调P2)
              │  FE-06    ▲                      ▲
              │           │                      │
P5(FE-AI)     │  等待P3   │   FE-21~22  FE-23~27 │ FE-28(联调P2+P4)
              │  FE-06    │            ▲         │
                          │            │         │
                          └─ 关键接合点 ──────────┘
```

### 8.4 关键协作节点

| 节点 | 时间点 | 涉及人员 | 内容 |
|------|------|------|------|
| 接合点1 | 项目启动时 | 全员 | 确认API契约文档、数据库Schema、统一响应格式 |
| 接合点2 | P1/P3完成后 | P1 + P3 | 联调注册登录流程，确认JWT签发和拦截器正确 |
| 接合点3 | P2/P4完成后 | P2 + P4 | 联调行程CRUD，确认冲突校验和筛选统计 |
| 接合点4 | P2/P5完成后 | P2 + P5 | 联调AI Skill接口，确认Prompt效果和JSON解析 |
| 接合点5 | P4/P5完成后 | P4 + P5 | 集成AI弹窗入口到列表页 |
| 接合点6 | 全部完成后 | 全员 | 端到端走查，验收标准10条逐条验证 |

---

## 九、开发环境与规范

### 9.1 统一环境

| 项目 | 要求 |
|------|------|
| Python | 3.10+ |
| Node.js | 18+ |
| 包管理 | pip (后端)、npm (前端) |
| 代码管理 | Git（统一仓库，main分支） |
| 后端端口 | 8000 |
| 前端端口 | 5173（Vite默认） |

### 9.2 命名规范

| 项目 | 规范 | 示例 |
|------|------|------|
| 后端文件名 | snake_case | `trip_service.py` |
| 后端类名 | PascalCase | `TripService` |
| 后端函数名 | snake_case | `check_conflict()` |
| 后端API端点 | kebab-case (URL路径) | `/api/ai/copywriting` |
| 前端组件名 | PascalCase | `TripFormDialog.vue` |
| 前端文件夹 | kebab-case / camelCase | `api/`, `stores/` |
| 前端CSS类名 | kebab-case | `.trip-card__title` |
| Git commit | 中文，动词开头 | `feat: 添加行程冲突校验` |

### 9.3 Git分支策略（简单版）

```
main ──────────────────────────────────────────────>
       ▲       ▲       ▲       ▲       ▲
       │       │       │       │       │
      BE-    FE-     BE-     FE-    联调
      Init   Init    Trip    Trip   修复
```

每人从main拉功能分支，完成后合并回main。分支命名：`be-auth`、`fe-trip-list`、`fe-ai-dialog` 等。

---

## 十、风险与应对

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|------|
| DeepSeek API不稳定或限流 | 中 | 高 | 后端加超时30s + 重试1次 + 友好的超时提示文案 |
| AI返回JSON格式异常 | 中 | 中 | 后端正则提取JSON + 解析失败返回错误码让前端提示重试 |
| 前端AI弹窗交互开发超时 | 高 | 中 | P5优先完成基本功能（展示+保存），行展开编辑可简化先做内联编辑 |
| 5人并行时前后端接口理解不一致 | 中 | 高 | 启动前全员过一遍API契约，联调前每人自测本模块 |
| SQLite并发写入问题 | 低 | 低 | FastAPI默认单线程执行，5人本地开发各自独立DB文件 |

---

## 十一、附录：开发启动检查清单

启动前，请每位成员确认以下事项：

- [ ] 已阅读 REQUIREMENTS.md（需求分析文档）
- [ ] 已阅读 CLAUDE.md（项目AI开发规范）
- [ ] 已阅读本文档中自己的任务清单
- [ ] 已安装 Python 3.10+ / Node.js 18+
- [ ] 已配置 DeepSeek API Key（P1、P2需要）
- [ ] 已克隆Git仓库并创建自己的功能分支
- [ ] 后端开发已确认API端点与前端对接人达成一致
- [ ] 前端开发已确认组件props/events与对接人达成一致

---

> 文档结束。下一步：各成员按第八章任务清单开始开发，每日站会同步进度。
