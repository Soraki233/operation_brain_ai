from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select, func, desc

from db.session import AsyncSession
from db.models import ChatThread as ChatThreadModel
from db.models import ChatMessage as ChatMessageModel
from db.models.user import User
from core.settings import settings


class ChatRepo:
    """会话（ChatThread）+ 消息（ChatMessage）持久化。"""

    # ------------------------------- Thread -------------------------------

    @staticmethod
    async def create_thread(
        user: User, title: Optional[str], db: AsyncSession
    ) -> ChatThreadModel:
        thread = ChatThreadModel(
            user_id=user.id,
            title=(title or "新对话"),
        )
        db.add(thread)
        await db.commit()
        await db.refresh(thread)
        return thread

    @staticmethod
    async def list_threads(user: User, db: AsyncSession) -> list[ChatThreadModel]:
        """按最近活跃（last_message_at desc, created_at desc）返回当前用户的会话。"""
        result = await db.execute(
            select(ChatThreadModel)
            .where(
                ChatThreadModel.user_id == user.id,
                ChatThreadModel.is_deleted == 0,
            )
            .order_by(
                desc(ChatThreadModel.last_message_at),
                desc(ChatThreadModel.created_at),
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_thread(
        thread_id: str, user: User, db: AsyncSession
    ) -> ChatThreadModel:
        """查询会话并做归属校验，失败直接抛 400。"""
        result = await db.execute(
            select(ChatThreadModel).where(
                ChatThreadModel.id == thread_id,
                ChatThreadModel.is_deleted == 0,
            )
        )
        thread = result.scalar_one_or_none()
        if not thread:
            raise HTTPException(status_code=400, detail="会话不存在")
        if thread.user_id != user.id:
            raise HTTPException(status_code=400, detail="您没有该权限")
        return thread

    @staticmethod
    async def delete_thread(
        thread_id: str, user: User, db: AsyncSession
    ) -> ChatThreadModel:
        """软删会话；会话下的消息保持原状（只按 thread_id 读取时会被过滤）。"""
        thread = await ChatRepo.get_thread(thread_id, user, db)
        thread.is_deleted = 1
        await db.commit()
        await db.refresh(thread)
        return thread

    @staticmethod
    async def update_thread_title(
        thread: ChatThreadModel, title: str, db: AsyncSession
    ) -> None:
        """首次提问后用用户提问内容回填标题。"""
        thread.title = title
        await db.commit()
        await db.refresh(thread)

    # ------------------------------- Message -------------------------------

    @staticmethod
    async def _next_sequence_no(thread_id: str, db: AsyncSession) -> int:
        result = await db.execute(
            select(func.coalesce(func.max(ChatMessageModel.sequence_no), 0)).where(
                ChatMessageModel.thread_id == thread_id,
            )
        )
        return int(result.scalar_one()) + 1

    @staticmethod
    async def append_message(
        thread: ChatThreadModel,
        role: str,
        content: str,
        db: AsyncSession,
        *,
        citations: Optional[list[dict]] = None,
    ) -> ChatMessageModel:
        """追加一条消息，并同步维护 thread.message_count / last_message_at。"""
        sequence_no = await ChatRepo._next_sequence_no(thread.id, db)
        message = ChatMessageModel(
            thread_id=thread.id,
            sequence_no=sequence_no,
            role=role,
            content=content,
            meta_json={"citations": citations} if citations else {},
        )
        db.add(message)

        thread.message_count = (thread.message_count or 0) + 1
        thread.last_message_at = datetime.now()

        await db.commit()
        await db.refresh(message)
        await db.refresh(thread)
        return message

    @staticmethod
    async def list_messages(
        thread_id: str, user: User, db: AsyncSession
    ) -> list[ChatMessageModel]:
        """按 sequence_no 升序返回会话下的消息（归属校验由路由层做）。"""
        # 复用 get_thread 做归属校验
        await ChatRepo.get_thread(thread_id, user, db)
        result = await db.execute(
            select(ChatMessageModel)
            .where(
                ChatMessageModel.thread_id == thread_id,
                ChatMessageModel.is_deleted == 0,
            )
            .order_by(ChatMessageModel.sequence_no.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def delete_message(
        message_id: str, user: User, db: AsyncSession
    ) -> ChatMessageModel:
        """软删单条消息，同时校验归属（必须属于该用户的某个会话）。"""
        result = await db.execute(
            select(ChatMessageModel).where(
                ChatMessageModel.id == message_id,
                ChatMessageModel.is_deleted == 0,
            )
        )
        message = result.scalar_one_or_none()
        if not message:
            raise HTTPException(status_code=400, detail="消息不存在")
        # 校验消息所属会话的归属
        await ChatRepo.get_thread(message.thread_id, user, db)
        message.is_deleted = 1
        await db.commit()
        await db.refresh(message)
        return message

    @staticmethod
    async def get_recent_messages(
        thread_id: str,
        db: AsyncSession,
        *,
        limit: Optional[int] = None,
    ) -> list[ChatMessageModel]:
        """
        取最近 N 条未删除消息用于拼 LLM 历史，按 sequence_no 升序返回。
        limit 默认读 settings.THREAD_KEEP_RECENT_MSGS。
        """
        n = limit if limit is not None else settings.THREAD_KEEP_RECENT_MSGS
        # 先按 desc 取最近 N 条，再按 asc 排序送回
        result = await db.execute(
            select(ChatMessageModel)
            .where(
                ChatMessageModel.thread_id == thread_id,
                ChatMessageModel.is_deleted == 0,
            )
            .order_by(ChatMessageModel.sequence_no.desc())
            .limit(n)
        )
        items = list(result.scalars().all())
        items.reverse()
        return items
