"""
配置文件监听器
"""

import os
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from .exceptions import ConfigError
from .loader import ConfigLoader
import logging

logger = logging.getLogger(__name__)


class ConfigFileEventHandler(FileSystemEventHandler):
    """配置文件事件处理器"""
    
    def __init__(self, config_watcher: 'ConfigWatcher'):
        self.config_watcher = config_watcher
        self._file_patterns = ['.yaml', '.yml']
    
    def on_modified(self, event: FileSystemEvent):
        """文件修改事件处理"""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        if file_path.suffix in self._file_patterns:
            logger.info(f"检测到配置文件变更: {file_path}")
            self.config_watcher._handle_config_change(file_path)
    
    def on_created(self, event: FileSystemEvent):
        """文件创建事件处理"""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        if file_path.suffix in self._file_patterns:
            logger.info(f"检测到新配置文件: {file_path}")
            self.config_watcher._handle_config_change(file_path)
    
    def on_deleted(self, event: FileSystemEvent):
        """文件删除事件处理"""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        if file_path.suffix in self._file_patterns:
            logger.info(f"检测到配置文件删除: {file_path}")
            self.config_watcher._handle_config_change(file_path)


class ConfigChangeEvent:
    """配置变更事件"""
    
    def __init__(self, event_type: str, file_path: Path, old_config: Optional[Dict[str, Any]] = None, new_config: Optional[Dict[str, Any]] = None):
        self.event_type = event_type  # 'modified', 'created', 'deleted'
        self.file_path = file_path
        self.old_config = old_config
        self.new_config = new_config
        self.timestamp = time.time()
        self.id = f"{event_type}_{int(self.timestamp * 1000)}"


class ConfigWatcher:
    """配置监听器"""
    
    def __init__(self, config_loader: ConfigLoader, watch_dirs: Optional[List[str]] = None):
        self.config_loader = config_loader
        self.watch_dirs = watch_dirs or [str(config_loader.config_dir)]
        self.observer = Observer()
        self.event_handlers: List[Callable[[ConfigChangeEvent], None]] = []
        self.recent_events: List[ConfigChangeEvent] = []
        self.max_events = 100
        self._watching = False
        self._reload_lock = threading.Lock()
        self._reload_pending = False
        self._reload_timer = None
        self._debounce_time = 1.0  # 防抖时间（秒）
    
    def add_event_handler(self, handler: Callable[[ConfigChangeEvent], None]):
        """添加事件处理器"""
        self.event_handlers.append(handler)
    
    def remove_event_handler(self, handler: Callable[[ConfigChangeEvent], None]):
        """移除事件处理器"""
        if handler in self.event_handlers:
            self.event_handlers.remove(handler)
    
    def start_watching(self):
        """开始监听"""
        if self._watching:
            logger.warning("配置监听器已经在运行")
            return
        
        logger.info(f"开始监听配置目录: {self.watch_dirs}")
        
        # 创建事件处理器
        event_handler = ConfigFileEventHandler(self)
        
        # 添加监听目录
        for watch_dir in self.watch_dirs:
            if os.path.exists(watch_dir):
                self.observer.schedule(event_handler, watch_dir, recursive=True)
                logger.info(f"添加监听目录: {watch_dir}")
            else:
                logger.warning(f"监听目录不存在: {watch_dir}")
        
        # 启动观察者
        self.observer.start()
        self._watching = True
        
        logger.info("配置监听器启动成功")
    
    def stop_watching(self):
        """停止监听"""
        if not self._watching:
            return
        
        logger.info("停止配置监听器")
        
        # 停止观察者
        self.observer.stop()
        self.observer.join()
        self._watching = False
        
        # 取消待处理的重载
        if self._reload_timer:
            self._reload_timer.cancel()
            self._reload_timer = None
        
        logger.info("配置监听器已停止")
    
    def _handle_config_change(self, file_path: Path):
        """处理配置变更"""
        try:
            # 记录事件
            event = ConfigChangeEvent('modified', file_path)
            self._add_event(event)
            
            # 通知事件处理器
            self._notify_handlers(event)
            
            # 防抖处理
            with self._reload_lock:
                if self._reload_timer:
                    self._reload_timer.cancel()
                
                # 延迟执行重载，避免频繁变更导致多次重载
                import threading
                self._reload_timer = threading.Timer(self._debounce_time, self._debounced_reload)
                self._reload_timer.start()
                self._reload_pending = True
            
        except Exception as e:
            logger.error(f"处理配置变更时出错: {e}")
    
    def _debounced_reload(self):
        """防抖重载"""
        with self._reload_lock:
            self._reload_pending = False
            self._reload_timer = None
        
        try:
            self._reload_config()
        except Exception as e:
            logger.error(f"重载配置时出错: {e}")
    
    def _reload_config(self):
        """重载配置"""
        try:
            # 获取当前配置
            old_config = self.config_loader.get_merged_config()
            
            # 重载配置
            new_config = self.config_loader.reload_config()
            
            # 创建变更事件
            event = ConfigChangeEvent('reloaded', Path(self.config_loader.config_dir), old_config, new_config)
            self._add_event(event)
            
            # 通知事件处理器
            self._notify_handlers(event)
            
            logger.info("配置重载成功")
            
        except Exception as e:
            logger.error(f"配置重载失败: {e}")
            raise ConfigError(f"配置重载失败: {e}")
    
    def _add_event(self, event: ConfigChangeEvent):
        """添加事件到历史记录"""
        self.recent_events.append(event)
        
        # 限制事件数量
        if len(self.recent_events) > self.max_events:
            self.recent_events = self.recent_events[-self.max_events:]
    
    def _notify_handlers(self, event: ConfigChangeEvent):
        """通知事件处理器"""
        for handler in self.event_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"事件处理器执行失败: {e}")
    
    def get_recent_events(self, limit: int = 50) -> List[ConfigChangeEvent]:
        """获取最近的事件"""
        return self.recent_events[-limit:]
    
    def get_event_history(self, event_type: Optional[str] = None, file_path: Optional[str] = None) -> List[ConfigChangeEvent]:
        """获取事件历史"""
        events = self.recent_events
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if file_path:
            events = [e for e in events if str(e.file_path) == file_path]
        
        return events
    
    def force_reload(self) -> Dict[str, Any]:
        """强制重载配置"""
        logger.info("强制重载配置")
        return self._reload_config()
    
    def is_watching(self) -> bool:
        """是否正在监听"""
        return self._watching
    
    def get_watching_status(self) -> Dict[str, Any]:
        """获取监听状态"""
        return {
            'watching': self._watching,
            'watch_dirs': self.watch_dirs,
            'event_handlers_count': len(self.event_handlers),
            'recent_events_count': len(self.recent_events),
            'reload_pending': self._reload_pending
        }
    
    def __enter__(self):
        """上下文管理器支持"""
        self.start_watching()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器支持"""
        self.stop_watching()