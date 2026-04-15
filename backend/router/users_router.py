from fastapi import APIRouter, Depends, HTTPException
from db.session import AsyncSession, get_db
from db.models.user import User
from schema.user_schema import (
    UserRegisterSchema,
    UserResponseSchema,
    LoginRequestSchema,
    TokenResponseSchema,
)
from repository.users_repo import UsersRepo
from core.reponse import success_response
from core.exception_handler import http_exception_handler
from core.security import verify_password, create_access_token
from core.deps import get_current_user

# ── 公开路由（无需 token） ──
public_router = APIRouter(prefix="/users", tags=["users"])


@public_router.post("/register", summary="创建用户")
async def register(
    register_data: UserRegisterSchema, db: AsyncSession = Depends(get_db)
):
    is_phone_exists = await UsersRepo.get_user_by_phone(register_data.phone, db)
    is_username_exists = await UsersRepo.get_user_by_username(
        register_data.username, db
    )
    verification_code = await UsersRepo.verify_verification_code(
        register_data.phone, register_data.verification_code
    )
    if is_phone_exists:
        raise HTTPException(status_code=400, detail="手机号已存在")
    if is_username_exists:
        raise HTTPException(status_code=400, detail="用户名已存在")
    if not verification_code:
        raise HTTPException(status_code=400, detail="验证码错误")

    user = await UsersRepo.create_user(register_data, db)
    if not user:
        return http_exception_handler(HTTPException(status_code=400, detail="注册失败"))
    return success_response(
        message="注册成功", data=UserResponseSchema.model_validate(user)
    )


@public_router.get("/send-verification-code", summary="发送验证码")
async def send_verification_code(phone: str):
    return await UsersRepo.send_verification_code(phone)


@public_router.post("/login", summary="登录")
async def login(login_data: LoginRequestSchema, db: AsyncSession = Depends(get_db)):
    user = await UsersRepo.get_user_by_phone(login_data.phone, db)
    if not user or not verify_password(login_data.password, user.hashed_password):
        return http_exception_handler(
            HTTPException(status_code=400, detail="用户不存在或密码错误")
        )
    access_token = create_access_token(
        UserResponseSchema.model_validate(user).model_dump()
    )
    return success_response(
        message="登录成功",
        data=TokenResponseSchema(
            access_token=access_token, user=UserResponseSchema.model_validate(user)
        ),
    )


# ── 需鉴权路由（需要 token） ──
# 这里的路由会在 main.py 中通过 dependencies=[Depends(get_current_user)] 统一注入鉴权
protected_router = APIRouter(prefix="/users", tags=["users"])


@protected_router.get("/me", summary="获取当前用户信息")
async def get_me(current_user: User = Depends(get_current_user)):
    return success_response(
        data=UserResponseSchema.model_validate(current_user)
    )
