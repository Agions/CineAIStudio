"""
视频剪辑工作流
定义标准的视频剪辑流程
"""

from typing import Dict, Any, Optional
from datetime import datetime

from app.agents.task_scheduler import (
    TaskScheduler, TaskPriority, TaskDependency, WorkflowDefinition
)
from app.agents import AgentCapability


class VideoEditingWorkflow:
    """
    视频剪辑工作流
    
    标准流程:
    1. 导演规划 (Director) - 分析素材，制定剪辑计划
    2. 粗剪 (Editor) - 按脚本粗剪
    3. 调色 (Colorist) - 色彩校正和风格化
    4. 音效 (Sound) - 配音、配乐、混音
    5. 特效 (VFX) - 添加特效
    6. 审核 (Reviewer) - 质量检查
    7. 导出 (Export) - 生成最终视频
    """
    
    def __init__(self, scheduler: TaskScheduler):
        self.scheduler = scheduler
        self.workflow_id = None
        
    def create_standard_workflow(self) -> str:
        """创建标准剪辑工作流"""
        tasks_config = [
            {
                'name': 'director_planning',
                'task_type': 'planning',
                'params': {},
                'priority': 0,  # CRITICAL
                'required_capabilities': [AgentCapability.PLANNING],
                'dependencies': [],
                'timeout_seconds': 120,
                'max_retries': 1
            },
            {
                'name': 'editor_rough_cut',
                'task_type': 'editing',
                'params': {'mode': 'rough'},
                'priority': 1,  # HIGH
                'required_capabilities': [AgentCapability.EDITING],
                'dependencies': [
                    {'task_id': 'director_planning', 'required_state': 'COMPLETED'}
                ],
                'timeout_seconds': 300,
                'max_retries': 1
            },
            {
                'name': 'colorist_grading',
                'task_type': 'color_grading',
                'params': {},
                'priority': 2,  # NORMAL
                'required_capabilities': [AgentCapability.COLOR_GRADING],
                'dependencies': [
                    {'task_id': 'editor_rough_cut', 'required_state': 'COMPLETED'}
                ],
                'timeout_seconds': 180,
                'max_retries': 1
            },
            {
                'name': 'sound_design',
                'task_type': 'sound_design',
                'params': {},
                'priority': 2,  # NORMAL
                'required_capabilities': [AgentCapability.SOUND_DESIGN],
                'dependencies': [
                    {'task_id': 'editor_rough_cut', 'required_state': 'COMPLETED'}
                ],
                'timeout_seconds': 240,
                'max_retries': 1
            },
            {
                'name': 'vfx_compositing',
                'task_type': 'vfx',
                'params': {},
                'priority': 2,  # NORMAL
                'required_capabilities': [AgentCapability.VFX],
                'dependencies': [
                    {'task_id': 'colorist_grading', 'required_state': 'COMPLETED'}
                ],
                'timeout_seconds': 300,
                'max_retries': 1
            },
            {
                'name': 'reviewer_check',
                'task_type': 'review',
                'params': {},
                'priority': 1,  # HIGH
                'required_capabilities': [AgentCapability.REVIEW],
                'dependencies': [
                    {'task_id': 'vfx_compositing', 'required_state': 'COMPLETED'},
                    {'task_id': 'sound_design', 'required_state': 'COMPLETED'}
                ],
                'timeout_seconds': 120,
                'max_retries': 0
            },
            {
                'name': 'final_export',
                'task_type': 'export',
                'params': {},
                'priority': 0,  # CRITICAL
                'dependencies': [
                    {'task_id': 'reviewer_check', 'required_state': 'COMPLETED'}
                ],
                'timeout_seconds': 600,
                'max_retries': 2
            }
        ]
        
        self.workflow_id = self.scheduler.create_workflow(
            name='standard_video_editing',
            description='标准视频剪辑工作流',
            tasks_config=tasks_config,
            parallel=False,  # 串行执行
            max_parallel=2
        )
        
        return self.workflow_id
        
    def create_parallel_workflow(self) -> str:
        """创建并行剪辑工作流（调色和音效并行）"""
        tasks_config = [
            {
                'name': 'director_planning',
                'task_type': 'planning',
                'params': {},
                'priority': 0,
                'required_capabilities': [AgentCapability.PLANNING],
                'dependencies': [],
                'timeout_seconds': 120,
                'max_retries': 1
            },
            {
                'name': 'editor_rough_cut',
                'task_type': 'editing',
                'params': {'mode': 'rough'},
                'priority': 1,
                'required_capabilities': [AgentCapability.EDITING],
                'dependencies': [
                    {'task_id': 'director_planning', 'required_state': 'COMPLETED'}
                ],
                'timeout_seconds': 300,
                'max_retries': 1
            },
            {
                'name': 'colorist_grading',
                'task_type': 'color_grading',
                'params': {},
                'priority': 2,
                'required_capabilities': [AgentCapability.COLOR_GRADING],
                'dependencies': [
                    {'task_id': 'editor_rough_cut', 'required_state': 'COMPLETED'}
                ],
                'timeout_seconds': 180,
                'max_retries': 1
            },
            {
                'name': 'sound_design',
                'task_type': 'sound_design',
                'params': {},
                'priority': 2,
                'required_capabilities': [AgentCapability.SOUND_DESIGN],
                'dependencies': [
                    {'task_id': 'editor_rough_cut', 'required_state': 'COMPLETED'}
                ],
                'timeout_seconds': 240,
                'max_retries': 1
            },
            {
                'name': 'vfx_compositing',
                'task_type': 'vfx',
                'params': {},
                'priority': 2,
                'required_capabilities': [AgentCapability.VFX],
                'dependencies': [
                    {'task_id': 'colorist_grading', 'required_state': 'COMPLETED'}
                ],
                'timeout_seconds': 300,
                'max_retries': 1
            },
            {
                'name': 'reviewer_check',
                'task_type': 'review',
                'params': {},
                'priority': 1,
                'required_capabilities': [AgentCapability.REVIEW],
                'dependencies': [
                    {'task_id': 'vfx_compositing', 'required_state': 'COMPLETED'},
                    {'task_id': 'sound_design', 'required_state': 'COMPLETED'}
                ],
                'timeout_seconds': 120,
                'max_retries': 0
            },
            {
                'name': 'final_export',
                'task_type': 'export',
                'params': {},
                'priority': 0,
                'dependencies': [
                    {'task_id': 'reviewer_check', 'required_state': 'COMPLETED'}
                ],
                'timeout_seconds': 600,
                'max_retries': 2
            }
        ]
        
        self.workflow_id = self.scheduler.create_workflow(
            name='parallel_video_editing',
            description='并行视频剪辑工作流（调色和音效并行）',
            tasks_config=tasks_config,
            parallel=True,  # 并行执行
            max_parallel=3
        )
        
        return self.workflow_id
        
    def create_ai_narration_workflow(self) -> str:
        """创建AI解说视频工作流"""
        tasks_config = [
            {
                'name': 'analyze_video',
                'task_type': 'video_analysis',
                'params': {},
                'priority': 0,
                'required_capabilities': [AgentCapability.VISION_ANALYSIS],
                'dependencies': [],
                'timeout_seconds': 180,
                'max_retries': 1
            },
            {
                'name': 'generate_script',
                'task_type': 'script_writing',
                'params': {'style': 'narration'},
                'priority': 0,
                'required_capabilities': [AgentCapability.SCRIPT_WRITING],
                'dependencies': [
                    {'task_id': 'analyze_video', 'required_state': 'COMPLETED'}
                ],
                'timeout_seconds': 120,
                'max_retries': 1
            },
            {
                'name': 'editor_cut',
                'task_type': 'editing',
                'params': {'mode': 'narration'},
                'priority': 1,
                'required_capabilities': [AgentCapability.EDITING],
                'dependencies': [
                    {'task_id': 'generate_script', 'required_state': 'COMPLETED'}
                ],
                'timeout_seconds': 300,
                'max_retries': 1
            },
            {
                'name': 'generate_voice',
                'task_type': 'tts',
                'params': {},
                'priority': 1,
                'required_capabilities': [AgentCapability.TTS],
                'dependencies': [
                    {'task_id': 'generate_script', 'required_state': 'COMPLETED'}
                ],
                'timeout_seconds': 180,
                'max_retries': 2
            },
            {
                'name': 'add_subtitles',
                'task_type': 'subtitle',
                'params': {},
                'priority': 2,
                'dependencies': [
                    {'task_id': 'editor_cut', 'required_state': 'COMPLETED'},
                    {'task_id': 'generate_voice', 'required_state': 'COMPLETED'}
                ],
                'timeout_seconds': 120,
                'max_retries': 1
            },
            {
                'name': 'final_export',
                'task_type': 'export',
                'params': {'format': 'mp4'},
                'priority': 0,
                'dependencies': [
                    {'task_id': 'add_subtitles', 'required_state': 'COMPLETED'}
                ],
                'timeout_seconds': 300,
                'max_retries': 2
            }
        ]
        
        self.workflow_id = self.scheduler.create_workflow(
            name='ai_narration_video',
            description='AI解说视频工作流',
            tasks_config=tasks_config,
            parallel=True,
            max_parallel=3
        )
        
        return self.workflow_id
        
    async def start(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        style: str = 'standard'
    ) -> str:
        """
        启动工作流
        
        Args:
            video_path: 输入视频路径
            output_path: 输出路径
            style: 工作流类型 ('standard', 'parallel', 'narration')
            
        Returns:
            instance_id: 工作流实例ID
        """
        # 选择工作流
        if style == 'parallel':
            workflow_id = self.create_parallel_workflow()
        elif style == 'narration':
            workflow_id = self.create_ai_narration_workflow()
        else:
            workflow_id = self.create_standard_workflow()
            
        # 全局参数
        global_params = {
            'video_path': video_path,
            'output_path': output_path or f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
            'created_at': datetime.now().isoformat()
        }
        
        # 启动工作流
        instance_id = await self.scheduler.start_workflow(workflow_id, global_params)
        
        return instance_id
        
    def get_progress(self, instance_id: str) -> Dict[str, Any]:
        """获取工作流进度"""
        return self.scheduler.get_workflow_status(instance_id)


# 便捷函数
async def create_video_editing_workflow(
    scheduler: TaskScheduler,
    video_path: str,
    output_path: Optional[str] = None,
    style: str = 'standard'
) -> str:
    """
    创建并启动视频剪辑工作流
    
    Args:
        scheduler: 任务调度器
        video_path: 输入视频路径
        output_path: 输出路径
        style: 工作流类型
        
    Returns:
        instance_id: 工作流实例ID
    """
    workflow = VideoEditingWorkflow(scheduler)
    return await workflow.start(video_path, output_path, style)
