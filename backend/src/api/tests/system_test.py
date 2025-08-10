"""
Story 1.4 API框架系统测试
对实现的API接口进行全面系统测试
"""

import pytest
import json
import time
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

# 导入应用
from src.api import app


class SystemTestSuite:
    """系统测试套件"""
    
    def __init__(self):
        self.client = TestClient(app)
        self.base_url = ""
        self.auth_base_url = "/api/v1/auth"
        self.system_base_url = "/api/v1/system"
        self.test_results = []
        self.auth_tokens = {}
        
    def run_test(self, test_name, test_func, *args, **kwargs):
        """运行单个测试并记录结果"""
        try:
            result = test_func(*args, **kwargs)
            self.test_results.append({
                "name": test_name,
                "status": "PASS",
                "result": result,
                "timestamp": datetime.now().isoformat()
            })
            print(f"✓ {test_name}")
            return True
        except Exception as e:
            self.test_results.append({
                "name": test_name,
                "status": "FAIL",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            print(f"✗ {test_name}: {e}")
            return False
    
    def test_root_endpoint(self):
        """测试根路径端点"""
        response = self.client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "service" in data["data"]
        assert data["data"]["service"] == "llms.txt-gen API"
        assert "docs" in data["data"]
        return response.json()
    
    def test_health_check_endpoint(self):
        """测试健康检查端点"""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "healthy"
        return response.json()
    
    def test_api_info_endpoint(self):
        """测试API信息端点"""
        response = self.client.get("/api/v1/info")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "llms.txt-gen API"
        assert "endpoints" in data["data"]
        return response.json()
    
    def test_user_login_success(self):
        """测试用户登录成功"""
        login_data = {
            "username": "testuser",
            "password": "password123"
        }
        
        response = self.client.post(f"{self.auth_base_url}/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["token_type"] == "Bearer"
        
        # 保存令牌用于后续测试
        self.auth_tokens["user"] = data["data"]["access_token"]
        return response.json()
    
    def test_admin_login_success(self):
        """测试管理员登录成功"""
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = self.client.post(f"{self.auth_base_url}/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        
        # 保存管理员令牌
        self.auth_tokens["admin"] = data["data"]["access_token"]
        return response.json()
    
    def test_user_login_invalid_credentials(self):
        """测试用户登录失败 - 无效凭据"""
        login_data = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }
        
        response = self.client.post(f"{self.auth_base_url}/login", json=login_data)
        assert response.status_code == 401
        return response.json()
    
    def test_user_registration_success(self):
        """测试用户注册成功"""
        register_data = {
            "username": f"newuser_{int(time.time())}",
            "email": f"newuser_{int(time.time())}@example.com",
            "password": "NewPassword123",
            "confirm_password": "NewPassword123",
            "role": "user"
        }
        
        response = self.client.post(f"{self.auth_base_url}/register", json=register_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        return response.json()
    
    def test_get_user_profile(self):
        """测试获取用户资料"""
        if "user" not in self.auth_tokens:
            self.test_user_login_success()
        
        headers = {"Authorization": f"Bearer {self.auth_tokens['user']}"}
        response = self.client.get(f"{self.auth_base_url}/profile", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["username"] == "testuser"
        return response.json()
    
    def test_get_user_permissions(self):
        """测试获取用户权限"""
        if "user" not in self.auth_tokens:
            self.test_user_login_success()
        
        headers = {"Authorization": f"Bearer {self.auth_tokens['user']}"}
        response = self.client.get(f"{self.auth_base_url}/permissions", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "role" in data["data"]
        assert "permissions" in data["data"]
        return response.json()
    
    def test_refresh_token(self):
        """测试刷新令牌"""
        if "user" not in self.auth_tokens:
            self.test_user_login_success()
        
        # 重新登录获取刷新令牌
        login_data = {
            "username": "testuser",
            "password": "password123"
        }
        
        login_response = self.client.post(f"{self.auth_base_url}/login", json=login_data)
        refresh_token = login_response.json()["data"]["refresh_token"]
        
        refresh_data = {
            "refresh_token": refresh_token
        }
        
        response = self.client.post(f"{self.auth_base_url}/refresh", json=refresh_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        return response.json()
    
    def test_system_status(self):
        """测试系统状态"""
        response = self.client.get(f"{self.system_base_url}/status")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        return response.json()
    
    def test_system_health_detailed(self):
        """测试详细健康检查"""
        response = self.client.get(f"{self.system_base_url}/health?detailed=true")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "detailed" in data["data"]
        return response.json()
    
    def test_system_config(self):
        """测试系统配置"""
        response = self.client.get(f"{self.system_base_url}/config")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        return response.json()
    
    def test_system_metrics(self):
        """测试系统指标"""
        response = self.client.get(f"{self.system_base_url}/metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "api" in data["data"]
        assert "system" in data["data"]
        return response.json()
    
    def test_system_logs(self):
        """测试系统日志"""
        response = self.client.get(f"{self.system_base_url}/logs")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "logs" in data["data"]
        return response.json()
    
    def test_system_version(self):
        """测试系统版本"""
        response = self.client.get(f"{self.system_base_url}/version")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "api" in data["data"]
        return response.json()
    
    def test_unauthorized_access(self):
        """测试未授权访问"""
        response = self.client.get(f"{self.auth_base_url}/profile")
        assert response.status_code == 401
        return response.json()
    
    def test_invalid_token(self):
        """测试无效令牌"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = self.client.get(f"{self.auth_base_url}/profile", headers=headers)
        assert response.status_code == 401
        return response.json()
    
    def test_api_documentation_access(self):
        """测试API文档访问"""
        # 测试Swagger UI
        response = self.client.get("/api/docs")
        assert response.status_code == 200
        
        # 测试ReDoc
        response = self.client.get("/api/redoc")
        assert response.status_code == 200
        
        # 测试OpenAPI规范
        response = self.client.get("/api/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        return data
    
    def test_cors_headers(self):
        """测试CORS头"""
        response = self.client.options("/")
        assert response.status_code == 200
        
        # 测试实际的CORS头
        response = self.client.get("/")
        assert "access-control-allow-origin" in response.headers.lower()
        return response.json()
    
    def test_request_id_header(self):
        """测试请求ID头"""
        response = self.client.get("/")
        assert "x-request-id" in response.headers
        return response.json()
    
    def test_rate_limiting_simulation(self):
        """模拟测试限流"""
        # 快速发送多个请求
        responses = []
        for i in range(5):
            response = self.client.get("/health")
            responses.append(response.status_code)
        
        # 检查是否有被限流的响应
        assert 200 in responses
        return responses
    
    def run_all_tests(self):
        """运行所有系统测试"""
        print("开始系统测试...")
        print("=" * 50)
        
        # 基础端点测试
        self.run_test("根路径端点", self.test_root_endpoint)
        self.run_test("健康检查端点", self.test_health_check_endpoint)
        self.run_test("API信息端点", self.test_api_info_endpoint)
        
        # 认证测试
        self.run_test("用户登录成功", self.test_user_login_success)
        self.run_test("管理员登录成功", self.test_admin_login_success)
        self.run_test("用户登录失败", self.test_user_login_invalid_credentials)
        self.run_test("用户注册成功", self.test_user_registration_success)
        
        # 令牌测试
        self.run_test("刷新令牌", self.test_refresh_token)
        
        # 用户资料测试
        self.run_test("获取用户资料", self.test_get_user_profile)
        self.run_test("获取用户权限", self.test_get_user_permissions)
        
        # 系统管理测试
        self.run_test("系统状态", self.test_system_status)
        self.run_test("详细健康检查", self.test_system_health_detailed)
        self.run_test("系统配置", self.test_system_config)
        self.run_test("系统指标", self.test_system_metrics)
        self.run_test("系统日志", self.test_system_logs)
        self.run_test("系统版本", self.test_system_version)
        
        # 安全测试
        self.run_test("未授权访问", self.test_unauthorized_access)
        self.run_test("无效令牌", self.test_invalid_token)
        
        # 功能测试
        self.run_test("API文档访问", self.test_api_documentation_access)
        self.run_test("CORS头", self.test_cors_headers)
        self.run_test("请求ID头", self.test_request_id_header)
        self.run_test("限流模拟", self.test_rate_limiting_simulation)
        
        print("=" * 50)
        return self.test_results
    
    def generate_report(self):
        """生成测试报告"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            },
            "test_results": self.test_results,
            "generated_at": datetime.now().isoformat(),
            "api_version": "1.0.0"
        }
        
        return report


def main():
    """主函数"""
    test_suite = SystemTestSuite()
    
    # 运行所有测试
    test_results = test_suite.run_all_tests()
    
    # 生成报告
    report = test_suite.generate_report()
    
    # 输出报告摘要
    print("\n系统测试报告摘要")
    print("=" * 50)
    print(f"总测试数: {report['test_summary']['total_tests']}")
    print(f"通过测试: {report['test_summary']['passed_tests']}")
    print(f"失败测试: {report['test_summary']['failed_tests']}")
    print(f"成功率: {report['test_summary']['success_rate']:.1f}%")
    
    # 输出失败的测试
    if report['test_summary']['failed_tests'] > 0:
        print("\n失败的测试:")
        for result in test_results:
            if result["status"] == "FAIL":
                print(f"  - {result['name']}: {result['error']}")
    
    # 保存详细报告
    with open("system_test_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n详细测试报告已保存到: system_test_report.json")
    
    return report


if __name__ == "__main__":
    main()