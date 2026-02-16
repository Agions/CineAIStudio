"""
Agent 增强版解说视频制作器
使用多Agent协同完成解说视频制作
"""

import os
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass, field

from ...agents.agent_manager import AgentManager
from ...agents.director_agent import DirectorAgent, EditingPlan
from ...agents.editor_agent import EditorAgent
from ...agents.colorist_agent import ColoristAgent
from ...agents.sound_agent import SoundAgent
from ...agents.vfx_agent import VFXAgent
from ...agents.reviewer_agent import ReviewerAgent
from ...agents.base_agent import AgentResult

from .commentary_maker import CommentaryMaker, CommentaryProject, CommentaryStyle


@dataclass
class AgentCommentaryConfig:
    """Agent解说配置"""
    # 启用哪些Agent
    use_editor: bool = True
    use_colorist: bool = True
    use_sound: bool = True
    use_vfx: bool = False
    use_reviewer: bool = True
    
    # 各Agent配置
    color_style: str = "cinematic"
    sound_preset: str = "dialogue"
    vfx_preset: str = "cinematic_intro"
    
    # 质量要求
    quality_threshold: int = 80


class AgentCommentaryMaker:
    """
    Agent 增强版解说视频制作器
    
    使用多Agent协同完成专业级解说视频：
    1. Director - 制定剪辑计划
    2. Editor - 视频剪辑
    3. Colorist - 调色
    4. Sound - 音效处理
    5. VFX - 特效（可选）
    6. Reviewer - 质量审核
    
    使用示例:
        maker = AgentCommentaryMaker()
        
        # 创建项目
        project = maker.create_project(
            source_video="input.mp4",
            topic="解析这部电影",
            style=CommentaryStyle.STORYTELLING
        )
        
        # 使用Agent协同制作
        result = await maker.create_with_agents(project)
    """
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        voice_provider: str = "edge",
        config: AgentCommentaryConfig = None
    ):
        self.config = config or AgentCommentaryConfig()
        
        # 基础制作器
        self.base_maker = CommentaryMaker(
            openai_api_key=openai_api_key,
            voice_provider=voice_provider
        )
        
        # Agent管理器
        self.agent_manager = AgentManager()
        
        # 初始化Agent
        self._init_agents()
        
        # 进度回调
        self._progress_callback: Optional[Callable[[str, float], None]] = None
        
    def _init_agents(self):
        """初始化所有Agent"""
        # Director
        self.director = DirectorAgent()
        self.agent_manager.register_agent(self.director)
        
        # Editor
        if self.config.use_editor:
            self.editor = EditorAgent()
            self.agent_manager.register_agent(self.editor)
            
        # Colorist
        if self.config.use_colorist:
            self.colorist = ColoristAgent()
            self.agent_manager.register_agent(self.colorist)
            
        # Sound
        if self.config.use_sound:
            self.sound = SoundAgent()
            self.agent_manager.register_agent(self.sound)
            
        # VFX
        if self.config.use_vfx:
            self.vfx = VFXAgent()
            self.agent_manager.register_agent(self.vfx)
            
        # Reviewer
        if self.config.use_reviewer:
            self.reviewer = ReviewerAgent()
            self.agent_manager.register_agent(self.reviewer)
            
    def set_progress_callback(self, callback: Callable[[str, float], None]):
        """设置进度回调"""
        self._progress_callback = callback
        
        # 也设置给base maker
        self.base_maker.set_progress_callback(callback)
        
    def _report_progress(self, stage: str, progress: float):
        """报告进度"""
        if self._progress_callback:
            self._progress_callback(stage, progress)
            
    async def create_with_agents(
        self,
        project: CommentaryProject
    ) -> Dict[str, Any]:
        """
        使用Agent协同创建解说视频
        
        工作流程:
        1. 基础制作（文案+配音+字幕）
        2. Agent协同后期
        3. 质量审核
        4. 导出
        """
        self._report_progress("初始化Agent", 0)
        
        # 1. 基础制作
        self._report_progress("生成解说内容", 10)
        base_result = await self._create_base_content(project)
        
        if not base_result['success']:
            return base_result
            
        # 2. Agent协同后期
        self._report_progress("Agent协同处理", 30)
        agent_result = await self._agent_collaboration(project)
        
        if not agent_result['success']:
            return agent_result
            
        # 3. 质量审核
        if self.config.use_reviewer:
            self._report_progress("质量审核", 80)
            review_result = await self._quality_review(project)
            
            if not review_result['passed']:
                # 审核未通过，返回问题
                return {
                    'success': False,
                    'stage': 'review',
                    'issues': review_result.get('issues', []),
                    'message': '质量审核未通过'
                }
                
        # 4. 导出
        self._report_progress("导出视频", 90)
        export_result = await self._export_project(project)
        
        self._report_progress("完成", 100)
        
        return {
            'success': True,
            'project': project,
            'base_result': base_result,
            'agent_result': agent_result,
            'export_result': export_result,
            'message': 'Agent协同制作完成'
        }
        
    async def _create_base_content(
        self,
        project: CommentaryProject
    ) -> Dict[str, Any]:
        """创建基础内容"""
        try:
            # 生成文案
            self.base_maker.generate_script(project)
            
            # 生成配音
            self.base_maker.generate_voice(project)
            
            # 生成字幕
            self.base_maker.generate_captions(project)
            
            return {
                'success': True,
                'message': '基础内容创建完成'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'基础内容创建失败: {e}'
            }
            
    async def _agent_collaboration(
        self,
        project: CommentaryProject
    ) -> Dict[str, Any]:
        """Agent协同处理"""
        # 创建项目计划
        plan = EditingPlan(
            project_id=project.id or "commentary_001",
            project_name=project.name,
            video_path=project.source_video,
            target_duration=project.total_duration,
            style=self._map_style(project.style)
        )
        
        # 创建项目任务
        task = {
            'type': 'create_project',
            'project': plan,
            'agents': list(self.agent_manager.agents.keys())
        }
        
        # 启动Agent管理器
        self.agent_manager.start()
        
        # 执行任务
        result = await self.director.run(task)
        
        return {
            'success': result.success,
            'data': result.data,
            'message': result.message
        }
        
    def _map_style(self, style: CommentaryStyle) -> str:
        """映射解说风格到剪辑风格"""
        style_map = {
            CommentaryStyle.EXPLAINER: 'professional',
            CommentaryStyle.REVIEW: 'cinematic',
            CommentaryStyle.STORYTELLING: 'cinematic',
            CommentaryStyle.EDUCATIONAL: 'professional',
            CommentaryStyle.NEWS: 'professional'
        }
        return style_map.get(style, 'professional')
        
    async def _quality_review(
        self,
        project: CommentaryProject
    ) -> Dict[str, Any]:
        """质量审核"""
        # 构建输出视频路径
        output_path = Path(project.output_dir) / f"{project.id}_final.mp4"
        
        task = {
            'type': 'review',
            'video_path': str(output_path),
            'project_id': project.id,
            'requirements': {
                'min_score': self.config.quality_threshold
            }
        }
        
        result = await self.reviewer.run(task)
        
        return {
            'passed': result.success,
            'score': result.data.get('total_score', 0),
            'issues': result.data.get('issues', []),
            'details': result.data
        }
        
    async def _export_project(
        self,
        project: CommentaryProject
    ) -> Dict[str, Any]:
        """导出项目"""
        try:
            draft_path = self.base_maker.export_to_jianying(
                project,
                project.output_dir
            )
            
            return {
                'success': True,
                'draft_path': draft_path,
                'message': '导出完成'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'导出失败: {e}'
            }
            
    def get_agent_manager(self) -> AgentManager:
        """获取Agent管理器（用于UI绑定）"""
        return self.agent_manager
        
    def get_available_color_styles(self) -> list:
        """获取可用调色风格"""
        if hasattr(self, 'colorist'):
            return self.colorist.get_available_styles()
        return []
        
    def get_available_sound_presets(self) -> list:
        """获取可用音效预设"""
        if hasattr(self, 'sound'):
            return self.sound.get_available_presets()
        return []
