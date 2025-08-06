"""
配置系统模块
"""
import logging

from .loader import ConfigLoader, ConfigManager, get_config, get_app_config, get_service_config, reload_config
from .validator import ConfigValidator
from .priority import ConfigPriority, ConfigMerger, ConfigStrategy
from .watcher import ConfigWatcher, ConfigChangeEvent
from .notifications import (
    NotificationManager, NotificationMessage, ConfigNotificationService,
    NotificationType, NotificationLevel
)
from .rollback import ConfigRollbackManager, ConfigVersion
from .api import router as config_api_router, init_config_api
from .management import init_config_management
from .routes import router as config_router
from .web import router as config_web_router
from .schemas import (
    AppConfig, SystemConfig, DatabaseConfig, RedisConfig, ApiConfig,
    AIServiceConfig, DocumentProcessorConfig, WebCrawlerConfig,
    LoggingConfig, MonitoringConfig, SecurityConfig, StorageConfig,
    ConfigTemplate, ConfigPreset, ConfigHistory, ConfigValidationResult,
    ConfigUpdateRequest, ConfigReloadRequest, ConfigRollbackRequest,
    EnvironmentType, LogLevel, StorageType
)
from .exceptions import (
    ConfigError, ConfigNotFoundError, ConfigValidationError,
    ConfigLoadError, ConfigParseError, ConfigMergeError, ConfigAccessError
)

logger = logging.getLogger(__name__)

__all__ = [
    # 核心类
    'ConfigLoader', 'ConfigManager', 'ConfigValidator', 
    'ConfigPriority', 'ConfigMerger', 'ConfigStrategy',
    
    # 热重载相关
    'ConfigWatcher', 'ConfigChangeEvent', 'ConfigRollbackManager', 'ConfigVersion',
    
    # 通知系统
    'NotificationManager', 'NotificationMessage', 'ConfigNotificationService',
    'NotificationType', 'NotificationLevel',
    
    # API相关
    'config_api_router', 'config_router', 'config_web_router', 'init_config_api', 'init_config_management',
    
    # 配置模型
    'AppConfig', 'SystemConfig', 'DatabaseConfig', 'RedisConfig', 'ApiConfig',
    'AIServiceConfig', 'DocumentProcessorConfig', 'WebCrawlerConfig',
    'LoggingConfig', 'MonitoringConfig', 'SecurityConfig', 'StorageConfig',
    'ConfigTemplate', 'ConfigPreset', 'ConfigHistory', 'ConfigValidationResult',
    'ConfigUpdateRequest', 'ConfigReloadRequest', 'ConfigRollbackRequest',
    
    # 枚举
    'EnvironmentType', 'LogLevel', 'StorageType',
    
    # 异常
    'ConfigError', 'ConfigNotFoundError', 'ConfigValidationError',
    'ConfigLoadError', 'ConfigParseError', 'ConfigMergeError', 'ConfigAccessError',
    
    # 便捷函数
    'get_config', 'get_app_config', 'get_service_config', 'reload_config',
    
    # 系统初始化
    'init_config_system', 'get_config_system', 'shutdown_config_system'
]

# 全局配置系统实例
_config_system = None

async def init_config_system(config_path: str = None, watch: bool = True) -> 'ConfigSystem':
    """初始化配置系统
    
    Args:
        config_path: 配置文件路径
        watch: 是否启用配置文件监听
        
    Returns:
        ConfigSystem: 配置系统实例
    """
    global _config_system
    
    if _config_system is not None:
        return _config_system
    
    from .core import ConfigSystem
    
    try:
        _config_system = ConfigSystem(config_path=config_path)
        
        if watch:
            await _config_system.start_watching()
        
        logger.info("配置系统初始化成功")
        return _config_system
        
    except Exception as e:
        logger.error(f"配置系统初始化失败: {e}")
        raise

def get_config_system() -> 'ConfigSystem':
    """获取配置系统实例
    
    Returns:
        ConfigSystem: 配置系统实例
    """
    if _config_system is None:
        raise RuntimeError("配置系统未初始化，请先调用 init_config_system")
    return _config_system

async def shutdown_config_system():
    """关闭配置系统"""
    global _config_system
    
    if _config_system is not None:
        try:
            await _config_system.stop_watching()
            _config_system = None
            logger.info("配置系统已关闭")
        except Exception as e:
            logger.error(f"关闭配置系统失败: {e}")
            raise