from pydantic_settings import BaseSettings
from pydantic import computed_field


# 环境设置类，用于获取当前环境
class EnvSettings(BaseSettings):
    env: str = "dev"

    class Config:
        env_file = ".env.current"


class Settings(BaseSettings):
    # 数据库配置
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    # 阿里云配置
    ALIYUN_ACCESS_KEY: str
    ALIYUN_SECRET_KEY: str
    SMS_SIGN_NAME: str
    SMS_TEMPLATE_CODE: str

    # Redis配置
    REDIS_HOST: str
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str
    REDIS_DB: int = 0
    REDIS_KEY_PREFIX: str
    REDIS_DEFAULT_TTL: int

    # Token相关
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int

    # RAG / Qwen
    DASHSCOPE_API_KEY: str = ""
    DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    QWEN_CHAT_MODEL: str = "qwen-plus"
    QWEN_EMBEDDING_MODEL: str = "text-embedding-v4"
    EMBEDDING_DIM: int = 1024

    # 文件
    KNOWLEDGE_UPLOAD_DIR: str = "storage/knowledge"
    KNOWLEDGE_MAX_FILE_SIZE_MB: int = 50

    # 切块
    KNOWLEDGE_CHUNK_SIZE: int = 800
    KNOWLEDGE_CHUNK_OVERLAP: int = 120

    # 检索
    KNOWLEDGE_RETRIEVE_TOP_K: int = 5

    # 线程历史压缩
    THREAD_SUMMARY_TRIGGER_MSG_COUNT: int = 20
    THREAD_SUMMARY_TRIGGER_TOKEN_EST: int = 6000
    THREAD_KEEP_RECENT_MSGS: int = 8

    # 上下文压缩
    MAX_CONTEXT_CHARS: int = 12000
    CONTEXT_GROUP_CHARS: int = 3500

    # 构建异步数据库 URL
    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )

    class Config:
        # 让环境变量文件名根据环境变量动态加载
        env_file = f".env.{EnvSettings().env}"
        extra = "ignore"


def get_settings():
    return Settings()


env_settings = EnvSettings()
settings = get_settings()
