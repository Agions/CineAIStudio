# CineFlow AI 安装指南

> 完整的安装、配置和故障排查指南

---

## 📋 系统要求

### 操作系统
- Windows 10 或更高版本 (推荐)
- macOS 11 (Big Sur) 或更高版本
- Linux (Ubuntu 20.04+, Debian 11+)

### 软件依赖
- **Python**: 3.12 或更高版本
- **pip**: Python 包管理器
- **FFmpeg**: 视频处理工具

---

## 🚀 快速开始

### 1. 克隆仓库

```bash
# 使用 HTTPS
git clone https://github.com/Agions/CineAIStudio.git
cd CineAIStudio

# 或使用 SSH
git clone git@github.com:Agions/CineAIStudio.git
cd CineAIStudio
```

### 2. 创建虚拟环境（推荐）

```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置 LLM API

**重要**: CineFlow AI 需要 LLM API 才能生成 AI 文案和处理视频。

#### 4.1 创建配置文件

```bash
# 复制示例配置
cp config/llm.yaml.example config/llm.yaml
# 或直接编辑现有的 config/llm.yaml
```

#### 4.2 获取 API 密钥

选择以下任一提供商：

| 提供商 | 注册地址 | 说明 |
|--------|----------|------|
| **通义千问** (推荐) | https://bailian.console.aliyun.com/ | 国产大模型，免费额度大 |
| **Kimi** | https://platform.moonshot.cn/ | 月之暗面，长文本能力强 |
| **智谱 GLM** | https://open.bigmodel.cn/ | GLM-5，推理能力强 |

#### 4.3 配置 API 密钥

编辑 `config/llm.yaml`:

```yaml
LLM:
  # 默认提供商 (qwen | kimi | glm5 | openai | local)
  default_provider: "qwen"

  # 通义千问 Qwen 3 (推荐)
  qwen:
    enabled: true
    api_key: "你的API密钥"  # 替换为你的密钥
    base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model: "qwen-plus"
    max_tokens: 2000
    temperature: 0.7
```

**推荐使用通义千问**的理由：
- ✅ 免费额度大（每月 100 万 tokens）
- ✅ 响应速度快
- ✅ 中文支持好
- ✅ API 稳定

#### 4.4 或使用环境变量（推荐）

```bash
# macOS / Linux
export QWEN_API_KEY="你的API密钥"

# Windows (PowerShell)
$env:QWEN_API_KEY="你的API密钥"

# Windows (CMD)
set QWEN_API_KEY=你的API密钥
```

### 5. 验证安装

```bash
# 检查版本
python3 scripts/check_version.py

# 运行单元测试
pytest tests/ -v
```

预期输出：
```
✅ 版本一致!
```

### 6. 启动应用

```bash
# 命令行启动
python3 app/main.py

# 或使用配置的命令入口
cineflow-ai
```

---

## 🔧 故障排查

### 问题 1: Windows 无法启动

**错误信息**:
```
ValueError: mutable default <class 'PyQt6.QtGui.QColor'> for field background_color is not allowed
```

**解决方案**:

```bash
# 升级 Python 到 3.12
py --version

# 重新安装 PyQt6
pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip
pip install PyQt6>=6.9.0 PyQt6-Qt6>=6.9.0 PyQt6-sip>=13.10.0

# 清理并重新安装
pip cache purge
pip install -r requirements.txt --upgrade --force-reinstall
```

### 问题 2: 所有功能不可用

**原因**: 未配置 LLM API

**解决方案**:

1. 获取 API 密钥（参考步骤 4）
2. 配置 `config/llm.yaml`
3. 重启应用

---

## 📦 依赖包详解

### 核心依赖

```
PyQt6>=6.9.0          # 图形界面
opencv-python>=4.8.1  # 视频/图像处理
numpy>=1.26.0          # 数值计算
pillow>=10.1.0         # 图像处理
ffmpeg-python==0.2.0   # FFmpeg Python 绑定
```

### AI 依赖

```
openai>=1.0.0          # OpenAI SDK (兼容)
httpx>=0.25.0          # 异步 HTTP 客户端
pyyaml>=6.0.1          # YAML 配置解析
```

### 可选依赖（开发）

```
pytest>=7.4.0          # 测试框架
black>=23.11.0         # 代码格式化
mypy>=1.7.0           # 静态类型检查
```

---

## 🎯 首次使用指南

### 1. 启动应用

```
cineflow-ai
```

### 2. 验证 API 连接

在应用界面中：
- 点击「AI 配置」
- 选择「通义千问」
- 输入 API 密钥
- 点击「测试连接」

**预期结果**: ✅ 连接成功

### 3. 生成第一个视频

1. 点击「AI 视频创作」
2. 输入主题：例如「分析《流浪地球》的科学设定」
3. 选择风格：「解说」
4. 选择时长：「60 秒」
5. 点击「生成文案」

---

## 📚 更多资源

- [快速上手指南](QUICKSTART.md)
- [故障排查手册](TROUBLESHOOT.md)
- [GitHub Issues](https://github.com/Agions/CineAIStudio/issues)

---

## 💡 常见问题

### Q: 是否必须配置 API？

**A**: 是的。CineFlow AI 是一个 AI 驱动的视频创作工具，所有功能都需要 LLM API 支持。

### Q: 如何选择 LLM 提供商？

**A**:
- **通义千问**: 推荐，免费额度大，性价比高
- **Kimi**: 长文本能力强
- **GLM-5**: 推理能力强

### Q: 是否支持本地模型？

**A**: 支持，但需要自行部署（如 Ollama）。推荐使用 API，更稳定、更快。

### Q: Windows 用户需要额外配置什么？

**A**:
1. 安装 FFmpeg（视频处理必需）
2. 确保正确安装 Python 3.12+
3. 使用最新版 PyQt6

---

**最后更新**: 2026-02-14
**版本**: v2.0.0-rc.1
