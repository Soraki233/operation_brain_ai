from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from db.session import engine, Base, get_db
from fastapi.middleware.cors import CORSMiddleware
import db.models  # noqa: F401 — 确保所有模型注册到 Base.metadata
from router.users_router import router as users_router
from core.redis import redis_manager
from repository.users_repo import UsersRepo
from db.session import AsyncSession


# 在fastAPI启动时，创建数据库表，app.on_event已弃用
@asynccontextmanager
async def lifespan(_: FastAPI):
    # 在数据库中创建所有模型对应的表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await redis_manager.connect()
    yield
    await redis_manager.close()


app = FastAPI(lifespan=lifespan, dependencies=[Depends(get_db)])
# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)


@app.get("/sms")
async def to_send_sms(db: AsyncSession = Depends(get_db)):
    return await UsersRepo.create_user_role(db)
