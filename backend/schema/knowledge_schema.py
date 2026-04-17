from typing import Generic, List, Literal, Optional, TypeVar
from fastapi import UploadFile
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime

T = TypeVar("T")

# 知识库范围，个人/共享
KnowledgeScope = Literal["personal", "shared"]


# 创建用户时会自动创建一个个人知识库，无需手动创建
# 创建知识库请求体
class KnowledgeBaseCreateSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="知识库名称")
    scope: KnowledgeScope = Field(..., description="知识库范围")
    owner_user_id: Optional[str] = Field(default=None, description="知识库归属用户ID")
    creator_user_id: str = Field(..., description="创建人ID")


# 知识库列表响应体
class KnowledgeBaseResponseSchema(BaseModel):
    model_config = {"from_attributes": True}

    id: str = Field(..., description="知识库ID")
    name: str = Field(..., description="知识库名称")
    scope: KnowledgeScope = Field(..., description="知识库范围")
    owner_user_id: Optional[str] = Field(default=None, description="知识库归属用户ID")
    creator_user_id: str = Field(..., description="创建人ID")

    @model_validator(mode="after")
    def validate_response(self):
        if self.scope == "personal":
            self.owner_user_id = self.creator_user_id
        return self


# 更新知识库
class KnowledgeBaseUpdateSchema(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    is_active: Optional[int] = Field(default=None)

    @model_validator(mode="after")
    def validate_any_field(self):
        if self.name is None and self.description is None and self.is_active is None:
            raise ValueError("至少提供一个更新字段")
        return self


# 获取知识库下的文件夹
class KnowledgeFolderRequestSchema(BaseModel):
    kb_id: str = Field(..., description="知识库ID")

    @model_validator(mode="after")
    def validate_request(self):
        if not self.kb_id:
            raise ValueError("知识库ID不能为空")
        return self


# 创建文件夹
class KnowledgeFolderCreateSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="文件夹名称")
    kb_id: str = Field(..., description="知识库ID")

    @model_validator(mode="after")
    def validate_request(self):
        if not self.kb_id:
            raise ValueError("知识库ID不能为空")
        if not self.name:
            raise ValueError("文件夹名称不能为空")
        return self


class KnowledgeFolderResponseSchema(BaseModel):
    model_config = {"from_attributes": True}

    id: str = Field(..., description="文件夹ID")
    kb_id: str = Field(..., description="知识库ID")
    name: str = Field(..., description="文件夹名称")
    creator_user_id: str = Field(..., description="创建人ID")


# 更新文件夹
class KnowledgeFolderUpdateSchema(BaseModel):
    id: str = Field(..., description="文件夹ID")
    name: str = Field(..., min_length=1, max_length=100, description="新文件夹名称")


# 删除文件夹
class KnowledgeFolderDeleteSchema(BaseModel):
    folder_id: str = Field(..., description="文件夹ID")


# 更新文件
class KnowledgeFileUpdateSchema(BaseModel):
    file_name: Optional[str] = Field(
        default=None, min_length=1, max_length=255, description="新文件名"
    )
    folder_id: Optional[str] = Field(default=None, description="目标文件夹ID")
    move_to_root: bool = Field(default=False, description="是否移动到知识库根目录")

    @model_validator(mode="after")
    def validate_update(self):
        if self.move_to_root and self.folder_id:
            raise ValueError("folder_id 与 move_to_root 不能同时传")
        if self.file_name is None and self.folder_id is None and not self.move_to_root:
            raise ValueError("至少提供一个更新字段")
        return self


# 创建知识库文件（多文件）请求体
class KnowledgeFileCreateRequestSchema(BaseModel):
    kb_id: str = Field(..., description="知识库ID")
    folder_id: Optional[str] = Field(default=None, description="文件夹ID")
    files: List[UploadFile] = Field(..., description="文件列表")


# 创建知识库文件（多文件）响应体
class KnowledgeFileCreateResponseSchema(BaseModel):
    model_config = {"from_attributes": True}
    id: str = Field(..., description="文件ID")
    kb_id: str = Field(..., description="知识库ID")
    folder_id: Optional[str] = Field(default=None, description="文件夹ID")
    file_name: str = Field(..., description="文件名")
    file_ext: str = Field(..., description="文件扩展名")
    mime_type: Optional[str] = Field(default=None, description="MIME类型")
    file_size: int = Field(..., description="文件大小")
    storage_path: str = Field(..., description="本地存储路径")
    parse_status: str = Field(..., description="解析状态")
    chunk_count: int = Field(..., description="切块数")
    uploaded_by: str = Field(..., description="上传人ID")
    error_message: Optional[str] = Field(default=None, description="失败原因")


# 分页响应体（通用）
class PagedResponseSchema(BaseModel, Generic[T]):
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页条数")
    items: List[T] = Field(..., description="数据列表")


# 查询文件列表请求体
class KnowledgeFileListRequestSchema(BaseModel):
    kb_id: str = Field(..., description="知识库ID")
    folder_id: Optional[str] = Field(default=None, description="文件夹ID，为空则查询知识库根目录")
    keyword: Optional[str] = Field(default=None, max_length=100, description="文件名模糊搜索关键词")
    page: int = Field(default=1, ge=1, description="页码，从1开始")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数，最大100")

    @field_validator("keyword", "folder_id", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        """空字符串统一转为 None，避免前端传 keyword='' 时触发校验错误"""
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

    @model_validator(mode="after")
    def validate_request(self):
        if not self.kb_id:
            raise ValueError("知识库ID不能为空")
        return self


# 文件列表单条响应体
class KnowledgeFileItemSchema(BaseModel):
    model_config = {"from_attributes": True}

    id: str = Field(..., description="文件ID")
    kb_id: str = Field(..., description="知识库ID")
    folder_id: Optional[str] = Field(default=None, description="文件夹ID")
    file_name: str = Field(..., description="文件名")
    file_ext: str = Field(..., description="文件扩展名")
    mime_type: Optional[str] = Field(default=None, description="MIME类型")
    file_size: int = Field(..., description="文件大小（字节）")
    parse_status: str = Field(..., description="解析状态: pending/processing/success/failed")
    chunk_count: int = Field(..., description="切块数")
    uploaded_by: str = Field(..., description="上传人ID")
    error_message: Optional[str] = Field(default=None, description="失败原因")
    created_at: datetime = Field(..., description="上传时间")
