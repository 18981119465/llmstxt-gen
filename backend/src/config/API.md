# 配置管理 API 文档

## 概述

配置管理 API 提供了完整的配置管理功能，包括配置查询、更新、验证、导入导出、历史版本管理等。

## 基础信息

- **Base URL**: `/api/v1/config`
- **认证方式**: Bearer Token
- **Content-Type**: `application/json`

## 端点列表

### 1. 配置查询和获取

#### 获取完整配置
- **URL**: `GET /`
- **描述**: 获取系统完整配置信息
- **响应**: `ConfigResponse`

```json
{
  "success": true,
  "config": {
    "app": {
      "name": "llmstxt-gen",
      "version": "1.0.0"
    }
  },
  "config_info": {
    "config_path": "/path/to/config.yaml",
    "last_modified": "2024-01-01T00:00:00Z",
    "file_size": 1024
  }
}
```

#### 获取特定配置部分
- **URL**: `GET /{section}`
- **描述**: 获取指定配置部分的值
- **参数**: 
  - `section` (path): 配置部分名称
- **响应**: `ConfigSectionResponse`

#### 获取配置信息
- **URL**: `GET /info`
- **描述**: 获取配置文件信息
- **响应**: `ConfigInfoResponse`

### 2. 配置更新和修改

#### 更新配置
- **URL**: `PUT /`
- **描述**: 更新完整配置
- **请求体**: `ConfigUpdateRequest`
- **响应**: `ConfigUpdateResponse`

```json
{
  "config": {
    "app": {
      "name": "new-name"
    }
  },
  "create_backup": true
}
```

#### 更新特定配置部分
- **URL**: `PUT /{section}`
- **描述**: 更新指定配置部分
- **参数**: 
  - `section` (path): 配置部分名称
- **请求体**: 配置数据
- **响应**: `ConfigUpdateResponse`

#### 删除配置部分
- **URL**: `DELETE /{section}`
- **描述**: 删除指定配置部分
- **参数**: 
  - `section` (path): 配置部分名称
- **响应**: `SuccessResponse`

### 3. 配置验证

#### 验证配置
- **URL**: `POST /validate`
- **描述**: 验证配置是否有效
- **请求体**: 配置数据 (可选)
- **响应**: `ConfigValidationResponse`

```json
{
  "valid": true,
  "errors": [],
  "warnings": [],
  "suggestions": []
}
```

#### 获取配置模板
- **URL**: `GET /template/{config_type}`
- **描述**: 获取指定类型的配置模板
- **参数**: 
  - `config_type` (path): 配置类型
- **响应**: 配置模板数据

### 4. 配置导入导出

#### 导出配置
- **URL**: `GET /export/{format}`
- **描述**: 导出配置为指定格式
- **参数**: 
  - `format` (path): 导出格式 (yaml/json)
  - `include_metadata` (query): 是否包含元数据
- **响应**: 文件下载

#### 导入配置
- **URL**: `POST /import/{format}`
- **描述**: 从指定格式导入配置
- **参数**: 
  - `format` (path): 导入格式 (yaml/json)
  - `backup` (query): 是否备份当前配置
- **请求体**: 文件上传
- **响应**: `SuccessResponse`

### 5. 配置历史和版本

#### 获取配置历史
- **URL**: `GET /history`
- **描述**: 获取配置修改历史
- **参数**: 
  - `limit` (query): 返回记录数量限制
- **响应**: `ConfigHistoryResponse`

```json
{
  "history": [
    {
      "id": "version_id",
      "timestamp": "2024-01-01T00:00:00Z",
      "description": "Configuration update",
      "author": "system"
    }
  ]
}
```

#### 回滚配置
- **URL**: `POST /rollback/{version_id}`
- **描述**: 回滚配置到指定版本
- **参数**: 
  - `version_id` (path): 版本ID
- **响应**: `SuccessResponse`

#### 创建版本快照
- **URL**: `POST /snapshot`
- **描述**: 创建当前配置的版本快照
- **请求体**: `ConfigSnapshotRequest`
- **响应**: `SuccessResponse`

### 6. 热重载控制

#### 重载配置
- **URL**: `POST /reload`
- **描述**: 手动重载配置文件
- **响应**: `ConfigReloadResponse`

#### 启动配置监听
- **URL**: `POST /watcher/start`
- **描述**: 启动配置文件监听
- **响应**: `SuccessResponse`

#### 停止配置监听
- **URL**: `POST /watcher/stop`
- **描述**: 停止配置文件监听
- **响应**: `SuccessResponse`

#### 获取监听状态
- **URL**: `GET /watcher/status`
- **描述**: 获取配置文件监听状态
- **响应**: `WatcherStatusResponse`

### 7. WebSocket 通知

#### 连接通知服务
- **URL**: `ws://localhost:8000/api/v1/config/notifications`
- **描述**: 连接配置变更通知的WebSocket
- **消息格式**: `NotificationMessage`

```json
{
  "type": "config_changed",
  "level": "info",
  "message": "Configuration file has been modified",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "change_type": "modified",
    "file_path": "/path/to/config.yaml"
  }
}
```

## 数据模型

### ConfigResponse
```typescript
interface ConfigResponse {
  success: boolean;
  config: Record<string, any>;
  config_info: ConfigInfo;
}
```

### ConfigUpdateRequest
```typescript
interface ConfigUpdateRequest {
  config: Record<string, any>;
  create_backup?: boolean;
}
```

### ConfigValidationResult
```typescript
interface ConfigValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
  suggestions: string[];
}
```

### ConfigHistory
```typescript
interface ConfigHistory {
  id: string;
  timestamp: string;
  description: string;
  author: string;
  changes?: Record<string, any>;
}
```

## 错误处理

API 使用标准 HTTP 状态码表示错误：

- `200 OK`: 请求成功
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 未授权
- `404 Not Found`: 资源不存在
- `422 Unprocessable Entity`: 数据验证失败
- `500 Internal Server Error`: 服务器内部错误

错误响应格式：
```json
{
  "detail": "错误描述信息"
}
```

## 使用示例

### 获取配置
```bash
curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/v1/config/
```

### 更新配置
```bash
curl -X PUT \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"config": {"app": {"name": "new-name"}}}' \
     http://localhost:8000/api/v1/config/
```

### 导出配置
```bash
curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/v1/config/export/yaml \
     --output config.yaml
```

### 验证配置
```bash
curl -X POST \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"app": {"name": "test"}}' \
     http://localhost:8000/api/v1/config/validate
```