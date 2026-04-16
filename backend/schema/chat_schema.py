from datetime import datetime

from pydantic import BaseModel, Field


class ChatAskSchema(BaseModel):
    question: str = Field(..., description="用户问题")
    thread_id: str | None = Field(default=None, description="线程ID")
    folder_ids: list[str] | None = Field(default=None, description="限定文件夹")
    file_ids: list[str] | None = Field(default=None, description="限定文件")
    top_k: int = Field(default=5, ge=1, le=10)


class ChatReferenceSchema(BaseModel):
    chunk_id: str
    file_id: str
    filename: str
    chunk_index: int
    meta: dict
    score: float


class ChatAskDataSchema(BaseModel):
    thread_id: str
    answer: str
    references: list[ChatReferenceSchema]


class ChatMessageItemSchema(BaseModel):
    id: str
    thread_id: str
    parent_message_id: str | None
    sequence_no: int
    role: str
    content: str
    meta_json: dict
    created_at: datetime