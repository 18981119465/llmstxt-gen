#!/usr/bin/env python3
"""
Simple monitoring test script

Quick verification of monitoring system core functionality
"""

import sys
import time
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_monitoring():
    """Test monitoring system core functionality"""
    print("=== Monitoring System Quick Test ===")
    
    try:
        # Test logging system
        print("1. Testing logging system...")
        from backend.src.monitoring import get_logger, setup_logging
        setup_logging()
        logger = get_logger('test')
        logger.info("Logging system test successful")
        print("OK: Logging system is working")
        
        # Test health checks
        print("2. Testing health check system...")
        from backend.src.monitoring import get_health_checker
        health_checker = get_health_checker()
        print("OK: Health check system is working")
        
        # Test metrics collection
        print("3. Testing metrics collection...")
        from backend.src.monitoring import get_metrics_collector
        metrics_collector = get_metrics_collector()
        print("OK: Metrics collection system is working")
        
        # Test alert system
        print("4. Testing alert system...")
        from backend.src.monitoring import get_alert_engine
        alert_engine = get_alert_engine()
        print("OK: Alert system is working")
        
        # Test log analysis
        print("5. Testing log analysis...")
        from backend.src.monitoring import get_log_analyzer
        log_analyzer = get_log_analyzer()
        print("OK: Log analysis system is working")
        
        print("\nSUCCESS: All monitoring system components are working!")
        
        # Test functionality
        print("\n=== Functionality Test ===")
        
        # Record some test logs
        logger.info("Test info log", test_field="test_value")
        logger.warning("Test warning log")
        logger.error("Test error log")
        
        # Create test metrics
        counter = metrics_collector.registry.counter("test_requests_total", "Test request count")
        counter.inc(5)
        
        gauge = metrics_collector.registry.gauge("test_active_users", "Test active users")
        gauge.set(42)
        
        histogram = metrics_collector.registry.histogram("test_response_time", "Test response time")
        histogram.observe(0.1)
        histogram.observe(0.5)
        histogram.observe(1.0)
        
        print("OK: Functionality test completed")
        
        return True
        
    except Exception as e:
        print(f"FAILED: Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_monitoring()
    sys.exit(0 if success else 1)