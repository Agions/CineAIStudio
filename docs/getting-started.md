# 快速开始

本指南将帮助您快速上手 ClipFlowCut。

## 环境要求

- Python 3.9+
- FFmpeg（需加入系统 PATH）
- macOS 10.15+ / Windows 10+

## 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/Agions/clip-flow-cut.git
cd clip-flow-cut

# 2. 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置 API 密钥
cp .env.example .env
# 编辑 .env，填入所需的 API Key

# 5. 运行应用
python main.py
```

## 首次运行

1. 启动应用后，进入**设置**页面配置 AI API
2. 选择您想要使用的 AI 提供商（OpenAI、Claude、Qwen 等）
3. 输入对应的 API Key
4. 返回**首页**，开始创建您的第一个项目

## 创建项目

1. 点击**项目管理** → **新建项目**
2. 选择项目类型（AI 解说/AI 混剪/AI 独白）
3. 导入素材视频
4. 让 AI 自动完成创作
5. 预览并导出成品

## 下一步

- [核心功能](features.md) - 了解更多功能
- [工作流程](workflow.md) - 深入了解创作流程
- [常见问题](faq.md) - 解答疑惑
