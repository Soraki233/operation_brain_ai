from fastapi import APIRouter, Depends
from db.session import AsyncSession, get_db
from schema.user_schema import UserRegisterSchema

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/register", summary="创建用户")
async def register(register_data: UserRegisterSchema, db: AsyncSession = Depends(get_db)):
