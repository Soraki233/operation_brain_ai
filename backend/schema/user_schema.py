from pydantic import BaseModel, Field, StringConstraints, field_validator
from typing import Annotated
import re

Phone = Annotated[str, StringConstraints(pattern=r"^1[3-9]\d{9}$")]
PHONE_REGEX = r"^1[3-9]\d{9}$"


class UserRegisterSchema(BaseModel):
    username: str = Field(..., description="用户名")
    phone: str = Field(..., description="手机号")
    verification_code: str = Field(..., description="验证码")
    password: str = Field(..., description="密码")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.match(PHONE_REGEX, v):
            raise ValueError("手机号格式不正确")
        return v


class SendCodeSchema(BaseModel):
    phone: str = Field(..., description="手机号")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.match(PHONE_REGEX, v):
            raise ValueError("手机号格式不正确")
        return v
