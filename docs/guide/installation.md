---
title: 安装指南
description: Narrafiilm 各平台完整安装步骤、依赖配置与故障排查。
---

# 安装指南

---

## Windows

### 方式一：安装包（推荐）

1. 下载 `Narrafiilm-Setup-x.x.x.exe`（[Releases 页面](https://github.com/Agions/Narrafiilm/releases/latest)）
2. 运行安装程序，一路 Next 即可
3. 首次启动会自动检测并提示安装 FFmpeg（如缺失）

### 方式二：便携版

下载 `.zip` 便携版，解压后直接运行 `Narrafiilm.exe`，无需安装。

### 方式三：源码运行

```powershell
# 安装 Python 3.10+
# 建议使用 pyenv-win 或 python.org 安装程序

git clone https://github.com/Agions/Narrafiilm.git
cd Narrafiilm
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app/main.py
```

### FFmpeg 安装（Windows）

**自动安装（推荐）**：首次启动时应用会自动提示下载 FFmpeg。

**手动安装**：
1. 下载 [FFmpeg Builds](https://www.gyan.dev/ffmpeg/builds/)（选择 `ffmpeg-release-essentials.zip`）
2. 解压到任意目录（如 `C:\ffmpeg`）
3. 将 `C:\ffmpeg\bin` 加入系统 PATH
4. 重启命令提示符，运行 `ffmpeg -version` 验证

### GPU 加速（CUDA）

如需 NVIDIA 显卡加速（视频分析提速约 3–5 倍）：

1. 安装 [NVIDIA Driver](https://www.nvidia.com/Download/index.aspx)（最新版本）
2. 安装 [CUDA Toolkit 12.x](https://developer.nvidia.com/cuda-downloads)
3. 安装 [cuDNN 9.x](https://developer.nvidia.com/cudnn-download)（需注册 NVIDIA 开发者账号）

```powershell
# 验证 CUDA 可用
python -c "import torch; print(torch.cuda.is_available())"
```

---

## macOS

### 方式一：DMG 安装包（推荐）

1. 下载 `Narrafiilm-x.x.x.dmg`
2. 打开并将应用拖入 Applications 文件夹
3. 首次启动：右键 → 打开（绕过 Gatekeeper）

### 方式二：Homebrew

```bash
brew install agions/tap/narrafiilm
brew install ffmpeg  # 如未安装
```

### 方式三：源码运行

```bash
git clone https://github.com/Agions/Narrafiilm.git
cd Narrafiilm
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app/main.py
```

### 依赖安装

```bash
brew install ffmpeg
brew install python@3.10  # 如需指定版本
```

### Apple Silicon (M1/M2/M3) 注意事项

- 应用为 universal binary，原生支持 Apple Silicon
- 推荐使用 PyTorch MPS 加速：安装 `torch>=2.0` 后自动启用
- 如遇 PySide6 兼容问题，使用 Homebrew 安装：`brew install pyside6`

---

## Linux

### 方式一：AppImage（推荐）

```bash
# 下载 Narrafiilm-x.x.x.AppImage
chmod +x Narrafiilm-x.x.x.AppImage
./Narrafiilm-x.x.x.AppImage
```

### 方式二：DEB / RPM 包

| 发行版 | 下载格式 | 安装命令 |
|--------|----------|----------|
| Debian / Ubuntu | `.deb` | `sudo dpkg -i narrafiilm_x.x.x_amd64.deb` |
| Fedora / RHEL | `.rpm` | `sudo rpm -i narrafiilm-x.x.x.rpm` |

### 方式三：源码运行

```bash
# 安装系统依赖
sudo apt install ffmpeg python3-venv python3-pip libegl1 libgl1 libxkbcommon0 libdbus-1-3

git clone https://github.com/Agions/Narrafiilm.git
cd Narrafiilm
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app/main.py
```

### 无头环境（服务器 / Docker）

服务器环境无需图形界面，可运行完整 AI 处理流程：

```bash
# 自动检测并使用 offscreen 模式
python3 app/main.py

# 或手动指定
export QT_QPA_PLATFORM=offscreen
python3 app/main.py
```

> 注意：无头模式下无法使用 GUI 编辑预览，但可以调用 Python API 进行批量处理。

### 依赖库说明

| 库 | 用途 | 安装 |
|-----|------|------|
| `libegl1` | Qt offscreen 平台 | `apt install libegl1` |
| `libgl1` | OpenGL 支持 | `apt install libgl1` |
| `libxkbcommon0` | 键盘事件处理 | `apt install libxkbcommon0` |
| `libdbus-1-3` | 进程间通信 | `apt install libdbus-1-3` |

### GPU 加速（CUDA）

```bash
# 安装 NVIDIA Driver
sudo apt install nvidia-driver-535  # 根据显卡型号选择

# 安装 CUDA Toolkit
wget https://developer.download.nvidia.com/compute/cuda/repos/debian12/x86_64/cuda-keyring_1.0-1_all.deb
sudo dpkg -i cuda-keyring_1.0-1_all.deb
sudo apt update
sudo apt install cuda-toolkit-12-3

# 验证
python3 -c "import torch; print(torch.cuda.is_available())"
```

---

## F5-TTS 音色克隆（可选）

F5-TTS 支持用 15–30 秒参考音频克隆任意音色，效果自然。

### 安装

```bash
pip install F5-TTS
```

### 使用方法

在应用设置 → 配音配置 → TTS 引擎，选择 **F5-TTS**。

首次使用会提示下载模型（约 500MB），需等待下载完成。

### 克隆流程

1. 准备参考音频（15–30 秒，干净人声，无背景音乐）
2. 在配音配置中选择 **F5-TTS** → **克隆新音色**
3. 上传参考音频，给音色命名
4. 生成后选择该音色即可使用

---

## Python API（高级用法）

Narrafiilm 提供 Python API，可集成到自动化流程：

```python
from app.services.ai.first_person_narrator import FirstPersonNarrator
from app.services.ai.llm_manager import load_llm_config

# 初始化
narrator = FirstPersonNarrator(
    llm_config=load_llm_config(),
    voice_config={"engine": "edge-tts", "voice": "zh-CN-Xiaoxiao"}
)

# 生成解说
result = narrator.narrate(
    video_path="/path/to/video.mp4",
    style="healing",  # 治愈/悬疑/励志/怀旧/浪漫
    output_dir="./output",
)

print(f"解说稿: {result['script']}")
print(f"音频: {result['audio_path']}")
print(f"字幕: {result['subtitle_path']}")
print(f"视频: {result['video_path']}")
```

---

## 故障排查

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 启动无反应（Windows） | 缺失 VC++ 运行库 | 安装 [VC++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe) |
| 启动无反应（Linux） | 缺失 libEGL | `sudo apt install libegl1 libgl1` |
| 视频加载失败 | FFmpeg 未安装或未加入 PATH | 安装 FFmpeg 并重启应用 |
| API 401 | API Key 错误或失效 | 检查 Key 是否正确、账户是否有余额 |
| GPU 加速无效 | CUDA 版本不匹配 | 确认 CUDA >= 12.0，cuDNN 已正确安装 |
| 显存 OOM | 视频太长或显卡显存不足 | 减少抽帧密度，或关闭 GPU 加速使用 CPU |
| 配音无法合成 | 网络问题无法访问 Edge TTS | 检查网络，或切换到本地 F5-TTS |
| 剪映导出失败 | 剪映版本过旧 | 更新剪映至最新版本 |
