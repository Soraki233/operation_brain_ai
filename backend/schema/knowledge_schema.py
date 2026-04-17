from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

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
