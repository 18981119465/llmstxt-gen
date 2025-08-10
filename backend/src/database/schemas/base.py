"""
基础Pydantic schemas
"""

from datetime import datetime
from typing import Optional, TypeVar, Generic
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, ConfigDict


class BaseSchema(BaseModel):
    """基础schema类"""
    
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
            UUID: lambda v: str(v)
        }
    )


class BaseResponse(BaseSchema):
    """基础响应schema"""
    success: bool = Field(True, description="操作是否成功")
    message: str = Field("", description="响应消息")
    data: Optional[dict] = Field(None, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间戳")
    
    @field_validator('timestamp', mode='before')
    @classmethod
    def set_timestamp(cls, v):
        return v or datetime.now()


T = TypeVar('T')


class PaginatedResponse(BaseSchema, Generic[T]):
    """分页响应schema"""
    items: list[T] = Field(..., description="数据列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    total_pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")


class FilterParams(BaseSchema):
    """查询参数schema"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页大小")
    sort_by: Optional[str] = Field(None, description="排序字段")
    sort_order: Optional[str] = Field("asc", pattern="^(asc|desc)$", description="排序方向")
    search: Optional[str] = Field(None, description="搜索关键词")
    
    @field_validator('page_size')
    @classmethod
    def validate_page_size(cls, v):
        return min(v, 100)


class SuccessResponse(BaseSchema):
    """成功响应schema"""
    success: bool = Field(True, description="操作是否成功")
    message: str = Field("操作成功", description="响应消息")
    data: Optional[dict] = Field(None, description="响应数据")


class ErrorResponse(BaseSchema):
    """错误响应schema"""
    success: bool = Field(False, description="操作是否成功")
    message: str = Field(..., description="错误消息")
    error_code: Optional[str] = Field(None, description="错误代码")
    details: Optional[dict] = Field(None, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.now, description="错误时间戳")


class ValidationError(BaseSchema):
    """验证错误schema"""
    field: str = Field(..., description="字段名")
    message: str = Field(..., description="错误消息")
    value: Optional[str] = Field(None, description="错误值")


class ValidationErrorResponse(ErrorResponse):
    """验证错误响应schema"""
    validation_errors: list[ValidationError] = Field(..., description="验证错误列表")