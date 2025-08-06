"""
配置变更通知系统
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime
from .watcher import ConfigChangeEvent
import websockets
from websockets.server import WebSocketServerProtocol

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """通知类型"""
    CONFIG_CHANGED = "config_changed"
    CONFIG_RELOADED = "config_reloaded"
    CONFIG_VALIDATION_ERROR = "config_validation_error"
    CONFIG_ROLLBACK = "config_rollback"
    SYSTEM_STATUS = "system_status"


class NotificationLevel(str, Enum):
    """通知级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    DEBUG = "debug"


@dataclass
class NotificationMessage:
    """通知消息"""
    id: str
    type: NotificationType
    level: NotificationLevel
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        result['type'] = self.type.value
        result['level'] = self.level.value
        return result


class NotificationManager:
    """通知管理器"""
    
    def __init__(self):
        self.subscribers: Dict[str, WebSocketServerProtocol] = {}
        self.notification_handlers: List[Callable[[NotificationMessage], None]] = []
        self.notification_history: List[NotificationMessage] = []
        self.max_history = 1000
        self._lock = asyncio.Lock()
    
    async def subscribe(self, websocket: WebSocketServerProtocol, client_id: str):
        """订阅通知"""
        async with self._lock:
            self.subscribers[client_id] = websocket
            logger.info(f"客户端 {client_id} 订阅通知")
            
            # 发送欢迎消息
            welcome_msg = NotificationMessage(
                id=f"welcome_{int(datetime.now().timestamp())}",
                type=NotificationType.SYSTEM_STATUS,
                level=NotificationLevel.INFO,
                title="连接成功",
                message="已成功连接到配置通知服务",
                data={"client_id": client_id}
            )
            await self._send_to_client(websocket, welcome_msg)
    
    async def unsubscribe(self, client_id: str):
        """取消订阅"""
        async with self._lock:
            if client_id in self.subscribers:
                del self.subscribers[client_id]
                logger.info(f"客户端 {client_id} 取消订阅")
    
    def add_notification_handler(self, handler: Callable[[NotificationMessage], None]):
        """添加通知处理器"""
        self.notification_handlers.append(handler)
    
    def remove_notification_handler(self, handler: Callable[[NotificationMessage], None]):
        """移除通知处理器"""
        if handler in self.notification_handlers:
            self.notification_handlers.remove(handler)
    
    async def send_notification(self, notification: NotificationMessage):
        """发送通知"""
        # 添加到历史记录
        self.notification_history.append(notification)
        
        # 限制历史记录数量
        if len(self.notification_history) > self.max_history:
            self.notification_history = self.notification_history[-self.max_history:]
        
        # 通知处理器
        for handler in self.notification_handlers:
            try:
                handler(notification)
            except Exception as e:
                logger.error(f"通知处理器执行失败: {e}")
        
        # 发送给所有订阅者
        if self.subscribers:
            await self._broadcast_notification(notification)
    
    async def _broadcast_notification(self, notification: NotificationMessage):
        """广播通知"""
        async with self._lock:
            if not self.subscribers:
                return
            
            # 创建通知消息
            message = json.dumps(notification.to_dict(), ensure_ascii=False)
            
            # 发送给所有客户端
            disconnected_clients = []
            for client_id, websocket in self.subscribers.items():
                try:
                    await websocket.send(message)
                except websockets.exceptions.ConnectionClosed:
                    disconnected_clients.append(client_id)
                except Exception as e:
                    logger.error(f"发送通知给客户端 {client_id} 失败: {e}")
                    disconnected_clients.append(client_id)
            
            # 清理断开连接的客户端
            for client_id in disconnected_clients:
                del self.subscribers[client_id]
                logger.warning(f"客户端 {client_id} 连接已断开，已移除")
    
    async def _send_to_client(self, websocket: WebSocketServerProtocol, notification: NotificationMessage):
        """发送消息给特定客户端"""
        try:
            message = json.dumps(notification.to_dict(), ensure_ascii=False)
            await websocket.send(message)
        except Exception as e:
            logger.error(f"发送消息给客户端失败: {e}")
    
    def get_notification_history(self, limit: int = 100, 
                                notification_type: Optional[NotificationType] = None,
                                level: Optional[NotificationLevel] = None) -> List[NotificationMessage]:
        """获取通知历史"""
        history = self.notification_history
        
        if notification_type:
            history = [n for n in history if n.type == notification_type]
        
        if level:
            history = [n for n in history if n.level == level]
        
        return history[-limit:]
    
    def get_subscribers_count(self) -> int:
        """获取订阅者数量"""
        return len(self.subscribers)
    
    def clear_history(self):
        """清空通知历史"""
        self.notification_history.clear()
        logger.info("通知历史已清空")


class ConfigNotificationService:
    """配置通知服务"""
    
    def __init__(self, notification_manager: NotificationManager):
        self.notification_manager = notification_manager
        self.websocket_server = None
        self._server_task = None
    
    async def start_websocket_server(self, host: str = "0.0.0.0", port: int = 8765):
        """启动WebSocket服务器"""
        logger.info(f"启动配置通知WebSocket服务器: {host}:{port}")
        
        async def handle_client(websocket: WebSocketServerProtocol, path: str):
            """处理客户端连接"""
            client_id = f"client_{id(websocket)}"
            try:
                await self.notification_manager.subscribe(websocket, client_id)
                
                # 保持连接
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        await self._handle_client_message(client_id, data)
                    except json.JSONDecodeError:
                        logger.warning(f"客户端 {client_id} 发送了无效的JSON消息")
                    except Exception as e:
                        logger.error(f"处理客户端 {client_id} 消息失败: {e}")
                        
            except websockets.exceptions.ConnectionClosed:
                logger.info(f"客户端 {client_id} 连接关闭")
            except Exception as e:
                logger.error(f"处理客户端 {client_id} 连接失败: {e}")
            finally:
                await self.notification_manager.unsubscribe(client_id)
        
        # 启动服务器
        self.websocket_server = await websockets.serve(handle_client, host, port)
        self._server_task = asyncio.create_task(self.websocket_server.wait_closed())
        
        logger.info(f"配置通知WebSocket服务器已启动: {host}:{port}")
    
    async def stop_websocket_server(self):
        """停止WebSocket服务器"""
        if self.websocket_server:
            logger.info("停止配置通知WebSocket服务器")
            self.websocket_server.close()
            await self.websocket_server.wait_closed()
            self.websocket_server = None
        
        if self._server_task:
            self._server_task.cancel()
            try:
                await self._server_task
            except asyncio.CancelledError:
                pass
            self._server_task = None
    
    async def _handle_client_message(self, client_id: str, data: Dict[str, Any]):
        """处理客户端消息"""
        action = data.get('action')
        
        if action == 'ping':
            # 心跳检测
            pong_msg = NotificationMessage(
                id=f"pong_{int(datetime.now().timestamp())}",
                type=NotificationType.SYSTEM_STATUS,
                level=NotificationLevel.DEBUG,
                title="心跳响应",
                message="服务器正常运行",
                data={"client_id": client_id}
            )
            await self.notification_manager.send_notification(pong_msg)
        
        elif action == 'get_history':
            # 获取历史记录
            limit = data.get('limit', 50)
            history = self.notification_manager.get_notification_history(limit)
            
            response = NotificationMessage(
                id=f"history_{int(datetime.now().timestamp())}",
                type=NotificationType.SYSTEM_STATUS,
                level=NotificationLevel.INFO,
                title="通知历史",
                message="获取通知历史成功",
                data={
                    "history": [msg.to_dict() for msg in history],
                    "count": len(history)
                }
            )
            await self.notification_manager.send_notification(response)
        
        else:
            logger.warning(f"未知的客户端动作: {action}")
    
    async def notify_config_changed(self, event: ConfigChangeEvent):
        """通知配置变更"""
        notification = NotificationMessage(
            id=f"config_change_{int(datetime.now().timestamp())}",
            type=NotificationType.CONFIG_CHANGED,
            level=NotificationLevel.INFO,
            title="配置变更",
            message=f"配置文件 {event.file_path.name} 发生变更",
            data={
                "file_path": str(event.file_path),
                "event_type": event.event_type,
                "timestamp": event.timestamp
            }
        )
        await self.notification_manager.send_notification(notification)
    
    async def notify_config_reloaded(self, old_config: Dict[str, Any], new_config: Dict[str, Any]):
        """通知配置重载"""
        notification = NotificationMessage(
            id=f"config_reload_{int(datetime.now().timestamp())}",
            type=NotificationType.CONFIG_RELOADED,
            level=NotificationLevel.INFO,
            title="配置重载",
            message="配置已成功重载",
            data={
                "old_config_size": len(old_config) if old_config else 0,
                "new_config_size": len(new_config) if new_config else 0,
                "timestamp": datetime.now().isoformat()
            }
        )
        await self.notification_manager.send_notification(notification)
    
    async def notify_config_validation_error(self, errors: List[str]):
        """通知配置验证错误"""
        notification = NotificationMessage(
            id=f"validation_error_{int(datetime.now().timestamp())}",
            type=NotificationType.CONFIG_VALIDATION_ERROR,
            level=NotificationLevel.ERROR,
            title="配置验证错误",
            message=f"配置验证失败，发现 {len(errors)} 个错误",
            data={
                "errors": errors,
                "error_count": len(errors)
            }
        )
        await self.notification_manager.send_notification(notification)
    
    async def notify_config_rollback(self, config_id: str, from_version: int, to_version: int):
        """通知配置回滚"""
        notification = NotificationMessage(
            id=f"rollback_{int(datetime.now().timestamp())}",
            type=NotificationType.CONFIG_ROLLBACK,
            level=NotificationLevel.WARNING,
            title="配置回滚",
            message=f"配置 {config_id} 从版本 {from_version} 回滚到版本 {to_version}",
            data={
                "config_id": config_id,
                "from_version": from_version,
                "to_version": to_version
            }
        )
        await self.notification_manager.send_notification(notification)