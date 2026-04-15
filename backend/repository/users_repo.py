from typing import Dict
from db.session import AsyncSession
from db.models import User as UserModel, UserRole as UserRoleModel
from sqlalchemy import select
from schema.user_schema import UserRegisterSchema, CreateUserRoleSchema
from core.security import get_password_hash
from core.redis import redis_manager
import random
from service.sms_service import AliyunSmsService
from core.reponse import success_response, error_response


class UsersRepo:
    # 根据手机号获取用户
    @staticmethod
    async def get_user_by_phone(phone: str, db: AsyncSession) -> UserModel | None:
        result = await db.execute(select(UserModel).where(UserModel.phone == phone))
        return result.scalar_one_or_none()

    # 根据用户名获取用户
    @staticmethod
    async def get_user_by_username(username: str, db: AsyncSession) -> UserModel | None:
        result = await db.execute(
            select(UserModel).where(UserModel.username == username)
        )
        return result.scalar_one_or_none()

    # 创建用户
    @staticmethod
    async def create_user(user_data: UserRegisterSchema, db: AsyncSession) -> UserModel:

        # 获取角色为staff的角色ID
        staff_role = await UsersRepo.get_role_by_key("staff", db)
        # 如果角色不存在，则创建角色
        if not staff_role:
            # 创建角色
            create_user_role_data = CreateUserRoleSchema(
                role_name="运行人员", role_key="staff"
            )
            # 创建角色
            staff_role = await UsersRepo.create_user_role(create_user_role_data, db)
            # 设置用户角色ID
        user = UserModel(
            phone=user_data.phone,
            username=user_data.username,
            hashed_password=get_password_hash(user_data.password),
            role_id=staff_role.id,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    # 创建用户角色
    @staticmethod
    async def create_user_role(
        user_role_data: CreateUserRoleSchema, db: AsyncSession
    ) -> UserRoleModel:
        # 验证角色是否存在
        is_role_exists_key = await UsersRepo.get_role_by_key(
            user_role_data.role_key, db
        )
        # 如果角色存在，则返回角色
        if is_role_exists_key:
            return is_role_exists_key
        is_role_exists_name = await UsersRepo.get_role_by_name(
            user_role_data.role_name, db
        )
        # 如果角色存在，则返回角色
        if is_role_exists_name:
            return is_role_exists_name
        # 创建角色
        user_role = UserRoleModel(
            role_name=user_role_data.role_name,
            role_key=user_role_data.role_key,
        )
        db.add(user_role)
        await db.commit()
        await db.refresh(user_role)
        return user_role

    # 根据角色名称获取角色
    @staticmethod
    async def get_role_by_name(
        role_name: str, db: AsyncSession
    ) -> UserRoleModel | None:
        result = await db.execute(
            select(UserRoleModel).where(UserRoleModel.role_name == role_name)
        )
        return result.scalar_one_or_none()

    # 根据角色key
    @staticmethod
    async def get_role_by_key(role_key: str, db: AsyncSession) -> UserRoleModel | None:
        result = await db.execute(
            select(UserRoleModel).where(UserRoleModel.role_key == role_key)
        )
        return result.scalar_one_or_none()

    # 发送验证码
    @staticmethod
    async def send_verification_code(phone: str) -> Dict[str, str | bool | None]:
        verification_code = str(random.randint(100000, 999999))
        response = await AliyunSmsService.send_sms(phone, verification_code)
        if response:
            print("发送验证码", verification_code)
            await redis_manager.set(
                f"verification_code:{phone}", verification_code, ex=300
            )
            return success_response(message="验证码发送成功")
        else:
            return error_response(message="验证码发送失败")

    # 验证验证码
    @staticmethod
    async def verify_verification_code(phone: str, verification_code: str) -> bool:
        stored_code = await redis_manager.get(f"verification_code:{phone}")
        print("验证", stored_code, verification_code)
        return stored_code == verification_code
