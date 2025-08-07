"""
监控系统配置管理模块

负责加载和管理监控系统的配置信息。
"""

import os
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
import json
import logging


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    format: str = "json"
    output: str = "both"
    file_path: str = "logs/app.log"
    max_size: str = "100MB"
    backup_count: int = 5
    rotation: str = "daily"
    fields: list = field(default_factory=lambda: [
        "timestamp", "level", "service_name", "message", 
        "user_id", "request_id", "trace_id", "span_id",
        "function_name", "line_number", "metadata"
    ])
    sensitive_fields: list = field(default_factory=lambda: [
        "password", "token", "api_key", "secret", "credit_card"
    ])
    hot_reload: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True, "watch_files": True, "reload_interval": 30
    })


@dataclass
class HealthConfig:
    """健康检查配置"""
    endpoint: str = "/health"
    check_interval: int = 30
    timeout: int = 10
    checks: list = field(default_factory=lambda: [
        {"name": "database", "type": "database", "enabled": True, "critical": True},
        {"name": "redis", "type": "redis", "enabled": True, "critical": True},
        {"name": "disk_space", "type": "disk", "enabled": True, "critical": False, "threshold": 10},
        {"name": "memory", "type": "memory", "enabled": True, "critical": False, "threshold": 80},
        {"name": "cpu", "type": "cpu", "enabled": True, "critical": False, "threshold": 80}
    ])


@dataclass
class MetricsConfig:
    """性能指标配置"""
    collection_interval: int = 15
    prometheus: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True, "port": 9090, "path": "/metrics"
    })
    custom_metrics: list = field(default_factory=lambda: [
        {"name": "request_count", "type": "counter", "description": "Total number of requests"},
        {"name": "request_duration", "type": "histogram", "description": "Request duration in seconds"},
        {"name": "error_count", "type": "counter", "description": "Total number of errors"},
        {"name": "active_users", "type": "gauge", "description": "Number of active users"}
    ])
    system_metrics: list = field(default_factory=lambda: [
        "cpu_usage", "memory_usage", "disk_usage", "network_io", "disk_io"
    ])


@dataclass
class AlertsConfig:
    """告警配置"""
    min_level: str = "WARNING"
    rules: list = field(default_factory=list)
    notifications: list = field(default_factory=list)
    history: Dict[str, Any] = field(default_factory=lambda: {
        "retention_days": 30, "max_records": 10000
    })


@dataclass
class DashboardConfig:
    """仪表板配置"""
    port: int = 3001
    refresh_interval: int = 30
    charts: list = field(default_factory=list)


@dataclass
class StorageConfig:
    """存储配置"""
    database: Dict[str, Any] = field(default_factory=lambda: {
        "type": "postgresql", "host": "localhost", "port": 5432,
        "database": "llmstxt_monitoring", "username": "postgres", "password": "",
        "table_prefix": "monitoring_"
    })
    redis: Dict[str, Any] = field(default_factory=lambda: {
        "host": "localhost", "port": 6379, "db": 1, "password": ""
    })
    retention: Dict[str, str] = field(default_factory=lambda: {
        "logs": "30d", "metrics": "90d", "alerts": "365d", "health_checks": "7d"
    })


@dataclass
class SecurityConfig:
    """安全配置"""
    access_control: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True, "admin_users": [], "viewer_users": []
    })
    encryption: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True, "key_rotation_days": 90
    })
    audit: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True, "log_access": True, "log_modifications": True
    })


@dataclass
class PerformanceConfig:
    """性能配置"""
    cache: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True, "ttl": 300, "max_size": 10000
    })
    batch: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True, "size": 100, "timeout": "5s"
    })
    concurrency: Dict[str, Any] = field(default_factory=lambda: {
        "max_workers": 10, "max_queue_size": 1000
    })


@dataclass
class MonitoringConfig:
    """监控系统主配置"""
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    health: HealthConfig = field(default_factory=HealthConfig)
    metrics: MetricsConfig = field(default_factory=MetricsConfig)
    alerts: AlertsConfig = field(default_factory=AlertsConfig)
    dashboard: DashboardConfig = field(default_factory=DashboardConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self._config: Optional[MonitoringConfig] = None
        self._watchers = []
        
    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        current_dir = Path(__file__).parent.parent.parent.parent
        return str(current_dir / "config" / "monitoring.yaml")
    
    def load_config(self) -> MonitoringConfig:
        """加载配置文件"""
        try:
            if not os.path.exists(self.config_path):
                logging.warning(f"配置文件不存在: {self.config_path}")
                return MonitoringConfig()
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # 解析监控配置
            monitoring_data = config_data.get('monitoring', {})
            
            # 创建配置对象
            config = MonitoringConfig()
            
            # 解析日志配置
            if 'logging' in monitoring_data:
                logging_data = monitoring_data['logging']
                config.logging = LoggingConfig(**logging_data)
            
            # 解析健康检查配置
            if 'health' in monitoring_data:
                health_data = monitoring_data['health']
                config.health = HealthConfig(**health_data)
            
            # 解析指标配置
            if 'metrics' in monitoring_data:
                metrics_data = monitoring_data['metrics']
                config.metrics = MetricsConfig(**metrics_data)
            
            # 解析告警配置
            if 'alerts' in monitoring_data:
                alerts_data = monitoring_data['alerts']
                config.alerts = AlertsConfig(**alerts_data)
            
            # 解析仪表板配置
            if 'dashboard' in monitoring_data:
                dashboard_data = monitoring_data['dashboard']
                config.dashboard = DashboardConfig(**dashboard_data)
            
            # 解析存储配置
            if 'storage' in monitoring_data:
                storage_data = monitoring_data['storage']
                config.storage = StorageConfig(**storage_data)
            
            # 解析安全配置
            if 'security' in monitoring_data:
                security_data = monitoring_data['security']
                config.security = SecurityConfig(**security_data)
            
            # 解析性能配置
            if 'performance' in monitoring_data:
                performance_data = monitoring_data['performance']
                config.performance = PerformanceConfig(**performance_data)
            
            self._config = config
            logging.info(f"配置加载成功: {self.config_path}")
            return config
            
        except Exception as e:
            logging.error(f"加载配置文件失败: {e}")
            return MonitoringConfig()
    
    def get_config(self) -> MonitoringConfig:
        """获取当前配置"""
        if self._config is None:
            self._config = self.load_config()
        return self._config
    
    def reload_config(self) -> MonitoringConfig:
        """重新加载配置"""
        self._config = None
        return self.load_config()
    
    def save_config(self, config: MonitoringConfig) -> bool:
        """保存配置到文件"""
        try:
            # 将配置对象转换为字典
            config_dict = {
                'monitoring': {
                    'logging': self._dataclass_to_dict(config.logging),
                    'health': self._dataclass_to_dict(config.health),
                    'metrics': self._dataclass_to_dict(config.metrics),
                    'alerts': self._dataclass_to_dict(config.alerts),
                    'dashboard': self._dataclass_to_dict(config.dashboard),
                    'storage': self._dataclass_to_dict(config.storage),
                    'security': self._dataclass_to_dict(config.security),
                    'performance': self._dataclass_to_dict(config.performance)
                }
            }
            
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # 保存配置文件
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
            
            self._config = config
            logging.info(f"配置保存成功: {self.config_path}")
            return True
            
        except Exception as e:
            logging.error(f"保存配置文件失败: {e}")
            return False
    
    def _dataclass_to_dict(self, obj) -> Dict[str, Any]:
        """将dataclass对象转换为字典"""
        if hasattr(obj, '__dataclass_fields__'):
            result = {}
            for field_name, field_value in obj.__dict__.items():
                if hasattr(field_value, '__dataclass_fields__'):
                    result[field_name] = self._dataclass_to_dict(field_value)
                else:
                    result[field_name] = field_value
            return result
        return obj
    
    def watch_config(self, callback):
        """监听配置文件变化"""
        import threading
        import time
        
        def watch_thread():
            last_mtime = 0
            while True:
                try:
                    if os.path.exists(self.config_path):
                        current_mtime = os.path.getmtime(self.config_path)
                        if current_mtime != last_mtime:
                            last_mtime = current_mtime
                            new_config = self.reload_config()
                            if callback:
                                callback(new_config)
                except Exception as e:
                    logging.error(f"监听配置文件变化失败: {e}")
                
                time.sleep(5)  # 每5秒检查一次
        
        thread = threading.Thread(target=watch_thread, daemon=True)
        thread.start()
        self._watchers.append(thread)


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_monitoring_config() -> MonitoringConfig:
    """获取监控配置"""
    return get_config_manager().get_config()


def load_monitoring_config(config_path: Optional[str] = None) -> MonitoringConfig:
    """加载监控配置"""
    if config_path:
        return ConfigManager(config_path).load_config()
    return get_monitoring_config()