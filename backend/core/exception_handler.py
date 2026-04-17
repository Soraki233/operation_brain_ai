from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.detail,
            "data": None,
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = jsonable_encoder(
        exc.errors(),
        custom_encoder={
            bytes: lambda value: value.decode("utf-8", errors="replace"),
        },
    )
    return JSONResponse(
        status_code=422,
        content={
            "code": 422,
            "message": "请求参数校验失败",
            "data": errors,
        },
    )


async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "data": str(exc),
        },
    )