"""
配置系统核心模块
"""
import asyncio
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

from .loader import ConfigManager
from .watcher import ConfigWatcher
from .notifications import ConfigNotificationService
from .rollback import ConfigRollbackManager
from .validator import ConfigValidator
from .schemas import ConfigHistory, ConfigValidationResult
from .exceptions import ConfigError

logger = logging.getLogger(__name__)


class ConfigSystem:
    """配置系统核心类"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化配置系统
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config_manager = ConfigManager(self.config_path)
        self.config_watcher = None
        self.notification_service = None
        self.rollback_manager = None
        self.validator = None
        self._is_watching = False
        
        logger.info(f"配置系统初始化，配置文件路径: {self.config_path}")
    
    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        # 优先级：环境变量 > 当前目录config.yaml > 项目根目录config.yaml
        env_path = os.getenv('CONFIG_PATH')
        if env_path:
            return env_path
        
        current_dir_config = Path.cwd() / 'config.yaml'
        if current_dir_config.exists():
            return str(current_dir_config)
        
        # 回退到项目根目录
        project_root = Path(__file__).parent.parent.parent
        project_config = project_root / 'config.yaml'
        return str(project_config)
    
    async def start_watching(self):
        """启动配置文件监听"""
        if self._is_watching:
            logger.warning("配置文件监听已启动")
            return
        
        try:
            # 初始化组件
            self.validator = ConfigValidator()
            self.rollback_manager = ConfigRollbackManager(self.config_path)
            self.notification_service = ConfigNotificationService()
            
            # 启动配置文件监听
            self.config_watcher = ConfigWatcher(
                config_path=self.config_path,
                config_manager=self.config_manager,
                notification_service=self.notification_service,
                rollback_manager=self.rollback_manager
            )
            
            await self.config_watcher.start_watching()
            self._is_watching = True
            
            logger.info("配置文件监听启动成功")
            
        except Exception as e:
            logger.error(f"启动配置文件监听失败: {e}")
            raise ConfigError(f"启动配置文件监听失败: {e}")
    
    async def stop_watching(self):
        """停止配置文件监听"""
        if not self._is_watching:
            logger.warning("配置文件监听未启动")
            return
        
        try:
            if self.config_watcher:
                await self.config_watcher.stop_watching()
                self.config_watcher = None
            
            if self.notification_service:
                await self.notification_service.stop()
                self.notification_service = None
            
            self._is_watching = False
            logger.info("配置文件监听已停止")
            
        except Exception as e:
            logger.error(f"停止配置文件监听失败: {e}")
            raise ConfigError(f"停止配置文件监听失败: {e}")
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self.config_manager.load_config()
    
    def get_config_info(self) -> Dict[str, Any]:
        """获取配置信息"""
        return self.config_manager.get_config_info()
    
    def reload_config(self) -> bool:
        """重新加载配置"""
        try:
            self.config_manager.reload_config()
            logger.info("配置重新加载成功")
            return True
        except Exception as e:
            logger.error(f"重新加载配置失败: {e}")
            return False
    
    def validate_config(self) -> ConfigValidationResult:
        """验证配置"""
        if not self.validator:
            raise ConfigError("配置验证器未初始化")
        
        config = self.get_config()
        return self.validator.validate_config(config)
    
    def get_config_history(self, limit: int = 50) -> List[ConfigHistory]:
        """获取配置历史"""
        if not self.rollback_manager:
            raise ConfigError("配置回滚管理器未初始化")
        
        return self.rollback_manager.get_history(limit)
    
    def rollback_config(self, version_id: str) -> bool:
        """回滚配置到指定版本"""
        if not self.rollback_manager:
            raise ConfigError("配置回滚管理器未初始化")
        
        return self.rollback_manager.rollback(version_id)
    
    def export_config(self, format_type: str = 'yaml', include_metadata: bool = True) -> str:
        """导出配置
        
        Args:
            format_type: 导出格式 (yaml, json)
            include_metadata: 是否包含元数据
            
        Returns:
            str: 导出的配置内容
        """
        config = self.get_config()
        
        if include_metadata:
            config['_metadata'] = {
                'exported_at': self._get_timestamp(),
                'version': '1.0',
                'source_path': self.config_path
            }
        
        if format_type.lower() == 'yaml':
            import yaml
            return yaml.dump(config, default_flow_style=False, allow_unicode=True)
        elif format_type.lower() == 'json':
            import json
            return json.dumps(config, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"不支持的导出格式: {format_type}")
    
    def import_config(self, config_content: str, format_type: str = 'yaml', backup: bool = True) -> bool:
        """导入配置
        
        Args:
            config_content: 配置内容
            format_type: 配置格式 (yaml, json)
            backup: 是否备份当前配置
            
        Returns:
            bool: 导入是否成功
        """
        try:
            # 解析配置
            if format_type.lower() == 'yaml':
                import yaml
                new_config = yaml.safe_load(config_content)
            elif format_type.lower() == 'json':
                import json
                new_config = json.loads(config_content)
            else:
                raise ValueError(f"不支持的配置格式: {format_type}")
            
            # 移除元数据
            if '_metadata' in new_config:
                del new_config['_metadata']
            
            # 验证配置
            if self.validator:
                validation_result = self.validator.validate_config(new_config)
                if not validation_result.valid:
                    raise ConfigError(f"配置验证失败: {validation_result.errors}")
            
            # 备份当前配置
            if backup and self.rollback_manager:
                self.rollback_manager.create_version()
            
            # 保存新配置
            self.config_manager.save_config(new_config)
            
            logger.info("配置导入成功")
            return True
            
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            raise ConfigError(f"导入配置失败: {e}")
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    @property
    def is_watching(self) -> bool:
        """是否正在监听配置文件"""
        return self._is_watching
    
    @property
    def config_file_path(self) -> str:
        """获取配置文件路径"""
        return self.config_path