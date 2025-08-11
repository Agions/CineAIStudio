# VideoEpicCreator - AI短剧视频编辑器

一款基于Python和PyQt6开发的AI驱动短剧视频编辑应用，专为短剧创作者设计。利用多种AI大模型实现智能解说生成、高能混剪、第一人称独白等功能，并与剪映深度集成。

## 🌟 核心特性

### AI驱动的三大编辑模式
1. **AI短剧解说 (Commentary)**: 自动生成适合短剧的解说内容，智能插入原始片段
2. **AI高能混剪 (Compilation)**: 创建激动人心的混剪视频，配备AI生成的旁白叠加
3. **AI第一人称独白 (Monologue)**: 生成第一人称叙述内容，自动插入相关原始片段

### 智能视频分析
- **智能场景检测**: 自动捕获和识别高能/精彩场景
- **自动场景匹配**: AI驱动的场景与生成内容匹配
- **内容理解**: 深度分析视频内容、情感和节奏

### 多AI模型支持
- **OpenAI**: GPT-3.5, GPT-4 支持
- **通义千问**: 阿里云大模型集成
- **文心一言**: 百度AI模型支持
- **Ollama**: 本地大模型支持
- **自定义API**: 支持兼容OpenAI格式的自定义API

### 语音合成集成
- 本地TTS引擎支持
- 第三方语音合成服务
- 多种声音选择和参数调节

### 剪映深度集成
- 自动检测剪映安装路径
- 一键导出为剪映草稿文件
- 完整的项目文件和资源导出

## 🚀 快速开始

### 环境要求
- Python 3.9+
- FFmpeg (用于视频处理)
- 支持的操作系统: Windows 10/11, macOS 10.15+, Linux

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/agions/VideoEpicCreator.git
cd VideoEpicCreator
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **运行应用**
```bash
python main.py
```

### 首次配置

1. **配置AI模型**
   - 打开设置面板 → AI模型选项卡
   - 选择要使用的AI模型提供商
   - 输入相应的API密钥
   - 点击"测试"按钮验证连接

2. **设置路径**
   - 配置项目默认保存位置
   - 设置剪映草稿文件夹路径（可自动检测）
   - 配置导出文件夹

3. **创建首个项目**
   - 点击"新建项目"
   - 选择编辑模式（解说/混剪/独白）
   - 上传视频文件
   - 开始AI驱动的视频编辑

## 🎯 使用流程

### 1. 项目管理
- **左侧面板**: 项目管理和应用设置
- **右侧面板**: 项目列表和新建项目界面
- **项目CRUD**: 完整的创建、读取、更新、删除操作

### 2. 视频编辑
- **视频上传**: 支持拖拽上传，多格式支持
- **编辑模式选择**: 根据需求选择解说、混剪或独白模式
- **AI内容生成**: 一键生成高质量的AI内容
- **实时预览**: 即时查看编辑效果

### 3. 导出与集成
- **多格式导出**: 支持MP4、AVI等主流格式
- **剪映集成**: 无缝导出到剪映进行进一步编辑
- **项目保存**: 完整的项目状态保存和恢复

## 🔧 技术架构

### 模块化设计
- **AI模块**: 统一的AI模型接口，支持多种提供商
- **核心模块**: 视频处理、项目管理、场景分析
- **UI模块**: 现代化的PyQt6界面，响应式设计
- **配置模块**: 安全的配置管理和API密钥存储

### 安全特性
- **API密钥加密**: 使用AES加密存储敏感信息
- **掩码显示**: 界面中安全显示API密钥
- **权限控制**: 基于配置状态的功能启用/禁用

### 扩展性
- **插件架构**: 易于添加新的AI模型提供商
- **模块化组件**: 可复用的UI和功能组件
- **配置驱动**: 灵活的配置系统支持定制化

## 📁 项目结构

```
VideoEpicCreator/
├── app/                          # 应用核心代码
│   ├── ai/                       # AI相关模块
│   │   ├── models/               # AI模型集成
│   │   ├── generators/           # AI内容生成器
│   │   └── analyzers/            # AI分析模块
│   ├── core/                     # 核心功能
│   │   ├── video_manager.py      # 视频管理
│   │   ├── project_manager.py    # 项目管理
│   │   └── scene_detector.py     # 场景检测
│   ├── ui/                       # 用户界面
│   │   ├── new_main_window.py    # 主窗口
│   │   ├── project_panel.py      # 项目管理面板
│   │   ├── settings_panel.py     # 设置面板
│   │   └── components/           # UI组件
│   ├── config/                   # 配置管理
│   │   ├── settings_manager.py   # 设置管理器
│   │   └── api_key_manager.py    # API密钥管理
│   └── utils/                    # 工具函数
├── resources/                    # 资源文件
├── docs/                         # 文档
├── tests/                        # 测试代码
├── main.py                       # 应用入口
└── requirements.txt              # 依赖列表
```

## 🔑 API密钥配置

### 支持的AI模型提供商

| 提供商 | 模型 | 获取方式 |
|--------|------|----------|
| OpenAI | GPT-3.5, GPT-4 | [platform.openai.com](https://platform.openai.com/) |
| 通义千问 | qwen-turbo, qwen-plus | [dashscope.aliyun.com](https://dashscope.aliyun.com/) |
| 文心一言 | ernie-bot, ernie-bot-turbo | [cloud.baidu.com](https://cloud.baidu.com/product/wenxinworkshop) |
| Ollama | llama2, mistral, 等 | [ollama.ai](https://ollama.ai/) |

### 配置步骤
1. 注册相应的AI服务账号
2. 获取API密钥
3. 在应用设置中配置密钥
4. 测试连接确保正常工作

## 🎨 界面特性

### 现代化设计
- **深色主题**: 护眼的深色界面设计
- **响应式布局**: 自适应不同屏幕尺寸
- **直观操作**: 简洁明了的用户交互

### 工作流优化
- **拖拽支持**: 直接拖拽视频文件到应用
- **快捷键**: 常用操作的键盘快捷键
- **状态保存**: 自动保存工作状态

## 🚧 开发状态

### 已完成功能
- ✅ 项目结构重组
- ✅ 配置管理系统
- ✅ 新UI布局设计
- ✅ 项目管理功能
- ✅ 设置面板
- ✅ API密钥管理

### 开发中功能
- 🔄 AI模型集成
- 🔄 场景检测算法
- 🔄 内容生成系统
- 🔄 语音合成集成
- 🔄 剪映导出功能

### 计划功能
- 📋 高级视频分析
- 📋 批量处理
- 📋 云端同步
- 📋 插件系统

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系方式

- 项目主页: [GitHub](https://github.com/agions/VideoEpicCreator)
- 问题反馈: [Issues](https://github.com/agions/VideoEpicCreator/issues)

---

**VideoEpicCreator** - 让AI为你的短剧创作赋能 🎬✨
