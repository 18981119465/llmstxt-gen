"""
过滤器模块

提供各种日志过滤器，包括敏感信息过滤、请求ID过滤等。
"""

import logging
import re
import json
from typing import Dict, Any, List, Optional, Set
import hashlib
import uuid


class SensitiveDataFilter(logging.Filter):
    """敏感信息过滤器"""
    
    def __init__(self, sensitive_fields: List[str] = None):
        super().__init__()
        self.sensitive_fields = sensitive_fields or [
            'password', 'token', 'api_key', 'secret', 'credit_card', 
            'ssn', 'phone', 'email', 'id_card', 'bank_account'
        ]
        self.patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """编译敏感信息匹配模式"""
        patterns = {}
        
        # 信用卡号模式
        patterns['credit_card'] = re.compile(
            r'\b(?:\d[ -]*?){13,16}\b'
        )
        
        # 邮箱模式
        patterns['email'] = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        
        # 手机号模式
        patterns['phone'] = re.compile(
            r'\b(?:\+?86)?1[3-9]\d{9}\b'
        )
        
        # 身份证号模式
        patterns['id_card'] = re.compile(
            r'\b\d{17}[\dXx]\b'
        )
        
        # 银行卡号模式
        patterns['bank_account'] = re.compile(
            r'\b\d{16,19}\b'
        )
        
        return patterns
    
    def filter(self, record: logging.LogRecord) -> bool:
        """过滤敏感信息"""
        # 过滤消息中的敏感信息
        record.msg = self._filter_sensitive_data(record.msg)
        
        # 过滤参数中的敏感信息
        if hasattr(record, 'args') and record.args:
            if isinstance(record.args, dict):
                filtered_args = {}
                for key, value in record.args.items():
                    if key.lower() in [field.lower() for field in self.sensitive_fields]:
                        filtered_args[key] = self._mask_value(value)
                    else:
                        filtered_args[key] = self._filter_sensitive_data(value)
                record.args = filtered_args
            elif isinstance(record.args, (list, tuple)):
                filtered_args = []
                for arg in record.args:
                    filtered_args.append(self._filter_sensitive_data(arg))
                record.args = tuple(filtered_args)
        
        # 过滤自定义属性中的敏感信息
        for attr_name in dir(record):
            if attr_name.startswith('_'):
                continue
            
            attr_value = getattr(record, attr_name)
            if attr_name.lower() in [field.lower() for field in self.sensitive_fields]:
                setattr(record, attr_name, self._mask_value(attr_value))
            elif isinstance(attr_value, str):
                setattr(record, attr_name, self._filter_sensitive_data(attr_value))
        
        return True
    
    def _filter_sensitive_data(self, data: Any) -> Any:
        """过滤敏感数据"""
        if isinstance(data, str):
            # 应用模式匹配
            filtered_text = data
            for pattern_name, pattern in self.patterns.items():
                filtered_text = pattern.sub(self._replacement_func, filtered_text)
            return filtered_text
        elif isinstance(data, dict):
            filtered_dict = {}
            for key, value in data.items():
                if key.lower() in [field.lower() for field in self.sensitive_fields]:
                    filtered_dict[key] = self._mask_value(value)
                else:
                    filtered_dict[key] = self._filter_sensitive_data(value)
            return filtered_dict
        elif isinstance(data, (list, tuple)):
            filtered_list = []
            for item in data:
                filtered_list.append(self._filter_sensitive_data(item))
            return type(data)(filtered_list)
        else:
            return data
    
    def _replacement_func(self, match) -> str:
        """敏感信息替换函数"""
        matched_text = match.group(0)
        return '*' * len(matched_text)
    
    def _mask_value(self, value: Any) -> str:
        """屏蔽敏感值"""
        if value is None:
            return '******'
        
        str_value = str(value)
        if len(str_value) <= 2:
            return '*' * len(str_value)
        elif len(str_value) <= 8:
            return str_value[:1] + '*' * (len(str_value) - 2) + str_value[-1:]
        else:
            return str_value[:2] + '*' * (len(str_value) - 4) + str_value[-2:]


class RequestIdFilter(logging.Filter):
    """请求ID过滤器"""
    
    def __init__(self, request_id_header: str = 'X-Request-ID'):
        super().__init__()
        self.request_id_header = request_id_header
        self._request_id = None
    
    def filter(self, record: logging.LogRecord) -> bool:
        """添加请求ID到日志记录"""
        if self._request_id:
            record.request_id = self._request_id
        elif hasattr(record, 'request_id'):
            # 保持现有的request_id
            pass
        else:
            # 生成新的request_id
            record.request_id = str(uuid.uuid4())
        
        return True
    
    def set_request_id(self, request_id: str):
        """设置当前请求ID"""
        self._request_id = request_id
    
    def clear_request_id(self):
        """清除当前请求ID"""
        self._request_id = None


class UserIdFilter(logging.Filter):
    """用户ID过滤器"""
    
    def __init__(self):
        super().__init__()
        self._user_id = None
    
    def filter(self, record: logging.LogRecord) -> bool:
        """添加用户ID到日志记录"""
        if self._user_id:
            record.user_id = self._user_id
        elif hasattr(record, 'user_id'):
            # 保持现有的user_id
            pass
        else:
            # 设置默认值
            record.user_id = 'anonymous'
        
        return True
    
    def set_user_id(self, user_id: str):
        """设置当前用户ID"""
        self._user_id = user_id
    
    def clear_user_id(self):
        """清除当前用户ID"""
        self._user_id = None


class ServiceNameFilter(logging.Filter):
    """服务名过滤器"""
    
    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name
    
    def filter(self, record: logging.LogRecord) -> bool:
        """添加服务名到日志记录"""
        record.service_name = self.service_name
        return True


class TraceIdFilter(logging.Filter):
    """追踪ID过滤器"""
    
    def __init__(self):
        super().__init__()
        self._trace_id = None
        self._span_id = None
    
    def filter(self, record: logging.LogRecord) -> bool:
        """添加追踪ID到日志记录"""
        if self._trace_id:
            record.trace_id = self._trace_id
        elif hasattr(record, 'trace_id'):
            # 保持现有的trace_id
            pass
        else:
            # 生成新的trace_id
            record.trace_id = str(uuid.uuid4())
        
        if self._span_id:
            record.span_id = self._span_id
        elif hasattr(record, 'span_id'):
            # 保持现有的span_id
            pass
        else:
            # 生成新的span_id
            record.span_id = str(uuid.uuid4())[:8]
        
        return True
    
    def set_trace_context(self, trace_id: str, span_id: str = None):
        """设置追踪上下文"""
        self._trace_id = trace_id
        self._span_id = span_id
    
    def clear_trace_context(self):
        """清除追踪上下文"""
        self._trace_id = None
        self._span_id = None


class LevelFilter(logging.Filter):
    """日志级别过滤器"""
    
    def __init__(self, min_level: str = 'DEBUG', max_level: str = 'CRITICAL'):
        super().__init__()
        self.min_level = getattr(logging, min_level.upper(), logging.DEBUG)
        self.max_level = getattr(logging, max_level.upper(), logging.CRITICAL)
    
    def filter(self, record: logging.LogRecord) -> bool:
        """过滤日志级别"""
        return self.min_level <= record.levelno <= self.max_level


class PatternFilter(logging.Filter):
    """模式过滤器"""
    
    def __init__(self, pattern: str, exclude: bool = False):
        super().__init__()
        self.pattern = re.compile(pattern)
        self.exclude = exclude
    
    def filter(self, record: logging.LogRecord) -> bool:
        """基于模式过滤"""
        message = record.getMessage()
        match = self.pattern.search(message)
        
        if self.exclude:
            return not match
        else:
            return bool(match)


class FilterChain(logging.Filter):
    """过滤器链"""
    
    def __init__(self):
        super().__init__()
        self.filters = []
    
    def add_filter(self, filter_instance: logging.Filter):
        """添加过滤器"""
        self.filters.append(filter_instance)
    
    def remove_filter(self, filter_instance: logging.Filter):
        """移除过滤器"""
        if filter_instance in self.filters:
            self.filters.remove(filter_instance)
    
    def clear_filters(self):
        """清除所有过滤器"""
        self.filters.clear()
    
    def filter(self, record: logging.LogRecord) -> bool:
        """应用所有过滤器"""
        for filter_instance in self.filters:
            if not filter_instance.filter(record):
                return False
        return True


class MetadataFilter(logging.Filter):
    """元数据过滤器"""
    
    def __init__(self, metadata: Dict[str, Any] = None):
        super().__init__()
        self.metadata = metadata or {}
    
    def filter(self, record: logging.LogRecord) -> bool:
        """添加元数据到日志记录"""
        if not hasattr(record, 'metadata'):
            record.metadata = {}
        
        # 合并元数据
        record.metadata.update(self.metadata)
        
        return True
    
    def add_metadata(self, key: str, value: Any):
        """添加元数据"""
        self.metadata[key] = value
    
    def remove_metadata(self, key: str):
        """移除元数据"""
        if key in self.metadata:
            del self.metadata[key]
    
    def clear_metadata(self):
        """清除所有元数据"""
        self.metadata.clear()