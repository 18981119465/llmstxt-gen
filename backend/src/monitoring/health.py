"""
健康检查模块

提供系统健康检查功能，包括服务状态、资源使用率、依赖服务等检查。
"""

import asyncio
import time
import psutil
import socket
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import requests
import asyncpg
import redis.asyncio as redis
from concurrent.futures import ThreadPoolExecutor, as_completed

from .config import get_monitoring_config, MonitoringConfig
from .logger import get_logger


class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class CheckType(Enum):
    """检查类型枚举"""
    DATABASE = "database"
    REDIS = "redis"
    DISK = "disk"
    MEMORY = "memory"
    CPU = "cpu"
    NETWORK = "network"
    HTTP = "http"
    CUSTOM = "custom"


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    name: str
    check_type: CheckType
    status: HealthStatus
    response_time: float
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    critical: bool = False


@dataclass
class HealthCheck:
    """健康检查配置"""
    name: str
    check_type: CheckType
    enabled: bool = True
    critical: bool = False
    interval: int = 30
    timeout: int = 10
    config: Dict[str, Any] = field(default_factory=dict)
    threshold: float = 0.0


class DatabaseChecker:
    """数据库健康检查器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger('health.database')
    
    async def check_health(self) -> HealthCheckResult:
        """检查数据库健康状态"""
        start_time = time.time()
        
        try:
            # 连接数据库
            conn = await asyncpg.connect(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 5432),
                database=self.config.get('database', 'postgres'),
                user=self.config.get('username', 'postgres'),
                password=self.config.get('password', ''),
                timeout=self.config.get('timeout', 10)
            )
            
            # 执行简单查询
            result = await conn.fetchval('SELECT 1')
            await conn.close()
            
            response_time = time.time() - start_time
            
            # 获取连接池统计
            details = {
                'connection_success': True,
                'query_result': result,
                'response_time': response_time
            }
            
            return HealthCheckResult(
                name="database",
                check_type=CheckType.DATABASE,
                status=HealthStatus.HEALTHY,
                response_time=response_time,
                message="数据库连接正常",
                details=details
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            self.logger.error("数据库健康检查失败", error=str(e))
            
            return HealthCheckResult(
                name="database",
                check_type=CheckType.DATABASE,
                status=HealthStatus.UNHEALTHY,
                response_time=response_time,
                message=f"数据库连接失败: {str(e)}",
                details={'error': str(e)}
            )


class RedisChecker:
    """Redis健康检查器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger('health.redis')
    
    async def check_health(self) -> HealthCheckResult:
        """检查Redis健康状态"""
        start_time = time.time()
        
        try:
            # 连接Redis
            redis_client = redis.Redis(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 6379),
                db=self.config.get('db', 0),
                password=self.config.get('password', ''),
                socket_timeout=self.config.get('timeout', 10)
            )
            
            # 执行PING命令
            result = await redis_client.ping()
            await redis_client.close()
            
            response_time = time.time() - start_time
            
            # 获取Redis信息
            details = {
                'ping_success': result,
                'response_time': response_time
            }
            
            return HealthCheckResult(
                name="redis",
                check_type=CheckType.REDIS,
                status=HealthStatus.HEALTHY,
                response_time=response_time,
                message="Redis连接正常",
                details=details
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            self.logger.error("Redis健康检查失败", error=str(e))
            
            return HealthCheckResult(
                name="redis",
                check_type=CheckType.REDIS,
                status=HealthStatus.UNHEALTHY,
                response_time=response_time,
                message=f"Redis连接失败: {str(e)}",
                details={'error': str(e)}
            )


class SystemResourceChecker:
    """系统资源检查器"""
    
    def __init__(self):
        self.logger = get_logger('health.system')
    
    def check_disk_health(self, threshold: float = 0.9) -> HealthCheckResult:
        """检查磁盘健康状态"""
        start_time = time.time()
        
        try:
            disk_usage = psutil.disk_usage('/')
            usage_percent = disk_usage.percent / 100
            
            details = {
                'total': disk_usage.total,
                'used': disk_usage.used,
                'free': disk_usage.free,
                'percent': disk_usage.percent
            }
            
            response_time = time.time() - start_time
            
            if usage_percent > threshold:
                status = HealthStatus.UNHEALTHY
                message = f"磁盘空间不足: {disk_usage.percent}%"
            elif usage_percent > threshold * 0.8:
                status = HealthStatus.DEGRADED
                message = f"磁盘空间紧张: {disk_usage.percent}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"磁盘空间正常: {disk_usage.percent}%"
            
            return HealthCheckResult(
                name="disk",
                check_type=CheckType.DISK,
                status=status,
                response_time=response_time,
                message=message,
                details=details,
                critical=usage_percent > threshold
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            self.logger.error("磁盘健康检查失败", error=str(e))
            
            return HealthCheckResult(
                name="disk",
                check_type=CheckType.DISK,
                status=HealthStatus.UNHEALTHY,
                response_time=response_time,
                message=f"磁盘检查失败: {str(e)}",
                details={'error': str(e)}
            )
    
    def check_memory_health(self, threshold: float = 0.8) -> HealthCheckResult:
        """检查内存健康状态"""
        start_time = time.time()
        
        try:
            memory = psutil.virtual_memory()
            usage_percent = memory.percent / 100
            
            details = {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'percent': memory.percent
            }
            
            response_time = time.time() - start_time
            
            if usage_percent > threshold:
                status = HealthStatus.UNHEALTHY
                message = f"内存使用率过高: {memory.percent}%"
            elif usage_percent > threshold * 0.8:
                status = HealthStatus.DEGRADED
                message = f"内存使用率较高: {memory.percent}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"内存使用正常: {memory.percent}%"
            
            return HealthCheckResult(
                name="memory",
                check_type=CheckType.MEMORY,
                status=status,
                response_time=response_time,
                message=message,
                details=details
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            self.logger.error("内存健康检查失败", error=str(e))
            
            return HealthCheckResult(
                name="memory",
                check_type=CheckType.MEMORY,
                status=HealthStatus.UNHEALTHY,
                response_time=response_time,
                message=f"内存检查失败: {str(e)}",
                details={'error': str(e)}
            )
    
    def check_cpu_health(self, threshold: float = 0.8) -> HealthCheckResult:
        """检查CPU健康状态"""
        start_time = time.time()
        
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            usage_percent = cpu_percent / 100
            
            details = {
                'cpu_percent': cpu_percent,
                'cpu_count': psutil.cpu_count(),
                'cpu_count_logical': psutil.cpu_count(logical=True)
            }
            
            response_time = time.time() - start_time
            
            if usage_percent > threshold:
                status = HealthStatus.UNHEALTHY
                message = f"CPU使用率过高: {cpu_percent}%"
            elif usage_percent > threshold * 0.8:
                status = HealthStatus.DEGRADED
                message = f"CPU使用率较高: {cpu_percent}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"CPU使用正常: {cpu_percent}%"
            
            return HealthCheckResult(
                name="cpu",
                check_type=CheckType.CPU,
                status=status,
                response_time=response_time,
                message=message,
                details=details
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            self.logger.error("CPU健康检查失败", error=str(e))
            
            return HealthCheckResult(
                name="cpu",
                check_type=CheckType.CPU,
                status=HealthStatus.UNHEALTHY,
                response_time=response_time,
                message=f"CPU检查失败: {str(e)}",
                details={'error': str(e)}
            )


class HTTPChecker:
    """HTTP健康检查器"""
    
    def __init__(self):
        self.logger = get_logger('health.http')
    
    def check_http_endpoint(self, url: str, timeout: int = 10, 
                          expected_status: int = 200) -> HealthCheckResult:
        """检查HTTP端点健康状态"""
        start_time = time.time()
        
        try:
            response = requests.get(url, timeout=timeout)
            response_time = time.time() - start_time
            
            details = {
                'url': url,
                'status_code': response.status_code,
                'response_time': response_time,
                'response_size': len(response.content)
            }
            
            if response.status_code == expected_status:
                status = HealthStatus.HEALTHY
                message = f"HTTP端点正常: {response.status_code}"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"HTTP端点异常: {response.status_code}"
            
            return HealthCheckResult(
                name="http",
                check_type=CheckType.HTTP,
                status=status,
                response_time=response_time,
                message=message,
                details=details
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            self.logger.error("HTTP健康检查失败", error=str(e))
            
            return HealthCheckResult(
                name="http",
                check_type=CheckType.HTTP,
                status=HealthStatus.UNHEALTHY,
                response_time=response_time,
                message=f"HTTP检查失败: {str(e)}",
                details={'error': str(e)}
            )


class HealthChecker:
    """健康检查管理器"""
    
    def __init__(self, config: Optional[MonitoringConfig] = None):
        self.config = config or get_monitoring_config()
        self.logger = get_logger('health')
        self.checks: List[HealthCheck] = []
        self.results: Dict[str, HealthCheckResult] = {}
        self.running = False
        self.check_thread = None
        
        # 初始化检查器
        self.database_checker = DatabaseChecker(self.config.storage.database)
        self.redis_checker = RedisChecker(self.config.storage.redis)
        self.system_checker = SystemResourceChecker()
        self.http_checker = HTTPChecker()
        
        # 初始化健康检查配置
        self._init_checks()
    
    def _init_checks(self):
        """初始化健康检查配置"""
        for check_config in self.config.health.checks:
            check = HealthCheck(
                name=check_config['name'],
                check_type=CheckType(check_config['type']),
                enabled=check_config.get('enabled', True),
                critical=check_config.get('critical', False),
                interval=check_config.get('interval', 30),
                timeout=check_config.get('timeout', 10),
                config=check_config,
                threshold=check_config.get('threshold', 0.0)
            )
            self.checks.append(check)
    
    async def check_all_health(self) -> Dict[str, HealthCheckResult]:
        """检查所有健康状态"""
        tasks = []
        
        for check in self.checks:
            if not check.enabled:
                continue
            
            if check.check_type == CheckType.DATABASE:
                tasks.append(self.database_checker.check_health())
            elif check.check_type == CheckType.REDIS:
                tasks.append(self.redis_checker.check_health())
            elif check.check_type == CheckType.DISK:
                result = self.system_checker.check_disk_health(check.threshold)
                self.results[check.name] = result
            elif check.check_type == CheckType.MEMORY:
                result = self.system_checker.check_memory_health(check.threshold)
                self.results[check.name] = result
            elif check.check_type == CheckType.CPU:
                result = self.system_checker.check_cpu_health(check.threshold)
                self.results[check.name] = result
            elif check.check_type == CheckType.HTTP:
                url = check.config.get('url')
                if url:
                    result = self.http_checker.check_http_endpoint(
                        url, check.timeout
                    )
                    self.results[check.name] = result
        
        # 执行异步任务
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error("健康检查异常", error=str(result))
                else:
                    check_name = self.checks[i].name
                    self.results[check_name] = result
        
        return self.results
    
    def get_overall_health(self) -> HealthStatus:
        """获取整体健康状态"""
        if not self.results:
            return HealthStatus.UNKNOWN
        
        has_critical = any(result.critical and result.status != HealthStatus.HEALTHY 
                          for result in self.results.values())
        has_unhealthy = any(result.status == HealthStatus.UNHEALTHY 
                          for result in self.results.values())
        has_degraded = any(result.status == HealthStatus.DEGRADED 
                          for result in self.results.values())
        
        if has_critical or has_unhealthy:
            return HealthStatus.UNHEALTHY
        elif has_degraded:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY
    
    def get_health_summary(self) -> Dict[str, Any]:
        """获取健康检查摘要"""
        overall_status = self.get_overall_health()
        
        summary = {
            'overall_status': overall_status.value,
            'timestamp': datetime.now().isoformat(),
            'total_checks': len(self.results),
            'healthy_checks': sum(1 for r in self.results.values() 
                                if r.status == HealthStatus.HEALTHY),
            'degraded_checks': sum(1 for r in self.results.values() 
                                 if r.status == HealthStatus.DEGRADED),
            'unhealthy_checks': sum(1 for r in self.results.values() 
                                  if r.status == HealthStatus.UNHEALTHY),
            'checks': {}
        }
        
        for name, result in self.results.items():
            summary['checks'][name] = {
                'status': result.status.value,
                'response_time': result.response_time,
                'message': result.message,
                'critical': result.critical,
                'timestamp': result.timestamp.isoformat()
            }
        
        return summary
    
    def start_monitoring(self):
        """启动健康检查监控"""
        if self.running:
            return
        
        self.running = True
        
        def monitoring_loop():
            while self.running:
                try:
                    # 异步执行健康检查
                    asyncio.run(self.check_all_health())
                    
                    # 记录健康状态
                    summary = self.get_health_summary()
                    self.logger.info("健康检查完成", **summary)
                    
                except Exception as e:
                    self.logger.error("健康检查监控异常", error=str(e))
                
                # 等待下一次检查
                time.sleep(self.config.health.check_interval)
        
        self.check_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self.check_thread.start()
        self.logger.info("健康检查监控已启动")
    
    def stop_monitoring(self):
        """停止健康检查监控"""
        self.running = False
        if self.check_thread:
            self.check_thread.join()
        self.logger.info("健康检查监控已停止")
    
    def add_custom_check(self, name: str, check_func: Callable, 
                        check_type: CheckType = CheckType.CUSTOM,
                        critical: bool = False, interval: int = 30):
        """添加自定义健康检查"""
        async def custom_check() -> HealthCheckResult:
            start_time = time.time()
            
            try:
                result = check_func()
                response_time = time.time() - start_time
                
                if isinstance(result, bool):
                    status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                    message = "自定义检查通过" if result else "自定义检查失败"
                elif isinstance(result, dict):
                    status = HealthStatus(result.get('status', 'unknown'))
                    message = result.get('message', '自定义检查完成')
                else:
                    status = HealthStatus.HEALTHY
                    message = "自定义检查完成"
                
                return HealthCheckResult(
                    name=name,
                    check_type=check_type,
                    status=status,
                    response_time=response_time,
                    message=message,
                    critical=critical
                )
                
            except Exception as e:
                response_time = time.time() - start_time
                return HealthCheckResult(
                    name=name,
                    check_type=check_type,
                    status=HealthStatus.UNHEALTHY,
                    response_time=response_time,
                    message=f"自定义检查异常: {str(e)}",
                    critical=critical
                )
        
        # 添加到检查列表
        check = HealthCheck(
            name=name,
            check_type=check_type,
            enabled=True,
            critical=critical,
            interval=interval,
            config={'custom_func': check_func}
        )
        self.checks.append(check)
    
    def remove_check(self, name: str):
        """移除健康检查"""
        self.checks = [check for check in self.checks if check.name != name]
        if name in self.results:
            del self.results[name]


# 全局健康检查器实例
_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """获取全局健康检查器实例"""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


def start_health_monitoring():
    """启动健康监控"""
    checker = get_health_checker()
    checker.start_monitoring()


def stop_health_monitoring():
    """停止健康监控"""
    checker = get_health_checker()
    checker.stop_monitoring()