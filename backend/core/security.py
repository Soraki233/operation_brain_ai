from bcrypt._bcrypt import hashpw, checkpw, gensalt
from typing import Any
from core.settings import settings
from jose import jwt
from datetime import datetime, timedelta, timezone


def get_password_hash(password: str) -> str:
    """
    对明文密码进行哈希，返回加密后的密码字符串
    :param password: 明文密码
    :return: 加密后的密码
    """
    return hashpw(password.encode("utf-8"), gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    校验明文密码与加密后的密码是否一致
    :param plain_password: 用户输入的明文密码
    :param hashed_password: 数据库存储的加密密码
    :return: 一致返回True，否则False
    """
    return checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    """
    生成 JWT 访问令牌（Access Token）

    :param data:          需要写入 token 的数据（Payload），如用户信息。
    :param expires_delta: 过期时间段。如果不传，则使用默认设置中的过期分钟数（settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES）。
    :return:              编码后的 JWT 字符串。
    """
    to_encode = data.copy()  # 复制传入的数据，避免修改原始数据
    now = datetime.now(timezone.utc)  # 获取当前 UTC 时间

    # 计算过期时间。如果调用方未提供 expires_delta，则使用默认值
    expire = now + (
        expires_delta
        if expires_delta
        else timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    # 在 payload 中加入过期时间(exp)和签发时间(iat)
    to_encode.update(
        {
            "exp": expire,  # JWT 标准声明，过期时间 (exp)
            "iat": now,  # JWT 标准声明，签发时间 (issued at)
        }
    )

    # 使用密钥和算法对 payload 进行编码，生成 JWT
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    print("encoded_jwt", encoded_jwt)
    return encoded_jwt

def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )