from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


ChatRole = Literal["user", "assistant", "system"]


# 引用来源：与 KnowledgeFile 的一个 chunk 对应
class ChatCitationSchema(BaseModel):
    file_id: str = Field(..., description="知识库文件ID")
    file_name: str = Field(..., description="文件名（文件被软删时回显'（已删除）'）")
    chunk_index: int = Field(..., description="命中 chunk 序号")
    score: float = Field(..., description="向量距离，越小越相似")
    snippet: str = Field(..., description="命中片段（已截断）")


# 创建会话
class ChatThreadCreateSchema(BaseModel):
    title: Optional[str] = Field(
        default=None, max_length=200, description="会话标题，留空则使用默认'新对话'"
    )


# 会话列表项
class ChatThreadItemSchema(BaseModel):
    model_config = {"from_attributes": True}

    id: str = Field(..., description="会话ID")
    title: str = Field(..., description="会话标题")
    summary: Optional[str] = Field(default=None, description="历史摘要")
    message_count: int = Field(..., description="消息数")
    last_message_at: Optional[datetime] = Field(default=None, description="最后消息时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


# 单条消息（含引用来源）
class ChatMessageItemSchema(BaseModel):
    id: str = Field(..., description="消息ID")
    role: ChatRole = Field(..., description="消息角色")
    content: str = Field(..., description="消息正文")
    citations: List[ChatCitationSchema] = Field(
        default_factory=list, description="引用资料（assistant 消息才有）"
    )
    created_at: datetime = Field(..., description="创建时间")


# 提问请求体
class ChatAskSchema(BaseModel):
    content: str = Field(..., min_length=1, description="用户提问")
    kb_ids: Optional[List[str]] = Field(
        default=None, description="限定检索的知识库ID列表，留空则使用当前用户可见的全部知识库"
    )
