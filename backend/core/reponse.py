from typing import Any
from schema.response import ResponseModel


def success_response(
    data: Any = None,
    message: str = "success",
    code: int = 200,
) -> ResponseModel:
    return ResponseModel(
        code=code,
        message=message,
        data=data,
    )


def error_response(
    message: str = "error",
    code: int = 400,
    data: Any = None,
) -> ResponseModel:
    return ResponseModel(
        code=code,
        message=message,
        data=data,
    )


def no_auth_response(
    message: str = "no auth",
    code: int = 401,
    data: Any = None,
) -> ResponseModel:
    return ResponseModel(
        code=code,
        message=message,
        data=data,
    )
