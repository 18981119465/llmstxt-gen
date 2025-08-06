"""
配置优先级和合并策略
"""

import os
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import copy
import re


class ConfigPriority:
    """配置优先级管理"""
    
    # 配置源优先级（从低到高）
    PRIORITY_LEVELS = {
        'default': 0,      # 默认配置
        'template': 1,     # 模板配置
        'preset': 2,       # 预设配置
        'environment': 3,  # 环境配置
        'override': 4,     # 覆盖配置
        'env_var': 5,      # 环境变量
        'runtime': 6       # 运行时配置
    }
    
    def __init__(self):
        self.config_sources = {}
        self.merged_config = {}
    
    def add_config_source(self, name: str, config: Dict[str, Any], source_type: str):
        """添加配置源"""
        if source_type not in self.PRIORITY_LEVELS:
            raise ValueError(f"不支持的配置源类型: {source_type}")
        
        self.config_sources[name] = {
            'config': config,
            'type': source_type,
            'priority': self.PRIORITY_LEVELS[source_type]
        }
    
    def merge_configs(self) -> Dict[str, Any]:
        """合并所有配置源"""
        # 按优先级排序
        sorted_sources = sorted(
            self.config_sources.items(),
            key=lambda x: x[1]['priority']
        )
        
        merged = {}
        
        for name, source_info in sorted_sources:
            config = source_info['config']
            source_type = source_info['type']
            
            # 特殊处理环境变量
            if source_type == 'env_var':
                config = self._process_env_vars(config)
            
            # 深度合并
            merged = self._deep_merge(merged, config)
        
        self.merged_config = merged
        return merged
    
    def _process_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """处理环境变量"""
        processed = copy.deepcopy(config)
        
        def process_value(value):
            if isinstance(value, str):
                # 替换环境变量引用
                def replace_env_var(match):
                    env_var = match.group(1)
                    default_value = match.group(2) if match.group(2) else ""
                    return os.getenv(env_var, default_value)
                
                # 支持 ${VAR} 和 ${VAR:default} 格式
                value = re.sub(r'\$\{([^}]+)(?::([^}]*))?\}', replace_env_var, value)
            return value
        
        def process_dict(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, (dict, list)):
                        process_dict(value)
                    else:
                        obj[key] = process_value(value)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    if isinstance(item, (dict, list)):
                        process_dict(item)
                    else:
                        obj[i] = process_value(item)
        
        process_dict(processed)
        return processed
    
    def _deep_merge(self, dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并字典"""
        result = copy.deepcopy(dict1)
        
        for key, value in dict2.items():
            if key in result:
                if isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = self._deep_merge(result[key], value)
                elif isinstance(result[key], list) and isinstance(value, list):
                    # 对于列表，根据策略决定是追加还是替换
                    result[key] = self._merge_lists(result[key], value)
                else:
                    # 高优先级覆盖低优先级
                    result[key] = value
            else:
                result[key] = value
        
        return result
    
    def _merge_lists(self, list1: List[Any], list2: List[Any]) -> List[Any]:
        """合并列表"""
        # 对于配置中的列表，通常使用替换策略
        return list2.copy()
    
    def get_config_value(self, key_path: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key_path.split('.')
        value = self.merged_config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_config_source(self, key_path: str) -> Optional[str]:
        """获取配置值的来源"""
        keys = key_path.split('.')
        
        # 按优先级从高到低检查
        for source_name, source_info in sorted(
            self.config_sources.items(),
            key=lambda x: -x[1]['priority']
        ):
            config = source_info['config']
            value = config
            
            try:
                for key in keys:
                    if isinstance(value, dict) and key in value:
                        value = value[key]
                    else:
                        break
                else:
                    return source_name
            except (KeyError, TypeError):
                continue
        
        return None


class ConfigStrategy:
    """配置策略管理"""
    
    def __init__(self):
        self.strategies = {
            'merge': self._merge_strategy,
            'override': self._override_strategy,
            'append': self._append_strategy,
            'unique': self._unique_strategy
        }
    
    def apply_strategy(self, strategy_name: str, target: Any, source: Any) -> Any:
        """应用配置策略"""
        if strategy_name not in self.strategies:
            raise ValueError(f"不支持的策略: {strategy_name}")
        
        return self.strategies[strategy_name](target, source)
    
    def _merge_strategy(self, target: Any, source: Any) -> Any:
        """合并策略"""
        if isinstance(target, dict) and isinstance(source, dict):
            result = target.copy()
            for key, value in source.items():
                if key in result:
                    result[key] = self._merge_strategy(result[key], value)
                else:
                    result[key] = value
            return result
        elif isinstance(target, list) and isinstance(source, list):
            return target + source
        else:
            return source
    
    def _override_strategy(self, target: Any, source: Any) -> Any:
        """覆盖策略"""
        return source
    
    def _append_strategy(self, target: Any, source: Any) -> Any:
        """追加策略"""
        if isinstance(target, list) and isinstance(source, list):
            return target + source
        elif isinstance(target, list):
            return target + [source]
        else:
            return source
    
    def _unique_strategy(self, target: Any, source: Any) -> Any:
        """唯一策略"""
        if isinstance(target, list) and isinstance(source, list):
            combined = target + source
            # 保持顺序去重
            seen = set()
            result = []
            for item in combined:
                if item not in seen:
                    seen.add(item)
                    result.append(item)
            return result
        else:
            return source


class ConfigMerger:
    """配置合并器"""
    
    def __init__(self):
        self.priority = ConfigPriority()
        self.strategy = ConfigStrategy()
        self.merge_rules = self._get_default_merge_rules()
    
    def _get_default_merge_rules(self) -> Dict[str, str]:
        """获取默认合并规则"""
        return {
            'system': 'merge',
            'database': 'merge',
            'redis': 'merge',
            'api': 'merge',
            'ai_service': 'merge',
            'document_processor': 'merge',
            'web_crawler': 'merge',
            'logging': 'merge',
            'monitoring': 'merge',
            'security': 'merge',
            'storage': 'merge',
            'api.cors_origins': 'unique',
            'api.cors_methods': 'unique',
            'api.cors_headers': 'unique',
            'document_processor.supported_formats': 'unique',
            'storage.allowed_extensions': 'unique'
        }
    
    def merge_with_strategy(self, configs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """使用策略合并配置"""
        # 添加配置源
        for config_name, config in configs.items():
            source_type = self._determine_source_type(config_name)
            self.priority.add_config_source(config_name, config, source_type)
        
        # 按规则合并
        merged = {}
        sorted_configs = sorted(
            configs.items(),
            key=lambda x: self.priority.PRIORITY_LEVELS.get(
                self._determine_source_type(x[0]), 0
            )
        )
        
        for config_name, config in sorted_configs:
            merged = self._merge_with_rules(merged, config)
        
        return merged
    
    def _determine_source_type(self, config_name: str) -> str:
        """确定配置源类型"""
        if config_name == 'default':
            return 'default'
        elif config_name in ['development', 'production', 'testing']:
            return 'environment'
        elif config_name.endswith('.template'):
            return 'template'
        elif config_name.endswith('.preset'):
            return 'preset'
        elif config_name == 'override':
            return 'override'
        else:
            return 'environment'
    
    def _merge_with_rules(self, target: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
        """根据规则合并配置"""
        result = target.copy()
        
        for key, value in source.items():
            # 跳过内部字段和特殊字段
            if key.startswith('_') or key in ['extends']:
                continue
                
            if key in result:
                # 查找匹配的规则
                strategy = self._find_merge_strategy(key)
                result[key] = self.strategy.apply_strategy(strategy, result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _find_merge_strategy(self, key: str) -> str:
        """查找合并策略"""
        for pattern, strategy in self.merge_rules.items():
            if self._match_pattern(key, pattern):
                return strategy
        return 'override'  # 默认策略
    
    def _match_pattern(self, key: str, pattern: str) -> bool:
        """匹配模式"""
        if pattern.endswith('*'):
            return key.startswith(pattern[:-1])
        return key == pattern
    
    def add_merge_rule(self, pattern: str, strategy: str):
        """添加合并规则"""
        if strategy not in self.strategy.strategies:
            raise ValueError(f"不支持的策略: {strategy}")
        self.merge_rules[pattern] = strategy