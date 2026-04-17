from fastapi import APIRouter, Depends
from db.models.user import User
from core.deps import get_current_user
from repository.knowledge_repo import KnowledgeRepo
from db.session import AsyncSession, get_db
from fastapi import HTTPException
from core.exception_handler import http_exception_handler
from core.reponse import success_response, error_response
from schema.knowledge_schema import KnowledgeBaseResponseSchema
from schema.knowledge_schema import KnowledgeFolderRequestSchema
from schema.knowledge_schema import KnowledgeFolderCreateSchema
from schema.knowledge_schema import KnowledgeFolderResponseSchema
from schema.knowledge_schema import KnowledgeFolderUpdateSchema
knowledge_router = APIRouter(prefix="/knowledge", tags=["knowledge"])


# 获取知识库列表
@knowledge_router.get("/list", summary="获取知识库列表")
async def get_knowledge_list(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    knowledge_list = await KnowledgeRepo.get_knowledge_list(current_user.id, db)
    if not knowledge_list:
        return http_exception_handler(
            HTTPException(status_code=400, detail="获取知识库列表失败")
        )
    knowledge_list = [
        KnowledgeBaseResponseSchema.model_validate(knowledge)
        for knowledge in knowledge_list
    ]
    return success_response(data=knowledge_list)


# 获取知识库文件夹列表
@knowledge_router.get("/folder/list", summary="获取知识库文件夹列表")
async def get_knowledge_folder_list(
    knowledge_folder_request: KnowledgeFolderRequestSchema = Depends(
        KnowledgeFolderRequestSchema
    ),
    db: AsyncSession = Depends(get_db),
):
    # 根据知识库ID获取知识库文件夹列表
    knowledge_folder_list = await KnowledgeRepo.get_knowledge_folder_list(
        knowledge_folder_request.kb_id, db
    )
    print(knowledge_folder_list)
    if knowledge_folder_list is None:
        return error_response("获取知识库文件夹列表失败", 400)
    return success_response(
        data=[
            KnowledgeFolderResponseSchema.model_validate(folder)
            for folder in knowledge_folder_list
        ]
    )


# 创建知识库文件夹
@knowledge_router.post("/folder/create", summary="创建知识库文件夹")
async def create_knowledge_folder(
    knowledge_folder_create: KnowledgeFolderCreateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    knowledge_folder = await KnowledgeRepo.create_knowledge_folder(
        knowledge_folder_create,
        current_user.id,
        db,
    )
    if not knowledge_folder:
        return error_response("创建知识库文件夹失败", 400)
    return success_response(data=KnowledgeFolderResponseSchema.model_validate(knowledge_folder))

# 更新知识库文件夹
@knowledge_router.put("/folder/update", summary="更新知识库文件夹")
async def update_knowledge_folder(
    knowledge_folder_update: KnowledgeFolderUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    knowledge_folder = await KnowledgeRepo.update_knowledge_folder(
        knowledge_folder_update, current_user.id, db)
    if not knowledge_folder:
        return error_response("更新知识库文件夹失败", 400)
    return success_response(data=KnowledgeFolderResponseSchema.model_validate(knowledge_folder))