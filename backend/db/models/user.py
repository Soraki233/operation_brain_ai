from sqlalchemy import Column, String, SmallInteger
from db.session import BaseModel


class User(BaseModel):
    __tablename__ = "user"

    username = Column(String(50), unique=True, index=True, comment="用户名")

    nickname = Column(String(50), comment="昵称")

    phone = Column(String(11), comment="手机号")

    hashed_password = Column(String(100), comment="加密后的密码")

    is_active = Column(
        SmallInteger,
        default=True,
        comment="	是否活跃 (1: 正常/活跃, 0: 禁用/不活跃)",
    )

    role_id = Column(String(100), comment="角色ID")


class UserRole(BaseModel):
    __tablename__ = "user_role"
    user_id = Column(String(100), comment="用户ID")

    role_name = Column(String(100), default="运行人员", comment="角色名称")

    role_key = Column(String(100), default="staff", comment="角色权限字符串 ")
