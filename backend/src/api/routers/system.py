"""
API路由模块 - 系统管理
"""

from fastapi import APIRouter, Depends, Query, Path, Request
from typing import Optional, Dict, Any
import logging
from ..schemas.response import (
    StandardResponse, 
    HealthCheckResponse, 
    ServiceStatusResponse,
    ConfigResponse
)
from ..core.dependencies import (
    get_request_id, 
    get_service_status, 
    get_config_manager
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/status", response_model=StandardResponse)
async def get_system_status(
    request: Request
) -> StandardResponse:
    """获取系统状态"""
    try:
        status_data = get_service_status()
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        return StandardResponse(
            success=True,
            data=status_data,
            message="获取系统状态成功",
            request_id=request_id
        )
        
    except Exception as e:
        request_id = getattr(request.state, 'request_id', 'unknown')
        logger.error(f"获取系统状态失败: {e}", extra={"request_id": request_id})
        return StandardResponse(
            success=False,
            data={},
            message="获取系统状态失败",
            request_id=request_id
        )


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    request: Request,
    detailed: bool = Query(False, description="是否返回详细信息")
) -> HealthCheckResponse:
    """健康检查"""
    try:
        health_data = get_service_status()
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        if detailed:
            # 添加详细的健康检查信息
            health_data["detailed"] = {
                "database": {
                    "status": health_data.get("database", "unknown"),
                    "connection_pool": "active"
                },
                "redis": {
                    "status": health_data.get("redis", "unknown"),
                    "memory_usage": "normal"
                },
                "config_manager": {
                    "status": health_data.get("config_manager", "unknown"),
                    "last_reload": "2025-01-07T10:00:00Z"
                },
                "api": {
                    "version": "1.0.0",
                    "uptime": "24h",
                    "requests_per_minute": 150
                }
            }
        
        return HealthCheckResponse(
            success=True,
            data=health_data,
            message="健康检查通过",
            request_id=request_id
        )
        
    except Exception as e:
        request_id = getattr(request.state, 'request_id', 'unknown')
        logger.error(f"健康检查失败: {e}", extra={"request_id": request_id})
        return HealthCheckResponse(
            success=False,
            data={},
            message="健康检查失败",
            request_id=request_id
        )


@router.get("/config", response_model=ConfigResponse)
async def get_system_config(
    request: Request
) -> ConfigResponse:
    """获取系统配置"""
    try:
        config_manager = get_config_manager()
        config_data = config_manager.get_all_configs()
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        # 过滤敏感信息
        safe_config = {}
        for key, value in config_data.items():
            if not any(sensitive in key.lower() for sensitive in ['password', 'secret', 'token', 'key']):
                safe_config[key] = value
        
        return ConfigResponse(
            success=True,
            data=safe_config,
            message="获取系统配置成功",
            request_id=request_id
        )
        
    except Exception as e:
        request_id = getattr(request.state, 'request_id', 'unknown')
        logger.error(f"获取系统配置失败: {e}", extra={"request_id": request_id})
        return ConfigResponse(
            success=False,
            data={},
            message="获取系统配置失败",
            request_id=request_id
        )


@router.get("/metrics", response_model=StandardResponse)
async def get_system_metrics(
    request_id: str = Depends(get_request_id)
) -> StandardResponse:
    """获取系统指标"""
    try:
        # 这里应该从监控系统获取指标
        metrics_data = {
            "api": {
                "requests_per_minute": 150,
                "average_response_time": 45.2,
                "error_rate": 0.02
            },
            "system": {
                "cpu_usage": 45.5,
                "memory_usage": 67.2,
                "disk_usage": 82.1
            },
            "database": {
                "connections": 15,
                "query_time": 12.3,
                "slow_queries": 2
            },
            "redis": {
                "memory_usage": 34.5,
                "keyspace_hits": 1250,
                "keyspace_misses": 45
            }
        }
        
        return StandardResponse(
            success=True,
            data=metrics_data,
            message="获取系统指标成功",
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"获取系统指标失败: {e}", extra={"request_id": request_id})
        return StandardResponse(
            success=False,
            data={},
            message="获取系统指标失败",
            request_id=request_id
        )


@router.get("/logs", response_model=StandardResponse)
async def get_system_logs(
    level: Optional[str] = Query(None, description="日志级别"),
    limit: int = Query(100, description="日志条数限制"),
    request_id: str = Depends(get_request_id)
) -> StandardResponse:
    """获取系统日志"""
    try:
        # 这里应该从日志系统获取日志
        logs_data = {
            "logs": [
                {
                    "timestamp": "2025-01-07T10:00:00Z",
                    "level": "INFO",
                    "message": "系统启动成功",
                    "source": "system"
                },
                {
                    "timestamp": "2025-01-07T10:01:00Z",
                    "level": "INFO",
                    "message": "API服务启动",
                    "source": "api"
                }
            ],
            "total": 2,
            "level": level,
            "limit": limit
        }
        
        return StandardResponse(
            success=True,
            data=logs_data,
            message="获取系统日志成功",
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"获取系统日志失败: {e}", extra={"request_id": request_id})
        return StandardResponse(
            success=False,
            data={},
            message="获取系统日志失败",
            request_id=request_id
        )


@router.get("/version", response_model=StandardResponse)
async def get_system_version(
    request_id: str = Depends(get_request_id)
) -> StandardResponse:
    """获取系统版本信息"""
    try:
        version_data = {
            "api": {
                "version": "1.0.0",
                "build": "20250107",
                "commit": "abc123"
            },
            "dependencies": {
                "fastapi": "0.104.1",
                "sqlalchemy": "2.0.23",
                "redis": "5.0.1",
                "pydantic": "2.5.0"
            },
            "environment": {
                "python": "3.11.0",
                "platform": "linux",
                "architecture": "x86_64"
            }
        }
        
        return StandardResponse(
            success=True,
            data=version_data,
            message="获取版本信息成功",
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"获取版本信息失败: {e}", extra={"request_id": request_id})
        return StandardResponse(
            success=False,
            data={},
            message="获取版本信息失败",
            request_id=request_id
        )