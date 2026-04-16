from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

# 知识库范围，个人/共享
KnowledgeScope = Literal["personal", "shared"]

# 创建用户时会自动创建一个个人知识库，无需手动创建
# 创建知识库请求体
# class KnowledgeBaseCreateSchema(BaseModel):
#     name: str = Field(..., min_length=1, max_length=100, description="知识库名称")
#     description: Optional[str] = Field(default=None, description="知识库描述")
#     scope: KnowledgeScope = Field(..., description="知识库范围")


# 更新知识库请求体
class KnowledgeBaseUpdateSchema(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    is_active: Optional[int] = Field(default=None)

    @model_validator(mode="after")
    def validate_any_field(self):
        if self.name is None and self.description is None and self.is_active is None:
            raise ValueError("至少提供一个更新字段")
        return self


# 创建文件夹请求体
class KnowledgeFolderCreateSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="文件夹名称")
    parent_id: Optional[str] = Field(default=None, description="父文件夹ID，当前可不传")


# 更新文件夹请求体
class KnowledgeFolderUpdateSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="新文件夹名称")


# 删除文件夹请求体
class KnowledgeFolderDeleteSchema(BaseModel):
    folder_id: str = Field(..., description="文件夹ID")


# 更新文件请求体
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
