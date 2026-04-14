from passlib.context import CryptContext  # 用于密码哈希和验证
from jose import jwt                      # 用于JWT的编码和解码
from datetime import datetime, timedelta  # 用于时间相关操作

# JWT 设置
SECRET_KEY = "your-secret-key"          # 应用的密钥，用于签名JWT
ALGORITHM = "HS256"                    # JWT所用的加密算法
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # Token过期时间：24小时

# 密码哈希上下文配置，这里采用bcrypt算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 密码加密
def hash_password(password: str):
    """
    使用bcrypt算法对明文密码进行哈希加密
    :param password: 明文密码
    :return: 哈希值
    """
    return pwd_context.hash(password)

# 密码验证
def verify_password(plain, hashed):
    """
    验证明文密码和哈希后的密码是否一致
    :param plain: 明文密码
    :param hashed: 已加密的密码哈希
    :return: 匹配结果（True/False）
    """
    return pwd_context.verify(plain, hashed)

# 生成JWT访问令牌
def create_access_token(data: dict):
    """
    创建JWT访问令牌，设置过期信息
    :param data: 要编码的数据（一般为用户信息字典）
    :return: JWT Token字符串
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# 解码JWT令牌
def decode_token(token: str):
    """
    解码JWT令牌并返回其中包含的数据
    :param token: 前端传入的JWT Token字符串
    :return: 解码后的数据（字典）
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])