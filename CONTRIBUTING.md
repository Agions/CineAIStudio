# 贡献指南

感谢您对 CineFlow AI 项目的关注！我们欢迎各种形式的贡献，包括但不限于代码、文档、测试、问题和建议。

## 🤝 贡献方式

### 报告问题
- 使用 [GitHub Issues](https://github.com/agions/CineFlow AI/issues) 报告 bug
- 提供详细的重现步骤和系统信息
- 包含相关的日志文件和截图

### 功能建议
- 在 Issues 中使用 "enhancement" 标签
- 详细描述功能需求和使用场景
- 说明预期的工作流程和用户体验

### 代码贡献
- Fork 项目到您的 GitHub 账户
- 创建功能分支：`git checkout -b feature/your-feature-name`
- 提交更改：`git commit -m "Add some feature"`
- 推送到分支：`git push origin feature/your-feature-name`
- 创建 Pull Request

### 文档改进
- 修正文档中的错误或不准确信息
- 改进现有文档的可读性
- 添加缺失的文档内容
- 翻译文档到其他语言

## 🏗️ 开发环境设置

### 环境要求
- Python 3.8+ (推荐 3.12+)
- Git
- 推荐使用 PyCharm、VSCode 等 IDE

### 克隆项目
```bash
git clone https://github.com/agions/CineFlow AI.git
cd CineFlow AI
```

### 设置开发环境
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -r requirements.txt[dev]

# 安装 pre-commit hooks
pre-commit install
```

### 运行测试
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_core/

# 生成覆盖率报告
pytest --cov=app tests/
```

## 📋 代码规范

### Python 代码风格
- 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- 使用 [Black](https://black.readthedocs.io/) 进行代码格式化
- 使用 [isort](https://isort.readthedocs.io/) 进行导入排序
- 使用 [flake8](https://flake8.pycqa.org/) 进行代码检查

### 类型注解
- 为所有公共函数和方法添加类型注解
- 使用 `typing` 模块中的类型
- 复杂类型使用 `typing.TypeAlias`

### 文档字符串
- 为所有公共模块、类和方法添加文档字符串
- 使用 Google 风格的文档字符串
- 包含参数说明、返回值说明和异常说明

```python
def example_function(param1: str, param2: int) -> bool:
    """示例函数的简短描述。

    详细描述函数的功能和工作原理。

    Args:
        param1: 参数1的描述
        param2: 参数2的描述

    Returns:
        返回值的描述

    Raises:
        ValueError: 当参数无效时抛出
    """
    return True
```

## 🔌 插件开发

CineFlow AI v3.0 支持插件开发。如果您想为项目贡献插件：

1. 阅读 [插件开发指南](app/plugins/README.md)
2. 查看 [示例插件](examples/plugins/)
3. 遵循插件接口规范
4. 提供完整的文档和测试

## 📝 提交规范

### Commit 消息格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

#### 类型 (type)
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式化（不影响代码运行的变动）
- `refactor`: 代码重构（既不是新增功能，也不是修改bug的代码变动）
- `test`: 增加测试
- `chore`: 构建过程或辅助工具的变动

#### 范围 (scope)
- 模块或组件名称，如 `core`, `ui`, `plugins`
- 可选，用于说明影响的范围

#### 示例
```
feat(ui): 添加新的快捷键管理器

- 实现全局快捷键绑定
- 添加冲突检测机制
- 支持自定义快捷键

Closes #123
```

## 🧪 测试指南

### 测试结构
```
tests/
├── conftest.py           # pytest 配置和 fixtures
├── test_core/           # 核心模块测试
├── test_ui/              # UI 组件测试
├── test_services/        # 服务层测试
├── test_plugins/         # 插件测试
└── test_integration/     # 集成测试
```

### 编写测试
- 为新功能编写单元测试
- 使用 pytest 的 fixtures 进行测试数据管理
- Mock 外部依赖和系统调用
- 确保测试覆盖边界情况和错误处理

### 测试覆盖率
- 目标覆盖率：单元测试 85%+，集成测试 70%+
- 使用 `pytest --cov` 检查覆盖率
- 关键路径要求 100% 覆盖

## 📦 构建和发布

### 版本号规范
遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规范：
- `MAJOR.MINOR.PATCH`
- 主版本号：不兼容的 API 修改
- 次版本号：向下兼容的功能性新增
- 修订号：向下兼容的问题修正

### 发布流程
1. 更新版本号
2. 更新 CHANGELOG.md
3. 运行完整测试套件
4. 创建 Git 标签
5. 构建发布包
6. 发布到 PyPI（如适用）

## 🐛 问题报告模板

### Bug 报告
```markdown
**Bug 描述**
简要描述遇到的问题

**重现步骤**
1. 打开应用
2. 执行操作 A
3. 执行操作 B
4. 观察到问题

**预期行为**
描述您期望发生的正确行为

**实际行为**
描述实际发生的错误行为

**环境信息**
- 操作系统：
- Python 版本：
- CineFlow AI 版本：
- 相关硬件信息：

**附加信息**
- 错误日志
- 截图
- 其他相关信息
```

### 功能请求
```markdown
**功能描述**
详细描述您希望添加的功能

**问题背景**
描述当前的问题或限制

**解决方案**
描述您建议的解决方案

**替代方案**
描述您考虑过的其他解决方案

**附加信息**
- 参考链接
- 相关截图或示例
```

## 🏆 贡献者认可

### 贡献者列表
我们使用 [All Contributors](https://allcontributors.org/) 规范来认可所有贡献者。贡献类型包括：
- 💻 代码
- 📖 文档
- 🐛 Bug 报告
- 💡 想法
- 🤔 问答
- 🎨 设计
- 📢 推广

### 认可方式
1. 贡献者将自动添加到 README.md 中的贡献者列表
2. 在 CHANGELOG.md 中记录重要贡献
3. 在发布说明中特别感谢主要贡献者

## 📞 联系方式

- 项目维护者：[Agions](https://github.com/agions)
- 邮箱：support@cineaistudio.com
- 讨论区：[GitHub Discussions](https://github.com/agions/CineFlow AI/discussions)

## 📄 行为准则

### 我们的承诺
为了营造一个开放和友好的环境，我们承诺：

- 尊重所有参与者，无论其经验水平、性别、性取向、残疾、个人外貌、体型、种族、民族、年龄、宗教或国籍
- 专注于对社区最有利的事情
- 对其他社区成员表现出同理心

### 期望行为
- 使用友好和包容的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表现出同理心

### 不当行为
- 使用性化的语言或图像
- 人身攻击或政治攻击
- 公开或私下骚扰
- 未经明确许可发布他人的私人信息
- 其他在专业环境中可能被认为不当的行为

## 🎉 致谢

感谢所有为 CineFlow AI 项目做出贡献的开发者、用户和支持者！

---

**让我们一起打造更好的视频编辑体验！** 🎬