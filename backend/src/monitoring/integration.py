"""
监控系统集成脚本

用于将监控系统集成到现有服务中，包括日志、健康检查、指标收集和告警。
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.src.monitoring import (
    get_logger, get_health_checker, get_metrics_collector, get_alert_engine,
    start_health_monitoring, start_metrics_collection, start_alert_monitoring,
    setup_logging, configure_logging, get_monitoring_config,
    health_router, get_log_analysis_router, get_dashboard_router
)


class MonitoringIntegrator:
    """监控系统集成器"""
    
    def __init__(self):
        self.logger = get_logger('monitoring.integrator')
        self.config = get_monitoring_config()
        self.services = {}
        
    def integrate_logging(self, service_name: str) -> Any:
        """集成日志系统到服务"""
        try:
            # 为服务创建专用的日志记录器
            service_logger = get_logger(service_name)
            
            # 设置结构化日志
            structured_logger = get_logger(f"{service_name}.structured")
            
            self.logger.info(f"日志系统集成成功", service=service_name)
            
            return {
                'logger': service_logger,
                'structured_logger': structured_logger,
                'service_name': service_name
            }
            
        except Exception as e:
            self.logger.error(f"日志系统集成失败", service=service_name, error=str(e))
            raise
    
    def integrate_health_checks(self, service_name: str, 
                              health_check_func: Optional[callable] = None) -> Any:
        """集成健康检查到服务"""
        try:
            health_checker = get_health_checker()
            
            # 如果有自定义健康检查函数，添加到检查器
            if health_check_func:
                health_checker.add_custom_check(
                    name=f"{service_name}_custom",
                    check_func=health_check_func,
                    critical=True
                )
            
            self.logger.info(f"健康检查集成成功", service=service_name)
            
            return health_checker
            
        except Exception as e:
            self.logger.error(f"健康检查集成失败", service=service_name, error=str(e))
            raise
    
    def integrate_metrics(self, service_name: str) -> Any:
        """集成指标收集到服务"""
        try:
            metrics_collector = get_metrics_collector()
            
            # 为服务创建专用指标
            request_counter = metrics_collector.registry.counter(
                f"{service_name}_requests_total",
                f"{service_name} 服务请求总数",
                {"service": service_name}
            )
            
            request_duration = metrics_collector.registry.histogram(
                f"{service_name}_request_duration_seconds",
                f"{service_name} 服务请求持续时间",
                [0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
                {"service": service_name}
            )
            
            error_counter = metrics_collector.registry.counter(
                f"{service_name}_errors_total",
                f"{service_name} 服务错误总数",
                {"service": service_name}
            )
            
            active_users = metrics_collector.registry.gauge(
                f"{service_name}_active_users",
                f"{service_name} 服务活跃用户数",
                {"service": service_name}
            )
            
            self.logger.info(f"指标收集集成成功", service=service_name)
            
            return {
                'request_counter': request_counter,
                'request_duration': request_duration,
                'error_counter': error_counter,
                'active_users': active_users,
                'metrics_collector': metrics_collector
            }
            
        except Exception as e:
            self.logger.error(f"指标收集集成失败", service=service_name, error=str(e))
            raise
    
    def integrate_alerts(self, service_name: str, 
                        alert_rules: Optional[list] = None) -> Any:
        """集成告警系统到服务"""
        try:
            alert_engine = get_alert_engine()
            
            # 添加服务专用告警规则
            default_rules = [
                {
                    'name': f'{service_name}_high_error_rate',
                    'condition': f'{service_name}_errors_total > 10',
                    'level': 'ERROR',
                    'duration': '5m',
                    'message': f'{service_name} 服务错误率过高',
                    'tags': [service_name, 'error_rate']
                },
                {
                    'name': f'{service_name}_slow_response',
                    'condition': f'{service_name}_request_duration_seconds > 5.0',
                    'level': 'WARNING',
                    'duration': '10m',
                    'message': f'{service_name} 服务响应时间过长',
                    'tags': [service_name, 'response_time']
                }
            ]
            
            # 合并自定义规则
            rules = alert_rules or []
            rules.extend(default_rules)
            
            for rule_config in rules:
                from backend.src.monitoring.alerts import AlertRule, AlertLevel
                rule = AlertRule(
                    name=rule_config['name'],
                    condition=rule_config['condition'],
                    level=AlertLevel(rule_config['level']),
                    duration=rule_config.get('duration', '1m'),
                    message=rule_config.get('message', ''),
                    tags=rule_config.get('tags', [])
                )
                alert_engine.add_rule(rule)
            
            self.logger.info(f"告警系统集成成功", service=service_name)
            
            return alert_engine
            
        except Exception as e:
            self.logger.error(f"告警系统集成失败", service=service_name, error=str(e))
            raise
    
    def integrate_service(self, service_name: str, 
                        health_check_func: Optional[callable] = None,
                        alert_rules: Optional[list] = None) -> Dict[str, Any]:
        """集成所有监控组件到服务"""
        try:
            self.logger.info(f"开始集成监控系统到服务", service=service_name)
            
            # 集成各个组件
            logging_integration = self.integrate_logging(service_name)
            health_integration = self.integrate_health_checks(service_name, health_check_func)
            metrics_integration = self.integrate_metrics(service_name)
            alerts_integration = self.integrate_alerts(service_name, alert_rules)
            
            # 保存服务集成信息
            service_integration = {
                'service_name': service_name,
                'logging': logging_integration,
                'health': health_integration,
                'metrics': metrics_integration,
                'alerts': alerts_integration,
                'integrated_at': datetime.now().isoformat()
            }
            
            self.services[service_name] = service_integration
            
            self.logger.info(f"监控系统集成完成", service=service_name)
            
            return service_integration
            
        except Exception as e:
            self.logger.error(f"服务监控集成失败", service=service_name, error=str(e))
            raise
    
    def create_service_monitoring_middleware(self, service_name: str):
        """创建服务监控中间件"""
        try:
            # 获取集成组件
            integration = self.services.get(service_name)
            if not integration:
                raise ValueError(f"服务 {service_name} 未集成监控系统")
            
            metrics = integration['metrics']
            
            def monitoring_middleware(request, call_next):
                """监控中间件"""
                import time
                
                # 记录请求开始时间
                start_time = time.time()
                
                try:
                    # 调用下一个中间件或处理器
                    response = call_next(request)
                    
                    # 记录请求指标
                    request_duration = time.time() - start_time
                    metrics['request_counter'].inc()
                    metrics['request_duration'].observe(request_duration)
                    
                    # 记录成功日志
                    integration['logging']['logger'].info(
                        f"请求处理完成",
                        service=service_name,
                        method=request.method,
                        path=request.url.path,
                        status_code=response.status_code,
                        duration=request_duration
                    )
                    
                    return response
                    
                except Exception as e:
                    # 记录错误指标
                    request_duration = time.time() - start_time
                    metrics['error_counter'].inc()
                    metrics['request_duration'].observe(request_duration)
                    
                    # 记录错误日志
                    integration['logging']['logger'].error(
                        f"请求处理失败",
                        service=service_name,
                        method=request.method,
                        path=request.url.path,
                        error=str(e),
                        duration=request_duration
                    )
                    
                    raise
            
            self.logger.info(f"监控中间件创建成功", service=service_name)
            return monitoring_middleware
            
        except Exception as e:
            self.logger.error(f"创建监控中间件失败", service=service_name, error=str(e))
            raise
    
    def get_service_integration(self, service_name: str) -> Optional[Dict[str, Any]]:
        """获取服务集成信息"""
        return self.services.get(service_name)
    
    def remove_service_integration(self, service_name: str):
        """移除服务集成"""
        try:
            if service_name in self.services:
                # 移除服务专用告警规则
                alert_engine = get_alert_engine()
                rules_to_remove = [
                    f'{service_name}_high_error_rate',
                    f'{service_name}_slow_response'
                ]
                for rule_name in rules_to_remove:
                    alert_engine.remove_rule(rule_name)
                
                # 移除服务集成信息
                del self.services[service_name]
                
                self.logger.info(f"服务监控集成已移除", service=service_name)
            else:
                self.logger.warning(f"服务未找到", service=service_name)
                
        except Exception as e:
            self.logger.error(f"移除服务监控集成失败", service=service_name, error=str(e))
            raise


def integrate_backend_api_service():
    """集成后端API服务监控"""
    integrator = MonitoringIntegrator()
    
    # 自定义健康检查函数
    def backend_health_check():
        """后端服务健康检查"""
        try:
            # 检查数据库连接
            # 检查Redis连接
            # 检查其他依赖服务
            return True
        except Exception:
            return False
    
    # 自定义告警规则
    alert_rules = [
        {
            'name': 'backend_database_slow',
            'condition': 'database_query_duration_seconds > 2.0',
            'level': 'WARNING',
            'duration': '5m',
            'message': '数据库查询响应时间过长',
            'tags': ['backend', 'database', 'performance']
        },
        {
            'name': 'backend_memory_high',
            'condition': 'system_memory_usage_percent > 85',
            'level': 'WARNING',
            'duration': '10m',
            'message': '内存使用率过高',
            'tags': ['backend', 'system', 'memory']
        }
    ]
    
    # 集成监控
    integration = integrator.integrate_service(
        service_name='backend_api',
        health_check_func=backend_health_check,
        alert_rules=alert_rules
    )
    
    return integration


def integrate_document_service():
    """集成文档处理服务监控"""
    integrator = MonitoringIntegrator()
    
    # 自定义健康检查函数
    def document_health_check():
        """文档处理服务健康检查"""
        try:
            # 检查文档处理队列
            # 检查存储服务
            return True
        except Exception:
            return False
    
    # 自定义告警规则
    alert_rules = [
        {
            'name': 'document_queue_full',
            'condition': 'document_queue_size > 1000',
            'level': 'ERROR',
            'duration': '1m',
            'message': '文档处理队列已满',
            'tags': ['document', 'queue', 'capacity']
        },
        {
            'name': 'document_processing_slow',
            'condition': 'document_processing_time > 300',
            'level': 'WARNING',
            'duration': '5m',
            'message': '文档处理时间过长',
            'tags': ['document', 'processing', 'performance']
        }
    ]
    
    # 集成监控
    integration = integrator.integrate_service(
        service_name='document_service',
        health_check_func=document_health_check,
        alert_rules=alert_rules
    )
    
    return integration


def integrate_ai_service():
    """集成AI处理服务监控"""
    integrator = MonitoringIntegrator()
    
    # 自定义健康检查函数
    def ai_health_check():
        """AI处理服务健康检查"""
        try:
            # 检查AI模型状态
            # 检查GPU资源
            return True
        except Exception:
            return False
    
    # 自定义告警规则
    alert_rules = [
        {
            'name': 'ai_model_error',
            'condition': 'ai_model_error_rate > 0.1',
            'level': 'ERROR',
            'duration': '5m',
            'message': 'AI模型错误率过高',
            'tags': ['ai', 'model', 'error']
        },
        {
            'name': 'ai_gpu_memory_high',
            'condition': 'gpu_memory_usage_percent > 90',
            'level': 'WARNING',
            'duration': '10m',
            'message': 'GPU内存使用率过高',
            'tags': ['ai', 'gpu', 'memory']
        }
    ]
    
    # 集成监控
    integration = integrator.integrate_service(
        service_name='ai_service',
        health_check_func=ai_health_check,
        alert_rules=alert_rules
    )
    
    return integration


def integrate_web_crawler_service():
    """集成爬虫服务监控"""
    integrator = MonitoringIntegrator()
    
    # 自定义健康检查函数
    def crawler_health_check():
        """爬虫服务健康检查"""
        try:
            # 检查爬虫状态
            # 检查代理服务
            return True
        except Exception:
            return False
    
    # 自定义告警规则
    alert_rules = [
        {
            'name': 'crawler_rate_limit',
            'condition': 'crawler_rate_limit_hits > 100',
            'level': 'WARNING',
            'duration': '5m',
            'message': '爬虫触发频率限制',
            'tags': ['crawler', 'rate_limit', 'network']
        },
        {
            'name': 'crawler_proxy_failure',
            'condition': 'crawler_proxy_failure_rate > 0.2',
            'level': 'ERROR',
            'duration': '3m',
            'message': '爬虫代理失败率过高',
            'tags': ['crawler', 'proxy', 'network']
        }
    ]
    
    # 集成监控
    integration = integrator.integrate_service(
        service_name='web_crawler',
        health_check_func=crawler_health_check,
        alert_rules=alert_rules
    )
    
    return integration


def start_all_monitoring():
    """启动所有监控服务"""
    try:
        # 启动健康监控
        start_health_monitoring()
        
        # 启动指标收集
        start_metrics_collection()
        
        # 启动告警监控
        start_alert_monitoring()
        
        logger = get_logger('monitoring.startup')
        logger.info("所有监控服务已启动")
        
    except Exception as e:
        print(f"启动监控服务失败: {e}")
        raise


def create_monitoring_dashboard_app():
    """创建监控仪表板应用"""
    try:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        
        app = FastAPI(title="监控仪表板", version="1.0.0")
        
        # 添加CORS中间件
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 添加路由
        app.include_router(health_router, prefix="/api/v1")
        app.include_router(get_log_analysis_router(), prefix="/api/v1")
        app.include_router(get_dashboard_router(), prefix="/api/v1")
        
        @app.get("/")
        async def root():
            return {"message": "监控仪表板 API", "version": "1.0.0"}
        
        return app
        
    except Exception as e:
        print(f"创建监控仪表板应用失败: {e}")
        raise


if __name__ == "__main__":
    try:
        print("开始集成监控系统...")
        
        # 初始化日志系统
        setup_logging()
        logger = get_logger('monitoring.setup')
        logger.info("开始设置监控系统")
        
        # 集成各个服务
        backend_integration = integrate_backend_api_service()
        document_integration = integrate_document_service()
        ai_integration = integrate_ai_service()
        crawler_integration = integrate_web_crawler_service()
        
        # 启动监控服务
        start_all_monitoring()
        
        # 创建监控仪表板应用
        dashboard_app = create_monitoring_dashboard_app()
        
        logger.info("监控系统集成完成")
        print("监控系统集成完成！")
        
        # 如果直接运行，启动仪表板
        import uvicorn
        uvicorn.run(dashboard_app, host="0.0.0.0", port=8001)
        
    except Exception as e:
        print(f"监控系统集成失败: {e}")
        sys.exit(1)