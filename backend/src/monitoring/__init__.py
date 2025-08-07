"""
监控系统模块

提供统一的日志记录、健康检查、性能监控和告警功能。
"""

from .logger import (
    Logger,
    get_logger,
    StructuredLogger,
    setup_logging,
    configure_logging
)

from .health import (
    HealthChecker,
    HealthCheck,
    HealthStatus,
    get_health_checker
)

from .metrics import (
    MetricsCollector,
    MetricsRegistry,
    Counter,
    Gauge,
    Histogram,
    get_metrics_collector
)

from .alerts import (
    AlertEngine,
    AlertRule,
    Alert,
    AlertLevel,
    AlertStatus,
    NotificationChannel,
    get_alert_engine,
    start_alert_monitoring,
    stop_alert_monitoring
)

from .log_analysis import (
    LogAnalyzer,
    LogQueryRequest,
    LogResponse,
    LogStatsRequest,
    LogStatsResponse,
    get_log_analyzer,
    get_log_analysis_router,
    get_dashboard_router
)

from .health_api import router as health_router

from .config import (
    MonitoringConfig,
    get_monitoring_config,
    load_monitoring_config
)

__version__ = "1.0.0"
__all__ = [
    # Logger
    "Logger",
    "get_logger", 
    "StructuredLogger",
    "setup_logging",
    "configure_logging",
    
    # Health
    "HealthChecker",
    "HealthCheck", 
    "HealthStatus",
    "get_health_checker",
    "health_router",
    
    # Metrics
    "MetricsCollector",
    "MetricsRegistry",
    "Counter",
    "Gauge", 
    "Histogram",
    "get_metrics_collector",
    
    # Alerts
    "AlertEngine",
    "AlertRule",
    "Alert",
    "AlertLevel",
    "AlertStatus",
    "NotificationChannel",
    "get_alert_engine",
    "start_alert_monitoring",
    "stop_alert_monitoring",
    
    # Log Analysis
    "LogAnalyzer",
    "LogQueryRequest",
    "LogResponse",
    "LogStatsRequest",
    "LogStatsResponse",
    "get_log_analyzer",
    "get_log_analysis_router",
    "get_dashboard_router",
    
    # Config
    "MonitoringConfig",
    "get_monitoring_config",
    "load_monitoring_config"
]