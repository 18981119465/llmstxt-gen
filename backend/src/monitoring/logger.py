"""
日志管理器模块

提供统一的日志记录接口，支持结构化日志、多种输出方式和热重载。
"""

import logging
import logging.config
import os
import sys
import yaml
import time
import threading
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from contextlib import contextmanager
from functools import wraps
import json

from .config import get_monitoring_config, MonitoringConfig
from .formatters import StructuredFormatter, ColoredFormatter, FormatterFactory
from .filters import SensitiveDataFilter, RequestIdFilter, UserIdFilter, ServiceNameFilter, FilterChain
from .handlers import AsyncFileHandler, HandlerFactory


class Logger:
    """日志管理器"""
    
    def __init__(self, name: str, config: Optional[MonitoringConfig] = None):
        self.name = name
        self.config = config or get_monitoring_config()
        self._logger = logging.getLogger(name)
        self._filters = FilterChain()
        self._setup_logger()
        
        # 请求上下文
        self._request_context = threading.local()
    
    def _setup_logger(self):
        """设置日志记录器"""
        # 清除现有处理器
        self._logger.handlers.clear()
        
        # 设置日志级别
        level = getattr(logging, self.config.logging.level.upper(), logging.INFO)
        self._logger.setLevel(level)
        
        # 创建格式化器
        formatter = self._create_formatter()
        
        # 创建处理器
        handlers = self._create_handlers(formatter)
        
        # 添加处理器到日志记录器
        for handler in handlers:
            self._logger.addHandler(handler)
        
        # 添加过滤器
        self._setup_filters()
        
        # 防止日志传播到父记录器
        self._logger.propagate = False
    
    def _create_formatter(self) -> logging.Formatter:
        """创建格式化器"""
        format_type = self.config.logging.format.lower()
        
        if format_type == 'json':
            return StructuredFormatter()
        elif format_type == 'text':
            return ColoredFormatter()
        else:
            return FormatterFactory.create_formatter(format_type)
    
    def _create_handlers(self, formatter: logging.Formatter) -> List[logging.Handler]:
        """创建处理器"""
        handlers = []
        output_type = self.config.logging.output.lower()
        
        # 控制台处理器
        if output_type in ['console', 'both']:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            handlers.append(console_handler)
        
        # 文件处理器
        if output_type in ['file', 'both']:
            # 确保日志目录存在
            log_dir = Path(self.config.logging.file_path).parent
            log_dir.mkdir(parents=True, exist_ok=True)
            
            file_handler = AsyncFileHandler(
                filename=self.config.logging.file_path,
                maxBytes=self._parse_size(self.config.logging.max_size),
                backupCount=self.config.logging.backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)
        
        return handlers
    
    def _setup_filters(self):
        """设置过滤器"""
        # 敏感信息过滤器
        sensitive_filter = SensitiveDataFilter(
            sensitive_fields=self.config.logging.sensitive_fields
        )
        self._filters.add_filter(sensitive_filter)
        
        # 服务名过滤器
        service_filter = ServiceNameFilter(self.name)
        self._filters.add_filter(service_filter)
        
        # 添加过滤器到日志记录器
        self._logger.addFilter(self._filters)
    
    def _parse_size(self, size_str: str) -> int:
        """解析大小字符串"""
        size_str = size_str.upper()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    def _log(self, level: int, message: str, **kwargs):
        """记录日志"""
        # 创建日志记录
        record = self._logger.makeRecord(
            self.name, level, "(unknown file)", 0, message, (), None
        )
        
        # 添加自定义字段
        for key, value in kwargs.items():
            setattr(record, key, value)
        
        # 添加请求上下文
        if hasattr(self._request_context, 'request_id'):
            record.request_id = self._request_context.request_id
        if hasattr(self._request_context, 'user_id'):
            record.user_id = self._request_context.user_id
        if hasattr(self._request_context, 'trace_id'):
            record.trace_id = self._request_context.trace_id
        if hasattr(self._request_context, 'span_id'):
            record.span_id = self._request_context.span_id
        
        # 处理日志记录
        self._logger.handle(record)
    
    def debug(self, message: str, **kwargs):
        """记录调试日志"""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """记录信息日志"""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """记录警告日志"""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """记录错误日志"""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """记录严重错误日志"""
        self._log(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """记录异常日志"""
        self._log(logging.ERROR, message, exc_info=True, **kwargs)
    
    # 请求上下文管理
    def set_request_context(self, request_id: str = None, user_id: str = None, 
                           trace_id: str = None, span_id: str = None):
        """设置请求上下文"""
        if request_id:
            self._request_context.request_id = request_id
        if user_id:
            self._request_context.user_id = user_id
        if trace_id:
            self._request_context.trace_id = trace_id
        if span_id:
            self._request_context.span_id = span_id
    
    def clear_request_context(self):
        """清除请求上下文"""
        if hasattr(self._request_context, 'request_id'):
            delattr(self._request_context, 'request_id')
        if hasattr(self._request_context, 'user_id'):
            delattr(self._request_context, 'user_id')
        if hasattr(self._request_context, 'trace_id'):
            delattr(self._request_context, 'trace_id')
        if hasattr(self._request_context, 'span_id'):
            delattr(self._request_context, 'span_id')
    
    @contextmanager
    def request_context(self, request_id: str = None, user_id: str = None,
                        trace_id: str = None, span_id: str = None):
        """请求上下文管理器"""
        old_context = {}
        
        # 保存旧上下文
        for attr in ['request_id', 'user_id', 'trace_id', 'span_id']:
            if hasattr(self._request_context, attr):
                old_context[attr] = getattr(self._request_context, attr)
        
        # 设置新上下文
        self.set_request_context(request_id, user_id, trace_id, span_id)
        
        try:
            yield
        finally:
            # 恢复旧上下文
            for attr in ['request_id', 'user_id', 'trace_id', 'span_id']:
                if hasattr(self._request_context, attr):
                    delattr(self._request_context, attr)
                if attr in old_context:
                    setattr(self._request_context, attr, old_context[attr])
    
    def reload_config(self):
        """重新加载配置"""
        self.config = get_monitoring_config()
        self._setup_logger()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取日志统计信息"""
        stats = {
            'name': self.name,
            'level': self._logger.level,
            'handlers_count': len(self._logger.handlers),
            'filters_count': len(self._filters.filters),
            'effective_level': self._logger.getEffectiveLevel()
        }
        return stats


class StructuredLogger(Logger):
    """结构化日志记录器"""
    
    def __init__(self, name: str, config: Optional[MonitoringConfig] = None):
        super().__init__(name, config)
    
    def log_structured(self, level: str, event: str, **kwargs):
        """记录结构化日志"""
        # 确保基础字段存在
        structured_data = {
            'event': event,
            'timestamp': time.time(),
            'service_name': self.name
        }
        
        # 合并其他字段
        structured_data.update(kwargs)
        
        # 记录日志
        message = json.dumps(structured_data, ensure_ascii=False, default=str)
        
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        log_level = level_map.get(level.upper(), logging.INFO)
        self._log(log_level, message, **structured_data)
    
    def log_event(self, event: str, **kwargs):
        """记录事件日志"""
        self.log_structured('INFO', event, **kwargs)
    
    def log_metric(self, metric_name: str, value: float, **kwargs):
        """记录指标日志"""
        self.log_structured('INFO', 'metric', 
                          metric_name=metric_name, value=value, **kwargs)
    
    def log_audit(self, action: str, resource: str, **kwargs):
        """记录审计日志"""
        self.log_structured('INFO', 'audit',
                          action=action, resource=resource, **kwargs)
    
    def log_security(self, event: str, **kwargs):
        """记录安全日志"""
        self.log_structured('WARNING', 'security',
                          event=event, **kwargs)


# 全局日志记录器缓存
_loggers: Dict[str, Logger] = {}


def get_logger(name: str = None, config: Optional[MonitoringConfig] = None) -> Logger:
    """获取日志记录器"""
    if name is None:
        name = 'app'
    
    if name not in _loggers:
        _loggers[name] = Logger(name, config)
    
    return _loggers[name]


def get_structured_logger(name: str = None, config: Optional[MonitoringConfig] = None) -> StructuredLogger:
    """获取结构化日志记录器"""
    if name is None:
        name = 'app'
    
    if name not in _loggers or not isinstance(_loggers[name], StructuredLogger):
        _loggers[name] = StructuredLogger(name, config)
    
    return _loggers[name]


def setup_logging(config_file: str = None):
    """设置日志系统"""
    if config_file:
        # 从配置文件设置
        with open(config_file, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)
        logging.config.dictConfig(config_dict)
    else:
        # 使用默认配置
        config = get_monitoring_config()
        root_logger = get_logger('root', config)
        logging.root = root_logger._logger


def configure_logging(config: MonitoringConfig):
    """配置日志系统"""
    # 清除现有日志记录器
    _loggers.clear()
    
    # 设置根日志记录器
    root_logger = get_logger('root', config)
    logging.root = root_logger._logger


# 装饰器
def log_execution_time(logger_name: str = None):
    """记录执行时间的装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name or func.__module__)
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(f"函数 {func.__name__} 执行完成", 
                          function=func.__name__, 
                          execution_time=execution_time)
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"函数 {func.__name__} 执行失败", 
                           function=func.__name__, 
                           execution_time=execution_time,
                           error=str(e))
                raise
        return wrapper
    return decorator


def log_function_calls(logger_name: str = None):
    """记录函数调用的装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name or func.__module__)
            logger.info(f"调用函数 {func.__name__}", 
                      function=func.__name__, 
                      args=args, 
                      kwargs=kwargs)
            
            try:
                result = func(*args, **kwargs)
                logger.info(f"函数 {func.__name__} 返回结果", 
                          function=func.__name__, 
                          result_type=type(result).__name__)
                return result
            except Exception as e:
                logger.error(f"函数 {func.__name__} 抛出异常", 
                           function=func.__name__, 
                           exception=str(e))
                raise
        return wrapper
    return decorator


def log_errors(logger_name: str = None):
    """记录错误的装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name or func.__module__)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.exception(f"函数 {func.__name__} 发生异常", 
                               function=func.__name__, 
                               exception=str(e))
                raise
        return wrapper
    return decorator


# 便捷函数
def log_debug(message: str, **kwargs):
    """记录调试日志"""
    get_logger().debug(message, **kwargs)


def log_info(message: str, **kwargs):
    """记录信息日志"""
    get_logger().info(message, **kwargs)


def log_warning(message: str, **kwargs):
    """记录警告日志"""
    get_logger().warning(message, **kwargs)


def log_error(message: str, **kwargs):
    """记录错误日志"""
    get_logger().error(message, **kwargs)


def log_critical(message: str, **kwargs):
    """记录严重错误日志"""
    get_logger().critical(message, **kwargs)


def log_exception(message: str, **kwargs):
    """记录异常日志"""
    get_logger().exception(message, **kwargs)