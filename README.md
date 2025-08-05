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
- **数据库**: SQLite (MVP) / PostgreSQL (生产)
- **AI服务**: OpenAI API
- **文档处理**: PyPDF2, python-docx, BeautifulSoup
- **爬取框架**: crawl4ai
- **部署**: Docker + Docker Compose

## 项目状态

- ✅ **需求分析完成**: 完整的PRD和项目简报
- ✅ **架构设计完成**: 详细的系统架构设计文档
- 🚀 **准备开发**: 即将开始Epic 1开发

## 文档

- [产品需求文档](docs/prd.md)
- [系统架构设计](docs/architecture.md)
- [项目简报](docs/brief.md)

## 快速开始

### 开发环境要求

- Python 3.11+
- Node.js 18+
- Docker (可选)

### 安装步骤

```bash
# 克隆项目
git clone https://github.com/18981119465/llmstxt-gen.git
cd llms.txt-gen

# 安装后端依赖
pip install -r requirements.txt

# 安装前端依赖
cd frontend
npm install

# 启动开发服务器
npm run dev
```

### Docker快速启动

```bash
docker-compose up -d
```

## 开发计划

### Epic 1: 项目基础架构与核心服务 (进行中)
- 项目初始化与开发环境配置
- 配置管理系统
- 日志与监控系统
- 基础API服务框架

### 后续史诗

- Epic 2: 文档处理引擎
- Epic 3: 网站爬取系统
- Epic 4: AI智能处理服务
- Epic 5: 本地HTTP服务
- Epic 6: Web用户界面
- Epic 7: 系统集成与测试

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- 项目维护者: John (PM)
- 技术架构师: Claude AI