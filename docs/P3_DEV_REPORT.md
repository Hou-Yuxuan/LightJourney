# P3 (FE-Lead) 开发报告


## 一、任务概览

| 任务ID | 任务 | 产出文件 | 状态 |
|--------|------|---------|------|
| FE-01 | Vue 3 + Vite 项目初始化 | `package.json`, `vite.config.js`, `index.html`, `main.js` | ✅ 已完成 |
| FE-02 | Element Plus 安装与全局配置 | `main.js` | ✅ 已完成 |
| FE-03 | CSS 变量文件 | `styles/variables.css` | ✅ 已完成 |
| FE-04 | Vue Router 路由表 + beforeEach 守卫 | `router/index.js` | ✅ 已完成 |
| FE-05 | Pinia 用户 Store | `stores/user.js` | ✅ 已完成 |
| FE-06 | Axios 实例 + 请求/响应拦截器 | `api/index.js` | ✅ 已完成 |
| FE-07 | Auth API 封装 | `api/auth.js` | ✅ 已完成 |
| FE-08 | 登录页面 | `views/Login.vue` | ✅ 已完成 |
| FE-09 | 注册页面 | `views/Register.vue` | ✅ 已完成 |
| FE-10 | App.vue 根组件 | `App.vue` | ✅ 已完成 |

---

## 二、修改文件清单

| # | 文件 | 类型 | 说明 |
|---|------|------|------|
| 1 | `frontend/src/api/index.js` | 修改 | axios 拦截器增加 auth 页判断：登录/注册页的 `code: 401` 跳过全局拦截，交由组件自行处理错误提示 |
| 2 | `frontend/src/styles/variables.css` | 修改 | 强调色从鼠尾草绿 `#7D9B76` 改为板岩蓝 `#5B7C99`，hover 色同步更新为 `#4A6B87` |
| 3 | `frontend/src/views/Login.vue` | 重写 | 实现完整登录业务逻辑 + 地图纹理背景 + 地形色块 + MapLocation 图标 |
| 4 | `frontend/src/views/Register.vue` | 重写 | 实现完整注册业务逻辑 + 同步登录页设计风格 |

---

## 三、功能实现详情

### 3.1 登录页 (Login.vue)

**业务流程：**
1. 表单前端校验（用户名必填、密码必填）
2. 调用 `POST /api/auth/login` 
3. 成功后：`access_token` + `username` 写入 Pinia store（持久化 localStorage），`ElMessage.success` 提示，跳转 `/trips`
4. 失败后：组件内 `catch` 处理，`ElMessage.error` 显示后端返回的具体错误信息（如"用户名或密码错误"），不走全局 401 的"登录过期"提示

**设计风格：**
- 背景：浅灰蓝底 `#ECEEF1` + 三层 CSS 纹理
  - 网格线（48px 间距）+ 对角等高线（96px 间距）+ 散点（24px 间距）
  - 6 个大地形色块椭圆渐变：左上森林绿、右上湖泊蓝、中左草甸绿、右下暖棕盆地、左下灰绿低地、顶部高地微光
- 标题：`MapLocation` 图标（Element Plus）+ "LightJourney"，板岩蓝 `#5B7C99`
- 卡片：380px 居中白卡、圆角 12px、弱投影

### 3.2 注册页 (Register.vue)

**业务流程：**
1. 表单前端校验（用户名 2-20 位字母数字下划线、密码 6-30 位、两次密码一致）
2. 调用 `POST /api/auth/register`
3. 注册成功后自动调用 `POST /api/auth/login` 获取 token
4. token 写入 Store → 提示"注册成功" → 跳转 `/trips`
5. 失败后组件内 `catch` 处理（同登录页）

**设计风格：** 与登录页保持一致（背景纹理 + 地形色块 + 板岩蓝配色 + MapLocation 图标）

### 3.3 Axios 拦截器调整 (api/index.js)

**变更：** 成功响应拦截器中 `code === 401` 的处理增加 `window.location.pathname` 判断：
- `/login` 和 `/register` 页面：只 `reject`，不弹窗、不重定向，由页面组件自行处理
- 其他页面：保持原有全局处理（清空 token → 提示 → 跳转登录页）

---

## 四、设计决策

| 决策 | 选择 | 原因 |
|------|------|------|
| 登录成功跳转 | 统一跳 `/trips`，不处理 redirect | 简单直接，符合 MVP 阶段 |
| 登录失败错误处理 | 组件内 catch，不走全局拦截器 | 避免"登录过期"的误导提示 |
| 注册后行为 | 自动登录并跳转 | 减少用户操作步骤，体验流畅 |
| Token 过期检测 | 不做额外前端校验 | 开发阶段够用，全局拦截器兜底 |
| 配色方案 | 板岩蓝 `#5B7C99` | 与地图纹理背景搭配，接近导航/地图经典配色 |
| 背景风格 | CSS 地图纹理 + 地形色块 | 旅行感强，无需外部图片，性能好 |

---

## 五、依赖说明

- 前端 P3 可独立运行查看 UI 效果
- 登录/注册的实际 API 调用依赖 **后端 P1** 完成 `POST /api/auth/register` 和 `POST /api/auth/login` 接口
- 目前已可在浏览器中访问 `http://localhost:5173/login` 查看完整页面效果
