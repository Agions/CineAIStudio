# 🎬 ClipFlowCut - AI 视频创作桌面应用

<p align="center">
  <img src="https://img.shields.io/badge/version-3.0.0-blue.svg" alt="Version" />
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License" />
  <img src="https://img.shields.io/badge/Python-3.9+-3776ab?logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/PyQt6-6.0+-41cd52" alt="PyQt6" />
  <img src="https://img.shields.io/badge/FFmpeg-required-007808" alt="FFmpeg" />
  <img src="https://img.shields.io/badge/platform-macOS%20|%20Windows-lightgrey" alt="Platform" />
  <img src="https://img.shields.io/badge/tests-58+-orange" alt="Tests" />
</p>

---

## ✨ 简介

ClipFlowCut 是专业的 **AI 驱动** 视频创作桌面应用，区别于传统手动剪辑软件（如 Premiere、Final Cut），ClipFlowCut 通过 AI 实现自动化创作。

基于 **PyQt6** 构建原生桌面界面，提供从视频理解到成片导出的完整创作能力。

---

## 🎯 核心功能

### 3 大 AI 创作模式

| 模式                   | 说明                           | 工作流                                    |
| ---------------------- | ------------------------------ | ----------------------------------------- |
| 🎙️ **AI 视频解说**     | 原视频 + AI 配音 + 动态字幕    | 场景分析 → 文案生成 → AI 配音 → 字幕合成  |
| 🎵 **AI 视频混剪**     | 多素材 + 节拍匹配 + 自动转场   | 素材分析 → BPM 检测 → 智能剪辑 → 转场合成 |
| 🎭 **AI 第一人称独白** | 画面情感 + 情感独白 + 电影字幕 | 情感分析 → 独白生成 → 配音合成 → 电影字幕 |

### 创作流程

```
素材导入 → AI 分析 → 模式选择 → 脚本生成 → 脚本编辑 → 时间轴编排 → AI 配音 → 预览 → 导出
```

---

## 🤖 AI 能力

### 支持的 LLM (2026年3月最新)

| 提供商        | 模型              | 文本 | 视觉 | 配音 |
| ------------- | ----------------- | :--: | :--: | :--: |
| **OpenAI**    | GPT-5.3           |  ✅  |  ✅  |  ✅  |
| **Anthropic** | Claude Sonnet 4.5 |  ✅  |  ✅  |  ❌  |
| **Google**    | Gemini 3.1 Flash  |  ✅  |  ✅  |  ❌  |
| **阿里云**    | Qwen 3.5          |  ✅  |  ✅  |  ❌  |
| **DeepSeek**  | R1 / V3.2         |  ✅  |  ❌  |  ❌  |
| **智谱AI**    | GLM-5 Plus         |  ✅  |  ✅  |  ❌  |
| **月之暗面**  | Kimi K2.5         |  ✅  |  ✅  |  ❌  |
| **字节豆包**  | Doubao Pro         |  ✅  |  ✅  |  ✅  |
| **腾讯混元**  | Hunyuan Pro       |  ✅  |  ❌  |  ✅  |
| **Edge TTS**  | 微软语音          |  ❌  |  ❌  |  ✅  |

### 核心 AI 能力

| 能力            | 说明                               | 技术                    |
| --------------- | ---------------------------------- | ----------------------- |
| 🎬 **场景理解** | 视频内容分析、场景分割、关键帧提取 | FFmpeg + OpenCV         |
| 📝 **文案生成** | 多风格文案创作（解说/独白/旁白）   | LLM (Qwen/Kimi/GLM/GPT) |
| 🎙️ **语音合成** | AI 配音，多种声音风格              | Edge TTS / OpenAI TTS   |
| 📄 **字幕生成** | 动态字幕，多样式风格               | 自研字幕引擎            |
| 🎵 **音画同步** | BPM 检测，智能对齐                 | librosa 节拍检测        |

---

## 📤 导出格式

### 视频平台预设

| 平台     | 分辨率 | 帧率 | 码率  | 用途         |
| -------- | ------ | ---- | ------ | ------------ |
| B站      | 1080P | 60fps | 8Mbps  | 高清投稿     |
| YouTube | 4K     | 60fps | 25Mbps | 超清发布     |
| Twitter | 1080P | 30fps | 4Mbps  | 压缩优化     |
| TikTok  | 1080P | 30fps | 6Mbps  | 竖屏短视频   |
| 微信     | 1080P | 30fps | 2Mbps  | 微信传输     |

### 导出格式

| 格式             | 文件类型        | 兼容软件            |
| ---------------- | --------------- | ------------------- |
| 📱 **剪映**      | Draft JSON      | 剪映                |
| 🎬 **Premiere**  | XML             | Adobe Premiere Pro  |
| 🍎 **Final Cut** | FCPXML          | Apple Final Cut Pro |
| 🎞️ **DaVinci**   | DaVinci Resolve | DaVinci Resolve     |
| 🎥 **MP4**       | H.264/H.265     | 所有播放器          |
| 📄 **SRT/ASS**   | 字幕文件        | 播放器/编辑软件     |

---

## 🎨 UI 特性

### 专业设计

- **V3.0 现代暗色主题** - 玻璃拟态 + 渐变背景
- **可折叠导航栏** - 节省空间
- **主题切换** - 深色/浅色模式
- **丰富动画** - 流畅过渡效果

### 组件库

- GradientButton - 渐变按钮
- GlassCard - 玻璃卡片
- StatCard - 统计卡片
- ProgressRing - 环形进度条
- LoadingOverlay - 加载遮罩
- SearchBar - 专业搜索栏

---

## 🚀 快速开始

### 环境要求

- Python 3.9+
- FFmpeg（需加入系统 PATH）
- macOS 10.15+ / Windows 10+

### ⚠️ 重要：必须使用 PyQt6

> **注意**：本项目基于 **PyQt6** 开发，**不是 PySide6**！
> 
> 如果你看到类似这样的错误：
> ```
> QLabel(...): argument 1 has unexpected type 'str'
> ```
> 说明你可能安装了错误的 Qt 库。

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/Agions/ClipFlowCut.git
cd ClipFlowCut

# 2. 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# 3. 检查是否已安装 PySide6（如果有请先卸载！）
pip uninstall PySide6  # 如果安装了的话

# 4. 安装依赖（必须使用 PyQt6）
pip install -r requirements.txt

# 5. 配置 API 密钥
cp .env.example .env
# 编辑 .env，填入所需的 API Key

# 6. 运行应用
python main.py
```

---

## 📁 项目结构

```
ClipFlowCut/
├── app/                    # 应用主代码
│   ├── core/              # 核心模块
│   │   ├── project_*.py  # 项目管理
│   │   └── logger.py      # 日志系统
│   ├── services/          # 服务模块
│   │   ├── ai/           # AI 服务
│   │   ├── video/        # 视频处理
│   │   ├── export/       # 导出模块
│   │   └── viral_video/  # 爆款功能
│   ├── ui/               # UI 模块
│   │   ├── main/         # 主窗口
│   │   ├── components/   # 组件库
│   │   └── theme/        # 主题系统
│   └── utils/            # 工具模块
├── tests/                 # 测试文件
├── docs/                  # 文档
├── scripts/               # 构建脚本
└── main.py               # 入口文件
```

---

## 🧪 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_core.py -v

# 运行性能测试
pytest tests/test_benchmark.py -v -s
```

---

## 📚 文档

- [在线文档](https://agions.github.io/ClipFlowCut/)
- [API 文档](./docs/api/)
- [使用指南](./docs/guides/)

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

MIT License

---

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Agions/ClipFlowCut&type=Date)](https://star-history.com/#Agions/ClipFlowCut&type=Date)
