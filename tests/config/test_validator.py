"""
配置验证器测试
"""

import pytest
import tempfile
import os
from pathlib import Path
import yaml
import json

from backend.src.config.validator import ConfigValidator
from backend.src.config.exceptions import ConfigValidationError
from backend.src.config.schemas import EnvironmentType


class TestConfigValidator:
    """配置验证器测试"""
    
    def setup_method(self):
        """设置测试环境"""
        self.validator = ConfigValidator()
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir)
    
    def teardown_method(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_validator_initialization(self):
        """测试验证器初始化"""
        assert self.validator.schema is not None
        assert 'system' in self.validator.schema['properties']
        assert 'database' in self.validator.schema['properties']
        assert len(self.validator.required_fields) > 0
    
    def test_validate_valid_config(self):
        """测试验证有效配置"""
        valid_config = {
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
        
        result = self.validator.validate_config(valid_config)
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.config is not None
    
    def test_validate_invalid_config_structure(self):
        """测试验证无效配置结构"""
        invalid_config = {
            'system': {
                'name': '',  # 空名称
                'version': 'invalid-version',  # 无效版本号
                'debug': True,
                'env': 'invalid-env'  # 无效环境
            }
            # 缺少必需字段
        }
        
        result = self.validator.validate_config(invalid_config)
        assert result.is_valid is False
        assert len(result.errors) > 0
    
    def test_validate_missing_required_fields(self):
        """测试验证缺少必需字段"""
        incomplete_config = {
            'system': {
                'name': 'test-app',
                'version': '1.0.0',
                'debug': True,
                'env': 'development'
            }
            # 缺少其他必需字段
        }
        
        result = self.validator.validate_config(incomplete_config)
        assert result.is_valid is False
        assert any('required' in str(error).lower() for error in result.errors)
    
    def test_validate_business_rules(self):
        """测试业务规则验证"""
        # 生产环境启用调试模式
        config = {
            'system': {
                'name': 'test-app',
                'version': '1.0.0',
                'debug': True,
                'env': 'production'
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
                'secret_key': 'short',  # 密钥太短
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
        
        result = self.validator.validate_config(config)
        assert result.is_valid is False
        assert any('生产环境不应启用调试模式' in error for error in result.errors)
        assert any('密钥长度不能少于32位' in error for error in result.errors)
    
    def test_validate_config_file_yaml(self):
        """测试验证YAML配置文件"""
        valid_config = {
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
                'password': 'test_password'
            }
        }
        
        config_file = self.config_dir / 'valid.yaml'
        with open(config_file, 'w') as f:
            yaml.dump(valid_config, f)
        
        result = self.validator.validate_config_file(str(config_file))
        assert result.is_valid is True
    
    def test_validate_config_file_json(self):
        """测试验证JSON配置文件"""
        valid_config = {
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
                'password': 'test_password'
            }
        }
        
        config_file = self.config_dir / 'valid.json'
        with open(config_file, 'w') as f:
            json.dump(valid_config, f)
        
        result = self.validator.validate_config_file(str(config_file))
        assert result.is_valid is True
    
    def test_validate_config_file_not_found(self):
        """测试验证不存在的配置文件"""
        result = self.validator.validate_config_file('nonexistent.yaml')
        assert result.is_valid is False
        assert any('不存在' in error for error in result.errors)
    
    def test_validate_config_file_invalid_yaml(self):
        """测试验证无效YAML文件"""
        config_file = self.config_dir / 'invalid.yaml'
        with open(config_file, 'w') as f:
            f.write('invalid: yaml: [')
        
        result = self.validator.validate_config_file(str(config_file))
        assert result.is_valid is False
        assert any('YAML解析错误' in error for error in result.errors)
    
    def test_validate_environment_variables(self):
        """测试环境变量验证"""
        config = {
            'database': {
                'host': '${DB_HOST}',
                'port': '${DB_PORT:5432}'
            },
            'redis': {
                'host': '${REDIS_HOST}'
            }
        }
        
        # 设置部分环境变量
        os.environ['DB_HOST'] = 'localhost'
        os.environ['DB_PORT'] = '5432'
        # REDIS_HOST 未设置
        
        errors = self.validator.validate_environment_variables(config)
        assert len(errors) == 1
        assert 'REDIS_HOST' in errors[0]
        
        # 清理环境变量
        del os.environ['DB_HOST']
        del os.environ['DB_PORT']
    
    def test_validate_config_hierarchy(self):
        """测试配置层次结构验证"""
        configs = {
            'default': {
                'system': {
                    'name': 'test-app',
                    'version': '1.0.0',
                    'debug': False,
                    'env': 'development'
                },
                'database': {
                    'host': 'localhost',
                    'port': 5432,
                    'name': 'test_db',
                    'user': 'test_user',
                    'password': 'test_password'
                }
            },
            'development': {
                'system': {
                    'debug': True
                },
                'database': {
                    'name': 'dev_db'
                }
            }
        }
        
        result = self.validator.validate_config_hierarchy(configs)
        assert result.is_valid is True
    
    def test_validate_config_hierarchy_missing_required(self):
        """测试验证缺少必需配置的层次结构"""
        configs = {
            'development': {  # 缺少default配置
                'system': {
                    'name': 'test-app',
                    'version': '1.0.0',
                    'debug': True,
                    'env': 'development'
                }
            }
        }
        
        result = self.validator.validate_config_hierarchy(configs)
        assert result.is_valid is False
        assert any('缺少必需的配置文件' in error for error in result.errors)
    
    def test_validate_config_hierarchy_invalid_inheritance(self):
        """测试验证无效的继承关系"""
        configs = {
            'default': {
                'system': {
                    'name': 'test-app',
                    'version': '1.0.0',
                    'debug': False,
                    'env': 'development'
                }
            },
            'development': {
                'extends': 'nonexistent',  # 继承不存在的配置
                'system': {
                    'debug': True
                }
            }
        }
        
        result = self.validator.validate_config_hierarchy(configs)
        assert result.is_valid is False
        assert any('继承的配置不存在' in error for error in result.errors)
    
    def test_merge_configs(self):
        """测试配置合并"""
        configs = {
            'default': {
                'system': {
                    'name': 'test-app',
                    'version': '1.0.0',
                    'debug': False,
                    'env': 'development'
                },
                'database': {
                    'host': 'localhost',
                    'port': 5432,
                    'name': 'test_db',
                    'user': 'test_user',
                    'password': 'test_password'
                }
            },
            'development': {
                'system': {
                    'debug': True
                },
                'database': {
                    'name': 'dev_db'
                }
            }
        }
        
        merged = self.validator._merge_configs(configs)
        assert merged['system']['name'] == 'test-app'  # 来自default
        assert merged['system']['debug'] is True  # 来自development
        assert merged['database']['host'] == 'localhost'  # 来自default
        assert merged['database']['name'] == 'dev_db'  # 来自development
    
    def test_deep_merge(self):
        """测试深度合并"""
        dict1 = {
            'a': 1,
            'b': {
                'c': 2,
                'd': 3
            },
            'e': [1, 2, 3]
        }
        
        dict2 = {
            'b': {
                'd': 4,
                'f': 5
            },
            'e': [4, 5],
            'g': 6
        }
        
        merged = self.validator._deep_merge(dict1, dict2)
        
        assert merged['a'] == 1
        assert merged['b']['c'] == 2
        assert merged['b']['d'] == 4
        assert merged['b']['f'] == 5
        assert merged['e'] == [4, 5]  # 列表被替换
        assert merged['g'] == 6


if __name__ == '__main__':
    pytest.main([__file__, '-v'])