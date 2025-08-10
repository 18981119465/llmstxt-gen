"""
用户相关schemas
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, EmailStr, field_validator, constr

from .base import BaseSchema, BaseResponse


class UserRole(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"
    GUEST = "guest"


class UserStatus(str, Enum):
    """用户状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"
    DELETED = "deleted"


class PermissionResource(str, Enum):
    """权限资源枚举"""
    USER = "user"
    PROJECT = "project"
    DOCUMENT = "document"
    TASK = "task"
    SYSTEM = "system"
    CONFIG = "config"


class PermissionAction(str, Enum):
    """权限操作枚举"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    MANAGE = "manage"


# 用户schemas
class UserBase(BaseSchema):
    """用户基础schema"""
    username: constr(min_length=3, max_length=50) = Field(..., description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    full_name: Optional[constr(max_length=100)] = Field(None, description="全名")
    phone: Optional[constr(max_length=20)] = Field(None, description="电话")
    bio: Optional[str] = Field(None, description="个人简介")
    timezone: str = Field("UTC", description="时区")
    language: str = Field("en", description="语言")
    is_active: bool = Field(True, description="是否激活")


class UserCreate(UserBase):
    """用户创建schema"""
    password: constr(min_length=8, max_length=100) = Field(..., description="密码")
    confirm_password: str = Field(..., description="确认密码")
    role: Optional[UserRole] = Field(UserRole.USER, description="角色")
    
    @field_validator('confirm_password')
    @classmethod
    def validate_passwords_match(cls, v, info):
        password = info.data.get('password')
        if password and v != password:
            raise ValueError('密码不匹配')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含数字')
        return v


class UserUpdate(BaseSchema):
    """用户更新schema"""
    full_name: Optional[constr(max_length=100)] = Field(None, description="全名")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    phone: Optional[constr(max_length=20)] = Field(None, description="电话")
    bio: Optional[str] = Field(None, description="个人简介")
    timezone: Optional[str] = Field(None, description="时区")
    language: Optional[str] = Field(None, description="语言")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    is_active: Optional[bool] = Field(None, description="是否激活")


class UserResponse(UserBase):
    """用户响应schema"""
    id: UUID = Field(..., description="用户ID")
    status: UserStatus = Field(..., description="用户状态")
    email_verified: bool = Field(..., description="邮箱是否验证")
    phone_verified: bool = Field(..., description="电话是否验证")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    login_count: int = Field(..., description="登录次数")
    mfa_enabled: bool = Field(..., description="是否启用多因素认证")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    roles: List['RoleResponse'] = Field(default_factory=list, description="用户角色")
    permissions: List['PermissionResponse'] = Field(default_factory=list, description="用户权限")


class UserProfile(UserResponse):
    """用户资料schema"""
    settings: Optional[dict] = Field(None, description="用户设置")
    preferences: Optional[dict] = Field(None, description="用户偏好")


class UserChangePassword(BaseSchema):
    """用户修改密码schema"""
    current_password: str = Field(..., description="当前密码")
    new_password: constr(min_length=8, max_length=100) = Field(..., description="新密码")
    confirm_password: str = Field(..., description="确认密码")
    
    @field_validator('confirm_password')
    @classmethod
    def validate_passwords_match(cls, v, info):
        new_password = info.data.get('new_password')
        if new_password and v != new_password:
            raise ValueError('密码不匹配')
        return v
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含数字')
        return v


# 角色schemas
class RoleBase(BaseSchema):
    """角色基础schema"""
    name: constr(min_length=2, max_length=50) = Field(..., description="角色名称")
    display_name: constr(min_length=2, max_length=100) = Field(..., description="显示名称")
    description: Optional[str] = Field(None, description="角色描述")
    is_system: bool = Field(False, description="是否系统角色")


class RoleCreate(RoleBase):
    """角色创建schema"""
    pass


class RoleUpdate(BaseSchema):
    """角色更新schema"""
    display_name: Optional[constr(max_length=100)] = Field(None, description="显示名称")
    description: Optional[str] = Field(None, description="角色描述")


class RoleResponse(RoleBase):
    """角色响应schema"""
    id: UUID = Field(..., description="角色ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    permissions: List['PermissionResponse'] = Field(default_factory=list, description="角色权限")


# 权限schemas
class PermissionBase(BaseSchema):
    """权限基础schema"""
    code: constr(min_length=2, max_length=50) = Field(..., description="权限代码")
    name: constr(min_length=2, max_length=100) = Field(..., description="权限名称")
    description: Optional[str] = Field(None, description="权限描述")
    resource: PermissionResource = Field(..., description="资源类型")
    action: PermissionAction = Field(..., description="操作类型")
    is_system: bool = Field(False, description="是否系统权限")


class PermissionCreate(PermissionBase):
    """权限创建schema"""
    pass


class PermissionUpdate(BaseSchema):
    """权限更新schema"""
    name: Optional[constr(max_length=100)] = Field(None, description="权限名称")
    description: Optional[str] = Field(None, description="权限描述")


class PermissionResponse(PermissionBase):
    """权限响应schema"""
    id: UUID = Field(..., description="权限ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


# 用户会话schemas
class UserSessionBase(BaseSchema):
    """用户会话基础schema"""
    user_id: UUID = Field(..., description="用户ID")
    device_info: Optional[dict] = Field(None, description="设备信息")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    expires_at: datetime = Field(..., description="过期时间")


class UserSessionCreate(UserSessionBase):
    """用户会话创建schema"""
    session_token: str = Field(..., description="会话令牌")
    refresh_token: Optional[str] = Field(None, description="刷新令牌")


class UserSessionResponse(UserSessionBase):
    """用户会话响应schema"""
    id: UUID = Field(..., description="会话ID")
    session_token: Optional[str] = Field(None, description="会话令牌")
    last_activity: datetime = Field(..., description="最后活动时间")
    is_active: bool = Field(..., description="是否活跃")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


# 用户登录schemas
class UserLogin(BaseSchema):
    """用户登录schema"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    remember_me: bool = Field(False, description="记住我")
    device_info: Optional[dict] = Field(None, description="设备信息")


class UserLoginResponse(BaseResponse):
    """用户登录响应schema"""
    data: dict = Field(..., description="登录数据")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "登录成功",
                "data": {
                    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "token_type": "Bearer",
                    "expires_in": 3600,
                    "user": {
                        "id": "12345678-1234-1234-1234-123456789012",
                        "username": "testuser",
                        "email": "test@example.com",
                        "full_name": "Test User",
                        "roles": ["user"],
                        "permissions": ["read", "write"]
                    }
                }
            }
        }


class UserRefreshToken(BaseSchema):
    """用户刷新令牌schema"""
    refresh_token: str = Field(..., description="刷新令牌")


class UserLogout(BaseSchema):
    """用户登出schema"""
    refresh_token: Optional[str] = Field(None, description="刷新令牌")
    session_token: Optional[str] = Field(None, description="会话令牌")


# 更新前向引用
UserResponse.model_rebuild()
RoleResponse.model_rebuild()