# llms.txt-gen

智能文档处理和AI知识管理工具

## 项目概述

llms.txt-gen 是一个基于crawl4ai框架的智能工具，专为AI开发者设计，用于自动爬取网站内容并生成优化的llms.txt文件。该工具解决了AI开发者面临的第三方库API文档更新频率快、AI模型训练数据滞后的核心痛点。

## 核心功能

- 🕷️ **网站内容爬取**: 基于crawl4ai框架的智能爬取系统
- 📄 **多格式文档处理**: 支持PDF、Word、Markdown、HTML、TXT等格式
- 🤖 **AI智能处理**: 集成OpenAI API进行内容分析和优化
- 📋 **llms.txt生成**: 生成符合AI理解标准的内容文件
- 🌐 **本地HTTP服务**: 提供处理后的文档内容访问服务
- 🎛️ **Web管理界面**: 直观的用户界面和配置管理

## 技术栈

- **前端**: React + TypeScript + Next.js
- **后端**: Python + FastAPI
- **数据库**: PostgreSQL + Redis
- **AI服务**: OpenAI API + Anthropic API
- **文档处理**: PyPDF2, python-docx, BeautifulSoup
- **爬取框架**: crawl4ai
- **部署**: Docker + Docker Compose + Kubernetes

## 项目状态

- ✅ **项目初始化完成**: 完整的开发环境配置
- ✅ **架构设计完成**: 详细的系统架构设计文档
- ✅ **CI/CD配置**: 自动化构建和部署流程
- 🚀 **开发就绪**: 可以开始功能开发

## 快速开始

### 开发环境要求

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

### 1. 克隆项目

```bash
git clone https://github.com/18981119465/llmstxt-gen.git
cd llms.txt-gen
```

### 2. 环境配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量，填入你的API密钥
nano .env
```

### 3. 启动开发环境

```bash
# 使用Docker Compose启动所有服务
./scripts/dev-setup.sh

# 或者手动启动
docker-compose up -d
```

### 4. 访问服务

- **前端应用**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **数据库**: localhost:5432
- **Redis**: localhost:6379

## 开发指南

### Git工作流程

```bash
# 安装Git钩子
./scripts/git-setup.sh

# 创建功能分支
./scripts/git-workflow.sh feature your-feature-name

# 完成开发后合并分支
./scripts/git-workflow.sh finish
```

### 代码质量检查

```bash
# 运行所有代码质量检查
./scripts/code-quality.sh

# 或者单独运行检查
# 后端
cd backend && black --check . && pylint src/
# 前端
cd frontend && npm run lint && npm run type-check
```

### 测试

```bash
# 后端测试
cd backend && pytest

# 前端测试
cd frontend && npm test

# 端到端测试
npm run test:e2e
```

## 项目结构

```
llms.txt-gen/
├── frontend/           # React + Next.js 前端服务
├── backend/            # FastAPI 后端服务
├── ai-service/         # AI 处理服务
├── document-processor/ # 文档处理引擎
├── web-crawler/        # 网站爬取系统
├── http-content/       # HTTP 内容服务
├── docs/              # 项目文档
├── .github/           # GitHub Actions 和配置
├── docker/            # Docker 配置文件
├── scripts/           # 开发和部署脚本
├── tests/             # 测试文件
└── shared/            # 共享代码和资源
```

## 文档

- [产品需求文档](docs/prd.md)
- [系统架构设计](docs/architecture.md)
- [前端UI/UX规范](docs/front-end-spec.md)
- [开发故事](docs/stories/)
- [API文档](http://localhost:8000/docs)

## 环境变量

参考 `.env.example` 文件配置环境变量：

```bash
# 数据库配置
DATABASE_URL=postgresql://postgres:password@localhost:5432/llms_txt_gen
REDIS_URL=redis://localhost:6379

# AI服务配置
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# 应用配置
SECRET_KEY=your-secret-key
DEBUG=True
```

## 开发计划

### Epic 1: 项目基础架构与核心服务 ✅
- [x] 项目初始化与开发环境配置
- [x] 配置管理系统
- [x] 日志与监控系统
- [x] 基础API服务框架
- [x] CI/CD流水线

### Epic 2: 文档处理引擎
- [ ] PDF处理模块
- [ ] Word文档处理
- [ ] Markdown处理
- [ ] HTML内容提取
- [ ] 文档分块和索引

### Epic 3: 网站爬取系统
- [ ] crawl4ai集成
- [ ] 爬取策略配置
- [ ] 内容过滤和清理
- [ ] 反爬虫处理
- [ ] 爬取任务管理

### Epic 4: AI智能处理服务
- [ ] OpenAI API集成
- [ ] 内容分析和优化
- [ ] llms.txt格式生成
- [ ] 内容质量评估
- [ ] 多模型支持

### Epic 5: 本地HTTP服务
- [ ] 静态文件服务
- [ ] 内容检索API
- [ ] 缓存机制
- [ ] 访问控制
- [ ] 性能优化

### Epic 6: Web用户界面
- [ ] 用户管理系统
- [ ] 文档上传界面
- [ ] 爬取配置界面
- [ ] 结果展示界面
- [ ] 系统监控面板

### Epic 7: 系统集成与测试
- [ ] 端到端测试
- [ ] 性能测试
- [ ] 安全测试
- [ ] 部署自动化
- [ ] 监控和日志

## 贡献指南

### 开发流程

1. Fork 项目
2. 创建功能分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -m 'feat: add your feature'`
4. 推送分支：`git push origin feature/your-feature`
5. 创建Pull Request

### 提交信息规范

使用 Conventional Commits 格式：

```
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式化
refactor: 重构
test: 测试相关
build: 构建相关
ci: CI/CD相关
chore: 其他更改
```

### 代码质量要求

- Python代码遵循PEP 8规范
- TypeScript代码使用ESLint + Prettier
- 所有新功能必须有单元测试
- 代码覆盖率要求80%+
- 通过所有CI/CD检查

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- 项目维护者: John (PM)
- 技术架构师: Claude AI
- 开发团队: James (Dev)

## 致谢

感谢所有为这个项目做出贡献的开发者！