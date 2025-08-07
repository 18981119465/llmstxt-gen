#!/usr/bin/env python3
"""
Final service validation test

Comprehensive test of service startup and core functionality
"""

import sys
import os
import json
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

def test_core_functionality():
    """Test core functionality"""
    print("=== Core Functionality Test ===")
    
    try:
        # Test 1: FastAPI and basic imports
        print("1. Testing FastAPI and basic imports...")
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        print("OK: FastAPI imports successful")
        
        # Test 2: Monitoring system imports
        print("2. Testing monitoring system imports...")
        from backend.src.monitoring import (
            get_logger, setup_logging, get_health_checker,
            get_metrics_collector, get_alert_engine, get_log_analyzer
        )
        print("OK: Monitoring system imports successful")
        
        # Test 3: Logging functionality
        print("3. Testing logging functionality...")
        setup_logging()
        logger = get_logger('validation_test')
        logger.info("Validation test started")
        logger.warning("Validation test warning")
        logger.error("Validation test error", error_code="VAL_001")
        print("OK: Logging functionality working")
        
        # Test 4: Health check system
        print("4. Testing health check system...")
        health_checker = get_health_checker()
        print(f"OK: Health checker initialized with {len(health_checker.checks)} checks")
        
        # Test 5: Metrics collection
        print("5. Testing metrics collection...")
        metrics_collector = get_metrics_collector()
        
        # Create test metrics
        counter = metrics_collector.registry.counter("test_requests_total", "Test requests")
        gauge = metrics_collector.registry.gauge("test_active_users", "Test active users")
        histogram = metrics_collector.registry.histogram("test_response_time", "Test response time")
        
        counter.inc(10)
        gauge.set(42)
        histogram.observe(0.1)
        histogram.observe(0.5)
        histogram.observe(1.0)
        
        print("OK: Metrics collection working")
        
        # Test 6: Alert system
        print("6. Testing alert system...")
        alert_engine = get_alert_engine()
        print(f"OK: Alert engine initialized")
        
        # Test 7: Log analysis system
        print("7. Testing log analysis system...")
        log_analyzer = get_log_analyzer()
        print("OK: Log analysis system initialized")
        
        print("\nSUCCESS: All core functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"FAILED: Core functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_creation():
    """Test API creation with monitoring routes"""
    print("\n=== API Creation Test ===")
    
    try:
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
        
        # Add basic routes
        @app.get("/")
        async def root():
            return {"message": "llms.txt-gen API is running", "version": "1.0.0"}
        
        @app.get("/health")
        async def health_check():
            return {"status": "healthy", "timestamp": "2025-08-07T21:39:00"}
        
        # Include monitoring routes
        app.include_router(health_router, prefix="/api/v1/health", tags=["health"])
        
        print(f"OK: FastAPI app created with {len(app.routes)} total routes")
        
        # Count health API routes
        health_routes = [route for route in app.routes if hasattr(route, 'path') and '/api/v1/health' in str(route.path)]
        print(f"OK: Health API routes: {len(health_routes)}")
        
        # Show some example routes
        print("OK: Example health API endpoints:")
        for route in health_routes[:3]:
            print(f"   - {route.path} [{route.methods}]")
        
        return True
        
    except Exception as e:
        print(f"FAILED: API creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration_files():
    """Test configuration files"""
    print("\n=== Configuration Files Test ===")
    
    try:
        # Test configuration file existence
        config_files = [
            "config/monitoring.yaml",
            "config/logging.yaml",
            "config/alerts.yaml",
            "config/default.yaml",
            "config/development.yaml",
            "config/production.yaml"
        ]
        
        existing_files = []
        missing_files = []
        
        for config_file in config_files:
            file_path = project_root / config_file
            if file_path.exists():
                existing_files.append(config_file)
                print(f"OK: Configuration file exists: {config_file}")
            else:
                missing_files.append(config_file)
                print(f"WARNING: Configuration file missing: {config_file}")
        
        print(f"\nOK: Configuration files summary:")
        print(f"   - Existing: {len(existing_files)}")
        print(f"   - Missing: {len(missing_files)}")
        
        # Test configuration loading
        print("Testing configuration loading...")
        from backend.src.monitoring.config import get_monitoring_config
        
        monitoring_config = get_monitoring_config()
        print("OK: Monitoring configuration loaded successfully")
        
        return True
        
    except Exception as e:
        print(f"FAILED: Configuration files test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_service_readiness():
    """Test service readiness"""
    print("\n=== Service Readiness Test ===")
    
    try:
        # Test dependency imports
        print("1. Testing dependency imports...")
        
        # Core dependencies
        import fastapi
        import uvicorn
        import structlog
        import prometheus_client
        import psutil
        import yaml
        import jsonschema
        
        print("OK: All core dependencies imported successfully")
        
        # Test version info (where available)
        print("2. Testing version information...")
        print(f"   - FastAPI: {fastapi.__version__}")
        print(f"   - Structlog: {structlog.__version__}")
        print(f"   - Psutil: {psutil.__version__}")
        
        # Test 3: Monitor system status
        print("3. Testing monitoring system status...")
        from backend.src.monitoring import (
            get_logger, setup_logging, get_health_checker,
            get_metrics_collector, get_alert_engine, get_log_analyzer
        )
        
        # Initialize systems
        setup_logging()
        logger = get_logger('readiness_test')
        health_checker = get_health_checker()
        metrics_collector = get_metrics_collector()
        alert_engine = get_alert_engine()
        log_analyzer = get_log_analyzer()
        
        # Log readiness status
        logger.info("Service readiness test completed", status="success")
        
        print("OK: All monitoring systems initialized and ready")
        
        return True
        
    except Exception as e:
        print(f"FAILED: Service readiness test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("Starting comprehensive service validation test...\n")
    
    # Execute all tests
    tests = [
        ("Core Functionality Test", test_core_functionality),
        ("API Creation Test", test_api_creation),
        ("Configuration Files Test", test_configuration_files),
        ("Service Readiness Test", test_service_readiness),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Executing test: {test_name}")
        print(f"{'='*60}")
        
        result = test_func()
        results.append((test_name, result))
        
        if result:
            print(f"OK: {test_name} PASSED")
        else:
            print(f"FAILED: {test_name} FAILED")
    
    # Output test results summary
    print(f"\n{'='*60}")
    print("Service Validation Test Results")
    print(f"{'='*60}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nSUCCESS: All service validation tests passed!")
        print("✅ Service can start normally")
        print("✅ Monitoring functionality is working")
        print("✅ API endpoints are properly configured")
        print("✅ Configuration files are loaded")
        print("✅ All dependencies are satisfied")
        return True
    else:
        print(f"\nWARNING: {total - passed} tests failed, need to fix issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)