from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from db.session import BaseModel

class ChatThread(BaseModel):
    __tablename__ = "chat_threads"

    title: Mapped[str] = mapped_column(
        String(200), nullable=False, default="新对话", comment="线程标题"
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True, comment="历史摘要")
    summary_version: Mapped[int] = mapped_column(Integer, default=0, comment="摘要版本")
    message_count: Mapped[int] = mapped_column(Integer, default=0, comment="消息数")
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="最后消息时间"
    )


# 对话消息
class ChatMessage(BaseModel):
    __tablename__ = "chat_messages"

    thread_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True, comment="线程ID"
    )
    parent_message_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True, comment="父消息ID"
    )
    sequence_no: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True, comment="线程内顺序号"
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="user/assistant/system"
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="消息内容")
    tokens_estimate: Mapped[int] = mapped_column(
        Integer, default=0, comment="粗略token数"
    )
    meta_json: Mapped[dict] = mapped_column(JSONB, default=dict, comment="引用来源等")
    is_summarized: Mapped[int] = mapped_column(
        Integer, default=0, comment="是否已汇总 0/1"
    )
