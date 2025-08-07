"""
监控系统测试脚本

用于测试日志、健康检查、指标收集和告警功能的完整性和正确性。
"""

import asyncio
import time
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.src.monitoring import (
    get_logger, get_health_checker, get_metrics_collector, get_alert_engine,
    start_health_monitoring, start_metrics_collection, start_alert_monitoring,
    get_monitoring_config, get_log_analyzer
)
from backend.src.monitoring.alerts import AlertRule, AlertLevel
from backend.src.monitoring.health import HealthStatus
from backend.src.monitoring.log_analysis import LogQueryRequest


class MonitoringTestRunner:
    """监控测试运行器"""
    
    def __init__(self):
        self.logger = get_logger('monitoring.test')
        self.test_results = []
        self.config = get_monitoring_config()
        
    def run_all_tests(self):
        """运行所有测试"""
        self.logger.info("开始运行监控系统测试")
        
        # 测试日志系统
        self.test_logging_system()
        
        # 测试健康检查
        self.test_health_checks()
        
        # 测试指标收集
        self.test_metrics_collection()
        
        # 测试告警系统
        self.test_alert_system()
        
        # 测试日志分析
        self.test_log_analysis()
        
        # 测试系统集成
        self.test_system_integration()
        
        # 生成测试报告
        self.generate_test_report()
        
        self.logger.info("监控系统测试完成")
        
    def test_logging_system(self):
        """测试日志系统"""
        self.logger.info("测试日志系统")
        
        try:
            # 测试基础日志记录
            test_logger = get_logger('test_service')
            test_logger.info("这是一条测试信息日志", test_field="test_value")
            test_logger.warning("这是一条测试警告日志")
            test_logger.error("这是一条测试错误日志")
            test_logger.debug("这是一条测试调试日志")
            
            # 测试结构化日志
            structured_logger = get_logger('test_service.structured')
            structured_logger.info("结构化日志测试", user_id="test_user", request_id="test_request")
            
            # 测试异常日志
            try:
                raise ValueError("测试异常")
            except Exception as e:
                test_logger.exception("捕获到异常", exception_type=type(e).__name__)
            
            self.add_test_result("logging_system", True, "日志系统测试通过")
            
        except Exception as e:
            self.add_test_result("logging_system", False, f"日志系统测试失败: {str(e)}")
    
    def test_health_checks(self):
        """测试健康检查"""
        self.logger.info("测试健康检查")
        
        try:
            health_checker = get_health_checker()
            
            # 执行健康检查
            import asyncio
            results = asyncio.run(health_checker.check_all_health())
            
            # 验证检查结果
            assert isinstance(results, dict), "健康检查结果应该是字典"
            
            # 获取整体健康状态
            overall_status = health_checker.get_overall_health()
            assert overall_status in HealthStatus, "健康状态应该是有效的枚举值"
            
            # 获取健康摘要
            summary = health_checker.get_health_summary()
            assert 'overall_status' in summary, "健康摘要应包含overall_status"
            assert 'total_checks' in summary, "健康摘要应包含total_checks"
            
            self.add_test_result("health_checks", True, "健康检查测试通过")
            
        except Exception as e:
            self.add_test_result("health_checks", False, f"健康检查测试失败: {str(e)}")
    
    def test_metrics_collection(self):
        """测试指标收集"""
        self.logger.info("测试指标收集")
        
        try:
            metrics_collector = get_metrics_collector()
            
            # 获取指标注册表
            registry = metrics_collector.registry
            
            # 创建测试指标
            test_counter = registry.counter("test_counter", "测试计数器")
            test_gauge = registry.gauge("test_gauge", "测试仪表")
            test_histogram = registry.histogram("test_histogram", "测试直方图")
            
            # 测试指标操作
            test_counter.inc(10)
            test_counter.inc(5)
            test_gauge.set(42)
            test_gauge.inc(8)
            test_histogram.observe(1.5)
            test_histogram.observe(2.0)
            test_histogram.observe(0.5)
            
            # 验证指标值
            assert test_counter.get_value() == 15, "计数器值应为15"
            assert test_gauge.get_value() == 50, "仪表值应为50"
            
            # 测试指标收集
            metrics = metrics_collector.collect_metrics()
            assert len(metrics) > 0, "应收集到指标"
            
            # 测试指标摘要
            summary = metrics_collector.get_metrics_summary()
            assert 'total_metrics' in summary, "指标摘要应包含total_metrics"
            
            self.add_test_result("metrics_collection", True, "指标收集测试通过")
            
        except Exception as e:
            self.add_test_result("metrics_collection", False, f"指标收集测试失败: {str(e)}")
    
    def test_alert_system(self):
        """测试告警系统"""
        self.logger.info("测试告警系统")
        
        try:
            alert_engine = get_alert_engine()
            
            # 创建测试告警规则
            test_rule = AlertRule(
                name="test_alert_rule",
                condition="test_counter > 5",
                level=AlertLevel.WARNING,
                duration="1m",
                message="测试告警规则触发",
                tags=["test"]
            )
            
            # 添加规则
            alert_engine.add_rule(test_rule)
            
            # 验证规则已添加
            assert test_rule.name in alert_engine.rules, "告警规则应已添加"
            
            # 测试规则移除
            alert_engine.remove_rule(test_rule.name)
            assert test_rule.name not in alert_engine.rules, "告警规则应已移除"
            
            # 测试告警摘要
            summary = alert_engine.get_alert_summary()
            assert 'total_active' in summary, "告警摘要应包含total_active"
            assert 'total_history' in summary, "告警摘要应包含total_history"
            
            self.add_test_result("alert_system", True, "告警系统测试通过")
            
        except Exception as e:
            self.add_test_result("alert_system", False, f"告警系统测试失败: {str(e)}")
    
    def test_log_analysis(self):
        """测试日志分析"""
        self.logger.info("测试日志分析")
        
        try:
            log_analyzer = get_log_analyzer()
            
            # 创建测试日志查询
            query = LogQueryRequest(
                query="test",
                limit=10,
                start_time=datetime.now() - timedelta(hours=1),
                end_time=datetime.now()
            )
            
            # 测试日志搜索
            results = log_analyzer.search_logs(query)
            assert isinstance(results.logs, list), "搜索结果应该是列表"
            assert isinstance(results.total, int), "总数应该是整数"
            
            # 测试日志统计
            stats = log_analyzer.get_log_stats({
                "start_time": datetime.now() - timedelta(hours=1),
                "end_time": datetime.now(),
                "group_by": "level"
            })
            assert isinstance(stats.total_logs, int), "日志总数应该是整数"
            assert isinstance(stats.grouped_stats, dict), "分组统计应该是字典"
            
            self.add_test_result("log_analysis", True, "日志分析测试通过")
            
        except Exception as e:
            self.add_test_result("log_analysis", False, f"日志分析测试失败: {str(e)}")
    
    def test_system_integration(self):
        """测试系统集成"""
        self.logger.info("测试系统集成")
        
        try:
            # 测试配置加载
            config = get_monitoring_config()
            assert config is not None, "监控配置不应为空"
            
            # 测试各个组件的获取
            health_checker = get_health_checker()
            metrics_collector = get_metrics_collector()
            alert_engine = get_alert_engine()
            
            assert health_checker is not None, "健康检查器不应为空"
            assert metrics_collector is not None, "指标收集器不应为空"
            assert alert_engine is not None, "告警引擎不应为空"
            
            # 测试组件之间的协调
            # 健康检查应能正常执行
            import asyncio
            health_results = asyncio.run(health_checker.check_all_health())
            assert isinstance(health_results, dict), "健康检查结果应为字典"
            
            # 指标收集应能正常工作
            metrics = metrics_collector.collect_metrics()
            assert len(metrics) > 0, "应能收集到指标"
            
            self.add_test_result("system_integration", True, "系统集成测试通过")
            
        except Exception as e:
            self.add_test_result("system_integration", False, f"系统集成测试失败: {str(e)}")
    
    def add_test_result(self, test_name: str, success: bool, message: str):
        """添加测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        if success:
            self.logger.info(f"测试通过: {test_name}")
        else:
            self.logger.error(f"测试失败: {test_name} - {message}")
    
    def generate_test_report(self):
        """生成测试报告"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "timestamp": datetime.now().isoformat()
            },
            "test_results": self.test_results
        }
        
        # 保存测试报告
        report_file = project_root / "test_results" / "monitoring_test_report.json"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"测试报告已保存到: {report_file}")
        
        # 输出测试摘要
        print(f"\n=== 监控系统测试报告 ===")
        print(f"总测试数: {total_tests}")
        print(f"通过测试: {passed_tests}")
        print(f"失败测试: {failed_tests}")
        print(f"成功率: {report['test_summary']['success_rate']:.1f}%")
        print(f"详细报告: {report_file}")
        
        if failed_tests > 0:
            print(f"\n失败的测试:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test_name']}: {result['message']}")


def test_performance():
    """性能测试"""
    print("开始性能测试...")
    
    try:
        import time
        
        # 测试日志性能
        logger = get_logger('performance_test')
        start_time = time.time()
        
        for i in range(1000):
            logger.info(f"性能测试日志 {i}", iteration=i)
        
        log_time = time.time() - start_time
        print(f"日志性能测试: 1000条日志耗时 {log_time:.2f}秒")
        
        # 测试指标性能
        metrics_collector = get_metrics_collector()
        counter = metrics_collector.registry.counter("performance_counter")
        
        start_time = time.time()
        for i in range(1000):
            counter.inc()
        
        metrics_time = time.time() - start_time
        print(f"指标性能测试: 1000次操作耗时 {metrics_time:.2f}秒")
        
        # 测试健康检查性能
        health_checker = get_health_checker()
        start_time = time.time()
        
        for i in range(10):
            asyncio.run(health_checker.check_all_health())
        
        health_time = time.time() - start_time
        print(f"健康检查性能测试: 10次检查耗时 {health_time:.2f}秒")
        
    except Exception as e:
        print(f"性能测试失败: {e}")


def main():
    """主函数"""
    try:
        print("=== 监控系统测试 ===")
        
        # 初始化监控系统
        from backend.src.monitoring.integration import start_all_monitoring
        start_all_monitoring()
        
        # 等待监控系统启动
        time.sleep(5)
        
        # 运行功能测试
        test_runner = MonitoringTestRunner()
        test_runner.run_all_tests()
        
        # 运行性能测试
        test_performance()
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"测试运行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()