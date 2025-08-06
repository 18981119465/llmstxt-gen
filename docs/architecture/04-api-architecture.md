# llms.txt-gen 系统架构设计文档 - API架构设计

*版本：v1.0*  
*生成日期：2025-01-05*  

---

## 4. API架构设计

### 4.1 API设计原则

- **RESTful设计**：遵循REST架构风格
- **版本控制**：API版本号在URL中（/api/v1/）
- **统一响应格式**：标准化的JSON响应结构
- **状态码使用**：正确使用HTTP状态码
- **错误处理**：统一的错误响应格式
- **安全性**：认证、授权、限流、CORS

### 4.2 API端点设计

#### 4.2.1 认证相关
```python
# 用户注册
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/logout
POST /api/v1/auth/refresh
GET  /api/v1/auth/profile
PUT  /api/v1/auth/profile
```

#### 4.2.2 项目管理
```python
GET    /api/v1/projects
POST   /api/v1/projects
GET    /api/v1/projects/{project_id}
PUT    /api/v1/projects/{project_id}
DELETE /api/v1/projects/{project_id}
```

#### 4.2.3 文档管理
```python
# 文档上传
POST   /api/v1/projects/{project_id}/documents
GET    /api/v1/projects/{project_id}/documents
GET    /api/v1/documents/{document_id}
PUT    /api/v1/documents/{document_id}
DELETE /api/v1/documents/{document_id}

# 文档处理
POST   /api/v1/documents/{document_id}/process
GET    /api/v1/documents/{document_id}/status
GET    /api/v1/documents/{document_id}/result
```

#### 4.2.4 爬取管理
```python
# 爬取任务
POST   /api/v1/projects/{project_id}/crawl
GET    /api/v1/projects/{project_id}/crawl-tasks
GET    /api/v1/crawl-tasks/{task_id}
PUT    /api/v1/crawl-tasks/{task_id}
DELETE /api/v1/crawl-tasks/{task_id}

# 爬取结果
GET    /api/v1/crawl-tasks/{task_id}/results
GET    /api/v1/crawl-results/{result_id}
```

#### 4.2.5 AI处理
```python
# AI任务
POST   /api/v1/documents/{document_id}/ai-process
GET    /api/v1/ai-tasks/{task_id}
GET    /api/v1/ai-tasks/{task_id}/result

# 内容查询
POST   /api/v1/content/search
GET    /api/v1/content/{content_id}
GET    /api/v1/content/{content_id}/llms-txt
```

#### 4.2.6 系统管理
```python
GET    /api/v1/system/status
GET    /api/v1/system/config
PUT    /api/v1/system/config
GET    /api/v1/system/logs
```

### 4.3 响应格式设计

#### 4.3.1 成功响应
```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "timestamp": "2025-01-05T10:00:00Z",
  "request_id": "req_123456789"
}
```

#### 4.3.2 错误响应
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "details": {
      "field": "email",
      "message": "邮箱格式不正确"
    }
  },
  "timestamp": "2025-01-05T10:00:00Z",
  "request_id": "req_123456789"
}
```

#### 4.3.3 分页响应
```json
{
  "success": true,
  "data": {
    "items": [],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 100,
      "pages": 5
    }
  },
  "message": "查询成功",
  "timestamp": "2025-01-05T10:00:00Z",
  "request_id": "req_123456789"
}
```

### 4.4 WebSocket API

#### 4.4.1 实时通信端点
```python
# 任务状态更新
/ws/tasks/{task_id}/status

# 文档处理进度
/ws/documents/{document_id}/progress

# 系统通知
/ws/notifications
```

---

*文档分片自：docs/architecture.md - 第4部分*