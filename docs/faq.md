---
title: 常见问题
description: Narrafiilm 使用过程中遇到的常见问题与解决方案。
---

# 常见问题

本文档收集了 Narrafiilm 使用过程中最常见的问题，分为几个类别方便快速查找。

---

## 安装问题

### ❓ 安装包无法下载或下载很慢？

**A:** GitHub 在国内的下载速度可能较慢，推荐使用镜像：

```bash
# 使用 ghproxy 镜像
wget https://ghproxy.com/https://github.com/Agions/Narrafiilm/releases/download/v3.1.0/Narrafiilm-Setup-x.x.x.exe

# 或使用 GitHub CLI
gh release download --pattern "Narrafiilm*.exe"
```

### ❓ Windows 安装时报"SmartScreen 已阻止"？

**A:** 这是 Windows 的正常安全提示：

1. 点击 **更多信息**
2. 点击 **仍要运行**
3. 如果问题持续，关闭 Windows SmartScreen：
   设置 → 更新和安全 → Windows 安全 → 应用和浏览器控制 → 关闭 SmartScreen

### ❓ macOS 提示"无法打开，因为无法验证开发者"？

**A:** macOS 对未签名应用的限制，解决方法：

1. 系统设置 → 隐私与安全性 → 滚动到下方
2. 点击 **仍要打开**
3. 如果仍不行：
   ```bash
   # 绕过 Gatekeeper（临时）
   sudo xattr -rd com.apple.quarantine /Applications/Narrafiilm.app
   ```

### ❓ Linux AppImage 无法运行？

**A:** 添加执行权限：

```bash
chmod +x Narrafiilm-x.x.x.AppImage
./Narrafiilm-x.x.x.AppImage
```

如果仍不行，可能是缺少 FUSE：

```bash
# Ubuntu/Debian
sudo apt install fuse libfuse2

# 或尝试不依赖 FUSE 模式
./Narrafiilm-x.x.x.AppImage --no-sandbox
```

---

## 启动问题

### ❓ 启动后黑屏或卡在加载界面？

**A:** 按顺序排查：

1. 更新显卡驱动（尤其是 NVIDIA）
2. 尝试以安全模式启动：
   ```bash
   python app/main.py --safe-mode
   ```
3. 清除缓存：
   ```bash
   python -m videoforge cache clear
   ```
4. 查看日志获取详细信息：
   ```bash
   tail -f ~/.videoforge/logs/app.log
   ```

### ❓ 提示 "Module not found" 或 "Import Error"？

**A:** 依赖未正确安装：

```bash
# 重新安装依赖
pip install --upgrade -r requirements.txt

# 如果是 PyQt6/PySide6 冲突
pip uninstall PySide6 PySide2
pip install PyQt6
```

### ❓ 提示 "Qt platform plugin not found"？

**A:** Qt 平台插件缺失（常见于 Linux 最小化安装）：

```bash
# Ubuntu/Debian
sudo apt install libxcb-xinerama0 libxkbcommon-x11-0 libegl1 libdbus-1-3

# Fedora
sudo dnf install libxkbcommon-x11 Mesa-libEGL dbus-x11
```

---

## AI 功能问题

### ❓ AI 功能报 "401 Unauthorized" 或 "Invalid API Key"？

**A:** 按以下顺序排查：

1. 检查 API Key 是否正确（注意无多余空格）
2. 检查 Key 是否过期或额度用完
3. 确认 API Key 与配置的提供商匹配（DeepSeek Key 不能用于 OpenAI）
4. 在 [对应平台](https://platform.deepseek.com) 检查 Key 状态

### ❓ AI 功能报 "429 Rate Limited"？

**A:** 请求过于频繁：

1. 等待 1 分钟后再试
2. 在设置中降低 AI 请求并发数
3. 如果是免费账户，考虑升级到付费计划
4. DeepSeek 的免费额度较充足，推荐作为主力

### ❓ 报 "500 Server Error" 或 "Service Unavailable"？

**A:** AI 服务商临时故障：

1. 检查 [服务商状态页](https://status.deepseek.com)
2. 切换到备用 AI 提供商（如从 DeepSeek 切换到 OpenAI）
3. 稍后再试

### ❓ 生成速度很慢？

**A:** 速度受多种因素影响：

| 影响因素 | 解决方案 |
|----------|----------|
| 网络延迟 | 使用国内 AI 提供商（DeepSeek/通义千问） |
| 模型选择 | 简单任务用小模型（如 GPT-4o-mini） |
| 显卡 | NVIDIA GPU 可加速本地推理（Ollama） |
| 并发 | 降低批量处理的并发数 |
| 服务器负载 | 避开高峰时段（国内晚间） |

---

## 视频处理问题

### ❓ 提示 "FFmpeg not found"？

**A:** FFmpeg 未安装或未添加到 PATH：

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows: 下载 https://ffmpeg.org/download.html 并添加到 PATH
```

验证安装：

```bash
ffmpeg -version
```

### ❓ 视频导入后无法预览？

**A:** 常见原因：

1. 视频格式不兼容 → 转为 MP4（H.264）
2. 视频损坏 → 用其他播放器测试源文件
3. 视频过大 → 降低预览分辨率（设置 → 性能 → 预览质量）
4. 缺少解码器 → 安装完整版 FFmpeg（不是 FFmpeg static）

### ❓ 处理过程中崩溃或卡死？

**A:** 内存不足或视频过大：

1. 关闭其他程序释放内存
2. 在设置中降低处理分辨率
3. 将长视频分段处理
4. 检查磁盘空间（至少 2 倍视频大小的空闲空间）

### ❓ 导出后视频有音画不同步？

**A:** 常见原因：

1. 源视频本身有问题（用其他软件验证）
2. 音频有可变码率问题（设置 → 导出 → 重新编码音频）
3. 使用了不兼容的编解码器（推荐使用 H.264）

---

## 订阅与付费问题

### ❓ Narrafiilm 本身收费吗？

**A:** **完全免费**，包括所有 AI 创作功能。Narrafiilm 是开源项目，仅收取运营成本（服务器/带宽），但不做强制收费。

### ❓ 为什么有些 AI 模型需要付费？

**A:** Narrafiilm 调用的是第三方 AI 服务商（OpenAI、DeepSeek 等），他们有自己的定价。你只需支付你使用的 AI 服务费用，Narrafiilm 不从中抽成。

### ❓ 如何控制 AI 费用？

**A:** 推荐配置：

| 方案 | AI 费用 | 说明 |
|------|---------|------|
| 完全免费 | ¥0 | DeepSeek V3.2 + Edge TTS |
| 低成本 | ¥20/月 | DeepSeek + OpenAI TTS |
| 高质量 | ¥100/月 | GPT-5.4 + OpenAI TTS |

---

## 数据与隐私问题

### ❓ 视频文件会上传到服务器吗？

**A:** **不会**。Narrafiilm 是一款本地桌面应用，所有处理都在你的电脑上完成。AI 功能通过调用第三方 API 实现（视频片段会上传到 OpenAI/DeepSeek 等），但不会存储在你的服务器上。

### ❓ API Key 安全吗？

**A:** 安全。Narrafiilm 使用 OS Keychain（系统级安全存储）或 Fernet 加密存储密钥，从不将 Key 以明文形式保存或传输。

详见 [安全设计](./security)。

---

## 其他问题

### ❓ 如何获取完整的错误日志？

**A:** 日志文件位置：

| 操作系统 | 日志路径 |
|-----------|----------|
| macOS | `~/Library/Logs/Narrafiilm/app.log` |
| Linux | `~/.videoforge/logs/app.log` |
| Windows | `%APPDATA%\Narrafiilm\logs\app.log` |

查看实时日志：

```bash
tail -f ~/.videoforge/logs/app.log
```

### ❓ 如何回滚到旧版本？

```bash
# GitHub 上找到旧版本
# 下载对应版本的安装包
# 先卸载当前版本
pip uninstall videoforge
# 安装旧版本
pip install videoforge==2.0.0
```

### ❓ 如何反馈问题或建议？

| 方式 | 入口 |
|------|------|
| Bug 报告 | [GitHub Issues](https://github.com/Agions/Narrafiilm/issues/new?template=bug_report.md) |
| 功能建议 | [GitHub Discussions](https://github.com/Agions/Narrafiilm/discussions) |
| 文档纠错 | 直接提交 PR |

::: tip 💡 提问技巧
报告问题时，请附上：
1. 操作系统和版本
2. Narrafiilm 版本
3. 完整的错误信息
4. 操作步骤（如何复现）
这能帮助我们更快定位和解决问题。
:::

---

## 疑难排查

以下问题通常不在日常使用中出现，但在特定环境下可能遇到。

### ❓ 报错 `libEGL.so.1: cannot open shared object file`？

**A:** PySide6 依赖 EGL 图形库，系统未安装：

```bash
# Ubuntu / Debian
sudo apt install libegl1 libgl1 libopengl0

# 验证
ldconfig -p | grep libEGL
```

---

### ❓ 提示 `System keyring not available`？

**A:** Linux 下 keyring 服务不可用。**不影响主功能**，只是 API Key 无法安全存储（仍可正常使用）：

```bash
# 可选：安装 keyring 服务
sudo apt install libsecret-1-0 gnome-keyring
```

---

### ❓ 提示 `Couldn't load pipewire-0.3 library`？

**A:** Qt 音频后端尝试加载 pipewire 失败，**不影响视频处理功能**：

```bash
# 可选：安装 pipewire 库
sudo apt install pipewire-audio-client-libraries

# 或强制使用 ALSA 后端
export QT_AUDIO_BACKEND=alsa
```

---

### ❓ 窗口显示不完整 / UI 错位 / 文字过小？

**A:** 高 DPI 屏幕缩放不匹配。尝试强制设置缩放：

```bash
# 自动适应屏幕
QT_AUTO_SCREEN_SCALE_FACTOR=1 python3 main.py

# 关闭缩放
QT_AUTO_SCREEN_SCALE_FACTOR=0 QT_SCALE_FACTOR=1 python3 main.py

# 强制 200% 缩放
QT_SCALE_FACTOR=2 python3 main.py
```

---

### ❓ 界面中文显示为方块（豆腐字符）？

**A:** 系统缺少 Noto CJK 字体：

```bash
# Ubuntu / Debian
sudo apt install fonts-noto-cjk

# macOS 一般自带，无需处理
# Windows：安装「Noto Sans CJK」字体
```

---

### ❓ 视频导入或导出速度极慢？

**A:** 源视频未经优化（高码率、H.265/HEVC、60fps 等格式对编辑不友好）：

1. 在剪映/Jianying 中先将视频导出为：
   - 分辨率：1080p
   - 编码：H.264（AVC）
   - 帧率：30fps
   - 码率：8–15 Mbps
2. 再导入 Narrafiilm 编辑

> 小体积、易处理的源素材能显著提升编辑和导出速度。

---

### ❓ 如何获取完整调试日志？

**A:** 在终端运行以下命令，将输出保存到文件：

```bash
# 完整 stdout 日志
QT_LOGGING_TO_STDOUT=1 python3 main.py 2>&1 | tee debug.log

# 无头模式（无显示器环境）
QT_QPA_PLATFORM=offscreen python3 main.py

# 组合使用
QT_LOGGING_TO_STDOUT=1 QT_QPA_PLATFORM=offscreen python3 main.py 2>&1 | tee debug.log
```

提交 Issue 时附上 `debug.log` 可大幅加快问题定位。
