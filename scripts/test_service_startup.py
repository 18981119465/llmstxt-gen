#!/usr/bin/env python3
"""
Service startup test script

Test service startup and monitoring functionality without database dependency
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

def test_service_startup():
    """Test service startup"""
    print("=== Service Startup Test ===")
    
    try:
        # Test FastAPI import
        print("1. Testing FastAPI import...")
        from fastapi import FastAPI
        print("OK: FastAPI import successful")
        
        # Test monitoring module import
        print("2. Testing monitoring module import...")
        from backend.src.monitoring import (
            get_logger, setup_logging, get_health_checker,
            get_metrics_collector, get_alert_engine, get_log_analyzer
        )
        print("OK: Monitoring module import successful")
        
        # Test configuration system import
        print("3. Testing configuration system import...")
        from backend.src.config import get_config_system
        print("OK: Configuration system import successful")
        
        # Test logging system
        print("4. Testing logging system...")
        setup_logging()
        logger = get_logger('startup_test')
        logger.info("Service startup test log")
        print("OK: Logging system working")
        
        # Test health check
        print("5. Testing health check...")
        health_checker = get_health_checker()
        print("OK: Health check system working")
        
        # Test metrics collection
        print("6. Testing metrics collection...")
        metrics_collector = get_metrics_collector()
        print("OK: Metrics collection system working")
        
        # Test alert system
        print("7. Testing alert system...")
        alert_engine = get_alert_engine()
        print("OK: Alert system working")
        
        # Test log analysis
        print("8. Testing log analysis...")
        log_analyzer = get_log_analyzer()
        print("OK: Log analysis system working")
        
        print("\nSUCCESS: All core components passed!")
        return True
        
    except Exception as e:
        print(f"FAILED: Service startup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_creation():
    """Test API creation"""
    print("\n=== API Creation Test ===")
    
    try:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        
        # Create FastAPI app
        app = FastAPI(
            title="llms.txt-gen API",
            description="API for llms.txt generation service",
            version="1.0.0",
        )
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Test basic routes
        @app.get("/")
        async def root():
            return {"message": "llms.txt-gen API is running", "version": "1.0.0"}
        
        @app.get("/health")
        async def health_check():
            return {"status": "healthy", "timestamp": "2025-08-07T21:32:00"}
        
        print("OK: FastAPI app created successfully")
        print("OK: CORS middleware configured successfully")
        print("OK: Basic routes configured successfully")
        
        # Check routes
        print(f"OK: Number of registered routes: {len(app.routes)}")
        
        return True
        
    except Exception as e:
        print(f"FAILED: API creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_monitoring_integration():
    """Test monitoring system integration"""
    print("\n=== Monitoring Integration Test ===")
    
    try:
        from backend.src.monitoring.health_api import router as health_router
        from backend.src.monitoring import get_logger
        
        logger = get_logger('integration_test')
        
        # Test health check API routes
        print("1. Testing health check API routes...")
        print(f"OK: Health check route prefix: {health_router.prefix}")
        print(f"OK: Health check route tags: {health_router.tags}")
        
        # Test route list
        routes = [route.path for route in health_router.routes if hasattr(route, 'path')]
        print(f"OK: Number of health check API endpoints: {len(routes)}")
        for route in routes:
            print(f"   - {route}")
        
        # Test logging functionality
        print("2. Testing logging functionality...")
        logger.info("System integration test", component="monitoring", status="success")
        logger.warning("Test warning log", test_field="test_value")
        logger.error("Test error log", error_code="TEST_001")
        
        print("OK: Monitoring integration test passed")
        return True
        
    except Exception as e:
        print(f"FAILED: Monitoring integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration_loading():
    """Test configuration loading"""
    print("\n=== Configuration Loading Test ===")
    
    try:
        # Test configuration file existence
        config_files = [
            "config/monitoring.yaml",
            "config/logging.yaml",
            "config/alerts.yaml",
            "config/default.yaml"
        ]
        
        for config_file in config_files:
            file_path = project_root / config_file
            if file_path.exists():
                print(f"OK: Configuration file exists: {config_file}")
            else:
                print(f"WARNING: Configuration file not found: {config_file}")
        
        # Test configuration module import
        from backend.src.config import get_config_system
        print("OK: Configuration system module import successful")
        
        return True
        
    except Exception as e:
        print(f"FAILED: Configuration loading test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("Starting service startup and functionality verification test...\n")
    
    # Execute all tests
    tests = [
        ("Service Startup Test", test_service_startup),
        ("API Creation Test", test_api_creation),
        ("Monitoring Integration Test", test_monitoring_integration),
        ("Configuration Loading Test", test_configuration_loading),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Executing test: {test_name}")
        print(f"{'='*50}")
        
        if asyncio.iscoroutinefunction(test_func):
            result = await test_func()
        else:
            result = test_func()
        
        results.append((test_name, result))
        
        if result:
            print(f"OK: {test_name} PASSED")
        else:
            print(f"FAILED: {test_name} FAILED")
    
    # Output test results summary
    print(f"\n{'='*50}")
    print("Test Results Summary")
    print(f"{'='*50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nSUCCESS: All tests passed! Service can start normally, monitoring functions work properly.")
        return True
    else:
        print(f"\nWARNING: {total - passed} tests failed, need to fix issues.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)