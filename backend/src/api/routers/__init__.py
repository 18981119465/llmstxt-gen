"""
API框架routers模块
"""

from .system import router as system_router
from .auth import router as auth_router

__all__ = ['system_router', 'auth_router']