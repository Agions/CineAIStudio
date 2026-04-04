"""编排服务模块

子模块：
- enums.py        工作流枚举（WorkflowStep/CreationMode/WorkflowStatus/ExportFormat）
- models.py       工作流数据模型（VideoSource/ScriptData/TimelineData 等）
- workflow_engine.py  工作流引擎主体（WorkflowEngine）
- project_manager.py  项目管理
- batch_processor.py  批量处理
- undo_manager.py    撤销管理
- prompt_templates.py 提示词模板
"""

from .enums import (
    WorkflowStep,
    CreationMode,
    WorkflowStatus,
    ExportFormat,
)

from .models import (
    VideoSource,
    AnalysisResult,
    ScriptData,
    TimelineData,
    VoiceoverData,
    WorkflowState,
    WorkflowCallbacks,
)

from .workflow_engine import (
    WorkflowEngine,
    create_workflow,
)

from .project_manager import (
    ProjectManager,
    ProjectType,
    ProjectVersion,
    ProjectMetadata,
    ProjectSource,
    ProjectConfig,
    VideoForgeProject,
    save_project,
    load_project,
)

from .batch_processor import (
    BatchProcessor,
    BatchTask,
    BatchConfig,
    BatchResult,
    BatchOperation,
    TaskStatus,
    batch_analyze,
    batch_subtitles,
    batch_transcode,
)

from .undo_manager import (
    UndoManager,
    Command,
    CompoundCommand,
    SnapshotCommand,
    PropertyChangeCommand,
    ListAddCommand,
    ListRemoveCommand,
    CommandStatus,
)

from .prompt_templates import (
    PromptTemplateManager,
    PromptTemplate,
    TemplateCategory,
    TemplateVariable,
    get_template_manager,
    render_template,
    get_builtin_templates,
)

__all__ = [
    # 枚举
    "WorkflowStep",
    "CreationMode",
    "WorkflowStatus",
    "ExportFormat",
    # 数据模型
    "VideoSource",
    "AnalysisResult",
    "ScriptData",
    "TimelineData",
    "VoiceoverData",
    "WorkflowState",
    "WorkflowCallbacks",
    # 工作流引擎
    "WorkflowEngine",
    "create_workflow",
    # 项目管理
    "ProjectManager",
    "ProjectType",
    "ProjectVersion",
    "ProjectMetadata",
    "ProjectSource",
    "ProjectConfig",
    "VideoForgeProject",
    "save_project",
    "load_project",
    # 批量处理
    "BatchProcessor",
    "BatchTask",
    "BatchConfig",
    "BatchResult",
    "BatchOperation",
    "TaskStatus",
    "batch_analyze",
    "batch_subtitles",
    "batch_transcode",
    # 撤销管理
    "UndoManager",
    "Command",
    "CompoundCommand",
    "SnapshotCommand",
    "PropertyChangeCommand",
    "ListAddCommand",
    "ListRemoveCommand",
    "CommandStatus",
    # 提示词模板
    "PromptTemplateManager",
    "PromptTemplate",
    "TemplateCategory",
    "TemplateVariable",
    "get_template_manager",
    "render_template",
    "get_builtin_templates",
]
