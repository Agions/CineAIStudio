---
title: 疑难排查
description: Narrafiilm 常见问题的详细解决方案。
---

# 疑难排查

---

## 启动问题

### 应用启动无反应（Windows）

可能缺少 Visual C++ 运行库。

**解决方案**：下载并安装 [VC++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)，然后重试。

---

### 应用启动无反应（Linux 无头环境）

这是正常行为。Linux 服务器或 Docker 环境会自动切换到 `QT_QPA_PLATFORM=offscreen` 模式，不显示图形界面。

```bash
# 手动指定无头模式
export QT_QPA_PLATFORM=offscreen
python3 app/main.py
```

如果在没有显示器的桌面 Linux 上也无反应：

```bash
sudo apt install libegl1 libgl1 libxkbcommon0 libdbus-1-3
```

---

## FFmpeg 问题

### 提示 "FFmpeg not found"

FFmpeg 是核心依赖，未安装时所有视频操作失败。

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg

# Windows
# 下载 https://www.gyan.dev/ffmpeg/builds/
# 解压后将 bin 目录加入 PATH，重启终端
```

验证安装：

```bash
ffmpeg -version
```

---

## API 问题

### 401 / 403 错误

API Key 无效、过期或账户额度用尽。

1. 登录 [platform.deepseek.com](https://platform.deepseek.com) 检查 Key 状态和余额
2. 确认 Key 填写正确（注意没有多余空格）
3. 重新复制 Key 粘贴到应用设置

### 429 Rate Limit

触发了 API 速率限制。等待 1 分钟重试，或在 DeepSeek 控制台查看配额。

### 网络超时

网络连接不稳定。检查：
- 本机网络是否正常
- API 服务是否可用（[status.deepseek.com](https://status.deepseek.com)）
- 是否有代理 / VPN 干扰

---

## 视频处理问题

### 视频加载失败

- 确认文件格式受支持：MP4 / MOV / AVI / MKV / WebM
- 确认视频文件未损坏（用播放器打开测试）
- 确认磁盘空间充足（导出需要原片 2–3 倍空间）

### 处理到一半卡住

- 长视频（30 分钟+）建议分段处理
- 检查网络连接（API 调用需要网络）
- 查看应用日志（应用目录下的 `logs/` 文件夹）

### 显存不足（OOM）

GPU 模式对显存要求高。关闭 GPU 加速：

设置 → AI 配置 → 启用 GPU 加速 → **关闭**

或减少抽帧密度：设置 → 场景理解 → 抽帧间隔 → 2 秒

---

## 导出问题

### 导出失败

1. 确认磁盘空间充足
2. 检查输出目录是否有写入权限
3. 临时关闭杀毒软件（部分杀软会拦截 FFmpeg）
4. 尝试换用 H.264 编码（兼容性最好）

### 导出后视频无声音

检查导出设置中 **"保留配音音轨"** 是否勾选。默认仅导出 AI 配音，原片音频需手动开启。

### 剪映草稿无法导入

- 确认剪映版本为最新
- 草稿 JSON 需在剪映内通过"导入草稿"加载，不可直接双击
- 避免在包含中文字符的路径下保存草稿

---

## 配音问题

### Edge-TTS 无法连接

- 检查网络连接
- 确认可以访问 `edge.tts.azureedge.net`
- 临时切换到 F5-TTS（完全本地，无需网络）

### 配音和字幕不同步

字幕同步依赖 TTS word-level timing，通常精度在 50ms 以内。明显不同步时：

1. 确认使用 Edge-TTS（非第三方 TTS）
2. 检查解说稿是否有异常字符或特殊符号
3. 在设置中开启 **强制重新对齐**

---

## 获取帮助

以上无法解决？去 [GitHub Issues](https://github.com/Agions/Narrafiilm/issues) 搜索或新建 issue，并附上：

- Narrafiilm 版本（设置 → 关于）
- 操作系统版本
- 完整的错误日志（`logs/` 目录下）
- 复现步骤
