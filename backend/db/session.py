from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from core.settings import settings, env_settings
from sqlalchemy import MetaData, String, DateTime, SmallInteger, Column
from datetime import datetime
import uuid


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


class BaseModel(Base):
    # __abstract__ = True 表示该 SQLAlchemy 模型（BaseModel）是抽象基类，
    # 不会在数据库中创建对应表，只用于被其他具体模型继承。这样可以统一定义主键、时间等通用字段。
    __abstract__ = True

    id = Column(String(100), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(
        DateTime, default=datetime.now, nullable=False, comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False,
        comment="更新时间",
    )
    is_deleted = Column(
        SmallInteger, default=0, nullable=False, comment="是否删除(0: 正常, 1: 删除)"
    )


# 创建异步数据库引擎，使用配置中的 DATABASE_URL
# 如果环境为开发（dev），则输出 SQL 调试信息（echo=True)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=(env_settings.env == "dev"),
    # 连接池大小（默认是5个）
    pool_size=10,
    # 允许连接池最大的连接数（默认是10个）
    max_overflow=20,
    # 获得连接超时时间（默认是30s）
    pool_timeout=10,
    # 连接回收时间（默认是-1，代表永不回收）
    pool_recycle=3600,
    # 连接前是否预检查（默认为False）
    pool_pre_ping=True,
)

# 创建异步 Session 工厂
# expire_on_commit=False 表示 session 提交后实例不会过期
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
)


# 异步依赖，获取数据库 session，用于依赖注入（如 FastAPI 路由中）
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
