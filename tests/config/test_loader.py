"""
配置加载器测试
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import yaml

from backend.src.config.loader import ConfigLoader, ConfigManager
from backend.src.config.exceptions import ConfigError, ConfigNotFoundError, ConfigValidationError


class TestConfigLoader:
    """配置加载器测试"""
    
    def setup_method(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "config"
        self.config_dir.mkdir()
        
        # 创建测试配置文件
        self.default_config = {
            'system': {
                'name': 'test-app',
                'version': '1.0.0',
                'debug': True,
                'env': 'development'
            },
            'database': {
                'host': 'localhost',
                'port': 5432,
                'name': 'test_db',
                'user': 'test_user',
                'password': 'test_password',
                'pool_size': 10,
                'max_overflow': 20,
                'pool_timeout': 30,
                'pool_recycle': 3600
            },
            'redis': {
                'host': 'localhost',
                'port': 6379,
                'db': 0,
                'password': '',
                'max_connections': 10
            },
            'api': {
                'host': '0.0.0.0',
                'port': 8000,
                'workers': 4,
                'cors_origins': ['*'],
                'cors_methods': ['GET', 'POST']
            },
            'ai_service': {
                'enabled': True,
                'model': 'gpt-3.5-turbo',
                'max_tokens': 1000,
                'temperature': 0.7,
                'timeout': 30,
                'retry_attempts': 3
            },
            'document_processor': {
                'enabled': True,
                'max_file_size': 10485760,
                'supported_formats': ['txt', 'md', 'pdf'],
                'processing_timeout': 300
            },
            'web_crawler': {
                'enabled': True,
                'max_pages': 100,
                'delay': 1,
                'timeout': 30,
                'user_agent': 'test-agent'
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file': 'logs/app.log',
                'max_file_size': 10485760,
                'backup_count': 5,
                'rotation': 'midnight'
            },
            'monitoring': {
                'enabled': True,
                'metrics_port': 9090,
                'health_check_interval': 30,
                'performance_tracking': True
            },
            'security': {
                'secret_key': 'a' * 32,
                'jwt_secret': 'b' * 32,
                'jwt_algorithm': 'HS256',
                'jwt_expiration': 3600,
                'bcrypt_rounds': 12
            },
            'storage': {
                'type': 'local',
                'local_path': 'data/storage',
                'max_storage_size': 1073741824,
                'allowed_extensions': ['txt', 'md', 'pdf']
            }
        }
        
        with open(self.config_dir / 'default.yaml', 'w') as f:
            yaml.dump(self.default_config, f)
        
        self.loader = ConfigLoader(str(self.config_dir), 'development')
    
    def teardown_method(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir)
        # 重置ConfigManager单例
        ConfigManager.reset_instance()
    
    def test_init_config_loader(self):
        """测试配置加载器初始化"""
        assert self.loader.config_dir == self.config_dir
        assert self.loader.env == 'development'
        assert self.loader._merged_config is None
    
    def test_load_config_file_success(self):
        """测试成功加载配置文件"""
        config = self.loader._load_config_file('default.yaml')
        assert config is not None
        assert config['system']['name'] == 'test-app'
        assert config['database']['host'] == 'localhost'
    
    def test_load_config_file_not_found(self):
        """测试配置文件不存在"""
        config = self.loader._load_config_file('nonexistent.yaml')
        assert config is None
    
    def test_load_config_invalid_yaml(self):
        """测试无效YAML文件"""
        with open(self.config_dir / 'invalid.yaml', 'w') as f:
            f.write('invalid: yaml: content: [')
        
        with pytest.raises(ConfigError):
            self.loader._load_config_file('invalid.yaml')
    
    def test_load_config_success(self):
        """测试成功加载配置"""
        # 创建development.yaml文件 - 包含完整的配置结构
        dev_config = {
            'system': {
                'name': 'test-app',  # 必需字段
                'version': '1.0.0',  # 必需字段
                'debug': True,
                'env': 'development'
            },
            'database': {
                'host': 'localhost',
                'port': 5432,
                'name': 'dev_db',
                'user': 'test_user',
                'password': 'test_password',
                'pool_size': 10,
                'max_overflow': 20,
                'pool_timeout': 30,
                'pool_recycle': 3600
            },
            'redis': {
                'host': 'localhost',
                'port': 6379,
                'db': 0,
                'password': '',
                'max_connections': 10
            },
            'api': {
                'host': '0.0.0.0',
                'port': 8000,
                'workers': 4,
                'cors_origins': ['*'],
                'cors_methods': ['GET', 'POST']
            },
            'ai_service': {
                'enabled': True,
                'model': 'gpt-3.5-turbo',
                'max_tokens': 1000,
                'temperature': 0.7,
                'timeout': 30,
                'retry_attempts': 3
            },
            'document_processor': {
                'enabled': True,
                'max_file_size': 10485760,
                'supported_formats': ['txt', 'md', 'pdf'],
                'processing_timeout': 300
            },
            'web_crawler': {
                'enabled': True,
                'max_pages': 100,
                'delay': 1,
                'timeout': 30,
                'user_agent': 'test-agent'
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file': 'logs/app.log',
                'max_file_size': 10485760,
                'backup_count': 5,
                'rotation': 'midnight'
            },
            'monitoring': {
                'enabled': True,
                'metrics_port': 9090,
                'health_check_interval': 30,
                'performance_tracking': True
            },
            'security': {
                'secret_key': 'a' * 32,
                'jwt_secret': 'b' * 32,
                'jwt_algorithm': 'HS256',
                'jwt_expiration': 3600,
                'bcrypt_rounds': 12
            },
            'storage': {
                'type': 'local',
                'local_path': 'data/storage',
                'max_storage_size': 1073741824,
                'allowed_extensions': ['txt', 'md', 'pdf']
            }
        }
        
        with open(self.config_dir / 'development.yaml', 'w') as f:
            yaml.dump(dev_config, f)
        
        config = self.loader.load_config()
        assert config is not None
        assert config['system']['name'] == 'test-app'
        assert config['system']['debug'] is True
        assert config['database']['name'] == 'dev_db'
        assert self.loader._merged_config is not None
    
    def test_load_config_with_env_override(self):
        """测试环境配置覆盖"""
        env_config = {
            'system': {
                'debug': False
            },
            'database': {
                'host': 'prod-host',
                'name': 'prod_db'  # 需要提供必需字段
            }
        }
        
        with open(self.config_dir / 'development.yaml', 'w') as f:
            yaml.dump(env_config, f)
        
        config = self.loader.load_config()
        assert config['system']['debug'] is False  # 被覆盖
        assert config['system']['name'] == 'test-app'  # 保持默认
        assert config['database']['host'] == 'prod-host'  # 被覆盖
        assert config['database']['name'] == 'prod_db'  # 被覆盖
    
    def test_get_config_value(self):
        """测试获取配置值"""
        self.loader.load_config()
        
        # 测试存在的键
        assert self.loader.get_config_value('system.name') == 'test-app'
        assert self.loader.get_config_value('database.port') == 5432
        
        # 测试不存在的键
        assert self.loader.get_config_value('nonexistent.key') is None
        assert self.loader.get_config_value('nonexistent.key', 'default') == 'default'
    
    def test_get_service_config(self):
        """测试获取服务配置"""
        self.loader.load_config()
        
        db_config = self.loader.get_database_config()
        assert db_config['host'] == 'localhost'
        assert db_config['port'] == 5432
        
        api_config = self.loader.get_api_config()
        assert api_config['host'] == '0.0.0.0'
        assert api_config['port'] == 8000
    
    def test_reload_config(self):
        """测试重载配置"""
        # 初始加载
        config1 = self.loader.load_config()
        assert config1['system']['debug'] is True
        
        # 修改配置文件
        env_config = {
            'system': {
                'debug': False
            }
        }
        
        with open(self.config_dir / 'development.yaml', 'w') as f:
            yaml.dump(env_config, f)
        
        # 重载配置
        config2 = self.loader.reload_config()
        assert config2['system']['debug'] is False
    
    def test_list_config_files(self):
        """测试列出配置文件"""
        files = self.loader.list_config_files()
        assert 'default.yaml' in files
        
        # 创建更多配置文件
        (self.config_dir / 'templates').mkdir()
        with open(self.config_dir / 'templates' / 'test.yaml', 'w') as f:
            yaml.dump({'test': 'value'}, f)
        
        files = self.loader.list_config_files()
        assert 'templates\\test.yaml' in files
    
    def test_get_config_info(self):
        """测试获取配置信息"""
        self.loader.load_config()
        
        info = self.loader.get_config_info()
        assert info['config_dir'] == str(self.config_dir)
        assert info['environment'] == 'development'
        assert 'default.yaml' in info['loaded_files']
        assert info['merged_config_size'] > 0
    
    def test_config_validation_error(self):
        """测试配置验证错误"""
        # 创建无效配置
        invalid_config = {
            'system': {
                'name': '',  # 空名称
                'version': 'invalid-version',  # 无效版本号
                'debug': True,
                'env': 'invalid-env'  # 无效环境
            }
        }
        
        with open(self.config_dir / 'invalid.yaml', 'w') as f:
            yaml.dump(invalid_config, f)
        
        # 修改loader以加载无效配置
        self.loader.config_dir = self.config_dir
        
        with pytest.raises(ConfigValidationError):
            self.loader.load_config()


class TestConfigManager:
    """配置管理器测试"""
    
    def setup_method(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "config"
        self.config_dir.mkdir()
        
        # 创建测试配置文件
        default_config = {
            'system': {
                'name': 'test-app',
                'version': '1.0.0',
                'debug': True,
                'env': 'development'
            },
            'database': {
                'host': 'localhost',
                'port': 5432,
                'name': 'test_db',
                'user': 'test_user',
                'password': 'test_password',
                'pool_size': 10,
                'max_overflow': 20,
                'pool_timeout': 30,
                'pool_recycle': 3600
            },
            'redis': {
                'host': 'localhost',
                'port': 6379,
                'db': 0,
                'password': '',
                'max_connections': 10
            },
            'api': {
                'host': '0.0.0.0',
                'port': 8000,
                'workers': 4,
                'cors_origins': ['*'],
                'cors_methods': ['GET', 'POST']
            },
            'ai_service': {
                'enabled': True,
                'model': 'gpt-3.5-turbo',
                'max_tokens': 1000,
                'temperature': 0.7,
                'timeout': 30,
                'retry_attempts': 3
            },
            'document_processor': {
                'enabled': True,
                'max_file_size': 10485760,
                'supported_formats': ['txt', 'md', 'pdf'],
                'processing_timeout': 300
            },
            'web_crawler': {
                'enabled': True,
                'max_pages': 100,
                'delay': 1,
                'timeout': 30,
                'user_agent': 'test-agent'
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file': 'logs/app.log',
                'max_file_size': 10485760,
                'backup_count': 5,
                'rotation': 'midnight'
            },
            'monitoring': {
                'enabled': True,
                'metrics_port': 9090,
                'health_check_interval': 30,
                'performance_tracking': True
            },
            'security': {
                'secret_key': 'a' * 32,
                'jwt_secret': 'b' * 32,
                'jwt_algorithm': 'HS256',
                'jwt_expiration': 3600,
                'bcrypt_rounds': 12
            },
            'storage': {
                'type': 'local',
                'local_path': 'data/storage',
                'max_storage_size': 1073741824,
                'allowed_extensions': ['txt', 'md', 'pdf']
            }
        }
        
        with open(self.config_dir / 'default.yaml', 'w') as f:
            yaml.dump(default_config, f)
    
    def teardown_method(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir)
        # 重置ConfigManager单例
        ConfigManager.reset_instance()
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        manager1 = ConfigManager.get_instance(str(self.config_dir))
        manager2 = ConfigManager.get_instance(str(self.config_dir))
        assert manager1 is manager2
    
    def test_config_manager_load_config(self):
        """测试配置管理器加载配置"""
        manager = ConfigManager.get_instance(str(self.config_dir))
        config = manager.load_config()
        assert config['system']['name'] == 'test-app'
    
    def test_config_manager_get_config_value(self):
        """测试配置管理器获取配置值"""
        manager = ConfigManager.get_instance(str(self.config_dir))
        value = manager.get_config_value('system.name')
        assert value == 'test-app'
    
    @patch('backend.src.config.loader.ConfigManager._instance')
    def test_config_manager_initialization(self, mock_instance):
        """测试配置管理器初始化"""
        mock_instance.return_value = None
        
        manager = ConfigManager(str(self.config_dir))
        assert manager._config_loader is not None
        assert manager._config_loader.config_dir == self.config_dir


class TestConfigIntegration:
    """配置集成测试"""
    
    def setup_method(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "config"
        self.config_dir.mkdir()
        
        # 创建完整的配置文件结构
        self.default_config = {
            'system': {
                'name': 'llmstxt-gen',
                'version': '1.0.0',
                'debug': True,
                'env': 'development'
            },
            'database': {
                'host': 'localhost',
                'port': 5432,
                'name': 'test_db',
                'user': 'test_user',
                'password': 'test_password',
                'pool_size': 10,
                'max_overflow': 20,
                'pool_timeout': 30,
                'pool_recycle': 3600
            },
            'redis': {
                'host': 'localhost',
                'port': 6379,
                'db': 0,
                'password': '',
                'max_connections': 10
            },
            'api': {
                'host': '0.0.0.0',
                'port': 8000,
                'workers': 4,
                'cors_origins': ['*'],
                'cors_methods': ['GET', 'POST']
            },
            'ai_service': {
                'enabled': True,
                'model': 'gpt-3.5-turbo',
                'max_tokens': 1000,
                'temperature': 0.7,
                'timeout': 30,
                'retry_attempts': 3
            },
            'document_processor': {
                'enabled': True,
                'max_file_size': 10485760,
                'supported_formats': ['txt', 'md', 'pdf'],
                'processing_timeout': 300
            },
            'web_crawler': {
                'enabled': True,
                'max_pages': 100,
                'delay': 1,
                'timeout': 30,
                'user_agent': 'test-agent'
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file': 'logs/app.log',
                'max_file_size': 10485760,
                'backup_count': 5,
                'rotation': 'midnight'
            },
            'monitoring': {
                'enabled': True,
                'metrics_port': 9090,
                'health_check_interval': 30,
                'performance_tracking': True
            },
            'security': {
                'secret_key': 'a' * 32,
                'jwt_secret': 'b' * 32,
                'jwt_algorithm': 'HS256',
                'jwt_expiration': 3600,
                'bcrypt_rounds': 12
            },
            'storage': {
                'type': 'local',
                'local_path': 'data/storage',
                'max_storage_size': 1073741824,
                'allowed_extensions': ['txt', 'md', 'pdf']
            }
        }
        
        with open(self.config_dir / 'default.yaml', 'w') as f:
            yaml.dump(self.default_config, f)
        
        # 开发环境配置
        dev_config = {
            'system': {
                'debug': True,
                'env': 'development'
            },
            'database': {
                'name': 'dev_db',
                'host': 'localhost',  # 保持必需字段
                'port': 5432,
                'user': 'test_user',
                'password': 'test_password',
                'pool_size': 10,
                'max_overflow': 20,
                'pool_timeout': 30,
                'pool_recycle': 3600
            },
            'redis': {
                'host': 'localhost',
                'port': 6379,
                'db': 0,
                'password': '',
                'max_connections': 10
            }
            # 其他必需字段会从默认配置继承
        }
        
        with open(self.config_dir / 'development.yaml', 'w') as f:
            yaml.dump(dev_config, f)
    
    def teardown_method(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir)
        # 重置ConfigManager单例
        ConfigManager.reset_instance()
    
    def test_complete_config_loading(self):
        """测试完整配置加载流程"""
        loader = ConfigLoader(str(self.config_dir), 'development')
        config = loader.load_config()
        
        # 验证配置合并
        assert config['system']['name'] == 'llmstxt-gen'  # 来自默认配置
        assert config['system']['debug'] is True  # 来自环境配置
        assert config['system']['env'] == 'development'  # 来自环境配置
        assert config['database']['name'] == 'dev_db'  # 来自环境配置
        assert config['database']['pool_size'] == 10  # 来自默认配置
    
    def test_environment_variables(self):
        """测试环境变量处理"""
        # 设置环境变量
        os.environ['TEST_DB_HOST'] = 'env-host'
        
        config_with_env = {
            'database': {
                'host': '${TEST_DB_HOST}',
                'port': '${TEST_DB_PORT:5432}'
            }
        }
        
        with open(self.config_dir / 'env_test.yaml', 'w') as f:
            yaml.dump(config_with_env, f)
        
        loader = ConfigLoader(str(self.config_dir), 'development')
        
        # 添加环境配置
        loader._load_all_configs = MagicMock()
        loader._load_all_configs.return_value = {
            'default': self.default_config,
            'development': config_with_env
        }
        
        # 模拟合并配置
        merged = loader.priority._process_env_vars(config_with_env)
        assert merged['database']['host'] == 'env-host'
        assert merged['database']['port'] == '5432'
        
        # 清理环境变量
        del os.environ['TEST_DB_HOST']
    
    def test_config_validation_comprehensive(self):
        """测试全面的配置验证"""
        # 创建有效配置
        valid_config = self.default_config.copy()
        
        with open(self.config_dir / 'valid.yaml', 'w') as f:
            yaml.dump(valid_config, f)
        
        loader = ConfigLoader(str(self.config_dir), 'development')
        result = loader.validate_config_file(str(self.config_dir / 'valid.yaml'))
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.config is not None
    
    def test_config_performance(self):
        """测试配置加载性能"""
        import time
        
        loader = ConfigLoader(str(self.config_dir), 'development')
        
        # 测试加载时间
        start_time = time.time()
        config = loader.load_config()
        load_time = time.time() - start_time
        
        assert load_time < 0.1  # 应该在100ms内完成
        
        # 测试重载时间
        start_time = time.time()
        config = loader.reload_config()
        reload_time = time.time() - start_time
        
        assert reload_time < 0.1  # 应该在100ms内完成


if __name__ == '__main__':
    pytest.main([__file__, '-v'])