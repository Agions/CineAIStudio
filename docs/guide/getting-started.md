# 快速开始

VideoForge 是一款 AI 驱动的智能视频剪辑工具，5 分钟即可上手。

## 环境要求

| 要求 | 最低配置 | 推荐配置 |
|------|----------|----------|
| 操作系统 | Windows 10 / macOS 11 / Ubuntu 20.04 | Windows 11 / macOS 13 / Ubuntu 22.04 |
| CPU | Intel i5 / Apple M1 | Intel i7 / Apple M2 |
| 内存 | 8 GB | 16 GB |
| 显卡 | NVIDIA 4GB / 集成显卡 | NVIDIA 8GB |
| 磁盘 | 10 GB 可用空间 | 20 GB SSD |

## 安装步骤

### 方式一：下载安装包

1. 访问 [GitHub Releases](https://github.com/Agions/VideoForge/releases)
2. 下载对应平台的最新版本
3. 运行安装程序

### 方式二：从源码构建

```bash
# 克隆项目
git clone https://github.com/Agions/VideoForge.git
cd VideoForge

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 复制环境配置
cp .env.example .env

# 运行应用
python app/main.py
```

## 首次配置

### 1. 配置 AI 模型

启动应用后，在 **设置 → AI 配置** 中配置您的 API Key：

```yaml
# 推荐配置（免费）
AI_PROVIDER=ollama
OLLAMA_MODEL=llama3

# 推荐配置（付费，能力更强）
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-5.4
```

### 2. 配置 FFmpeg（可选）

VideoForge 需要 FFmpeg 进行视频处理：

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows
# 从 https://ffmpeg.org/download.html 下载
```

## 快速教程

### 1. 创建新项目

1. 点击 **新建项目**
2. 选择项目保存位置
3. 输入项目名称

### 2. 导入视频素材

1. 点击 **导入素材** 或直接拖拽文件
2. 支持格式：MP4, MOV, AVI, MKV, WebM

### 3. 选择 AI 模式

| 模式 | 适用场景 |
|------|----------|
| 🎬 **剧情分析** | 电影解说、Vlog 整理 |
| 🎙️ **AI 解说** | 纪录片、产品介绍 |
| 🎵 **智能混剪** | 音乐视频、节奏剪辑 |
| 🎭 **AI 独白** | 情感视频、电影感 Vlog |
| 📱 **短视频切片** | 直播切片、社交媒体 |
| 🌐 **视频翻译** | 内容出海、本地化 |

### 4. 调整参数

根据需要调整：
- 剪辑风格
- 输出格式
- 画质设置

### 5. 导出成片

1. 点击 **导出**
2. 选择格式和保存位置
3. 等待处理完成

## 常见问题

### 启动报错

**Q: 提示 "Module not found"**

```bash
pip install -r requirements.txt
```

**Q: 提示 "FFmpeg not found"**

安装 FFmpeg 或在设置中配置路径。

### AI 功能不工作

1. 检查 API Key 是否配置正确
2. 确认网络连接正常
3. 查看日志获取详细错误

## 下一步

- [功能详细介绍](/features) - 了解更多功能
- [AI 模型配置](/ai-models) - 配置不同的 AI 模型
- [常见问题](/faq) - 常见问题解答
