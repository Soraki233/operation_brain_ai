from db.session import AsyncSession
from db.models import KnowledgeBase as KnowledgeBaseModel
from db.models import KnowledgeFolder as KnowledgeFolderModel
from schema.knowledge_schema import (
    KnowledgeBaseCreateSchema,
    KnowledgeFolderCreateSchema,
    KnowledgeFolderUpdateSchema,
)
from sqlalchemy import select, func
from core.reponse import error_response
from db.models import KnowledgeFile as KnowledgeFileModel
from fastapi import UploadFile
from core.settings import settings
import asyncio
from uuid import uuid4
from pathlib import Path


class KnowledgeRepo:
    @staticmethod
    async def ensure_shared_knowledge_base(db: AsyncSession) -> KnowledgeBaseModel:
        """
        启动时确保至少存在一个共享知识库。
        若不存在则自动创建默认共享知识库。
        """
        result = await db.execute(
            select(KnowledgeBaseModel).where(
                KnowledgeBaseModel.scope == "shared",
                KnowledgeBaseModel.owner_user_id.is_(None),
                KnowledgeBaseModel.is_deleted == 0,
            )
        )
        shared_knowledge_base = result.scalar_one_or_none()
        if shared_knowledge_base:
            return shared_knowledge_base

        shared_knowledge_base = KnowledgeBaseModel(
            name="共享知识库",
            scope="shared",
            owner_user_id=None,
            creator_user_id="system",
        )
        db.add(shared_knowledge_base)
        await db.commit()
        await db.refresh(shared_knowledge_base)
        return shared_knowledge_base

    @staticmethod
    async def create_knowledge_base(
        knowledge_base_data: KnowledgeBaseCreateSchema, db: AsyncSession
    ) -> KnowledgeBaseModel:
        knowledge_base = KnowledgeBaseModel(
            name=knowledge_base_data.name,
            scope=knowledge_base_data.scope,
            owner_user_id=knowledge_base_data.owner_user_id,
            creator_user_id=knowledge_base_data.creator_user_id,
        )
        print("创建个人知识库", knowledge_base)
        db.add(knowledge_base)
        await db.commit()
        await db.refresh(knowledge_base)
        return knowledge_base

    # 查询知识库列表：共享知识库和个人知识库
    @staticmethod
    async def get_knowledge_list(
        current_user_id: str, db: AsyncSession
    ) -> list[KnowledgeBaseModel]:
        # 查询个人知识库
        personal_knowledge_bases = await db.execute(
            select(KnowledgeBaseModel).where(
                KnowledgeBaseModel.owner_user_id == current_user_id,
                KnowledgeBaseModel.is_active == 1,
                KnowledgeBaseModel.is_deleted == 0,
            )
        )
        # 查询共享知识库
        shared_knowledge_bases = await db.execute(
            select(KnowledgeBaseModel).where(
                KnowledgeBaseModel.owner_user_id.is_(None),
                KnowledgeBaseModel.is_active == 1,
                KnowledgeBaseModel.is_deleted == 0,
            )
        )
        # 将个人知识库和共享知识库合并
        knowledge_bases = (
            personal_knowledge_bases.scalars().all()
            + shared_knowledge_bases.scalars().all()
        )
        return knowledge_bases

    @staticmethod
    async def get_knowledge_folder_list(
        kb_id: str, db: AsyncSession
    ) -> list[KnowledgeFolderModel]:
        knowledge_folder_list = await db.execute(
            select(KnowledgeFolderModel).where(
                KnowledgeFolderModel.kb_id == kb_id,
                KnowledgeFolderModel.is_active == 1,
                KnowledgeFolderModel.is_deleted == 0,
            )
        )
        return knowledge_folder_list.scalars().all()

    @staticmethod
    async def create_knowledge_folder(
        knowledge_folder_data: KnowledgeFolderCreateSchema,
        creator_user_id: str,
        db: AsyncSession,
    ) -> KnowledgeFolderModel:
        knowledge_folder = KnowledgeFolderModel(
            kb_id=knowledge_folder_data.kb_id,
            name=knowledge_folder_data.name,
            creator_user_id=creator_user_id,
        )
        db.add(knowledge_folder)
        await db.commit()
        await db.refresh(knowledge_folder)
        return knowledge_folder

    @staticmethod
    async def update_knowledge_folder(
        knowledge_folder_data: KnowledgeFolderUpdateSchema,
        creator_user_id: str,
        db: AsyncSession,
    ) -> KnowledgeFolderModel:
        # 根据文件夹ID查询活跃且未删除的文件夹
        knowledge_folder = await db.execute(
            select(KnowledgeFolderModel).where(
                KnowledgeFolderModel.id == knowledge_folder_data.id,
                KnowledgeFolderModel.is_active == 1,
                KnowledgeFolderModel.is_deleted == 0,
            )
        )
        # 获取查询结果
        knowledge_folder = knowledge_folder.scalar_one_or_none()
        if not knowledge_folder:
            # 如果未找到对应文件夹，则返回None
            return error_response("文件夹不存在", 400)
        # 更新文件夹名称
        knowledge_folder.name = knowledge_folder_data.name
        # 提交更新到数据库
        await db.commit()
        # 刷新实例以获取最新数据
        await db.refresh(knowledge_folder)
        # 返回更新后的文件夹对象
        return knowledge_folder

    @staticmethod
    async def get_knowledge_file_list(
        kb_id: str,
        page: int,
        page_size: int,
        db: AsyncSession,
        folder_id: str | None = None,
        keyword: str | None = None,
    ) -> tuple[int, list[KnowledgeFileModel]]:
        """
        分页查询知识库文件列表。
        folder_id 为 None 时查询知识库根目录下的文件（未归属任何文件夹）。
        keyword 不为空时对 file_name 做模糊匹配。
        返回 (total, items) 元组。
        """
        base_condition = [
            KnowledgeFileModel.kb_id == kb_id,
            KnowledgeFileModel.is_deleted == 0,
        ]
        if folder_id is not None:
            base_condition.append(KnowledgeFileModel.folder_id == folder_id)
        else:
            base_condition.append(KnowledgeFileModel.folder_id.is_(None))

        if keyword:
            base_condition.append(KnowledgeFileModel.file_name.ilike(f"%{keyword}%"))

        # 查询总数
        count_result = await db.execute(
            select(func.count()).select_from(KnowledgeFileModel).where(*base_condition)
        )
        total = count_result.scalar_one()

        # 分页查询
        offset = (page - 1) * page_size
        items_result = await db.execute(
            select(KnowledgeFileModel)
            .where(*base_condition)
            .order_by(KnowledgeFileModel.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        items = items_result.scalars().all()
        return total, list(items)

    @staticmethod
    async def create_knowledge_files(
        kb_id: str,
        folder_id: str | None,
        file: UploadFile,
        uploaded_by: str,
        db: AsyncSession,
    ) -> KnowledgeFileModel:
        # 获取文件后缀
        suffix = Path(file.filename).suffix.lower()
        # 读取文件内容
        content = await file.read()
        # 生成文件物理名称
        physical_name = f"{uuid4().hex}{suffix}"
        # 生成文件保存目录
        save_dir = Path(settings.KNOWLEDGE_UPLOAD_DIR) / kb_id
        # 创建文件保存目录
        save_dir.mkdir(parents=True, exist_ok=True)
        # 生成文件保存路径
        save_path = save_dir / physical_name
        # 写入文件内容
        await asyncio.to_thread(save_path.write_bytes, content,)
        # 创建知识库文件对象
        file = KnowledgeFileModel(
            kb_id=kb_id,
            folder_id=folder_id,
            file_name=file.filename,
            file_ext=suffix,
            mime_type=file.content_type,
            file_size=len(content),
            storage_path=str(save_path),
            parse_status="pending",
            chunk_count=0,
            uploaded_by=uploaded_by,
            error_message=None,
        )
        db.add(file)
        await db.commit()
        await db.refresh(file)
        return file
