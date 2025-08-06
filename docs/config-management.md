# 配置管理系统文档

## 概述

配置管理系统为 llms.txt-gen 项目提供了一个完整的配置解决方案，包括配置加载、验证、热重载、版本管理、API接口、Web界面和SDK等功能。

## 系统架构

### 核心组件

1. **ConfigManager** - 配置管理器，负责配置的加载、保存和访问
2. **ConfigValidator** - 配置验证器，确保配置符合预定义的 schema
3. **ConfigWatcher** - 配置文件监视器，实现热重载功能
4. **ConfigRollbackManager** - 配置版本管理器，支持配置回滚
5. **NotificationManager** - 通知管理器，处理配置变更通知

### 支持的配置格式

- YAML (推荐)
- JSON
- 环境变量
- 命令行参数

## 快速开始

### 1. 基本使用

```python
from src.config import ConfigManager, get_config

# 创建配置管理器
config_manager = ConfigManager("config/config.yaml")

# 加载配置
config = config_manager.load_config()

# 获取配置值
app_name = config_manager.get_config_value("app.name")

# 更新配置值
config_manager.update_config_value("app.debug", True)
```

### 2. 使用热重载

```python
from src.config import ConfigWatcher, ConfigChangeEvent

def on_config_change(event: ConfigChangeEvent):
    print(f"配置文件已变更: {event.change_type}")
    # 重新加载配置
    new_config = config_manager.load_config()

# 创建监视器
watcher = ConfigWatcher("config/config.yaml")
watcher.add_callback(on_config_change)
watcher.start_watching()
```

### 3. 配置验证

```python
from src.config import ConfigValidator

validator = ConfigValidator()

# 验证配置
result = validator.validate_config(config)
if result.valid:
    print("配置有效")
else:
    print("配置错误:")
    for error in result.errors:
        print(f"  - {error}")
```

## 配置文件结构

### 主配置文件 (config.yaml)

```yaml
# 应用配置
app:
  name: "llms.txt-gen"
  version: "1.0.0"
  debug: false
  environment: "production"

# 系统配置
system:
  max_workers: 4
  timeout: 30
  retry_count: 3

# 数据库配置
database:
  url: "postgresql://localhost:5432/llms_txt_gen"
  pool_size: 10
  max_overflow: 20

# Redis配置
redis:
  url: "redis://localhost:6379"
  db: 0
  password: ""

# API配置
api:
  host: "0.0.0.0"
  port: 8000
  cors_origins:
    - "http://localhost:3000"
    - "http://localhost:8080"

# AI服务配置
ai_services:
  openai:
    api_key: "${OPENAI_API_KEY}"
    model: "gpt-4"
    max_tokens: 4000
    temperature: 0.7
  
  claude:
    api_key: "${CLAUDE_API_KEY}"
    model: "claude-3-sonnet-20240229"
    max_tokens: 4000
    temperature: 0.7

# 文档处理配置
document_processor:
  chunk_size: 1000
  chunk_overlap: 200
  supported_formats:
    - "txt"
    - "md"
    - "pdf"
    - "docx"

# 爬虫配置
web_crawler:
  max_pages: 100
  delay: 1
  timeout: 30
  user_agent: "llms.txt-gen/1.0.0"

# 日志配置
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/app.log"
  max_size: "10MB"
  backup_count: 5

# 监控配置
monitoring:
  enabled: true
  metrics_port: 9090
  health_check_interval: 30

# 安全配置
security:
  secret_key: "${SECRET_KEY}"
  access_token_expire_minutes: 30
  refresh_token_expire_days: 7

# 存储配置
storage:
  type: "local"
  local_path: "./data"
  s3_bucket: ""
  s3_region: ""
```

### 环境配置文件 (config.${ENVIRONMENT}.yaml)

```yaml
# 开发环境配置
app:
  debug: true
  environment: "development"

database:
  url: "postgresql://localhost:5432/llms_txt_gen_dev"

logging:
  level: "DEBUG"
```

## API 接口

### 基础 URL

- 配置管理 API: `/api/v1/config`
- 配置 Web 界面: `/config`

### 主要端点

#### 1. 获取配置

```http
GET /api/v1/config/
```

响应:
```json
{
  "success": true,
  "config": {
    "app": {
      "name": "llms.txt-gen",
      "version": "1.0.0"
    }
  },
  "config_info": {
    "config_path": "/path/to/config.yaml",
    "file_size": 1024,
    "last_modified": "2024-01-01T00:00:00Z"
  }
}
```

#### 2. 更新配置

```http
POST /api/v1/config/
Content-Type: application/json

{
  "config": {
    "app": {
      "debug": true
    }
  }
}
```

#### 3. 获取配置部分

```http
GET /api/v1/config/sections/database
```

#### 4. 更新配置部分

```http
PUT /api/v1/config/sections/database
Content-Type: application/json

{
  "section": {
    "pool_size": 20,
    "max_overflow": 30
  }
}
```

#### 5. 获取配置值

```http
GET /api/v1/config/values/app.debug
```

#### 6. 设置配置值

```http
POST /api/v1/config/values/app.debug
Content-Type: application/json

{
  "value": true
}
```

#### 7. 验证配置

```http
POST /api/v1/config/validate
Content-Type: application/json

{
  "config": {
    "app": {
      "name": "test",
      "version": "1.0.0"
    }
  }
}
```

#### 8. 导出配置

```http
GET /api/v1/config/export?format=yaml
```

#### 9. 导入配置

```http
POST /api/v1/config/import
Content-Type: application/json

{
  "config": {
    "app": {
      "name": "imported-app"
    }
  }
}
```

#### 10. 获取配置历史

```http
GET /api/v1/config/history
```

#### 11. 回滚配置

```http
POST /api/v1/config/rollback
Content-Type: application/json

{
  "version_id": "20240101-120000-000"
}
```

## Web 界面

### 访问地址

```
http://localhost:8000/config/
```

### 功能特性

1. **配置仪表板** - 显示配置概览和系统状态
2. **配置编辑器** - 可视化编辑配置文件
3. **配置验证** - 实时验证配置有效性
4. **历史记录** - 查看和回滚配置历史
5. **导入/导出** - 支持多种格式的配置导入导出
6. **热重载控制** - 启用/禁用配置文件监听
7. **通知中心** - 查看配置变更通知

### 界面截图

#### 仪表板
- 显示当前配置状态
- 系统健康检查
- 最近变更记录

#### 配置编辑器
- 语法高亮的 YAML 编辑器
- 实时验证反馈
- 配置项提示

#### 历史记录
- 时间线视图
- 版本对比
- 一键回滚

## SDK 使用

### 安装

```bash
pip install llms-txt-gen-config
```

### 基本使用

#### 1. 远程配置客户端

```python
import asyncio
from src.config.sdk import ConfigClient, ConfigClientOptions

async def main():
    # 创建配置客户端
    options = ConfigClientOptions(
        api_base_url="http://localhost:8000/api/v1/config",
        timeout=10
    )
    
    async with ConfigClient(options) as client:
        # 获取配置
        config = await client.get_config()
        print(f"应用名称: {config['app']['name']}")
        
        # 更新配置
        await client.set_value("app.debug", True)
        
        # 验证配置
        result = await client.validate_config()
        print(f"配置有效: {result['valid']}")
        
        # 获取历史记录
        history = await client.get_history()
        print(f"历史记录数量: {len(history)}")

if __name__ == "__main__":
    asyncio.run(main())
```

#### 2. 本地配置管理器

```python
from src.config.sdk import LocalConfigManager

# 创建本地配置管理器
manager = LocalConfigManager("config/config.yaml")

# 加载配置
config = manager.load_config()

# 更新配置
manager.set_value("app.debug", True)

# 验证配置
result = manager.validate_config()
print(f"配置有效: {result['valid']}")

# 导出配置
yaml_config = manager.export_config("yaml")
print(yaml_config)
```

### 批量操作

```python
async def batch_operations():
    async with ConfigClient() as client:
        # 批量更新
        updates = [
            ("app.debug", True),
            ("database.pool_size", 20),
            ("api.port", 8080)
        ]
        
        for key, value in updates:
            await client.set_value(key, value)
        
        # 批量获取
        keys = ["app.name", "app.debug", "database.url"]
        for key in keys:
            value = await client.get_value(key)
            print(f"{key}: {value}")
```

### 错误处理

```python
async def error_handling():
    async with ConfigClient() as client:
        try:
            # 尝试获取不存在的配置
            value = await client.get_value("nonexistent.key")
        except Exception as e:
            print(f"错误: {e}")
        
        try:
            # 尝试验证无效配置
            invalid_config = {"app": {"name": ""}}
            result = await client.validate_config(invalid_config)
            print(f"验证结果: {result}")
        except Exception as e:
            print(f"错误: {e}")
```

## 命令行工具

### 基本命令

```bash
# 查看配置
python -m src.config.cli show

# 获取配置值
python -m src.config.cli get app.name

# 设置配置值
python -m src.config.cli set app.debug true

# 验证配置
python -m src.config.cli validate

# 导出配置
python -m src.config.cli export --format yaml

# 导入配置
python -m src.config.cli import --file config.yaml

# 查看历史记录
python -m src.config.cli history

# 回滚配置
python -m src.config.cli rollback VERSION_ID

# 启动 Web 界面
python -m src.config.cli web
```

### 高级功能

```bash
# 监视配置文件变化
python -m src.config.cli watch

# 批量更新配置
python -m src.config.cli batch-update updates.json

# 配置文件对比
python -m src.config.cli diff FILE1 FILE2

# 生成配置模板
python -m src.config.cli template > template.yaml
```

## 配置验证规则

### 应用配置验证

```python
class AppConfig(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    version: str = Field(..., regex=r'^\d+\.\d+\.\d+$')
    debug: bool = False
    environment: EnvironmentType = EnvironmentType.DEVELOPMENT
```

### 数据库配置验证

```python
class DatabaseConfig(BaseModel):
    url: str = Field(..., regex=r'^postgresql://')
    pool_size: int = Field(..., ge=1, le=100)
    max_overflow: int = Field(..., ge=0, le=50)
    timeout: int = Field(..., ge=1, le=300)
```

### 通用验证规则

- 必填字段检查
- 数据类型验证
- 格式验证（URL、邮箱等）
- 数值范围检查
- 枚举值验证
- 自定义验证逻辑

## 热重载机制

### 工作原理

1. **文件监视** - 使用 watchdog 库监视配置文件变化
2. **事件处理** - 捕获文件创建、修改、删除事件
3. **配置重载** - 自动重新加载配置文件
4. **通知发送** - 通过 WebSocket 发送变更通知
5. **状态更新** - 更新内存中的配置状态

### 配置选项

```yaml
watcher:
  enabled: true
  debounce_interval: 1.0  # 防抖间隔（秒）
  watch_extensions: [".yaml", ".yml", ".json"]
  recursive: true
  ignore_patterns:
    - "*.tmp"
    - "*.bak"
    - ".*"
```

### 事件类型

- `CREATED` - 文件创建
- `MODIFIED` - 文件修改
- `DELETED` - 文件删除
- `MOVED` - 文件移动

## 版本管理

### 版本号格式

```
YYYYMMDD-HHMMSS-SEQ
例如: 20240101-120000-000
```

### 版本操作

```python
# 获取版本历史
history = rollback_manager.get_history()

# 回滚到指定版本
success = rollback_manager.rollback("20240101-120000-000")

# 获取版本详情
version = rollback_manager.get_version("20240101-120000-000")

# 比较版本差异
diff = rollback_manager.compare_versions("20240101-120000-000", "20240101-130000-000")
```

### 存储策略

- 版本文件存储在 `config/versions/` 目录
- 最多保留 100 个版本
- 支持定期清理旧版本
- 压缩存储以节省空间

## 安全考虑

### 敏感信息处理

1. **环境变量** - 使用 `${VAR_NAME}` 语法引用环境变量
2. **加密存储** - 支持配置值加密
3. **访问控制** - API 接口需要认证
4. **审计日志** - 记录所有配置变更操作

### 最佳实践

1. 不要在配置文件中存储敏感信息
2. 使用环境变量存储密钥和密码
3. 定期轮换密钥和证书
4. 启用配置文件访问日志
5. 实施配置变更审批流程

## 性能优化

### 缓存策略

- 内存缓存当前配置
- 文件内容缓存
- 验证结果缓存
- 版本信息缓存

### 异步处理

- 异步文件操作
- 异步网络请求
- 异步通知发送
- 并发配置验证

### 监控指标

- 配置加载时间
- 验证耗时
- 文件监视延迟
- API 响应时间

## 故障排除

### 常见问题

1. **配置文件格式错误**
   - 检查 YAML/JSON 语法
   - 使用验证工具检查格式

2. **配置文件权限问题**
   - 确保应用有读写权限
   - 检查文件所有者和组

3. **热重载不工作**
   - 检查文件监视器状态
   - 确认文件路径正确

4. **API 访问失败**
   - 检查服务状态
   - 验证认证信息

### 调试技巧

```python
# 启用调试日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 检查配置文件状态
from pathlib import Path
config_path = Path("config/config.yaml")
print(f"配置文件存在: {config_path.exists()}")
print(f"文件大小: {config_path.stat().st_size}")

# 测试配置加载
from src.config import ConfigManager
config_manager = ConfigManager("config/config.yaml")
config = config_manager.load_config()
print(f"配置加载成功: {config is not None}")
```

## 扩展开发

### 自定义验证器

```python
from src.config.validator import ConfigValidator

class CustomValidator(ConfigValidator):
    def validate_custom_field(self, value):
        # 自定义验证逻辑
        if not isinstance(value, str):
            return False, "必须是字符串"
        if len(value) < 3:
            return False, "长度不能小于3"
        return True, "验证通过"
```

### 自定义通知处理器

```python
from src.config.notifications import NotificationHandler

class SlackNotificationHandler(NotificationHandler):
    async def send_notification(self, message: NotificationMessage):
        # 发送 Slack 通知
        await self.send_to_slack(message.content)
```

### 自定义存储后端

```python
from src.config.storage import StorageBackend

class S3StorageBackend(StorageBackend):
    def save_config(self, config: dict, version_id: str):
        # 保存到 S3
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=f"config/{version_id}.yaml",
            Body=yaml.dump(config)
        )
```

## 贡献指南

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/18981119465/llmstxt-gen.git
cd llmstxt-gen

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 运行测试
python -m pytest tests/

# 启动开发服务器
python -m uvicorn main:app --reload
```

### 代码风格

- 遵循 PEP 8 规范
- 使用 Black 进行代码格式化
- 使用 isort 进行导入排序
- 使用 flake8 进行代码检查

### 测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/test_config.py

# 生成覆盖率报告
python -m pytest --cov=src tests/
```

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](../LICENSE) 文件。

## 联系方式

- 项目主页: https://github.com/18981119465/llmstxt-gen
- 问题反馈: https://github.com/18981119465/llmstxt-gen/issues
- 邮箱: 18981119465@qq.com

---

*最后更新: 2024-01-01*