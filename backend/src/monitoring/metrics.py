"""
性能监控指标收集模块

提供系统性能指标收集、存储和查询功能。
"""

import time
import threading
import asyncio
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import psutil
import statistics
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor

from .config import get_monitoring_config, MonitoringConfig
from .logger import get_logger


class MetricType(Enum):
    """指标类型枚举"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricValue:
    """指标值"""
    name: str
    type: MetricType
    value: float
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class HistogramBucket:
    """直方图桶"""
    upper_bound: float
    count: int


@dataclass
class HistogramSnapshot:
    """直方图快照"""
    sum: float
    count: int
    buckets: List[HistogramBucket]


class Counter:
    """计数器指标"""
    
    def __init__(self, name: str, description: str = "", tags: Dict[str, str] = None):
        self.name = name
        self.description = description
        self.tags = tags or {}
        self._value = 0.0
        self._lock = threading.Lock()
        self._created_at = datetime.now()
    
    def inc(self, amount: float = 1.0):
        """增加计数"""
        with self._lock:
            self._value += amount
    
    def dec(self, amount: float = 1.0):
        """减少计数"""
        with self._lock:
            self._value -= amount
    
    def set(self, value: float):
        """设置值"""
        with self._lock:
            self._value = value
    
    def get_value(self) -> float:
        """获取当前值"""
        with self._lock:
            return self._value
    
    def reset(self):
        """重置计数器"""
        with self._lock:
            self._value = 0.0
    
    def to_metric_value(self) -> MetricValue:
        """转换为指标值"""
        return MetricValue(
            name=self.name,
            type=MetricType.COUNTER,
            value=self.get_value(),
            tags=self.tags.copy()
        )


class Gauge:
    """仪表盘指标"""
    
    def __init__(self, name: str, description: str = "", tags: Dict[str, str] = None):
        self.name = name
        self.description = description
        self.tags = tags or {}
        self._value = 0.0
        self._lock = threading.Lock()
        self._created_at = datetime.now()
    
    def set(self, value: float):
        """设置值"""
        with self._lock:
            self._value = value
    
    def inc(self, amount: float = 1.0):
        """增加值"""
        with self._lock:
            self._value += amount
    
    def dec(self, amount: float = 1.0):
        """减少值"""
        with self._lock:
            self._value -= amount
    
    def get_value(self) -> float:
        """获取当前值"""
        with self._lock:
            return self._value
    
    def to_metric_value(self) -> MetricValue:
        """转换为指标值"""
        return MetricValue(
            name=self.name,
            type=MetricType.GAUGE,
            value=self.get_value(),
            tags=self.tags.copy()
        )


class Histogram:
    """直方图指标"""
    
    def __init__(self, name: str, description: str = "", 
                 buckets: List[float] = None, tags: Dict[str, str] = None):
        self.name = name
        self.description = description
        self.tags = tags or {}
        self.buckets = buckets or [0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
        self._observations = deque(maxlen=10000)
        self._lock = threading.Lock()
        self._created_at = datetime.now()
    
    def observe(self, value: float):
        """观察值"""
        with self._lock:
            self._observations.append(value)
    
    def get_snapshot(self) -> HistogramSnapshot:
        """获取快照"""
        with self._lock:
            if not self._observations:
                return HistogramSnapshot(sum=0, count=0, buckets=[])
            
            observations = list(self._observations)
            count = len(observations)
            total = sum(observations)
            
            # 计算桶
            bucket_counts = defaultdict(int)
            for obs in observations:
                for bucket in self.buckets:
                    if obs <= bucket:
                        bucket_counts[bucket] += 1
                    else:
                        bucket_counts[float('inf')] += 1
            
            buckets = [
                HistogramBucket(upper_bound=bound, count=bucket_counts[bound])
                for bound in self.buckets + [float('inf')]
            ]
            
            return HistogramSnapshot(sum=total, count=count, buckets=buckets)
    
    def reset(self):
        """重置直方图"""
        with self._lock:
            self._observations.clear()
    
    def to_metric_values(self) -> List[MetricValue]:
        """转换为指标值列表"""
        snapshot = self.get_snapshot()
        metrics = []
        
        # 添加计数和总和
        metrics.append(MetricValue(
            name=f"{self.name}_count",
            type=MetricType.COUNTER,
            value=snapshot.count,
            tags=self.tags.copy()
        ))
        
        metrics.append(MetricValue(
            name=f"{self.name}_sum",
            type=MetricType.COUNTER,
            value=snapshot.sum,
            tags=self.tags.copy()
        ))
        
        # 添加桶
        for bucket in snapshot.buckets:
            metrics.append(MetricValue(
                name=f"{self.name}_bucket",
                type=MetricType.COUNTER,
                value=bucket.count,
                tags={**self.tags, "le": str(bucket.upper_bound)}
            ))
        
        return metrics


class MetricsRegistry:
    """指标注册表"""
    
    def __init__(self):
        self._metrics: Dict[str, Union[Counter, Gauge, Histogram]] = {}
        self._lock = threading.Lock()
    
    def counter(self, name: str, description: str = "", 
               tags: Dict[str, str] = None) -> Counter:
        """获取或创建计数器"""
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = Counter(name, description, tags)
            elif not isinstance(self._metrics[name], Counter):
                raise ValueError(f"指标 {name} 已存在且类型不是Counter")
            return self._metrics[name]
    
    def gauge(self, name: str, description: str = "", 
              tags: Dict[str, str] = None) -> Gauge:
        """获取或创建仪表盘"""
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = Gauge(name, description, tags)
            elif not isinstance(self._metrics[name], Gauge):
                raise ValueError(f"指标 {name} 已存在且类型不是Gauge")
            return self._metrics[name]
    
    def histogram(self, name: str, description: str = "", 
                  buckets: List[float] = None, tags: Dict[str, str] = None) -> Histogram:
        """获取或创建直方图"""
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = Histogram(name, description, buckets, tags)
            elif not isinstance(self._metrics[name], Histogram):
                raise ValueError(f"指标 {name} 已存在且类型不是Histogram")
            return self._metrics[name]
    
    def get_metric(self, name: str) -> Optional[Union[Counter, Gauge, Histogram]]:
        """获取指标"""
        with self._lock:
            return self._metrics.get(name)
    
    def get_all_metrics(self) -> Dict[str, Union[Counter, Gauge, Histogram]]:
        """获取所有指标"""
        with self._lock:
            return self._metrics.copy()
    
    def collect(self) -> List[MetricValue]:
        """收集所有指标值"""
        metrics = []
        for metric in self._metrics.values():
            if isinstance(metric, (Counter, Gauge)):
                metrics.append(metric.to_metric_value())
            elif isinstance(metric, Histogram):
                metrics.extend(metric.to_metric_values())
        return metrics
    
    def remove_metric(self, name: str):
        """移除指标"""
        with self._lock:
            if name in self._metrics:
                del self._metrics[name]
    
    def clear(self):
        """清空所有指标"""
        with self._lock:
            self._metrics.clear()


class SystemMetricsCollector:
    """系统指标收集器"""
    
    def __init__(self):
        self.logger = get_logger("metrics.system")
        self._network_io_prev = psutil.net_io_counters()
        self._disk_io_prev = psutil.disk_io_counters()
        self._last_collection = time.time()
    
    def collect_cpu_metrics(self) -> List[MetricValue]:
        """收集CPU指标"""
        metrics = []
        
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics.append(MetricValue(
                name="system_cpu_usage_percent",
                type=MetricType.GAUGE,
                value=cpu_percent
            ))
            
            # CPU核心数
            cpu_count = psutil.cpu_count()
            cpu_count_logical = psutil.cpu_count(logical=True)
            metrics.append(MetricValue(
                name="system_cpu_count",
                type=MetricType.GAUGE,
                value=cpu_count,
                tags={"type": "physical"}
            ))
            metrics.append(MetricValue(
                name="system_cpu_count",
                type=MetricType.GAUGE,
                value=cpu_count_logical,
                tags={"type": "logical"}
            ))
            
            # CPU负载
            load_avg = psutil.getloadavg()
            metrics.append(MetricValue(
                name="system_load_avg_1min",
                type=MetricType.GAUGE,
                value=load_avg[0]
            ))
            metrics.append(MetricValue(
                name="system_load_avg_5min",
                type=MetricType.GAUGE,
                value=load_avg[1]
            ))
            metrics.append(MetricValue(
                name="system_load_avg_15min",
                type=MetricType.GAUGE,
                value=load_avg[2]
            ))
            
        except Exception as e:
            self.logger.error("收集CPU指标失败", error=str(e))
        
        return metrics
    
    def collect_memory_metrics(self) -> List[MetricValue]:
        """收集内存指标"""
        metrics = []
        
        try:
            # 虚拟内存
            virtual_memory = psutil.virtual_memory()
            metrics.append(MetricValue(
                name="system_memory_total_bytes",
                type=MetricType.GAUGE,
                value=virtual_memory.total
            ))
            metrics.append(MetricValue(
                name="system_memory_used_bytes",
                type=MetricType.GAUGE,
                value=virtual_memory.used
            ))
            metrics.append(MetricValue(
                name="system_memory_available_bytes",
                type=MetricType.GAUGE,
                value=virtual_memory.available
            ))
            metrics.append(MetricValue(
                name="system_memory_usage_percent",
                type=MetricType.GAUGE,
                value=virtual_memory.percent
            ))
            
            # 交换内存
            swap_memory = psutil.swap_memory()
            metrics.append(MetricValue(
                name="system_swap_total_bytes",
                type=MetricType.GAUGE,
                value=swap_memory.total
            ))
            metrics.append(MetricValue(
                name="system_swap_used_bytes",
                type=MetricType.GAUGE,
                value=swap_memory.used
            ))
            metrics.append(MetricValue(
                name="system_swap_usage_percent",
                type=MetricType.GAUGE,
                value=swap_memory.percent
            ))
            
        except Exception as e:
            self.logger.error("收集内存指标失败", error=str(e))
        
        return metrics
    
    def collect_disk_metrics(self) -> List[MetricValue]:
        """收集磁盘指标"""
        metrics = []
        
        try:
            # 磁盘使用率
            disk_usage = psutil.disk_usage('/')
            metrics.append(MetricValue(
                name="system_disk_total_bytes",
                type=MetricType.GAUGE,
                value=disk_usage.total
            ))
            metrics.append(MetricValue(
                name="system_disk_used_bytes",
                type=MetricType.GAUGE,
                value=disk_usage.used
            ))
            metrics.append(MetricValue(
                name="system_disk_free_bytes",
                type=MetricType.GAUGE,
                value=disk_usage.free
            ))
            metrics.append(MetricValue(
                name="system_disk_usage_percent",
                type=MetricType.GAUGE,
                value=disk_usage.percent
            ))
            
            # 磁盘IO
            disk_io = psutil.disk_io_counters()
            if disk_io and self._disk_io_prev:
                time_diff = time.time() - self._last_collection
                read_bytes_rate = (disk_io.read_bytes - self._disk_io_prev.read_bytes) / time_diff
                write_bytes_rate = (disk_io.write_bytes - self._disk_io_prev.write_bytes) / time_diff
                
                metrics.append(MetricValue(
                    name="system_disk_read_bytes_per_second",
                    type=MetricType.GAUGE,
                    value=read_bytes_rate
                ))
                metrics.append(MetricValue(
                    name="system_disk_write_bytes_per_second",
                    type=MetricType.GAUGE,
                    value=write_bytes_rate
                ))
            
            self._disk_io_prev = disk_io
            
        except Exception as e:
            self.logger.error("收集磁盘指标失败", error=str(e))
        
        return metrics
    
    def collect_network_metrics(self) -> List[MetricValue]:
        """收集网络指标"""
        metrics = []
        
        try:
            # 网络IO
            net_io = psutil.net_io_counters()
            if net_io and self._network_io_prev:
                time_diff = time.time() - self._last_collection
                bytes_sent_rate = (net_io.bytes_sent - self._network_io_prev.bytes_sent) / time_diff
                bytes_recv_rate = (net_io.bytes_recv - self._network_io_prev.bytes_recv) / time_diff
                
                metrics.append(MetricValue(
                    name="system_network_bytes_sent_per_second",
                    type=MetricType.GAUGE,
                    value=bytes_sent_rate
                ))
                metrics.append(MetricValue(
                    name="system_network_bytes_recv_per_second",
                    type=MetricType.GAUGE,
                    value=bytes_recv_rate
                ))
            
            self._network_io_prev = net_io
            
        except Exception as e:
            self.logger.error("收集网络指标失败", error=str(e))
        
        return metrics
    
    def collect_process_metrics(self) -> List[MetricValue]:
        """收集进程指标"""
        metrics = []
        
        try:
            process = psutil.Process()
            
            # 进程CPU使用率
            cpu_percent = process.cpu_percent()
            metrics.append(MetricValue(
                name="process_cpu_usage_percent",
                type=MetricType.GAUGE,
                value=cpu_percent
            ))
            
            # 进程内存使用
            memory_info = process.memory_info()
            metrics.append(MetricValue(
                name="process_memory_rss_bytes",
                type=MetricType.GAUGE,
                value=memory_info.rss
            ))
            metrics.append(MetricValue(
                name="process_memory_vms_bytes",
                type=MetricType.GAUGE,
                value=memory_info.vms
            ))
            
            # 进程线程数
            num_threads = process.num_threads()
            metrics.append(MetricValue(
                name="process_thread_count",
                type=MetricType.GAUGE,
                value=num_threads
            ))
            
            # 进程文件描述符数
            try:
                num_fds = process.num_fds()
                metrics.append(MetricValue(
                    name="process_file_descriptor_count",
                    type=MetricType.GAUGE,
                    value=num_fds
                ))
            except AttributeError:
                pass
            
        except Exception as e:
            self.logger.error("收集进程指标失败", error=str(e))
        
        return metrics
    
    def collect_all_metrics(self) -> List[MetricValue]:
        """收集所有系统指标"""
        all_metrics = []
        
        all_metrics.extend(self.collect_cpu_metrics())
        all_metrics.extend(self.collect_memory_metrics())
        all_metrics.extend(self.collect_disk_metrics())
        all_metrics.extend(self.collect_network_metrics())
        all_metrics.extend(self.collect_process_metrics())
        
        self._last_collection = time.time()
        
        return all_metrics


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self, config: Optional[MonitoringConfig] = None):
        self.config = config or get_monitoring_config()
        self.logger = get_logger("metrics")
        self.registry = MetricsRegistry()
        self.system_collector = SystemMetricsCollector()
        self.custom_collectors: List[Callable] = []
        self.running = False
        self.collection_thread = None
        self.metrics_history: deque = deque(maxlen=10000)
        
        # 初始化默认指标
        self._init_default_metrics()
    
    def _init_default_metrics(self):
        """初始化默认指标"""
        # 请求计数
        self.registry.counter(
            "http_requests_total",
            "HTTP请求总数",
            {"service": "backend"}
        )
        
        # 请求持续时间
        self.registry.histogram(
            "http_request_duration_seconds",
            "HTTP请求持续时间",
            [0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
            {"service": "backend"}
        )
        
        # 错误计数
        self.registry.counter(
            "http_errors_total",
            "HTTP错误总数",
            {"service": "backend"}
        )
        
        # 活跃用户数
        self.registry.gauge(
            "active_users_count",
            "活跃用户数",
            {"service": "backend"}
        )
        
        # 数据库查询计数
        self.registry.counter(
            "database_queries_total",
            "数据库查询总数",
            {"service": "backend"}
        )
        
        # 数据库查询持续时间
        self.registry.histogram(
            "database_query_duration_seconds",
            "数据库查询持续时间",
            [0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
            {"service": "backend"}
        )
    
    def collect_metrics(self) -> List[MetricValue]:
        """收集所有指标"""
        all_metrics = []
        
        # 收集应用指标
        app_metrics = self.registry.collect()
        all_metrics.extend(app_metrics)
        
        # 收集系统指标
        system_metrics = self.system_collector.collect_all_metrics()
        all_metrics.extend(system_metrics)
        
        # 收集自定义指标
        for collector in self.custom_collectors:
            try:
                custom_metrics = collector()
                all_metrics.extend(custom_metrics)
            except Exception as e:
                self.logger.error("收集自定义指标失败", error=str(e))
        
        # 记录指标历史
        timestamp = datetime.now()
        for metric in all_metrics:
            self.metrics_history.append({
                "metric": metric,
                "timestamp": timestamp
            })
        
        return all_metrics
    
    def start_collecting(self):
        """启动指标收集"""
        if self.running:
            return
        
        self.running = True
        
        def collection_loop():
            while self.running:
                try:
                    # 收集指标
                    metrics = self.collect_metrics()
                    
                    # 记录收集完成
                    self.logger.debug("指标收集完成", count=len(metrics))
                    
                except Exception as e:
                    self.logger.error("指标收集异常", error=str(e))
                
                # 等待下一次收集
                time.sleep(self.config.metrics.collection_interval)
        
        self.collection_thread = threading.Thread(target=collection_loop, daemon=True)
        self.collection_thread.start()
        self.logger.info("指标收集已启动")
    
    def stop_collecting(self):
        """停止指标收集"""
        self.running = False
        if self.collection_thread:
            self.collection_thread.join()
        self.logger.info("指标收集已停止")
    
    def add_custom_collector(self, collector: Callable[[], List[MetricValue]]):
        """添加自定义指标收集器"""
        self.custom_collectors.append(collector)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        metrics = self.collect_metrics()
        
        summary = {
            "total_metrics": len(metrics),
            "timestamp": datetime.now().isoformat(),
            "metrics_by_type": {
                "counter": 0,
                "gauge": 0,
                "histogram": 0
            },
            "sample_metrics": {}
        }
        
        # 按类型统计
        for metric in metrics:
            metric_type = metric.type.value
            summary["metrics_by_type"][metric_type] += 1
            
            # 添加示例指标
            if metric.name in ["system_cpu_usage_percent", "system_memory_usage_percent", 
                             "http_requests_total", "active_users_count"]:
                summary["sample_metrics"][metric.name] = {
                    "value": metric.value,
                    "type": metric_type,
                    "tags": metric.tags
                }
        
        return summary
    
    def get_metrics_history(self, metric_name: str = None, 
                           start_time: datetime = None, 
                           end_time: datetime = None) -> List[Dict[str, Any]]:
        """获取指标历史"""
        history = []
        
        for record in self.metrics_history:
            metric = record["metric"]
            timestamp = record["timestamp"]
            
            # 过滤条件
            if metric_name and metric.name != metric_name:
                continue
            if start_time and timestamp < start_time:
                continue
            if end_time and timestamp > end_time:
                continue
            
            history.append({
                "name": metric.name,
                "type": metric.type.value,
                "value": metric.value,
                "tags": metric.tags,
                "timestamp": timestamp.isoformat()
            })
        
        return history


# 全局指标收集器实例
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """获取全局指标收集器实例"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def start_metrics_collection():
    """启动指标收集"""
    collector = get_metrics_collector()
    collector.start_collecting()


def stop_metrics_collection():
    """停止指标收集"""
    collector = get_metrics_collector()
    collector.stop_collecting()


# 便捷函数
def get_counter(name: str, description: str = "", tags: Dict[str, str] = None) -> Counter:
    """获取计数器"""
    collector = get_metrics_collector()
    return collector.registry.counter(name, description, tags)


def get_gauge(name: str, description: str = "", tags: Dict[str, str] = None) -> Gauge:
    """获取仪表盘"""
    collector = get_metrics_collector()
    return collector.registry.gauge(name, description, tags)


def get_histogram(name: str, description: str = "", 
                  buckets: List[float] = None, tags: Dict[str, str] = None) -> Histogram:
    """获取直方图"""
    collector = get_metrics_collector()
    return collector.registry.histogram(name, description, buckets, tags)