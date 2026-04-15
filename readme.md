# 运行智脑 OpsBrain AI

<p align="center">
  <img src="frontend/public/favicon.png" alt="OpsBrain AI Logo" width="120" />
</p>

<p align="center">
  <strong>智能运维管理平台</strong><br/>
  AI 驱动的运维管理系统，实现智能监控、自动化运维、数据驱动决策与绿色节能管理（持续迭代中）
</p>

---

## 技术架构

本项目采用前后端分离架构：

| 层级 | 技术栈 |
|------|--------|
| **前端** | Vue 3 · TypeScript · Vite · Vue Router · Pinia · Axios · Naive UI · Less |
| **前端扩展** | 知识库本地文档预览：`mammoth`（Word）· `xlsx`（Excel）· `docx` |
| **后端** | Python 3.13+ · FastAPI · SQLAlchemy 2（async）· PostgreSQL · Pydantic Settings |
| **数据迁移** | Alembic（`psycopg2-binary` 用于迁移脚本同步元数据） |
| **缓存 / 会话** | Redis（验证码等） |
| **短信** | 阿里云号码认证 / 短信服务（`alibabacloud-dypnsapi20170525`） |
| **认证** | JWT（`python-jose`）· bcrypt 密码哈希 |

## 当前能力概览

| 模块 | 说明 |
|------|------|
| **用户与认证** | 手机号注册 / 登录、短信验证码、JWT 鉴权、`/users/me` 获取当前用户 |
| **工作台** | 登录后首页仪表盘（占位统计，可对接真实监控数据） |
| **知识库** | 文件夹与文件列表 UI、上传入口、多格式预览（当前列表与部分数据为前端演示；`src/api/knowledge.ts` 预留后端接口） |
| **AI 对话** | 多会话聊天界面（当前为前端本地演示数据；`src/api/chat.ts` 预留后端接口） |

后端启动时会连接 Redis；注册流程依赖短信配置与验证码缓存。

## 项目结构

```
operation_brain_ai/
├── backend/
│   ├── main.py                 # FastAPI 入口：生命周期、CORS、路由与全局异常
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── alembic.ini             # Alembic 配置
│   ├── alembic/                # 迁移脚本与 env
│   ├── core/
│   │   ├── settings.py         # 多环境配置（.env.current + .env.{env}）
│   │   ├── security.py         # JWT、密码哈希
│   │   ├── deps.py             # get_current_user 等依赖
│   │   ├── redis.py            # Redis 连接管理
│   │   ├── exception_handler.py
│   │   └── reponse.py          # 统一成功/错误响应封装
│   ├── db/
│   │   ├── session.py          # 异步引擎、get_db
│   │   └── models/             # User、UserRole 等
│   ├── router/
│   │   └── users_router.py     # 公开路由 + 需鉴权路由
│   ├── repository/
│   │   └── users_repo.py       # 用户与验证码数据访问
│   ├── service/
│   │   └── sms_service.py      # 阿里云短信发送
│   ├── schema/                 # Pydantic 模型（含统一 ResponseModel）
│   ├── .env.current            # 当前环境名（由 EnvSettings 读取）
│   ├── .env.dev / .env.prod   # 各环境密钥与连接串（勿提交真实密钥）
│   └── .env.example            # 环境变量模板
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts          # 开发代理：/api -> 后端 8000
│   ├── public/
│   └── src/
│       ├── main.ts
│       ├── App.vue
│       ├── api/                # users、chat、knowledge、core
│       ├── router/index.ts     # 登录 / 注册 / 首页子路由
│       ├── stores/
│       ├── utils/              # request、知识库预览工具
│       ├── styles/
│       └── views/
│           ├── Login/Login.vue
│           ├── Register/Register.vue
│           ├── Home/Home.vue
│           ├── Dashboard/
│           ├── Knowledge/      # 知识库页面与组件
│           └── Chat/           # AI 对话页面与组件
│
└── README.md
```

## 快速开始

### 环境要求

- **Python** >= 3.13  
- **Node.js** >= 18（可使用 **npm** 或 **pnpm**；仓库含 `pnpm-lock.yaml`）  
- **PostgreSQL** >= 14  
- **Redis**（与 `core/settings.py` 中配置一致）  
- **uv**（推荐，用于安装 Python 依赖）

### 1. 数据库

```sql
CREATE DATABASE operation_brain;
```

### 2. 后端环境变量

1. 在 `backend/.env.current` 中设置当前环境，例如：`ENV=dev`（对应 `EnvSettings.env`，用于加载 `backend/.env.dev`）。  
2. 复制 `backend/.env.example` 为 `backend/.env.dev`（或 `prod`），并补全下列变量：

| 类别 | 变量（示例） | 说明 |
|------|----------------|------|
| 数据库 | `POSTGRES_*` | 主机、端口、用户、密码、库名 |
| Redis | `REDIS_*` | 主机、端口、密码、DB、键前缀、`REDIS_DEFAULT_TTL` |
| 阿里云短信 | `ALIYUN_ACCESS_KEY`、`ALIYUN_SECRET_KEY`、`SMS_SIGN_NAME`、`SMS_TEMPLATE_CODE` | 注册验证码发送 |
| JWT | `JWT_SECRET_KEY`、`JWT_ALGORITHM`（如 `HS256`）、`JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | 签发访问令牌 |

> **说明**：应用启动时会在 lifespan 中执行 `create_all` 并连接 Redis。生产环境建议以 **Alembic 迁移** 为单一事实来源，并视情况关闭或收紧自动建表行为。

### 3. 启动后端

```bash
cd backend
uv sync
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- 服务地址：`http://localhost:8000`  
- Swagger：`http://localhost:8000/docs`  

**数据库迁移（可选）**：

```bash
cd backend
# 生成修订（改模型后）
alembic revision --autogenerate -m "describe_change"
# 升级到最新
alembic upgrade head
```

### 4. 启动前端

```bash
cd frontend
npm install   # 或 pnpm install
npm run dev   # 或 pnpm dev
```

- 前端开发地址：`http://localhost:3000`  
- 请求默认 `baseURL` 为 `/api`，由 Vite 代理到 `http://localhost:8000`（路径会去掉 `/api` 前缀）。  
- 若部署到与后端不同源的环境，可设置环境变量 `VITE_API_BASE_URL` 指向真实 API 根路径。

### 5. 前端生产构建

```bash
cd frontend
npm run build
```

产物位于 `frontend/dist`。

## API 与约定

- **统一响应体**：业务成功时多为 `{ code, message, data }`（见 `schema/response.py` 与 `success_response`）。  
- **公开接口**（无需 Token）：`POST /users/register`、`POST /users/login`、`GET /users/send-verification-code`  
- **需鉴权接口**：在 `main.py` 中对 `protected_router` 统一注入 `get_current_user`，例如 `GET /users/me`  
- **前端鉴权**：Axios 请求头携带 `Bearer <token>`；HTTP 401 时清空 token 并跳转登录。

## 主题色

从项目 Logo 提取的双色方案：

| 色彩 | 色值 | 用途 |
|------|------|------|
| 科技蓝 | `#2196F3` | 主色、主要交互 |
| 生态绿 | `#4CAF50` | 辅助色、成功态 |

品牌区域常用渐变：`linear-gradient(135deg, #2196F3, #4CAF50)`。

## 后端说明摘要

- **多环境**：`.env.current` 决定加载 `.env.dev` 或 `.env.prod`。  
- **异步数据库**：`asyncpg` + SQLAlchemy 2 异步会话。  
- **模型基类**：`BaseModel` 提供 `id`（UUID）、时间戳、`is_deleted` 等公共字段。  
- **异常处理**：HTTP / 校验 / 未捕获异常统一处理，返回一致错误结构。  

## 前端说明摘要

- **UI**：Naive UI，中文语言包与主题色覆盖。  
- **状态**：Pinia；Token 与用户名等持久化策略见 `stores/user.ts`。  
- **路由**：`meta.public` 控制登录页；私有路由无 token 时重定向登录并带 `redirect`。  
- **样式**：Less 全局变量注入，便于主题与布局统一。  

## 常用命令

| 命令 | 说明 |
|------|------|
| `cd frontend && npm run dev` | 前端开发服务 |
| `cd frontend && npm run build` | 前端生产构建 |
| `cd frontend && npm run preview` | 预览构建产物 |
| `cd backend && uvicorn main:app --reload` | 后端开发服务 |
| `cd backend && alembic upgrade head` | 应用数据库迁移 |

## License

MIT
