"""
系统模型
"""

from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Integer, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base, TimestampMixin


class SystemConfig(Base, TimestampMixin):
    """系统配置模型"""
    __tablename__ = 'system_configs'
    
    # 配置信息
    config_key = Column(String(100), unique=True, nullable=False, index=True)
    config_value = Column(JSONB, nullable=False)
    config_type = Column(String(50), default='string', nullable=False)  # string, number, boolean, json
    category = Column(String(50), default='general', nullable=False)  # general, security, performance, etc.
    
    # 配置描述
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # 配置属性
    is_sensitive = Column(Boolean, default=False, nullable=False)  # 是否敏感信息
    is_system = Column(Boolean, default=False, nullable=False)  # 是否系统配置
    is_overridable = Column(Boolean, default=True, nullable=False)  # 是否可覆盖
    is_required = Column(Boolean, default=False, nullable=False)  # 是否必需
    
    # 配置验证
    validation_rules = Column(JSONB, nullable=True)
    default_value = Column(JSONB, nullable=True)
    allowed_values = Column(JSONB, nullable=True)
    
    # 配置状态
    is_active = Column(Boolean, default=True, nullable=False)
    environment = Column(String(50), default='all', nullable=False)  # all, development, staging, production
    
    # 配置版本
    version = Column(Integer, default=1, nullable=False)
    last_modified_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    
    # 关联关系
    modified_by = relationship("User")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        config_dict = {
            'config_key': self.config_key,
            'config_value': self.config_value if not self.is_sensitive else '***',
            'config_type': self.config_type,
            'category': self.category,
            'name': self.name,
            'description': self.description,
            'is_sensitive': self.is_sensitive,
            'is_system': self.is_system,
            'is_overridable': self.is_overridable,
            'is_required': self.is_required,
            'validation_rules': self.validation_rules,
            'default_value': self.default_value,
            'allowed_values': self.allowed_values,
            'is_active': self.is_active,
            'environment': self.environment,
            'version': self.version,
            'last_modified_by': str(self.last_modified_by) if self.last_modified_by else None,
            'modified_by': self.modified_by.to_dict() if self.modified_by else None
        }
        return {**base_dict, **config_dict}


class SystemLog(Base, TimestampMixin):
    """系统日志模型"""
    __tablename__ = 'system_logs'
    
    # 日志信息
    log_level = Column(String(20), default='info', nullable=False)  # debug, info, warning, error, critical
    message = Column(Text, nullable=False)
    
    # 日志详情
    details = Column(JSONB, nullable=True)
    stack_trace = Column(Text, nullable=True)
    
    # 日志来源
    source = Column(String(100), nullable=False)  # 日志来源模块
    component = Column(String(100), nullable=True)  # 组件名称
    function_name = Column(String(100), nullable=True)
    line_number = Column(Integer, nullable=True)
    
    # 日志上下文
    context = Column(JSONB, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    session_id = Column(String(100), nullable=True)
    request_id = Column(String(100), nullable=True)
    
    # 性能信息
    execution_time = Column(Integer, nullable=True)  # 执行时间（毫秒）
    memory_usage = Column(Integer, nullable=True)  # 内存使用（字节）
    cpu_usage = Column(Integer, nullable=True)  # CPU使用（百分比）
    
    # 日志标签
    tags = Column(JSONB, nullable=True)
    
    # 关联关系
    user = relationship("User")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        log_dict = {
            'log_level': self.log_level,
            'message': self.message,
            'details': self.details,
            'stack_trace': self.stack_trace,
            'source': self.source,
            'component': self.component,
            'function_name': self.function_name,
            'line_number': self.line_number,
            'context': self.context,
            'user_id': str(self.user_id) if self.user_id else None,
            'session_id': self.session_id,
            'request_id': self.request_id,
            'execution_time': self.execution_time,
            'memory_usage': self.memory_usage,
            'cpu_usage': self.cpu_usage,
            'tags': self.tags,
            'user': self.user.to_dict() if self.user else None
        }
        return {**base_dict, **log_dict}


class AuditLog(Base, TimestampMixin):
    """审计日志模型"""
    __tablename__ = 'audit_logs'
    
    # 审计信息
    action = Column(String(100), nullable=False)  # 操作类型
    resource_type = Column(String(100), nullable=False)  # 资源类型
    resource_id = Column(UUID(as_uuid=True), nullable=True)  # 资源ID
    resource_name = Column(String(255), nullable=True)  # 资源名称
    
    # 操作信息
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    session_id = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # 操作详情
    old_values = Column(JSONB, nullable=True)  # 操作前的值
    new_values = Column(JSONB, nullable=True)  # 操作后的值
    changes = Column(JSONB, nullable=True)  # 变更详情
    
    # 操作结果
    status = Column(String(20), default='success', nullable=False)  # success, failure, error
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)
    
    # 操作时间
    action_time = Column(DateTime, default=func.now(), nullable=False)
    duration = Column(Integer, nullable=True)  # 操作持续时间（毫秒）
    
    # 审计标签
    tags = Column(JSONB, nullable=True)
    severity = Column(String(20), default='info', nullable=False)  # low, medium, high, critical
    
    # 关联关系
    user = relationship("User")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        audit_dict = {
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': str(self.resource_id) if self.resource_id else None,
            'resource_name': self.resource_name,
            'user_id': str(self.user_id),
            'session_id': self.session_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'changes': self.changes,
            'status': self.status,
            'error_message': self.error_message,
            'error_code': self.error_code,
            'action_time': self.action_time.isoformat() if self.action_time else None,
            'duration': self.duration,
            'tags': self.tags,
            'severity': self.severity,
            'user': self.user.to_dict() if self.user else None
        }
        return {**base_dict, **audit_dict}


class SystemMetric(Base, TimestampMixin):
    """系统指标模型"""
    __tablename__ = 'system_metrics'
    
    # 指标信息
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Integer, nullable=False)
    metric_type = Column(String(50), default='gauge', nullable=False)  # gauge, counter, histogram
    
    # 指标分类
    category = Column(String(50), default='system', nullable=False)  # system, application, database, etc.
    subcategory = Column(String(50), nullable=True)
    
    # 指标详情
    unit = Column(String(20), nullable=True)  # 单位
    description = Column(Text, nullable=True)
    
    # 指标维度
    dimensions = Column(JSONB, nullable=True)  # 指标维度标签
    
    # 指标阈值
    warning_threshold = Column(Integer, nullable=True)
    critical_threshold = Column(Integer, nullable=True)
    
    # 指标状态
    status = Column(String(20), default='normal', nullable=False)  # normal, warning, critical
    
    # 关联关系
    # 无直接关联关系
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        metric_dict = {
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'metric_type': self.metric_type,
            'category': self.category,
            'subcategory': self.subcategory,
            'unit': self.unit,
            'description': self.description,
            'dimensions': self.dimensions,
            'warning_threshold': self.warning_threshold,
            'critical_threshold': self.critical_threshold,
            'status': self.status
        }
        return {**base_dict, **metric_dict}


class SystemAlert(Base, TimestampMixin):
    """系统告警模型"""
    __tablename__ = 'system_alerts'
    
    # 告警信息
    alert_name = Column(String(255), nullable=False)
    alert_type = Column(String(50), nullable=False)  # system, security, performance, etc.
    severity = Column(String(20), default='warning', nullable=False)  # info, warning, error, critical
    
    # 告警内容
    message = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    
    # 告警详情
    details = Column(JSONB, nullable=True)
    metrics = Column(JSONB, nullable=True)
    
    # 告警状态
    status = Column(String(20), default='active', nullable=False)  # active, acknowledged, resolved, suppressed
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    
    # 告警规则
    rule_name = Column(String(100), nullable=True)
    rule_id = Column(String(100), nullable=True)
    
    # 告警通知
    notification_sent = Column(Boolean, default=False, nullable=False)
    notification_channels = Column(JSONB, nullable=True)
    
    # 告警统计
    occurrence_count = Column(Integer, default=1, nullable=False)
    first_occurrence = Column(DateTime, default=func.now(), nullable=False)
    last_occurrence = Column(DateTime, default=func.now(), nullable=False)
    
    # 关联关系
    acknowledged_by_user = relationship("User", foreign_keys=[acknowledged_by])
    resolved_by_user = relationship("User", foreign_keys=[resolved_by])
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        alert_dict = {
            'alert_name': self.alert_name,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'message': self.message,
            'description': self.description,
            'details': self.details,
            'metrics': self.metrics,
            'status': self.status,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'acknowledged_by': str(self.acknowledged_by) if self.acknowledged_by else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': str(self.resolved_by) if self.resolved_by else None,
            'rule_name': self.rule_name,
            'rule_id': self.rule_id,
            'notification_sent': self.notification_sent,
            'notification_channels': self.notification_channels,
            'occurrence_count': self.occurrence_count,
            'first_occurrence': self.first_occurrence.isoformat() if self.first_occurrence else None,
            'last_occurrence': self.last_occurrence.isoformat() if self.last_occurrence else None,
            'acknowledged_by_user': self.acknowledged_by_user.to_dict() if self.acknowledged_by_user else None,
            'resolved_by_user': self.resolved_by_user.to_dict() if self.resolved_by_user else None
        }
        return {**base_dict, **alert_dict}


class SystemBackup(Base, TimestampMixin):
    """系统备份模型"""
    __tablename__ = 'system_backups'
    
    # 备份信息
    backup_name = Column(String(255), nullable=False)
    backup_type = Column(String(50), nullable=False)  # full, incremental, differential
    backup_category = Column(String(50), default='database', nullable=False)  # database, files, config
    
    # 备份文件
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # bytes
    file_hash = Column(String(64), nullable=True)
    
    # 备份状态
    status = Column(String(20), default='pending', nullable=False)  # pending, in_progress, completed, failed
    progress = Column(Integer, default=0, nullable=False)  # 0-100
    
    # 备份时间
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # 备份配置
    config = Column(JSONB, nullable=True)
    included_tables = Column(JSONB, nullable=True)
    excluded_tables = Column(JSONB, nullable=True)
    
    # 备份统计
    records_count = Column(Integer, nullable=True)
    compressed_size = Column(Integer, nullable=True)  # bytes
    compression_ratio = Column(Integer, nullable=True)  # percentage
    
    # 备份验证
    is_verified = Column(Boolean, default=False, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    verification_result = Column(JSONB, nullable=True)
    
    # 备份保留
    retention_days = Column(Integer, default=30, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    is_expired = Column(Boolean, default=False, nullable=False)
    
    # 备份元数据
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(JSONB, nullable=True)
    
    # 关联关系
    created_by_user = relationship("User")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        backup_dict = {
            'backup_name': self.backup_name,
            'backup_type': self.backup_type,
            'backup_category': self.backup_category,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_hash': self.file_hash,
            'status': self.status,
            'progress': self.progress,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'config': self.config,
            'included_tables': self.included_tables,
            'excluded_tables': self.excluded_tables,
            'records_count': self.records_count,
            'compressed_size': self.compressed_size,
            'compression_ratio': self.compression_ratio,
            'is_verified': self.is_verified,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'verification_result': self.verification_result,
            'retention_days': self.retention_days,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_expired': self.is_expired,
            'created_by': str(self.created_by) if self.created_by else None,
            'description': self.description,
            'tags': self.tags,
            'created_by_user': self.created_by_user.to_dict() if self.created_by_user else None
        }
        return {**base_dict, **backup_dict}