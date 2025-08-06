"""
配置管理 API 测试
"""
import pytest
import json
import yaml
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import os

from ..main import app
from .management import router as management_router
from .core import ConfigSystem
from .schemas import ConfigUpdateRequest, ConfigValidationResult
from .exceptions import ConfigError


class TestConfigManagementAPI:
    """配置管理 API 测试类"""
    
    def setup_method(self):
        """测试前设置"""
        # 创建测试客户端
        self.client = TestClient(app)
        
        # 创建临时配置文件
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        self.test_config = {
            'app': {
                'name': 'test-app',
                'version': '1.0.0',
                'debug': True
            },
            'database': {
                'url': 'sqlite:///test.db',
                'pool_size': 10
            }
        }
        yaml.dump(self.test_config, self.temp_config, default_flow_style=False)
        self.temp_config.close()
        
        # 模拟配置管理器
        self.mock_config_manager = Mock()
        self.mock_config_manager.load_config.return_value = self.test_config
        self.mock_config_manager.get_config_info.return_value = {
            'config_path': self.temp_config.name,
            'last_modified': '2024-01-01T00:00:00Z',
            'file_size': 1024
        }
        self.mock_config_manager.save_config.return_value = True
        self.mock_config_manager.reload_config.return_value = True
        
        # 模拟配置系统
        self.mock_config_system = Mock(spec=ConfigSystem)
        self.mock_config_system.get_config.return_value = self.test_config
        self.mock_config_system.get_config_info.return_value = {
            'config_path': self.temp_config.name,
            'last_modified': '2024-01-01T00:00:00Z',
            'file_size': 1024
        }
        self.mock_config_system.reload_config.return_value = True
        self.mock_config_system.validate_config.return_value = ConfigValidationResult(
            valid=True,
            errors=[],
            warnings=[],
            suggestions=[]
        )
        
        # 模拟配置验证器
        self.mock_validator = Mock()
        self.mock_validator.validate_config.return_value = ConfigValidationResult(
            valid=True,
            errors=[],
            warnings=[],
            suggestions=[]
        )
        
        # 模拟回滚管理器
        self.mock_rollback_manager = Mock()
        self.mock_rollback_manager.get_history.return_value = []
        self.mock_rollback_manager.create_version.return_value = "test-version-id"
        self.mock_rollback_manager.rollback.return_value = True
    
    def teardown_method(self):
        """测试后清理"""
        # 删除临时配置文件
        if os.path.exists(self.temp_config.name):
            os.unlink(self.temp_config.name)
    
    def test_get_config_success(self):
        """测试获取配置成功"""
        with patch('src.config.management.get_config_manager', return_value=self.mock_config_manager):
            response = self.client.get("/api/v1/config/")
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert data['config'] == self.test_config
            assert 'config_info' in data
    
    def test_get_config_section_success(self):
        """测试获取配置部分成功"""
        with patch('src.config.management.get_config_manager', return_value=self.mock_config_manager):
            response = self.client.get("/api/v1/config/app")
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert data['section'] == 'app'
            assert data['data'] == self.test_config['app']
    
    def test_get_config_section_not_found(self):
        """测试获取不存在的配置部分"""
        with patch('src.config.management.get_config_manager', return_value=self.mock_config_manager):
            response = self.client.get("/api/v1/config/nonexistent")
            
            assert response.status_code == 404
            data = response.json()
            assert '配置部分不存在' in data['detail']
    
    def test_get_config_info_success(self):
        """测试获取配置信息成功"""
        with patch('src.config.management.get_config_manager', return_value=self.mock_config_manager):
            response = self.client.get("/api/v1/config/info")
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert 'config_info' in data
    
    def test_update_config_success(self):
        """测试更新配置成功"""
        update_data = {
            'config': {
                'app': {
                    'name': 'updated-app'
                }
            },
            'create_backup': True
        }
        
        with patch('src.config.management.get_config_manager', return_value=self.mock_config_manager), \
             patch('src.config.management.get_config_system', return_value=self.mock_config_system):
            
            response = self.client.put(
                "/api/v1/config/",
                json=update_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert data['message'] == '配置更新成功'
    
    def test_update_config_section_success(self):
        """测试更新配置部分成功"""
        section_data = {
            'name': 'updated-app',
            'version': '2.0.0'
        }
        
        with patch('src.config.management.get_config_manager', return_value=self.mock_config_manager), \
             patch('src.config.management.get_config_system', return_value=self.mock_config_system):
            
            response = self.client.put(
                "/api/v1/config/app",
                json=section_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert data['message'] == '配置部分更新成功'
    
    def test_delete_config_section_success(self):
        """测试删除配置部分成功"""
        with patch('src.config.management.get_config_manager', return_value=self.mock_config_manager), \
             patch('src.config.management.get_config_system', return_value=self.mock_config_system):
            
            response = self.client.delete("/api/v1/config/app")
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert data['message'] == '配置部分删除成功'
    
    def test_validate_config_success(self):
        """测试验证配置成功"""
        with patch('src.config.management.get_config_system', return_value=self.mock_config_system):
            response = self.client.post("/api/v1/config/validate")
            
            assert response.status_code == 200
            data = response.json()
            assert data['valid'] is True
            assert data['errors'] == []
            assert data['warnings'] == []
            assert data['suggestions'] == []
    
    def test_validate_config_with_data(self):
        """测试验证提供的数据配置"""
        test_config_data = {
            'app': {
                'name': 'test-app',
                'version': '1.0.0'
            }
        }
        
        with patch('src.config.management.get_validator', return_value=self.mock_validator):
            response = self.client.post(
                "/api/v1/config/validate",
                json=test_config_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['valid'] is True
    
    def test_validate_config_invalid(self):
        """测试验证无效配置"""
        self.mock_validator.validate_config.return_value = ConfigValidationResult(
            valid=False,
            errors=['Invalid configuration'],
            warnings=['Warning message'],
            suggestions=['Suggestion message']
        )
        
        with patch('src.config.management.get_validator', return_value=self.mock_validator):
            response = self.client.post(
                "/api/v1/config/validate",
                json={'invalid': 'config'}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['valid'] is False
            assert len(data['errors']) > 0
    
    def test_export_config_yaml(self):
        """测试导出 YAML 配置"""
        with patch('src.config.management.get_config_system', return_value=self.mock_config_system):
            response = self.client.get("/api/v1/config/export/yaml")
            
            assert response.status_code == 200
            assert response.headers['content-type'] == 'application/yaml'
            assert 'attachment; filename=' in response.headers['content-disposition']
    
    def test_export_config_json(self):
        """测试导出 JSON 配置"""
        with patch('src.config.management.get_config_system', return_value=self.mock_config_system):
            response = self.client.get("/api/v1/config/export/json")
            
            assert response.status_code == 200
            assert response.headers['content-type'] == 'application/json'
            assert 'attachment; filename=' in response.headers['content-disposition']
    
    def test_export_config_invalid_format(self):
        """测试导出无效格式"""
        with patch('src.config.management.get_config_system', return_value=self.mock_config_system):
            response = self.client.get("/api/v1/config/export/invalid")
            
            assert response.status_code == 400
    
    def test_import_config_yaml(self):
        """测试导入 YAML 配置"""
        import_data = yaml.dump(self.test_config, default_flow_style=False)
        
        with patch('src.config.management.get_config_system', return_value=self.mock_config_system):
            response = self.client.post(
                "/api/v1/config/import/yaml",
                data=import_data,
                headers={'content-type': 'application/yaml'}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert data['message'] == '配置导入成功'
    
    def test_import_config_json(self):
        """测试导入 JSON 配置"""
        import_data = json.dumps(self.test_config)
        
        with patch('src.config.management.get_config_system', return_value=self.mock_config_system):
            response = self.client.post(
                "/api/v1/config/import/json",
                data=import_data,
                headers={'content-type': 'application/json'}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert data['message'] == '配置导入成功'
    
    def test_import_config_invalid_format(self):
        """测试导入无效格式"""
        with patch('src.config.management.get_config_system', return_value=self.mock_config_system):
            response = self.client.post("/api/v1/config/import/invalid")
            
            assert response.status_code == 400
    
    def test_get_config_history(self):
        """测试获取配置历史"""
        with patch('src.config.management.get_config_system', return_value=self.mock_config_system):
            response = self.client.get("/api/v1/config/history")
            
            assert response.status_code == 200
            data = response.json()
            assert 'history' in data
            assert isinstance(data['history'], list)
    
    def test_rollback_config_success(self):
        """测试回滚配置成功"""
        with patch('src.config.management.get_config_system', return_value=self.mock_config_system):
            response = self.client.post("/api/v1/config/rollback/test-version-id")
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert data['message'] == '配置回滚成功'
    
    def test_create_snapshot_success(self):
        """测试创建快照成功"""
        snapshot_data = {
            'description': 'Test snapshot',
            'author': 'test-user'
        }
        
        with patch('src.config.management.get_config_system', return_value=self.mock_config_system):
            response = self.client.post(
                "/api/v1/config/snapshot",
                json=snapshot_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert data['message'] == '配置快照创建成功'
    
    def test_reload_config_success(self):
        """测试重载配置成功"""
        with patch('src.config.management.get_config_manager', return_value=self.mock_config_manager):
            response = self.client.post("/api/v1/config/reload")
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert data['message'] == '配置重载成功'
    
    def test_get_config_template(self):
        """测试获取配置模板"""
        response = self.client.get("/api/v1/config/template/app")
        
        assert response.status_code == 200
        data = response.json()
        assert data['config_type'] == 'app'
        assert 'template' in data


class TestConfigSystemIntegration:
    """配置系统集成测试"""
    
    def setup_method(self):
        """测试前设置"""
        # 创建临时配置文件
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        self.test_config = {
            'app': {
                'name': 'integration-test',
                'version': '1.0.0'
            }
        }
        yaml.dump(self.test_config, self.temp_config, default_flow_style=False)
        self.temp_config.close()
        
        # 创建配置系统实例
        self.config_system = ConfigSystem(self.temp_config.name)
    
    def teardown_method(self):
        """测试后清理"""
        # 删除临时配置文件
        if os.path.exists(self.temp_config.name):
            os.unlink(self.temp_config.name)
    
    @pytest.mark.asyncio
    async def test_config_system_lifecycle(self):
        """测试配置系统生命周期"""
        # 测试获取配置
        config = self.config_system.get_config()
        assert config == self.test_config
        
        # 测试获取配置信息
        config_info = self.config_system.get_config_info()
        assert 'config_path' in config_info
        
        # 测试导出配置
        yaml_export = self.config_system.export_config('yaml')
        assert 'name: integration-test' in yaml_export
        
        json_export = self.config_system.export_config('json')
        json_data = json.loads(json_export)
        assert json_data['app']['name'] == 'integration-test'
        
        # 测试导入配置
        new_config = {
            'app': {
                'name': 'imported-test',
                'version': '2.0.0'
            }
        }
        
        import_yaml = yaml.dump(new_config, default_flow_style=False)
        self.config_system.import_config(import_yaml, 'yaml', backup=False)
        
        updated_config = self.config_system.get_config()
        assert updated_config['app']['name'] == 'imported-test'
    
    def test_config_validation(self):
        """测试配置验证"""
        # 由于验证器可能未初始化，这里测试错误处理
        try:
            self.config_system.validate_config()
        except ConfigError as e:
            assert '配置验证器未初始化' in str(e)
    
    def test_config_history(self):
        """测试配置历史"""
        # 由于回滚管理器可能未初始化，这里测试错误处理
        try:
            self.config_system.get_config_history()
        except ConfigError as e:
            assert '配置回滚管理器未初始化' in str(e)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])