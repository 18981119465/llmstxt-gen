"""
API框架异常处理模块
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Optional, Dict, Any
import logging
from ..schemas.response import ErrorResponse

logger = logging.getLogger(__name__)


class APIException(Exception):
    """API异常基类"""
    
    def __init__(self, 
                 error_code: str,
                 message: str,
                 status_code: int = 400,
                 details: Optional[Dict[str, Any]] = None):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(APIException):
    """认证异常"""
    
    def __init__(self, message: str = "认证失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code="AUTHENTICATION_ERROR",
            message=message,
            status_code=401,
            details=details
        )


class AuthorizationError(APIException):
    """授权异常"""
    
    def __init__(self, message: str = "权限不足", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code="AUTHORIZATION_ERROR",
            message=message,
            status_code=403,
            details=details
        )


class ValidationError(APIException):
    """验证异常"""
    
    def __init__(self, message: str = "数据验证失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code="VALIDATION_ERROR",
            message=message,
            status_code=422,
            details=details
        )


class ResourceNotFoundError(APIException):
    """资源未找到异常"""
    
    def __init__(self, resource: str = "资源", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code="RESOURCE_NOT_FOUND",
            message=f"{resource}未找到",
            status_code=404,
            details=details
        )


class RateLimitError(APIException):
    """限流异常"""
    
    def __init__(self, message: str = "请求频率过高", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code="RATE_LIMIT_ERROR",
            message=message,
            status_code=429,
            details=details
        )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP异常处理器"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.warning(
        f"HTTP异常: {exc.status_code} - {exc.detail}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code
        }
    )
    
    error_code = "HTTP_ERROR"
    if exc.status_code == 401:
        error_code = "AUTHENTICATION_ERROR"
    elif exc.status_code == 403:
        error_code = "AUTHORIZATION_ERROR"
    elif exc.status_code == 404:
        error_code = "RESOURCE_NOT_FOUND"
    elif exc.status_code == 422:
        error_code = "VALIDATION_ERROR"
    elif exc.status_code == 429:
        error_code = "RATE_LIMIT_ERROR"
    elif exc.status_code >= 500:
        error_code = "INTERNAL_SERVER_ERROR"
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            error=error_code,
            message=str(exc.detail),
            request_id=request_id
        ).dict()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """验证异常处理器"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.warning(
        f"验证异常: {exc}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # 格式化验证错误
    validation_errors = []
    for error in exc.errors():
        validation_errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            success=False,
            error="VALIDATION_ERROR",
            message="数据验证失败",
            request_id=request_id,
            details={"validation_errors": validation_errors}
        ).dict()
    )


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """API异常处理器"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.warning(
        f"API异常: {exc.error_code} - {exc.message}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "error_code": exc.error_code,
            "status_code": exc.status_code
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            error=exc.error_code,
            message=exc.message,
            request_id=request_id,
            details=exc.details
        ).dict()
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.error(
        f"未处理的异常: {exc}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            success=False,
            error="INTERNAL_SERVER_ERROR",
            message="服务器内部错误",
            request_id=request_id
        ).dict()
    )