# 更新日志

所有显著变更都将记录在此文件。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

## [3.0.0-beta3] - 2025-01-20

### ✨ 新增

#### 多Agent系统
- 6个专业Agent完整实现
  - DirectorAgent - 项目规划、任务分配
  - EditorAgent - 粗剪精剪、转场节奏
  - ColoristAgent - 调色、LUT匹配
  - SoundAgent - 音效、AI配音
  - VFXAgent - 画面理解、特效生成
  - ReviewerAgent - 质量审核
- AgentManager - 任务调度、状态监控
- Agent间消息通信机制

#### 核心服务
- VideoProcessor - FFmpeg视频处理
  - 视频信息获取（带缓存）
  - 格式转换、分辨率调整
  - 视频剪辑、合并
  - 关键帧提取
  - 场景检测
  - LUT调色
  - 文字叠加
  - 批量处理
- AudioEngine - 音频处理
  - 音频提取、合并
  - TTS配音（Edge/阿里）
  - 节拍检测
  - 音频标准化
  - 混音
- DraftExporter - 剪映草稿导出
  - Windows/macOS自动检测
  - 素材管理
  - 轨道信息
  - 特效支持
  - 字幕导出
- ProjectManager - 项目管理
  - 项目生命周期管理
  - Agent结果跟踪
  - 导入/导出

#### LLM客户端
- 多模型统一接口
- 支持4家国产大模型
  - DeepSeek-V3
  - Kimi K2.5
  - Qwen 2.5
  - ERNIE 4.0
- HTTP连接池复用
- 智能重试机制
- 性能统计
- 视觉分析支持

#### UI界面
- PyQt6主窗口
- Agent监控中心
  - 6个Agent状态卡片
  - 实时状态刷新
  - 任务队列显示
- 项目管理页面
  - 新建/导入项目
  - 项目列表
- 暗色主题
- 异步初始化
- 加载进度显示

#### 跨平台打包
- Windows打包脚本
  - PyInstaller配置
  - NSIS安装程序
- macOS打包脚本
  - 代码签名
  - DMG生成

### 🔧 优化

#### 性能优化
- LLM连接池复用
- 视频信息缓存
- 异步初始化
- 进度回调支持

#### 代码质量
- 类型注解完善
- 文档字符串补充
- 异常处理增强
- 日志记录规范
- 样式系统分离

### 🐛 修复
- Kimi K2.5模型命名修正
- VFXAgent从图像生成改为画面理解
- 国产大模型数据更新为2025年正确版本

### 📚 文档
- 项目规划文档 (PROJECT_PLAN_v3.md)
- 开发路线图 (ROADMAP.md)
- 内存文件 (memory/2025-01-20.md)

## [3.0.0-beta2] - 2025-01-20

### ✨ 新增
- PyQt6 UI实现
  - Agent监控页面
  - 项目管理页面
  - 暗色主题

## [3.0.0-beta1] - 2025-01-20

### ✨ 新增
- 核心功能实现
  - 6个Agent
  - 4个核心服务
  - 跨平台打包脚本

## [2.0.0-rc.1] - 2026-02-14

### ✨ 新增
- 项目重命名为 CineFlow AI
- 版本统一系统
- 国产 LLM 集成 (Qwen, Kimi, GLM-5)
- LLM 管理器 (自动切换)
- 单元测试框架
- 安装指南文档
- 技术栈文档

### 🔧 优化
- 性能优化
- 错误处理增强

## [1.0.0] - 2025-01-01

### ✨ 新增
- 初始版本发布
- 基础视频处理功能
- 简单UI界面

---

[Unreleased]: https://github.com/Agions/CineFlow/compare/v3.0.0-beta3...HEAD
[3.0.0-beta3]: https://github.com/Agions/CineFlow/compare/v3.0.0-beta2...v3.0.0-beta3
[3.0.0-beta2]: https://github.com/Agions/CineFlow/compare/v3.0.0-beta1...v3.0.0-beta2
[3.0.0-beta1]: https://github.com/Agions/CineFlow/compare/v2.0.0-rc.1...v3.0.0-beta1
[2.0.0-rc.1]: https://github.com/Agions/CineFlow/compare/v1.0.0...v2.0.0-rc.1
[1.0.0]: https://github.com/Agions/CineFlow/releases/tag/v1.0.0
