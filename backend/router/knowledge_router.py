from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from core.reponse import success_response
from db.session import get_db
from schema.chat_schema import ChatAskSchema
from schema.knowledge_schema import KnowledgeFolderCreateSchema
from service.rag_service import (
    ask_with_rag_service,
    create_knowledge_file_and_process,
    delete_knowledge_file_service,
    get_knowledge_file_detail_service,
    list_knowledge_files_service,
)
from repository.knowledge_repo import (
    create_knowledge_folder_repo,
    list_all_knowledge_folders_repo,
    try_soft_delete_knowledge_folder_repo,
)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/folders")
async def list_knowledge_folders(db: AsyncSession = Depends(get_db)):
    items = await list_all_knowledge_folders_repo(db)
    return success_response(
        data={
            "items": [
                {
                    "id": r.id,
                    "name": r.name,
                    "sort_no": r.sort_no,
                    "created_at": r.created_at,
                    "updated_at": r.updated_at,
                }
                for r in items
            ],
        }
    )


@router.post("/folders")
async def create_knowledge_folder(
    payload: KnowledgeFolderCreateSchema,
    db: AsyncSession = Depends(get_db),
):
    row = await create_knowledge_folder_repo(
        db,
        name=payload.name,
        sort_no=payload.sort_no,
    )
    if not row:
        raise HTTPException(status_code=404, detail="创建失败")
    return success_response(
        data={
            "id": row.id,
            "name": row.name,
            "sort_no": row.sort_no,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        },
        message="创建成功",
    )


@router.delete("/folders/{folder_id}")
async def delete_knowledge_folder(
    folder_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await try_soft_delete_knowledge_folder_repo(db, folder_id=folder_id)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="文件夹不存在")
    if result == "not_empty":
        raise HTTPException(
            status_code=400,
            detail="文件夹内仍有文件，请先删除文件后再删除文件夹",
        )
    return success_response(message="删除成功")


@router.post("/files/upload")
async def upload_knowledge_files(
    files: list[UploadFile] = File(...),
    folder_id: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
):
    # 初始化返回的文件信息列表
    items = []

    # 遍历每一个上传的文件
    for upload in files:
        # 校验文件名是否存在
        if not upload.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")

        # 创建知识库文件，并异步解析文件内容
        row = await create_knowledge_file_and_process(
            db,
            folder_id=folder_id,
            upload_file=upload,
        )

        # 将文件部分信息加入返回列表
        items.append(
            {
                "id": row.id,
                "filename": row.filename,
                "status": row.status,
                "size": row.size,
            }
        )

    return success_response(data={"items": items}, message="上传成功，已进入异步解析")


@router.get("/files")
async def list_knowledge_files(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页条数"),
    folder_id: str | None = Query(None, description="文件夹ID"),
    keyword: str | None = Query(None, description="文件名关键词"),
    status: str | None = Query(None, description="文件状态"),
    db: AsyncSession = Depends(get_db),
):
    data = await list_knowledge_files_service(
        db,
        page=page,
        page_size=page_size,
        folder_id=folder_id,
        keyword=keyword,
        status=status,
    )
    return success_response(data=data)


@router.get("/files/{file_id}")
async def get_knowledge_file_detail(
    file_id: str,
    db: AsyncSession = Depends(get_db),
):
    data = await get_knowledge_file_detail_service(db, file_id=file_id)
    if not data:
        raise HTTPException(status_code=404, detail="文件不存在")
    return success_response(data=data)


@router.delete("/files/{file_id}")
async def delete_knowledge_file(
    file_id: str,
    db: AsyncSession = Depends(get_db),
):
    ok = await delete_knowledge_file_service(db, file_id=file_id)
    if not ok:
        raise HTTPException(status_code=404, detail="文件不存在")
    return success_response(message="删除成功")


@router.post("/chat/ask")
async def ask_with_rag(
    payload: ChatAskSchema,
    db: AsyncSession = Depends(get_db),
):
    data = await ask_with_rag_service(
        db,
        question=payload.question,
        thread_id=payload.thread_id,
        folder_ids=payload.folder_ids,
        file_ids=payload.file_ids,
        top_k=payload.top_k,
    )
    return success_response(data=data)
