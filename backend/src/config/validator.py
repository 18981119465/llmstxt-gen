"""
配置验证器
"""

import os
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from .schemas import AppConfig, ConfigValidationResult, EnvironmentType
import yaml
import json
from jsonschema import validate, ValidationError


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self):
        self.required_fields = [
            'system', 'database', 'redis', 'api', 'ai_service',
            'document_processor', 'web_crawler', 'logging', 
            'monitoring', 'security', 'storage'
        ]
        self.schema = self._get_config_schema()
    
    def _get_config_schema(self) -> Dict[str, Any]:
        """获取配置JSON Schema"""
        return {
            "type": "object",
            "properties": {
                "system": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "minLength": 1},
                        "version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},
                        "debug": {"type": "boolean"},
                        "env": {"type": "string", "enum": ["development", "production", "testing"]}
                    },
                    "required": ["name", "version", "debug", "env"]
                },
                "database": {
                    "type": "object",
                    "properties": {
                        "host": {"type": "string", "minLength": 1},
                        "port": {"type": "integer", "minimum": 1, "maximum": 65535},
                        "name": {"type": "string", "minLength": 1},
                        "user": {"type": "string", "minLength": 1},
                        "password": {"type": "string"},
                        "pool_size": {"type": "integer", "minimum": 1, "maximum": 100},
                        "max_overflow": {"type": "integer", "minimum": 0, "maximum": 50},
                        "pool_timeout": {"type": "integer", "minimum": 1, "maximum": 300},
                        "pool_recycle": {"type": "integer", "minimum": 300}
                    },
                    "required": ["host", "port", "name", "user", "password"]
                },
                "redis": {
                    "type": "object",
                    "properties": {
                        "host": {"type": "string", "minLength": 1},
                        "port": {"type": "integer", "minimum": 1, "maximum": 65535},
                        "db": {"type": "integer", "minimum": 0, "maximum": 15},
                        "password": {"type": "string"},
                        "max_connections": {"type": "integer", "minimum": 1, "maximum": 100}
                    },
                    "required": ["host", "port", "db", "max_connections"]
                },
                "api": {
                    "type": "object",
                    "properties": {
                        "host": {"type": "string"},
                        "port": {"type": "integer", "minimum": 1, "maximum": 65535},
                        "workers": {"type": "integer", "minimum": 1, "maximum": 32},
                        "reload": {"type": "boolean"},
                        "cors_origins": {"type": "array", "items": {"type": "string"}},
                        "cors_methods": {"type": "array", "items": {"type": "string"}},
                        "cors_headers": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["host", "port", "workers"]
                }
            },
            "required": self.required_fields
        }
    
    def validate_config(self, config: Dict[str, Any]) -> ConfigValidationResult:
        """验证配置"""
        errors = []
        warnings = []
        
        try:
            # JSON Schema验证
            validate(instance=config, schema=self.schema)
            
            # Pydantic模型验证
            app_config = AppConfig(**config)
            
            # 额外的业务规则验证
            self._validate_business_rules(config, errors, warnings)
            
            if not errors:
                return ConfigValidationResult(
                    is_valid=True,
                    errors=errors,
                    warnings=warnings,
                    config=app_config.dict()
                )
            else:
                return ConfigValidationResult(
                    is_valid=False,
                    errors=errors,
                    warnings=warnings
                )
                
        except ValidationError as e:
            errors.append(f"JSON Schema验证失败: {e.message}")
        except Exception as e:
            errors.append(f"配置验证失败: {str(e)}")
        
        return ConfigValidationResult(
            is_valid=False,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_business_rules(self, config: Dict[str, Any], errors: List[str], warnings: List[str]):
        """验证业务规则"""
        
        # 系统配置验证
        system = config.get('system', {})
        if system.get('env') == 'production' and system.get('debug'):
            errors.append("生产环境不应启用调试模式")
        
        # 数据库配置验证
        database = config.get('database', {})
        if database.get('pool_size', 0) > 50:
            warnings.append("数据库连接池过大，可能导致资源浪费")
        
        # 安全配置验证
        security = config.get('security', {})
        secret_key = security.get('secret_key', '')
        if len(secret_key) < 32:
            errors.append("密钥长度不能少于32位")
        
        if secret_key in ['your-secret-key-change-in-production', 'dev-secret-key-not-for-production']:
            errors.append("请修改默认密钥")
        
        # API配置验证
        api = config.get('api', {})
        if api.get('cors_origins') == ['*'] and config.get('system', {}).get('env') == 'production':
            warnings.append("生产环境不建议使用通配符CORS配置")
        
        # 存储配置验证
        storage = config.get('storage', {})
        if storage.get('type') == 'local':
            local_path = storage.get('local_path', '')
            if not local_path:
                errors.append("本地存储路径不能为空")
            else:
                # 检查路径是否有效
                try:
                    Path(local_path).mkdir(parents=True, exist_ok=True)
                except Exception:
                    warnings.append(f"无法创建存储路径: {local_path}")
        
        # 服务配置验证
        ai_service = config.get('ai_service', {})
        if ai_service.get('enabled'):
            model = ai_service.get('model', '')
            if not model:
                errors.append("AI服务启用时必须指定模型")
        
        # 文档处理配置验证
        doc_processor = config.get('document_processor', {})
        if doc_processor.get('enabled'):
            max_size = doc_processor.get('max_file_size', 0)
            if max_size > 100 * 1024 * 1024:  # 100MB
                warnings.append("文档处理最大文件大小过大，可能影响性能")
        
        # 网站爬取配置验证
        web_crawler = config.get('web_crawler', {})
        if web_crawler.get('enabled'):
            delay = web_crawler.get('delay', 0)
            if delay < 1:
                warnings.append("爬取延迟小于1秒可能对目标服务器造成压力")
    
    def validate_environment_variables(self, config: Dict[str, Any]) -> List[str]:
        """验证环境变量引用"""
        errors = []
        
        def check_env_vars(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    if isinstance(value, str):
                        # 检查环境变量引用
                        env_vars = re.findall(r'\$\{([^}]+)\}', value)
                        for env_var in env_vars:
                            if not os.getenv(env_var):
                                errors.append(f"环境变量 {env_var} 未设置 (路径: {current_path})")
                    elif isinstance(value, (dict, list)):
                        check_env_vars(value, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_env_vars(item, f"{path}[{i}]")
        
        check_env_vars(config)
        return errors
    
    def validate_config_file(self, file_path: str) -> ConfigValidationResult:
        """验证配置文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                    config = yaml.safe_load(f)
                elif file_path.endswith('.json'):
                    config = json.load(f)
                else:
                    return ConfigValidationResult(
                        is_valid=False,
                        errors=[f"不支持的配置文件格式: {file_path}"]
                    )
            
            return self.validate_config(config)
            
        except FileNotFoundError:
            return ConfigValidationResult(
                is_valid=False,
                errors=[f"配置文件不存在: {file_path}"]
            )
        except yaml.YAMLError as e:
            return ConfigValidationResult(
                is_valid=False,
                errors=[f"YAML解析错误: {str(e)}"]
            )
        except json.JSONDecodeError as e:
            return ConfigValidationResult(
                is_valid=False,
                errors=[f"JSON解析错误: {str(e)}"]
            )
        except Exception as e:
            return ConfigValidationResult(
                is_valid=False,
                errors=[f"配置文件读取错误: {str(e)}"]
            )
    
    def validate_config_hierarchy(self, configs: Dict[str, Dict[str, Any]]) -> ConfigValidationResult:
        """验证配置层次结构"""
        errors = []
        warnings = []
        
        # 检查是否所有必需的配置文件都存在
        required_configs = ['default']
        env = os.getenv('ENV', 'development')
        required_configs.append(env)
        
        for config_name in required_configs:
            if config_name not in configs:
                errors.append(f"缺少必需的配置文件: {config_name}")
        
        # 检查配置继承关系
        for config_name, config in configs.items():
            if 'extends' in config:
                parent_config = config['extends']
                if parent_config not in configs:
                    errors.append(f"配置 {config_name} 继承的配置 {parent_config} 不存在")
        
        if not errors:
            # 合并配置并验证
            merged_config = self._merge_configs(configs)
            return self.validate_config(merged_config)
        
        return ConfigValidationResult(
            is_valid=False,
            errors=errors,
            warnings=warnings
        )
    
    def _merge_configs(self, configs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """合并配置"""
        merged = {}
        
        # 按优先级排序配置
        priority_order = ['default', 'development', 'production', 'testing']
        sorted_configs = sorted(configs.items(), 
                              key=lambda x: priority_order.index(x[0]) if x[0] in priority_order else 999)
        
        for config_name, config in sorted_configs:
            # 处理继承关系
            if 'extends' in config:
                parent_config = configs.get(config['extends'], {})
                merged.update(parent_config)
            
            # 移除继承字段
            config_copy = config.copy()
            if 'extends' in config_copy:
                del config_copy['extends']
            
            # 深度合并
            merged = self._deep_merge(merged, config_copy)
        
        return merged
    
    def _deep_merge(self, dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并字典"""
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result