from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager

from fastapi.middleware.cors import CORSMiddleware
from router.knowledge_router import router as knowledge_router
from router.users_router import public_router, protected_router
from core.redis import redis_manager
from core.deps import get_current_user
from core.exception_handler import (
    http_exception_handler,
    validation_exception_handler,
    global_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


@asynccontextmanager
async def lifespan(_: FastAPI):
    await redis_manager.connect()
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
