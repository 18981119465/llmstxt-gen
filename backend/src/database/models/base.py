"""
基础数据模型类
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4
import uuid

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base, as_declarative
from sqlalchemy.sql import func

Base = declarative_base()


class Base(Base):
    """基础模型类"""
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': str(self.id),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active
        }
    
    def update(self, **kwargs):
        """更新模型属性"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = func.now()


class TimestampMixin:
    """时间戳混入类"""
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class SoftDeleteMixin:
    """软删除混入类"""
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    
    def soft_delete(self):
        """软删除"""
        self.is_deleted = True
        self.deleted_at = func.now()
    
    def restore(self):
        """恢复"""
        self.is_deleted = False
        self.deleted_at = None


class ActivatedMixin:
    """激活状态混入类"""
    is_active = Column(Boolean, default=True, nullable=False)
    activated_at = Column(DateTime, default=func.now(), nullable=True)
    
    def activate(self):
        """激活"""
        self.is_active = True
        self.activated_at = func.now()
    
    def deactivate(self):
        """停用"""
        self.is_active = False
        self.activated_at = None