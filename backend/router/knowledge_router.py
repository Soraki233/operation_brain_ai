from pathlib import Path
from typing import Annotated, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
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
from schema.knowledge_schema import KnowledgeFileCreateResponseSchema
from schema.knowledge_schema import KnowledgeFileItemSchema
from schema.knowledge_schema import KnowledgeFileUpdateSchema
from schema.response import PagedResponseSchema
from schema.knowledge_schema import KnowledgeFolderDeleteSchema

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
        current_user,
        db,
    )
    if not knowledge_folder:
        return error_response("创建知识库文件夹失败", 400)
    return success_response(
        data=KnowledgeFolderResponseSchema.model_validate(knowledge_folder)
    )


# 更新知识库文件夹
@knowledge_router.put("/folder/update", summary="更新知识库文件夹")
async def update_knowledge_folder(
    knowledge_folder_update: KnowledgeFolderUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    knowledge_folder = await KnowledgeRepo.update_knowledge_folder(
        knowledge_folder_update, current_user, db
    )
    if not knowledge_folder:
        return error_response("更新知识库文件夹失败", 400)
    return success_response(
        data=KnowledgeFolderResponseSchema.model_validate(knowledge_folder)
    )


# 删除知识库文件夹
@knowledge_router.delete("/folder/delete", summary="删除知识库文件夹")
async def delete_knowledge_folder(
    knowledge_folder_delete: KnowledgeFolderDeleteSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    knowledge_folder = await KnowledgeRepo.delete_knowledge_folder(knowledge_folder_delete, current_user, db)
    if not knowledge_folder:
        return error_response("删除知识库文件夹失败", 400)
    return success_response(
        data=KnowledgeFolderResponseSchema.model_validate(knowledge_folder)
    )

# 获取知识库文件列表（分页）
@knowledge_router.get("/files/list", summary="获取知识库文件列表（分页）")
async def get_knowledge_file_list(
    kb_id: Annotated[str, Query(..., min_length=1, description="知识库ID")],
    folder_id: Annotated[Optional[str], Query(description="文件夹ID，不传查询根目录")] = None,
    keyword: Annotated[
        Optional[str], Query(max_length=100, description="文件名模糊搜索关键词")
    ] = None,
    page: Annotated[int, Query(ge=1, description="页码，从1开始")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="每页条数，最大100")] = 20,
    db: AsyncSession = Depends(get_db),
):
    # 空字符串统一视为未传
    folder_id_val = folder_id if folder_id else None
    keyword_val = keyword.strip() if keyword and keyword.strip() else None

    total, items = await KnowledgeRepo.get_knowledge_file_list(
        kb_id=kb_id,
        page=page,
        page_size=page_size,
        db=db,
        folder_id=folder_id_val,
        keyword=keyword_val,
    )
    return success_response(
        data=PagedResponseSchema[KnowledgeFileItemSchema](
            total=total,
            page=page,
            page_size=page_size,
            items=[KnowledgeFileItemSchema.model_validate(item) for item in items],
        )
    )


# 创建知识库文件（多文件）
@knowledge_router.post("/files/upload", summary="创建知识库文件（多文件）")
async def create_knowledge_file(
    background_tasks: BackgroundTasks,
    kb_id: Annotated[str, Form(...)],
    files: Annotated[list[UploadFile], File(...)],
    folder_id: Annotated[str | None, Form(alias="folder_id")] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    上传文件接口只做落盘 + 写 pending 记录并立即返回，
    向量切块入库通过 BackgroundTasks 在响应发送后异步执行，
    前端通过轮询 parse_status 感知 pending -> success / failed 的状态变化。
    """
    knowledge_files = []
    for file in files:
        knowledge_file = await KnowledgeRepo.create_knowledge_files(
            kb_id,
            folder_id,
            file,
            current_user.id,
            db,
        )
        background_tasks.add_task(
            KnowledgeRepo.ingest_file_in_background, knowledge_file.id
        )
        knowledge_files.append(knowledge_file)
    return success_response(
        data=[
            KnowledgeFileCreateResponseSchema.model_validate(item)
            for item in knowledge_files
        ]
    )


# 删除知识库文件（软删除 + 同步清理向量）
@knowledge_router.delete("/files/{file_id}", summary="删除知识库文件")
async def delete_knowledge_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    knowledge_file = await KnowledgeRepo.delete_knowledge_file(
        file_id, current_user, db
    )
    return success_response(
        data=KnowledgeFileItemSchema.model_validate(knowledge_file)
    )


# 更新知识库文件（重命名 / 移动）
@knowledge_router.put("/files/update", summary="更新知识库文件（重命名 / 移动）")
async def update_knowledge_file(
    knowledge_file_update: KnowledgeFileUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    knowledge_file = await KnowledgeRepo.update_knowledge_file(
        knowledge_file_update, current_user, db
    )
    return success_response(
        data=KnowledgeFileItemSchema.model_validate(knowledge_file)
    )


# 获取知识库文件（二进制流，用于在线预览）
@knowledge_router.get(
    "/files/{file_id}/preview",
    summary="获取知识库文件（二进制流，用于在线预览）",
)
async def get_knowledge_file_preview(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    knowledge_file = await KnowledgeRepo.get_knowledge_file_by_id(file_id, db)
    if not knowledge_file:
        raise HTTPException(status_code=404, detail="文件不存在")

    storage_path = Path(knowledge_file.storage_path)
    if not storage_path.exists() or not storage_path.is_file():
        raise HTTPException(status_code=404, detail="文件物理存储已丢失")

    return FileResponse(
        path=str(storage_path),
        media_type=knowledge_file.mime_type or "application/octet-stream",
        filename=knowledge_file.file_name,
        content_disposition_type="inline",
    )

