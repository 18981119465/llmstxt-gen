"""
日志过滤器模块

提供各种日志过滤功能，包括敏感信息过滤、请求ID过滤等。
"""

import logging
import re
import json
from typing import Dict, Any, List, Set, Optional
from dataclasses import dataclass


@dataclass
class FilterConfig:
    """过滤器配置"""
    sensitive_fields: List[str] = None
    sensitive_patterns: List[str] = None
    allowed_ips: List[str] = None
    blocked_ips: List[str] = None
    log_levels: List[str] = None
    min_level: str = None


class SensitiveDataFilter(logging.Filter):
    """敏感信息过滤器"""
    
    def __init__(self, sensitive_fields: List[str] = None, 
                 sensitive_patterns: List[str] = None):
        super().__init__()
        self.sensitive_fields = set(sensitive_fields or [
            'password', 'token', 'api_key', 'secret', 'credit_card',
            'ssn', 'phone', 'email', 'address', 'id_card'
        ])
        self.sensitive_patterns = sensitive_patterns or [
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # 信用卡号
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # 邮箱
            r'\b\d{11}\b',  # 手机号
            r'\b\d{17}[\dXx]\b',  # 身份证号
        ]
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) 
                                 for pattern in self.sensitive_patterns]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """过滤敏感信息"""
        # 处理消息
        if hasattr(record, 'msg'):
            record.msg = self._filter_sensitive_data(record.msg)
        
        # 处理参数
        if hasattr(record, 'args'):
            if isinstance(record.args, dict):
                record.args = self._filter_dict(record.args)
            elif isinstance(record.args, (list, tuple)):
                record.args = tuple(self._filter_sensitive_data(str(arg)) 
                                  for arg in record.args)
        
        # 处理自定义字段
        for field_name in dir(record):
            if field_name in self.sensitive_fields:
                value = getattr(record, field_name, None)
                if value:
                    setattr(record, field_name, self._mask_sensitive_data(str(value)))
        
        return True
    
    def _filter_sensitive_data(self, text: str) -> str:
        """过滤文本中的敏感信息"""
        if not isinstance(text, str):
            return text
        
        # 使用正则表达式匹配敏感信息
        for pattern in self.compiled_patterns:
            text = pattern.sub(self._mask_value, text)
        
        return text
    
    def _filter_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """过滤字典中的敏感信息"""
        if not isinstance(data, dict):
            return data
        
        filtered_dict = {}
        for key, value in data.items():
            if key in self.sensitive_fields:
                filtered_dict[key] = self._mask_sensitive_data(str(value))
            else:
                filtered_dict[key] = value
        
        return filtered_dict
    
    def _mask_sensitive_data(self, value: str) -> str:
        """脱敏敏感数据"""
        if len(value) <= 8:
            return '*' * len(value)
        else:
            return value[:2] + '*' * (len(value) - 4) + value[-2:]
    
    def _mask_value(self, match: re.Match) -> str:
        """脱敏匹配到的值"""
        value = match.group()
        return self._mask_sensitive_data(value)


class RequestIdFilter(logging.Filter):
    """请求ID过滤器"""
    
    def __init__(self):
        super().__init__()
        self.request_id = None
        self.trace_id = None
        self.span_id = None
    
    def filter(self, record: logging.LogRecord) -> bool:
        """添加请求ID到日志记录"""
        if self.request_id:
            record.request_id = self.request_id
        if self.trace_id:
            record.trace_id = self.trace_id
        if self.span_id:
            record.span_id = self.span_id
        
        return True
    
    def set_request_id(self, request_id: str, trace_id: str = None, span_id: str = None):
        """设置请求ID"""
        self.request_id = request_id
        self.trace_id = trace_id
        self.span_id = span_id
    
    def clear_request_id(self):
        """清除请求ID"""
        self.request_id = None
        self.trace_id = None
        self.span_id = None


class UserIdFilter(logging.Filter):
    """用户ID过滤器"""
    
    def __init__(self):
        super().__init__()
        self.user_id = None
    
    def filter(self, record: logging.LogRecord) -> bool:
        """添加用户ID到日志记录"""
        if self.user_id:
            record.user_id = self.user_id
        
        return True
    
    def set_user_id(self, user_id: str):
        """设置用户ID"""
        self.user_id = user_id
    
    def clear_user_id(self):
        """清除用户ID"""
        self.user_id = None


class ServiceNameFilter(logging.Filter):
    """服务名过滤器"""
    
    def __init__(self, service_name: str = None):
        super().__init__()
        self.service_name = service_name or 'unknown'
    
    def filter(self, record: logging.LogRecord) -> bool:
        """添加服务名到日志记录"""
        record.service_name = self.service_name
        return True
    
    def set_service_name(self, service_name: str):
        """设置服务名"""
        self.service_name = service_name


class LevelFilter(logging.Filter):
    """日志级别过滤器"""
    
    def __init__(self, min_level: str = 'INFO'):
        super().__init__()
        self.min_level = min_level.upper()
        self.level_map = {
            'DEBUG': 10,
            'INFO': 20,
            'WARNING': 30,
            'ERROR': 40,
            'CRITICAL': 50
        }
        self.min_level_value = self.level_map.get(self.min_level, 20)
    
    def filter(self, record: logging.LogRecord) -> bool:
        """过滤日志级别"""
        return record.levelno >= self.min_level_value


class PerformanceFilter(logging.Filter):
    """性能过滤器"""
    
    def __init__(self, threshold_ms: int = 1000):
        super().__init__()
        self.threshold_ms = threshold_ms
    
    def filter(self, record: logging.LogRecord) -> bool:
        """过滤性能日志"""
        # 如果有持续时间，只记录超过阈值的
        if hasattr(record, 'duration'):
            return record.duration >= self.threshold_ms
        
        return True


class SecurityFilter(logging.Filter):
    """安全过滤器"""
    
    def __init__(self, allowed_ips: List[str] = None, blocked_ips: List[str] = None):
        super().__init__()
        self.allowed_ips = set(allowed_ips or [])
        self.blocked_ips = set(blocked_ips or [])
    
    def filter(self, record: logging.LogRecord) -> bool:
        """过滤安全相关的日志"""
        # 检查IP白名单
        if self.allowed_ips and hasattr(record, 'client_ip'):
            if record.client_ip not in self.allowed_ips:
                return False
        
        # 检查IP黑名单
        if self.blocked_ips and hasattr(record, 'client_ip'):
            if record.client_ip in self.blocked_ips:
                return False
        
        return True


class HealthFilter(logging.Filter):
    """健康检查过滤器"""
    
    def __init__(self, include_health_checks: bool = False):
        super().__init__()
        self.include_health_checks = include_health_checks
    
    def filter(self, record: logging.LogRecord) -> bool:
        """过滤健康检查日志"""
        # 如果是健康检查相关的日志
        if hasattr(record, 'health_check'):
            return self.include_health_checks
        
        return True


class DuplicateFilter(logging.Filter):
    """重复日志过滤器"""
    
    def __init__(self, window_seconds: int = 60):
        super().__init__()
        self.window_seconds = window_seconds
        self.recent_messages = {}
    
    def filter(self, record: logging.LogRecord) -> bool:
        """过滤重复日志"""
        import time
        
        current_time = time.time()
        message_key = f"{record.levelname}:{record.name}:{record.getMessage()}"
        
        # 检查是否在时间窗口内
        if message_key in self.recent_messages:
            last_time = self.recent_messages[message_key]
            if current_time - last_time < self.window_seconds:
                return False
        
        # 更新记录
        self.recent_messages[message_key] = current_time
        
        # 清理过期记录
        expired_keys = [key for key, timestamp in self.recent_messages.items()
                       if current_time - timestamp > self.window_seconds]
        for key in expired_keys:
            del self.recent_messages[key]
        
        return True


class MetadataFilter(logging.Filter):
    """元数据过滤器"""
    
    def __init__(self, required_fields: List[str] = None):
        super().__init__()
        self.required_fields = set(required_fields or [])
    
    def filter(self, record: logging.LogRecord) -> bool:
        """过滤元数据"""
        # 检查必需字段
        if self.required_fields:
            for field in self.required_fields:
                if not hasattr(record, field):
                    return False
        
        return True


class FilterFactory:
    """过滤器工厂"""
    
    @staticmethod
    def create_filter(filter_type: str, **kwargs) -> logging.Filter:
        """创建过滤器"""
        filters = {
            'sensitive': SensitiveDataFilter,
            'request_id': RequestIdFilter,
            'user_id': UserIdFilter,
            'service_name': ServiceNameFilter,
            'level': LevelFilter,
            'performance': PerformanceFilter,
            'security': SecurityFilter,
            'health': HealthFilter,
            'duplicate': DuplicateFilter,
            'metadata': MetadataFilter
        }
        
        filter_class = filters.get(filter_type.lower())
        if not filter_class:
            raise ValueError(f"不支持的过滤器类型: {filter_type}")
        
        return filter_class(**kwargs)
    
    @staticmethod
    def get_available_filters() -> list:
        """获取可用的过滤器类型"""
        return ['sensitive', 'request_id', 'user_id', 'service_name', 
                'level', 'performance', 'security', 'health', 'duplicate', 'metadata']


class FilterChain:
    """过滤器链"""
    
    def __init__(self):
        self.filters = []
    
    def add_filter(self, filter_obj: logging.Filter):
        """添加过滤器"""
        self.filters.append(filter_obj)
    
    def remove_filter(self, filter_obj: logging.Filter):
        """移除过滤器"""
        if filter_obj in self.filters:
            self.filters.remove(filter_obj)
    
    def filter(self, record: logging.LogRecord) -> bool:
        """应用所有过滤器"""
        for filter_obj in self.filters:
            if not filter_obj.filter(record):
                return False
        return True
    
    def clear(self):
        """清空过滤器"""
        self.filters.clear()