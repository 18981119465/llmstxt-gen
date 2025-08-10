"""
简化的系统测试脚本
"""

import json
import sys
import os
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from src.api import app

def run_system_tests():
    """运行系统测试"""
    client = TestClient(app)
    results = []
    
    print("开始系统测试...")
    print("=" * 50)
    
    # 测试1: 根路径
    try:
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "service" in data["data"]
        print("PASS 根路径端点测试通过")
        results.append({"name": "根路径端点", "status": "PASS"})
    except Exception as e:
        print(f"FAIL 根路径端点测试失败: {e}")
        results.append({"name": "根路径端点", "status": "FAIL", "error": str(e)})
    
    # 测试2: 健康检查
    try:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        print("PASS 健康检查端点测试通过")
        results.append({"name": "健康检查端点", "status": "PASS"})
    except Exception as e:
        print(f"FAIL 健康检查端点测试失败: {e}")
        results.append({"name": "健康检查端点", "status": "FAIL", "error": str(e)})
    
    # 测试3: API信息
    try:
        response = client.get("/api/v1/info")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        print("PASS API信息端点测试通过")
        results.append({"name": "API信息端点", "status": "PASS"})
    except Exception as e:
        print(f"FAIL API信息端点测试失败: {e}")
        results.append({"name": "API信息端点", "status": "FAIL", "error": str(e)})
    
    # 测试4: 用户登录
    try:
        login_data = {
            "username": "testuser",
            "password": "password123"
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        print("PASS 用户登录测试通过")
        results.append({"name": "用户登录", "status": "PASS"})
        access_token = data["data"]["access_token"]
    except Exception as e:
        print(f"FAIL 用户登录测试失败: {e}")
        results.append({"name": "用户登录", "status": "FAIL", "error": str(e)})
        access_token = None
    
    # 测试5: 用户资料 (需要登录成功)
    if access_token:
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = client.get("/api/v1/auth/profile", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            print("PASS 用户资料测试通过")
            results.append({"name": "用户资料", "status": "PASS"})
        except Exception as e:
            print(f"FAIL 用户资料测试失败: {e}")
            results.append({"name": "用户资料", "status": "FAIL", "error": str(e)})
    
    # 测试6: 系统状态
    try:
        response = client.get("/api/v1/system/status")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        print("PASS 系统状态测试通过")
        results.append({"name": "系统状态", "status": "PASS"})
    except Exception as e:
        print(f"FAIL 系统状态测试失败: {e}")
        results.append({"name": "系统状态", "status": "FAIL", "error": str(e)})
    
    # 测试7: 系统健康
    try:
        response = client.get("/api/v1/system/health")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        print("PASS 系统健康测试通过")
        results.append({"name": "系统健康", "status": "PASS"})
    except Exception as e:
        print(f"FAIL 系统健康测试失败: {e}")
        results.append({"name": "系统健康", "status": "FAIL", "error": str(e)})
    
    # 测试8: 系统配置
    try:
        response = client.get("/api/v1/system/config")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        print("PASS 系统配置测试通过")
        results.append({"name": "系统配置", "status": "PASS"})
    except Exception as e:
        print(f"FAIL 系统配置测试失败: {e}")
        results.append({"name": "系统配置", "status": "FAIL", "error": str(e)})
    
    # 测试9: 未授权访问
    try:
        response = client.get("/api/v1/auth/profile")
        # 401 Unauthorized 或 403 Forbidden 都是可接受的
        assert response.status_code in [401, 403]
        print("PASS 未授权访问测试通过")
        results.append({"name": "未授权访问", "status": "PASS"})
    except Exception as e:
        print(f"FAIL 未授权访问测试失败: {e}")
        results.append({"name": "未授权访问", "status": "FAIL", "error": str(e)})
    
    # 测试10: API文档访问
    try:
        response = client.get("/api/docs")
        assert response.status_code == 200
        print("PASS API文档访问测试通过")
        results.append({"name": "API文档访问", "status": "PASS"})
    except Exception as e:
        print(f"FAIL API文档访问测试失败: {e}")
        results.append({"name": "API文档访问", "status": "FAIL", "error": str(e)})
    
    print("=" * 50)
    
    # 生成报告
    total_tests = len(results)
    passed_tests = len([r for r in results if r["status"] == "PASS"])
    failed_tests = len([r for r in results if r["status"] == "FAIL"])
    
    print(f"总测试数: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"失败测试: {failed_tests}")
    print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
    
    # 保存报告
    report = {
        "test_summary": {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests/total_tests)*100 if total_tests > 0 else 0
        },
        "test_results": results,
        "generated_at": "2025-08-07T23:59:00Z",
        "api_version": "1.0.0"
    }
    
    with open("system_test_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"详细测试报告已保存到: system_test_report.json")
    
    return report

if __name__ == "__main__":
    run_system_tests()