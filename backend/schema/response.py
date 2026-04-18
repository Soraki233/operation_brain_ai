from typing import Generic, TypeVar, List
from pydantic import BaseModel, Field


T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    code: int
    message: str
    data: T | None = None



# 分页响应体（通用）
class PagedResponseSchema(BaseModel, Generic[T]):
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页条数")
    items: List[T] = Field(..., description="数据列表")
