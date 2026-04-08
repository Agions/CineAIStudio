# Narrafiilm UI + 代码重构计划

## 目标

将 Narrafiilm 从「功能堆砌单页」重构为「3步向导 + 单流程 Pipeline」的专业创作工具。

---

## Phase 1: UI 重构（用户可见）

### 1.1 新建 `CreationWizardPage`（向导容器）
- 3 步横向进度指示器
- `current_step: 0|1|2` 控制显示
- Step1 / Step2 / Step3 页面独立，按需加载

### 1.2 Step1 — 上传配置页 (`step_upload.py`)
- 视频拖放 + 元数据显示（时长/分辨率/码率）
- 快速 AI 配置（风格/情感/语言）
- 新建项目名输入 → 自动创建 ProjectManager 项目

### 1.3 Step2 — Pipeline 执行台 (`step_pipeline.py`)
- 横向 4 阶段卡片：理解 → 文案 → 配音 → 字幕
- 每阶段独立状态（idle/running/done/error）
- 中间产物预览（点击阶段卡片展开）
- ScriptEditor 内嵌（文案生成后可编辑再继续）

### 1.4 Step3 — 预览导出页 (`step_export.py`)
- 视频 + 字幕同步预览
- 字幕样式选择（cinematic/minimal/dynamic）
- 导出格式（MP4 / 剪映草稿）

### 1.5 删除旧组件
- 删除 `ai_video_creator_page.py`（733行混用模式）
- 删除 home_page 中的模板卡引用旧模式（MashupMaker 等）
- 清理 `_legacy/` 中已无引用的死代码

---

## Phase 2: 代码结构重构（逻辑层）

### 2.1 PipelineController
- `app/orchestration/pipeline_controller.py`
- 事件驱动：每阶段完成 → Signal → UI 更新
- 支持暂停/跳过/重试
- 单例，通过 ServiceContainer 注入

### 2.2 MonologueMaker 精简
- 只保留 MonologueMaker 单流程
- 暴露各阶段中间产物（供 Step2 预览）
- 移除所有 if creation_type == "mashup"/"commentary" 分支

### 2.3 Service 层清理
- 删除 `services/video/base_maker.py`（空壳接口）
- 删除 `_legacy/mashup_maker.py`（不再引用）
- 确认 `services/video/monologue_maker.py` 外部引用后删除 `_legacy/`

---

## Phase 3: 项目管理激活

### 3.1 ProjectManager 激活
- 项目创建/保存/加载/列表
- 项目元数据（video_path/created_at/pipeline_state）
- 保存 pipeline 中间产物（避免重复调用 AI）

### 3.2 ProjectsPage 重构
- 改为真实项目列表（本地 JSON 存储）
- 支持：新建/打开/删除/重命名

---

## 交付物

| 文件 | 操作 |
|------|------|
| `PLAN.md` | 创建 |
| `app/ui/main/pages/creation_wizard_page.py` | 新建 |
| `app/ui/main/pages/step_upload.py` | 新建 |
| `app/ui/main/pages/step_pipeline.py` | 新建 |
| `app/ui/main/pages/step_export.py` | 新建 |
| `app/orchestration/pipeline_controller.py` | 新建 |
| `app/ui/main/pages/home_page.py` | 重写（清理旧模板卡） |
| `app/ui/main/pages/ai_video_creator_page.py` | 删除 |
| `app/services/video/monologue_maker.py` | 精简 |
| `app/core/project_manager.py` | 激活 |
| `app/ui/main/pages/projects_page.py` | 激活 |

---

## 执行顺序

```
Phase 1 → Phase 2 → Phase 3
（每 Phase 结束后运行测试，测试全过再进入下个 Phase）
```
