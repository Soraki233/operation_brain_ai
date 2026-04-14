from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from db.session import engine, Base, get_db
from fastapi.middleware.cors import CORSMiddleware
import db.models  # noqa: F401 — 确保所有模型注册到 Base.metadata
from router.users_router import router as users_router


# 在fastAPI启动时，创建数据库表，app.on_event已弃用
@asynccontextmanager
async def lifespan(_: FastAPI):
    # 在数据库中创建所有模型对应的表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


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

# if __name__ == "__main__":
#     # 启动FastAPI应用
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
