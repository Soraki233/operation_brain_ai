from db.session import AsyncSession
from db.models import KnowledgeBase as KnowledgeBaseModel
from db.models import KnowledgeFolder as KnowledgeFolderModel
from schema.knowledge_schema import (
    KnowledgeBaseCreateSchema,
    KnowledgeFolderCreateSchema,
    KnowledgeFolderUpdateSchema,
    KnowledgeFileUpdateSchema,
)
from sqlalchemy import select, func
from db.models import KnowledgeFile as KnowledgeFileModel
from fastapi import UploadFile, Depends, HTTPException
from core.settings import settings
import asyncio
from uuid import uuid4
from pathlib import Path
from schema.knowledge_schema import KnowledgeFolderDeleteSchema
from db.models.user import User
from core.deps import get_current_user, get_db
from db.models.user import UserRole as UserRoleModel


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
        do_create_user: User,
        db: AsyncSession,
    ) -> KnowledgeFolderModel:
        has_knowledge_permission = await get_has_knowledge_permission(
            knowledge_folder_data.kb_id, do_create_user, db
        )
        if not has_knowledge_permission:
            raise HTTPException(status_code=400, detail="您没有该权限")
            
        knowledge_folder = KnowledgeFolderModel(
            kb_id=knowledge_folder_data.kb_id,
            name=knowledge_folder_data.name,
            creator_user_id=do_create_user.id,
        )
        db.add(knowledge_folder)
        await db.commit()
        await db.refresh(knowledge_folder)
        return knowledge_folder

    @staticmethod
    async def update_knowledge_folder(
        knowledge_folder_data: KnowledgeFolderUpdateSchema,
        do_update_user: User,
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
        knowledge_folder = knowledge_folder.scalar_one_or_none()

        # 先校验文件夹存在，再校验权限，避免对 None 取 kb_id
        if not knowledge_folder:
            raise HTTPException(status_code=400, detail="文件夹不存在")

        has_knowledge_permission = await get_has_knowledge_permission(
            knowledge_folder.kb_id, do_update_user, db
        )
        if not has_knowledge_permission:
            raise HTTPException(status_code=400, detail="您没有该权限")

        knowledge_folder.name = knowledge_folder_data.name
        await db.commit()
        await db.refresh(knowledge_folder)
        return knowledge_folder

    # 删除知识库文件夹
    # 查询文件夹下所有文件，并删除文件，再删除文件夹
    @staticmethod
    async def delete_knowledge_folder(
        KnowledgeFolderDeleteSchema: KnowledgeFolderDeleteSchema,
        do_delete_user: User,
        db: AsyncSession,
    ) -> KnowledgeFolderModel:
        """
        删除知识库文件夹及其下所有文件（软删除）。
        步骤如下：
        1. 查询目标文件夹下的所有未被删除的文件。
        2. 遍历这些文件，将其 is_deleted 字段更新为1（软删除），并提交数据库。
        3. 查询目标文件夹，确认其存在且为活跃未删除状态。
        4. 将该文件夹的 is_deleted 字段更新为1（软删除），并提交数据库。
        5. 返回被删除的文件夹对象。
        如果找不到对应的文件夹，则返回错误响应。
        6.如果文件夹是共享知识库的，那么判断只能在该用户的role_key为admin时才能删除
        """
        has_knowledge_permission = await get_has_knowledge_permission(
            KnowledgeFolderDeleteSchema.kb_id, do_delete_user, db
        )
        if not has_knowledge_permission:
            raise HTTPException(status_code=400, detail="您没有该权限")
        # 查询该文件夹下所有活跃且未被删除的文件
        knowledge_files = await db.execute(
            select(KnowledgeFileModel).where(
                KnowledgeFileModel.folder_id == KnowledgeFolderDeleteSchema.folder_id,
                KnowledgeFileModel.is_deleted == 0,
            )
        )
        knowledge_files = knowledge_files.scalars().all()
        # 遍历并软删除文件
        for knowledge_file in knowledge_files:
            knowledge_file.is_deleted = 1  # 软删除文件
            await db.commit()
            await db.refresh(knowledge_file)
        # 查询活跃且未被删除的文件夹
        knowledge_folder = await db.execute(
            select(KnowledgeFolderModel).where(
                KnowledgeFolderModel.id == KnowledgeFolderDeleteSchema.folder_id,
                KnowledgeFolderModel.is_active == 1,
                KnowledgeFolderModel.is_deleted == 0,
            )
        )
        knowledge_folder = knowledge_folder.scalar_one_or_none()
        if not knowledge_folder:
            raise HTTPException(status_code=400, detail="文件夹不存在")
        knowledge_folder.is_deleted = 1  # 软删除文件夹
        await db.commit()
        await db.refresh(knowledge_folder)
        return knowledge_folder

    @staticmethod
    async def get_knowledge_file_by_id(
        file_id: str, db: AsyncSession
    ) -> KnowledgeFileModel | None:
        """根据文件ID查询未被软删除的知识库文件记录。"""
        result = await db.execute(
            select(KnowledgeFileModel).where(
                KnowledgeFileModel.id == file_id,
                KnowledgeFileModel.is_deleted == 0,
            )
        )
        return result.scalar_one_or_none()

    # 更新知识库文件：支持重命名（file_name）/ 移动（folder_id、move_to_root）
    # 物理文件 storage_path 保持不变，仅更新数据库字段
    @staticmethod
    async def update_knowledge_file(
        data: KnowledgeFileUpdateSchema,
        do_update_user: User,
        db: AsyncSession,
    ) -> KnowledgeFileModel:
        knowledge_file = await KnowledgeRepo.get_knowledge_file_by_id(data.id, db)
        if not knowledge_file:
            raise HTTPException(status_code=400, detail="文件不存在")

        has_knowledge_permission = await get_has_knowledge_permission(
            knowledge_file.kb_id, do_update_user, db
        )
        if not has_knowledge_permission:
            raise HTTPException(status_code=400, detail="您没有该权限")

        # 1) 目标文件夹：move_to_root 优先，其次 folder_id；未传则保持原值
        target_folder_id = knowledge_file.folder_id
        if data.move_to_root:
            target_folder_id = None
        elif data.folder_id is not None:
            folder_result = await db.execute(
                select(KnowledgeFolderModel).where(
                    KnowledgeFolderModel.id == data.folder_id,
                    KnowledgeFolderModel.kb_id == knowledge_file.kb_id,
                    KnowledgeFolderModel.is_active == 1,
                    KnowledgeFolderModel.is_deleted == 0,
                )
            )
            if folder_result.scalar_one_or_none() is None:
                raise HTTPException(
                    status_code=400, detail="目标文件夹不存在或不属于该知识库"
                )
            target_folder_id = data.folder_id

        # 2) 目标文件名：未带扩展名时自动拼回原扩展名，避免用户误删后缀
        target_file_name = knowledge_file.file_name
        target_file_ext = knowledge_file.file_ext
        if data.file_name is not None:
            trimmed = data.file_name.strip()
            if not trimmed:
                raise HTTPException(status_code=400, detail="文件名不能为空")
            has_ext = "." in trimmed
            target_file_name = (
                trimmed
                if has_ext or not knowledge_file.file_ext
                else f"{trimmed}{knowledge_file.file_ext}"
            )
            target_file_ext = (
                Path(target_file_name).suffix.lower() or knowledge_file.file_ext
            )

        # 3) 同目录下文件名唯一性校验
        dup_conditions = [
            KnowledgeFileModel.kb_id == knowledge_file.kb_id,
            KnowledgeFileModel.file_name == target_file_name,
            KnowledgeFileModel.id != knowledge_file.id,
            KnowledgeFileModel.is_deleted == 0,
        ]
        if target_folder_id is None:
            dup_conditions.append(KnowledgeFileModel.folder_id.is_(None))
        else:
            dup_conditions.append(KnowledgeFileModel.folder_id == target_folder_id)

        duplicate = await db.execute(
            select(KnowledgeFileModel).where(*dup_conditions)
        )
        if duplicate.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="当前目录下已存在同名文件")

        knowledge_file.file_name = target_file_name
        knowledge_file.file_ext = target_file_ext
        knowledge_file.folder_id = target_folder_id
        await db.commit()
        await db.refresh(knowledge_file)
        return knowledge_file

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
        await asyncio.to_thread(
            save_path.write_bytes,
            content,
        )
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


async def get_has_knowledge_permission(
    kb_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> bool:
    # 查询知识库
    knowledge_base = await db.execute(
        select(KnowledgeBaseModel).where(
            KnowledgeBaseModel.id == kb_id,
            KnowledgeBaseModel.is_active == 1,
            KnowledgeBaseModel.is_deleted == 0,
        )
    )
    knowledge_base = knowledge_base.scalar_one_or_none()
    # 查询该用户的role_key
    user_role = await db.execute(
        select(UserRoleModel).where(
            UserRoleModel.id == current_user.role_id,
        )
    )
    user_role = user_role.scalar_one_or_none()
    if knowledge_base.scope == "shared":
        if user_role.role_key != "admin":
            return False
    if knowledge_base.creator_user_id != current_user.id:
        return False
    return True
