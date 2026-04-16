import math
from typing import Literal

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.knowledge import KnowledgeChunk, KnowledgeFile, KnowledgeFolder


async def get_knowledge_folder_by_id(
    db: AsyncSession,
    folder_id: str,
) -> KnowledgeFolder | None:
    stmt = select(KnowledgeFolder).where(
        KnowledgeFolder.id == folder_id,
        KnowledgeFolder.is_deleted == 0,
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def create_knowledge_folder_repo(
    db: AsyncSession,
    name: str,
    sort_no: int = 0,
) -> KnowledgeFolder:
    row = KnowledgeFolder(
        name=name,
        sort_no=sort_no,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def list_all_knowledge_folders_repo(db: AsyncSession) -> list[KnowledgeFolder]:
    stmt = (
        select(KnowledgeFolder)
        .where(KnowledgeFolder.is_deleted == 0)
        .order_by(KnowledgeFolder.sort_no.asc(), KnowledgeFolder.created_at.asc())
    )
    return list((await db.execute(stmt)).scalars().all())


async def count_knowledge_files_in_folder(db: AsyncSession, folder_id: str) -> int:
    stmt = (
        select(func.count())
        .select_from(KnowledgeFile)
        .where(
            KnowledgeFile.folder_id == folder_id,
            KnowledgeFile.is_deleted == 0,
        )
    )
    return int((await db.execute(stmt)).scalar_one() or 0)


async def try_soft_delete_knowledge_folder_repo(
    db: AsyncSession,
    folder_id: str,
) -> Literal["ok", "not_found", "not_empty"]:
    row = await get_knowledge_folder_by_id(db, folder_id)
    if not row:
        return "not_found"
    n = await count_knowledge_files_in_folder(db, folder_id)
    if n > 0:
        return "not_empty"
    await db.execute(
        update(KnowledgeFolder)
        .where(KnowledgeFolder.id == folder_id, KnowledgeFolder.is_deleted == 0)
        .values(is_deleted=1)
    )
    await db.commit()
    return "ok"


async def create_knowledge_file(
    db: AsyncSession,
    *,
    folder_id: str | None,
    filename: str,
    ext: str,
    content_type: str | None,
    size: int,
    storage_path: str,
) -> KnowledgeFile:
    row = KnowledgeFile(
        folder_id=folder_id,
        filename=filename,
        ext=ext,
        content_type=content_type,
        size=size,
        storage_path=storage_path,
        status="pending",
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_knowledge_file_by_id(
    db: AsyncSession,
    file_id: str,
) -> KnowledgeFile | None:
    stmt = select(KnowledgeFile).where(
        KnowledgeFile.id == file_id,
        KnowledgeFile.is_deleted == 0,
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def list_knowledge_files_page(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    folder_id: str | None = None,
    keyword: str | None = None,
    status: str | None = None,
):
    filters = [KnowledgeFile.is_deleted == 0]

    if folder_id is not None:
        filters.append(KnowledgeFile.folder_id == folder_id)

    if keyword:
        filters.append(KnowledgeFile.filename.ilike(f"%{keyword.strip()}%"))

    if status:
        filters.append(KnowledgeFile.status == status)

    count_stmt = select(func.count()).select_from(KnowledgeFile).where(*filters)
    total = (await db.execute(count_stmt)).scalar_one()

    offset = (page - 1) * page_size
    data_stmt = (
        select(KnowledgeFile)
        .where(*filters)
        .order_by(KnowledgeFile.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    rows = (await db.execute(data_stmt)).scalars().all()

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return rows, {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }


async def update_knowledge_file_status(
    db: AsyncSession,
    *,
    file_id: str,
    status: str,
    error_message: str | None = None,
    chunk_count: int | None = None,
):
    values = {
        "status": status,
        "error_message": error_message,
    }
    if chunk_count is not None:
        values["chunk_count"] = chunk_count

    stmt = (
        update(KnowledgeFile)
        .where(KnowledgeFile.id == file_id, KnowledgeFile.is_deleted == 0)
        .values(**values)
    )
    await db.execute(stmt)
    await db.commit()


async def soft_delete_knowledge_file(
    db: AsyncSession,
    *,
    file_id: str,
):
    await db.execute(
        update(KnowledgeFile)
        .where(KnowledgeFile.id == file_id, KnowledgeFile.is_deleted == 0)
        .values(is_deleted=1)
    )
    await db.execute(
        update(KnowledgeChunk)
        .where(KnowledgeChunk.file_id == file_id, KnowledgeChunk.is_deleted == 0)
        .values(is_deleted=1)
    )
    await db.commit()


async def clear_chunks_by_file_id(db: AsyncSession, file_id: str):
    await db.execute(
        update(KnowledgeChunk)
        .where(KnowledgeChunk.file_id == file_id, KnowledgeChunk.is_deleted == 0)
        .values(is_deleted=1)
    )
    await db.commit()


async def bulk_insert_chunks(
    db: AsyncSession,
    chunks: list[KnowledgeChunk],
):
    db.add_all(chunks)
    await db.commit()