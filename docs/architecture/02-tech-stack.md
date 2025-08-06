# llms.txt-gen 系统架构设计文档 - 技术栈设计

*版本：v1.0*  
*生成日期：2025-01-05*  

---

## 2. 技术栈详细设计

### 2.1 前端技术栈

#### 2.1.1 核心框架
- **React 18**：现代UI组件库，支持并发特性
- **TypeScript**：类型安全，提高代码质量
- **Next.js 14**：全栈框架，支持SSR和静态生成
- **Tailwind CSS**：实用优先的CSS框架，支持Airbnb风格

#### 2.1.2 状态管理
- **Zustand**：轻量级状态管理库
- **React Query**：服务器状态管理，缓存和同步
- **SWR**：数据获取库，支持实时更新

#### 2.1.3 UI组件库
- **自定义组件库**：基于Airbnb设计风格
- **React Icons**：图标库
- **React Hook Form**：表单处理
- **React Dropzone**：文件上传组件

#### 2.1.4 构建工具
- **Vite**：快速构建工具
- **ESLint + Prettier**：代码质量和格式化
- **Husky**：Git hooks管理

### 2.2 后端技术栈

#### 2.2.1 Web框架
- **FastAPI**：现代异步Web框架
- **Pydantic**：数据验证和序列化
- **Uvicorn**：ASGI服务器
- **Gunicorn**：WSGI HTTP服务器

#### 2.2.2 数据库
- **PostgreSQL 15+**：主数据库，存储元数据
- **SQLite**：开发环境数据库
- **Redis 7+**：缓存和会话存储
- **ChromaDB**：向量数据库，存储文档嵌入

#### 2.2.3 任务队列
- **Celery**：异步任务队列
- **Redis**：消息代理
- **Flower**：任务监控界面

#### 2.2.4 文档处理
- **PyPDF2**：PDF文档处理
- **python-docx**：Word文档处理
- **BeautifulSoup4**：HTML解析
- **Markdown**：Markdown处理
- **python-magic**：文件类型检测

### 2.3 AI服务集成

#### 2.3.1 OpenAI集成
- **openai-python**：官方Python客户端
- **LangChain**：AI应用开发框架
- **tiktoken**：Token计算
- **Tenacity**：重试机制

#### 2.3.2 本地模型支持
- **llama-cpp-python**：本地LLM支持
- **transformers**：Hugging Face模型
- **sentence-transformers**：句子嵌入

### 2.4 爬取技术栈

#### 2.4.1 核心爬取
- **crawl4ai**：主要爬取框架
- **aiohttp**：异步HTTP客户端
- **beautifulsoup4**：HTML解析
- **lxml**：XML/HTML解析器

#### 2.4.2 反爬虫处理
- **fake-useragent**：User-Agent轮换
- **aiohttp-client-session**：会话管理
- **proxy-chain**：代理支持

---

*文档分片自：docs/architecture.md - 第2部分*