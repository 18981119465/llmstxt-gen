"""
处理器模块

提供各种日志处理器，包括异步文件处理器、HTTP处理器等。
"""

import logging
import logging.handlers
import json
import time
import threading
import queue
import requests
import gzip
import io
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pathlib import Path
import os
import socket
import ssl


class AsyncFileHandler(logging.Handler):
    """异步文件处理器"""
    
    def __init__(self, filename: str, mode: str = 'a', 
                 encoding: str = 'utf-8', delay: bool = False,
                 maxBytes: int = 0, backupCount: int = 0):
        super().__init__()
        self.filename = filename
        self.mode = mode
        self.encoding = encoding
        self.delay = delay
        self.maxBytes = maxBytes
        self.backupCount = backupCount
        
        # 创建队列和线程
        self.queue = queue.Queue(maxsize=10000)
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()
        
        # 确保目录存在
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化文件
        if not delay:
            self._open_file()
    
    def _open_file(self):
        """打开文件"""
        self.stream = open(self.filename, self.mode, encoding=self.encoding)
    
    def _worker(self):
        """工作线程"""
        while True:
            try:
                # 获取日志记录
                record = self.queue.get(timeout=1)
                if record is None:  # 停止信号
                    break
                
                # 处理日志记录
                self._write_record(record)
                
                # 检查文件大小
                if self.maxBytes > 0:
                    self._check_file_size()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"AsyncFileHandler error: {e}")
    
    def _write_record(self, record: logging.LogRecord):
        """写入日志记录"""
        try:
            msg = self.format(record)
            self.stream.write(msg + self.terminator)
            self.stream.flush()
        except Exception as e:
            print(f"Error writing log record: {e}")
    
    def _check_file_size(self):
        """检查文件大小"""
        try:
            if self.stream.tell() >= self.maxBytes:
                self._do_rollover()
        except Exception as e:
            print(f"Error checking file size: {e}")
    
    def _do_rollover(self):
        """执行日志轮转"""
        if self.stream:
            self.stream.close()
            self.stream = None
        
        # 备份现有文件
        if self.backupCount > 0:
            for i in range(self.backupCount - 1, 0, -1):
                sfn = f"{self.filename}.{i}"
                dfn = f"{self.filename}.{i + 1}"
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            
            dfn = f"{self.filename}.1"
            if os.path.exists(dfn):
                os.remove(dfn)
            os.rename(self.filename, dfn)
        
        # 重新打开文件
        self._open_file()
    
    def emit(self, record: logging.LogRecord) -> None:
        """发送日志记录"""
        try:
            self.queue.put_nowait(record)
        except queue.Full:
            print("AsyncFileHandler queue is full, dropping log record")
    
    def close(self) -> None:
        """关闭处理器"""
        # 发送停止信号
        self.queue.put(None)
        
        # 等待线程结束
        if self.thread.is_alive():
            self.thread.join(timeout=5)
        
        # 关闭文件
        if hasattr(self, 'stream') and self.stream:
            self.stream.close()
        
        super().close()


class HTTPHandler(logging.Handler):
    """HTTP处理器"""
    
    def __init__(self, url: str, method: str = 'POST', 
                 timeout: int = 30, headers: Dict[str, str] = None,
                 compress: bool = False, max_retries: int = 3):
        super().__init__()
        self.url = url
        self.method = method.upper()
        self.timeout = timeout
        self.headers = headers or {'Content-Type': 'application/json'}
        self.compress = compress
        self.max_retries = max_retries
        
        # 创建会话
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def emit(self, record: logging.LogRecord) -> None:
        """发送日志记录"""
        try:
            # 格式化日志记录
            log_data = {
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno,
                'thread': record.thread,
                'process': record.process
            }
            
            # 添加异常信息
            if record.exc_info:
                log_data['exception'] = {
                    'type': record.exc_info[0].__name__,
                    'message': str(record.exc_info[1]),
                    'traceback': self.formatException(record.exc_info)
                }
            
            # 添加自定义字段
            for key, value in record.__dict__.items():
                if not key.startswith('_') and key not in ['args', 'msg', 'exc_info']:
                    log_data[key] = value
            
            # 发送数据
            self._send_data(log_data)
            
        except Exception as e:
            print(f"HTTPHandler error: {e}")
    
    def _send_data(self, data: Dict[str, Any]) -> None:
        """发送数据"""
        json_data = json.dumps(data, ensure_ascii=False, default=str)
        
        # 压缩数据
        if self.compress:
            buf = io.BytesIO()
            with gzip.GzipFile(fileobj=buf, mode='wb') as f:
                f.write(json_data.encode('utf-8'))
            payload = buf.getvalue()
            headers = {'Content-Encoding': 'gzip'}
        else:
            payload = json_data.encode('utf-8')
            headers = {}
        
        # 重试机制
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(
                    self.method,
                    self.url,
                    data=payload,
                    headers=headers,
                    timeout=self.timeout
                )
                
                if response.status_code < 400:
                    return
                else:
                    print(f"HTTP request failed: {response.status_code}")
                    
            except Exception as e:
                print(f"HTTP request attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
    
    def close(self) -> None:
        """关闭处理器"""
        self.session.close()
        super().close()


class SyslogHandler(logging.Handler):
    """系统日志处理器"""
    
    def __init__(self, host: str = 'localhost', port: int = 514,
                 facility: int = 1, socktype: socket.SocketKind = socket.SOCK_DGRAM):
        super().__init__()
        self.host = host
        self.port = port
        self.facility = facility
        self.socktype = socktype
        
        # 创建socket
        self.socket = socket.socket(socket.AF_INET, socktype)
        self.socket.settimeout(5)
        
        # 日志级别映射
        self.level_map = {
            logging.DEBUG: 7,
            logging.INFO: 6,
            logging.WARNING: 4,
            logging.ERROR: 3,
            logging.CRITICAL: 2
        }
    
    def emit(self, record: logging.LogRecord) -> None:
        """发送日志记录"""
        try:
            # 获取日志级别
            priority = self.facility * 8 + self.level_map.get(record.levelno, 6)
            
            # 格式化消息
            msg = self.format(record)
            
            # 构建syslog消息
            syslog_msg = f"<{priority}>{datetime.fromtimestamp(record.created).strftime('%b %d %H:%M:%S')} {socket.gethostname()} {record.name}: {msg}"
            
            # 发送消息
            if self.socktype == socket.SOCK_STREAM:
                self.socket.sendall(syslog_msg.encode('utf-8'))
            else:
                self.socket.sendto(syslog_msg.encode('utf-8'), (self.host, self.port))
                
        except Exception as e:
            print(f"SyslogHandler error: {e}")
    
    def close(self) -> None:
        """关闭处理器"""
        self.socket.close()
        super().close()


class RotatingFileHandler(logging.handlers.RotatingFileHandler):
    """轮转文件处理器（扩展）"""
    
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, 
                 encoding=None, delay=False, compress=False):
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)
        self.compress = compress
    
    def doRollover(self):
        """执行日志轮转"""
        if self.stream:
            self.stream.close()
            self.stream = None
        
        # 备份现有文件
        if self.backupCount > 0:
            for i in range(self.backupCount - 1, 0, -1):
                sfn = f"{self.baseFilename}.{i}.gz" if self.compress else f"{self.baseFilename}.{i}"
                dfn = f"{self.baseFilename}.{i + 1}.gz" if self.compress else f"{self.baseFilename}.{i + 1}"
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            
            dfn = f"{self.baseFilename}.1.gz" if self.compress else f"{self.baseFilename}.1"
            if os.path.exists(dfn):
                os.remove(dfn)
            
            # 压缩文件
            if self.compress:
                self._compress_file(self.baseFilename, dfn)
            else:
                os.rename(self.baseFilename, dfn)
        
        # 重新打开文件
        if not self.delay:
            self.stream = open(self.baseFilename, self.mode, encoding=self.encoding)
    
    def _compress_file(self, source: str, target: str):
        """压缩文件"""
        with open(source, 'rb') as f_in:
            with gzip.open(target, 'wb') as f_out:
                f_out.writelines(f_in)
        os.remove(source)


class TimedRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    """定时轮转文件处理器（扩展）"""
    
    def __init__(self, filename, when='h', interval=1, backupCount=0, 
                 encoding=None, delay=False, utc=False, compress=False):
        super().__init__(filename, when, interval, backupCount, encoding, delay, utc)
        self.compress = compress
    
    def doRollover(self):
        """执行日志轮转"""
        if self.stream:
            self.stream.close()
            self.stream = None
        
        # 获取轮转时间
        currentTime = int(self.computeRollover(self.rolloverAt))
        
        # 生成新文件名
        dfn = self.rotation_filename(self.getNewRolloverTime(currentTime))
        
        # 备份现有文件
        if os.path.exists(self.baseFilename):
            if self.compress:
                self._compress_file(self.baseFilename, dfn + '.gz')
            else:
                os.rename(self.baseFilename, dfn)
        
        # 重新打开文件
        if not self.delay:
            self.stream = open(self.baseFilename, self.mode, encoding=self.encoding)
        
        # 计算下次轮转时间
        self.rolloverAt = self.computeRollover(currentTime)
    
    def _compress_file(self, source: str, target: str):
        """压缩文件"""
        with open(source, 'rb') as f_in:
            with gzip.open(target, 'wb') as f_out:
                f_out.writelines(f_in)
        os.remove(source)


class QueueHandler(logging.Handler):
    """队列处理器"""
    
    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self.log_queue = log_queue
    
    def emit(self, record: logging.LogRecord) -> None:
        """发送日志记录到队列"""
        try:
            self.log_queue.put_nowait(record)
        except queue.Full:
            print("QueueHandler queue is full, dropping log record")


class MemoryHandler(logging.handlers.MemoryHandler):
    """内存处理器（扩展）"""
    
    def __init__(self, capacity=100, target=None, flushLevel=logging.ERROR):
        super().__init__(capacity, target, flushLevel)
        self.records = []
    
    def emit(self, record: logging.LogRecord) -> None:
        """发送日志记录"""
        self.records.append(record)
        
        # 检查是否需要刷新
        if (record.levelno >= self.flushLevel or 
            len(self.records) >= self.capacity):
            self.flush()
    
    def flush(self) -> None:
        """刷新日志记录"""
        if self.target:
            for record in self.records:
                self.target.handle(record)
        self.records.clear()
    
    def get_records(self) -> List[logging.LogRecord]:
        """获取内存中的日志记录"""
        return self.records.copy()
    
    def clear_records(self):
        """清除内存中的日志记录"""
        self.records.clear()


class HandlerFactory:
    """处理器工厂"""
    
    @staticmethod
    def create_handler(handler_type: str, **kwargs) -> logging.Handler:
        """创建处理器"""
        handler_type = handler_type.lower()
        
        if handler_type == 'async_file':
            return AsyncFileHandler(**kwargs)
        elif handler_type == 'http':
            return HTTPHandler(**kwargs)
        elif handler_type == 'syslog':
            return SyslogHandler(**kwargs)
        elif handler_type == 'rotating_file':
            return RotatingFileHandler(**kwargs)
        elif handler_type == 'timed_rotating_file':
            return TimedRotatingFileHandler(**kwargs)
        elif handler_type == 'queue':
            return QueueHandler(**kwargs)
        elif handler_type == 'memory':
            return MemoryHandler(**kwargs)
        else:
            # 使用标准库处理器
            if handler_type == 'stream':
                return logging.StreamHandler(**kwargs)
            elif handler_type == 'file':
                return logging.FileHandler(**kwargs)
            else:
                raise ValueError(f"Unknown handler type: {handler_type}")
    
    @staticmethod
    def get_available_handlers() -> list:
        """获取可用的处理器类型"""
        return [
            'async_file', 'http', 'syslog', 'rotating_file', 
            'timed_rotating_file', 'queue', 'memory', 
            'stream', 'file'
        ]