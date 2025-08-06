"""
统一配置API路由
整合配置管理和热重载功能
"""

from fastapi import APIRouter
from .management import router as management_router
from .api import router as hot_reload_router

# 创建统一的路由器
router = APIRouter()

# 包含管理功能路由 (无前缀)
router.include_router(management_router)

# 包含热重载功能路由
router.include_router(hot_reload_router)

# 导出主要的路由器
__all__ = ["router"]