from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class KnowledgeFolderCreateSchema(BaseModel):
    name: str = Field(..., max_length=100, description="文件夹名称")
    sort_no: int = Field(default=0, ge=0, description="排序号")

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("文件夹名称不能为空")
        if len(s) > 100:
            raise ValueError("文件夹名称不能超过100个字符")
        return s

# 知识库文件项
class KnowledgeFileItemSchema(BaseModel):
    id: str
    folder_id: str | None
    filename: str
    ext: str
    status: str
    size: int
    chunk_count: int
    created_at: datetime
    updated_at: datetime


# 分页
class PaginationSchema(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


# 知识库文件分页数据
class KnowledgeFilePageDataSchema(BaseModel):
    items: list[KnowledgeFileItemSchema]
    pagination: PaginationSchema


# 知识库文件详情
class KnowledgeFileDetailSchema(BaseModel):
    id: str
    folder_id: str | None
    filename: str
    ext: str
    content_type: str | None
    size: int
    storage_path: str
    status: str
    error_message: str | None
    chunk_count: int
    created_at: datetime
    updated_at: datetime


# 上传知识库文件项
class UploadKnowledgeFileItemSchema(BaseModel):
    id: str
    filename: str
    status: str
    size: int