"""
日志格式化器模块

提供多种日志格式化功能，包括JSON、结构化、彩色等格式。
"""

import json
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
import sys


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""
    
    def __init__(self, fmt: str = None, datefmt: str = None, style: str = '%'):
        super().__init__(fmt, datefmt, style)
        self._fields = [
            'timestamp', 'level', 'service_name', 'message',
            'user_id', 'request_id', 'trace_id', 'span_id',
            'function_name', 'line_number', 'metadata'
        ]
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        # 基础字段
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger_name': record.name,
            'message': record.getMessage(),
            'function_name': record.funcName,
            'line_number': record.lineno,
            'module': record.module,
            'thread_id': record.thread,
            'process_id': record.process
        }
        
        # 添加异常信息
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # 添加堆栈跟踪
        if record.stack_info:
            log_entry['stack_info'] = record.stack_info
        
        # 添加自定义字段
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        
        if hasattr(record, 'trace_id'):
            log_entry['trace_id'] = record.trace_id
        
        if hasattr(record, 'span_id'):
            log_entry['span_id'] = record.span_id
        
        if hasattr(record, 'service_name'):
            log_entry['service_name'] = record.service_name
        
        # 添加元数据
        if hasattr(record, 'metadata'):
            log_entry['metadata'] = record.metadata
        
        # 添加性能指标
        if hasattr(record, 'duration'):
            log_entry['duration_ms'] = record.duration
        
        # 添加请求信息
        if hasattr(record, 'request_method'):
            log_entry['request_method'] = record.request_method
            log_entry['request_path'] = record.request_path
            log_entry['request_status'] = record.request_status
        
        # 添加数据库信息
        if hasattr(record, 'database_operation'):
            log_entry['database_operation'] = record.database_operation
            log_entry['database_table'] = record.database_table
            log_entry['database_duration'] = record.database_duration
        
        return json.dumps(log_entry, ensure_ascii=False, default=str)


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""
    
    # 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
        'RESET': '\033[0m'      # 重置
    }
    
    def __init__(self, fmt: str = None, datefmt: str = None, style: str = '%'):
        super().__init__(fmt, datefmt, style)
        self.fmt = fmt or '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        self.datefmt = datefmt or '%Y-%m-%d %H:%M:%S'
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        # 获取颜色代码
        color = self.COLORS.get(record.levelname, '')
        reset = self.COLORS['RESET']
        
        # 应用颜色
        record.levelname = f"{color}{record.levelname}{reset}"
        
        # 格式化消息
        formatted = super().format(record)
        
        return formatted


class CompactFormatter(logging.Formatter):
    """紧凑格式化器"""
    
    def __init__(self, fmt: str = None, datefmt: str = None, style: str = '%'):
        super().__init__(fmt, datefmt, style)
        self.fmt = fmt or '%(asctime)s [%(levelname).1s] %(name)s: %(message)s'
        self.datefmt = datefmt or '%H:%M:%S'
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        return super().format(record)


class DetailedFormatter(logging.Formatter):
    """详细格式化器"""
    
    def __init__(self, fmt: str = None, datefmt: str = None, style: str = '%'):
        super().__init__(fmt, datefmt, style)
        self.fmt = fmt or (
            '%(asctime)s - %(name)s - %(levelname)s - '
            '%(funcName)s:%(lineno)d - %(message)s'
        )
        self.datefmt = datefmt or '%Y-%m-%d %H:%M:%S'
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        formatted = super().format(record)
        
        # 添加异常信息
        if record.exc_info:
            formatted += '\n' + ''.join(traceback.format_exception(*record.exc_info))
        
        # 添加堆栈跟踪
        if record.stack_info:
            formatted += '\n' + record.stack_info
        
        return formatted


class PrometheusFormatter(logging.Formatter):
    """Prometheus指标格式化器"""
    
    def __init__(self, fmt: str = None, datefmt: str = None, style: str = '%'):
        super().__init__(fmt, datefmt, style)
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为Prometheus指标"""
        # 将日志转换为Prometheus指标
        metrics = []
        
        # 基础指标
        timestamp = int(record.created * 1000)  # 毫秒时间戳
        
        # 日志计数指标
        metrics.append(f'log_count_total{{level="{record.levelname}",logger="{record.name}"}} 1 {timestamp}')
        
        # 如果有持续时间，添加性能指标
        if hasattr(record, 'duration'):
            metrics.append(f'log_duration_seconds{{level="{record.levelname}",logger="{record.name}"}} {record.duration} {timestamp}')
        
        # 如果有请求状态，添加HTTP指标
        if hasattr(record, 'request_status'):
            metrics.append(f'http_requests_total{{status="{record.request_status}",method="{record.request_method}"}} 1 {timestamp}')
        
        return '\n'.join(metrics)


class ELKFormatter(logging.Formatter):
    """ELK Stack格式化器"""
    
    def __init__(self, fmt: str = None, datefmt: str = None, style: str = '%'):
        super().__init__(fmt, datefmt, style)
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为ELK格式"""
        elk_entry = {
            '@timestamp': datetime.fromtimestamp(record.created).isoformat() + 'Z',
            '@version': '1',
            'message': record.getMessage(),
            'logger_name': record.name,
            'level': record.levelname,
            'thread_name': record.threadName,
            'level_value': record.levelno,
            'logger': record.name
        }
        
        # 添加源信息
        elk_entry['source'] = {
            'file': {
                'name': record.pathname,
                'line': record.lineno
            },
            'function': record.funcName,
            'module': record.module
        }
        
        # 添加进程信息
        elk_entry['process'] = {
            'id': record.process,
            'name': record.processName
        }
        
        # 添加线程信息
        elk_entry['thread'] = {
            'id': record.thread,
            'name': record.threadName
        }
        
        # 添加异常信息
        if record.exc_info:
            elk_entry['exception'] = {
                'class': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'stacktrace': traceback.format_exception(*record.exc_info)
            }
        
        # 添加自定义字段
        for key, value in record.__dict__.items():
            if key not in ['args', 'exc_info', 'exc_text', 'msg', 'pathname', 'lineno', 
                          'funcName', 'created', 'msecs', 'relativeCreated', 'thread',
                          'threadName', 'processName', 'process', 'getMessage', 'levelname',
                          'levelno', 'module', 'name', 'pathname', 'stack_info']:
                elk_entry[key] = value
        
        return json.dumps(elk_entry, ensure_ascii=False, default=str)


class FormatterFactory:
    """格式化器工厂"""
    
    @staticmethod
    def create_formatter(formatter_type: str, **kwargs) -> logging.Formatter:
        """创建格式化器"""
        formatters = {
            'structured': StructuredFormatter,
            'colored': ColoredFormatter,
            'compact': CompactFormatter,
            'detailed': DetailedFormatter,
            'prometheus': PrometheusFormatter,
            'elk': ELKFormatter
        }
        
        formatter_class = formatters.get(formatter_type.lower())
        if not formatter_class:
            raise ValueError(f"不支持的格式化器类型: {formatter_type}")
        
        return formatter_class(**kwargs)
    
    @staticmethod
    def get_available_formatters() -> list:
        """获取可用的格式化器类型"""
        return ['structured', 'colored', 'compact', 'detailed', 'prometheus', 'elk']