# CineAIStudio v2.0

![CineAIStudio Logo](resources/icons/app_icon.png)

专业的 AI 视频编辑器，支持多机位编辑、AI 增强、智能剪辑和云渲染。

## 特性

- **AI 视频增强**：自动画质提升、降噪、智能剪辑
- **多机位编辑**：同步多摄像机源、自动切换、实时预览
- **专业时间线**：多轨道编辑、特效应用、精确控制
- **国产 AI 集成**：支持文心一言、星火、Qwen 等模型
- **云渲染支持**：分布式渲染、高性能导出
- **专业导出**：支持 ProRes、H.265、多格式预设

## 安装

### 使用 Poetry (推荐)

```bash
git clone https://github.com/agions/cineai-studio.git
cd cineai-studio
poetry install
poetry run cineai-studio
```

### 使用 venv (解决 macOS Python 3.12 外部管理环境问题)

```bash
git clone https://github.com/Agions/CineAIStudio.git
cd CineAIStudio
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows
pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

**注意**: 如果遇到 "externally-managed-environment" 错误，请使用虚拟环境 (venv) 安装依赖。requirements.txt 已更新支持 Python 3.12，包括 sparkdesk-python 和 deepseek-sdk 等 AI SDK。

```bash
git clone https://github.com/agions/cineai-studio.git
cd cineai-studio
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows
pip install -e .[dev]
python main.py
```

### 依赖

- Python 3.12+
- PyQt6 for UI
- OpenCV for video processing
- FFmpeg for media handling
- NumPy, Pillow for image processing

## 快速开始

1. **启动应用**

   ```bash
   poetry run cineai-studio
   ```

2. **导入媒体**

   - 点击"导入"按钮选择视频文件
   - 支持 MP4, AVI, MOV, MKV 等格式

3. **AI 增强**

   - 选择视频后点击"AI 增强"
   - 选择"画质增强"或"智能剪辑"

4. **多机位编辑**

   - 导入多个摄像机角度视频
   - 使用"同步"工具对齐时间线
   - 在时间线中切换角度

5. **导出**
   - 点击"导出"选择格式和质量
   - 支持本地导出和云渲染

## 功能模块

### AI 服务集成

- 文心一言 (Baidu)
- 星火大模型 (iFlytek)
- Qwen (Alibaba)
- GLM (Zhipu AI)
- 支持 API 密钥安全存储

### 视频处理引擎

- FFmpeg 集成
- GPU 加速支持
- 实时预览和处理
- 多格式支持

### UI 组件

- PyQt6 现代界面
- 拖拽时间线编辑
- 实时属性调整
- 暗色主题支持

## 架构

详见 [docs/architecture.md](docs/architecture.md)

## API 文档

详见 [docs/api.md](docs/api.md)

## 贡献指南

1. Fork 仓库
2. 创建功能分支 `git checkout -b feature/amazing-feature`
3. 提交更改 `git commit -m 'Add some AmazingFeature'`
4. 推送分支 `git push origin feature/amazing-feature`
5. 创建 Pull Request

### 代码规范

- 使用 Black 格式化
- 类型提示
- 编写单元测试
- 更新文档

## 常见问题 (FAQ)

### 1. pip install 失败，报 "externally-managed-environment" 错误 (macOS)

**问题**: 在 macOS 上运行 `pip install -r requirements.txt` 时出现外部管理环境错误。

**解决方案**:

- 使用虚拟环境 (venv) 安装依赖，避免系统 Python 冲突。
- 按照 "使用 venv" 部分步骤创建 .venv 并激活。
- 示例:
  ```
  python3 -m venv .venv
  source .venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
  ```
- **原因**: macOS Python 3.9+ 默认外部管理，防止系统包冲突。venv 隔离环境解决此问题。

### 2. requirements.txt 缺失 AI 依赖 (sparkdesk-python, deepseek-sdk 等)

**问题**: 安装后 AI 功能报 ImportError 或模型不可用。

**解决方案**:

- requirements.txt 已更新包含所有 AI SDK：
  - iFlytekSpark>=1.0.0 (星火大模型，替换 sparkdesk-python)
  - deepseek-sdk>=1.0.0 (DeepSeek)
  - dashscope>=1.17.7 (通义千问)
  - qianfan>=0.4.6 (文心一言)
  - zhipuai>=2.0.6 (智谱 AI)
- 重新安装: `pip install -r requirements.txt` (在 venv 中)。
- 配置 API 密钥: 编辑 .env 文件添加 API_KEY=your_key (参考 app/core/secure_key_manager.py)。

### 3. Python 版本兼容问题 (非 3.12)

**问题**: 系统 Python 3.9.6，安装失败或运行时版本错误。

**解决方案**:

- requirements.txt 支持 Python 3.9+ (调整版本如 PyQt6>=6.4.0, numpy>=1.21.0)。
- 使用系统 Python 创建 venv 测试安装成功。
- 如果需要 Python 3.12，安装 via Homebrew: `brew install python@3.12`，然后使用 `python3.12 -m venv .venv`。
- 验证版本: `python -V` 应为 3.9+。

### 4. main.py 启动失败或 "管理器问题"

**问题**: 运行 `python main.py` 报 ImportError、QApplication 错误或 UI 不显示。

**解决方案**:

- 确保 venv 激活并依赖安装: `source .venv/bin/activate && pip install -r requirements.txt`。
- 检查 PyQt6 安装: `pip show PyQt6` (应 >=6.4.0)。
- 常见错误:
  - "No module named 'app.core.application'": 确保在项目根目录运行，sys.path 已添加。
  - UI 不启动: 安装 FFmpeg (brew install ffmpeg)，检查日志 (logs/app.log)。
- 测试运行: `python main.py` 应显示启动画面和主窗口，无异常。

### 5. AI 功能不可用 (模型加载失败)

**问题**: AI 增强/字幕生成报 API 错误或模型未找到。

**解决方案**:

- 配置 .env: API_KEY=your_key, MODEL_ID=spark-large-v3.5 等 (参考 app/services/ai_service_manager.py)。
- 测试健康检查: 运行应用，检查 AI 设置页 (一键 AI 配置)。
- 网络问题: 确保代理/防火墙允许访问 AI API (e.g., spark-api.xf-yun.com)。
- 更新 SDK: `pip install --upgrade dashscope qianfan zhipuai iFlytekSpark deepseek-sdk`。

### 6. 视频导入/导出失败

**问题**: 导入 MP4 报格式错误，或导出无输出。

**解决方案**:

- 安装 FFmpeg: `brew install ffmpeg` (macOS) 或系统包管理器。
- 支持格式: MP4/AVI/MOV/MKV (OpenCV/FFmpeg 处理)。
- 权限问题: 确保 .venv 有读写权限，输出路径存在。
- 日志检查: 查看 logs/app.log 错误 (e.g., "FFmpeg not found")。

如果问题持续，检查 GitHub Issues 或提交新 issue 提供日志。

## 许可证

MIT License - 详见 LICENSE 文件

## 联系

- Email: agions@qq.com
- GitHub Issues: [Issues](https://github.com/agions/CineAIStudio/issues)

---

\_Copyright © 2025 Agions
