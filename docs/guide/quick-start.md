---
title: 快速开始
description: 5 分钟完成 Voxplore 安装与首次第一人称视频解说生成。
---

# 快速开始

> ⏱️ 预计时间：5 分钟（已安装应用者 2 分钟）

---

## 系统要求

| 项目 | 最低要求 | 推荐 |
|------|----------|------|
| 操作系统 | Windows 10+ / macOS 11+ / Ubuntu 20.04+ | Windows 11 / macOS 13+ |
| 内存 | 8 GB | 16 GB |
| 显卡 | — | NVIDIA 4GB+（CUDA 加速）|
| 存储 | 2 GB | 10 GB（包含模型缓存）|
| 网络 | 用于调用 AI API | — |

---

## 下载与安装

### 方式一：安装包（推荐）

1. 打开 [GitHub Releases](https://github.com/Agions/Voxplore/releases/latest)
2. 下载对应平台版本：

| 平台 | 文件名 |
|------|--------|
| Windows | `Voxplore-Setup-x.x.x.exe` |
| macOS | `Voxplore-x.x.x.dmg` |
| Linux | `Voxplore-x.x.x.AppImage` |

3. 运行安装包，按提示完成

### 方式二：Homebrew（macOS / Linux）

```bash
brew install agions/tap/voxplore
```

### 方式三：源码安装

```bash
git clone https://github.com/Agions/Voxplore.git
cd Voxplore
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app/main.py
```

> ⚠️ 源码安装需要自行安装 [FFmpeg](https://ffmpeg.org/download.html)。

---

## 配置 API Key {#配置-api-key}

Voxplore 需要一个 AI API Key 来生成解说词。**DeepSeek-V4** 性价比最高，每月约 ¥7 可处理数十个视频（<¥0.01 / 视频）。

### 获取 DeepSeek API Key

1. 打开 [platform.deepseek.com](https://platform.deepseek.com)
2. 注册并登录
3. 进入 **API Keys** → **Create API Key**
4. 复制生成的 Key（格式：`sk-...`）

### 填入应用

启动 Voxplore → **设置** → **AI 配置** → 粘贴 Key → **保存**

或直接编辑项目根目录的 `.env` 文件：

```env
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
```

### 验证连接

进入 **设置 → AI 配置**，点击 **连接测试**。出现 ✅ 即表示配置成功。

---

## 创建第一个解说视频（4 步）

### 第 1 步：新建项目

启动应用 → 在项目列表点击 **新建项目** → 输入项目名称

### 第 2 步：上传视频

- 点击 **选择文件** 或拖拽视频到窗口
- 支持文件夹批量选择 / Ctrl 多选
- 支持格式：`MP4` / `MOV` / `AVI` / `MKV` / `WebM`

### 第 3 步：选择风格，开始创作

1. 确认视频已加载
2. 选择**情感风格**：治愈 / 悬疑 / 励志 / 怀旧 / 浪漫 / 幽默 / 纪录片（共 7 种）
3. 选择**配音音色**：默认 XiaoXiao（女声）
4. 点击 **开始创作**

等待 AI 完成处理（通常 1–5 分钟），自动完成：场景理解 → 智能分组 → 叙事选段 → 解说生成 → 配音合成。

### 第 4 步：预览并导出

预览解说效果，满意后点击 **导出**，选择格式（MP4 / 剪映草稿 JSON）。

---

## 常见问题

### 提示 "FFmpeg not found"

FFmpeg 是视频处理的核心依赖，未安装会导致所有视频操作失败。

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg

# Windows
# 下载 https://www.gyan.dev/ffmpeg/builds/ ，解压后将 bin 目录加入 PATH
```

安装后重启应用。

### AI 功能报错 401 / 403

API Key 无效或额度用尽。进入 [platform.deepseek.com](https://platform.deepseek.com) 检查 Key 状态和账户余额。

### 处理速度很慢

- 确认网络连接稳定（调用外部 API）
- 有 NVIDIA 显卡时自动启用 CUDA 加速
- 减少抽帧密度可提速（设置 → 场景理解 → 抽帧间隔）

### 显存不足（OOM）

GPU 模式对显存要求较高。进入 **设置 → AI 配置**，关闭 **启用 GPU 加速**，回退到 CPU 模式。

### 无 DISPLAY 环境运行静默退出

Linux 无头环境（SSH / 服务器）下，应用会自动设置 `QT_QPA_PLATFORM=offscreen`，无需额外配置。

---

## 下一步

- [功能详细介绍](../features) — 情感风格、字幕样式、导出格式详解
- [完整安装指南](../guide/installation) — 各平台依赖、CUDA 配置、F5-TTS 安装
- [常见问题](../faq) — 更多问题解答
