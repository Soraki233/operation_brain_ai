from fastapi import APIRouter, Depends, HTTPException
from db.session import AsyncSession, get_db
from schema.user_schema import UserRegisterSchema
from repository.users_repo import UsersRepo

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", summary="创建用户")
async def register(
    register_data: UserRegisterSchema, db: AsyncSession = Depends(get_db)
):
    # 验证手机号和用户名是否存在
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
    # 获取角色为staff的角色ID
    staff_role = await UsersRepo.get_role_by_name("staff", db)
    user.role_id = staff_role.id
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/send-verification-code", summary="发送验证码")
async def send_verification_code(phone: str, db: AsyncSession = Depends(get_db)):
    return await UsersRepo.send_verification_code(phone)
