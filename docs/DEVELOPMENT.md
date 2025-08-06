# Development Guide

## 开发环境设置

### 前置要求

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

### 1. 项目克隆

```bash
git clone https://github.com/18981119465/llmstxt-gen.git
cd llms.txt-gen
```

### 2. 环境配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量，填入必要的配置
nano .env
```

必须配置的环境变量：
- `DATABASE_URL`: 数据库连接字符串
- `REDIS_URL`: Redis连接字符串
- `SECRET_KEY`: 应用密钥
- `OPENAI_API_KEY`: OpenAI API密钥
- `ANTHROPIC_API_KEY`: Anthropic API密钥

### 3. 开发环境启动

```bash
# 使用自动化脚本启动
./scripts/dev-setup.sh

# 或手动启动Docker服务
docker-compose up -d
```

### 4. 验证安装

```bash
# 检查服务状态
docker-compose ps

# 测试后端API
curl http://localhost:8000/health

# 测试前端
curl http://localhost:3000
```

## 开发工作流程

### Git工作流程

1. **获取最新代码**
   ```bash
   git pull origin main
   git checkout develop
   git pull origin develop
   ```

2. **创建功能分支**
   ```bash
   ./scripts/git-workflow.sh feature your-feature-name
   ```

3. **开发代码**
   ```bash
   # 编写代码
   # 运行测试
   # 代码质量检查
   ```

4. **提交更改**
   ```bash
   git add .
   git commit -m "feat: add your feature"
   git push origin feature/your-feature-name
   ```

5. **创建Pull Request**
   - 在GitHub上创建PR
   - 等待代码审查
   - 合并到develop分支

6. **完成开发**
   ```bash
   ./scripts/git-workflow.sh finish
   ```

### 代码质量标准

#### Python代码规范

- 遵循PEP 8规范
- 使用类型注解
- 代码长度限制88字符
- 使用Black格式化
- 使用Pylint检查

```bash
# 格式化代码
cd backend
black .

# 检查代码质量
pylint src/

# 类型检查
mypy src/
```

#### TypeScript代码规范

- 使用ESLint + Prettier
- 严格类型检查
- 组件和服务的标准化

```bash
# 格式化代码
cd frontend
npm run format

# 检查代码质量
npm run lint

# 类型检查
npm run type-check
```

### 测试规范

#### 测试要求

- 所有新功能必须有单元测试
- 关键流程必须有集成测试
- 测试覆盖率要求80%+
- 测试必须通过才能合并

#### 运行测试

```bash
# 后端测试
cd backend
pytest --cov=src --cov-report=term-missing

# 前端测试
cd frontend
npm test

# 端到端测试
npm run test:e2e
```

## 项目架构

### 目录结构

```
llms.txt-gen/
├── frontend/                 # React前端应用
│   ├── src/
│   │   ├── components/      # 组件库
│   │   ├── pages/          # 页面组件
│   │   ├── services/       # API服务
│   │   ├── utils/          # 工具函数
│   │   ├── hooks/          # 自定义Hook
│   │   └── types/          # TypeScript类型
│   ├── tests/              # 测试文件
│   └── package.json
├── backend/                 # FastAPI后端服务
│   ├── src/
│   │   ├── models/         # 数据模型
│   │   ├── services/       # 业务逻辑
│   │   ├── api/           # API路由
│   │   └── utils/         # 工具函数
│   ├── tests/              # 测试文件
│   └── requirements.txt
├── ai-service/              # AI处理服务
├── document-processor/     # 文档处理引擎
├── web-crawler/           # 网站爬取系统
├── http-content/          # HTTP内容服务
├── shared/                # 共享代码
├── docker/                # Docker配置
├── scripts/               # 开发脚本
└── tests/                 # 集成测试
```

### 模块职责

#### 前端模块 (frontend/)
- 用户界面展示
- 用户交互处理
- API调用
- 状态管理

#### 后端模块 (backend/)
- RESTful API
- 数据库操作
- 业务逻辑
- 用户认证

#### AI服务模块 (ai-service/)
- 文本分析
- 内容生成
- 模型集成
- AI处理任务

#### 文档处理模块 (document-processor/)
- 文档解析
- 格式转换
- 内容提取
- 文档分块

#### 网站爬取模块 (web-crawler/)
- 网页爬取
- 内容过滤
- 链接管理
- 反爬虫处理

#### HTTP内容服务 (http-content/)
- 静态文件服务
- 内容检索
- 缓存管理
- 访问控制

## 开发工具

### 命令行工具

```bash
# 开发环境管理
./scripts/dev-setup.sh      # 启动开发环境
./scripts/git-setup.sh      # Git工作流设置
./scripts/git-workflow.sh   # Git工作流管理
./scripts/code-quality.sh   # 代码质量检查

# Docker管理
docker-compose up -d        # 启动所有服务
docker-compose down         # 停止所有服务
docker-compose logs -f      # 查看日志
docker-compose ps           # 查看服务状态
```

### IDE配置

#### VSCode推荐插件

- Python: Python, Pylance, Black Formatter
- TypeScript: TypeScript Importer, ESLint, Prettier
- Docker: Docker
- Git: GitLens, Git History
- 测试: Jest Runner, Python Test Explorer

#### PyCharm配置

- 设置Python解释器
- 配置Docker Compose
- 设置代码检查工具
- 配置测试运行器

## 调试和故障排除

### 常见问题

#### 1. Docker容器启动失败

```bash
# 检查Docker服务状态
docker-compose logs

# 重新构建容器
docker-compose build --no-cache

# 清理Docker资源
docker-compose down -v
docker system prune -a
```

#### 2. 数据库连接问题

```bash
# 检查数据库容器状态
docker-compose ps postgres

# 查看数据库日志
docker-compose logs postgres

# 手动连接数据库
docker-compose exec postgres psql -U postgres -d llms_txt_gen
```

#### 3. 前端构建失败

```bash
# 清理node_modules
rm -rf node_modules package-lock.json
npm install

# 清理Next.js缓存
rm -rf .next
npm run build
```

#### 4. 后端依赖问题

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 日志查看

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend

# 查看应用日志
docker-compose exec backend tail -f logs/app.log
```

## 部署指南

### 开发环境部署

```bash
# 启动开发环境
docker-compose up -d

# 更新代码
git pull origin main
docker-compose build
docker-compose up -d
```

### 生产环境部署

```bash
# 构建生产镜像
docker-compose -f docker-compose.prod.yml build

# 启动生产环境
docker-compose -f docker-compose.prod.yml up -d

# 运行数据库迁移
docker-compose exec backend python -m alembic upgrade head
```

### Kubernetes部署

```bash
# 部署到K8s集群
kubectl apply -f k8s/

# 查看部署状态
kubectl get pods -l app=llms-txt-gen

# 查看服务状态
kubectl get svc llms-txt-gen
```

## 性能优化

### 代码优化

#### 后端优化

- 使用异步I/O (async/await)
- 数据库查询优化
- 缓存策略
- 连接池管理

#### 前端优化

- 组件懒加载
- 图片优化
- 代码分割
- 缓存策略

### 数据库优化

- 索引优化
- 查询优化
- 连接池配置
- 读写分离

## 安全考虑

### 代码安全

- 输入验证
- SQL注入防护
- XSS防护
- CSRF防护

### 部署安全

- 环境变量管理
- HTTPS配置
- 防火墙配置
- 访问控制

## 贡献指南

### 代码审查

- 代码必须通过所有测试
- 代码质量检查必须通过
- 文档必须更新
- 提交信息必须规范

### 文档更新

- 新功能需要更新README
- API变更需要更新API文档
- 配置变更需要更新配置文档
- 架构变更需要更新架构文档

### 问题报告

- 使用GitHub Issues报告问题
- 提供详细的复现步骤
- 包含错误日志和截图
- 标注问题的严重程度

## 联系支持

- 开发团队：通过GitHub Issues
- 紧急问题：创建高优先级Issue
- 功能请求：使用Feature Request模板
- 文档问题：直接在文档文件中提出