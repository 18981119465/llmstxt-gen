"""
任务模型
"""

from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Integer, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base, TimestampMixin, ActivatedMixin


class Task(Base, TimestampMixin, ActivatedMixin):
    """任务模型"""
    __tablename__ = 'tasks'
    
    # 任务基本信息
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id'), nullable=True)
    task_type = Column(String(50), nullable=False, index=True)  # document_process, web_crawl, ai_analysis, etc.
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # 任务状态
    status = Column(String(20), default='pending', nullable=False)  # pending, running, completed, failed, cancelled
    progress = Column(Integer, default=0, nullable=False)  # 0-100
    priority = Column(String(20), default='normal', nullable=False)  # low, normal, high, urgent
    
    # 任务配置
    config = Column(JSONB, nullable=True)
    parameters = Column(JSONB, nullable=True)
    
    # 任务结果
    result = Column(JSONB, nullable=True)
    result_summary = Column(Text, nullable=True)
    output_files = Column(JSONB, nullable=True)  # 输出文件列表
    
    # 错误信息
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)
    error_stack_trace = Column(Text, nullable=True)
    
    # 任务时间
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    estimated_duration = Column(Integer, nullable=True)  # 预计持续时间（秒）
    actual_duration = Column(Integer, nullable=True)  # 实际持续时间（秒）
    
    # 任务属性
    is_recurring = Column(Boolean, default=False, nullable=False)
    recurring_config = Column(JSONB, nullable=True)  # 循环任务配置
    parent_task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id'), nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    
    # 任务统计
    processed_items = Column(Integer, default=0, nullable=False)
    total_items = Column(Integer, default=0, nullable=False)
    success_items = Column(Integer, default=0, nullable=False)
    failed_items = Column(Integer, default=0, nullable=False)
    
    # 任务创建者
    created_by_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    assigned_to_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    
    # 关联关系
    project = relationship("Project", back_populates="tasks")
    document = relationship("Document", back_populates="tasks")
    created_by = relationship("User", foreign_keys=[created_by_id], back_populates="created_tasks")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    parent_task = relationship("Task", remote_side=[id], back_populates="subtasks")
    subtasks = relationship("Task", back_populates="parent_task")
    results = relationship("TaskResult", back_populates="task")
    logs = relationship("TaskLog", back_populates="task")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        task_dict = {
            'project_id': str(self.project_id) if self.project_id else None,
            'document_id': str(self.document_id) if self.document_id else None,
            'task_type': self.task_type,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'progress': self.progress,
            'priority': self.priority,
            'config': self.config,
            'parameters': self.parameters,
            'result': self.result,
            'result_summary': self.result_summary,
            'output_files': self.output_files,
            'error_message': self.error_message,
            'error_code': self.error_code,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'estimated_duration': self.estimated_duration,
            'actual_duration': self.actual_duration,
            'is_recurring': self.is_recurring,
            'recurring_config': self.recurring_config,
            'parent_task_id': str(self.parent_task_id) if self.parent_task_id else None,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'processed_items': self.processed_items,
            'total_items': self.total_items,
            'success_items': self.success_items,
            'failed_items': self.failed_items,
            'created_by_id': str(self.created_by_id),
            'assigned_to_id': str(self.assigned_to_id) if self.assigned_to_id else None,
            'created_by': self.created_by.to_dict() if self.created_by else None,
            'assigned_to': self.assigned_to.to_dict() if self.assigned_to else None,
            'project': self.project.to_dict() if self.project else None,
            'document': self.document.to_dict() if self.document else None
        }
        return {**base_dict, **task_dict}
    
    def update_progress(self, progress: int, processed_items: int = None):
        """更新任务进度"""
        self.progress = max(0, min(100, progress))
        if processed_items is not None:
            self.processed_items = processed_items
        
        # 如果任务完成，更新状态
        if self.progress >= 100:
            self.status = 'completed'
            self.completed_at = func.now()
            if self.started_at:
                self.actual_duration = (self.completed_at - self.started_at).total_seconds()
    
    def start_task(self):
        """开始任务"""
        self.status = 'running'
        self.started_at = func.now()
        self.progress = 0
    
    def complete_task(self, result_data: dict = None):
        """完成任务"""
        self.status = 'completed'
        self.completed_at = func.now()
        self.progress = 100
        if result_data:
            self.result = result_data
        if self.started_at:
            self.actual_duration = (self.completed_at - self.started_at).total_seconds()
    
    def fail_task(self, error_message: str, error_code: str = None):
        """任务失败"""
        self.status = 'failed'
        self.completed_at = func.now()
        self.error_message = error_message
        if error_code:
            self.error_code = error_code
        if self.started_at:
            self.actual_duration = (self.completed_at - self.started_at).total_seconds()
    
    def cancel_task(self):
        """取消任务"""
        self.status = 'cancelled'
        self.completed_at = func.now()
        if self.started_at:
            self.actual_duration = (self.completed_at - self.started_at).total_seconds()
    
    def can_retry(self) -> bool:
        """检查是否可以重试"""
        return self.status == 'failed' and self.retry_count < self.max_retries
    
    def retry_task(self):
        """重试任务"""
        if self.can_retry():
            self.retry_count += 1
            self.status = 'pending'
            self.started_at = None
            self.completed_at = None
            self.progress = 0
            self.error_message = None
            self.error_code = None
            self.error_stack_trace = None
            self.result = None
            self.result_summary = None
            self.actual_duration = None


class TaskResult(Base, TimestampMixin):
    """任务结果模型"""
    __tablename__ = 'task_results'
    
    # 结果信息
    task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id'), nullable=False)
    result_type = Column(String(50), nullable=False)  # text, json, file, etc.
    result_data = Column(JSONB, nullable=True)
    result_text = Column(Text, nullable=True)
    result_file_path = Column(String(500), nullable=True)
    result_file_size = Column(Integer, nullable=True)
    
    # 结果统计
    processing_time = Column(Integer, nullable=True)  # 处理时间（毫秒）
    memory_usage = Column(Integer, nullable=True)  # 内存使用（字节）
    cpu_usage = Column(Integer, nullable=True)  # CPU使用（百分比）
    
    # 结果质量
    quality_score = Column(Integer, nullable=True)  # 0-100
    confidence_score = Column(Integer, nullable=True)  # 0-100
    accuracy_score = Column(Integer, nullable=True)  # 0-100
    
    # 结果元数据
    result_metadata = Column(JSONB, nullable=True)
    tags = Column(JSONB, nullable=True)
    
    # 结果状态
    is_valid = Column(Boolean, default=True, nullable=False)
    validation_errors = Column(JSONB, nullable=True)
    
    # 关联关系
    task = relationship("Task", back_populates="results")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        result_dict = {
            'task_id': str(self.task_id),
            'result_type': self.result_type,
            'result_data': self.result_data,
            'result_text': self.result_text,
            'result_file_path': self.result_file_path,
            'result_file_size': self.result_file_size,
            'processing_time': self.processing_time,
            'memory_usage': self.memory_usage,
            'cpu_usage': self.cpu_usage,
            'quality_score': self.quality_score,
            'confidence_score': self.confidence_score,
            'accuracy_score': self.accuracy_score,
            'metadata': self.result_metadata,
            'tags': self.tags,
            'is_valid': self.is_valid,
            'validation_errors': self.validation_errors
        }
        return {**base_dict, **result_dict}


class TaskLog(Base, TimestampMixin):
    """任务日志模型"""
    __tablename__ = 'task_logs'
    
    # 日志信息
    task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id'), nullable=False)
    log_level = Column(String(20), default='info', nullable=False)  # debug, info, warning, error, critical
    message = Column(Text, nullable=False)
    
    # 日志详情
    details = Column(JSONB, nullable=True)
    stack_trace = Column(Text, nullable=True)
    
    # 日志来源
    source = Column(String(100), nullable=True)  # 日志来源组件
    function_name = Column(String(100), nullable=True)
    line_number = Column(Integer, nullable=True)
    
    # 日志上下文
    context = Column(JSONB, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    session_id = Column(String(100), nullable=True)
    
    # 性能信息
    execution_time = Column(Integer, nullable=True)  # 执行时间（毫秒）
    memory_usage = Column(Integer, nullable=True)  # 内存使用（字节）
    
    # 关联关系
    task = relationship("Task", back_populates="logs")
    user = relationship("User")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        log_dict = {
            'task_id': str(self.task_id),
            'log_level': self.log_level,
            'message': self.message,
            'details': self.details,
            'stack_trace': self.stack_trace,
            'source': self.source,
            'function_name': self.function_name,
            'line_number': self.line_number,
            'context': self.context,
            'user_id': str(self.user_id) if self.user_id else None,
            'session_id': self.session_id,
            'execution_time': self.execution_time,
            'memory_usage': self.memory_usage,
            'user': self.user.to_dict() if self.user else None
        }
        return {**base_dict, **log_dict}


class TaskSchedule(Base, TimestampMixin):
    """任务调度模型"""
    __tablename__ = 'task_schedules'
    
    # 调度信息
    task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id'), nullable=False)
    schedule_name = Column(String(100), nullable=False)
    schedule_type = Column(String(50), nullable=False)  # cron, interval, once
    schedule_config = Column(JSONB, nullable=False)  # 调度配置
    
    # 调度状态
    is_active = Column(Boolean, default=True, nullable=False)
    next_run_time = Column(DateTime, nullable=False)
    last_run_time = Column(DateTime, nullable=True)
    run_count = Column(Integer, default=0, nullable=False)
    
    # 调度设置
    timezone = Column(String(50), default='UTC', nullable=False)
    max_runs = Column(Integer, nullable=True)  # 最大运行次数
    end_time = Column(DateTime, nullable=True)  # 结束时间
    
    # 调度属性
    created_by_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # 关联关系
    task = relationship("Task")
    created_by = relationship("User")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        schedule_dict = {
            'task_id': str(self.task_id),
            'schedule_name': self.schedule_name,
            'schedule_type': self.schedule_type,
            'schedule_config': self.schedule_config,
            'is_active': self.is_active,
            'next_run_time': self.next_run_time.isoformat() if self.next_run_time else None,
            'last_run_time': self.last_run_time.isoformat() if self.last_run_time else None,
            'run_count': self.run_count,
            'timezone': self.timezone,
            'max_runs': self.max_runs,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'created_by_id': str(self.created_by_id),
            'created_by': self.created_by.to_dict() if self.created_by else None
        }
        return {**base_dict, **schedule_dict}


class TaskDependency(Base, TimestampMixin):
    """任务依赖模型"""
    __tablename__ = 'task_dependencies'
    
    # 依赖信息
    task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id'), nullable=False)
    depends_on_task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id'), nullable=False)
    dependency_type = Column(String(50), default='completion', nullable=False)  # completion, success, output
    
    # 依赖状态
    is_satisfied = Column(Boolean, default=False, nullable=False)
    satisfied_at = Column(DateTime, nullable=True)
    
    # 依赖配置
    config = Column(JSONB, nullable=True)
    
    # 关联关系
    task = relationship("Task", foreign_keys=[task_id])
    depends_on_task = relationship("Task", foreign_keys=[depends_on_task_id])
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        dependency_dict = {
            'task_id': str(self.task_id),
            'depends_on_task_id': str(self.depends_on_task_id),
            'dependency_type': self.dependency_type,
            'is_satisfied': self.is_satisfied,
            'satisfied_at': self.satisfied_at.isoformat() if self.satisfied_at else None,
            'config': self.config,
            'task': self.task.to_dict() if self.task else None,
            'depends_on_task': self.depends_on_task.to_dict() if self.depends_on_task else None
        }
        return {**base_dict, **dependency_dict}