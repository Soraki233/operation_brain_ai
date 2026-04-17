from pydantic import BaseModel, Field, StringConstraints, field_validator
from typing import Annotated
import re

Phone = Annotated[str, StringConstraints(pattern=r"^1[3-9]\d{9}$")]
PHONE_REGEX = r"^1[3-9]\d{9}$"


class UserRegisterSchema(BaseModel):
    username: str = Field(..., description="用户名")
    phone: str = Field(..., description="手机号")
    verification_code: str = Field(..., description="验证码", alias="verificationCode")
    password: str = Field(..., description="密码")
    confirm_password: str = Field(..., description="确认密码", alias="confirmPassword")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.match(PHONE_REGEX, v):
            raise ValueError("手机号格式不正确")
        return v


class UserCreateSchema(BaseModel):
    username: str = Field(..., description="用户名")
    phone: str = Field(..., description="手机号")
    password: str = Field(..., description="密码")
    confirm_password: str = Field(..., description="确认密码")
    role_id: str = Field(..., description="角色ID")


class CreateUserRoleSchema(BaseModel):
    role_name: str = Field(default="运行人员", description="角色名称")
    role_key: str = Field(default="staff", description="角色权限字符串")


class UserResponseSchema(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    username: str
    phone: str
    nickname: str | None = None
    is_active: int
    role_id: str


class SendCodeSchema(BaseModel):
    phone: str = Field(..., description="手机号")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.match(PHONE_REGEX, v):
            raise ValueError("手机号格式不正确")
        return v


class LoginRequestSchema(BaseModel):
    phone: str = Field(..., description="手机号")
    password: str = Field(..., min_length=6, max_length=32, description="密码")


class TokenResponseSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponseSchema
