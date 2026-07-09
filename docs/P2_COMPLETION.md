# P2 (BE-AI) 完成报告

> 角色：后端开发 | 代号：BE-AI | 分支：`be-ai-p2`
> 日期：2026-07-09 | 测试：**79/79 passed**

---

## 一、任务完成清单

| 任务ID | 内容 | 产出文件 | 状态 |
|--------|------|---------|:--:|
| BE-11 | 行程 CRUD 服务层（冲突检测 + 预算统计） | `backend/services/trip_service.py` | ✅ |
| BE-12 | 行程 CRUD 路由 GET/POST/PUT/DELETE | `backend/routers/trips.py` | ✅ |
| BE-13 | DeepSeek 客户端封装（超时/重试/JSON容错） | `backend/services/ai_service.py` | ✅ |
| BE-14 | Skill1 Prompt 模板（行程规划） | `backend/prompts/planning.py` | ✅ |
| BE-15 | Skill2 Prompt 模板（文案生成） | `backend/prompts/copywriting.py` | ✅ |
| BE-16 | AI 规划接口 POST /api/ai/plan | `backend/routers/ai.py` | ✅ |
| BE-17 | AI 文案接口 POST /api/ai/copywriting | `backend/routers/ai.py` | ✅ |
| 补 | JWT 依赖注入（P1 BE-07 阻塞项） | `backend/dependencies.py` + `backend/services/auth_service.py` | ✅ |
| 补 | 路由注册到 main.py | `backend/main.py` | ✅ |
| 补 | 测试套件（4 文件，79 tests） | `backend/tests/` | ✅ |
| 补 | API 端点连通验证 | deepseek-v4-pro @ 172.171.82.25:5443 | ✅ |

---

## 二、产出文件一览

### 业务代码

| 文件 | 行数 | 核心内容 |
|------|------|---------|
| `backend/services/trip_service.py` | ~280 | 冲突检测算法、CRUD 5函数、预算统计、数据隔离校验 |
| `backend/routers/trips.py` | ~140 | 4 端点 + Pydantic Schema + 统一响应格式 |
| `backend/services/ai_service.py` | ~140 | httpx 直连 DeepSeek、30s 超时、1 次重试、3 级 JSON 容错 |
| `backend/routers/ai.py` | ~170 | Skill1 规划 + Skill2 文案 + 冲突标记 |

### Prompt 模板

| 文件 | 内容 |
|------|------|
| `backend/prompts/planning.py` | 专业旅行规划师角色、JSON-only 输出、每天2-3条约束、`build_planning_user_message()` |
| `backend/prompts/copywriting.py` | 真实旅行博主角色、口语化4-6句、上下文注入、`build_copywriting_user_message()` |

### 补充 P1

| 文件 | 实现 |
|------|------|
| `backend/dependencies.py` | `get_current_user()` JWT 验证 + `get_db()` 数据库会话 |
| `backend/services/auth_service.py` | `decode_access_token()` JWT 解析 |
| `backend/main.py` | 取消注释，注册 auth/trips/ai 三个路由模块 |

### 测试代码

| 文件 | 测试数 | 覆盖范围 |
|------|:------:|---------|
| `backend/tests/test_trip_service.py` | 28 | 冲突检测(8) + CRUD(8) + 预算(3) + 更新/删除(9) |
| `backend/tests/test_trip_routes.py` | 16 | 4 端点全路径测试（含鉴权/404/403/409） |
| `backend/tests/test_ai_service.py` | 20 | JSON 容错(9) + DeepSeek 调用(8) + 组合调用(2) + Key 校验(1) |
| `backend/tests/test_ai_routes.py` | 11 | Skill1 规划(6) + Skill2 文案(5) |
| `backend/tests/conftest_service.py` | — | 内存 SQLite + create_test_trip 辅助函数 |
| `backend/tests/conftest_web.py` | — | TestClient + 依赖注入覆写 |

---

## 三、关键技术决策

1. **httpx 直连代替 OpenAI SDK**：SDK v2.44 的 `http_client` 参数与内部网关 SSL 存在兼容问题，改用 httpx `Client(verify=False)` 直连，配合 `with` 上下文管理。

2. **延迟初始化**：OpenAI 客户端改为 `_get_client()` 延迟初始化，避免模块导入时因 API Key 缺失报错。

3. **JSON 3 级容错**：直接解析 → 正则提取代码块 → 正则提取最外层 []/{}，覆盖绝大部分 DeepSeek 格式异常。

4. **SQLite 类型转换**：`_parse_date()` / `_parse_time()` 将 API 字符串参数转为 Python date/time 对象，兼容 SQLite 严格类型检查。

5. **AI 不直写库**：`POST /api/ai/plan` 只返回预览数据和冲突标记（`_conflict` 字段），保存由前端逐条调 `POST /api/trips` 完成。

---

## 四、测试结果

```
======================== 79 passed, 3 warnings in 4.60s ========================
```

```
test_trip_service.py  ████████████████████████████  28/28
test_trip_routes.py   ████████████████████████████  16/16
test_ai_service.py    ████████████████████████████  20/20
test_ai_routes.py     ████████████████████████████  11/11
```

---

## 五、剩余工作（非 P2 范围）

| 任务 | 所属 | 说明 |
|------|:--:|------|
| `hash_password` / `verify_password` / `create_access_token` | P1 | 注册/登录需要 |
| `POST /api/auth/register` / `POST /api/auth/login` | P1 | 鉴权端点 |
| BE-18 联调 | P2 + P5 | 等 P5 完成 AI 弹窗后对接 |
| 前端 CRUD 联调 | P2 + P4 | 等 P4 完成行程列表页后对接 |

---

## 六、运行方式

```bash
cd backend
cp .env.example .env    # 并填入真实 API Key

pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 测试
PYTHONPATH=. pytest tests/ -v
```
