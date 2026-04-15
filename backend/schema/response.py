from typing import Generic, TypeVar
from pydantic import BaseModel
from pydantic.generics import GenericModel

T = TypeVar("T")


class ResponseModel(GenericModel, Generic[T]):
    code: int
    message: str
    data: T | None = None