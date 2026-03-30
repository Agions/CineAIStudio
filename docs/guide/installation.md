---
title: 安装配置
description: VideoForge 各平台详细安装指南，包含常见问题的故障排除。
---

# 安装配置

本文档提供 VideoForge 在各平台上的完整安装步骤。

---

## Windows 安装

### 系统要求

| 要求 | 最低配置 | 推荐配置 |
|------|----------|----------|
| 版本 | Windows 10 (64-bit) | Windows 11 |
| 内存 | 8 GB | 16 GB |
| 显卡 | 集成显卡 | NVIDIA 6GB+ |
| 磁盘 | 10 GB 可用空间 | 20 GB SSD |
| 显示器 | 1280×720 | 1920×1080 |

### 安装步骤

1. 下载 `VideoForge-Setup-x.x.x.exe` from [Releases](https://github.com/Agions/VideoForge/releases/latest)
2. 右键安装文件 → **属性** → 勾选 **解除锁定**（如出现）
3. 双击运行安装程序
4. 按照提示完成安装（建议选择"为当前用户安装"避免权限问题）
5. 首次运行如遇 SmartScreen 提示，点击 **仍要运行**

### 卸载

通过 Windows 设置 → 应用 → VideoForge → 卸载，或使用安装包自带的卸载程序。

### 常见问题

#### 提示"无法验证发布者"

这是 Windows 的正常安全警告，点击 **仍要运行** 即可。VideoForge 是开源项目，未购买代码签名证书。

#### 安装后无法启动（黑屏/闪退）

1. 更新显卡驱动
2. 安装 [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
3. 以兼容模式运行：右键 → 属性 → 兼容性 → Windows 10

---

## macOS 安装

### 系统要求

| 要求 | 最低配置 | 推荐配置 |
|------|----------|----------|
| 版本 | macOS 11 (Big Sur) | macOS 13+ |
| 芯片 | Apple Silicon 或 Intel | Apple Silicon (M1/M2/M3) |
| 内存 | 8 GB | 16 GB |
| 磁盘 | 10 GB 可用空间 | 20 GB SSD |

### 安装步骤

#### DMG 安装（推荐）

1. 下载 `VideoForge-x.x.x.dmg` from [Releases](https://github.com/Agions/VideoForge/releases/latest)
2. 打开 DMG 文件
3. 将 VideoForge 拖入 Applications 文件夹
4. 首次运行：打开 Applications → 右键 VideoForge → 选择"打开"
5. 遇到"无法验证开发者"提示时，点击"仍要打开"

#### Homebrew 安装

```bash
brew install videoforge
brew install --cask videoforge  # 如果上面不行
```

### Apple Silicon (M1/M2/M3) 注意事项

- VideoForge 提供 Universal 和 Apple Silicon 两个版本
- **推荐下载 Apple Silicon 版本**（性能更好、功耗更低）
- Rosetta 2 兼容模式下也可以运行 Universal 版本（性能略差）

### 常见问题

#### "VideoForge can't be opened because it is from an unidentified developer"

**解决方法（任选其一）：**

1. 右键点击应用 → **打开** → 弹出确认框 → 点击 **打开**
2. 系统设置 → 隐私与安全性 → 滚动到下方 → 点击 **仍要打开 VideoForge**
3. 终端命令绕过（不推荐长期使用）：
   ```bash
   sudo xattr -rd com.apple.quarantine /Applications/VideoForge.app
   ```

#### 卸载

```bash
# 删除应用
rm -rf /Applications/VideoForge.app

# 删除配置（可选）
rm -rf ~/.videoforge
```

---

## Linux 安装

### 系统要求

| 要求 | 最低配置 | 推荐配置 |
|------|----------|----------|
| 发行版 | Ubuntu 20.04 / Debian 11 | Ubuntu 22.04+ |
| 内存 | 8 GB | 16 GB |
| 显卡 | 集成显卡 | NVIDIA + CUDA |
| 桌面环境 | GNOME / KDE / XFCE | GNOME |

### AppImage 安装（推荐）

```bash
# 1. 下载 AppImage
wget https://github.com/Agions/VideoForge/releases/download/v3.1.0/VideoForge-x.x.x.AppImage

# 2. 添加执行权限
chmod +x VideoForge-x.x.x.AppImage

# 3. 运行
./VideoForge-x.x.x.AppImage
```

#### AppImage 依赖问题

如果提示缺少库，安装基础依赖：

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install fuse libfuse2 libxcb-xinerama0 libxkbcommon-x11-0 libegl1 libdbus-1-3

# Fedora
sudo dnf install fuse libxkbcommon-x11 Mesa-libEGL dbus-x11
```

如果仍有问题，使用 `--no-sandbox` 模式：

```bash
./VideoForge-x.x.x.AppImage --no-sandbox
```

### PPA 安装（Ubuntu/Debian）

```bash
sudo add-apt-repository ppa:videoforge/stable
sudo apt update
sudo apt install videoforge
```

### AUR 安装（Arch Linux）

```bash
# 使用 yay
yay -S videoforge

# 或使用 paru
paru -S videoforge
```

### Snap 安装

```bash
sudo snap install videoforge --classic
```

### 从源码安装

```bash
# 安装系统依赖
sudo apt install python3.10 python3-pip ffmpeg libxcb-xinerama0 libxkbcommon-x11-0

# 克隆并安装
git clone https://github.com/Agions/VideoForge.git
cd VideoForge
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 运行
python app/main.py
```

### 常见问题

#### Linux 字体显示异常

```bash
# Ubuntu/Debian — 安装中文字体
sudo apt install fonts-noto fonts-wqy-microhei fonts-wqy-zenhei

# 刷新字体缓存
fc-cache -fv
```

#### Qt 平台插件错误

```bash
# 缺失 Qt 平台插件
sudo apt install libxcb-xinerama0

# 或者使用 XCB 平台
export QT_QPA_PLATFORM=xbcb
./VideoForge
```

---

## FFmpeg 安装（必须）

FFmpeg 是 VideoForge 的核心依赖，所有视频编解码都依赖它。

### 各平台安装

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows
# 1. 访问 https://ffmpeg.org/download.html
# 2. 下载 ffmpeg-release-essentials.zip
# 3. 解压到 C:\ffmpeg
# 4. 将 C:\ffmpeg\bin 添加到系统 PATH
# 5. 重启终端后验证
```

### 验证安装

```bash
ffmpeg -version
# 应该输出版本信息，包含 "ffmpeg version ..."

ffprobe -version
# 如果也输出版本信息，说明安装成功
```

### FFmpeg 版本过旧

部分 Linux 发行版的包管理器提供的 FFmpeg 版本较旧（< 5.0）。建议使用 [John Van Engen 的 PPA](https://launchpad.net/~jonathonf/+archive/ubuntu/ffmpeg-4) 或从源码编译：

```bash
# Ubuntu 20.04/22.04 添加新版 PPA
sudo add-apt-repository ppa:jonathonf/ffmpeg-4
sudo apt update
sudo apt install ffmpeg
```

---

## Python 环境

### 版本要求

Python 3.10+ 必需。检查版本：

```bash
python --version
# 或
python3 --version
```

### 使用 pyenv（推荐）

```bash
# 安装 pyenv
curl https://pyenv.run | bash

# 添加到 ~/.bashrc 或 ~/.zshrc
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# 安装指定 Python 版本
pyenv install 3.10.12

# 创建虚拟环境
pyenv virtualenv 3.10.12 videoforge
pyenv local videoforge

# 在项目目录自动激活
cd /path/to/VideoForge
# .python-version 已配置，会自动使用 videoforge 环境

# 安装依赖
pip install -r requirements.txt
```

### 使用 venv（简单方式）

```bash
cd VideoForge
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate    # Windows

pip install -r requirements.txt
```

---

## GPU 加速（可选）

### NVIDIA CUDA

GPU 加速可以显著提升视频处理和 AI 推理速度。

```bash
# 检查是否有 NVIDIA 显卡
nvidia-smi

# 检查 CUDA 版本
nvcc --version
```

如果未安装 CUDA：

1. 下载 [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads)
2. 安装后配置环境变量：
   ```bash
   export PATH=/usr/local/cuda/bin:$PATH
   export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
   ```

### CuPy（NVIDIA GPU 加速库）

```bash
# 安装与当前 CUDA 版本匹配的 CuPy
pip install cupy-cuda11x  # CUDA 11.x
# 或
pip install cupy-cuda12x  # CUDA 12.x
```

### Apple Silicon

Apple Silicon Mac 无需额外配置，原生支持 GPU 加速。

---

## 环境变量配置

编辑 `.env` 文件（项目根目录）：

```env
# AI API 配置（至少配置一个）
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
# OPENAI_API_KEY=sk-your-key
# DASHSCOPE_API_KEY=your-key

# 语音合成（免费，使用 Edge TTS）
# 默认使用 Edge TTS，如需 OpenAI TTS：
# TTS_PROVIDER=openai
# OPENAI_TTS_KEY=sk-your-key

# FFmpeg 路径（如果不在 PATH 中）
# FFMPEG_PATH=/usr/local/bin/ffmpeg

# 日志级别
LOG_LEVEL=INFO

# 代理设置（如需要）
# HTTP_PROXY=http://127.0.0.1:7890
# HTTPS_PROXY=http://127.0.0.1:7890
```

---

## 故障排除速查

| 症状 | 解决方案 |
|------|----------|
| 启动报错 Module not found | `pip install -r requirements.txt` |
| FFmpeg not found | 安装 FFmpeg 并确保在 PATH 中 |
| macOS 无法打开 | 解除锁定或右键"仍要打开" |
| Linux 字体显示异常 | 安装中文字体包 |
| Qt platform plugin not found | 安装 `libxcb-xinerama0` |
| 视频无法预览 | 确认是 H.264/MP4 格式 |
| AI 报 401 错误 | 检查 API Key 是否正确 |
| 内存不足 | 关闭其他程序，降低处理分辨率 |
