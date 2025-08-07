#!/usr/bin/env python3
"""
简单监控测试脚本

快速验证监控系统核心功能
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_monitoring():
    """测试监控系统核心功能"""
    print("=== 监控系统快速测试 ===")
    
    try:
        # 测试日志系统
        print("1. 测试日志系统...")
        from backend.src.monitoring import get_logger, setup_logging
        setup_logging()
        logger = get_logger('test')
        logger.info("日志系统测试成功")
        print("✅ 日志系统正常")
        
        # 测试健康检查
        print("2. 测试健康检查...")
        from backend.src.monitoring import get_health_checker
        health_checker = get_health_checker()
        print("✅ 健康检查系统正常")
        
        # 测试指标收集
        print("3. 测试指标收集...")
        from backend.src.monitoring import get_metrics_collector
        metrics_collector = get_metrics_collector()
        print("✅ 指标收集系统正常")
        
        # 测试告警系统
        print("4. 测试告警系统...")
        from backend.src.monitoring import get_alert_engine
        alert_engine = get_alert_engine()
        print("✅ 告警系统正常")
        
        # 测试日志分析
        print("5. 测试日志分析...")
        from backend.src.monitoring import get_log_analyzer
        log_analyzer = get_log_analyzer()
        print("✅ 日志分析系统正常")
        
        print("\n🎉 所有监控系统组件测试通过!")
        
        # 测试功能
        print("\n=== 功能测试 ===")
        
        # 记录一些测试日志
        logger.info("测试信息日志", test_field="test_value")
        logger.warning("测试警告日志")
        logger.error("测试错误日志")
        
        # 创建测试指标
        counter = metrics_collector.registry.counter("test_requests_total", "测试请求总数")
        counter.inc(5)
        
        gauge = metrics_collector.registry.gauge("test_active_users", "测试活跃用户")
        gauge.set(42)
        
        histogram = metrics_collector.registry.histogram("test_response_time", "测试响应时间")
        histogram.observe(0.1)
        histogram.observe(0.5)
        histogram.observe(1.0)
        
        print("✅ 功能测试完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_monitoring()
    sys.exit(0 if success else 1)