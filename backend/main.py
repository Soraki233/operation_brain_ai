import logging

from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager

from fastapi.middleware.cors import CORSMiddleware
from router.users_router import public_router, protected_router
from core.redis import redis_manager
from core.deps import get_current_user
from db.session import AsyncSessionLocal
from repository.knowledge_repo import KnowledgeRepo
from core.exception_handler import (
    http_exception_handler,
    validation_exception_handler,
    global_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from router.knowledge_router import knowledge_router
from router.chat_router import chat_router


# 让自有模块的 logger.info 能打到终端；不动 uvicorn / sqlalchemy 自己的 logger。
# 使用 basicConfig(force=True) 覆盖默认 WARNING 级别。
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
    force=True,
)
# SQLAlchemy engine 的 INFO 很吵（每条 SQL 都打），关掉避免干扰 RAG/LLM 耗时日志
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await redis_manager.connect()
    # 启动时确保至少存在一个共享知识库
    async with AsyncSessionLocal() as db:
        await KnowledgeRepo.ensure_shared_knowledge_base(db)
    # 启动时兜底扫描：把上次意外中断 (热重载 / 进程被杀) 停在 pending / processing
    # 的文件重新推进，避免前端一直看到"待处理"。
    await KnowledgeRepo.requeue_unfinished_files()
    yield
    await redis_manager.close()


app = FastAPI(lifespan=lifespan)

app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 公开路由：注册、登录、发送验证码等，不需要 token
app.include_router(public_router)

# 需要鉴权的路由：全局注入 get_current_user 依赖
app.include_router(protected_router, dependencies=[Depends(get_current_user)])

app.include_router(knowledge_router, dependencies=[Depends(get_current_user)])

app.include_router(chat_router, dependencies=[Depends(get_current_user)])
