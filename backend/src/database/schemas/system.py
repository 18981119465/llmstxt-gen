"""
系统相关schemas
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, field_validator, constr

from .base import BaseSchema, BaseResponse


class ConfigType(str, Enum):
    """配置类型枚举"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    JSON = "json"


class ConfigCategory(str, Enum):
    """配置类别枚举"""
    GENERAL = "general"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DATABASE = "database"
    API = "api"
    NOTIFICATION = "notification"
    BACKUP = "backup"
    MONITORING = "monitoring"


class LogLevel(str, Enum):
    """日志级别枚举"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditAction(str, Enum):
    """审计操作枚举"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    UPLOAD = "upload"
    DOWNLOAD = "download"
    EXECUTE = "execute"
    CONFIG_CHANGE = "config_change"
    PERMISSION_CHANGE = "permission_change"


class MetricCategory(str, Enum):
    """指标类别枚举"""
    SYSTEM = "system"
    APPLICATION = "application"
    DATABASE = "database"
    NETWORK = "network"
    STORAGE = "storage"
    MEMORY = "memory"
    CPU = "cpu"


class MetricType(str, Enum):
    """指标类型枚举"""
    GAUGE = "gauge"
    COUNTER = "counter"
    HISTOGRAM = "histogram"


class AlertType(str, Enum):
    """告警类型枚举"""
    SYSTEM = "system"
    SECURITY = "security"
    PERFORMANCE = "performance"
    BUSINESS = "business"
    OPERATIONAL = "operational"


class AlertSeverity(str, Enum):
    """告警严重性枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """告警状态枚举"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class BackupType(str, Enum):
    """备份类型枚举"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"


class BackupCategory(str, Enum):
    """备份类别枚举"""
    DATABASE = "database"
    FILES = "files"
    CONFIG = "config"


# 系统配置schemas
class SystemConfigBase(BaseSchema):
    """系统配置基础schema"""
    config_key: constr(min_length=1, max_length=100) = Field(..., description="配置键")
    config_value: Dict[str, Any] = Field(..., description="配置值")
    config_type: ConfigType = Field(ConfigType.STRING, description="配置类型")
    category: ConfigCategory = Field(ConfigCategory.GENERAL, description="配置类别")
    name: constr(min_length=1, max_length=255) = Field(..., description="配置名称")
    description: Optional[str] = Field(None, description="配置描述")
    is_sensitive: bool = Field(False, description="是否敏感信息")
    is_system: bool = Field(False, description="是否系统配置")
    is_overridable: bool = Field(True, description="是否可覆盖")
    is_required: bool = Field(False, description="是否必需")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="验证规则")
    default_value: Optional[Dict[str, Any]] = Field(None, description="默认值")
    allowed_values: Optional[List[Any]] = Field(None, description="允许的值")
    is_active: bool = Field(True, description="是否激活")
    environment: str = Field("all", description="环境")
    version: int = Field(1, ge=1, description="版本号")


class SystemConfigCreate(SystemConfigBase):
    """系统配置创建schema"""
    pass


class SystemConfigUpdate(BaseSchema):
    """系统配置更新schema"""
    config_value: Optional[Dict[str, Any]] = Field(None, description="配置值")
    config_type: Optional[ConfigType] = Field(None, description="配置类型")
    category: Optional[ConfigCategory] = Field(None, description="配置类别")
    name: Optional[constr(max_length=255)] = Field(None, description="配置名称")
    description: Optional[str] = Field(None, description="配置描述")
    is_sensitive: Optional[bool] = Field(None, description="是否敏感信息")
    is_system: Optional[bool] = Field(None, description="是否系统配置")
    is_overridable: Optional[bool] = Field(None, description="是否可覆盖")
    is_required: Optional[bool] = Field(None, description="是否必需")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="验证规则")
    default_value: Optional[Dict[str, Any]] = Field(None, description="默认值")
    allowed_values: Optional[List[Any]] = Field(None, description="允许的值")
    is_active: Optional[bool] = Field(None, description="是否激活")
    environment: Optional[str] = Field(None, description="环境")


class SystemConfigResponse(SystemConfigBase):
    """系统配置响应schema"""
    id: UUID = Field(..., description="配置ID")
    last_modified_by: Optional[UUID] = Field(None, description="最后修改者")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    modified_by: Optional['UserResponse'] = Field(None, description="修改者信息")


# 系统日志schemas
class SystemLogBase(BaseSchema):
    """系统日志基础schema"""
    log_level: LogLevel = Field(LogLevel.INFO, description="日志级别")
    message: str = Field(..., description="日志消息")
    details: Optional[Dict[str, Any]] = Field(None, description="日志详情")
    stack_trace: Optional[str] = Field(None, description="堆栈跟踪")
    source: constr(min_length=1, max_length=100) = Field(..., description="日志来源")
    component: Optional[constr(max_length=100)] = Field(None, description="组件名称")
    function_name: Optional[constr(max_length=100)] = Field(None, description="函数名称")
    line_number: Optional[int] = Field(None, ge=0, description="行号")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文")
    session_id: Optional[str] = Field(None, description="会话ID")
    request_id: Optional[str] = Field(None, description="请求ID")
    execution_time: Optional[int] = Field(None, ge=0, description="执行时间(毫秒)")
    memory_usage: Optional[int] = Field(None, ge=0, description="内存使用(字节)")
    cpu_usage: Optional[int] = Field(None, ge=0, le=100, description="CPU使用率(%)")
    tags: Optional[List[str]] = Field(None, description="标签")


class SystemLogCreate(SystemLogBase):
    """系统日志创建schema"""
    user_id: Optional[UUID] = Field(None, description="用户ID")


class SystemLogUpdate(BaseSchema):
    """系统日志更新schema"""
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
    cpu_usage: Optional[int] = Field(None, ge=0, le=100, description="CPU使用率(%)")
    tags: Optional[List[str]] = Field(None, description="标签")


class SystemLogResponse(SystemLogBase):
    """系统日志响应schema"""
    id: UUID = Field(..., description="日志ID")
    user_id: Optional[UUID] = Field(None, description="用户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    user: Optional['UserResponse'] = Field(None, description="用户信息")


# 审计日志schemas
class AuditLogBase(BaseSchema):
    """审计日志基础schema"""
    action: AuditAction = Field(..., description="操作类型")
    resource_type: constr(min_length=1, max_length=100) = Field(..., description="资源类型")
    resource_id: Optional[UUID] = Field(None, description="资源ID")
    resource_name: Optional[constr(max_length=255)] = Field(None, description="资源名称")
    user_id: UUID = Field(..., description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    old_values: Optional[Dict[str, Any]] = Field(None, description="操作前的值")
    new_values: Optional[Dict[str, Any]] = Field(None, description="操作后的值")
    changes: Optional[Dict[str, Any]] = Field(None, description="变更详情")
    status: str = Field("success", description="操作状态")
    error_message: Optional[str] = Field(None, description="错误消息")
    error_code: Optional[str] = Field(None, description="错误代码")
    duration: Optional[int] = Field(None, ge=0, description="操作持续时间(毫秒)")
    tags: Optional[List[str]] = Field(None, description="标签")
    severity: str = Field("info", description="严重性")


class AuditLogCreate(AuditLogBase):
    """审计日志创建schema"""
    pass


class AuditLogUpdate(BaseSchema):
    """审计日志更新schema"""
    action: Optional[AuditAction] = Field(None, description="操作类型")
    resource_type: Optional[constr(max_length=100)] = Field(None, description="资源类型")
    resource_id: Optional[UUID] = Field(None, description="资源ID")
    resource_name: Optional[constr(max_length=255)] = Field(None, description="资源名称")
    user_id: Optional[UUID] = Field(None, description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    old_values: Optional[Dict[str, Any]] = Field(None, description="操作前的值")
    new_values: Optional[Dict[str, Any]] = Field(None, description="操作后的值")
    changes: Optional[Dict[str, Any]] = Field(None, description="变更详情")
    status: Optional[str] = Field(None, description="操作状态")
    error_message: Optional[str] = Field(None, description="错误消息")
    error_code: Optional[str] = Field(None, description="错误代码")
    duration: Optional[int] = Field(None, ge=0, description="操作持续时间(毫秒)")
    tags: Optional[List[str]] = Field(None, description="标签")
    severity: Optional[str] = Field(None, description="严重性")


class AuditLogResponse(AuditLogBase):
    """审计日志响应schema"""
    id: UUID = Field(..., description="日志ID")
    action_time: datetime = Field(..., description="操作时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    user: Optional['UserResponse'] = Field(None, description="用户信息")


# 系统指标schemas
class SystemMetricBase(BaseSchema):
    """系统指标基础schema"""
    metric_name: constr(min_length=1, max_length=100) = Field(..., description="指标名称")
    metric_value: int = Field(..., description="指标值")
    metric_type: MetricType = Field(MetricType.GAUGE, description="指标类型")
    category: MetricCategory = Field(MetricCategory.SYSTEM, description="指标类别")
    subcategory: Optional[str] = Field(None, description="子类别")
    unit: Optional[str] = Field(None, description="单位")
    description: Optional[str] = Field(None, description="指标描述")
    dimensions: Optional[Dict[str, str]] = Field(None, description="指标维度")
    warning_threshold: Optional[int] = Field(None, description="警告阈值")
    critical_threshold: Optional[int] = Field(None, description="严重阈值")
    status: str = Field("normal", description="指标状态")


class SystemMetricCreate(SystemMetricBase):
    """系统指标创建schema"""
    pass


class SystemMetricUpdate(BaseSchema):
    """系统指标更新schema"""
    metric_value: Optional[int] = Field(None, description="指标值")
    metric_type: Optional[MetricType] = Field(None, description="指标类型")
    category: Optional[MetricCategory] = Field(None, description="指标类别")
    subcategory: Optional[str] = Field(None, description="子类别")
    unit: Optional[str] = Field(None, description="单位")
    description: Optional[str] = Field(None, description="指标描述")
    dimensions: Optional[Dict[str, str]] = Field(None, description="指标维度")
    warning_threshold: Optional[int] = Field(None, description="警告阈值")
    critical_threshold: Optional[int] = Field(None, description="严重阈值")
    status: Optional[str] = Field(None, description="指标状态")


class SystemMetricResponse(SystemMetricBase):
    """系统指标响应schema"""
    id: UUID = Field(..., description="指标ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


# 系统告警schemas
class SystemAlertBase(BaseSchema):
    """系统告警基础schema"""
    alert_name: constr(min_length=1, max_length=255) = Field(..., description="告警名称")
    alert_type: AlertType = Field(..., description="告警类型")
    severity: AlertSeverity = Field(AlertSeverity.WARNING, description="告警严重性")
    message: str = Field(..., description="告警消息")
    description: Optional[str] = Field(None, description="告警描述")
    details: Optional[Dict[str, Any]] = Field(None, description="告警详情")
    metrics: Optional[Dict[str, Any]] = Field(None, description="指标数据")
    status: AlertStatus = Field(AlertStatus.ACTIVE, description="告警状态")
    rule_name: Optional[str] = Field(None, description="规则名称")
    rule_id: Optional[str] = Field(None, description="规则ID")
    notification_sent: bool = Field(False, description="是否已发送通知")
    notification_channels: Optional[List[str]] = Field(None, description="通知渠道")
    occurrence_count: int = Field(1, ge=1, description="发生次数")
    first_occurrence: datetime = Field(default_factory=datetime.now, description="首次发生时间")
    last_occurrence: datetime = Field(default_factory=datetime.now, description="最后发生时间")


class SystemAlertCreate(SystemAlertBase):
    """系统告警创建schema"""
    pass


class SystemAlertUpdate(BaseSchema):
    """系统告警更新schema"""
    alert_name: Optional[constr(max_length=255)] = Field(None, description="告警名称")
    alert_type: Optional[AlertType] = Field(None, description="告警类型")
    severity: Optional[AlertSeverity] = Field(None, description="告警严重性")
    message: Optional[str] = Field(None, description="告警消息")
    description: Optional[str] = Field(None, description="告警描述")
    details: Optional[Dict[str, Any]] = Field(None, description="告警详情")
    metrics: Optional[Dict[str, Any]] = Field(None, description="指标数据")
    status: Optional[AlertStatus] = Field(None, description="告警状态")
    rule_name: Optional[str] = Field(None, description="规则名称")
    rule_id: Optional[str] = Field(None, description="规则ID")
    notification_sent: Optional[bool] = Field(None, description="是否已发送通知")
    notification_channels: Optional[List[str]] = Field(None, description="通知渠道")
    occurrence_count: Optional[int] = Field(None, ge=1, description="发生次数")


class SystemAlertResponse(SystemAlertBase):
    """系统告警响应schema"""
    id: UUID = Field(..., description="告警ID")
    acknowledged_at: Optional[datetime] = Field(None, description="确认时间")
    acknowledged_by: Optional[UUID] = Field(None, description="确认者")
    resolved_at: Optional[datetime] = Field(None, description="解决时间")
    resolved_by: Optional[UUID] = Field(None, description="解决者")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    acknowledged_by_user: Optional['UserResponse'] = Field(None, description="确认者信息")
    resolved_by_user: Optional['UserResponse'] = Field(None, description="解决者信息")


# 系统备份schemas
class SystemBackupBase(BaseSchema):
    """系统备份基础schema"""
    backup_name: constr(min_length=1, max_length=255) = Field(..., description="备份名称")
    backup_type: BackupType = Field(..., description="备份类型")
    backup_category: BackupCategory = Field(BackupCategory.DATABASE, description="备份类别")
    file_path: str = Field(..., description="文件路径")
    file_size: int = Field(..., ge=0, description="文件大小(字节)")
    file_hash: Optional[str] = Field(None, description="文件哈希")
    status: str = Field("pending", description="备份状态")
    progress: int = Field(0, ge=0, le=100, description="进度(0-100)")
    config: Optional[Dict[str, Any]] = Field(None, description="备份配置")
    included_tables: Optional[List[str]] = Field(None, description="包含的表")
    excluded_tables: Optional[List[str]] = Field(None, description="排除的表")
    records_count: Optional[int] = Field(None, ge=0, description="记录数")
    compressed_size: Optional[int] = Field(None, ge=0, description="压缩后大小")
    compression_ratio: Optional[int] = Field(None, ge=0, le=100, description="压缩率")
    is_verified: bool = Field(False, description="是否已验证")
    verification_result: Optional[Dict[str, Any]] = Field(None, description="验证结果")
    retention_days: int = Field(30, ge=1, description="保留天数")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    is_expired: bool = Field(False, description="是否过期")
    description: Optional[str] = Field(None, description="备份描述")
    tags: Optional[List[str]] = Field(None, description="标签")


class SystemBackupCreate(SystemBackupBase):
    """系统备份创建schema"""
    created_by: Optional[UUID] = Field(None, description="创建者")


class SystemBackupUpdate(BaseSchema):
    """系统备份更新schema"""
    backup_name: Optional[constr(max_length=255)] = Field(None, description="备份名称")
    backup_type: Optional[BackupType] = Field(None, description="备份类型")
    backup_category: Optional[BackupCategory] = Field(None, description="备份类别")
    file_path: Optional[str] = Field(None, description="文件路径")
    file_size: Optional[int] = Field(None, ge=0, description="文件大小(字节)")
    file_hash: Optional[str] = Field(None, description="文件哈希")
    status: Optional[str] = Field(None, description="备份状态")
    progress: Optional[int] = Field(None, ge=0, le=100, description="进度(0-100)")
    config: Optional[Dict[str, Any]] = Field(None, description="备份配置")
    included_tables: Optional[List[str]] = Field(None, description="包含的表")
    excluded_tables: Optional[List[str]] = Field(None, description="排除的表")
    records_count: Optional[int] = Field(None, ge=0, description="记录数")
    compressed_size: Optional[int] = Field(None, ge=0, description="压缩后大小")
    compression_ratio: Optional[int] = Field(None, ge=0, le=100, description="压缩率")
    is_verified: Optional[bool] = Field(None, description="是否已验证")
    verification_result: Optional[Dict[str, Any]] = Field(None, description="验证结果")
    retention_days: Optional[int] = Field(None, ge=1, description="保留天数")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    is_expired: Optional[bool] = Field(None, description="是否过期")
    description: Optional[str] = Field(None, description="备份描述")
    tags: Optional[List[str]] = Field(None, description="标签")


class SystemBackupResponse(SystemBackupBase):
    """系统备份响应schema"""
    id: UUID = Field(..., description="备份ID")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    verified_at: Optional[datetime] = Field(None, description="验证时间")
    created_by: Optional[UUID] = Field(None, description="创建者")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by_user: Optional['UserResponse'] = Field(None, description="创建者信息")


# 更新前向引用
from .user import UserResponse
SystemConfigResponse.model_rebuild()
SystemLogResponse.model_rebuild()
AuditLogResponse.model_rebuild()
SystemAlertResponse.model_rebuild()
SystemBackupResponse.model_rebuild()