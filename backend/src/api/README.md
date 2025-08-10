# API框架开发文档

## 概述

本项目基于FastAPI构建了一个完整的API服务框架，提供了RESTful API服务，支持用户认证、授权、请求验证、响应标准化等功能。

## 核心特性

### 1. 模块化架构
- **核心模块** (`core/`): 应用核心、异常处理、中间件、依赖注入
- **认证模块** (`auth/`): JWT认证、RBAC授权、权限管理
- **路由模块** (`routers/`): 业务路由模块
- **数据模型** (`schemas/`): 请求/响应数据模型
- **工具模块** (`utils/`): 分页、安全、验证工具
- **测试模块** (`tests/`): 单元测试和集成测试

### 2. 核心组件

#### APIFramework类
```python
from src.api.core import APIFramework, get_app, get_api_framework

# 创建API框架实例
api_framework = APIFramework(
    title="llms.txt-gen API",
    description="API for llms.txt generation service",
    version="1.0.0"
)

# 获取FastAPI应用
app = get_app()
```

#### 中间件
- **RequestIDMiddleware**: 请求ID生成和追踪
- **TimingMiddleware**: 请求处理时间统计
- **LoggingMiddleware**: 请求日志记录
- **SecurityHeadersMiddleware**: 安全头部添加
- **RateLimitMiddleware**: 请求限流
- **RequestBodyMiddleware**: 请求体处理
- **ResponseBodyMiddleware**: 响应体处理

#### 异常处理
- **APIException**: API异常基类
- **AuthenticationError**: 认证异常
- **AuthorizationError**: 授权异常
- **ValidationError**: 验证异常
- **ResourceNotFoundError**: 资源未找到异常
- **RateLimitError**: 限流异常

#### 响应模型
- **StandardResponse**: 标准响应格式
- **ErrorResponse**: 错误响应格式
- **PaginatedResponse**: 分页响应格式
- **BatchResponse**: 批量操作响应格式

### 3. 使用示例

#### 创建新的路由
```python
from fastapi import APIRouter, Depends
from src.api.schemas import StandardResponse
from src.api.core.dependencies import get_current_user

router = APIRouter()

@router.get("/profile", response_model=StandardResponse)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """获取用户资料"""
    return StandardResponse(
        success=True,
        data=current_user,
        message="获取用户资料成功"
    )
```

#### 使用分页工具
```python
from src.api.utils.pagination import PaginationHelper, PaginatedResponse
from src.api.schemas import create_paginated_response

@router.get("/items", response_model=PaginatedResponse)
async def get_items(
    page: int = 1,
    page_size: int = 10
):
    """获取项目列表（分页）"""
    items = [{"id": i, "name": f"Item {i}"} for i in range(1, 101)]
    
    paginated_result = PaginationHelper.paginate_list(
        items, page, page_size
    )
    
    return create_paginated_response(
        data=paginated_result.items,
        total=paginated_result.total,
        page=paginated_result.page,
        page_size=paginated_result.page_size
    )
```

#### 使用安全工具
```python
from src.api.utils.security import SecurityHelper

# 生成安全令牌
token = SecurityHelper.generate_secure_token()

# 密码哈希和验证
password_hash, salt = SecurityHelper.hash_password("password123")
is_valid = SecurityHelper.verify_password("password123", salt, password_hash)

# 检测SQL注入
is_malicious = SecurityHelper.detect_sql_injection("SELECT * FROM users")

# 清理输入
clean_input = SecurityHelper.sanitize_input("<script>alert('xss')</script>")
```

#### 使用验证工具
```python
from src.api.utils.validation import ValidationHelper

# 验证必填字段
data = {"name": "test", "age": 25}
required_fields = ["name", "email"]
errors = ValidationHelper.validate_required_fields(data, required_fields)

# 验证邮箱
is_valid_email = ValidationHelper.validate_email("test@example.com")

# 验证UUID
is_valid_uuid = ValidationHelper.validate_uuid("550e8400-e29b-41d4-a716-446655440000")
```

### 4. 配置和部署

#### 环境变量
```bash
# 数据库配置
DATABASE_URL=postgresql://postgres:password@localhost:5432/llms_txt_gen

# Redis配置
REDIS_URL=redis://localhost:6379

# 应用配置
HOST=0.0.0.0
PORT=8000
RELOAD=True
```

#### 启动服务
```bash
# 开发模式
uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload

# 生产模式
uvicorn src.api:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 运行测试
```bash
# 运行所有测试
pytest src/api/tests/ -v

# 运行特定测试
pytest src/api/tests/test_api_framework.py -v

# 生成覆盖率报告
pytest src/api/tests/ --cov=src/api --cov-report=html
```

### 5. API文档

启动服务后，可以通过以下地址访问API文档：

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

### 6. 系统端点

- `GET /`: 根路径，返回服务信息
- `GET /health`: 健康检查
- `GET /api/v1/info`: API信息
- `GET /api/v1/system/status`: 系统状态
- `GET /api/v1/system/health`: 系统健康检查
- `GET /api/v1/system/config`: 系统配置
- `GET /api/v1/system/metrics`: 系统指标
- `GET /api/v1/system/logs`: 系统日志
- `GET /api/v1/system/version`: 系统版本

### 7. 开发规范

#### 代码风格
- 遵循PEP 8规范
- 使用类型注解
- 编写文档字符串
- 编写单元测试

#### API设计
- 使用RESTful设计风格
- 统一响应格式
- 合理使用HTTP状态码
- 完善的错误处理

#### 安全考虑
- 输入验证和清理
- SQL注入防护
- XSS攻击防护
- CSRF防护
- 访问控制

### 8. 测试脚本

提供了专门的测试脚本来验证API框架：

```bash
# 运行API框架测试
python scripts/test_api_framework.py
```

这个脚本会：
1. 启动API服务器
2. 测试所有API端点
3. 输出测试结果
4. 关闭服务器

### 9. 故障排除

#### 常见问题

1. **依赖问题**
   ```bash
   pip install -r requirements.txt
   ```

2. **数据库连接问题**
   - 检查DATABASE_URL配置
   - 确保PostgreSQL服务正在运行

3. **Redis连接问题**
   - 检查REDIS_URL配置
   - 确保Redis服务正在运行

4. **端口占用问题**
   - 更改PORT环境变量
   - 或者停止占用端口的进程

#### 调试模式

```bash
# 启用调试日志
export LOG_LEVEL=DEBUG
uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

### 10. 性能优化

#### 数据库优化
- 使用连接池
- 添加索引
- 优化查询

#### 缓存优化
- 使用Redis缓存
- 实现请求缓存
- 使用CDN

#### 代码优化
- 异步处理
- 减少数据库查询
- 使用缓存

## 总结

这个API框架提供了完整的Web API开发解决方案，包含了现代Web应用所需的各种功能。通过模块化设计和丰富的工具类，可以快速开发和部署高质量的API服务。