from passlib.context import CryptContext

# 创建一个密码上下文，用于安全地处理密码的哈希和校验，采用 bcrypt 算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """
    对明文密码进行哈希，返回加密后的密码字符串
    :param password: 明文密码
    :return: 加密后的密码
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    校验明文密码与加密后的密码是否一致
    :param plain_password: 用户输入的明文密码
    :param hashed_password: 数据库存储的加密密码
    :return: 一致返回True，否则False
    """
    return pwd_context.verify(plain_password, hashed_password)