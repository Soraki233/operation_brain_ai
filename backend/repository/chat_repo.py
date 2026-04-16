from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.chat import ChatMessage, ChatThread


async def create_chat_thread(
    db: AsyncSession,
    *,
    title: str,
) -> ChatThread:
    row = ChatThread(
        title=title[:200] or "新对话",
        last_message_at=datetime.utcnow(),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_chat_thread(
    db: AsyncSession,
    thread_id: str,
) -> ChatThread | None:
    stmt = select(ChatThread).where(
        ChatThread.id == thread_id,
        ChatThread.is_deleted == 0,
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def get_next_sequence_no(
    db: AsyncSession,
    thread_id: str,
) -> int:
    stmt = select(func.max(ChatMessage.sequence_no)).where(
        ChatMessage.thread_id == thread_id,
        ChatMessage.is_deleted == 0,
    )
    max_no = (await db.execute(stmt)).scalar()
    return (max_no or 0) + 1


async def append_chat_message(
    db: AsyncSession,
    *,
    thread_id: str,
    role: str,
    content: str,
    parent_message_id: str | None = None,
    tokens_estimate: int = 0,
    meta_json: dict | None = None,
) -> ChatMessage:
    seq = await get_next_sequence_no(db, thread_id)

    row = ChatMessage(
        thread_id=thread_id,
        parent_message_id=parent_message_id,
        sequence_no=seq,
        role=role,
        content=content,
        tokens_estimate=tokens_estimate,
        meta_json=meta_json or {},
    )
    db.add(row)

    await db.execute(
        update(ChatThread)
        .where(ChatThread.id == thread_id, ChatThread.is_deleted == 0)
        .values(
            message_count=ChatThread.message_count + 1,
            last_message_at=datetime.utcnow(),
        )
    )

    await db.commit()
    await db.refresh(row)
    return row


async def list_unsummarized_messages(
    db: AsyncSession,
    *,
    thread_id: str,
):
    stmt = (
        select(ChatMessage)
        .where(
            ChatMessage.thread_id == thread_id,
            ChatMessage.is_deleted == 0,
            ChatMessage.is_summarized == 0,
        )
        .order_by(ChatMessage.sequence_no.asc())
    )
    return (await db.execute(stmt)).scalars().all()


async def mark_messages_summarized(
    db: AsyncSession,
    *,
    message_ids: list[str],
):
    if not message_ids:
        return

    await db.execute(
        update(ChatMessage)
        .where(ChatMessage.id.in_(message_ids), ChatMessage.is_deleted == 0)
        .values(is_summarized=1)
    )
    await db.commit()


async def update_thread_summary(
    db: AsyncSession,
    *,
    thread_id: str,
    summary: str,
):
    await db.execute(
        update(ChatThread)
        .where(ChatThread.id == thread_id, ChatThread.is_deleted == 0)
        .values(
            summary=summary,
            summary_version=ChatThread.summary_version + 1,
            updated_at=datetime.utcnow(),
        )
    )
    await db.commit()


async def list_recent_unsummarized_messages(
    db: AsyncSession,
    *,
    thread_id: str,
    limit: int,
):
    stmt = (
        select(ChatMessage)
        .where(
            ChatMessage.thread_id == thread_id,
            ChatMessage.is_deleted == 0,
            ChatMessage.is_summarized == 0,
        )
        .order_by(ChatMessage.sequence_no.desc())
        .limit(limit)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return list(reversed(rows))