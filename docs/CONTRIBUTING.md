# 贡献指南

感谢您对 llms.txt-gen 项目的兴趣！我们欢迎所有形式的贡献。

## 如何贡献

### 报告问题

如果您发现了bug或有功能建议，请：

1. 检查是否已有相关Issue
2. 创建新的Issue，使用适当的模板
3. 提供详细的信息：
   - 问题的详细描述
   - 复现步骤
   - 期望的行为
   - 实际的行为
   - 错误日志
   - 环境信息

### 代码贡献

#### 开发流程

1. **Fork项目**
   ```bash
   # Fork并克隆项目
   git clone https://github.com/YOUR_USERNAME/llms.txt-gen.git
   cd llms.txt-gen
   ```

2. **设置上游仓库**
   ```bash
   git remote add upstream https://github.com/18981119465/llms.txt-gen.git
   ```

3. **创建功能分支**
   ```bash
   git checkout develop
   git pull upstream develop
   git checkout -b feature/your-feature-name
   ```

4. **开发代码**
   - 遵循代码规范
   - 编写测试
   - 更新文档

5. **提交更改**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

6. **推送分支**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **创建Pull Request**
   - 在GitHub上创建PR
   - 填写PR描述
   - 链接相关Issue
   - 等待审查

#### 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**类型 (type):**
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式化（不影响代码运行）
- `refactor`: 重构（既不是新功能也不是修复bug）
- `test`: 测试相关
- `build`: 构建相关
- `ci`: CI/CD相关
- `chore`: 其他更改

**示例：**
```bash
feat(auth): add user login functionality
fix(api): resolve memory leak in data processing
docs(readme): update installation instructions
style(format): apply black formatting to backend code
```

#### 代码质量要求

**Python代码:**
- 遵循PEP 8规范
- 使用类型注解
- 代码长度限制88字符
- 必须通过Black格式化
- 必须通过Pylint检查
- 测试覆盖率80%+

**TypeScript代码:**
- 使用ESLint + Prettier
- 严格类型检查
- 组件和服务的标准化
- 必须通过所有检查

**测试要求:**
- 所有新功能必须有单元测试
- 关键流程必须有集成测试
- 测试必须通过才能合并
- 保持测试覆盖率

### 文档贡献

文档改进同样重要！您可以：

1. 修正拼写错误和语法问题
2. 改进文档结构和可读性
3. 添加缺失的文档
4. 更新过时的信息
5. 添加示例和教程

### 设计贡献

如果您是设计师，可以：

1. 改进UI/UX设计
2. 创建新的图标和图形
3. 优化用户体验
4. 提供设计反馈

## 开发环境设置

### 前置要求

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

### 环境设置

```bash
# 克隆项目
git clone https://github.com/YOUR_USERNAME/llms.txt-gen.git
cd llms.txt-gen

# 设置环境变量
cp .env.example .env
# 编辑 .env 文件

# 启动开发环境
./scripts/dev-setup.sh
```

### 验证设置

```bash
# 运行测试
./scripts/code-quality.sh

# 检查服务状态
docker-compose ps
```

## 代码审查流程

### Pull Request审查

1. **自动化检查**
   - 代码格式化检查
   - 代码质量检查
   - 测试运行
   - 安全扫描

2. **人工审查**
   - 代码逻辑审查
   - 架构设计审查
   - 性能影响评估
   - 安全性评估

### 审查标准

- **代码质量**: 代码是否清晰、可维护
- **测试覆盖**: 是否有足够的测试
- **文档**: 是否有适当的文档
- **性能**: 是否会影响系统性能
- **安全**: 是否存在安全风险
- **兼容性**: 是否向后兼容

## 发布流程

### 版本号规范

使用 [Semantic Versioning](https://semver.org/)：

- `MAJOR.MINOR.PATCH`
- `MAJOR`: 不兼容的API更改
- `MINOR`: 向后兼容的功能新增
- `PATCH`: 向后兼容的bug修复

### 发布步骤

1. 更新版本号
2. 更新CHANGELOG
3. 创建发布标签
4. 构建和发布
5. 更新文档

## 社区准则

### 行为准则

- 尊重所有贡献者
- 提供建设性的反馈
- 专注于技术讨论
- 保持耐心和理解

### 沟通指南

- 使用清晰、简洁的语言
- 提供足够的上下文
- 专注于解决问题
- 保持专业和礼貌

## 获得帮助

### 技术问题

- 查看 [文档](docs/)
- 搜索现有的Issues
- 创建新的Issue

### 社区支持

- GitHub Discussions
- Issue评论区
- Pull Request讨论

### 联系维护者

- 通过GitHub @mention
- 在Issue中请求帮助

## 贡献者认可

### 贡献者列表

所有贡献者都会在项目的贡献者文件中得到认可。

### 贡献者奖励

- 代码贡献者会在发布说明中被提及
- 长期贡献者可能会被邀请成为维护者
- 重大贡献者会获得特殊的认可

## 许可证

通过贡献代码，您同意您的贡献将在项目的 [MIT许可证](LICENSE) 下发布。

## 常见问题

### 我如何开始？

1. 从小的bug修复开始
2. 查看 "good first issue" 标签的Issues
3. 从文档改进开始
4. 参与讨论和审查

### 我的PR被拒绝了怎么办？

- 不要灰心，这是正常的
- 仔细阅读审查意见
- 根据反馈进行修改
- 重新提交PR

### 我如何成为维护者？

- 持续贡献高质量的代码
- 积极参与代码审查
- 帮助解答社区问题
- 展示对项目的深入理解

---

再次感谢您的贡献！🎉