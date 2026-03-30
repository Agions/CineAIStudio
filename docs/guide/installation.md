# 安装配置

详细的安装指南。

## Windows 安装

### 系统要求

- Windows 10 (64-bit) 或更高版本
- 至少 8GB RAM
- NVIDIA 显卡（可选，用于 GPU 加速）

### 安装步骤

1. 下载 `VideoForge-Setup-x.x.x.exe` from [Releases](https://github.com/Agions/VideoForge/releases)
2. 运行安装程序
3. 按照提示完成安装

### 依赖安装

VideoForge 自动安装以下依赖：
- Visual C++ Redistributable
- FFmpeg

## macOS 安装

### 系统要求

- macOS 11 (Big Sur) 或更高版本
- Apple Silicon (M1/M2/M3) 或 Intel

### 安装步骤

1. 下载 `VideoForge-x.x.x.dmg` from [Releases](https://github.com/Agions/VideoForge/releases)
2. 拖拽到 Applications 文件夹
3. 首次运行需要在系统偏好设置中允许运行

### Homebrew 安装

```bash
brew install --cask videoforge
```

## Linux 安装

### Ubuntu/Debian

```bash
# 添加 PPA
sudo add-apt-repository ppa:videoforge/stable
sudo apt update

# 安装
sudo apt install videoforge
```

### Arch Linux

```bash
# 使用 AUR
yay -S videoforge
```

### 从源码

```bash
# 安装依赖
sudo apt install python3.10 python3-pip ffmpeg

# 克隆并安装
git clone https://github.com/Agions/VideoForge.git
cd VideoForge
pip install -r requirements.txt

# 运行
python app/main.py
```

## FFmpeg 安装

FFmpeg 是 VideoForge 的核心依赖。

### macOS

```bash
brew install ffmpeg
```

### Ubuntu/Debian

```bash
sudo apt install ffmpeg
```

### Windows

1. 下载 [FFmpeg](https://ffmpeg.org/download.html)
2. 解压到 `C:\ffmpeg`
3. 将 `C:\ffmpeg\bin` 添加到 PATH

### 验证安装

```bash
ffmpeg -version
```

## Python 环境

### 使用 pyenv (推荐)

```bash
# 安装 pyenv
curl https://pyenv.run | bash

# 安装 Python 3.10+
pyenv install 3.10.12

# 创建虚拟环境
pyenv virtualenv 3.10.12 videoforge
pyenv local videoforge

# 安装依赖
pip install -r requirements.txt
```

### 使用 venv

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

## GPU 加速 (可选)

### NVIDIA CUDA

```bash
# 安装 CUDA Toolkit
conda install cudatoolkit=11.8

# 安装 CuDF
pip install cupy-cuda11x
```

### Apple Silicon

Apple Silicon Mac 原生支持，无需额外配置。

## 故障排除

### macOS 无法运行

**错误**: "VideoForge can't be opened because it is from an unidentified developer"

**解决**: 
1. 系统偏好设置 → 安全性与隐私 → 通用
2. 点击"仍要打开"

### Linux 字体缺失

```bash
# Ubuntu/Debian
sudo apt install fonts-noto fonts-wqy-microhei
```

### 模块导入错误

```bash
# 重新安装依赖
pip install --upgrade -r requirements.txt
```
