# 🎬 CineFlow v3.0 - 多Agent智能视频剪辑

> 6个专业Agent协同，一键生成剪映草稿 | 支持 Windows & macOS | 全中文AI

[![Windows](https://img.shields.io/badge/Windows-0078D6?style=flat-square&logo=windows&logoColor=white)](./INSTALL.md#windows)
[![macOS](https://img.shields.io/badge/macOS-000000?style=flat-square&logo=apple&logoColor=white)](./INSTALL.md#macos)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white)](./requirements.txt)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](./LICENSE)
[![Version](https://img.shields.io/badge/Version-3.0.0--beta3-blue?style=flat-square)](./CHANGELOG.md)

## ✨ 核心特性

### 🤖 多Agent专业协同

| Agent | 职责 | 模型 | 能力 |
|-------|------|------|------|
| 🎬 **Director** | 导演 | DeepSeek-V3 | 项目规划、任务分配、质量把控 |
| ✂️ **Editor** | 剪辑 | Kimi K2.5 | 粗剪精剪、转场节奏、结构优化 |
| 🎨 **Colorist** | 调色 | Kimi K2.5 | 色彩分析、风格化、LUT匹配 |
| 🎵 **Sound** | 音效 | Qwen 2.5 | 音频分析、配乐混音、AI配音 |
| ✨ **VFX** | 特效 | Kimi K2.5 | 画面理解、特效生成、合成 |
| 🔍 **Reviewer** | 审核 | DeepSeek-Coder | 质量检查、问题反馈、优化建议 |

### 💻 跨平台原生支持

- **Windows** - `.exe` 安装程序，原生体验
- **macOS** - `.app` / `.dmg` 安装包，M1/M2/Intel 全支持
- **内置FFmpeg** - 无需额外安装，开箱即用

### 🎬 三大创作模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| 🎙️ **AI解说** | 画面分析 → 解说文案 → AI配音 → 动态字幕 | 影视解说、知识分享 |
| 🎵 **AI混剪** | 多素材智能剪辑 → 节拍匹配 → 自动转场 | 音乐MV、短视频 |
| 🎭 **AI独白** | 画面情感分析 → 情感独白 → 电影字幕 | Vlog、情感短片 |

### 🔗 剪映无缝对接

- 一键导出剪映草稿
- 完美保留剪辑信息
- 支持剪映电脑版/专业版

## 🚀 快速开始

### 方式一：直接运行（开发者）

```bash
# 1. 克隆仓库
git clone https://github.com/Agions/CineFlow.git
cd CineFlow

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置API密钥
export DEEPSEEK_API_KEY="your_key"
export MOONSHOT_API_KEY="your_key"
export DASHSCOPE_API_KEY="your_key"

# 4. 启动
python launch.py
```

### 方式二：安装包（用户）

下载对应平台的安装包：
- [Windows 安装包](https://github.com/Agions/CineFlow/releases)
- [macOS 安装包](https://github.com/Agions/CineFlow/releases)

## 📋 系统要求

| 平台 | 要求 |
|------|------|
| Windows | Windows 10/11, 64位 |
| macOS | macOS 10.15+, Intel/Apple Silicon |
| Python | 3.9+ (源码运行) |
| 内存 | 8GB+ 推荐 |
| 存储 | 2GB+ 可用空间 |

## 🔧 配置说明

### API密钥配置

创建 `.env` 文件：

```bash
# DeepSeek (导演、审核)
DEEPSEEK_API_KEY=your_deepseek_key

# Moonshot/Kimi (剪辑、调色、特效)
MOONSHOT_API_KEY=your_moonshot_key

# 阿里通义千问 (音效)
DASHSCOPE_API_KEY=your_dashscope_key

# 百度文心 (可选)
BAIDU_API_KEY=your_baidu_key
BAIDU_SECRET_KEY=your_baidu_secret
```

### 获取API密钥

- [DeepSeek](https://platform.deepseek.com/)
- [Moonshot](https://platform.moonshot.cn/)
- [阿里云](https://dashscope.aliyun.com/)

## 🏗️ 项目架构

```
CineFlow/
├── app/
│   ├── agents/          # 6个专业Agent
│   │   ├── director_agent.py
│   │   ├── editor_agent.py
│   │   ├── colorist_agent.py
│   │   ├── sound_agent.py
│   │   ├── vfx_agent.py
│   │   ├── reviewer_agent.py
│   │   ├── agent_manager.py
│   │   └── llm_client.py    # 多模型统一接口
│   ├── core/            # 核心服务
│   │   ├── video_processor.py   # FFmpeg视频处理
│   │   ├── audio_engine.py      # 音频处理/TTS
│   │   ├── draft_exporter.py    # 剪映草稿导出
│   │   └── project_manager.py   # 项目管理
│   ├── ui/              # PyQt6界面
│   │   ├── main_window.py
│   │   └── styles.py
│   └── main.py
├── build/               # 打包脚本
│   ├── windows/
│   └── macos/
├── docs/                # 文档
├── tests/               # 测试
└── requirements.txt
```

## 📖 文档

- [安装指南](./INSTALL.md)
- [项目规划](./PROJECT_PLAN_v3.md)
- [开发路线](./ROADMAP.md)
- [更新日志](./CHANGELOG.md)
- [API文档](./docs/API.md)

## 🤝 参与贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

[MIT License](./LICENSE) © 2025 Agions

## 🙏 致谢

- [DeepSeek](https://deepseek.com/) - 深度求索
- [Moonshot](https://moonshot.cn/) - 月之暗面
- [阿里云](https://dashscope.aliyun.com/) - 通义千问
- [FFmpeg](https://ffmpeg.org/) - 视频处理
- [PyQt6](https://riverbankcomputing.com/software/pyqt/) - GUI框架

---

<p align="center">
  Made with ❤️ by Agions
</p>
