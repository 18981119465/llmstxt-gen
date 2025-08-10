"""
认证模块测试
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json
import time

# 导入应用
from src.api import app


class TestAuthentication:
    """认证测试类"""
    
    def setup_method(self):
        """设置测试环境"""
        self.client = TestClient(app)
        self.base_url = "/api/v1/auth"
    
    def test_login_success(self):
        """测试登录成功"""
        login_data = {
            "username": "testuser",
            "password": "password123"
        }
        
        response = self.client.post(f"{self.base_url}/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["token_type"] == "Bearer"
    
    def test_login_invalid_credentials(self):
        """测试登录失败 - 无效凭据"""
        login_data = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }
        
        response = self.client.post(f"{self.base_url}/login", json=login_data)
        
        assert response.status_code == 401
    
    def test_login_missing_fields(self):
        """测试登录失败 - 缺少字段"""
        login_data = {
            "username": "testuser"
            # 缺少 password
        }
        
        response = self.client.post(f"{self.base_url}/login", json=login_data)
        
        assert response.status_code == 422
    
    def test_register_success(self):
        """测试注册成功"""
        register_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "NewPassword123",
            "confirm_password": "NewPassword123",
            "role": "user"
        }
        
        response = self.client.post(f"{self.base_url}/register", json=register_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "access_token" in data["data"]
    
    def test_register_duplicate_username(self):
        """测试注册失败 - 用户名重复"""
        register_data = {
            "username": "testuser",  # 已存在的用户名
            "email": "another@example.com",
            "password": "NewPassword123",
            "confirm_password": "NewPassword123"
        }
        
        response = self.client.post(f"{self.base_url}/register", json=register_data)
        
        assert response.status_code == 400
    
    def test_register_weak_password(self):
        """测试注册失败 - 弱密码"""
        register_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "123",  # 弱密码
            "confirm_password": "123"
        }
        
        response = self.client.post(f"{self.base_url}/register", json=register_data)
        
        assert response.status_code == 422
    
    def test_refresh_token_success(self):
        """测试刷新令牌成功"""
        # 先登录获取刷新令牌
        login_data = {
            "username": "testuser",
            "password": "password123"
        }
        
        login_response = self.client.post(f"{self.base_url}/login", json=login_data)
        refresh_token = login_response.json()["data"]["refresh_token"]
        
        # 使用刷新令牌
        refresh_data = {
            "refresh_token": refresh_token
        }
        
        response = self.client.post(f"{self.base_url}/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
    
    def test_refresh_token_invalid(self):
        """测试刷新令牌失败 - 无效令牌"""
        refresh_data = {
            "refresh_token": "invalid_token"
        }
        
        response = self.client.post(f"{self.base_url}/refresh", json=refresh_data)
        
        assert response.status_code == 401
    
    def test_get_profile_unauthorized(self):
        """测试获取用户资料 - 未授权"""
        response = self.client.get(f"{self.base_url}/profile")
        
        assert response.status_code in [401, 403]
    
    def test_get_profile_authorized(self):
        """测试获取用户资料 - 已授权"""
        # 先登录
        login_data = {
            "username": "testuser",
            "password": "password123"
        }
        
        login_response = self.client.post(f"{self.base_url}/login", json=login_data)
        access_token = login_response.json()["data"]["access_token"]
        
        # 使用访问令牌获取用户资料
        headers = {"Authorization": f"Bearer {access_token}"}
        response = self.client.get(f"{self.base_url}/profile", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["username"] == "testuser"
    
    def test_get_permissions(self):
        """测试获取用户权限"""
        # 先登录
        login_data = {
            "username": "testuser",
            "password": "password123"
        }
        
        login_response = self.client.post(f"{self.base_url}/login", json=login_data)
        access_token = login_response.json()["data"]["access_token"]
        
        # 使用访问令牌获取权限
        headers = {"Authorization": f"Bearer {access_token}"}
        response = self.client.get(f"{self.base_url}/permissions", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "role" in data["data"]
        assert "permissions" in data["data"]


class TestJWTHandler:
    """JWT处理器测试类"""
    
    def setup_method(self):
        """设置测试环境"""
        from src.api.auth.jwt import JWTHandler
        self.jwt_handler = JWTHandler()
    
    def test_create_access_token(self):
        """测试创建访问令牌"""
        user_data = {
            "sub": "user123",
            "username": "testuser",
            "role": "user"
        }
        
        token = self.jwt_handler.create_access_token(user_data)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_token(self):
        """测试验证令牌"""
        user_data = {
            "sub": "user123",
            "username": "testuser",
            "role": "user"
        }
        
        token = self.jwt_handler.create_access_token(user_data)
        payload = self.jwt_handler.verify_token(token)
        
        assert payload["sub"] == "user123"
        assert payload["username"] == "testuser"
        assert payload["role"] == "user"
    
    def test_verify_invalid_token(self):
        """测试验证无效令牌"""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException):
            self.jwt_handler.verify_token("invalid_token")
    
    def test_is_token_expired(self):
        """测试检查令牌是否过期"""
        user_data = {
            "sub": "user123",
            "username": "testuser",
            "role": "user"
        }
        
        token = self.jwt_handler.create_access_token(user_data)
        
        # 新创建的令牌不应该过期
        assert self.jwt_handler.is_token_expired(token) is False
    
    def test_refresh_access_token(self):
        """测试刷新访问令牌"""
        user_data = {
            "sub": "user123",
            "username": "testuser",
            "role": "user"
        }
        
        refresh_token = self.jwt_handler.create_refresh_token(user_data)
        new_access_token = self.jwt_handler.refresh_access_token(refresh_token)
        
        assert isinstance(new_access_token, str)
        assert len(new_access_token) > 0


class TestPasswordHandler:
    """密码处理器测试类"""
    
    def setup_method(self):
        """设置测试环境"""
        from src.api.auth.jwt import PasswordHandler
        self.password_handler = PasswordHandler()
    
    def test_hash_password(self):
        """测试密码哈希"""
        password = "test_password"
        hashed = self.password_handler.hash_password(password)
        
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed != password
    
    def test_verify_password(self):
        """测试密码验证"""
        password = "test_password"
        hashed = self.password_handler.hash_password(password)
        
        assert self.password_handler.verify_password(password, hashed) is True
        assert self.password_handler.verify_password("wrong_password", hashed) is False
    
    def test_validate_password_strength(self):
        """测试密码强度验证"""
        # 测试弱密码
        weak_result = self.password_handler.validate_password_strength("123")
        assert weak_result["is_valid"] is False
        assert len(weak_result["errors"]) > 0
        
        # 测试强密码
        strong_result = self.password_handler.validate_password_strength("StrongP@ssw0rd")
        assert strong_result["is_valid"] is True
        assert len(strong_result["errors"]) == 0


class TestRBAC:
    """RBAC测试类"""
    
    def setup_method(self):
        """设置测试环境"""
        from src.api.auth.rbac import RBACManager, UserRole, Resource, Permission
        self.rbac_manager = RBACManager()
        self.user_role = UserRole.USER
        self.admin_role = UserRole.ADMIN
        self.document_resource = Resource.DOCUMENTS
        self.read_permission = Permission.READ
        self.write_permission = Permission.WRITE
    
    def test_user_has_read_permission(self):
        """测试用户有读取权限"""
        has_permission = self.rbac_manager.has_permission(
            self.user_role, self.document_resource, self.read_permission
        )
        assert has_permission is True
    
    def test_user_has_write_permission(self):
        """测试用户有写入权限"""
        has_permission = self.rbac_manager.has_permission(
            self.user_role, self.document_resource, self.write_permission
        )
        assert has_permission is True
    
    def test_admin_has_all_permissions(self):
        """测试管理员有所有权限"""
        has_permission = self.rbac_manager.has_permission(
            self.admin_role, self.document_resource, self.write_permission
        )
        assert has_permission is True
    
    def test_get_user_permissions(self):
        """测试获取用户权限"""
        permissions = self.rbac_manager.get_user_permissions(self.user_role)
        
        assert isinstance(permissions, dict)
        assert self.document_resource in permissions
        assert self.read_permission in permissions[self.document_resource]
    
    def test_get_accessible_resources(self):
        """测试获取可访问资源"""
        resources = self.rbac_manager.get_accessible_resources(self.user_role)
        
        assert isinstance(resources, list)
        assert len(resources) > 0
        assert self.document_resource in resources


if __name__ == "__main__":
    pytest.main([__file__, "-v"])