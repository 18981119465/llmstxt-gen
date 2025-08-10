"""
项目模型
"""

from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Integer, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base, TimestampMixin, ActivatedMixin


class Project(Base, TimestampMixin, ActivatedMixin):
    """项目模型"""
    __tablename__ = 'projects'
    
    # 基本信息
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    
    # 项目配置
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    config = Column(JSONB, nullable=True)
    settings = Column(JSONB, nullable=True)
    
    # 项目状态
    status = Column(String(20), default='active', nullable=False)
    visibility = Column(String(20), default='private', nullable=False)  # private, public, team
    is_archived = Column(Boolean, default=False, nullable=False)
    
    # 项目统计
    document_count = Column(Integer, default=0, nullable=False)
    task_count = Column(Integer, default=0, nullable=False)
    storage_used = Column(Integer, default=0, nullable=False)  # bytes
    
    # 项目设置
    max_documents = Column(Integer, default=1000, nullable=False)
    max_storage = Column(Integer, default=1024*1024*1024, nullable=False)  # 1GB
    allowed_file_types = Column(JSONB, nullable=True)
    
    # 关联关系
    owner = relationship("User", back_populates="owned_projects")
    documents = relationship("Document", back_populates="project")
    tasks = relationship("Task", back_populates="project")
    project_configs = relationship("ProjectConfig", back_populates="project")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        project_dict = {
            'name': self.name,
            'description': self.description,
            'slug': self.slug,
            'owner_id': str(self.owner_id),
            'config': self.config,
            'settings': self.settings,
            'status': self.status,
            'visibility': self.visibility,
            'is_archived': self.is_archived,
            'document_count': self.document_count,
            'task_count': self.task_count,
            'storage_used': self.storage_used,
            'max_documents': self.max_documents,
            'max_storage': self.max_storage,
            'allowed_file_types': self.allowed_file_types,
            'owner': self.owner.to_dict() if self.owner else None
        }
        return {**base_dict, **project_dict}
    
    def update_stats(self):
        """更新项目统计"""
        self.document_count = len([d for d in self.documents if d.is_active])
        self.task_count = len([t for t in self.tasks if t.is_active])
        self.storage_used = sum(d.file_size or 0 for d in self.documents if d.is_active)


class ProjectConfig(Base, TimestampMixin):
    """项目配置模型"""
    __tablename__ = 'project_configs'
    
    # 配置信息
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    config_type = Column(String(50), nullable=False, index=True)  # document, task, system, etc.
    name = Column(String(100), nullable=False)
    value = Column(JSONB, nullable=False)
    description = Column(Text, nullable=True)
    
    # 配置属性
    is_active = Column(Boolean, default=True, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)  # 系统配置不可删除
    version = Column(Integer, default=1, nullable=False)
    
    # 关联关系
    project = relationship("Project", back_populates="project_configs")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        config_dict = {
            'project_id': str(self.project_id),
            'config_type': self.config_type,
            'name': self.name,
            'value': self.value,
            'description': self.description,
            'is_system': self.is_system,
            'version': self.version
        }
        return {**base_dict, **config_dict}


class ProjectMember(Base, TimestampMixin):
    """项目成员模型"""
    __tablename__ = 'project_members'
    
    # 成员信息
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # 成员角色和权限
    role = Column(String(50), default='member', nullable=False)  # owner, admin, member, viewer
    permissions = Column(JSONB, nullable=True)
    
    # 成员状态
    status = Column(String(20), default='active', nullable=False)  # active, inactive, pending, removed
    joined_at = Column(DateTime, default=func.now(), nullable=False)
    left_at = Column(DateTime, nullable=True)
    
    # 成员设置
    can_invite = Column(Boolean, default=False, nullable=False)
    can_edit = Column(Boolean, default=False, nullable=False)
    can_delete = Column(Boolean, default=False, nullable=False)
    can_manage_members = Column(Boolean, default=False, nullable=False)
    
    # 关联关系
    project = relationship("Project")
    user = relationship("User")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        member_dict = {
            'project_id': str(self.project_id),
            'user_id': str(self.user_id),
            'role': self.role,
            'permissions': self.permissions,
            'status': self.status,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'left_at': self.left_at.isoformat() if self.left_at else None,
            'can_invite': self.can_invite,
            'can_edit': self.can_edit,
            'can_delete': self.can_delete,
            'can_manage_members': self.can_manage_members,
            'user': self.user.to_dict() if self.user else None
        }
        return {**base_dict, **member_dict}


class ProjectInvite(Base, TimestampMixin):
    """项目邀请模型"""
    __tablename__ = 'project_invites'
    
    # 邀请信息
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    inviter_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    invitee_email = Column(String(255), nullable=False)
    invitee_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    
    # 邀请设置
    role = Column(String(50), default='member', nullable=False)
    permissions = Column(JSONB, nullable=True)
    message = Column(Text, nullable=True)
    
    # 邀请状态
    status = Column(String(20), default='pending', nullable=False)  # pending, accepted, rejected, expired
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    
    # 关联关系
    project = relationship("Project")
    inviter = relationship("User", foreign_keys=[inviter_id])
    invitee = relationship("User", foreign_keys=[invitee_id])
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        invite_dict = {
            'project_id': str(self.project_id),
            'inviter_id': str(self.inviter_id),
            'invitee_email': self.invitee_email,
            'invitee_id': str(self.invitee_id) if self.invitee_id else None,
            'role': self.role,
            'permissions': self.permissions,
            'message': self.message,
            'status': self.status,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'accepted_at': self.accepted_at.isoformat() if self.accepted_at else None,
            'rejected_at': self.rejected_at.isoformat() if self.rejected_at else None,
            'inviter': self.inviter.to_dict() if self.inviter else None,
            'invitee': self.invitee.to_dict() if self.invitee else None
        }
        return {**base_dict, **invite_dict}


class ProjectActivity(Base, TimestampMixin):
    """项目活动模型"""
    __tablename__ = 'project_activities'
    
    # 活动信息
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # 活动内容
    action = Column(String(50), nullable=False)  # created, updated, deleted, joined, left, etc.
    resource_type = Column(String(50), nullable=False)  # project, document, task, member, etc.
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    resource_name = Column(String(255), nullable=True)
    
    # 活动详情
    details = Column(JSONB, nullable=True)
    changes = Column(JSONB, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # 关联关系
    project = relationship("Project")
    user = relationship("User")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        base_dict = super().to_dict()
        activity_dict = {
            'project_id': str(self.project_id),
            'user_id': str(self.user_id),
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': str(self.resource_id) if self.resource_id else None,
            'resource_name': self.resource_name,
            'details': self.details,
            'changes': self.changes,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'user': self.user.to_dict() if self.user else None
        }
        return {**base_dict, **activity_dict}