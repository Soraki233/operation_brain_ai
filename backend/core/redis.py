import json
from typing import Any, Optional

import redis.asyncio as redis
from redis.exceptions import RedisError

from core.settings import settings


class RedisManager:
    def __init__(self) -> None:
        self._client: Optional[redis.Redis] = None

    async def connect(self) -> None:
        """
        初始化 Redis 连接。
        """
        if self._client is not None:
            return

        self._client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            encoding="utf-8",
            decode_responses=True,
        )
        # 启动时检测连接
        await self._client.ping()

    async def close(self) -> None:
        """
        关闭 Redis 连接。
        """
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def get_client(self) -> redis.Redis:
        """
        获取底层 Redis 客户端。
        """
        if self._client is None:
            raise RuntimeError("Redis 未初始化，请先执行 connect()")
        return self._client

    def make_key(self, key: str) -> str:
        """
        统一 key 前缀。
        """
        return f"{settings.REDIS_KEY_PREFIX}{key}"

    # ---------------------------
    # 基础字符串操作
    # ---------------------------
    async def set(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None,
    ) -> bool:
        client = self.get_client()
        real_key = self.make_key(key)

        if isinstance(value, (dict, list, tuple, bool, int, float)):
            value = json.dumps(value, ensure_ascii=False)

        try:
            return await client.set(real_key, value, ex=ex)
        except RedisError as e:
            raise RuntimeError(f"Redis set 失败: {e}") from e

    async def get(self, key: str) -> Optional[str]:
        client = self.get_client()
        real_key = self.make_key(key)

        try:
            return await client.get(real_key)
        except RedisError as e:
            raise RuntimeError(f"Redis get 失败: {e}") from e

    async def delete(self, key: str) -> int:
        client = self.get_client()
        real_key = self.make_key(key)

        try:
            return await client.delete(real_key)
        except RedisError as e:
            raise RuntimeError(f"Redis delete 失败: {e}") from e

    async def exists(self, key: str) -> int:
        client = self.get_client()
        real_key = self.make_key(key)

        try:
            return await client.exists(real_key)
        except RedisError as e:
            raise RuntimeError(f"Redis exists 失败: {e}") from e

    async def expire(self, key: str, seconds: int) -> bool:
        client = self.get_client()
        real_key = self.make_key(key)

        try:
            return await client.expire(real_key, seconds)
        except RedisError as e:
            raise RuntimeError(f"Redis expire 失败: {e}") from e

    async def incr(self, key: str, amount: int = 1) -> int:
        client = self.get_client()
        real_key = self.make_key(key)

        try:
            return await client.incr(real_key, amount)
        except RedisError as e:
            raise RuntimeError(f"Redis incr 失败: {e}") from e

    # ---------------------------
    # JSON 操作
    # ---------------------------
    async def set_json(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None,
    ) -> bool:
        client = self.get_client()
        real_key = self.make_key(key)

        try:
            payload = json.dumps(value, ensure_ascii=False)
            return await client.set(real_key, payload, ex=ex)
        except RedisError as e:
            raise RuntimeError(f"Redis set_json 失败: {e}") from e

    async def get_json(self, key: str) -> Any:
        client = self.get_client()
        real_key = self.make_key(key)

        try:
            value = await client.get(real_key)
            if value is None:
                return None
            return json.loads(value)
        except RedisError as e:
            raise RuntimeError(f"Redis get_json 失败: {e}") from e

    # ---------------------------
    # Hash 操作
    # ---------------------------
    async def hset(self, key: str, mapping: dict[str, Any]) -> int:
        client = self.get_client()
        real_key = self.make_key(key)

        new_mapping = {}
        for k, v in mapping.items():
            if isinstance(v, (dict, list, tuple, bool)):
                new_mapping[k] = json.dumps(v, ensure_ascii=False)
            else:
                new_mapping[k] = v

        try:
            return await client.hset(real_key, mapping=new_mapping)
        except RedisError as e:
            raise RuntimeError(f"Redis hset 失败: {e}") from e

    async def hgetall(self, key: str) -> dict[str, Any]:
        client = self.get_client()
        real_key = self.make_key(key)

        try:
            return await client.hgetall(real_key)
        except RedisError as e:
            raise RuntimeError(f"Redis hgetall 失败: {e}") from e


redis_manager = RedisManager()
