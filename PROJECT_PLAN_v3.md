# CineFlow v3.0 项目规划

> 多Agent智能视频剪辑系统 | 跨平台支持 (Windows & macOS)

---

## 🎯 产品定位

**CineFlow v3.0** 是一款基于多Agent协同的智能视频剪辑工具，专为内容创作者设计：

- 🎬 **多Agent专业分工** - 导演/剪辑/调色/音效/特效/审核，各司其职
- 🤖 **AI驱动全流程** - 从素材分析到成品输出，全程智能化
- 💻 **跨平台原生应用** - 支持 Windows (.exe) 和 macOS (.app/.dmg)
- 🎨 **剪映无缝对接** - 一键导出剪映草稿，延续创作流程

---

## 🏗️ 核心架构

### 多Agent协同系统

```
┌─────────────────────────────────────────────────────────────┐
│                      CineFlow v3.0                          │
├─────────────────────────────────────────────────────────────┤
│  UI Layer (React + TypeScript)                              │
│  ├── Dashboard - 项目仪表盘                                  │
│  ├── Agent Monitor - Agent实时监控                          │
│  ├── Timeline Editor - 简化时间线编辑                        │
│  └── Export Center - 导出管理                               │
├─────────────────────────────────────────────────────────────┤
│  Agent Orchestration Layer                                   │
│  ├── AgentManager - Agent调度管理器                          │
│  ├── TaskScheduler - 任务调度器                              │
│  └── MessageBus - Agent间通信总线                           │
├─────────────────────────────────────────────────────────────┤
│  Agent Pool (6 Professional Agents)                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Director │ │  Editor  │ │Colorist  │ │  Sound   │       │
│  │  导演    │ │  剪辑    │ │  调色    │ │  音效    │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  ┌──────────┐ ┌──────────┐                                   │
│  │   VFX    │ │ Reviewer │                                   │
│  │  特效    │ │  审核    │                                   │
│  └──────────┘ └──────────┘                                   │
├─────────────────────────────────────────────────────────────┤
│  AI Engine (国产大模型)                                       │
│  ├── DeepSeek-V3 - 规划/推理                                  │
│  ├── Kimi K2.5 - 长文本/视觉理解                               │
│  ├── Qwen 2.5 - 音频/多模态                                   │
│  └── ERNIE 4.0 - 创意生成                                     │
├─────────────────────────────────────────────────────────────┤
│  Core Services                                               │
│  ├── VideoProcessor - FFmpeg视频处理                         │
│  ├── AudioEngine - 音频处理与TTS                              │
│  ├── DraftExporter - 剪映草稿导出                             │
│  └── ProjectManager - 项目管理                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤖 Agent详细设计

### Agent分工与模型配置

| Agent | 职责 | 国产模型 | 核心能力 |
|-------|------|----------|----------|
| **Director** | 项目规划、任务分配、质量把控 | DeepSeek-V3 | 强逻辑推理、规划能力 |
| **Editor** | 粗剪、精剪、转场、节奏 | Kimi K2.5 | 256K超长上下文，视频结构分析 |
| **Colorist** | 调色、风格化、LUT匹配 | Kimi K2.5 | 视觉理解，色彩分析 |
| **Sound** | 音效、配乐、混音、TTS | Qwen 2.5 | 音频理解，多模态处理 |
| **VFX** | 特效、动画、合成 | Kimi K2.5 | 画面理解+特效生成 |
| **Reviewer** | 质量检查、问题反馈 | DeepSeek-Coder | 细致评估，代码化检查 |

### Agent协作流程

```
用户上传素材
    ↓
┌─────────────────────────────────────────┐
│ DirectorAgent                           │
│ - 分析项目需求                          │
│ - 制定剪辑计划                          │
│ - 分配任务给各Agent                      │
└─────────────────────────────────────────┘
    ↓
    ┌──────────────┬──────────────┬──────────────┐
    ↓              ↓              ↓              ↓
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│ Editor  │  │Colorist │  │  Sound  │  │   VFX   │
│ 剪辑    │  │ 调色    │  │ 音效    │  │ 特效    │
│ (并行)  │  │ (并行)  │  │ (并行)  │  │ (并行)  │
└─────────┘  └─────────┘  └─────────┘  └─────────┘
    ↓              ↓              ↓              ↓
    └──────────────┴──────────────┴──────────────┘
    ↓
┌─────────────────────────────────────────┐
│ ReviewerAgent                           │
│ - 技术质量检查                          │
│ - 内容质量检查                          │
│ - 生成修改建议                          │
└─────────────────────────────────────────┘
    ↓ (如有问题，循环回各Agent修改)
    ↓ (通过审核)
┌─────────────────────────────────────────┐
│ DirectorAgent                           │
│ - 整合各Agent输出                       │
│ - 生成最终成品                          │
│ - 导出剪映草稿                          │
└─────────────────────────────────────────┘
    ↓
成品输出
```

---

## 💻 跨平台架构

### 技术栈

| 层级 | Windows | macOS | 说明 |
|------|---------|-------|------|
| **UI** | Electron + React | Electron + React | 统一前端框架 |
| **后端** | Python + FastAPI | Python + FastAPI | 共享Python核心 |
| **打包** | PyInstaller + NSIS | PyInstaller + create-dmg | 原生安装包 |
| **视频处理** | FFmpeg ( bundled ) | FFmpeg ( bundled ) | 内置FFmpeg |

### 项目结构

```
CineFlow/
├── app/
│   ├── agents/              # 多Agent系统
│   │   ├── base_agent.py
│   │   ├── director_agent.py
│   │   ├── editor_agent.py
│   │   ├── colorist_agent.py
│   │   ├── sound_agent.py
│   │   ├── vfx_agent.py
│   │   ├── reviewer_agent.py
│   │   ├── agent_manager.py
│   │   └── llm_client.py    # 国产大模型客户端
│   │
│   ├── ui/                  # 前端UI (React)
│   │   ├── src/
│   │   │   ├── components/  # 组件
│   │   │   ├── pages/       # 页面
│   │   │   ├── stores/      # 状态管理
│   │   │   └── utils/       # 工具函数
│   │   ├── public/
│   │   └── package.json
│   │
│   ├── core/                # 核心服务
│   │   ├── video_processor.py
│   │   ├── audio_engine.py
│   │   ├── draft_exporter.py
│   │   └── project_manager.py
│   │
│   └── main.py              # 主入口
│
├── build/                   # 打包配置
│   ├── windows/
│   │   ├── build.py
│   │   └── installer.nsi
│   └── macos/
│       ├── build.py
│       └── entitlements.plist
│
├── resources/               # 资源文件
│   ├── ffmpeg/
│   │   ├── windows/
│   │   └── macos/
│   ├── models/              # 本地模型
│   └── presets/             # 预设配置
│
├── tests/                   # 测试
├── docs/                    # 文档
├── scripts/                 # 脚本
├── requirements.txt
├── package.json
└── README.md
```

---

## 📋 开发路线图

### Phase 1: 多Agent系统完善 (Week 1-2)

#### Week 1: Agent核心功能
- [ ] ColoristAgent 完整实现
  - 色彩分析 (Kimi K2.5视觉)
  - LUT生成与应用
  - 风格迁移
- [ ] SoundAgent 完整实现
  - 音频分析 (Qwen 2.5)
  - 音效推荐与生成
  - TTS配音集成
- [ ] VFXAgent 完整实现
  - 画面理解 (Kimi K2.5)
  - 特效参数生成
  - 素材描述生成

#### Week 2: Agent协作与监控
- [ ] AgentManager 完善
  - 任务调度优化
  - 并行执行控制
  - 错误恢复机制
- [ ] Agent监控UI
  - 实时状态显示
  - 进度追踪
  - 日志查看
- [ ] 集成测试
  - Agent协作流程测试
  - 端到端测试

### Phase 2: 跨平台支持 (Week 3-4)

#### Week 3: Windows打包
- [ ] FFmpeg Windows捆绑
- [ ] PyInstaller配置
- [ ] NSIS安装程序
- [ ] Windows测试

#### Week 4: macOS打包
- [ ] FFmpeg macOS捆绑
- [ ] 代码签名
- [ ] Notarization
- [ ] DMG生成
- [ ] macOS测试

### Phase 3: UI重构 (Week 5-6)

#### Week 5: 核心页面
- [ ] Dashboard - 项目仪表盘
  - 项目列表
  - 快捷操作
  - 统计信息
- [ ] Agent Monitor - Agent监控
  - 实时状态
  - 任务队列
  - 资源使用
- [ ] Creator - 创作向导
  - 步骤引导
  - 素材上传
  - 参数配置

#### Week 6: 编辑与导出
- [ ] Timeline Editor - 简化时间线
  - 片段预览
  - 基础剪辑
  - Agent建议展示
- [ ] Export Center - 导出管理
  - 格式选择
  - 剪映草稿导出
  - 批量导出

### Phase 4: 功能完善 (Week 7-8)

#### Week 7: 功能增强
- [ ] 智能解说增强
  - 更多解说风格
  - 情绪匹配优化
  - 批量生成
- [ ] 智能混剪增强
  - 节拍检测优化
  - 智能匹配算法
  - 转场库扩展

#### Week 8: 质量与文档
- [ ] 性能优化
- [ ] 错误处理完善
- [ ] 文档更新
- [ ] 用户手册
- [ ] 视频教程

---

## 🛠️ 技术规范

### Agent开发规范

```python
class AgentExample(BaseAgent):
    """
    Agent开发模板
    """
    
    def __init__(self):
        super().__init__(
            name="Agent名称",
            capabilities=[AgentCapability.XXX]
        )
        # 初始化对应的大模型
        self.init_llm('agent_type')
    
    async def execute(self, task: Dict) -> AgentResult:
        """
        执行任务
        """
        # 1. 报告进度
        self.report_progress(10, "开始任务...")
        
        # 2. 调用LLM进行智能分析
        llm_result = await self.call_llm(
            prompt="分析任务...",
            system_prompt="你是专业的..."
        )
        
        # 3. 执行专业操作
        self.report_progress(50, "执行中...")
        
        # 4. 返回结果
        return AgentResult(
            success=True,
            data={},
            message="任务完成"
        )
```

### 国产大模型调用规范

```python
# 统一通过LLMClient调用
from app.agents.llm_client import LLMClient

# 为Agent创建客户端
llm = LLMClient.for_agent('director')  # DeepSeek-V3
llm = LLMClient.for_agent('editor')    # Kimi K2.5
llm = LLMClient.for_agent('sound')     # Qwen 2.5

# 文本生成
result = await llm.complete(
    prompt="分析视频...",
    system_prompt="你是专业剪辑师"
)

# 视觉分析 (Kimi K2.5)
result = await llm.analyze_image(
    image_path="frame.jpg",
    prompt="分析画面色彩..."
)
```

---

## 📦 发布计划

### v3.0.0-beta (Week 6)
- 多Agent系统完整实现
- 基础UI重构
- Windows/macOS打包

### v3.0.0-rc.1 (Week 7)
- 功能完善
- 集成测试
- 文档更新

### v3.0.0 正式版 (Week 8)
- 性能优化
- Bug修复
- 正式发布

---

## 🎯 验收标准

### 功能验收
- [ ] 6个Agent可独立工作
- [ ] Agent协作流程完整
- [ ] Windows安装包可正常运行
- [ ] macOS安装包可正常运行
- [ ] 剪映草稿导出功能正常

### 性能验收
- [ ] 视频处理速度 > 2x 实时
- [ ] UI响应 < 100ms
- [ ] 内存占用 < 4GB
- [ ] 安装包大小 < 500MB

### 质量验收
- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试通过率 100%
- [ ] 无P0/P1级别Bug
- [ ] 文档完整度 100%

---

## 📚 相关文档

- [README.md](./README.md) - 项目介绍
- [ROADMAP.md](./ROADMAP.md) - 开发路线图
- [DEVELOPER.md](./DEVELOPER.md) - 开发指南
- [INSTALL.md](./INSTALL.md) - 安装指南
- [CHANGELOG.md](./CHANGELOG.md) - 更新日志

---

**规划版本**: v3.0.0
**规划日期**: 2025-01-20
**预计发布**: 2025-03-15
