"""
API响应数据模型
"""

from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List, Generic, TypeVar
from datetime import datetime, timezone
from enum import Enum

T = TypeVar('T')


class ResponseStatus(str, Enum):
    """响应状态枚举"""
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
    PROCESSING = "processing"


class StandardResponse(BaseModel, Generic[T]):
    """标准响应模型"""
    
    success: bool = Field(..., description="请求是否成功")
    data: Optional[T] = Field(None, description="响应数据")
    message: str = Field(..., description="响应消息")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="响应时间戳")
    request_id: Optional[str] = Field(None, description="请求ID")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseModel):
    """错误响应模型"""
    
    success: bool = Field(False, description="请求是否成功")
    error: str = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="错误时间戳")
    request_id: Optional[str] = Field(None, description="请求ID")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaginationMeta(BaseModel):
    """分页元数据模型"""
    
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    total_pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模型"""
    
    success: bool = Field(True, description="请求是否成功")
    data: List[T] = Field(..., description="响应数据列表")
    meta: PaginationMeta = Field(..., description="分页元数据")
    message: str = Field("获取数据成功", description="响应消息")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="响应时间戳")
    request_id: Optional[str] = Field(None, description="请求ID")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BatchResponse(BaseModel, Generic[T]):
    """批量操作响应模型"""
    
    success: bool = Field(True, description="请求是否成功")
    data: List[T] = Field(..., description="操作结果列表")
    summary: Dict[str, int] = Field(..., description="操作摘要")
    message: str = Field("批量操作完成", description="响应消息")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="响应时间戳")
    request_id: Optional[str] = Field(None, description="请求ID")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FileUploadResponse(BaseModel):
    """文件上传响应模型"""
    
    success: bool = Field(True, description="上传是否成功")
    data: Dict[str, Any] = Field(..., description="文件信息")
    message: str = Field("文件上传成功", description="响应消息")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="响应时间戳")
    request_id: Optional[str] = Field(None, description="请求ID")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class HealthCheckResponse(BaseModel):
    """健康检查响应模型"""
    
    success: bool = Field(True, description="健康检查是否通过")
    data: Dict[str, Any] = Field(..., description="健康状态数据")
    message: str = Field("健康检查通过", description="响应消息")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="响应时间戳")
    request_id: Optional[str] = Field(None, description="请求ID")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ServiceStatusResponse(BaseModel):
    """服务状态响应模型"""
    
    success: bool = Field(True, description="请求是否成功")
    data: Dict[str, Any] = Field(..., description="服务状态数据")
    message: str = Field("获取服务状态成功", description="响应消息")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="响应时间戳")
    request_id: Optional[str] = Field(None, description="请求ID")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ConfigResponse(BaseModel):
    """配置响应模型"""
    
    success: bool = Field(True, description="请求是否成功")
    data: Dict[str, Any] = Field(..., description="配置数据")
    message: str = Field("获取配置成功", description="响应消息")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="响应时间戳")
    request_id: Optional[str] = Field(None, description="请求ID")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ValidationErrorResponse(BaseModel):
    """验证错误响应模型"""
    
    success: bool = Field(False, description="请求是否成功")
    error: str = Field("VALIDATION_ERROR", description="错误代码")
    message: str = Field("数据验证失败", description="错误消息")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="错误时间戳")
    request_id: Optional[str] = Field(None, description="请求ID")
    details: Dict[str, List[str]] = Field(..., description="验证错误详情")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RateLimitResponse(BaseModel):
    """限流响应模型"""
    
    success: bool = Field(False, description="请求是否成功")
    error: str = Field("RATE_LIMIT_ERROR", description="错误代码")
    message: str = Field("请求频率过高", description="错误消息")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="错误时间戳")
    request_id: Optional[str] = Field(None, description="请求ID")
    details: Dict[str, Any] = Field(..., description="限流详情")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# 响应工厂函数
def create_success_response(
    data: Any = None,
    message: str = "操作成功",
    request_id: Optional[str] = None
) -> StandardResponse:
    """创建成功响应"""
    return StandardResponse(
        success=True,
        data=data,
        message=message,
        request_id=request_id
    )


def create_error_response(
    error: str,
    message: str,
    request_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> ErrorResponse:
    """创建错误响应"""
    return ErrorResponse(
        success=False,
        error=error,
        message=message,
        request_id=request_id,
        details=details
    )


def create_paginated_response(
    data: List[Any],
    total: int,
    page: int,
    page_size: int,
    message: str = "获取数据成功",
    request_id: Optional[str] = None
) -> PaginatedResponse:
    """创建分页响应"""
    total_pages = (total + page_size - 1) // page_size
    has_next = page < total_pages
    has_prev = page > 1
    
    meta = PaginationMeta(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev
    )
    
    return PaginatedResponse(
        data=data,
        meta=meta,
        message=message,
        request_id=request_id
    )


def create_batch_response(
    data: List[Any],
    summary: Dict[str, int],
    message: str = "批量操作完成",
    request_id: Optional[str] = None
) -> BatchResponse:
    """创建批量操作响应"""
    return BatchResponse(
        data=data,
        summary=summary,
        message=message,
        request_id=request_id
    )


def create_health_check_response(
    health_data: Dict[str, Any],
    message: str = "健康检查通过",
    request_id: Optional[str] = None
) -> HealthCheckResponse:
    """创建健康检查响应"""
    return HealthCheckResponse(
        data=health_data,
        message=message,
        request_id=request_id
    )


def create_service_status_response(
    status_data: Dict[str, Any],
    message: str = "获取服务状态成功",
    request_id: Optional[str] = None
) -> ServiceStatusResponse:
    """创建服务状态响应"""
    return ServiceStatusResponse(
        data=status_data,
        message=message,
        request_id=request_id
    )