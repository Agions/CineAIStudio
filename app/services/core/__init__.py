"""核心服务模块"""

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

from .workflow_engine import (
    WorkflowEngine,
    WorkflowStep,
    WorkflowStatus,
    WorkflowState,
    WorkflowCallbacks,
    CreationMode,
    ExportFormat,
    VideoSource,
    AnalysisResult,
    ScriptData,
    TimelineData,
    VoiceoverData,
    create_workflow,
)

from .project_manager import (
    ProjectManager,
    ProjectType,
    ProjectVersion,
    ProjectMetadata,
    ProjectSource,
    ProjectConfig,
    ClipFlowProject,
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
    # 撤销管理
    'UndoManager',
    'Command',
    'CompoundCommand',
    'SnapshotCommand',
    'PropertyChangeCommand',
    'ListAddCommand',
    'ListRemoveCommand',
    'CommandStatus',
    
    # 工作流引擎
    'WorkflowEngine',
    'WorkflowStep',
    'WorkflowStatus',
    'WorkflowState',
    'WorkflowCallbacks',
    'CreationMode',
    'ExportFormat',
    'VideoSource',
    'AnalysisResult',
    'ScriptData',
    'TimelineData',
    'VoiceoverData',
    'create_workflow',
    
    # 项目管理
    'ProjectManager',
    'ProjectType',
    'ProjectVersion',
    'ProjectMetadata',
    'ProjectSource',
    'ProjectConfig',
    'ClipFlowProject',
    'save_project',
    'load_project',
    
    # 批量处理
    'BatchProcessor',
    'BatchTask',
    'BatchConfig',
    'BatchResult',
    'BatchOperation',
    'TaskStatus',
    'batch_analyze',
    'batch_subtitles',
    'batch_transcode',
    
    # 提示词模板
    'PromptTemplateManager',
    'PromptTemplate',
    'TemplateCategory',
    'TemplateVariable',
    'get_template_manager',
    'render_template',
    'get_builtin_templates',
]
