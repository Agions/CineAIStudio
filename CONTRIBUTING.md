# 🤝 贡献指南

感谢你对 ClipFlowCut 项目的兴趣！欢迎贡献代码、文档或提出问题。

## 📋 行为准则

请阅读并遵守我们的 [行为准则](CODE_OF_CONDUCT.md)。保持友好、包容和专业的交流环境。

## 🚀 快速开始

### 开发环境搭建

```bash
# 克隆项目
git clone https://github.com/your-repo/ClipFlowCut.git
cd ClipFlowCut

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 运行应用
python main.py
```

### 前置要求

- Python 3.9+
- FFmpeg (系统级安装)
- PyQt6

## 🏗️ 项目结构

```
ClipFlowCut/
├── app/                    # 应用核心代码
│   ├── core/              # 核心模块
│   ├── services/          # AI 服务
│   ├── ui/                # 界面组件
│   └── utils/             # 工具类
├── config/                # 配置文件
├── docs/                  # 项目文档
├── resources/             # 资源文件
├── scripts/               # 脚本工具
└── tests/                 # 测试代码
```

## 🔧 开发指南

### 代码风格

- 遵循 PEP 8
- 使用 type hints
- 使用 Black 格式化代码
- 使用 isort 排序 import

```bash
# 安装开发依赖
pip install black isort mypy pylint

# 格式化代码
black app/
isort app/

# 类型检查
mypy app/

# 代码检查
pylint app/
```

### 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型 (type):**
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具链更新

**示例:**
```
feat(ai): 添加 Kimi K2.5 模型支持

- 支持 Kimi K2.5 多模态理解
- 优化上下文窗口处理
- 添加流式响应支持

Closes #123
```

### Git 工作流

1. Fork 项目
2. 创建功能分支: `git checkout -b feature/amazing-feature`
3. 提交更改: `git commit -m 'feat: 添加超棒的功能'`
4. 推送分支: `git push origin feature/amazing-feature`
5. 创建 Pull Request

## 🧪 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定模块测试
pytest tests/services/ -v

# 带覆盖率运行
pytest tests/ --cov=app --cov-report=html
```

## 📝 文档

- API 文档使用 Sphinx 生成
- 用户文档使用 VitePress
- 请确保新增功能有对应的文档说明

## 🐛 报告问题

请使用 GitHub Issues 并包含：

1. **问题描述**: 清晰描述问题
2. **复现步骤**: 详细的重现步骤
3. **预期行为**: 应该发生什么
4. **实际行为**: 实际发生了什么
5. **环境信息**: OS、Python 版本等
6. **截图/日志**: 如果有的话

## 💬 参与讨论

- GitHub Discussions: 问题解答和功能讨论
- Discord: 实时聊天讨论

## 📜 许可证

贡献的代码将遵循项目的 MIT 许可证。

---

感谢你的贡献！ 🎉
