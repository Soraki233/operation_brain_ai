# 后端结构说明

本文档概括 **operation_brain_ai** 项目后端（`backend/`）的目录组织、技术栈与各层职责，便于快速上手与扩展。

---

## 技术栈

| 类别 | 技术 |
|------|------|
| Web 框架 | FastAPI（异步） |
| ORM | SQLAlchemy 2.x + **asyncpg**（PostgreSQL 异步驱动） |
| 数据库 | PostgreSQL |
| 缓存 | Redis（`redis.asyncio`） |
| 配置 | `pydantic-settings`，按环境加载 `.env.{env}`（由 `.env.current` 中的 `env` 决定，默认 `dev`） |
| 迁移 | Alembic |
| 认证 | JWT（`python-jose`）+ HTTP Bearer；密码 **bcrypt** |
| 短信 | 阿里云 Dypnsapi（`alibabacloud-dypnsapi20170525`） |
| 包管理 | `uv` / `pyproject.toml`，Python **≥ 3.13** |

---

## 目录结构（概览）

```
backend/
├── main.py                 # FastAPI 应用入口：生命周期、中间件、路由挂载、异常处理
├── pyproject.toml          # 依赖与项目元数据
├── alembic.ini             # Alembic 配置
├── alembic/                # 数据库迁移脚本
│   ├── env.py
│   └── versions/
├── core/                   # 横切能力：配置、安全、Redis、依赖注入、统一响应与异常
│   ├── settings.py         # 环境变量与 DATABASE_URL 等
│   ├── security.py         # 密码哈希、JWT 签发与解析
│   ├── redis.py            # Redis 连接与通用封装（redis_manager）
│   ├── deps.py             # get_current_user 等 FastAPI 依赖
│   ├── reponse.py          # success_response / error_response（文件名拼写为 reponse）
│   └── exception_handler.py # HTTP / 校验 / 全局异常 → JSON 响应
├── db/
│   ├── session.py          # AsyncEngine、AsyncSession、Base / BaseModel、get_db
│   └── models/             # SQLAlchemy 模型
│       ├── __init__.py     # 导出 User、UserRole
│       └── user.py         # User、UserRole 表定义
├── schema/                 # Pydantic 模型：入参、出参、通用响应壳
│   ├── response.py         # ResponseModel[T]
│   └── user_schema.py      # 注册、登录、用户展示等 Schema
├── repository/             # 数据访问层（面向表/聚合的查询与写入）
│   └── users_repo.py       # 用户与角色、验证码相关持久化与 Redis 逻辑
├── service/                # 外部服务封装
│   └── sms_service.py      # 阿里云短信发送
├── router/                 # API 路由（按业务拆分）
│   └── users_router.py     # 用户：公开路由 + 需鉴权路由
└── .env.example            # 环境变量示例（实际使用 .env.dev / .env.prod 等）
```

当前业务路由主要围绕 **用户模块**；知识库、对话等若接入后端，可按相同分层增加 `router/`、`repository/`、`service/` 与 `db/models/`。

---

## 应用入口（`main.py`）

1. **生命周期（`lifespan`）**  
   - 启动：`create_all` 同步元数据到数据库（开发便捷；生产通常以 Alembic 为准）。  
   - 连接 **Redis**（`redis_manager.connect()`）。  
   - 关闭：断开 Redis。

2. **异常处理**  
   - `HTTPException`、`RequestValidationError`、未捕获 `Exception` 统一转为 JSON（与 `schema/response.py` 风格可对照使用）。

3. **CORS**  
   - 当前为宽松配置（`allow_origins=["*"]`），上线建议按前端域名收紧。

4. **路由挂载**  
   - **公开路由**：`public_router`（如注册、登录、发验证码），无需 Token。  
   - **保护路由**：`protected_router`，在 `include_router` 时统一注入 `Depends(get_current_user)`。

---

## 分层职责

| 层级 | 路径 | 职责 |
|------|------|------|
| **路由** | `router/` | 定义 URL、HTTP 方法、依赖注入；薄层，组合调用 Repository / Service。 |
| **Schema** | `schema/` | 请求体验证、响应结构；与 ORM 模型解耦。 |
| **Repository** | `repository/` | 异步 SQLAlchemy 查询/事务；可调用 Redis、其他底层 API。 |
| **Service** | `service/` | 第三方 SDK（短信等）、复杂领域流程的可复用封装。 |
| **DB 模型** | `db/models/` | 表结构；继承 `BaseModel` 获得 `id`、`created_at`、`updated_at`、`is_deleted`。 |
| **Core** | `core/` | 配置、JWT、密码、Redis、当前用户解析、统一成功/错误响应包装。 |

---

## 数据库与会话（`db/session.py`）

- **`Base`**：`DeclarativeBase`，统一命名约定（索引、外键等）。  
- **`BaseModel`**：抽象基类，公共字段：`id`（UUID 字符串）、时间戳、软删标记 `is_deleted`。  
- **`engine`**：`create_async_engine(settings.DATABASE_URL, ...)`，`dev` 环境可 `echo` SQL。  
- **`get_db`**：请求级 `AsyncSession` 依赖，用于路由或下层 Repository。

---

## 认证与当前用户（`core/deps.py`）

- 客户端携带 **`Authorization: Bearer <JWT>`**。  
- `get_current_user`：解析 JWT → 取用户 `id` → 查库 → 校验 `is_active`。  
- 保护路由在 `main.py` 中统一挂载该依赖，各接口可再显式 `Depends(get_current_user)` 获取 `User` 实例。

---

## API 一览（用户模块，`router/users_router.py`）

前缀均为 **`/users`**，`tags=["users"]`。

**公开（无需 Token）**

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/users/register` | 注册（校验手机号验证码、用户名/手机号唯一性） |
| GET | `/users/send-verification-code` | 发送短信验证码（Query: `phone`） |
| POST | `/users/login` | 登录，返回 `access_token` 与用户信息 |

**需鉴权（全局已挂 `get_current_user`）**

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/users/me` | 当前登录用户信息 |

---

## 统一响应格式

- **`schema/response.py`**：`ResponseModel` 含 `code`、`message`、`data`。  
- **`core/reponse.py`**：`success_response` / `error_response` 等用于组装成功或业务错误响应。  
- 部分路径仍通过 **`HTTPException`** + `http_exception_handler` 返回 `code` + `message` + `data: null` 结构，与成功响应字段风格一致，便于前端统一处理。

---

## 配置说明（`core/settings.py`）

- 先读 **`EnvSettings`**（`.env.current`）得到 `env`（如 `dev` / `prod`）。  
- 再读 **`.env.{env}`** 加载 `Settings`：PostgreSQL、Redis、阿里云短信、JWT 等。  
- **`DATABASE_URL`** 由 `computed_field` 拼接为 `postgresql+asyncpg://...`。

本地开发需准备对应 env 文件，可参考 **`.env.example`**。

---

## 数据库迁移（Alembic）

- 配置见 **`alembic.ini`** 与 **`alembic/env.py`**。  
- 版本脚本在 **`alembic/versions/`**（如初始化表、角色相关迁移）。  
- 模型变更后应生成新版本迁移，并在部署流程中执行 `alembic upgrade head`。

---

## 扩展建议

新增业务模块时，推荐顺序：

1. 在 `db/models/` 定义模型并在 `db/models/__init__.py` 导出（供 Alembic / `create_all` 发现）。  
2. 编写 Alembic 迁移。  
3. 在 `schema/` 增加请求/响应模型。  
4. 在 `repository/` 实现数据访问。  
5. 在 `router/` 增加 `APIRouter`，于 `main.py` 中按是否鉴权分别 `include_router`。

---


