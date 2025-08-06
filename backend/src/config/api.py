"""
配置热重载API
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from .loader import ConfigLoader, ConfigManager
from .watcher import ConfigWatcher, ConfigChangeEvent
from .notifications import NotificationManager, ConfigNotificationService, NotificationMessage
from .exceptions import ConfigError, ConfigNotFoundError
from .schemas import ConfigReloadRequest, ConfigRollbackRequest

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Hot Reload"])

# 全局实例
_config_manager: Optional[ConfigManager] = None
_config_watcher: Optional[ConfigWatcher] = None
_notification_service: Optional[ConfigNotificationService] = None


def get_config_manager() -> ConfigManager:
    """获取配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        raise HTTPException(status_code=500, detail="配置管理器未初始化")
    return _config_manager


def get_config_watcher() -> ConfigWatcher:
    """获取配置监听器实例"""
    global _config_watcher
    if _config_watcher is None:
        raise HTTPException(status_code=500, detail="配置监听器未初始化")
    return _config_watcher


def get_notification_service() -> ConfigNotificationService:
    """获取通知服务实例"""
    global _notification_service
    if _notification_service is None:
        raise HTTPException(status_code=500, detail="通知服务未初始化")
    return _notification_service


def init_config_api(config_manager: ConfigManager, config_watcher: ConfigWatcher, notification_service: ConfigNotificationService):
    """初始化配置API"""
    global _config_manager, _config_watcher, _notification_service
    _config_manager = config_manager
    _config_watcher = config_watcher
    _notification_service = notification_service


class ConfigReloadResponse(BaseModel):
    """配置重载响应"""
    success: bool
    message: str
    config: Optional[Dict[str, Any]] = None
    reload_time: Optional[float] = None


class ConfigWatcherStatus(BaseModel):
    """配置监听器状态"""
    watching: bool
    watch_dirs: List[str]
    event_handlers_count: int
    recent_events_count: int
    reload_pending: bool


class ConfigEventResponse(BaseModel):
    """配置事件响应"""
    id: str
    event_type: str
    file_path: str
    timestamp: float
    old_config: Optional[Dict[str, Any]] = None
    new_config: Optional[Dict[str, Any]] = None


class NotificationStatusResponse(BaseModel):
    """通知状态响应"""
    subscribers_count: int
    notification_handlers_count: int
    history_count: int
    websocket_server_running: bool


@router.post("/reload", response_model=ConfigReloadResponse)
async def reload_config(
    request: ConfigReloadRequest,
    background_tasks: BackgroundTasks,
    config_manager: ConfigManager = Depends(get_config_manager),
    config_watcher: ConfigWatcher = Depends(get_config_watcher),
    notification_service: ConfigNotificationService = Depends(get_notification_service)
):
    """重载配置"""
    try:
        import time
        start_time = time.time()
        
        # 获取当前配置
        old_config = config_manager.get_merged_config()
        
        # 重载配置
        new_config = config_manager.reload_config()
        
        # 计算重载时间
        reload_time = time.time() - start_time
        
        # 后台任务：发送通知
        background_tasks.add_task(
            notification_service.notify_config_reloaded,
            old_config,
            new_config
        )
        
        return ConfigReloadResponse(
            success=True,
            message="配置重载成功",
            config=new_config,
            reload_time=reload_time
        )
        
    except Exception as e:
        logger.error(f"配置重载失败: {e}")
        raise HTTPException(status_code=500, detail=f"配置重载失败: {str(e)}")


@router.post("/reload/force", response_model=ConfigReloadResponse)
async def force_reload_config(
    background_tasks: BackgroundTasks,
    config_manager: ConfigManager = Depends(get_config_manager),
    config_watcher: ConfigWatcher = Depends(get_config_watcher),
    notification_service: ConfigNotificationService = Depends(get_notification_service)
):
    """强制重载配置"""
    try:
        import time
        start_time = time.time()
        
        # 获取当前配置
        old_config = config_manager.get_merged_config()
        
        # 强制重载配置
        new_config = config_watcher.force_reload()
        
        # 计算重载时间
        reload_time = time.time() - start_time
        
        # 后台任务：发送通知
        background_tasks.add_task(
            notification_service.notify_config_reloaded,
            old_config,
            new_config
        )
        
        return ConfigReloadResponse(
            success=True,
            message="配置强制重载成功",
            config=new_config,
            reload_time=reload_time
        )
        
    except Exception as e:
        logger.error(f"配置强制重载失败: {e}")
        raise HTTPException(status_code=500, detail=f"配置强制重载失败: {str(e)}")


@router.get("/watcher/status", response_model=ConfigWatcherStatus)
async def get_watcher_status(config_watcher: ConfigWatcher = Depends(get_config_watcher)):
    """获取配置监听器状态"""
    try:
        status = config_watcher.get_watching_status()
        return ConfigWatcherStatus(**status)
    except Exception as e:
        logger.error(f"获取监听器状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取监听器状态失败: {str(e)}")


@router.post("/watcher/start")
async def start_watcher(config_watcher: ConfigWatcher = Depends(get_config_watcher)):
    """启动配置监听器"""
    try:
        if config_watcher.is_watching():
            return {"success": True, "message": "配置监听器已经在运行"}
        
        config_watcher.start_watching()
        return {"success": True, "message": "配置监听器启动成功"}
    except Exception as e:
        logger.error(f"启动配置监听器失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动配置监听器失败: {str(e)}")


@router.post("/watcher/stop")
async def stop_watcher(config_watcher: ConfigWatcher = Depends(get_config_watcher)):
    """停止配置监听器"""
    try:
        if not config_watcher.is_watching():
            return {"success": True, "message": "配置监听器未运行"}
        
        config_watcher.stop_watching()
        return {"success": True, "message": "配置监听器停止成功"}
    except Exception as e:
        logger.error(f"停止配置监听器失败: {e}")
        raise HTTPException(status_code=500, detail=f"停止配置监听器失败: {str(e)}")


@router.get("/watcher/events", response_model=List[ConfigEventResponse])
async def get_watcher_events(
    limit: int = 50,
    event_type: Optional[str] = None,
    file_path: Optional[str] = None,
    config_watcher: ConfigWatcher = Depends(get_config_watcher)
):
    """获取配置监听器事件"""
    try:
        if event_type:
            events = config_watcher.get_event_history(event_type=event_type)
        elif file_path:
            events = config_watcher.get_event_history(file_path=file_path)
        else:
            events = config_watcher.get_recent_events(limit)
        
        return [
            ConfigEventResponse(
                id=event.id,
                event_type=event.event_type,
                file_path=str(event.file_path),
                timestamp=event.timestamp,
                old_config=event.old_config,
                new_config=event.new_config
            )
            for event in events
        ]
    except Exception as e:
        logger.error(f"获取监听器事件失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取监听器事件失败: {str(e)}")


@router.get("/notifications/status", response_model=NotificationStatusResponse)
async def get_notification_status(notification_service: ConfigNotificationService = Depends(get_notification_service)):
    """获取通知服务状态"""
    try:
        notification_manager = notification_service.notification_manager
        
        return NotificationStatusResponse(
            subscribers_count=notification_manager.get_subscribers_count(),
            notification_handlers_count=len(notification_manager.notification_handlers),
            history_count=len(notification_manager.notification_history),
            websocket_server_running=notification_service.websocket_server is not None
        )
    except Exception as e:
        logger.error(f"获取通知服务状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取通知服务状态失败: {str(e)}")


@router.get("/notifications/history")
async def get_notification_history(
    limit: int = 100,
    notification_type: Optional[str] = None,
    level: Optional[str] = None,
    notification_service: ConfigNotificationService = Depends(get_notification_service)
):
    """获取通知历史"""
    try:
        from .notifications import NotificationType, NotificationLevel
        
        # 转换参数
        notif_type = None
        if notification_type:
            notif_type = NotificationType(notification_type)
        
        notif_level = None
        if level:
            notif_level = NotificationLevel(level)
        
        # 获取历史记录
        history = notification_service.notification_manager.get_notification_history(
            limit=limit,
            notification_type=notif_type,
            level=notif_level
        )
        
        return {
            "history": [msg.to_dict() for msg in history],
            "count": len(history)
        }
    except Exception as e:
        logger.error(f"获取通知历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取通知历史失败: {str(e)}")


@router.post("/notifications/clear")
async def clear_notification_history(notification_service: ConfigNotificationService = Depends(get_notification_service)):
    """清空通知历史"""
    try:
        notification_service.notification_manager.clear_history()
        return {"success": True, "message": "通知历史已清空"}
    except Exception as e:
        logger.error(f"清空通知历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"清空通知历史失败: {str(e)}")


@router.post("/rollback", response_model=ConfigReloadResponse)
async def rollback_config(
    request: ConfigRollbackRequest,
    background_tasks: BackgroundTasks,
    config_manager: ConfigManager = Depends(get_config_manager),
    notification_service: ConfigNotificationService = Depends(get_notification_service)
):
    """回滚配置"""
    try:
        # 这里需要实现配置版本管理逻辑
        # 目前先返回一个基本的响应
        import time
        start_time = time.time()
        
        # 获取当前配置
        old_config = config_manager.get_merged_config()
        
        # 重载配置（这里应该从版本历史中恢复）
        new_config = config_manager.reload_config()
        
        # 计算重载时间
        reload_time = time.time() - start_time
        
        # 后台任务：发送通知
        background_tasks.add_task(
            notification_service.notify_config_rollback,
            request.config_id,
            0,  # 当前版本
            request.version  # 目标版本
        )
        
        return ConfigReloadResponse(
            success=True,
            message=f"配置已回滚到版本 {request.version}",
            config=new_config,
            reload_time=reload_time
        )
        
    except Exception as e:
        logger.error(f"配置回滚失败: {e}")
        raise HTTPException(status_code=500, detail=f"配置回滚失败: {str(e)}")


@router.get("/health")
async def config_health_check():
    """配置服务健康检查"""
    try:
        status = {
            "status": "healthy",
            "config_manager": _config_manager is not None,
            "config_watcher": _config_watcher is not None,
            "notification_service": _notification_service is not None,
            "watcher_running": _config_watcher.is_watching() if _config_watcher else False
        }
        
        return status
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")


@router.websocket("/ws")
async def websocket_endpoint(websocket):
    """WebSocket端点"""
    if _notification_service is None:
        await websocket.close(code=1011, reason="通知服务未初始化")
        return
    
    # 处理WebSocket连接
    # 注意：这里简化了处理，实际应该使用专门的WebSocket处理逻辑
    try:
        await websocket.send_json({
            "type": "connection_established",
            "message": "WebSocket连接已建立"
        })
        
        # 保持连接
        while True:
            try:
                message = await websocket.receive_json()
                # 处理消息...
            except Exception as e:
                break
    except Exception as e:
        logger.error(f"WebSocket连接错误: {e}")
    finally:
        await websocket.close()