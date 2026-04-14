from sqlalchemy import Column, String, SmallInteger
from db.session import BaseModel


class User(BaseModel):
    __tablename__ = "user"

    username = Column(String(50), unique=True, index=True, comment="用户名", nullable=False)

    nickname = Column(String(50), nullable=True, comment="昵称")

    phone = Column(String(11), comment="手机号", nullable=False)

    hashed_password = Column(String(100), comment="加密后的密码", nullable=False)

    is_active = Column(
        SmallInteger,
        default=1,
        comment="	是否活跃 (1: 正常/活跃, 0: 禁用/不活跃)",
        nullable=False,
    )

    role_id = Column(String(100), comment="角色ID", nullable=False)


class UserRole(BaseModel):
    __tablename__ = "user_role"

    role_name = Column(String(100), default="运行人员", comment="角色名称")

    role_key = Column(String(100), default="staff", comment="角色权限字符串 ")
