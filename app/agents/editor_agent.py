"""
剪辑 Agent
负责视频剪辑工作
"""

from typing import Dict, Any, List
from pathlib import Path

from .base_agent import BaseAgent, AgentCapability, AgentResult


class EditorAgent(BaseAgent):
    """
    剪辑 Agent
    
    职责：
    1. 视频粗剪 - 去除废片，保留精华
    2. 视频精剪 - 节奏控制，转场处理
    3. 多轨道编辑 - 视频、音频、字幕轨道
    4. 时间线管理 - 片段排序，时长调整
    """
    
    def __init__(self):
        super().__init__(
            name="Editor",
            capabilities=[AgentCapability.EDITING]
        )
        
        # 初始化LLM - Editor使用Claude进行长上下文分析
        self.init_llm('editor')
        
    async def execute(self, task: Dict[str, Any]) -> AgentResult:
        """
        执行剪辑任务
        
        Args:
            task: {
                'type': 'editing',
                'video_path': str,
                'project_id': str,
                'requirements': dict
            }
        """
        video_path = task.get('video_path')
        project_id = task.get('project_id')
        
        if not video_path or not Path(video_path).exists():
            return AgentResult(
                success=False,
                data={},
                message=f"视频文件不存在: {video_path}"
            )
            
        try:
            self.report_progress(10, "分析视频内容...")
            
            # 1. 视频分析
            analysis = await self._analyze_video(video_path)
            
            self.report_progress(30, "进行粗剪...")
            
            # 2. 粗剪
            rough_cut = await self._rough_cut(video_path, analysis)
            
            self.report_progress(60, "进行精剪...")
            
            # 3. 精剪
            fine_cut = await self._fine_cut(rough_cut)
            
            self.report_progress(80, "添加转场效果...")
            
            # 4. 添加转场
            transitions = await self._add_transitions(fine_cut)
            
            self.report_progress(100, "剪辑完成")
            
            return AgentResult(
                success=True,
                data={
                    'project_id': project_id,
                    'video_segments': fine_cut.get('segments', []),
                    'transitions': transitions,
                    'duration': fine_cut.get('duration', 0),
                    'analysis': analysis
                },
                message="剪辑任务完成"
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                data={},
                message=f"剪辑失败: {str(e)}"
            )
            
    async def _analyze_video(self, video_path: str) -> Dict[str, Any]:
        """分析视频内容 - 结合LLM智能分析"""
        # 基础分析
        from ..services.ai.video_content_analyzer import VideoContentAnalyzer
        
        analyzer = VideoContentAnalyzer()
        keyframes = analyzer.extract_keyframes(video_path)
        scenes = analyzer.analyze_scenes(video_path)
        
        # 使用LLM进行智能剪辑建议
        scene_descriptions = []
        for i, scene in enumerate(scenes[:10]):  # 前10个场景
            scene_descriptions.append(
                f"场景{i+1}: {scene.get('start', 0):.1f}s-{scene.get('end', 0):.1f}s, "
                f"质量{scene.get('quality', 0.8):.2f}"
            )
        
        prompt = f"""
作为专业剪辑师，分析以下视频场景：

视频信息：
- 路径: {video_path}
- 时长: {analyzer.get_duration(video_path):.1f}秒
- 分辨率: {analyzer.get_resolution(video_path)}

场景列表：
{chr(10).join(scene_descriptions)}

请提供：
1. 哪些场景应该保留（给出场景编号）
2. 建议的剪辑节奏
3. 推荐的转场类型
4. 潜在问题

以JSON格式返回：
{{
    "keep_scenes": [1, 3, 5],
    "pacing": "fast/medium/slow",
    "transition_style": "cut/fade/dissolve",
    "issues": ["问题描述"]
}}
"""
        
        try:
            llm_result = await self.call_llm(
                prompt=prompt,
                system_prompt="你是专业视频剪辑师，擅长分析视频结构并给出剪辑建议。只返回JSON。"
            )
            
            llm_suggestions = {}
            if llm_result.get('success'):
                import json
                content = llm_result['content']
                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0]
                elif '```' in content:
                    content = content.split('```')[1].split('```')[0]
                llm_suggestions = json.loads(content.strip())
                
        except Exception:
            llm_suggestions = {}
            
        return {
            'keyframes': keyframes,
            'scenes': scenes,
            'duration': analyzer.get_duration(video_path),
            'resolution': analyzer.get_resolution(video_path),
            'llm_suggestions': llm_suggestions
        }
        
    async def _rough_cut(
        self,
        video_path: str,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """粗剪 - 去除废片"""
        scenes = analysis.get('scenes', [])
        
        segments = []
        for i, scene in enumerate(scenes):
            # 过滤掉过短或质量差的片段
            if scene.get('duration', 0) < 1.0:
                continue
                
            segments.append({
                'id': f'segment_{i}',
                'start': scene.get('start', 0),
                'end': scene.get('end', 0),
                'duration': scene.get('duration', 0),
                'type': 'video',
                'quality_score': scene.get('quality', 0.8)
            })
            
        return {
            'segments': segments,
            'duration': sum(s['duration'] for s in segments)
        }
        
    async def _fine_cut(self, rough_cut: Dict[str, Any]) -> Dict[str, Any]:
        """精剪 - 节奏控制"""
        segments = rough_cut.get('segments', [])
        
        # 节奏优化
        optimized_segments = []
        for segment in segments:
            # 调整片段时长，保持节奏感
            duration = segment['duration']
            
            # 理想时长：3-10秒
            if duration > 10:
                # 长片段可能需要拆分
                segment['suggested_split'] = True
                
            optimized_segments.append(segment)
            
        return {
            'segments': optimized_segments,
            'duration': rough_cut.get('duration', 0)
        }
        
    async def _add_transitions(
        self,
        fine_cut: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """添加转场效果"""
        segments = fine_cut.get('segments', [])
        transitions = []
        
        transition_types = ['cut', 'fade', 'dissolve', 'slide']
        
        for i in range(len(segments) - 1):
            transitions.append({
                'from_segment': segments[i]['id'],
                'to_segment': segments[i + 1]['id'],
                'type': transition_types[i % len(transition_types)],
                'duration': 0.5
            })
            
        return transitions
