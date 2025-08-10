"""
API框架测试
"""

import pytest
import httpx
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json

# 导入应用
from src.api import app


class TestAPIFramework:
    """API框架测试类"""
    
    def setup_method(self):
        """设置测试环境"""
        self.client = TestClient(app)
    
    def test_root_endpoint(self):
        """测试根路径"""
        response = self.client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["service"] == "llms.txt-gen API"
        assert data["data"]["version"] == "1.0.0"
        assert data["message"] == "API服务正在运行"
    
    def test_health_check(self):
        """测试健康检查"""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "healthy"
        assert data["message"] == "健康检查通过"
    
    def test_api_info(self):
        """测试API信息"""
        response = self.client.get("/api/v1/info")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "llms.txt-gen API"
        assert data["data"]["version"] == "1.0.0"
        assert "endpoints" in data["data"]
    
    def test_system_status(self):
        """测试系统状态"""
        response = self.client.get("/api/v1/system/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "status" in data["data"]
    
    def test_system_health(self):
        """测试系统健康检查"""
        response = self.client.get("/api/v1/system/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "status" in data["data"]
    
    def test_request_id_header(self):
        """测试请求ID头"""
        response = self.client.get("/")
        
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0
    
    def test_cors_headers(self):
        """测试CORS头"""
        response = self.client.get("/")
        
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
    
    def test_validation_error(self):
        """测试验证错误"""
        # 发送无效的请求数据
        response = self.client.post(
            "/api/v1/test",
            json={"invalid_field": "invalid_value"}
        )
        
        # 应该返回404或验证错误
        assert response.status_code in [404, 422]
    
    def test_not_found_error(self):
        """测试404错误"""
        response = self.client.get("/api/v1/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "RESOURCE_NOT_FOUND"
    
    def test_system_config(self):
        """测试系统配置"""
        response = self.client.get("/api/v1/system/config")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
    
    def test_system_metrics(self):
        """测试系统指标"""
        response = self.client.get("/api/v1/system/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "api" in data["data"]
        assert "system" in data["data"]
    
    def test_system_logs(self):
        """测试系统日志"""
        response = self.client.get("/api/v1/system/logs")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "logs" in data["data"]
    
    def test_system_version(self):
        """测试系统版本"""
        response = self.client.get("/api/v1/system/version")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "api" in data["data"]
        assert "version" in data["data"]["api"]


class TestSecurityHelper:
    """安全助手测试类"""
    
    def test_generate_secure_token(self):
        """测试生成安全令牌"""
        from src.api.utils.security import SecurityHelper
        
        token = SecurityHelper.generate_secure_token()
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_generate_api_key(self):
        """测试生成API密钥"""
        from src.api.utils.security import SecurityHelper
        
        api_key = SecurityHelper.generate_api_key()
        assert isinstance(api_key, str)
        assert api_key.startswith("llms_")
    
    def test_hash_password(self):
        """测试密码哈希"""
        from src.api.utils.security import SecurityHelper
        
        password = "test_password"
        password_hash, salt = SecurityHelper.hash_password(password)
        
        assert isinstance(password_hash, str)
        assert isinstance(salt, str)
        assert len(password_hash) > 0
        assert len(salt) > 0
    
    def test_verify_password(self):
        """测试密码验证"""
        from src.api.utils.security import SecurityHelper
        
        password = "test_password"
        password_hash, salt = SecurityHelper.hash_password(password)
        
        assert SecurityHelper.verify_password(password, salt, password_hash) is True
        assert SecurityHelper.verify_password("wrong_password", salt, password_hash) is False
    
    def test_validate_password_strength(self):
        """测试密码强度验证"""
        from src.api.utils.security import SecurityHelper
        
        # 测试弱密码
        weak_result = SecurityHelper.validate_password_strength("123")
        assert weak_result["is_valid"] is False
        assert len(weak_result["errors"]) > 0
        
        # 测试强密码
        strong_result = SecurityHelper.validate_password_strength("StrongP@ssw0rd")
        assert strong_result["is_valid"] is True
        assert len(strong_result["errors"]) == 0
    
    def test_validate_email(self):
        """测试邮箱验证"""
        from src.api.utils.security import SecurityHelper
        
        assert SecurityHelper.validate_email("test@example.com") is True
        assert SecurityHelper.validate_email("invalid-email") is False
    
    def test_validate_username(self):
        """测试用户名验证"""
        from src.api.utils.security import SecurityHelper
        
        assert SecurityHelper.validate_username("testuser") is True
        assert SecurityHelper.validate_username("test@user") is False
        assert SecurityHelper.validate_username("") is False
    
    def test_sanitize_input(self):
        """测试输入清理"""
        from src.api.utils.security import SecurityHelper
        
        input_string = "<script>alert('xss')</script>"
        sanitized = SecurityHelper.sanitize_input(input_string)
        
        assert "<script>" not in sanitized
        assert "</script>" not in sanitized
    
    def test_detect_sql_injection(self):
        """测试SQL注入检测"""
        from src.api.utils.security import SecurityHelper
        
        malicious_input = "SELECT * FROM users"
        assert SecurityHelper.detect_sql_injection(malicious_input) is True
        
        safe_input = "normal text"
        assert SecurityHelper.detect_sql_injection(safe_input) is False
    
    def test_detect_xss(self):
        """测试XSS检测"""
        from src.api.utils.security import SecurityHelper
        
        malicious_input = "<script>alert('xss')</script>"
        assert SecurityHelper.detect_xss(malicious_input) is True
        
        safe_input = "normal text"
        assert SecurityHelper.detect_xss(safe_input) is False


class TestValidationHelper:
    """验证助手测试类"""
    
    def test_validate_required_fields(self):
        """测试必填字段验证"""
        from src.api.utils.validation import ValidationHelper
        
        data = {"name": "test", "age": 25}
        required_fields = ["name", "email"]
        
        errors = ValidationHelper.validate_required_fields(data, required_fields)
        assert "email" in errors
        assert "name" not in errors
    
    def test_validate_string_length(self):
        """测试字符串长度验证"""
        from src.api.utils.validation import ValidationHelper
        
        data = {"name": "test"}
        field_rules = {"name": {"min_length": 5, "max_length": 10}}
        
        errors = ValidationHelper.validate_string_length(data, field_rules)
        assert "name" in errors
    
    def test_validate_numeric_range(self):
        """测试数值范围验证"""
        from src.api.utils.validation import ValidationHelper
        
        data = {"age": 150}
        field_rules = {"age": {"min_value": 0, "max_value": 120}}
        
        errors = ValidationHelper.validate_numeric_range(data, field_rules)
        assert "age" in errors
    
    def test_validate_uuid(self):
        """测试UUID验证"""
        from src.api.utils.validation import ValidationHelper
        
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        invalid_uuid = "invalid-uuid"
        
        assert ValidationHelper.validate_uuid(valid_uuid) is True
        assert ValidationHelper.validate_uuid(invalid_uuid) is False
    
    def test_validate_url(self):
        """测试URL验证"""
        from src.api.utils.validation import ValidationHelper
        
        valid_url = "https://example.com"
        invalid_url = "not-a-url"
        
        assert ValidationHelper.validate_url(valid_url) is True
        assert ValidationHelper.validate_url(invalid_url) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])