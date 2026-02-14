# CineFlow AI 完整安装指南

## 📋 系统要求

### Windows
- Windows 10/11 (64位)
- Python 3.12+
- 4GB RAM (推荐 8GB+)
- 硬盘空间: 2GB+

### macOS
- macOS 12 (Monterey) 或更高版本
- Python 3.12+
- 4GB RAM (推荐 8GB+)
- 硬盘空间: 2GB+

### Linux (GUI)
- Ubuntu 20.04+ / Fedora 35+ / Debian 11+
- 桌面环境 (GNOME, KDE, etc.)
- Python 3.12+
- X11 或 Wayland 显示服务器

### Linux (CLI)
- 任意 Linux 发行版
- Python 3.12+
- 无需图形界面

---

## 🚀 快速开始

### 1. 下载/克隆项目

```bash
git clone https://github.com/Agions/CineFlow.git
cd CineFlow
```

### 2. 安装依赖

#### 方法 A: 使用 venv (推荐)

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 如果需要开发工具
pip install pytest pytest-cov black flake8 mypy
```

#### 方法 B: 使用 conda

```bash
# 创建环境
conda create -n cineflow python=3.12
conda activate cineflow

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置 API 密钥

#### 方式 A: 编辑配置文件

创建 `config/app_config.yaml`:

```yaml
llm_providers:
  qwen:
    enabled: true
    api_key: "your-qwen-api-key"
    model: "qwen-plus"
    temperature: 0.7
    max_tokens: 2000

  kimi:
    enabled: false
    api_key: "your-kimi-api-key"
    model: "moonshot-v1-8k"

  glm5:
    enabled: false
    api_key: "your-glm5-api-key"
    model: "glm-5"

cache:
  enabled: true
  max_size: 100
  ttl: 3600

retry:
  max_retries: 3
  base_delay: 1.0
  max_delay: 60.0
  backoff_factor: 2.0

default_provider: "qwen"
log_level: "INFO"
```

#### 方式 B: 环境变量

```bash
# 通义千问
export QWEN_API_KEY="your-api-key"

# Kimi
export KIMI_API_KEY="your-api-key"

# GLM-5
export GLM5_API_KEY="your-api-key"
```

### 4. 运行程序

#### GUI 版本 (Windows/macOS/Linux GUI)

```bash
python main.py
```

#### CLI 版本 (无 GUI 环境)

```bash
python cli.py
```

CLI 命令说明:
```
CineFlow> 你好，请介绍一下自己      # 发送到 LLM
CineFlow> @qwen                    # 切换到通义千问
CineFlow> /stats                   # 查看性能统计
CineFlow> /cache                   # 查看缓存统计
CineFlow> /clear                   # 清空缓存
CineFlow> /help                    # 查看帮助
CineFlow> /quit                    # 退出
```

---

## ❓ 常见问题

### 1. ImportError: No module named 'PyQt6'

**原因**: PyQt6 未安装

**解决方案**:

```bash
# Windows/macOS/Linux
pip install PyQt6 PyQt6-Qt6 PyQt6-sip

# 如果安装失败，尝试:
pip install --upgrade pip
pip install PyQt6==6.6.1
```

### 2. ModuleNotFoundError: No module named 'openai'

**原因**: openai 库未安装

**解决方案**:

```bash
pip install openai>=1.0.0
```

### 3. Windows 窗口无法显示

**原因**: 显示设置问题

**解决方案**:

- 更新显卡驱动
- 尝试兼容模式运行
- 检查显示缩放设置 (100% 或 125%)

### 4. macOS "应用程序已损坏"

**原因**: 安全设置阻止

**解决方案**:

```bash
# 终端运行
xattr -cr /path/to/CineFlow.app
sudo spctl --master-disable
```

### 5. Linux 显示错误

**原因**: 缺少 X11 库

**解决方案**:

```bash
# Debian/Ubuntu
sudo apt-get install libxcb-xinerama0 libxcb-cursor0

# Fedora
sudo dnf install libxcb-xinerama libxcb-cursor

# 或使用 CLI 版本 (无需 GUI)
python cli.py
```

### 6. API 密钥错误

**原因**: 配置文件路径或格式错误

**解决方案**:

1. 确认 `config/app_config.yaml` 存在
2. 检查 YAML 格式 (使用 YAML 验证工具)
3. 使用 CLI 测试配置

```bash
python cli.py  # 会自动检查配置
```

### 7. 缓存或性能问题

**原因**: 缓存设置不当

**解决方案**:

编辑 `config/app_config.yaml`:

```yaml
cache:
  enabled: true
  max_size: 100      # 减小缓存大小
  ttl: 3600         # 缩短缓存时间
```

---

## 🐧 Linux 无 GUI 服务器

如果服务器没有图形界面，使用 CLI 版本:

```bash
cd CineFlow
python3 cli.py
```

CLI 功能:
- ✅ 所有 LLM 功能
- ✅ 脚本生成
- ✅ 缓存和重试
- ✅ 性能监控
- ❌ 没有视频编辑界面

---

## 🐳 Docker + VNC (远程 GUI)

### Windows/Linux/macOS 用户

```bash
# 构建镜像
docker build -t cineflow:latest .

# 运行 (端口 5900 用于 VNC)
docker run -d \
  -p 5900:5900 \
  -p 8080:8080 \
  cineflow:latest

# 使用 VNC 客户端连接
# 地址: localhost:5900
# 密码: vncpassword
```

### 使用 noVNC (浏览器访问)

```bash
# 访问 http://localhost:8080
```

---

## 🔧 开发环境

### 安装开发工具

```bash
pip install pytest pytest-cov pytest-asyncio black flake8 mypy
```

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_version.py -v

# 生成覆盖率报告
pytest tests/ --cov=app --cov-report=html
```

### 代码格式化

```bash
# 格式化代码
black app/ tests/

# 检查代码风格
flake8 app/ tests/

# 类型检查
mypy app/
```

---

## 📦 创建安装包

### Windows

```bash
# 使用 PyInstaller
pip install pyinstaller

# 构建 EXE
pyinstaller --onefile --windowed \
  --icon=resources/icons/app_icon_128.png \
  --name=CineFlow \
  main.py

# 安装包位于: dist/CineFlow.exe
```

### macOS

```bash
# 使用 py2app
pip install py2app

# 构建 .app
python setup.py py2app

# 安装包位于: dist/CineFlow.app
```

---

## 📞 获取帮助

- 文档: https://github.com/Agions/CineFlow/tree/main/docs
- Issues: https://github.com/Agions/CineFlow/issues
- 讨论: https://github.com/Agions/CineFlow/discussions

---

**祝使用愉快!** 🚀
