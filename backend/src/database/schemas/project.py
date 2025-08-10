"""
项目相关schemas
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, field_validator, constr

from .base import BaseSchema, BaseResponse


class ProjectStatus(str, Enum):
    """项目状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ProjectVisibility(str, Enum):
    """项目可见性枚举"""
    PRIVATE = "private"
    PUBLIC = "public"
    TEAM = "team"


class ProjectMemberRole(str, Enum):
    """项目成员角色枚举"""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class ProjectMemberStatus(str, Enum):
    """项目成员状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    REMOVED = "removed"


class ProjectInviteStatus(str, Enum):
    """项目邀请状态枚举"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ProjectActivityAction(str, Enum):
    """项目活动操作枚举"""
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    JOINED = "joined"
    LEFT = "left"
    INVITED = "invited"
    ACCEPTED_INVITE = "accepted_invite"
    REJECTED_INVITE = "rejected_invite"
    ARCHIVED = "archived"
    RESTORED = "restored"


# 项目schemas
class ProjectBase(BaseSchema):
    """项目基础schema"""
    name: constr(min_length=1, max_length=255) = Field(..., description="项目名称")
    description: Optional[constr(max_length=1000)] = Field(None, description="项目描述")
    visibility: ProjectVisibility = Field(ProjectVisibility.PRIVATE, description="项目可见性")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        return v.strip()


class ProjectCreate(ProjectBase):
    """项目创建schema"""
    slug: Optional[constr(min_length=1, max_length=255)] = Field(None, description="项目slug")
    config: Optional[Dict[str, Any]] = Field(None, description="项目配置")
    settings: Optional[Dict[str, Any]] = Field(None, description="项目设置")
    max_documents: int = Field(1000, ge=1, le=10000, description="最大文档数")
    max_storage: int = Field(1024*1024*1024, ge=1, description="最大存储空间(字节)")
    allowed_file_types: Optional[List[str]] = Field(None, description="允许的文件类型")
    
    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v):
        if v:
            return v.lower().replace(' ', '-').replace('_', '-')
        return v


class ProjectUpdate(BaseSchema):
    """项目更新schema"""
    name: Optional[constr(max_length=255)] = Field(None, description="项目名称")
    description: Optional[constr(max_length=1000)] = Field(None, description="项目描述")
    visibility: Optional[ProjectVisibility] = Field(None, description="项目可见性")
    config: Optional[Dict[str, Any]] = Field(None, description="项目配置")
    settings: Optional[Dict[str, Any]] = Field(None, description="项目设置")
    max_documents: Optional[int] = Field(None, ge=1, le=10000, description="最大文档数")
    max_storage: Optional[int] = Field(None, ge=1, description="最大存储空间(字节)")
    allowed_file_types: Optional[List[str]] = Field(None, description="允许的文件类型")
    is_archived: Optional[bool] = Field(None, description="是否归档")


class ProjectResponse(ProjectBase):
    """项目响应schema"""
    id: UUID = Field(..., description="项目ID")
    slug: str = Field(..., description="项目slug")
    owner_id: UUID = Field(..., description="所有者ID")
    status: ProjectStatus = Field(..., description="项目状态")
    is_archived: bool = Field(..., description="是否归档")
    document_count: int = Field(..., description="文档数量")
    task_count: int = Field(..., description="任务数量")
    storage_used: int = Field(..., description="已用存储空间")
    max_documents: int = Field(..., description="最大文档数")
    max_storage: int = Field(..., description="最大存储空间")
    allowed_file_types: Optional[List[str]] = Field(None, description="允许的文件类型")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    owner: Optional['UserResponse'] = Field(None, description="项目所有者")


class ProjectStats(BaseSchema):
    """项目统计schema"""
    project_id: UUID = Field(..., description="项目ID")
    document_count: int = Field(..., description="文档数量")
    task_count: int = Field(..., description="任务数量")
    storage_used: int = Field(..., description="已用存储空间")
    member_count: int = Field(..., description="成员数量")
    active_tasks: int = Field(..., description="活跃任务数量")
    completed_tasks: int = Field(..., description="已完成任务数量")
    failed_tasks: int = Field(..., description="失败任务数量")


# 项目配置schemas
class ProjectConfigBase(BaseSchema):
    """项目配置基础schema"""
    config_type: constr(min_length=1, max_length=50) = Field(..., description="配置类型")
    name: constr(min_length=1, max_length=100) = Field(..., description="配置名称")
    value: Dict[str, Any] = Field(..., description="配置值")
    description: Optional[constr(max_length=500)] = Field(None, description="配置描述")


class ProjectConfigCreate(ProjectConfigBase):
    """项目配置创建schema"""
    project_id: UUID = Field(..., description="项目ID")
    is_system: bool = Field(False, description="是否系统配置")


class ProjectConfigUpdate(BaseSchema):
    """项目配置更新schema"""
    name: Optional[constr(max_length=100)] = Field(None, description="配置名称")
    value: Optional[Dict[str, Any]] = Field(None, description="配置值")
    description: Optional[constr(max_length=500)] = Field(None, description="配置描述")
    is_active: Optional[bool] = Field(None, description="是否激活")


class ProjectConfigResponse(ProjectConfigBase):
    """项目配置响应schema"""
    id: UUID = Field(..., description="配置ID")
    project_id: UUID = Field(..., description="项目ID")
    is_active: bool = Field(..., description="是否激活")
    is_system: bool = Field(..., description="是否系统配置")
    version: int = Field(..., description="版本号")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


# 项目成员schemas
class ProjectMemberBase(BaseSchema):
    """项目成员基础schema"""
    role: ProjectMemberRole = Field(..., description="成员角色")
    permissions: Optional[Dict[str, Any]] = Field(None, description="成员权限")


class ProjectMemberCreate(ProjectMemberBase):
    """项目成员创建schema"""
    project_id: UUID = Field(..., description="项目ID")
    user_id: UUID = Field(..., description="用户ID")
    can_invite: bool = Field(False, description="是否可以邀请")
    can_edit: bool = Field(False, description="是否可以编辑")
    can_delete: bool = Field(False, description="是否可以删除")
    can_manage_members: bool = Field(False, description="是否可以管理成员")


class ProjectMemberUpdate(BaseSchema):
    """项目成员更新schema"""
    role: Optional[ProjectMemberRole] = Field(None, description="成员角色")
    permissions: Optional[Dict[str, Any]] = Field(None, description="成员权限")
    status: Optional[ProjectMemberStatus] = Field(None, description="成员状态")
    can_invite: Optional[bool] = Field(None, description="是否可以邀请")
    can_edit: Optional[bool] = Field(None, description="是否可以编辑")
    can_delete: Optional[bool] = Field(None, description="是否可以删除")
    can_manage_members: Optional[bool] = Field(None, description="是否可以管理成员")


class ProjectMemberResponse(ProjectMemberBase):
    """项目成员响应schema"""
    id: UUID = Field(..., description="成员ID")
    project_id: UUID = Field(..., description="项目ID")
    user_id: UUID = Field(..., description="用户ID")
    status: ProjectMemberStatus = Field(..., description="成员状态")
    joined_at: datetime = Field(..., description="加入时间")
    left_at: Optional[datetime] = Field(None, description="离开时间")
    can_invite: bool = Field(..., description="是否可以邀请")
    can_edit: bool = Field(..., description="是否可以编辑")
    can_delete: bool = Field(..., description="是否可以删除")
    can_manage_members: bool = Field(..., description="是否可以管理成员")
    user: Optional['UserResponse'] = Field(None, description="用户信息")


# 项目邀请schemas
class ProjectInviteBase(BaseSchema):
    """项目邀请基础schema"""
    invitee_email: str = Field(..., description="被邀请者邮箱")
    role: ProjectMemberRole = Field(ProjectMemberRole.MEMBER, description="邀请角色")
    permissions: Optional[Dict[str, Any]] = Field(None, description="邀请权限")
    message: Optional[constr(max_length=500)] = Field(None, description="邀请消息")


class ProjectInviteCreate(ProjectInviteBase):
    """项目邀请创建schema"""
    project_id: UUID = Field(..., description="项目ID")
    expires_in_hours: int = Field(24, ge=1, le=168, description="过期时间(小时)")


class ProjectInviteResponse(ProjectInviteBase):
    """项目邀请响应schema"""
    id: UUID = Field(..., description="邀请ID")
    project_id: UUID = Field(..., description="项目ID")
    inviter_id: UUID = Field(..., description="邀请者ID")
    invitee_id: Optional[UUID] = Field(None, description="被邀请者ID")
    status: ProjectInviteStatus = Field(..., description="邀请状态")
    token: str = Field(..., description="邀请令牌")
    expires_at: datetime = Field(..., description="过期时间")
    accepted_at: Optional[datetime] = Field(None, description="接受时间")
    rejected_at: Optional[datetime] = Field(None, description="拒绝时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    inviter: Optional['UserResponse'] = Field(None, description="邀请者")
    invitee: Optional['UserResponse'] = Field(None, description="被邀请者")


# 项目活动schemas
class ProjectActivityBase(BaseSchema):
    """项目活动基础schema"""
    action: ProjectActivityAction = Field(..., description="活动操作")
    resource_type: str = Field(..., description="资源类型")
    resource_id: Optional[UUID] = Field(None, description="资源ID")
    resource_name: Optional[str] = Field(None, description="资源名称")
    details: Optional[Dict[str, Any]] = Field(None, description="活动详情")
    changes: Optional[Dict[str, Any]] = Field(None, description="变更内容")


class ProjectActivityCreate(ProjectActivityBase):
    """项目活动创建schema"""
    project_id: UUID = Field(..., description="项目ID")
    user_id: UUID = Field(..., description="用户ID")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")


class ProjectActivityResponse(ProjectActivityBase):
    """项目活动响应schema"""
    id: UUID = Field(..., description="活动ID")
    project_id: UUID = Field(..., description="项目ID")
    user_id: UUID = Field(..., description="用户ID")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    created_at: datetime = Field(..., description="创建时间")
    user: Optional['UserResponse'] = Field(None, description="用户信息")


# 项目搜索schemas
class ProjectSearchParams(BaseSchema):
    """项目搜索参数schema"""
    search: Optional[str] = Field(None, description="搜索关键词")
    status: Optional[ProjectStatus] = Field(None, description="项目状态")
    visibility: Optional[ProjectVisibility] = Field(None, description="项目可见性")
    owner_id: Optional[UUID] = Field(None, description="所有者ID")
    is_archived: Optional[bool] = Field(None, description="是否归档")
    created_after: Optional[datetime] = Field(None, description="创建时间之后")
    created_before: Optional[datetime] = Field(None, description="创建时间之前")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页大小")
    sort_by: Optional[str] = Field("created_at", description="排序字段")
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$", description="排序方向")


# 更新前向引用
from .user import UserResponse
ProjectResponse.model_rebuild()
ProjectMemberResponse.model_rebuild()
ProjectInviteResponse.model_rebuild()
ProjectActivityResponse.model_rebuild()