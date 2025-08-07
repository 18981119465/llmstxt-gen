"""
日志处理器模块

提供各种日志处理器，包括文件、网络、数据库等输出方式。
"""

import logging
import json
import requests
import time
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import queue
import os


class AsyncFileHandler(RotatingFileHandler):
    """异步文件处理器"""
    
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, encoding=None, delay=False):
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)
        self.queue = queue.Queue()
        self.running = False
        self.thread = None
        self.start()
    
    def start(self):
        """启动异步处理线程"""
        self.running = True
        self.thread = threading.Thread(target=self._process_queue, daemon=True)
        self.thread.start()
    
    def _process_queue(self):
        """处理队列中的日志记录"""
        while self.running:
            try:
                record = self.queue.get(timeout=1)
                if record is None:
                    break
                super().emit(record)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"异步文件处理器错误: {e}")
    
    def emit(self, record):
        """发送日志记录到队列"""
        try:
            self.queue.put(record)
        except Exception as e:
            print(f"异步文件处理器发送错误: {e}")
    
    def close(self):
        """关闭处理器"""
        self.running = False
        if self.thread:
            self.thread.join()
        super().close()


class HTTPHandler(logging.Handler):
    """HTTP处理器"""
    
    def __init__(self, url: str, method: str = 'POST', 
                 headers: Dict[str, str] = None, timeout: int = 5,
                 retries: int = 3, batch_size: int = 10):
        super().__init__()
        self.url = url
        self.method = method.upper()
        self.headers = headers or {'Content-Type': 'application/json'}
        self.timeout = timeout
        self.retries = retries
        self.batch_size = batch_size
        self.batch = []
        self.lock = threading.Lock()
        self.session = requests.Session()
        
        # 启动批处理线程
        self.start_batch_processor()
    
    def start_batch_processor(self):
        """启动批处理线程"""
        def process_batch():
            while True:
                time.sleep(5)  # 每5秒处理一次
                self.flush_batch()
        
        thread = threading.Thread(target=process_batch, daemon=True)
        thread.start()
    
    def emit(self, record):
        """发送日志记录"""
        try:
            log_entry = self.format(record)
            
            with self.lock:
                self.batch.append(log_entry)
                
                if len(self.batch) >= self.batch_size:
                    self.flush_batch()
                    
        except Exception as e:
            print(f"HTTP处理器错误: {e}")
    
    def flush_batch(self):
        """刷新批处理"""
        with self.lock:
            if not self.batch:
                return
            
            batch_data = self.batch.copy()
            self.batch.clear()
        
        try:
            if self.method == 'POST':
                response = self.session.post(
                    self.url,
                    json={'logs': batch_data},
                    headers=self.headers,
                    timeout=self.timeout
                )
            elif self.method == 'PUT':
                response = self.session.put(
                    self.url,
                    json={'logs': batch_data},
                    headers=self.headers,
                    timeout=self.timeout
                )
            else:
                raise ValueError(f"不支持的HTTP方法: {self.method}")
            
            if response.status_code >= 400:
                print(f"HTTP处理器发送失败: {response.status_code}")
                
        except Exception as e:
            print(f"HTTP处理器批处理错误: {e}")
    
    def close(self):
        """关闭处理器"""
        self.flush_batch()
        self.session.close()
        super().close()


class DatabaseHandler(logging.Handler):
    """数据库处理器"""
    
    def __init__(self, db_config: Dict[str, Any], table_name: str = 'system_logs'):
        super().__init__()
        self.db_config = db_config
        self.table_name = table_name
        self.connection_pool = []
        self.pool_size = 5
        self.init_connection_pool()
    
    def init_connection_pool(self):
        """初始化连接池"""
        try:
            import psycopg2
            from psycopg2 import pool
            
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=self.pool_size,
                host=self.db_config.get('host', 'localhost'),
                port=self.db_config.get('port', 5432),
                database=self.db_config.get('database', 'postgres'),
                user=self.db_config.get('username', 'postgres'),
                password=self.db_config.get('password', '')
            )
        except ImportError:
            print("psycopg2 未安装，无法使用数据库处理器")
        except Exception as e:
            print(f"数据库连接池初始化失败: {e}")
    
    def emit(self, record):
        """发送日志记录到数据库"""
        if not self.connection_pool:
            return
        
        connection = None
        try:
            connection = self.connection_pool.getconn()
            cursor = connection.cursor()
            
            # 准备日志数据
            log_data = {
                'timestamp': datetime.fromtimestamp(record.created),
                'level': record.levelname,
                'service_name': getattr(record, 'service_name', 'unknown'),
                'message': record.getMessage(),
                'user_id': getattr(record, 'user_id', None),
                'request_id': getattr(record, 'request_id', None),
                'metadata': json.dumps(self._get_metadata(record), ensure_ascii=False),
                'function_name': record.funcName,
                'line_number': record.lineno,
                'module': record.module
            }
            
            # 构建SQL
            columns = ', '.join(log_data.keys())
            placeholders = ', '.join(['%s'] * len(log_data))
            sql = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
            
            # 执行插入
            cursor.execute(sql, list(log_data.values()))
            connection.commit()
            
        except Exception as e:
            print(f"数据库处理器错误: {e}")
            if connection:
                connection.rollback()
        finally:
            if connection:
                self.connection_pool.putconn(connection)
    
    def _get_metadata(self, record) -> Dict[str, Any]:
        """获取元数据"""
        metadata = {}
        
        # 添加异常信息
        if record.exc_info:
            metadata['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1])
            }
        
        # 添加自定义字段
        for attr in dir(record):
            if attr.startswith('_'):
                continue
            if attr in ['args', 'msg', 'message', 'exc_info', 'exc_text', 
                       'stack_info', 'created', 'msecs', 'relativeCreated',
                       'thread', 'threadName', 'processName', 'process',
                       'levelname', 'levelno', 'pathname', 'filename',
                       'module', 'lineno', 'funcName', 'name']:
                continue
            
            value = getattr(record, attr, None)
            if value is not None:
                metadata[attr] = value
        
        return metadata
    
    def close(self):
        """关闭处理器"""
        if self.connection_pool:
            self.connection_pool.closeall()
        super().close()


class RedisHandler(logging.Handler):
    """Redis处理器"""
    
    def __init__(self, redis_config: Dict[str, Any], key_prefix: str = 'logs'):
        super().__init__()
        self.redis_config = redis_config
        self.key_prefix = key_prefix
        self.redis_client = None
        self.init_redis_client()
    
    def init_redis_client(self):
        """初始化Redis客户端"""
        try:
            import redis
            
            self.redis_client = redis.Redis(
                host=self.redis_config.get('host', 'localhost'),
                port=self.redis_config.get('port', 6379),
                db=self.redis_config.get('db', 0),
                password=self.redis_config.get('password', ''),
                decode_responses=True
            )
        except ImportError:
            print("redis 未安装，无法使用Redis处理器")
        except Exception as e:
            print(f"Redis客户端初始化失败: {e}")
    
    def emit(self, record):
        """发送日志记录到Redis"""
        if not self.redis_client:
            return
        
        try:
            log_entry = {
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'metadata': self._get_metadata(record)
            }
            
            # 使用LPUSH添加到列表
            key = f"{self.key_prefix}:{datetime.now().strftime('%Y-%m-%d')}"
            self.redis_client.lpush(key, json.dumps(log_entry, ensure_ascii=False))
            
            # 设置过期时间（30天）
            self.redis_client.expire(key, 30 * 24 * 3600)
            
        except Exception as e:
            print(f"Redis处理器错误: {e}")
    
    def _get_metadata(self, record) -> Dict[str, Any]:
        """获取元数据"""
        metadata = {}
        
        # 添加基本字段
        metadata['function'] = record.funcName
        metadata['line'] = record.lineno
        metadata['module'] = record.module
        metadata['thread'] = record.thread
        metadata['process'] = record.process
        
        # 添加异常信息
        if record.exc_info:
            metadata['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1])
            }
        
        # 添加自定义字段
        for attr in dir(record):
            if attr.startswith('_'):
                continue
            if attr in ['args', 'msg', 'message', 'exc_info', 'exc_text', 
                       'stack_info', 'created', 'msecs', 'relativeCreated',
                       'thread', 'threadName', 'processName', 'process',
                       'levelname', 'levelno', 'pathname', 'filename',
                       'module', 'lineno', 'funcName', 'name']:
                continue
            
            value = getattr(record, attr, None)
            if value is not None:
                metadata[attr] = value
        
        return metadata
    
    def close(self):
        """关闭处理器"""
        if self.redis_client:
            self.redis_client.close()
        super().close()


class ElasticsearchHandler(logging.Handler):
    """Elasticsearch处理器"""
    
    def __init__(self, es_config: Dict[str, Any], index_prefix: str = 'logs'):
        super().__init__()
        self.es_config = es_config
        self.index_prefix = index_prefix
        self.es_client = None
        self.init_es_client()
    
    def init_es_client(self):
        """初始化Elasticsearch客户端"""
        try:
            from elasticsearch import Elasticsearch
            
            self.es_client = Elasticsearch([{
                'host': self.es_config.get('host', 'localhost'),
                'port': self.es_config.get('port', 9200),
                'scheme': self.es_config.get('scheme', 'http')
            }])
        except ImportError:
            print("elasticsearch 未安装，无法使用Elasticsearch处理器")
        except Exception as e:
            print(f"Elasticsearch客户端初始化失败: {e}")
    
    def emit(self, record):
        """发送日志记录到Elasticsearch"""
        if not self.es_client:
            return
        
        try:
            # 生成索引名（按日期）
            index_name = f"{self.index_prefix}-{datetime.now().strftime('%Y-%m-%d')}"
            
            # 准备文档
            doc = {
                '@timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'source': {
                    'file': record.pathname,
                    'line': record.lineno,
                    'function': record.funcName
                },
                'process': {
                    'id': record.process,
                    'name': record.processName
                },
                'thread': {
                    'id': record.thread,
                    'name': record.threadName
                }
            }
            
            # 添加自定义字段
            for attr in dir(record):
                if attr.startswith('_'):
                    continue
                if attr in ['args', 'msg', 'message', 'exc_info', 'exc_text', 
                           'stack_info', 'created', 'msecs', 'relativeCreated',
                           'thread', 'threadName', 'processName', 'process',
                           'levelname', 'levelno', 'pathname', 'filename',
                           'module', 'lineno', 'funcName', 'name']:
                    continue
                
                value = getattr(record, attr, None)
                if value is not None:
                    doc[attr] = value
            
            # 发送到Elasticsearch
            self.es_client.index(index=index_name, document=doc)
            
        except Exception as e:
            print(f"Elasticsearch处理器错误: {e}")
    
    def close(self):
        """关闭处理器"""
        if self.es_client:
            self.es_client.close()
        super().close()


class KafkaHandler(logging.Handler):
    """Kafka处理器"""
    
    def __init__(self, kafka_config: Dict[str, Any], topic: str = 'logs'):
        super().__init__()
        self.kafka_config = kafka_config
        self.topic = topic
        self.producer = None
        self.init_kafka_producer()
    
    def init_kafka_producer(self):
        """初始化Kafka生产者"""
        try:
            from kafka import KafkaProducer
            
            self.producer = KafkaProducer(
                bootstrap_servers=self.kafka_config.get('bootstrap_servers', ['localhost:9092']),
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
        except ImportError:
            print("kafka-python 未安装，无法使用Kafka处理器")
        except Exception as e:
            print(f"Kafka生产者初始化失败: {e}")
    
    def emit(self, record):
        """发送日志记录到Kafka"""
        if not self.producer:
            return
        
        try:
            log_entry = {
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'metadata': self._get_metadata(record)
            }
            
            # 发送到Kafka
            self.producer.send(self.topic, value=log_entry)
            
        except Exception as e:
            print(f"Kafka处理器错误: {e}")
    
    def _get_metadata(self, record) -> Dict[str, Any]:
        """获取元数据"""
        metadata = {
            'function': record.funcName,
            'line': record.lineno,
            'module': record.module,
            'thread': record.thread,
            'process': record.process
        }
        
        # 添加异常信息
        if record.exc_info:
            metadata['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1])
            }
        
        return metadata
    
    def close(self):
        """关闭处理器"""
        if self.producer:
            self.producer.flush()
            self.producer.close()
        super().close()


class HandlerFactory:
    """处理器工厂"""
    
    @staticmethod
    def create_handler(handler_type: str, **kwargs) -> logging.Handler:
        """创建处理器"""
        handlers = {
            'async_file': AsyncFileHandler,
            'http': HTTPHandler,
            'database': DatabaseHandler,
            'redis': RedisHandler,
            'elasticsearch': ElasticsearchHandler,
            'kafka': KafkaHandler
        }
        
        handler_class = handlers.get(handler_type.lower())
        if not handler_class:
            raise ValueError(f"不支持的处理器类型: {handler_type}")
        
        return handler_class(**kwargs)
    
    @staticmethod
    def get_available_handlers() -> list:
        """获取可用的处理器类型"""
        return ['async_file', 'http', 'database', 'redis', 'elasticsearch', 'kafka']