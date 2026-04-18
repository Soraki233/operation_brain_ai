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
| **前端扩展** | 本地文档预览：`mammoth`（Word）· `xlsx`（Excel）· Markdown 渲染 |
| **后端** | Python 3.13+ · FastAPI · SQLAlchemy 2（async）· PostgreSQL · Pydantic Settings |
| **数据迁移** | Alembic（`psycopg2-binary` 用于迁移脚本同步元数据） |
| **缓存 / 会话** | Redis（验证码等） |
| **向量数据库** | PostgreSQL + `pgvector` 扩展（`langchain-postgres` PGVector） |
| **AI / LLM** | 阿里云 DashScope（Qwen）OpenAI 兼容协议（`langchain-openai`） |
| **短信** | 阿里云号码认证 / 短信服务（`alibabacloud-dypnsapi20170525`） |
| **认证** | JWT（`python-jose`）· bcrypt 密码哈希 |

## 当前能力概览

| 模块 | 说明 |
|------|------|
| **用户与认证** | 手机号注册 / 登录、短信验证码、JWT 鉴权、`/users/me` 获取当前用户 |
| **工作台** | 登录后首页仪表盘（占位统计，可对接真实监控数据） |
| **知识库** | 知识库 / 文件夹 / 文件完整 CRUD；多格式文件上传并异步入库（PDF · DOCX · DOC · XLSX · XLS · MD · TXT）；LLM 结构感知切块；PGVector 向量存储；文件预览与下载 |
| **AI 对话** | 多会话管理；RAG 检索增强（PGVector 召回 + 知识库过滤）；SSE 流式输出；引用来源展示；对话历史自动压缩 |

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
│   │   └── models/             # User · Knowledge · Chat 等 ORM 模型
│   ├── router/
│   │   ├── users_router.py     # 用户注册/登录/鉴权路由
│   │   ├── knowledge_router.py # 知识库/文件夹/文件 CRUD + 上传/下载
│   │   └── chat_router.py      # 会话 CRUD + SSE 流式问答
│   ├── repository/
│   │   ├── users_repo.py       # 用户与验证码数据访问
│   │   ├── knowledge_repo.py   # 知识库数据访问
│   │   └── chat_repo.py        # 对话数据访问
│   ├── service/
│   │   ├── sms_service.py           # 阿里云短信发送
│   │   ├── vector_store_service.py  # PGVector 向量存储（DashScope Embedding）
│   │   ├── knowledge_ingest_service.py  # 文件摄取：解析→切块→入库
│   │   ├── structure_analyzer.py    # LLM 结构感知切分（章节/条款/段落/表格）
│   │   └── agent_service.py         # RAG Agent：检索 + Qwen 推理 + 历史压缩
│   ├── schema/                 # Pydantic 模型（含统一 ResponseModel）
│   ├── storage/
│   │   └── knowledge/          # 上传文件本地存储（按知识库 UUID 分目录）
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
│       ├── api/                # users · chat · knowledge · core
│       ├── router/index.ts     # 登录 / 注册 / 首页子路由
│       ├── stores/
│       ├── types/              # TypeScript 类型定义（knowledge 等）
│       ├── utils/              # request · Markdown 渲染 · 知识库预览工具
│       ├── styles/
│       └── views/
│           ├── Login/Login.vue
│           ├── Register/Register.vue
│           ├── Home/Home.vue
│           ├── Dashboard/
│           ├── Knowledge/      # 知识库页面与组件（含上传/预览/文件夹管理）
│           └── Chat/           # AI 对话页面与组件（含侧边栏/消息/引用卡片）
│
└── README.md
```

## 快速开始

### 环境要求

- **Python** >= 3.13  
- **Node.js** >= 18（可使用 **npm** 或 **pnpm**；仓库含 `pnpm-lock.yaml`）  
- **PostgreSQL** >= 14，并安装 **pgvector** 扩展  
- **Redis**（与 `core/settings.py` 中配置一致）  
- **uv**（推荐，用于安装 Python 依赖）

### 1. 数据库

```sql
-- 创建业务数据库
CREATE DATABASE operation_brain_ai_dev;

-- 启用向量扩展（需在目标库中执行）
\c operation_brain_ai_dev
CREATE EXTENSION IF NOT EXISTS vector;
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
| DashScope / Qwen | `DASHSCOPE_API_KEY`、`DASHSCOPE_BASE_URL`、`QWEN_CHAT_MODEL`、`QWEN_EMBEDDING_MODEL`、`EMBEDDING_DIM` | AI 推理与向量化 |
| 文件存储 | `KNOWLEDGE_UPLOAD_DIR`、`KNOWLEDGE_MAX_FILE_SIZE_MB` | 上传文件本地路径与大小限制 |
| 知识库切块 | `KNOWLEDGE_CHUNK_SIZE`、`KNOWLEDGE_CHUNK_OVERLAP` | 文本分块参数 |
| 知识库检索 | `KNOWLEDGE_RETRIEVE_TOP_K` | 向量召回 Top-K 数量 |
| 结构分析 | `STRUCTURE_ANALYZER_ENABLED` | 是否启用 LLM 结构感知切分（`true`/`false`） |
| 对话历史压缩 | `THREAD_SUMMARY_TRIGGER_MSG_COUNT`、`THREAD_SUMMARY_TRIGGER_TOKEN_EST`、`THREAD_KEEP_RECENT_MSGS` | 触发摘要压缩的阈值 |
| Agent 参数 | `AGENT_MAX_TOKENS`、`AGENT_TEMPERATURE`、`AGENT_EVIDENCE_MAX_TOKENS` | 推理 token 上限与温度 |

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

- **统一响应体**：业务成功时为 `{ code, message, data }`（见 `schema/response.py` 与 `success_response`）。  
- **公开接口**（无需 Token）：`POST /users/register`、`POST /users/login`、`GET /users/send-verification-code`  
- **需鉴权接口**：在 `main.py` 中对 `protected_router` 统一注入 `get_current_user`，例如 `GET /users/me`、所有知识库与对话接口  
- **前端鉴权**：Axios 请求头携带 `Bearer <token>`；HTTP 401 时清空 token 并跳转登录  
- **SSE 流式对话**：`POST /chat/threads/{thread_id}/ask`，返回 `text/event-stream`；事件类型包括 `thinking`（证据分析）、`token`（正文 token）、`citations`（引用来源）、`done`

## 知识库文件摄取流程

```
上传文件
  └─ knowledge_router → 异步后台任务
       └─ KnowledgeIngestService
            ├─ load_file()       解析原始文本
            │    ├─ PDF         PyPDFLoader
            │    ├─ DOCX/DOC    python-docx → docx2txt → ZIP 直解（兼容 WPS）
            │    ├─ XLSX/XLS    pandas（自动识别多级表头，行级 Document）
            │    └─ MD/TXT      直接读文本
            ├─ split_documents() 切块
            │    ├─ Excel 行级 Document → 直接入库（不二次切分）
            │    └─ 其余 → StructureAnalyzer（LLM 结构感知）→ 超时/失败退化为 RecursiveCharacterTextSplitter
            └─ ingest_file()    按批（10条/批）写入 PGVector
```

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
- **向量数据库**：`langchain-postgres` PGVector，存储于同一 PostgreSQL 实例，collection 名为 `knowledge_chunks`；每条向量携带 `kb_id`、`file_id`、`chunk_index` 等 JSONB metadata 便于过滤。  
- **RAG Agent**：`AgentService` 先检索相关 chunk（按 `kb_ids` 过滤），再用 `evidence_llm` 做证据分析（streaming 供前端展示"思考"），最后交主 LLM 生成回答；历史过长时触发摘要压缩。  
- **模型基类**：`BaseModel` 提供 `id`（UUID）、时间戳、`is_deleted` 等公共字段。  
- **异常处理**：HTTP / 校验 / 未捕获异常统一处理，返回一致错误结构。  

## 前端说明摘要

- **UI**：Naive UI，中文语言包与主题色覆盖。  
- **状态**：Pinia；Token 与用户名等持久化策略见 `stores/user.ts`。  
- **路由**：`meta.public` 控制登录页；私有路由无 token 时重定向登录并带 `redirect`。  
- **样式**：Less 全局变量注入，便于主题与布局统一。  
- **知识库**：`KnowledgeUploadModal` 多文件上传，轮询文件状态（`pending`→`processing`→`done`/`failed`）；`KnowledgePreviewDrawer` 本地渲染 Word/Excel/MD 预览。  
- **AI 对话**：`ChatInputBar` 支持 @ 知识库选择；`ChatMessageRow` 展示 AI 引用来源卡片；SSE 流式接收 `thinking` / `token` / `citations` 事件。  

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
