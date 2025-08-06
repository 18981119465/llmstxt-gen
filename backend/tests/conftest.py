"""
测试配置文件
"""
import pytest
import asyncio
import tempfile
import os
from pathlib import Path

# 测试根目录
TEST_ROOT = Path(__file__).parent

# 测试数据目录
TEST_DATA_DIR = TEST_ROOT / 'data'
TEST_DATA_DIR.mkdir(exist_ok=True)

# 临时文件目录
TEMP_DIR = TEST_ROOT / 'temp'
TEMP_DIR.mkdir(exist_ok=True)


@pytest.fixture
def temp_config_file():
    """创建临时配置文件"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config_content = """
app:
  name: test-app
  version: 1.0.0
  debug: true

database:
  url: sqlite:///test.db
  pool_size: 10
  timeout: 30

redis:
  host: localhost
  port: 6379
  db: 0
  password: ""

api:
  host: 0.0.0.0
  port: 8000
  debug: true
"""
        f.write(config_content)
        f.flush()
        
        yield f.name
    
    # 清理
    if os.path.exists(f.name):
        os.unlink(f.name)


@pytest.fixture
def sample_config():
    """示例配置数据"""
    return {
        'app': {
            'name': 'test-app',
            'version': '1.0.0',
            'debug': True
        },
        'database': {
            'url': 'sqlite:///test.db',
            'pool_size': 10,
            'timeout': 30
        },
        'redis': {
            'host': 'localhost',
            'port': 6379,
            'db': 0,
            'password': ''
        },
        'api': {
            'host': '0.0.0.0',
            'port': 8000,
            'debug': True
        }
    }


@pytest.fixture
def invalid_config():
    """无效配置数据"""
    return {
        'app': {
            'name': '',  # 空名称应该无效
            'version': 'invalid-version',  # 无效版本号
            'debug': 'not-a-boolean'  # 无效布尔值
        },
        'database': {
            'url': '',  # 空URL应该无效
            'pool_size': -1,  # 负数应该无效
            'timeout': 'not-a-number'  # 无效数字
        }
    }


@pytest.fixture
def event_loop():
    """创建事件循环"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_dependencies():
    """模拟依赖项"""
    from unittest.mock import Mock
    
    # 模拟配置管理器
    mock_config_manager = Mock()
    mock_config_manager.load_config.return_value = {
        'app': {'name': 'test', 'version': '1.0.0'},
        'database': {'url': 'sqlite:///test.db'}
    }
    mock_config_manager.get_config_info.return_value = {
        'config_path': '/test/config.yaml',
        'last_modified': '2024-01-01T00:00:00Z',
        'file_size': 1024
    }
    mock_config_manager.save_config.return_value = True
    mock_config_manager.reload_config.return_value = True
    
    # 模拟配置验证器
    mock_validator = Mock()
    mock_validator.validate_config.return_value = Mock(
        valid=True,
        errors=[],
        warnings=[],
        suggestions=[]
    )
    
    # 模拟配置观察者
    mock_watcher = Mock()
    mock_watcher.start_watching = Mock()
    mock_watcher.stop_watching = Mock()
    
    # 模拟通知服务
    mock_notification_service = Mock()
    mock_notification_service.start = Mock()
    mock_notification_service.stop = Mock()
    
    # 模拟回滚管理器
    mock_rollback_manager = Mock()
    mock_rollback_manager.get_history.return_value = []
    mock_rollback_manager.create_version.return_value = 'test-version-id'
    mock_rollback_manager.rollback.return_value = True
    
    return {
        'config_manager': mock_config_manager,
        'validator': mock_validator,
        'watcher': mock_watcher,
        'notification_service': mock_notification_service,
        'rollback_manager': mock_rollback_manager
    }


# 测试用例标记
unit_test = pytest.mark.unit
integration_test = pytest.mark.integration
slow_test = pytest.mark.slow