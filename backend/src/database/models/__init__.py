"""
数据模型模块
"""

from .base import Base, TimestampMixin, SoftDeleteMixin, ActivatedMixin
from .user import (
    User, Role, Permission, UserSession,
    user_roles, user_permissions, role_permissions
)
from .project import (
    Project, ProjectConfig, ProjectMember, 
    ProjectInvite, ProjectActivity
)
from .document import (
    Document, DocumentContent, DocumentMetadata, 
    DocumentVersion, DocumentTag, DocumentComment
)
from .task import (
    Task, TaskResult, TaskLog, TaskSchedule, TaskDependency
)
from .system import (
    SystemConfig, SystemLog, AuditLog, SystemMetric, 
    SystemAlert, SystemBackup
)

__all__ = [
    # 基础模型
    "Base", "TimestampMixin", "SoftDeleteMixin", "ActivatedMixin",
    
    # 用户模型
    "User", "Role", "Permission", "UserSession",
    "user_roles", "user_permissions", "role_permissions",
    
    # 项目模型
    "Project", "ProjectConfig", "ProjectMember", 
    "ProjectInvite", "ProjectActivity",
    
    # 文档模型
    "Document", "DocumentContent", "DocumentMetadata", 
    "DocumentVersion", "DocumentTag", "DocumentComment",
    
    # 任务模型
    "Task", "TaskResult", "TaskLog", "TaskSchedule", "TaskDependency",
    
    # 系统模型
    "SystemConfig", "SystemLog", "AuditLog", "SystemMetric", 
    "SystemAlert", "SystemBackup"
]