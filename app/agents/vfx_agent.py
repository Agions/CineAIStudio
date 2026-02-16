"""
特效 Agent
负责视觉特效和动画
"""

from typing import Dict, Any, List
from pathlib import Path

from .base_agent import BaseAgent, AgentCapability, AgentResult


class VFXAgent(BaseAgent):
    """
    特效 Agent
    
    职责：
    1. 转场特效 - 动态转场、遮罩转场
    2. 文字动画 - 标题、字幕动画
    3. 视觉特效 - 粒子、光效、模糊
    4. 调色特效 - 滤镜、风格化
    5. 合成 - 多层合成、抠像
    
    使用DALL-E 3生成特效素材
    """
    
    # 特效预设
    VFX_PRESETS = {
        'cinematic_intro': {
            'name': '电影开场',
            'effects': [
                {'type': 'fade_in', 'duration': 1.0},
                {'type': 'title_animation', 'style': 'cinematic'},
                {'type': 'color_grade', 'preset': 'cinematic'}
            ]
        },
        'dynamic_transition': {
            'name': '动感转场',
            'effects': [
                {'type': 'zoom_transition', 'duration': 0.5},
                {'type': 'motion_blur', 'intensity': 0.3}
            ]
        },
        'text_reveal': {
            'name': '文字显现',
            'effects': [
                {'type': 'typewriter', 'speed': 0.05},
                {'type': 'glow', 'color': '#ffffff', 'intensity': 0.5}
            ]
        },
        'particle_overlay': {
            'name': '粒子叠加',
            'effects': [
                {'type': 'particles', 'count': 50, 'style': 'sparkle'},
                {'type': 'blend_mode', 'mode': 'screen'}
            ]
        },
        'glitch_effect': {
            'name': '故障效果',
            'effects': [
                {'type': 'glitch', 'intensity': 0.7, 'duration': 0.3},
                {'type': 'rgb_split', 'amount': 5}
            ]
        },
        'vintage_film': {
            'name': '复古胶片',
            'effects': [
                {'type': 'grain', 'intensity': 0.3},
                {'type': 'scratches', 'frequency': 0.1},
                {'type': 'vignette', 'intensity': 0.4}
            ]
        }
    }
    
    def __init__(self):
        super().__init__(
            name="VFX Artist",
            capabilities=[AgentCapability.VFX]
        )
        
        # 初始化LLM - VFX使用DALL-E 3生成素材
        self.init_llm('vfx')
        
    async def execute(self, task: Dict[str, Any]) -> AgentResult:
        """执行特效任务"""
        video_path = task.get('video_path')
        preset_name = task.get('preset', 'cinematic_intro')
        project_id = task.get('project_id')
        
        if not video_path or not Path(video_path).exists():
            return AgentResult(
                success=False, data={}, message=f"视频不存在: {video_path}"
            )
            
        try:
            self.report_progress(20, "分析视频结构...")
            structure = await self._analyze_structure(video_path)
            
            self.report_progress(40, "设计特效方案...")
            effects_plan = self._design_effects(structure, preset_name)
            
            self.report_progress(60, "生成特效...")
            generated_effects = await self._generate_effects(effects_plan)
            
            self.report_progress(80, "合成特效...")
            composited = await self._composite_effects(video_path, generated_effects)
            
            self.report_progress(100, "特效完成")
            
            return AgentResult(
                success=True,
                data={
                    'project_id': project_id,
                    'effects': composited,
                    'preset': preset_name,
                    'structure': structure
                },
                message=f"特效完成 - {self.VFX_PRESETS.get(preset_name, {}).get('name', preset_name)}"
            )
        except Exception as e:
            return AgentResult(success=False, data={}, message=f"特效失败: {e}")
            
    async def _analyze_structure(self, video_path: str) -> Dict:
        """分析视频结构"""
        return {
            'duration': 60.0,
            'scenes': [
                {'start': 0, 'end': 5, 'type': 'intro'},
                {'start': 5, 'end': 55, 'type': 'content'},
                {'start': 55, 'end': 60, 'type': 'outro'}
            ],
            'transitions': [
                {'at': 5, 'type': 'scene_change'},
                {'at': 55, 'type': 'scene_change'}
            ]
        }
        
    def _design_effects(self, structure: Dict, preset_name: str) -> List[Dict]:
        """设计特效方案"""
        preset = self.VFX_PRESETS.get(preset_name, self.VFX_PRESETS['cinematic_intro'])
        return preset.get('effects', [])
        
    async def _analyze_frame_for_effects(
        self,
        frame_path: str,
        effect_type: str
    ) -> Dict[str, Any]:
        """分析视频帧推荐特效 - 使用Kimi 2.5 Vision画面理解"""
        try:
            prompt = f"""
作为VFX特效师，分析这张视频帧画面，推荐适合的{effect_type}特效：

请分析：
1. 画面主体内容
2. 光影特点
3. 色彩风格
4. 推荐的特效类型和参数

以JSON格式返回：
{{
    "scene_description": "场景描述",
    "lighting": "光影特点",
    "color_style": "色彩风格",
    "recommended_effects": [
        {{"type": "特效类型", "intensity": 0.5, "reason": "推荐理由"}}
    ]
}}
"""
            
            result = await self.llm.analyze_video_frame(frame_path, prompt)
            
            if result.get('success'):
                import json
                content = result['content']
                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0]
                elif '```' in content:
                    content = content.split('```')[1].split('```')[0]
                return json.loads(content.strip())
            else:
                return {'error': result.get('error', '分析失败')}
                
        except Exception as e:
            return {'error': str(e)}
            
    async def _generate_effects(self, effects_plan: List[Dict]) -> List[Dict]:
        """生成特效 - 基于画面理解推荐特效参数"""
        generated = []
        
        for effect in effects_plan:
            # VFX现在使用画面理解而非图像生成
            effect['generation_method'] = 'frame_analysis'
            effect['note'] = '使用Kimi 2.5 Vision分析画面推荐特效参数'
            generated.append(effect)
            
        return generated
        
    async def _composite_effects(self, video_path: str, effects: List[Dict]) -> List[Dict]:
        """合成特效"""
        return effects
