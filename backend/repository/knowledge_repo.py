from db.session import AsyncSession
from db.models import KnowledgeBase as KnowledgeBaseModel
from db.models import KnowledgeFolder as KnowledgeFolderModel
from schema.knowledge_schema import KnowledgeBaseCreateSchema, KnowledgeFolderCreateSchema, KnowledgeFolderUpdateSchema
from sqlalchemy import select
from core.reponse import error_response

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
        knowledge_folder_data: KnowledgeFolderCreateSchema, creator_user_id: str, db: AsyncSession
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
        knowledge_folder_data: KnowledgeFolderUpdateSchema, creator_user_id: str, db: AsyncSession
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