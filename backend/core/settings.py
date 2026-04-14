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
