"""
告警系统模块

提供错误告警和异常处理功能，包括告警规则引擎、通知机制等。
"""

import asyncio
import time
import threading
import json
import smtplib
import requests
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import queue
import re
from collections import defaultdict, deque

from .config import get_monitoring_config, MonitoringConfig
from .logger import get_logger
from .metrics import get_metrics_collector


class AlertLevel(Enum):
    """告警级别枚举"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """告警状态枚举"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"
    EXPIRED = "expired"


@dataclass
class AlertRule:
    """告警规则"""
    name: str
    condition: str
    level: AlertLevel
    duration: str = "1m"
    enabled: bool = True
    message: str = ""
    tags: List[str] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """告警"""
    id: str
    rule_name: str
    level: AlertLevel
    message: str
    status: AlertStatus
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    resolved_at: Optional[datetime] = None
    first_triggered: Optional[datetime] = None
    trigger_count: int = 0


@dataclass
class NotificationChannel:
    """通知渠道"""
    name: str
    type: str
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    recipients: List[str] = field(default_factory=list)


class EmailNotifier:
    """邮件通知器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger('alerts.email')
    
    def send_notification(self, alert: Alert, recipients: List[str]):
        """发送邮件通知"""
        try:
            # 创建邮件内容
            msg = MIMEMultipart()
            msg['From'] = self.config.get('username')
            msg['To'] = ', '.join(resipients)
            msg['Subject'] = f"[{alert.level.value.upper()}] {alert.rule_name}"
            
            # 邮件正文
            body = self._create_email_body(alert)
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            
            # 发送邮件
            server = smtplib.SMTP(
                self.config.get('smtp_server', 'smtp.gmail.com'),
                self.config.get('smtp_port', 587)
            )
            server.starttls()
            server.login(self.config.get('username'), self.config.get('password'))
            
            text = msg.as_string()
            server.sendmail(self.config.get('username'), recipients, text)
            server.quit()
            
            self.logger.info("邮件通知发送成功", alert_id=alert.id, recipients=len(recipients))
            
        except Exception as e:
            self.logger.error("邮件通知发送失败", alert_id=alert.id, error=str(e))
    
    def _create_email_body(self, alert: Alert) -> str:
        """创建邮件正文"""
        return f"""
        <html>
        <body>
            <h2>🚨 {alert.level.value.upper()} 告警</h2>
            <table border="1" style="border-collapse: collapse;">
                <tr>
                    <td><strong>规则名称</strong></td>
                    <td>{alert.rule_name}</td>
                </tr>
                <tr>
                    <td><strong>告警级别</strong></td>
                    <td>{alert.level.value}</td>
                </tr>
                <tr>
                    <td><strong>告警消息</strong></td>
                    <td>{alert.message}</td>
                </tr>
                <tr>
                    <td><strong>触发时间</strong></td>
                    <td>{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td>
                </tr>
                <tr>
                    <td><strong>告警状态</strong></td>
                    <td>{alert.status.value}</td>
                </tr>
                <tr>
                    <td><strong>触发次数</strong></td>
                    <td>{alert.trigger_count}</td>
                </tr>
            </table>
            <br>
            <p><strong>元数据:</strong></p>
            <pre>{json.dumps(alert.metadata, indent=2, ensure_ascii=False)}</pre>
        </body>
        </html>
        """


class SlackNotifier:
    """Slack通知器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger('alerts.slack')
    
    def send_notification(self, alert: Alert, channel: str = "#alerts"):
        """发送Slack通知"""
        try:
            webhook_url = self.config.get('webhook_url')
            if not webhook_url:
                self.logger.warning("Slack webhook URL未配置")
                return
            
            # 创建Slack消息
            color_map = {
                AlertLevel.DEBUG: "#36a64f",
                AlertLevel.INFO: "#36a64f",
                AlertLevel.WARNING: "#ff9500",
                AlertLevel.ERROR: "#ff4d4f",
                AlertLevel.CRITICAL: "#722ed1"
            }
            
            payload = {
                "channel": channel,
                "attachments": [
                    {
                        "color": color_map.get(alert.level, "#36a64f"),
                        "title": f"🚨 {alert.level.value.upper()} - {alert.rule_name}",
                        "text": alert.message,
                        "fields": [
                            {
                                "title": "状态",
                                "value": alert.status.value,
                                "short": True
                            },
                            {
                                "title": "触发时间",
                                "value": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                                "short": True
                            },
                            {
                                "title": "触发次数",
                                "value": str(alert.trigger_count),
                                "short": True
                            }
                        ],
                        "footer": "监控系统",
                        "ts": int(alert.timestamp.timestamp())
                    }
                ]
            }
            
            # 发送消息
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            self.logger.info("Slack通知发送成功", alert_id=alert.id)
            
        except Exception as e:
            self.logger.error("Slack通知发送失败", alert_id=alert.id, error=str(e))


class WebhookNotifier:
    """Webhook通知器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger('alerts.webhook')
    
    def send_notification(self, alert: Alert):
        """发送Webhook通知"""
        try:
            url = self.config.get('url')
            if not url:
                self.logger.warning("Webhook URL未配置")
                return
            
            headers = self.config.get('headers', {})
            headers.setdefault('Content-Type', 'application/json')
            
            # 创建webhook payload
            payload = {
                "alert_id": alert.id,
                "rule_name": alert.rule_name,
                "level": alert.level.value,
                "message": alert.message,
                "status": alert.status.value,
                "timestamp": alert.timestamp.isoformat(),
                "metadata": alert.metadata,
                "tags": alert.tags,
                "trigger_count": alert.trigger_count
            }
            
            # 发送webhook
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            
            self.logger.info("Webhook通知发送成功", alert_id=alert.id)
            
        except Exception as e:
            self.logger.error("Webhook通知发送失败", alert_id=alert.id, error=str(e))


class AlertEngine:
    """告警引擎"""
    
    def __init__(self, config: Optional[MonitoringConfig] = None):
        self.config = config or get_monitoring_config()
        self.logger = get_logger('alerts.engine')
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=10000)
        self.notifiers: Dict[str, Union[EmailNotifier, SlackNotifier, WebhookNotifier]] = {}
        self.running = False
        self.evaluation_thread = None
        
        # 初始化通知器
        self._init_notifiers()
        
        # 加载告警规则
        self._load_rules()
    
    def _init_notifiers(self):
        """初始化通知器"""
        for notification_config in self.config.alerts.notifications:
            notifier_type = notification_config.get('type')
            if notifier_type == 'email' and notification_config.get('enabled'):
                self.notifiers['email'] = EmailNotifier(notification_config)
            elif notifier_type == 'slack' and notification_config.get('enabled'):
                self.notifiers['slack'] = SlackNotifier(notification_config)
            elif notifier_type == 'webhook' and notification_config.get('enabled'):
                self.notifiers['webhook'] = WebhookNotifier(notification_config)
    
    def _load_rules(self):
        """加载告警规则"""
        # 从配置文件加载规则
        for rule_config in self.config.alerts.rules:
            rule = AlertRule(
                name=rule_config['name'],
                condition=rule_config['condition'],
                level=AlertLevel(rule_config['level']),
                duration=rule_config.get('duration', '1m'),
                enabled=rule_config.get('enabled', True),
                message=rule_config.get('message', ''),
                tags=rule_config.get('tags', []),
                actions=rule_config.get('actions', []),
                metadata=rule_config.get('metadata', {})
            )
            self.rules[rule.name] = rule
    
    def add_rule(self, rule: AlertRule):
        """添加告警规则"""
        self.rules[rule.name] = rule
        self.logger.info("告警规则已添加", rule_name=rule.name)
    
    def remove_rule(self, rule_name: str):
        """移除告警规则"""
        if rule_name in self.rules:
            del self.rules[rule_name]
            # 清理相关的活跃告警
            if rule_name in self.active_alerts:
                del self.active_alerts[rule_name]
            self.logger.info("告警规则已移除", rule_name=rule_name)
    
    def evaluate_rules(self):
        """评估告警规则"""
        try:
            # 获取当前指标
            metrics_collector = get_metrics_collector()
            current_metrics = metrics_collector.collect_metrics()
            
            # 转换为指标字典
            metrics_dict = {}
            for metric in current_metrics:
                key = f"{metric.name}_{json.dumps(metric.tags, sort_keys=True)}"
                metrics_dict[key] = metric.value
            
            # 评估每个规则
            for rule_name, rule in self.rules.items():
                if not rule.enabled:
                    continue
                
                try:
                    self._evaluate_rule(rule, metrics_dict)
                except Exception as e:
                    self.logger.error("评估告警规则失败", rule_name=rule_name, error=str(e))
        
        except Exception as e:
            self.logger.error("评估告警规则时发生异常", error=str(e))
    
    def _evaluate_rule(self, rule: AlertRule, metrics_dict: Dict[str, float]):
        """评估单个告警规则"""
        # 解析条件
        condition_result = self._evaluate_condition(rule.condition, metrics_dict)
        
        if condition_result:
            # 条件满足，触发告警
            self._trigger_alert(rule, metrics_dict)
        else:
            # 条件不满足，尝试解决告警
            self._resolve_alert(rule.name)
    
    def _evaluate_condition(self, condition: str, metrics_dict: Dict[str, float]) -> bool:
        """评估条件表达式"""
        try:
            # 替换指标变量
            eval_expression = condition
            
            # 处理常见的指标模式
            import re
            
            # 替换 system.cpu.usage > 80 这样的表达式
            pattern = r'([a-zA-Z_][a-zA-Z0-9_.]*)\s*([><=!]+)\s*([0-9.]+)'
            matches = re.findall(pattern, condition)
            
            for metric_name, operator, value in matches:
                # 查找匹配的指标
                for key, metric_value in metrics_dict.items():
                    if metric_name in key:
                        eval_expression = eval_expression.replace(
                            f"{metric_name} {operator} {value}",
                            f"{metric_value} {operator} {value}"
                        )
                        break
            
            # 安全评估表达式
            allowed_names = {}
            allowed_names.update(metrics_dict)
            allowed_names.update({
                'True': True, 'False': False, 'None': None,
                'and': lambda x, y: x and y,
                'or': lambda x, y: x or y,
                'not': lambda x: not x
            })
            
            code = compile(eval_expression, '<string>', 'eval')
            result = eval(code, {"__builtins__": {}}, allowed_names)
            
            return bool(result)
        
        except Exception as e:
            self.logger.error("评估条件表达式失败", condition=condition, error=str(e))
            return False
    
    def _trigger_alert(self, rule: AlertRule, metrics_dict: Dict[str, float]):
        """触发告警"""
        current_time = datetime.now()
        
        if rule.name in self.active_alerts:
            # 告警已存在，更新触发次数
            alert = self.active_alerts[rule.name]
            alert.trigger_count += 1
            alert.metadata['last_metrics'] = metrics_dict
            alert.timestamp = current_time
        else:
            # 创建新告警
            alert = Alert(
                id=f"{rule.name}_{int(current_time.timestamp())}",
                rule_name=rule.name,
                level=rule.level,
                message=rule.message or f"告警规则 {rule.name} 触发",
                status=AlertStatus.ACTIVE,
                timestamp=current_time,
                first_triggered=current_time,
                trigger_count=1,
                metadata={'metrics': metrics_dict},
                tags=rule.tags
            )
            self.active_alerts[rule.name] = alert
            
            # 发送通知
            self._send_notifications(alert)
            
            self.logger.warning("新告警触发", alert_id=alert.id, rule_name=rule.name)
    
    def _resolve_alert(self, rule_name: str):
        """解决告警"""
        if rule_name in self.active_alerts:
            alert = self.active_alerts[rule_name]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now()
            
            # 移到历史记录
            self.alert_history.append(alert)
            del self.active_alerts[rule_name]
            
            self.logger.info("告警已解决", alert_id=alert.id, rule_name=rule_name)
    
    def _send_notifications(self, alert: Alert):
        """发送告警通知"""
        for notifier_name, notifier in self.notifiers.items():
            try:
                if isinstance(notifier, EmailNotifier):
                    recipients = self.config.alerts.notifications[0].get('recipients', [])
                    if recipients:
                        notifier.send_notification(alert, recipients)
                elif isinstance(notifier, SlackNotifier):
                    notifier.send_notification(alert)
                elif isinstance(notifier, WebhookNotifier):
                    notifier.send_notification(alert)
            except Exception as e:
                self.logger.error("发送告警通知失败", notifier=notifier_name, error=str(e))
    
    def start_monitoring(self):
        """启动告警监控"""
        if self.running:
            return
        
        self.running = True
        
        def monitoring_loop():
            while self.running:
                try:
                    # 评估告警规则
                    self.evaluate_rules()
                    
                    # 清理过期的活跃告警
                    self._cleanup_expired_alerts()
                    
                except Exception as e:
                    self.logger.error("告警监控异常", error=str(e))
                
                # 等待下一次评估
                time.sleep(60)  # 每分钟评估一次
        
        self.evaluation_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self.evaluation_thread.start()
        self.logger.info("告警监控已启动")
    
    def stop_monitoring(self):
        """停止告警监控"""
        self.running = False
        if self.evaluation_thread:
            self.evaluation_thread.join()
        self.logger.info("告警监控已停止")
    
    def _cleanup_expired_alerts(self):
        """清理过期的活跃告警"""
        current_time = datetime.now()
        expired_alerts = []
        
        for rule_name, alert in self.active_alerts.items():
            # 如果告警活跃超过24小时，标记为过期
            if (current_time - alert.timestamp).total_seconds() > 24 * 3600:
                expired_alerts.append(rule_name)
        
        for rule_name in expired_alerts:
            alert = self.active_alerts[rule_name]
            alert.status = AlertStatus.EXPIRED
            self.alert_history.append(alert)
            del self.active_alerts[rule_name]
            self.logger.warning("告警已过期", alert_id=alert.id, rule_name=rule_name)
    
    def get_active_alerts(self) -> List[Alert]:
        """获取活跃告警"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """获取告警历史"""
        return list(self.alert_history)[-limit:]
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """获取告警摘要"""
        active_alerts = self.get_active_alerts()
        alert_history = self.get_alert_history()
        
        # 按级别统计
        level_stats = defaultdict(int)
        for alert in active_alerts:
            level_stats[alert.level.value] += 1
        
        return {
            'total_active': len(active_alerts),
            'total_history': len(alert_history),
            'active_by_level': dict(level_stats),
            'timestamp': datetime.now().isoformat()
        }


# 全局告警引擎实例
_alert_engine: Optional[AlertEngine] = None


def get_alert_engine() -> AlertEngine:
    """获取全局告警引擎实例"""
    global _alert_engine
    if _alert_engine is None:
        _alert_engine = AlertEngine()
    return _alert_engine


def start_alert_monitoring():
    """启动告警监控"""
    engine = get_alert_engine()
    engine.start_monitoring()


def stop_alert_monitoring():
    """停止告警监控"""
    engine = get_alert_engine()
    engine.stop_monitoring()