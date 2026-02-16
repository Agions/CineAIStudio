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
    
    使用Kimi K2.5:
    - 画面理解: 分析视频帧内容
    - 特效生成: 基于理解生成特效参数和素材描述
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
        
        # 初始化LLM - VFX使用Kimi K2.5进行画面理解和特效生成
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
            
            # 提取关键帧用于画面理解
            self.report_progress(50, "提取关键帧...")
            video_frames = await self._extract_keyframes(video_path, structure)
            
            self.report_progress(60, "画面理解+生成特效...")
            generated_effects = await self._generate_effects(effects_plan, video_frames)
            
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
        
    async def _extract_keyframes(self, video_path: str, structure: Dict) -> List[str]:
        """
        提取视频关键帧用于画面理解
        
        从每个场景中提取代表性帧，用于Kimi K2.5分析
        """
        keyframes = []
        scenes = structure.get('scenes', [])
        
        for scene in scenes:
            # 提取场景中间时刻的帧
            start = scene.get('start', 0)
            end = scene.get('end', 0)
            mid_time = (start + end) / 2
            
            # 模拟帧路径 (实际应调用ffmpeg提取)
            frame_path = f"/tmp/frames/{Path(video_path).stem}_frame_{int(mid_time)}.jpg"
            keyframes.append(frame_path)
            
        return keyframes
        
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
            
    async def _generate_effects(
        self,
        effects_plan: List[Dict],
        video_frames: List[str] = None
    ) -> List[Dict]:
        """
        生成特效 - 结合画面理解和AI生成
        
        1. 使用Kimi K2.5理解视频帧画面
        2. 基于理解生成特效参数和素材描述
        3. 生成特效配置文件
        """
        generated = []
        
        for i, effect in enumerate(effects_plan):
            # 如果有视频帧，先进行画面理解
            if video_frames and i < len(video_frames):
                frame_path = video_frames[i]
                
                # 1. 画面理解
                analysis = await self._analyze_frame_for_effects(
                    frame_path,
                    effect.get('type', 'particles')
                )
                
                # 2. 基于理解生成特效参数
                effect['frame_analysis'] = analysis
                effect['generated_params'] = await self._generate_effect_params(
                    effect,
                    analysis
                )
                
                # 3. 生成特效素材描述 (用于后续渲染)
                effect['asset_description'] = await self._generate_asset_description(
                    effect,
                    analysis
                )
                
                effect['generation_method'] = 'ai_understanding'
            else:
                # 无画面时生成默认参数
                effect['generated_params'] = self._get_default_params(effect)
                effect['generation_method'] = 'default'
            
            generated.append(effect)
            
        return generated
        
    async def _generate_effect_params(
        self,
        effect: Dict,
        frame_analysis: Dict
    ) -> Dict[str, Any]:
        """基于画面理解生成特效参数"""
        effect_type = effect.get('type', 'particles')
        
        # 根据画面分析调整特效参数
        params = {
            'type': effect_type,
            'intensity': 0.5,
            'blend_mode': 'screen',
            'duration': effect.get('duration', 1.0)
        }
        
        # 根据画面光影调整
        lighting = frame_analysis.get('lighting', '')
        if '暗' in lighting or 'dark' in lighting.lower():
            params['intensity'] = 0.7
            params['glow'] = True
        elif '亮' in lighting or 'bright' in lighting.lower():
            params['intensity'] = 0.4
            
        # 根据色彩风格调整
        color_style = frame_analysis.get('color_style', '')
        if '暖' in color_style or 'warm' in color_style.lower():
            params['color_temperature'] = 'warm'
            params['tint'] = '#ffaa44'
        elif '冷' in color_style or 'cool' in color_style.lower():
            params['color_temperature'] = 'cool'
            params['tint'] = '#44aaff'
            
        return params
        
    async def _generate_asset_description(
        self,
        effect: Dict,
        frame_analysis: Dict
    ) -> str:
        """生成特效素材描述 (用于渲染引擎)"""
        effect_type = effect.get('type', 'particles')
        scene = frame_analysis.get('scene_description', '场景')
        
        descriptions = {
            'particles': f"{scene}中的金色粒子效果，与画面光影融合",
            'light_leak': f"{scene}边缘的自然光晕，模拟镜头漏光",
            'lens_flare': f"{scene}中的镜头光斑，增强视觉冲击力",
            'glow': f"{scene}主体的柔和发光效果",
            'bokeh': f"{scene}背景的散景光斑，突出主体"
        }
        
        return descriptions.get(effect_type, f"{scene}的特效素材")
        
    def _get_default_params(self, effect: Dict) -> Dict[str, Any]:
        """获取默认特效参数"""
        return {
            'type': effect.get('type', 'particles'),
            'intensity': 0.5,
            'blend_mode': 'screen',
            'duration': effect.get('duration', 1.0),
            'color_temperature': 'neutral',
            'note': '默认参数，未进行画面分析'
        }
        
    async def _composite_effects(self, video_path: str, effects: List[Dict]) -> List[Dict]:
        """合成特效到视频"""
        composited = []
        
        for effect in effects:
            # 构建特效合成配置
            composite_config = {
                'effect_type': effect.get('type'),
                'params': effect.get('generated_params', {}),
                'asset_description': effect.get('asset_description', ''),
                'frame_analysis': effect.get('frame_analysis', {}),
                'timestamp': effect.get('timestamp', 0),
                'duration': effect.get('duration', 1.0)
            }
            
            # 模拟合成过程
            composite_config['status'] = 'ready_to_render'
            composite_config['render_engine'] = 'vfx_pipeline'
            
            composited.append(composite_config)
            
        return composited
