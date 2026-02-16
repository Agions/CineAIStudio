"""
音效 Agent
负责音频处理和音效设计
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import numpy as np

from .base_agent import BaseAgent, AgentCapability, AgentResult


class SoundAgent(BaseAgent):
    """
    音效 Agent
    
    职责：
    1. 音频清理 - 降噪、去混响
    2. 音量平衡 - 自动增益、压缩
    3. 音效设计 - 添加环境音、音效
    4. 混音 - 多轨道混音
    5. 音乐匹配 - BGM自动匹配
    """
    
    # 音效预设
    SOUND_PRESETS = {
        'dialogue': {
            'name': '对话增强',
            'noise_reduction': True,
            'compression': 3.0,
            'eq': [
                {'freq': 100, 'gain': -3, 'q': 1.0},   # 低频削减
                {'freq': 3000, 'gain': 2, 'q': 1.5},   # 清晰度提升
                {'freq': 8000, 'gain': 1, 'q': 2.0},   # 空气感
            ]
        },
        'cinematic': {
            'name': '电影感',
            'compression': 4.0,
            'eq': [
                {'freq': 80, 'gain': 2, 'q': 0.7},     # 低频增强
                {'freq': 400, 'gain': -2, 'q': 1.2},    # 中频削减
                {'freq': 3000, 'gain': 3, 'q': 1.5},   # 高频提升
            ],
            'reverb': {'room_size': 0.3, 'damping': 0.5}
        },
        'podcast': {
            'name': '播客风格',
            'noise_reduction': True,
            'compression': 5.0,
            'eq': [
                {'freq': 150, 'gain': -4, 'q': 1.0},
                {'freq': 2500, 'gain': 3, 'q': 1.2},
            ],
            'limiter': {'threshold': -1.0, 'release': 100}
        },
        'music_video': {
            'name': '音乐视频',
            'compression': 2.0,
            'eq': [
                {'freq': 60, 'gain': 3, 'q': 0.8},
                {'freq': 12000, 'gain': 2, 'q': 2.0},
            ],
            'stereo_widening': 1.2
        }
    }
    
    def __init__(self):
        super().__init__(
            name="Sound Designer",
            capabilities=[AgentCapability.SOUND_DESIGN]
        )
        
    async def execute(self, task: Dict[str, Any]) -> AgentResult:
        """
        执行音效任务
        
        Args:
            task: {
                'type': 'sound_design',
                'video_path': str,
                'audio_tracks': List[dict],
                'preset': str,
                'bgm_path': str,  # optional
                'project_id': str
            }
        """
        video_path = task.get('video_path')
        audio_tracks = task.get('audio_tracks', [])
        preset_name = task.get('preset', 'dialogue')
        project_id = task.get('project_id')
        
        if not video_path or not Path(video_path).exists():
            return AgentResult(
                success=False,
                data={},
                message=f"视频文件不存在: {video_path}"
            )
            
        try:
            self.report_progress(10, "分析音频...")
            
            # 1. 音频分析
            audio_analysis = await self._analyze_audio(video_path, audio_tracks)
            
            self.report_progress(25, "音频清理...")
            
            # 2. 音频清理
            cleaned_audio = await self._clean_audio(audio_analysis)
            
            self.report_progress(40, "音量平衡...")
            
            # 3. 音量平衡
            balanced_audio = await self._balance_audio(cleaned_audio, preset_name)
            
            self.report_progress(55, "EQ调整...")
            
            # 4. EQ调整
            eq_audio = await self._apply_eq(balanced_audio, preset_name)
            
            self.report_progress(70, "添加音效...")
            
            # 5. 添加音效
            enhanced_audio = await self._add_effects(eq_audio, preset_name)
            
            self.report_progress(85, "混音...")
            
            # 6. 混音
            mixed_audio = await self._mix_audio(enhanced_audio, task.get('bgm_path'))
            
            self.report_progress(100, "音效处理完成")
            
            return AgentResult(
                success=True,
                data={
                    'project_id': project_id,
                    'audio_tracks': mixed_audio,
                    'preset_used': preset_name,
                    'analysis': audio_analysis,
                    'output_path': mixed_audio.get('output_path', '')
                },
                message=f"音效处理完成 - 预设: {self.SOUND_PRESETS.get(preset_name, {}).get('name', preset_name)}"
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                data={},
                message=f"音效处理失败: {str(e)}"
            )
            
    async def _analyze_audio(
        self,
        video_path: str,
        audio_tracks: List[Dict]
    ) -> Dict[str, Any]:
        """分析音频"""
        analysis = {
            'video_path': video_path,
            'tracks': [],
            'duration': 0,
            'sample_rate': 48000,
            'channels': 2,
            'recommendations': []
        }
        
        # 分析每个音轨
        for track in audio_tracks:
            track_analysis = {
                'id': track.get('id'),
                'type': track.get('type', 'unknown'),
                'duration': track.get('duration', 0),
                'volume_stats': {
                    'peak': -6.0,
                    'rms': -20.0,
                    'dynamic_range': 14.0
                },
                'issues': []
            }
            
            # 检测问题
            if track_analysis['volume_stats']['peak'] > -3.0:
                track_analysis['issues'].append('clipping')
                analysis['recommendations'].append(f"轨道 {track['id']}: 存在削波，建议降低音量")
                
            if track_analysis['volume_stats']['rms'] < -30.0:
                track_analysis['issues'].append('too_quiet')
                analysis['recommendations'].append(f"轨道 {track['id']}: 音量过低，建议提升")
                
            analysis['tracks'].append(track_analysis)
            
        return analysis
        
    async def _clean_audio(self, audio_analysis: Dict) -> Dict:
        """音频清理"""
        cleaned = audio_analysis.copy()
        
        for track in cleaned['tracks']:
            # 降噪
            if 'noise' in track.get('issues', []):
                track['processing'].append('noise_reduction')
                
            # 去混响
            if 'reverb' in track.get('issues', []):
                track['processing'].append('de_reverb')
                
            # 去爆音
            if 'plosives' in track.get('issues', []):
                track['processing'].append('de_plosive')
                
        return cleaned
        
    async def _balance_audio(
        self,
        audio_data: Dict,
        preset_name: str
    ) -> Dict:
        """音量平衡"""
        preset = self.SOUND_PRESETS.get(preset_name, self.SOUND_PRESETS['dialogue'])
        
        for track in audio_data['tracks']:
            # 自动增益
            target_rms = -20.0
            current_rms = track['volume_stats']['rms']
            gain_adjustment = target_rms - current_rms
            
            track['gain'] = gain_adjustment
            
            # 压缩
            if 'compression' in preset:
                track['compression'] = {
                    'ratio': preset['compression'],
                    'threshold': -18.0,
                    'attack': 10,
                    'release': 100
                }
                
        return audio_data
        
    async def _apply_eq(self, audio_data: Dict, preset_name: str) -> Dict:
        """应用EQ"""
        preset = self.SOUND_PRESETS.get(preset_name, self.SOUND_PRESETS['dialogue'])
        
        eq_settings = preset.get('eq', [])
        
        for track in audio_data['tracks']:
            track['eq'] = eq_settings
            
        return audio_data
        
    async def _add_effects(self, audio_data: Dict, preset_name: str) -> Dict:
        """添加音效"""
        preset = self.SOUND_PRESETS.get(preset_name, self.SOUND_PRESETS['dialogue'])
        
        for track in audio_data['tracks']:
            track['effects'] = []
            
            # 混响
            if 'reverb' in preset:
                track['effects'].append({
                    'type': 'reverb',
                    'params': preset['reverb']
                })
                
            # 限制器
            if 'limiter' in preset:
                track['effects'].append({
                    'type': 'limiter',
                    'params': preset['limiter']
                })
                
            # 立体声扩展
            if 'stereo_widening' in preset:
                track['effects'].append({
                    'type': 'stereo_widening',
                    'width': preset['stereo_widening']
                })
                
        return audio_data
        
    async def _mix_audio(
        self,
        audio_data: Dict,
        bgm_path: Optional[str]
    ) -> Dict:
        """混音"""
        # 设置各轨道音量
        track_volumes = {
            'dialogue': 0.0,      # 0 dB
            'sfx': -10.0,         # -10 dB
            'bgm': -18.0,         # -18 dB
            'music': -12.0        # -12 dB
        }
        
        for track in audio_data['tracks']:
            track_type = track.get('type', 'unknown')
            track['final_volume'] = track_volumes.get(track_type, -6.0)
            
        # 添加BGM
        if bgm_path and Path(bgm_path).exists():
            audio_data['tracks'].append({
                'id': 'bgm',
                'type': 'bgm',
                'path': bgm_path,
                'final_volume': track_volumes['bgm'],
                'ducking': True  # 自动闪避
            })
            
        # 计算输出路径
        output_dir = Path.home() / "CineFlow" / "Audio"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{audio_data.get('project_id', 'temp')}_mixed.wav"
        
        audio_data['output_path'] = str(output_path)
        
        return audio_data
        
    def get_available_presets(self) -> List[Dict[str, str]]:
        """获取可用预设"""
        return [
            {'id': key, 'name': value['name']}
            for key, value in self.SOUND_PRESETS.items()
        ]
        
    def analyze_loudness(self, audio_path: str) -> Dict[str, float]:
        """分析响度"""
        # 模拟响度分析
        return {
            'integrated_lufs': -16.0,
            'short_term_lufs': -14.0,
            'momentary_lufs': -12.0,
            'lra': 8.0,  # 响度范围
            'true_peak': -1.0
        }
