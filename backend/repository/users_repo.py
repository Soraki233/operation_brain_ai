from db.session import AsyncSession
from db.models import User as UserModel, UserRole as UserRoleModel
from sqlalchemy import select
from schema.user_schema import UserRegisterSchema
from core.security import get_password_hash
from core.redis import redis_manager
import random
from service.sms_service import AliyunSmsService


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
        user = UserModel(
            phone=user_data.phone,
            username=user_data.username,
            hashed_password=get_password_hash(user_data.password),
            verification_code=user_data.verification_code,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    # 创建用户角色
    @staticmethod
    async def create_user_role(db: AsyncSession) -> UserRoleModel:
        user_role = UserRoleModel(
            role_name="运行人员",
            role_key="staff",
        )
        db.add(user_role)
        await db.commit()
        await db.refresh(user_role)
        return user_role

    # 发送验证码
    @staticmethod
    async def send_verification_code(phone: str) -> str:
        verification_code = str(random.randint(100000, 999999))
        resp = await AliyunSmsService.send_sms(phone, verification_code)
        if resp["body"]["Code"] == "OK":
            await redis_manager.set(
                f"verification_code:{phone}", verification_code, ex=300
            )
        return verification_code

    # 验证验证码
    @staticmethod
    async def verify_verification_code(phone: str, verification_code: str) -> bool:
        stored_code = await redis_manager.get(f"verification_code:{phone}")
        return stored_code == verification_code