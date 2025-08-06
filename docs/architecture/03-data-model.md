# llms.txt-gen 系统架构设计文档 - 数据模型设计

*版本：v1.0*  
*生成日期：2025-01-05*  

---

## 3. 数据模型设计

### 3.1 数据库架构

#### 3.1.1 主数据库表结构

```sql
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 项目表
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id UUID REFERENCES users(id),
    config JSONB,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 文档表
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'pdf', 'word', 'markdown', 'html', 'txt', 'web'
    source_url TEXT,
    file_path VARCHAR(500),
    file_size BIGINT,
    metadata JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 文档内容表
CREATE TABLE document_contents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id),
    chunk_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    tokens INTEGER,
    embedding VECTOR(1536),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 爬取任务表
CREATE TABLE crawl_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    name VARCHAR(255) NOT NULL,
    config JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    total_pages INTEGER,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 爬取结果表
CREATE TABLE crawl_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES crawl_tasks(id),
    url TEXT NOT NULL,
    title VARCHAR(500),
    content TEXT,
    extracted_data JSONB,
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT,
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI处理任务表
CREATE TABLE ai_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id),
    task_type VARCHAR(50) NOT NULL, -- 'analysis', 'optimization', 'chunking'
    model VARCHAR(50) DEFAULT 'gpt-3.5-turbo',
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost DECIMAL(10, 6),
    status VARCHAR(20) DEFAULT 'pending',
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- 系统配置表
CREATE TABLE system_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(100) UNIQUE NOT NULL,
    value JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 操作日志表
CREATE TABLE operation_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    metadata JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.1.2 索引设计

```sql
-- 文档表索引
CREATE INDEX idx_documents_project_id ON documents(project_id);
CREATE INDEX idx_documents_type ON documents(type);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_created_at ON documents(created_at);

-- 文档内容表索引
CREATE INDEX idx_document_contents_document_id ON document_contents(document_id);
CREATE INDEX idx_document_contents_chunk_number ON document_contents(document_id, chunk_number);
CREATE INDEX idx_document_contents_embedding ON document_contents USING hnsw (embedding vector_cosine_ops);

-- 爬取任务表索引
CREATE INDEX idx_crawl_tasks_project_id ON crawl_tasks(project_id);
CREATE INDEX idx_crawl_tasks_status ON crawl_tasks(status);
CREATE INDEX idx_crawl_tasks_created_at ON crawl_tasks(created_at);

-- AI任务表索引
CREATE INDEX idx_ai_tasks_document_id ON ai_tasks(document_id);
CREATE INDEX idx_ai_tasks_task_type ON ai_tasks(task_type);
CREATE INDEX idx_ai_tasks_status ON ai_tasks(status);
CREATE INDEX idx_ai_tasks_created_at ON ai_tasks(created_at);

-- 操作日志表索引
CREATE INDEX idx_operation_logs_user_id ON operation_logs(user_id);
CREATE INDEX idx_operation_logs_action ON operation_logs(action);
CREATE INDEX idx_operation_logs_created_at ON operation_logs(created_at);
```

### 3.2 缓存策略

#### 3.2.1 Redis缓存设计
- **用户会话缓存**：TTL 24小时
- **API响应缓存**：TTL 1小时
- **文档处理结果缓存**：TTL 7天
- **爬取结果缓存**：TTL 24小时
- **AI处理结果缓存**：TTL 30天

#### 3.2.2 缓存键命名规范
```
llms:session:{session_id}
llms:api:{endpoint}:{hash}
llms:doc:{document_id}:{version}
llms:crawl:{task_id}:{url_hash}
llms:ai:{task_id}:{model}
```

### 3.3 文件存储设计

#### 3.3.1 目录结构
```
/storage/
├── documents/           # 原始文档
│   ├── pdf/
│   ├── word/
│   ├── markdown/
│   ├── html/
│   └── txt/
├── processed/          # 处理后的文档
│   ├── chunks/
│   ├── embeddings/
│   └── optimized/
├── cache/             # 缓存文件
├── logs/              # 日志文件
└── temp/              # 临时文件
```

#### 3.3.2 文件命名规范
```
原始文档: {document_id}.{extension}
处理后的分块: {document_id}_chunk_{chunk_number}.txt
嵌入向量: {document_id}_embedding_{chunk_number}.npy
优化后内容: {document_id}_optimized_{chunk_number}.txt
```

---

*文档分片自：docs/architecture.md - 第3部分*