from fastapi import APIRouter, Depends, HTTPException
from db.session import AsyncSession, get_db
from schema.user_schema import UserRegisterSchema, CreateUserRoleSchema
from repository.users_repo import UsersRepo
from core.reponse import success_response

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
    print("验证码", register_data.verification_code)
    print("手机号", register_data.phone)
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
    staff_role = await UsersRepo.get_role_by_key("staff", db)
    # 如果角色不存在，则创建角色
    if not staff_role:
        # 创建角色
        create_user_role_data = CreateUserRoleSchema(role_name="运行人员", role_key="staff")
        # 创建角色
        staff_role = await UsersRepo.create_user_role(create_user_role_data, db)
    # 设置用户角色ID
    user.role_id = staff_role.id
    # 提交事务
    await db.commit()
    # 刷新用户
    await db.refresh(user)
    return success_response(message="注册成功", data=user)


@router.get("/send-verification-code", summary="发送验证码")
async def send_verification_code(phone: str, db: AsyncSession = Depends(get_db)):
    return await UsersRepo.send_verification_code(phone)
