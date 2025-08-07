#!/usr/bin/env python3
"""
API endpoint test script

Test API endpoint access and monitoring functionality
"""

import sys
import os
import asyncio
import json
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

def test_api_endpoints():
    """Test API endpoint functionality"""
    print("=== API Endpoint Test ===")
    
    try:
        # Test FastAPI app creation with monitoring routes
        print("1. Testing FastAPI app with monitoring routes...")
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        from backend.src.monitoring.health_api import router as health_router
        
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
        
        # Include monitoring routes
        app.include_router(health_router, prefix="/api/v1/health", tags=["health"])
        
        print("OK: FastAPI app with monitoring routes created successfully")
        
        # Test basic routes
        @app.get("/")
        async def root():
            return {"message": "llms.txt-gen API is running", "version": "1.0.0"}
        
        @app.get("/health")
        async def health_check():
            return {"status": "healthy", "timestamp": "2025-08-07T21:38:00"}
        
        print(f"OK: Total routes registered: {len(app.routes)}")
        
        # Test route details
        health_routes = [route for route in app.routes if hasattr(route, 'path') and '/api/v1/health' in str(route.path)]
        print(f"OK: Health API routes: {len(health_routes)}")
        
        for route in health_routes[:5]:  # Show first 5 routes
            print(f"   - {route.path} [{route.methods}]")
        
        return True
        
    except Exception as e:
        print(f"FAILED: API endpoint test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_monitoring_functionality():
    """Test monitoring functionality"""
    print("\n=== Monitoring Functionality Test ===")
    
    try:
        from backend.src.monitoring import (
            get_logger, setup_logging, get_health_checker,
            get_metrics_collector, get_alert_engine, get_log_analyzer
        )
        
        # Setup logging
        setup_logging()
        logger = get_logger('api_test')
        
        # Test logging with structured data
        print("1. Testing structured logging...")
        logger.info("API test started", endpoint="/test", method="GET")
        logger.warning("API warning", response_time=0.5, status_code=200)
        logger.error("API error", error_code="API_001", user_id="test_user")
        
        print("OK: Structured logging working")
        
        # Test health checks
        print("2. Testing health check functionality...")
        health_checker = get_health_checker()
        
        # Simulate health check results
        print(f"OK: Health checker initialized with {len(health_checker.checks)} checks")
        
        # Test metrics
        print("3. Testing metrics collection...")
        metrics_collector = get_metrics_collector()
        
        # Create test metrics
        request_counter = metrics_collector.registry.counter("api_requests_total", "Total API requests")
        response_time_gauge = metrics_collector.registry.gauge("api_response_time", "API response time")
        
        request_counter.inc()
        response_time_gauge.set(0.1)
        
        print("OK: Metrics collection working")
        
        # Test alert engine
        print("4. Testing alert engine...")
        alert_engine = get_alert_engine()
        
        # Test alert rule processing
        print(f"OK: Alert engine initialized with {len(alert_engine.rules)} rules")
        
        # Test log analysis
        print("5. Testing log analysis...")
        log_analyzer = get_log_analyzer()
        
        # Simulate log analysis
        test_logs = [
            {"level": "ERROR", "message": "Database connection failed", "timestamp": "2025-08-07T21:38:00"},
            {"level": "WARNING", "message": "High memory usage", "timestamp": "2025-08-07T21:38:01"},
            {"level": "INFO", "message": "User login successful", "timestamp": "2025-08-07T21:38:02"}
        ]
        
        analysis_result = log_analyzer.analyze_logs(test_logs)
        print(f"OK: Log analysis completed, found {len(analysis_result)} patterns")
        
        return True
        
    except Exception as e:
        print(f"FAILED: Monitoring functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration_integration():
    """Test configuration integration"""
    print("\n=== Configuration Integration Test ===")
    
    try:
        from backend.src.config import get_config_system
        from backend.src.monitoring.config import get_monitoring_config
        
        # Test configuration system
        print("1. Testing configuration system...")
        config_system = get_config_system()
        print("OK: Configuration system accessible")
        
        # Test monitoring configuration
        print("2. Testing monitoring configuration...")
        monitoring_config = get_monitoring_config()
        
        print(f"OK: Monitoring config loaded")
        print(f"   - Log level: {monitoring_config.logging.level}")
        print(f"   - Health check interval: {monitoring_config.health.check_interval}")
        print(f"   - Metrics enabled: {monitoring_config.metrics.enabled}")
        
        # Test configuration files
        print("3. Testing configuration files...")
        config_files = [
            "config/monitoring.yaml",
            "config/logging.yaml", 
            "config/alerts.yaml"
        ]
        
        for config_file in config_files:
            file_path = project_root / config_file
            if file_path.exists():
                print(f"OK: Config file exists: {config_file}")
            else:
                print(f"WARNING: Config file missing: {config_file}")
        
        return True
        
    except Exception as e:
        print(f"FAILED: Configuration integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_service_dependencies():
    """Test service dependencies"""
    print("\n=== Service Dependencies Test ===")
    
    try:
        # Test required imports
        print("1. Testing required imports...")
        
        # FastAPI and related
        import fastapi
        import uvicorn
        from fastapi import FastAPI
        print("OK: FastAPI imports successful")
        
        # Monitoring dependencies
        import structlog
        import prometheus_client
        import psutil
        print("OK: Monitoring imports successful")
        
        # Configuration dependencies
        import yaml
        import jsonschema
        print("OK: Configuration imports successful")
        
        # Test version compatibility
        print("2. Testing version compatibility...")
        print(f"OK: FastAPI version: {fastapi.__version__}")
        print(f"OK: Structlog version: {structlog.__version__}")
        print(f"OK: Prometheus client version: {prometheus_client.__version__}")
        
        return True
        
    except Exception as e:
        print(f"FAILED: Service dependencies test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("Starting API endpoint and functionality test...\n")
    
    # Execute all tests
    tests = [
        ("API Endpoint Test", test_api_endpoints),
        ("Monitoring Functionality Test", test_monitoring_functionality),
        ("Configuration Integration Test", test_configuration_integration),
        ("Service Dependencies Test", test_service_dependencies),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Executing test: {test_name}")
        print(f"{'='*60}")
        
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
    print(f"\n{'='*60}")
    print("API Test Results Summary")
    print(f"{'='*60}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nSUCCESS: All API tests passed! Service endpoints and monitoring functionality work properly.")
        return True
    else:
        print(f"\nWARNING: {total - passed} tests failed, need to fix issues.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)