"""
Pydantic schemas module
"""

from .base import BaseSchema, BaseResponse
from .user import (
    UserCreate, UserUpdate, UserResponse, UserProfile,
    RoleCreate, RoleUpdate, RoleResponse,
    PermissionCreate, PermissionUpdate, PermissionResponse,
    UserSessionCreate, UserSessionResponse
)
from .project import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    ProjectConfigCreate, ProjectConfigUpdate, ProjectConfigResponse
)
from .document import (
    DocumentCreate, DocumentUpdate, DocumentResponse,
    DocumentContentCreate, DocumentContentUpdate, DocumentContentResponse,
    DocumentMetadataCreate, DocumentMetadataUpdate, DocumentMetadataResponse
)
from .task import (
    TaskCreate, TaskUpdate, TaskResponse,
    TaskResultCreate, TaskResultUpdate, TaskResultResponse,
    TaskLogCreate, TaskLogUpdate, TaskLogResponse
)
from .system import (
    SystemConfigCreate, SystemConfigUpdate, SystemConfigResponse,
    SystemLogCreate, SystemLogResponse,
    AuditLogCreate, AuditLogResponse
)

__all__ = [
    # 基础schemas
    "BaseSchema", "BaseResponse",
    
    # 用户schemas
    "UserCreate", "UserUpdate", "UserResponse", "UserProfile",
    "RoleCreate", "RoleUpdate", "RoleResponse",
    "PermissionCreate", "PermissionUpdate", "PermissionResponse",
    "UserSessionCreate", "UserSessionResponse",
    
    # 项目schemas
    "ProjectCreate", "ProjectUpdate", "ProjectResponse",
    "ProjectConfigCreate", "ProjectConfigUpdate", "ProjectConfigResponse",
    
    # 文档schemas
    "DocumentCreate", "DocumentUpdate", "DocumentResponse",
    "DocumentContentCreate", "DocumentContentUpdate", "DocumentContentResponse",
    "DocumentMetadataCreate", "DocumentMetadataUpdate", "DocumentMetadataResponse",
    
    # 任务schemas
    "TaskCreate", "TaskUpdate", "TaskResponse",
    "TaskResultCreate", "TaskResultUpdate", "TaskResultResponse",
    "TaskLogCreate", "TaskLogUpdate", "TaskLogResponse",
    
    # 系统schemas
    "SystemConfigCreate", "SystemConfigUpdate", "SystemConfigResponse",
    "SystemLogCreate", "SystemLogResponse",
    "AuditLogCreate", "AuditLogResponse"
]