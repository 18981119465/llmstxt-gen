"""
用户模型
"""

from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Table, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base, TimestampMixin, ActivatedMixin
from ..schemas.user import UserRole, UserStatus


# 用户角色关联表
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id'), primary_key=True),
    Column('created_at', DateTime, default=func.now(), nullable=False)
)


# 用户权限关联表
user_permissions = Table(
    'user_permissions',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('permission_id', UUID(as_uuid=True), ForeignKey('permissions.id'), primary_key=True),
    Column('granted_at', DateTime, default=func.now(), nullable=False),
    Column('granted_by', UUID(as_uuid=True), ForeignKey('users.id'))
)


# 角色权限关联表
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', UUID(as_uuid=True), ForeignKey('permissions.id'), primary_key=True),
    Column('created_at', DateTime, default=func.now(), nullable=False)
)


class User(Base, TimestampMixin, ActivatedMixin):
    """用户模型"""
    __tablename__ = 'users'
    
    # 基本信息
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # 用户状态
    status = Column(String(20), default=UserStatus.ACTIVE, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    phone_verified = Column(Boolean, default=False, nullable=False)
    
    # 用户信息
    phone = Column(String(20), nullable=True)
    bio = Column(Text, nullable=True)
    timezone = Column(String(50), default='UTC', nullable=False)
    language = Column(String(10), default='en', nullable=False)
    
    # 登录信息
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String(45), nullable=True)
    login_count = Column(Integer, default=0, nullable=False)
    
    # 安全信息
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, nullable=True)
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(255), nullable=True)
    
    # 用户设置
    settings = Column(JSONB, nullable=True)
    preferences = Column(JSONB, nullable=True)
    
    # 关联关系
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    owned_projects = relationship("Project", back_populates="owner")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        user_dict = {
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'avatar_url': self.avatar_url,
            'status': self.status,
            'email_verified': self.email_verified,
            'phone_verified': self.phone_verified,
            'phone': self.phone,
            'bio': self.bio,
            'timezone': self.timezone,
            'language': self.language,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'login_count': self.login_count,
            'mfa_enabled': self.mfa_enabled,
            'settings': self.settings,
            'preferences': self.preferences,
            'roles': [role.to_dict() for role in self.roles] if self.roles else [],
            'permissions': []
        }
        return {**base_dict, **user_dict}
    
    def has_permission(self, permission_code: str) -> bool:
        """检查用户是否有指定权限"""
        # 检查角色权限
        for role in self.roles:
            if role.has_permission(permission_code):
                return True
        
        return False
    
    def has_role(self, role_name: str) -> bool:
        """检查用户是否有指定角色"""
        return any(role.name == role_name for role in self.roles)


class Role(Base, TimestampMixin):
    """角色模型"""
    __tablename__ = 'roles'
    
    name = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_system = Column(Boolean, default=False, nullable=False)  # 系统角色不可删除
    
    # 关联关系
    users = relationship("User", secondary=user_roles, back_populates="roles")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        role_dict = {
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'is_system': self.is_system,
            'permissions': []
        }
        return {**base_dict, **role_dict}
    
    def has_permission(self, permission_code: str) -> bool:
        """检查角色是否有指定权限"""
        return False  # 简化实现，避免循环引用


class Permission(Base, TimestampMixin):
    """权限模型"""
    __tablename__ = 'permissions'
    
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    resource = Column(String(100), nullable=False)  # 资源类型
    action = Column(String(50), nullable=False)  # 操作类型
    is_system = Column(Boolean, default=False, nullable=False)  # 系统权限不可删除
    
    # 关联关系
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        perm_dict = {
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'resource': self.resource,
            'action': self.action,
            'is_system': self.is_system
        }
        return {**base_dict, **perm_dict}


class UserSession(Base, TimestampMixin):
    """用户会话模型"""
    __tablename__ = 'user_sessions'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, nullable=True)
    device_info = Column(JSONB, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # 关联关系
    user = relationship("User", backref="sessions")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        session_dict = {
            'user_id': str(self.user_id),
            'device_info': self.device_info,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'is_active': self.is_active
        }
        return {**base_dict, **session_dict}