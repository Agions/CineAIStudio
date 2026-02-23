# CONTRIBUTING.md - 贡献指南

感谢你对 CineFlow 的关注！欢迎贡献代码。

## 开发环境设置

```bash
# 1. 克隆项目
git clone https://github.com/Agions/cine-flow.git
cd cine-flow

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 安装开发依赖
pip install pytest black flake8 mypy isort
```

## 代码规范

### 格式化

```bash
# Black 格式化
black app/ tests/

# isort 导入排序
isort app/ tests/

# flake8 检查
flake8 app/ --max-line-length=88
```

### 类型检查

```bash
mypy app/ --ignore-missing-imports
```

### 测试

```bash
# 运行测试
pytest tests/ -v

# 带覆盖率
pytest tests/ --cov=app --cov-report=html
```

## 提交规范

### 提交信息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试
- `chore`: 构建/工具

### 示例

```
feat(ai): 添加 DeepSeek LLM 支持

- 新增 DeepSeekProvider 类
- 支持 Chat 和 Coder 模型
- 更新 README 文档

Closes #123
```

## 分支管理

- `main`: 主分支，稳定版本
- `develop`: 开发分支
- `feature/*`: 功能分支
- `fix/*`: 修复分支

## 提交步骤

```bash
# 1. 创建分支
git checkout -b feature/your-feature

# 2. 开发并测试
# ...

# 3. 提交更改
git add .
git commit -m "feat: 添加新功能"

# 4. 推送并创建 PR
git push -u origin feature/your-feature
```

## 代码审查清单

- [ ] 代码符合格式化规范
- [ ] 通过所有测试
- [ ] 添加了必要的文档
- [ ] 提交信息清晰

---

有问题？请提交 Issue 或讨论。
