from pydantic import BaseModel, Field


class UserRegisterSchema(BaseModel):
    phone: str = Field(..., description="用户名")
    verification_code: str = Field(..., description="验证码")
    password: str = Field(..., description="密码")
