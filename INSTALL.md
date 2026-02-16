# 安装指南

CineFlow 支持 Windows 和 macOS 平台。

## 目录

- [系统要求](#系统要求)
- [Windows 安装](#windows-安装)
- [macOS 安装](#macos-安装)
- [源码安装](#源码安装)
- [配置说明](#配置说明)
- [常见问题](#常见问题)

## 系统要求

| 组件 | 最低要求 | 推荐配置 |
|------|---------|---------|
| 操作系统 | Windows 10 / macOS 10.15 | Windows 11 / macOS 14 |
| 处理器 | Intel/AMD x64 | Apple Silicon / Intel i5+ |
| 内存 | 4GB | 8GB+ |
| 存储 | 2GB 可用空间 | 10GB+ SSD |
| 网络 | 可选 | 需要API调用 |

## Windows 安装

### 方式一：安装包（推荐）

1. 下载最新版安装包
   - 访问 [Releases](https://github.com/Agions/CineFlow/releases)
   - 下载 `CineFlow-Setup-x64.exe`

2. 运行安装程序
   - 双击下载的 `.exe` 文件
   - 按向导提示完成安装

3. 启动应用
   - 桌面快捷方式
   - 或开始菜单 → CineFlow

### 方式二：便携版

1. 下载便携版
   - 下载 `CineFlow-Portable.zip`

2. 解压到任意位置
   ```powershell
   # 使用 PowerShell
   Expand-Archive CineFlow-Portable.zip -DestinationPath C:\CineFlow
   ```

3. 运行
   - 双击 `CineFlow.exe`

## macOS 安装

### 方式一：DMG 安装包（推荐）

1. 下载最新版
   - 访问 [Releases](https://github.com/Agions/CineFlow/releases)
   - 下载 `CineFlow-x64.dmg` (Intel) 或 `CineFlow-arm64.dmg` (Apple Silicon)

2. 打开 DMG
   - 双击下载的 `.dmg` 文件

3. 安装应用
   - 将 `CineFlow.app` 拖到 `Applications` 文件夹

4. 首次运行
   - 右键点击 `CineFlow.app` → 打开
   - 或前往 系统设置 → 隐私与安全性 → 允许

### 方式二：Homebrew（即将支持）

```bash
# 即将支持
brew install --cask cineflow
```

## 源码安装

适合开发者或需要自定义功能的用户。

### 1. 环境准备

**Windows:**
```powershell
# 安装 Python 3.9+
# 从 https://python.org 下载安装

# 安装 Git
# 从 https://git-scm.com/download/win 下载

# 安装 FFmpeg（可选，内置）
# 或使用 chocolatey
choco install ffmpeg
```

**macOS:**
```bash
# 安装 Homebrew（如未安装）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装 Python
brew install python@3.11

# 安装 FFmpeg（可选，内置）
brew install ffmpeg
```

### 2. 克隆仓库

```bash
git clone https://github.com/Agions/CineFlow.git
cd CineFlow
```

### 3. 创建虚拟环境

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. 安装依赖

```bash
pip install -r requirements.txt
```

### 5. 配置 API 密钥

创建 `.env` 文件：

```bash
# 复制示例配置
cp .env.example .env

# 编辑 .env 文件，填入你的 API 密钥
```

### 6. 运行

```bash
# 方式一：使用启动脚本
python launch.py

# 方式二：直接运行
python -m app.main
```

## 配置说明

### API 密钥获取

#### DeepSeek (导演、审核)
1. 访问 [DeepSeek 开放平台](https://platform.deepseek.com/)
2. 注册账号
3. 创建 API Key
4. 复制到 `.env` 文件

#### Moonshot/Kimi (剪辑、调色、特效)
1. 访问 [Moonshot 开放平台](https://platform.moonshot.cn/)
2. 注册账号
3. 创建 API Key
4. 复制到 `.env` 文件

#### 阿里云 (音效)
1. 访问 [阿里云 DashScope](https://dashscope.aliyun.com/)
2. 开通服务
3. 创建 API Key
4. 复制到 `.env` 文件

### 配置文件示例

```bash
# .env 文件

# DeepSeek API
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# Moonshot API
MOONSHOT_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# 阿里云 DashScope
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# 百度文心（可选）
BAIDU_API_KEY=xxxxxxxxxxxxxxxx
BAIDU_SECRET_KEY=xxxxxxxxxxxxxxxx
```

## 常见问题

### Q: Windows 提示 "Windows 已保护你的电脑"

这是 Windows SmartScreen 的提示，因为应用未进行代码签名。

**解决方法：**
1. 点击 "更多信息"
2. 点击 "仍要运行"

### Q: macOS 提示 "无法打开，因为无法验证开发者"

**解决方法：**
1. 右键点击应用 → 打开
2. 或前往 系统设置 → 隐私与安全性 → 安全性 → 允许

### Q: 启动时报错 "FFmpeg 不可用"

**解决方法：**
1. 确保 FFmpeg 已安装
2. 或将 FFmpeg 放入 `resources/ffmpeg/` 目录
3. 或设置环境变量 `FFMPEG_PATH`

### Q: API 调用失败

**检查清单：**
- [ ] API Key 是否正确
- [ ] 网络连接是否正常
- [ ] 账户余额是否充足
- [ ] 是否配置了正确的 `.env` 文件

### Q: 如何更新到最新版本

**安装包用户：**
1. 下载最新版安装包
2. 直接安装（会自动覆盖旧版本）
3. 配置会保留

**源码用户：**
```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

### Q: 如何卸载

**Windows:**
- 设置 → 应用 → 找到 CineFlow → 卸载
- 或运行安装目录的 `uninstall.exe`

**macOS:**
- 将 `CineFlow.app` 拖到废纸篓
- 删除配置：`~/Library/Application Support/CineFlow`

## 获取帮助

- 📖 [查看文档](./README.md)
- 🐛 [提交 Issue](https://github.com/Agions/CineFlow/issues)
- 💬 [加入讨论](https://github.com/Agions/CineFlow/discussions)

---

**提示：** 首次使用建议先阅读 [快速开始](./README.md#快速开始) 指南。
