# 监控系统使用指南

## 概述

本项目实现了一个完整的日志与监控系统，包含以下核心功能：

- **结构化日志记录**：支持JSON格式的结构化日志，包含丰富的上下文信息
- **健康检查机制**：自动检查系统各组件的健康状态
- **性能监控指标**：收集应用性能、系统资源和业务指标
- **告警系统**：基于规则的告警引擎，支持多种通知方式
- **日志查询分析**：提供REST API进行日志查询和分析
- **监控仪表板**：统一的监控仪表板界面

## 快速开始

### 1. 初始化监控系统

```python
from backend.src.monitoring.integration import start_all_monitoring

# 启动所有监控服务
start_all_monitoring()
```

### 2. 在服务中使用监控

```python
from backend.src.monitoring import get_logger, get_metrics_collector

# 获取日志记录器
logger = get_logger('my_service')
logger.info("服务启动", service_name="my_service")

# 获取指标收集器
metrics_collector = get_metrics_collector()
request_counter = metrics_collector.registry.counter(
    "my_service_requests_total", 
    "服务请求总数",
    {"service": "my_service"}
)
request_counter.inc()
```

### 3. 集成到现有服务

```python
from backend.src.monitoring.integration import MonitoringIntegrator

integrator = MonitoringIntegrator()

# 集成监控到服务
integration = integrator.integrate_service(
    service_name='my_service',
    health_check_func=my_health_check_function,
    alert_rules=my_custom_alert_rules
)
```

## 主要组件

### 日志系统 (logger.py)

- **Logger**: 主要的日志管理器类
- **StructuredLogger**: 结构化日志记录器
- **格式化器**: 支持JSON、彩色文本、详细格式等
- **处理器**: 支持文件、HTTP、数据库、Redis等输出方式
- **过滤器**: 敏感信息过滤、请求ID过滤等

### 健康检查 (health.py)

- **HealthChecker**: 健康检查管理器
- **DatabaseChecker**: 数据库健康检查
- **RedisChecker**: Redis健康检查
- **SystemResourceChecker**: 系统资源检查
- **HTTPChecker**: HTTP端点检查

### 指标收集 (metrics.py)

- **MetricsCollector**: 指标收集管理器
- **Counter**: 计数器指标
- **Gauge**: 仪表盘指标
- **Histogram**: 直方图指标
- **SystemMetricsCollector**: 系统指标收集器

### 告警系统 (alerts.py)

- **AlertEngine**: 告警引擎
- **AlertRule**: 告警规则定义
- **Alert**: 告警实例
- **通知器**: 邮件、Slack、Webhook通知

### 日志分析 (log_analysis.py)

- **LogAnalyzer**: 日志分析器
- **查询API**: 日志搜索和过滤
- **统计API**: 日志统计分析
- **错误分析**: 错误模式识别

## 配置文件

### monitoring.yaml
主配置文件，包含日志、健康检查、指标、告警等配置。

### logging.yaml
日志系统详细配置，包括格式化器、处理器、过滤器等。

### alerts.yaml
告警规则配置，包括告警条件、通知方式等。

## API接口

### 健康检查API
```
GET /api/v1/health/ - 获取整体健康状态
GET /api/v1/health/checks - 获取所有健康检查结果
POST /api/v1/health/check - 触发健康检查
```

### 日志查询API
```
POST /api/v1/logs/search - 搜索日志
POST /api/v1/logs/stats - 获取日志统计
GET /api/v1/logs/error-analysis - 获取错误分析
```

### 仪表板API
```
GET /api/v1/dashboard/overview - 获取仪表板概览
GET /api/v1/dashboard/metrics - 获取仪表板指标
GET /api/v1/dashboard/alerts - 获取仪表板告警
```

## 监控仪表板

启动监控仪表板：

```bash
python backend/src/monitoring/integration.py
```

仪表板将在 http://localhost:8001 启动，提供：
- 系统健康状态概览
- 实时指标图表
- 告警状态监控
- 日志查询界面

## 测试

运行监控系统测试：

```bash
python scripts/test_monitoring.py
```

测试包括：
- 日志系统功能测试
- 健康检查功能测试
- 指标收集功能测试
- 告警系统功能测试
- 日志分析功能测试
- 系统集成测试

## 性能特性

- **高性能**: 异步日志处理，支持高并发
- **低延迟**: 日志写入延迟 < 10ms（1000条/秒）
- **可扩展**: 支持多种输出方式和存储后端
- **实时性**: 支持实时日志流和指标收集
- **可靠性**: 支持日志轮转、压缩和归档

## 安全特性

- **敏感信息过滤**: 自动过滤密码、token等敏感信息
- **访问控制**: 支持基于角色的访问控制
- **审计日志**: 记录所有监控操作的审计日志
- **数据加密**: 支持日志数据加密存储

## 扩展性

系统设计为高度可扩展的架构：

- **自定义格式化器**: 可以添加新的日志格式
- **自定义处理器**: 可以添加新的日志输出方式
- **自定义检查器**: 可以添加新的健康检查类型
- **自定义指标**: 可以添加新的指标类型
- **自定义通知器**: 可以添加新的通知方式

## 故障排除

### 常见问题

1. **日志文件未创建**
   - 检查日志目录权限
   - 确保日志目录存在

2. **健康检查失败**
   - 检查数据库连接配置
   - 确认依赖服务状态

3. **指标收集异常**
   - 检查指标注册表状态
   - 确认指标收集器正常运行

4. **告警不触发**
   - 检查告警规则配置
   - 确认通知渠道配置

### 日志级别

- **DEBUG**: 调试信息，用于开发调试
- **INFO**: 一般信息，记录系统运行状态
- **WARNING**: 警告信息，记录潜在问题
- **ERROR**: 错误信息，记录错误事件
- **CRITICAL**: 严重错误，记录系统严重故障

## 最佳实践

1. **使用结构化日志**
   - 包含丰富的上下文信息
   - 使用JSON格式便于分析

2. **合理设置日志级别**
   - 生产环境使用INFO及以上级别
   - 开发环境可以使用DEBUG级别

3. **监控关键指标**
   - 请求量、响应时间、错误率
   - 系统资源使用情况

4. **配置合适的告警规则**
   - 避免告警风暴
   - 设置合理的告警阈值

5. **定期维护监控数据**
   - 清理过期的日志和指标
   - 备份重要的监控数据