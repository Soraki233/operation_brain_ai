from pgvector.sqlalchemy import Vector
from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from db.session import BaseModel
from core.settings import settings


# 知识库文件夹
class KnowledgeFolder(BaseModel):
    __tablename__ = "knowledge_folders"

    # parent_id: Mapped[str | None] = mapped_column(
    #     String(36), nullable=True, index=True, comment="父级文件夹ID"
    # )
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="文件夹名称")
    sort_no: Mapped[int] = mapped_column(Integer, default=0, comment="排序号")


# 知识库文件
class KnowledgeFile(BaseModel):
    __tablename__ = "knowledge_files"

    folder_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True, comment="文件夹ID"
    )
    filename: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="原始文件名"
    )
    ext: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True, comment="扩展名"
    )
    content_type: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="MIME类型"
    )
    size: Mapped[int] = mapped_column(Integer, default=0, comment="文件字节数")
    storage_path: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="文件存储路径"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        index=True,
        comment="文件状态: pending/parsing/ready/failed",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="错误信息"
    )
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, comment="切块数量")


# 知识库切块
class KnowledgeChunk(BaseModel):
    __tablename__ = "knowledge_chunks"

    file_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True, comment="文件ID"
    )
    folder_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True, comment="文件夹ID"
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="切块序号"
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="文本内容")
    meta_json: Mapped[dict] = mapped_column(
        JSONB, default=dict, comment="页码、sheet等元信息"
    )
    embedding: Mapped[list[float]] = mapped_column(
        Vector(settings.EMBEDDING_DIM), nullable=False, comment="向量"
    )
