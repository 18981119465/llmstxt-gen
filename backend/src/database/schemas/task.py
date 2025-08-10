"""
任务相关schemas
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, field_validator, constr

from .base import BaseSchema, BaseResponse


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """任务类型枚举"""
    DOCUMENT_PROCESS = "document_process"
    WEB_CRAWL = "web_crawl"
    AI_ANALYSIS = "ai_analysis"
    DATA_EXPORT = "data_export"
    SYSTEM_BACKUP = "system_backup"
    NOTIFICATION = "notification"
    OTHER = "other"


class TaskPriority(str, Enum):
    """任务优先级枚举"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ResultType(str, Enum):
    """结果类型枚举"""
    TEXT = "text"
    JSON = "json"
    FILE = "file"
    BINARY = "binary"


class ScheduleType(str, Enum):
    """调度类型枚举"""
    CRON = "cron"
    INTERVAL = "interval"
    ONCE = "once"


class DependencyType(str, Enum):
    """依赖类型枚举"""
    COMPLETION = "completion"
    SUCCESS = "success"
    OUTPUT = "output"


class LogLevel(str, Enum):
    """日志级别枚举"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(str, Enum):
    """指标类型枚举"""
    GAUGE = "gauge"
    COUNTER = "counter"
    HISTOGRAM = "histogram"


# 任务schemas
class TaskBase(BaseSchema):
    """任务基础schema"""
    task_type: TaskType = Field(..., description="任务类型")
    name: constr(min_length=1, max_length=255) = Field(..., description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    priority: TaskPriority = Field(TaskPriority.NORMAL, description="任务优先级")
    config: Optional[Dict[str, Any]] = Field(None, description="任务配置")
    parameters: Optional[Dict[str, Any]] = Field(None, description="任务参数")
    is_recurring: bool = Field(False, description="是否循环任务")
    recurring_config: Optional[Dict[str, Any]] = Field(None, description="循环配置")
    max_retries: int = Field(3, ge=0, le=10, description="最大重试次数")
    estimated_duration: Optional[int] = Field(None, ge=0, description="预计持续时间(秒)")


class TaskCreate(TaskBase):
    """任务创建schema"""
    project_id: Optional[UUID] = Field(None, description="项目ID")
    document_id: Optional[UUID] = Field(None, description="文档ID")
    created_by_id: UUID = Field(..., description="创建者ID")
    assigned_to_id: Optional[UUID] = Field(None, description="分配给谁")
    parent_task_id: Optional[UUID] = Field(None, description="父任务ID")


class TaskUpdate(BaseSchema):
    """任务更新schema"""
    name: Optional[constr(max_length=255)] = Field(None, description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    priority: Optional[TaskPriority] = Field(None, description="任务优先级")
    status: Optional[TaskStatus] = Field(None, description="任务状态")
    progress: Optional[int] = Field(None, ge=0, le=100, description="进度(0-100)")
    config: Optional[Dict[str, Any]] = Field(None, description="任务配置")
    parameters: Optional[Dict[str, Any]] = Field(None, description="任务参数")
    result: Optional[Dict[str, Any]] = Field(None, description="任务结果")
    result_summary: Optional[str] = Field(None, description="结果摘要")
    output_files: Optional[List[str]] = Field(None, description="输出文件")
    error_message: Optional[str] = Field(None, description="错误消息")
    error_code: Optional[str] = Field(None, description="错误代码")
    assigned_to_id: Optional[UUID] = Field(None, description="分配给谁")
    max_retries: Optional[int] = Field(None, ge=0, le=10, description="最大重试次数")
    estimated_duration: Optional[int] = Field(None, ge=0, description="预计持续时间(秒)")


class TaskResponse(TaskBase):
    """任务响应schema"""
    id: UUID = Field(..., description="任务ID")
    project_id: Optional[UUID] = Field(None, description="项目ID")
    document_id: Optional[UUID] = Field(None, description="文档ID")
    status: TaskStatus = Field(..., description="任务状态")
    progress: int = Field(..., description="进度(0-100)")
    result: Optional[Dict[str, Any]] = Field(None, description="任务结果")
    result_summary: Optional[str] = Field(None, description="结果摘要")
    output_files: Optional[List[str]] = Field(None, description="输出文件")
    error_message: Optional[str] = Field(None, description="错误消息")
    error_code: Optional[str] = Field(None, description="错误代码")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    actual_duration: Optional[int] = Field(None, description="实际持续时间(秒)")
    parent_task_id: Optional[UUID] = Field(None, description="父任务ID")
    retry_count: int = Field(..., description="重试次数")
    processed_items: int = Field(..., description="处理项目数")
    total_items: int = Field(..., description="总项目数")
    success_items: int = Field(..., description="成功项目数")
    failed_items: int = Field(..., description="失败项目数")
    created_by_id: UUID = Field(..., description="创建者ID")
    assigned_to_id: Optional[UUID] = Field(None, description="分配给谁")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    project: Optional['ProjectResponse'] = Field(None, description="项目信息")
    document: Optional['DocumentResponse'] = Field(None, description="文档信息")
    created_by: Optional['UserResponse'] = Field(None, description="创建者信息")
    assigned_to: Optional['UserResponse'] = Field(None, description="分配给谁")


# 任务结果schemas
class TaskResultBase(BaseSchema):
    """任务结果基础schema"""
    result_type: ResultType = Field(..., description="结果类型")
    result_data: Optional[Dict[str, Any]] = Field(None, description="结果数据")
    result_text: Optional[str] = Field(None, description="结果文本")
    result_file_path: Optional[str] = Field(None, description="结果文件路径")
    result_file_size: Optional[int] = Field(None, ge=0, description="结果文件大小")
    processing_time: Optional[int] = Field(None, ge=0, description="处理时间(毫秒)")
    memory_usage: Optional[int] = Field(None, ge=0, description="内存使用(字节)")
    cpu_usage: Optional[int] = Field(None, ge=0, le=100, description="CPU使用率(%)")
    quality_score: Optional[int] = Field(None, ge=0, le=100, description="质量评分")
    confidence_score: Optional[int] = Field(None, ge=0, le=100, description="置信度评分")
    accuracy_score: Optional[int] = Field(None, ge=0, le=100, description="准确度评分")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    tags: Optional[List[str]] = Field(None, description="标签")
    is_valid: bool = Field(True, description="是否有效")
    validation_errors: Optional[Dict[str, Any]] = Field(None, description="验证错误")


class TaskResultCreate(TaskResultBase):
    """任务结果创建schema"""
    task_id: UUID = Field(..., description="任务ID")


class TaskResultUpdate(BaseSchema):
    """任务结果更新schema"""
    result_type: Optional[ResultType] = Field(None, description="结果类型")
    result_data: Optional[Dict[str, Any]] = Field(None, description="结果数据")
    result_text: Optional[str] = Field(None, description="结果文本")
    result_file_path: Optional[str] = Field(None, description="结果文件路径")
    result_file_size: Optional[int] = Field(None, ge=0, description="结果文件大小")
    processing_time: Optional[int] = Field(None, ge=0, description="处理时间(毫秒)")
    memory_usage: Optional[int] = Field(None, ge=0, description="内存使用(字节)")
    cpu_usage: Optional[int] = Field(None, ge=0, le=100, description="CPU使用率(%)")
    quality_score: Optional[int] = Field(None, ge=0, le=100, description="质量评分")
    confidence_score: Optional[int] = Field(None, ge=0, le=100, description="置信度评分")
    accuracy_score: Optional[int] = Field(None, ge=0, le=100, description="准确度评分")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    tags: Optional[List[str]] = Field(None, description="标签")
    is_valid: Optional[bool] = Field(None, description="是否有效")
    validation_errors: Optional[Dict[str, Any]] = Field(None, description="验证错误")


class TaskResultResponse(TaskResultBase):
    """任务结果响应schema"""
    id: UUID = Field(..., description="结果ID")
    task_id: UUID = Field(..., description="任务ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


# 任务日志schemas
class TaskLogBase(BaseSchema):
    """任务日志基础schema"""
    log_level: LogLevel = Field(LogLevel.INFO, description="日志级别")
    message: str = Field(..., description="日志消息")
    details: Optional[Dict[str, Any]] = Field(None, description="日志详情")
    stack_trace: Optional[str] = Field(None, description="堆栈跟踪")
    source: Optional[constr(max_length=100)] = Field(None, description="日志来源")
    component: Optional[constr(max_length=100)] = Field(None, description="组件名称")
    function_name: Optional[constr(max_length=100)] = Field(None, description="函数名称")
    line_number: Optional[int] = Field(None, ge=0, description="行号")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文")
    session_id: Optional[str] = Field(None, description="会话ID")
    request_id: Optional[str] = Field(None, description="请求ID")
    execution_time: Optional[int] = Field(None, ge=0, description="执行时间(毫秒)")
    memory_usage: Optional[int] = Field(None, ge=0, description="内存使用(字节)")
    tags: Optional[List[str]] = Field(None, description="标签")


class TaskLogCreate(TaskLogBase):
    """任务日志创建schema"""
    task_id: UUID = Field(..., description="任务ID")
    user_id: Optional[UUID] = Field(None, description="用户ID")


class TaskLogUpdate(BaseSchema):
    """任务日志更新schema"""
    log_level: Optional[LogLevel] = Field(None, description="日志级别")
    message: Optional[str] = Field(None, description="日志消息")
    details: Optional[Dict[str, Any]] = Field(None, description="日志详情")
    stack_trace: Optional[str] = Field(None, description="堆栈跟踪")
    source: Optional[constr(max_length=100)] = Field(None, description="日志来源")
    component: Optional[constr(max_length=100)] = Field(None, description="组件名称")
    function_name: Optional[constr(max_length=100)] = Field(None, description="函数名称")
    line_number: Optional[int] = Field(None, ge=0, description="行号")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文")
    user_id: Optional[UUID] = Field(None, description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    request_id: Optional[str] = Field(None, description="请求ID")
    execution_time: Optional[int] = Field(None, ge=0, description="执行时间(毫秒)")
    memory_usage: Optional[int] = Field(None, ge=0, description="内存使用(字节)")
    tags: Optional[List[str]] = Field(None, description="标签")


class TaskLogResponse(TaskLogBase):
    """任务日志响应schema"""
    id: UUID = Field(..., description="日志ID")
    task_id: UUID = Field(..., description="任务ID")
    user_id: Optional[UUID] = Field(None, description="用户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    user: Optional['UserResponse'] = Field(None, description="用户信息")


# 任务调度schemas
class TaskScheduleBase(BaseSchema):
    """任务调度基础schema"""
    schedule_name: constr(min_length=1, max_length=100) = Field(..., description="调度名称")
    schedule_type: ScheduleType = Field(..., description="调度类型")
    schedule_config: Dict[str, Any] = Field(..., description="调度配置")
    is_active: bool = Field(True, description="是否激活")
    next_run_time: datetime = Field(..., description="下次运行时间")
    timezone: str = Field("UTC", description="时区")
    max_runs: Optional[int] = Field(None, ge=1, description="最大运行次数")
    end_time: Optional[datetime] = Field(None, description="结束时间")


class TaskScheduleCreate(TaskScheduleBase):
    """任务调度创建schema"""
    task_id: UUID = Field(..., description="任务ID")
    created_by_id: UUID = Field(..., description="创建者ID")


class TaskScheduleUpdate(BaseSchema):
    """任务调度更新schema"""
    schedule_name: Optional[constr(max_length=100)] = Field(None, description="调度名称")
    schedule_config: Optional[Dict[str, Any]] = Field(None, description="调度配置")
    is_active: Optional[bool] = Field(None, description="是否激活")
    next_run_time: Optional[datetime] = Field(None, description="下次运行时间")
    timezone: Optional[str] = Field(None, description="时区")
    max_runs: Optional[int] = Field(None, ge=1, description="最大运行次数")
    end_time: Optional[datetime] = Field(None, description="结束时间")


class TaskScheduleResponse(TaskScheduleBase):
    """任务调度响应schema"""
    id: UUID = Field(..., description="调度ID")
    task_id: UUID = Field(..., description="任务ID")
    last_run_time: Optional[datetime] = Field(None, description="最后运行时间")
    run_count: int = Field(..., description="运行次数")
    created_by_id: UUID = Field(..., description="创建者ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: Optional['UserResponse'] = Field(None, description="创建者信息")


# 任务依赖schemas
class TaskDependencyBase(BaseSchema):
    """任务依赖基础schema"""
    depends_on_task_id: UUID = Field(..., description="依赖的任务ID")
    dependency_type: DependencyType = Field(DependencyType.COMPLETION, description="依赖类型")
    is_satisfied: bool = Field(False, description="是否满足")
    config: Optional[Dict[str, Any]] = Field(None, description="依赖配置")


class TaskDependencyCreate(TaskDependencyBase):
    """任务依赖创建schema"""
    task_id: UUID = Field(..., description="任务ID")


class TaskDependencyUpdate(BaseSchema):
    """任务依赖更新schema"""
    depends_on_task_id: Optional[UUID] = Field(None, description="依赖的任务ID")
    dependency_type: Optional[DependencyType] = Field(None, description="依赖类型")
    is_satisfied: Optional[bool] = Field(None, description="是否满足")
    config: Optional[Dict[str, Any]] = Field(None, description="依赖配置")


class TaskDependencyResponse(TaskDependencyBase):
    """任务依赖响应schema"""
    id: UUID = Field(..., description="依赖ID")
    task_id: UUID = Field(..., description="任务ID")
    satisfied_at: Optional[datetime] = Field(None, description="满足时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


# 任务搜索schemas
class TaskSearchParams(BaseSchema):
    """任务搜索参数schema"""
    search: Optional[str] = Field(None, description="搜索关键词")
    task_type: Optional[TaskType] = Field(None, description="任务类型")
    status: Optional[TaskStatus] = Field(None, description="任务状态")
    priority: Optional[TaskPriority] = Field(None, description="任务优先级")
    project_id: Optional[UUID] = Field(None, description="项目ID")
    document_id: Optional[UUID] = Field(None, description="文档ID")
    created_by_id: Optional[UUID] = Field(None, description="创建者ID")
    assigned_to_id: Optional[UUID] = Field(None, description="分配给谁")
    created_after: Optional[datetime] = Field(None, description="创建时间之后")
    created_before: Optional[datetime] = Field(None, description="创建时间之前")
    is_recurring: Optional[bool] = Field(None, description="是否循环任务")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页大小")
    sort_by: Optional[str] = Field("created_at", description="排序字段")
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$", description="排序方向")


# 更新前向引用
from .user import UserResponse
from .project import ProjectResponse
from .document import DocumentResponse
TaskResponse.model_rebuild()
TaskLogResponse.model_rebuild()
TaskScheduleResponse.model_rebuild()