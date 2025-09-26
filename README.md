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

### 使用 venv

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

## 许可证

MIT License - 详见 LICENSE 文件

## 联系

- Email: team@cineaistudio.com
- GitHub Issues: [Issues](https://github.com/agions/cineai-studio/issues)

---

_Copyright © 2025 CineAIStudio Team_
