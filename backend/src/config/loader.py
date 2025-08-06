"""
配置加载器
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from .schemas import AppConfig, EnvironmentType
from .validator import ConfigValidator
from .priority import ConfigPriority, ConfigMerger
from .exceptions import ConfigError, ConfigNotFoundError, ConfigValidationError


class ConfigLoader:
    """配置加载器"""
    
    def __init__(self, config_dir: str = "config", env: Optional[str] = None):
        self.config_dir = Path(config_dir)
        self.env = env or os.getenv('ENV', 'development')
        self.validator = ConfigValidator()
        self.priority = ConfigPriority()
        self.merger = ConfigMerger()
        self._loaded_configs = {}
        self._merged_config = None
    
    def load_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """加载配置"""
        if self._merged_config and not force_reload:
            return self._merged_config
        
        try:
            # 加载所有配置文件
            configs = self._load_all_configs()
            
            # 验证配置层次结构
            validation_result = self.validator.validate_config_hierarchy(configs)
            if not validation_result.is_valid:
                raise ConfigValidationError(f"配置验证失败: {validation_result.errors}")
            
            # 合并配置
            merged_config = self.merger.merge_with_strategy(configs)
            
            # 验证最终配置
            final_validation = self.validator.validate_config(merged_config)
            if not final_validation.is_valid:
                raise ConfigValidationError(f"最终配置验证失败: {final_validation.errors}")
            
            # 检查环境变量
            env_errors = self.validator.validate_environment_variables(merged_config)
            if env_errors:
                raise ConfigValidationError(f"环境变量验证失败: {env_errors}")
            
            self._merged_config = merged_config
            self._loaded_configs = configs
            
            return merged_config
            
        except Exception as e:
            raise ConfigError(f"配置加载失败: {str(e)}")
    
    def _load_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """加载所有配置文件"""
        configs = {}
        
        # 必需的配置文件
        required_configs = ['default', self.env]
        
        # 加载默认配置
        default_config = self._load_config_file('default.yaml')
        if default_config:
            configs['default'] = default_config
        
        # 加载环境配置
        env_config = self._load_config_file(f'{self.env}.yaml')
        if env_config:
            configs[self.env] = env_config
        
        # 加载模板配置
        template_dir = self.config_dir / 'templates'
        if template_dir.exists():
            for template_file in template_dir.glob('*.yaml'):
                template_name = template_file.stem
                template_config = self._load_config_file(f'templates/{template_file.name}')
                if template_config:
                    configs[f'{template_name}.template'] = template_config
        
        # 加载预设配置
        preset_dir = self.config_dir / 'presets'
        if preset_dir.exists():
            for preset_file in preset_dir.glob('*.yaml'):
                preset_name = preset_file.stem
                preset_config = self._load_config_file(f'presets/{preset_file.name}')
                if preset_config:
                    configs[f'{preset_name}.preset'] = preset_config
        
        # 加载覆盖配置
        override_config = self._load_config_file('override.yaml')
        if override_config:
            configs['override'] = override_config
        
        return configs
    
    def _load_config_file(self, filename: str) -> Optional[Dict[str, Any]]:
        """加载单个配置文件"""
        file_path = self.config_dir / filename
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if filename.endswith('.yaml') or filename.endswith('.yml'):
                    return yaml.safe_load(f)
                elif filename.endswith('.json'):
                    return json.load(f)
                else:
                    raise ConfigError(f"不支持的配置文件格式: {filename}")
                    
        except Exception as e:
            raise ConfigError(f"加载配置文件 {filename} 失败: {str(e)}")
    
    def get_app_config(self) -> AppConfig:
        """获取应用配置对象"""
        config_dict = self.load_config()
        return AppConfig(**config_dict)
    
    def get_config_value(self, key_path: str, default: Any = None) -> Any:
        """获取配置值"""
        if not self._merged_config:
            self.load_config()
        
        keys = key_path.split('.')
        value = self._merged_config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """获取服务配置"""
        config = self.load_config()
        return config.get(service_name, {})
    
    def get_merged_config(self) -> Dict[str, Any]:
        """获取合并后的配置"""
        if not self._merged_config:
            self.load_config()
        return self._merged_config
    
    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        return self.get_service_config('database')
    
    def get_redis_config(self) -> Dict[str, Any]:
        """获取Redis配置"""
        return self.get_service_config('redis')
    
    def get_api_config(self) -> Dict[str, Any]:
        """获取API配置"""
        return self.get_service_config('api')
    
    def get_ai_service_config(self) -> Dict[str, Any]:
        """获取AI服务配置"""
        return self.get_service_config('ai_service')
    
    def get_document_processor_config(self) -> Dict[str, Any]:
        """获取文档处理服务配置"""
        return self.get_service_config('document_processor')
    
    def get_web_crawler_config(self) -> Dict[str, Any]:
        """获取网站爬取服务配置"""
        return self.get_service_config('web_crawler')
    
    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self.get_service_config('logging')
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """获取监控配置"""
        return self.get_service_config('monitoring')
    
    def get_security_config(self) -> Dict[str, Any]:
        """获取安全配置"""
        return self.get_service_config('security')
    
    def get_storage_config(self) -> Dict[str, Any]:
        """获取存储配置"""
        return self.get_service_config('storage')
    
    def get_system_config(self) -> Dict[str, Any]:
        """获取系统配置"""
        return self.get_service_config('system')
    
    def reload_config(self) -> Dict[str, Any]:
        """重载配置"""
        return self.load_config(force_reload=True)
    
    def validate_config_file(self, file_path: str) -> Dict[str, Any]:
        """验证配置文件"""
        return self.validator.validate_config_file(file_path)
    
    def get_config_source(self, key_path: str) -> Optional[str]:
        """获取配置值来源"""
        return self.priority.get_config_source(key_path)
    
    def list_config_files(self) -> List[str]:
        """列出所有配置文件"""
        config_files = []
        
        # 递归查找配置文件
        for file_path in self.config_dir.rglob('*.yaml'):
            relative_path = file_path.relative_to(self.config_dir)
            config_files.append(str(relative_path))
        
        for file_path in self.config_dir.rglob('*.yml'):
            relative_path = file_path.relative_to(self.config_dir)
            config_files.append(str(relative_path))
        
        for file_path in self.config_dir.rglob('*.json'):
            relative_path = file_path.relative_to(self.config_dir)
            config_files.append(str(relative_path))
        
        return sorted(config_files)
    
    def get_config_info(self) -> Dict[str, Any]:
        """获取配置信息"""
        return {
            'config_dir': str(self.config_dir),
            'environment': self.env,
            'loaded_files': self.list_config_files(),
            'config_sources': list(self._loaded_configs.keys()),
            'merged_config_size': len(self._merged_config) if self._merged_config else 0
        }


class ConfigManager:
    """配置管理器 - 全局配置管理"""
    
    _instance = None
    _config_loader = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config_dir: str = "config", env: Optional[str] = None):
        if self._config_loader is None:
            self._config_loader = ConfigLoader(config_dir, env)
    
    @classmethod
    def get_instance(cls, config_dir: str = "config", env: Optional[str] = None):
        """获取配置管理器实例"""
        if cls._instance is None:
            cls._instance = cls(config_dir, env)
        return cls._instance
    
    def load_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """加载配置"""
        return self._config_loader.load_config(force_reload)
    
    def get_config_value(self, key_path: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._config_loader.get_config_value(key_path, default)
    
    def get_app_config(self) -> AppConfig:
        """获取应用配置对象"""
        return self._config_loader.get_app_config()
    
    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """获取服务配置"""
        return self._config_loader.get_service_config(service_name)
    
    def reload_config(self) -> Dict[str, Any]:
        """重载配置"""
        return self._config_loader.reload_config()
    
    def get_config_info(self) -> Dict[str, Any]:
        """获取配置信息"""
        return self._config_loader.get_config_info()
    
    @classmethod
    def reset_instance(cls):
        """重置实例（用于测试）"""
        cls._instance = None
        cls._config_loader = None


# 便捷函数
def get_config(key_path: str = None, default: Any = None) -> Any:
    """获取配置值的便捷函数"""
    manager = ConfigManager.get_instance()
    if key_path is None:
        return manager.load_config()
    return manager.get_config_value(key_path, default)


def get_app_config() -> AppConfig:
    """获取应用配置对象的便捷函数"""
    manager = ConfigManager.get_instance()
    return manager.get_app_config()


def get_service_config(service_name: str) -> Dict[str, Any]:
    """获取服务配置的便捷函数"""
    manager = ConfigManager.get_instance()
    return manager.get_service_config(service_name)


def reload_config() -> Dict[str, Any]:
    """重载配置的便捷函数"""
    manager = ConfigManager.get_instance()
    return manager.reload_config()