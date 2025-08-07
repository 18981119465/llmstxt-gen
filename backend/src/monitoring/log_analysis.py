"""
日志查询和分析API

提供日志查询、分析、统计等功能的REST API接口。
"""

import json
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import logging
from pathlib import Path
import re
import gzip
import io
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

from .config import get_monitoring_config, MonitoringConfig
from .logger import get_logger
from .health import get_health_checker
from .metrics import get_metrics_collector
from .alerts import get_alert_engine, Alert, AlertLevel


# Pydantic 模型
class LogQueryRequest(BaseModel):
    """日志查询请求"""
    query: str = Field(..., description="查询字符串")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    level: Optional[str] = Field(None, description="日志级别")
    service: Optional[str] = Field(None, description="服务名")
    limit: int = Field(100, description="返回记录数限制", ge=1, le=1000)
    offset: int = Field(0, description="偏移量", ge=0)
    sort_field: str = Field("timestamp", description="排序字段")
    sort_order: str = Field("desc", description="排序方向")


class LogResponse(BaseModel):
    """日志响应"""
    logs: List[Dict[str, Any]]
    total: int
    query: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    level: Optional[str]
    service: Optional[str]
    limit: int
    offset: int


class LogStatsRequest(BaseModel):
    """日志统计请求"""
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    service: Optional[str] = Field(None, description="服务名")
    group_by: str = Field("level", description="分组字段")


class LogStatsResponse(BaseModel):
    """日志统计响应"""
    total_logs: int
    grouped_stats: Dict[str, int]
    time_range: Dict[str, datetime]
    service: Optional[str]


class AlertQueryRequest(BaseModel):
    """告警查询请求"""
    level: Optional[str] = Field(None, description="告警级别")
    status: Optional[str] = Field(None, description="告警状态")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    limit: int = Field(100, description="返回记录数限制", ge=1, le=1000)
    offset: int = Field(0, description="偏移量", ge=0)


class MetricsQueryRequest(BaseModel):
    """指标查询请求"""
    metric_name: str = Field(..., description="指标名称")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    tags: Optional[Dict[str, str]] = Field(None, description="标签过滤")
    aggregation: str = Field("avg", description="聚合方式")


class LogAnalyzer:
    """日志分析器"""
    
    def __init__(self, config: Optional[MonitoringConfig] = None):
        self.config = config or get_monitoring_config()
        self.logger = get_logger('log_analyzer')
        self.log_files = self._find_log_files()
        self.index = {}
        
    def _find_log_files(self) -> List[Path]:
        """查找日志文件"""
        log_files = []
        
        # 查找主日志文件
        log_dir = Path(self.config.logging.file_path).parent
        if log_dir.exists():
            for file_pattern in ['*.log', '*.log.gz']:
                log_files.extend(log_dir.glob(file_pattern))
        
        return sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True)
    
    def search_logs(self, query: LogQueryRequest) -> LogResponse:
        """搜索日志"""
        try:
            results = []
            total = 0
            
            # 解析查询字符串
            query_regex = self._parse_query(query.query)
            
            # 搜索日志文件
            for log_file in self.log_files:
                if len(results) >= query.limit + query.offset:
                    break
                
                file_results = self._search_file(log_file, query_regex, query)
                results.extend(file_results)
            
            # 排序结果
            if query.sort_field in ['timestamp', 'created']:
                reverse = query.sort_order.lower() == 'desc'
                results.sort(key=lambda x: x.get(query.sort_field, 0), reverse=reverse)
            
            # 应用分页
            total = len(results)
            paginated_results = results[query.offset:query.offset + query.limit]
            
            return LogResponse(
                logs=paginated_results,
                total=total,
                query=query.query,
                start_time=query.start_time,
                end_time=query.end_time,
                level=query.level,
                service=query.service,
                limit=query.limit,
                offset=query.offset
            )
            
        except Exception as e:
            self.logger.error("搜索日志失败", error=str(e))
            raise HTTPException(status_code=500, detail=f"搜索日志失败: {str(e)}")
    
    def _parse_query(self, query_str: str) -> re.Pattern:
        """解析查询字符串为正则表达式"""
        # 简单的查询解析：支持 AND, OR, NOT 操作
        # 这里简化处理，直接转换为正则表达式
        try:
            return re.compile(query_str, re.IGNORECASE)
        except re.error:
            # 如果不是有效的正则表达式，进行转义
            return re.compile(re.escape(query_str), re.IGNORECASE)
    
    def _search_file(self, log_file: Path, query_regex: re.Pattern, query: LogQueryRequest) -> List[Dict[str, Any]]:
        """搜索单个日志文件"""
        results = []
        
        try:
            # 确定文件打开方式
            if log_file.suffix == '.gz':
                file_opener = gzip.open
                mode = 'rt'
            else:
                file_opener = open
                mode = 'r'
            
            with file_opener(log_file, mode, encoding='utf-8') as f:
                for line in f:
                    try:
                        # 解析日志行
                        log_entry = self._parse_log_line(line.strip())
                        
                        # 应用过滤条件
                        if not self._matches_filters(log_entry, query):
                            continue
                        
                        # 应用查询条件
                        if query_regex.search(line):
                            results.append(log_entry)
                            
                    except Exception as e:
                        self.logger.warning("解析日志行失败", file=log_file.name, error=str(e))
                        continue
                        
        except Exception as e:
            self.logger.error("搜索日志文件失败", file=log_file.name, error=str(e))
        
        return results
    
    def _parse_log_line(self, line: str) -> Dict[str, Any]:
        """解析日志行"""
        try:
            # 尝试解析JSON格式
            return json.loads(line)
        except json.JSONDecodeError:
            # 如果不是JSON，创建简单的日志条目
            return {
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'message': line,
                'raw': line
            }
    
    def _matches_filters(self, log_entry: Dict[str, Any], query: LogQueryRequest) -> bool:
        """检查日志条目是否匹配过滤条件"""
        # 时间过滤
        if query.start_time:
            log_time = self._parse_timestamp(log_entry.get('timestamp'))
            if log_time and log_time < query.start_time:
                return False
        
        if query.end_time:
            log_time = self._parse_timestamp(log_entry.get('timestamp'))
            if log_time and log_time > query.end_time:
                return False
        
        # 级别过滤
        if query.level:
            log_level = log_entry.get('level', '').upper()
            if log_level != query.level.upper():
                return False
        
        # 服务过滤
        if query.service:
            log_service = log_entry.get('service_name', '')
            if query.service not in log_service:
                return False
        
        return True
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """解析时间戳"""
        if not timestamp_str:
            return None
        
        try:
            # 尝试不同的时间格式
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%f',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%dT%H:%M:%S.%fZ'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(timestamp_str, fmt)
                except ValueError:
                    continue
            
            return None
            
        except Exception:
            return None
    
    def get_log_stats(self, stats_request: LogStatsRequest) -> LogStatsResponse:
        """获取日志统计"""
        try:
            stats = defaultdict(int)
            total_logs = 0
            
            # 构建查询
            query = LogQueryRequest(
                query="*",
                start_time=stats_request.start_time,
                end_time=stats_request.end_time,
                service=stats_request.service,
                limit=10000  # 限制统计的日志数量
            )
            
            # 搜索日志
            response = self.search_logs(query)
            
            # 统计分组
            group_field = stats_request.group_by
            for log_entry in response.logs:
                key = log_entry.get(group_field, 'unknown')
                stats[key] += 1
                total_logs += 1
            
            return LogStatsResponse(
                total_logs=total_logs,
                grouped_stats=dict(stats),
                time_range={
                    'start': stats_request.start_time or datetime.min,
                    'end': stats_request.end_time or datetime.max
                },
                service=stats_request.service
            )
            
        except Exception as e:
            self.logger.error("获取日志统计失败", error=str(e))
            raise HTTPException(status_code=500, detail=f"获取日志统计失败: {str(e)}")
    
    def get_error_analysis(self, start_time: Optional[datetime] = None, 
                          end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """获取错误分析"""
        try:
            # 查询错误日志
            query = LogQueryRequest(
                query="*",
                start_time=start_time,
                end_time=end_time,
                level="ERROR",
                limit=1000
            )
            
            response = self.search_logs(query)
            
            # 分析错误模式
            error_patterns = defaultdict(int)
            error_services = defaultdict(int)
            error_messages = defaultdict(int)
            
            for log_entry in response.logs:
                # 提取错误模式
                message = log_entry.get('message', '')
                service = log_entry.get('service_name', 'unknown')
                
                # 简单的错误模式提取
                error_pattern = self._extract_error_pattern(message)
                error_patterns[error_pattern] += 1
                error_services[service] += 1
                error_messages[message] += 1
            
            return {
                'total_errors': response.total,
                'error_patterns': dict(error_patterns),
                'error_by_service': dict(error_services),
                'top_error_messages': dict(sorted(error_messages.items(), key=lambda x: x[1], reverse=True)[:10]),
                'time_range': {
                    'start': start_time or datetime.min,
                    'end': end_time or datetime.max
                }
            }
            
        except Exception as e:
            self.logger.error("获取错误分析失败", error=str(e))
            raise HTTPException(status_code=500, detail=f"获取错误分析失败: {str(e)}")
    
    def _extract_error_pattern(self, message: str) -> str:
        """提取错误模式"""
        # 简单的错误模式提取
        patterns = [
            r'(\w+Exception)',
            r'(\w+Error)',
            r'Connection\s+\w+',
            r'Timeout',
            r'Permission\s+denied',
            r'Not\s+found',
            r'Invalid\s+\w+'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "UnknownError"


# 创建路由器
router = APIRouter(prefix="/api/v1/logs", tags=["logs"])

# 全局日志分析器实例
_log_analyzer: Optional[LogAnalyzer] = None


def get_log_analyzer() -> LogAnalyzer:
    """获取全局日志分析器实例"""
    global _log_analyzer
    if _log_analyzer is None:
        _log_analyzer = LogAnalyzer()
    return _log_analyzer


@router.post("/search")
async def search_logs(
    query_request: LogQueryRequest,
    analyzer: LogAnalyzer = Depends(get_log_analyzer)
) -> LogResponse:
    """搜索日志"""
    return analyzer.search_logs(query_request)


@router.post("/stats")
async def get_log_stats(
    stats_request: LogStatsRequest,
    analyzer: LogAnalyzer = Depends(get_log_analyzer)
) -> LogStatsResponse:
    """获取日志统计"""
    return analyzer.get_log_stats(stats_request)


@router.get("/error-analysis")
async def get_error_analysis(
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    analyzer: LogAnalyzer = Depends(get_log_analyzer)
) -> Dict[str, Any]:
    """获取错误分析"""
    return analyzer.get_error_analysis(start_time, end_time)


@router.get("/services")
async def get_services(
    analyzer: LogAnalyzer = Depends(get_log_analyzer)
) -> List[str]:
    """获取服务列表"""
    try:
        query = LogQueryRequest(query="*", limit=1000)
        response = analyzer.search_logs(query)
        
        services = set()
        for log_entry in response.logs:
            service = log_entry.get('service_name')
            if service:
                services.add(service)
        
        return sorted(list(services))
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取服务列表失败: {str(e)}")


@router.get("/levels")
async def get_log_levels() -> List[str]:
    """获取日志级别列表"""
    return ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


@router.get("/export")
async def export_logs(
    query_request: LogQueryRequest,
    format: str = Query("json", description="导出格式"),
    analyzer: LogAnalyzer = Depends(get_log_analyzer)
):
    """导出日志"""
    try:
        response = analyzer.search_logs(query_request)
        
        if format == "json":
            return JSONResponse(content={
                "logs": response.logs,
                "total": response.total,
                "export_time": datetime.now().isoformat()
            })
        elif format == "csv":
            # 简单的CSV导出
            import csv
            import io
            
            output = io.StringIO()
            if response.logs:
                writer = csv.DictWriter(output, fieldnames=response.logs[0].keys())
                writer.writeheader()
                writer.writerows(response.logs)
            
            return Response(
                content=output.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=logs.csv"}
            )
        else:
            raise HTTPException(status_code=400, detail="不支持的导出格式")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出日志失败: {str(e)}")


@router.get("/health")
async def get_logs_health():
    """获取日志服务健康状态"""
    try:
        analyzer = get_log_analyzer()
        return {
            "status": "healthy",
            "log_files_count": len(analyzer.log_files),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取健康状态失败: {str(e)}")


# 监控仪表板API
dashboard_router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@dashboard_router.get("/overview")
async def get_dashboard_overview():
    """获取仪表板概览"""
    try:
        # 获取各种统计信息
        health_checker = get_health_checker()
        metrics_collector = get_metrics_collector()
        alert_engine = get_alert_engine()
        
        # 健康状态
        health_summary = health_checker.get_health_summary()
        
        # 指标摘要
        metrics_summary = metrics_collector.get_metrics_summary()
        
        # 告警摘要
        alert_summary = alert_engine.get_alert_summary()
        
        return {
            "health": health_summary,
            "metrics": metrics_summary,
            "alerts": alert_summary,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取仪表板概览失败: {str(e)}")


@dashboard_router.get("/metrics")
async def get_dashboard_metrics(
    metric_name: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None)
):
    """获取仪表板指标"""
    try:
        metrics_collector = get_metrics_collector()
        
        if metric_name:
            # 获取特定指标的历史数据
            history = metrics_collector.get_metrics_history(metric_name, start_time, end_time)
            return {
                "metric_name": metric_name,
                "history": history,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # 获取所有指标的当前值
            summary = metrics_collector.get_metrics_summary()
            return summary
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取仪表板指标失败: {str(e)}")


@dashboard_router.get("/alerts")
async def get_dashboard_alerts(
    status: Optional[str] = Query(None),
    level: Optional[str] = Query(None)
):
    """获取仪表板告警"""
    try:
        alert_engine = get_alert_engine()
        
        if status == "active":
            alerts = alert_engine.get_active_alerts()
        else:
            alerts = alert_engine.get_alert_history()
        
        # 应用过滤
        if level:
            alerts = [alert for alert in alerts if alert.level.value == level]
        
        return {
            "alerts": [
                {
                    "id": alert.id,
                    "rule_name": alert.rule_name,
                    "level": alert.level.value,
                    "message": alert.message,
                    "status": alert.status.value,
                    "timestamp": alert.timestamp.isoformat(),
                    "trigger_count": alert.trigger_count
                }
                for alert in alerts
            ],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取仪表板告警失败: {str(e)}")


# 导出路由器
def get_log_analysis_router():
    """获取日志分析路由器"""
    return router


def get_dashboard_router():
    """获取仪表板路由器"""
    return dashboard_router