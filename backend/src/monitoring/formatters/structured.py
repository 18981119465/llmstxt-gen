"""
格式化器模块

提供各种日志格式化器，包括结构化格式、彩色文本格式等。
"""

import logging
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime
import re


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""
    
    def __init__(self, fmt: str = None, datefmt: str = None, style: str = '%'):
        super().__init__(fmt, datefmt, style)
        self.default_fields = [
            'timestamp', 'level', 'service_name', 'message',
            'user_id', 'request_id', 'trace_id', 'span_id',
            'function_name', 'line_number', 'metadata'
        ]
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        # 创建结构化日志数据
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'service_name': record.name,
            'message': record.getMessage(),
            'function_name': record.funcName,
            'line_number': record.lineno,
            'thread_id': record.thread,
            'process_id': record.process
        }
        
        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
        
        # 添加自定义字段
        for field in self.default_fields:
            if hasattr(record, field):
                log_data[field] = getattr(record, field)
        
        # 添加所有额外属性
        for key, value in record.__dict__.items():
            if key not in ['args', 'msg', 'exc_info', 'exc_text', 'stack_info', 
                          'created', 'msecs', 'relativeCreated', 'levelname', 
                          'levelno', 'pathname', 'filename', 'module', 'lineno', 
                          'funcName', 'created', 'msecs', 'relativeCreated', 'thread', 
                          'threadName', 'processName', 'process', 'message', 'name']:
                if not key.startswith('_'):
                    log_data[key] = value
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""
    
    # ANSI 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
        'RESET': '\033[0m'      # 重置
    }
    
    def __init__(self, fmt: str = None, datefmt: str = None, style: str = '%'):
        if fmt is None:
            fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        if datefmt is None:
            datefmt = '%Y-%m-%d %H:%M:%S'
        super().__init__(fmt, datefmt, style)
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        # 获取基础格式化结果
        message = super().format(record)
        
        # 添加颜色
        level_color = self.COLORS.get(record.levelname, '')
        reset_color = self.COLORS['RESET']
        
        return f"{level_color}{message}{reset_color}"


class DetailedFormatter(logging.Formatter):
    """详细日志格式化器"""
    
    def __init__(self, fmt: str = None, datefmt: str = None, style: str = '%'):
        if fmt is None:
            fmt = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        if datefmt is None:
            datefmt = '%Y-%m-%d %H:%M:%S'
        super().__init__(fmt, datefmt, style)
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        # 获取基础格式化结果
        message = super().format(record)
        
        # 添加额外信息
        extra_info = []
        
        # 添加请求上下文
        if hasattr(record, 'request_id'):
            extra_info.append(f"request_id={record.request_id}")
        if hasattr(record, 'user_id'):
            extra_info.append(f"user_id={record.user_id}")
        if hasattr(record, 'trace_id'):
            extra_info.append(f"trace_id={record.trace_id}")
        
        # 添加性能信息
        if hasattr(record, 'execution_time'):
            extra_info.append(f"execution_time={record.execution_time:.3f}s")
        
        # 添加自定义元数据
        if hasattr(record, 'metadata') and record.metadata:
            metadata_str = ', '.join([f"{k}={v}" for k, v in record.metadata.items()])
            extra_info.append(f"metadata={metadata_str}")
        
        if extra_info:
            message = f"{message} [{', '.join(extra_info)}]"
        
        return message


class SimpleFormatter(logging.Formatter):
    """简单日志格式化器"""
    
    def __init__(self, fmt: str = None, datefmt: str = None, style: str = '%'):
        if fmt is None:
            fmt = '%(levelname)s - %(message)s'
        if datefmt is None:
            datefmt = '%H:%M:%S'
        super().__init__(fmt, datefmt, style)


class PrometheusFormatter(logging.Formatter):
    """Prometheus 指标格式化器"""
    
    def __init__(self, fmt: str = None, datefmt: str = None, style: str = '%'):
        super().__init__(fmt, datefmt, style)
        self.metrics = {}
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化为Prometheus指标格式"""
        # 基于日志级别创建指标
        metric_name = f"log_messages_total"
        labels = {
            'level': record.levelname,
            'service': record.name,
            'function': record.funcName
        }
        
        # 添加自定义标签
        if hasattr(record, 'request_id'):
            labels['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            labels['user_id'] = record.user_id
        
        # 构建Prometheus指标行
        label_str = ','.join([f'{k}="{v}"' for k, v in labels.items()])
        metric_line = f'{metric_name}{{{label_str}}} 1 {int(record.created * 1000)}'
        
        return metric_line


class FormatterFactory:
    """格式化器工厂"""
    
    @staticmethod
    def create_formatter(formatter_type: str, **kwargs) -> logging.Formatter:
        """创建格式化器"""
        formatter_type = formatter_type.lower()
        
        if formatter_type == 'json':
            return StructuredFormatter(**kwargs)
        elif formatter_type == 'colored':
            return ColoredFormatter(**kwargs)
        elif formatter_type == 'detailed':
            return DetailedFormatter(**kwargs)
        elif formatter_type == 'simple':
            return SimpleFormatter(**kwargs)
        elif formatter_type == 'prometheus':
            return PrometheusFormatter(**kwargs)
        else:
            return logging.Formatter(**kwargs)
    
    @staticmethod
    def get_available_formatters() -> list:
        """获取可用的格式化器类型"""
        return ['json', 'colored', 'detailed', 'simple', 'prometheus', 'default']