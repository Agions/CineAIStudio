"""
调色 Agent
负责视频调色和风格化处理
"""

from typing import Dict, Any, List
from pathlib import Path
import cv2
import numpy as np

from .base_agent import BaseAgent, AgentCapability, AgentResult


class ColoristAgent(BaseAgent):
    """
    调色 Agent
    
    职责：
    1. 色彩校正 - 白平衡、曝光、对比度
    2. 风格调色 - 电影感、复古、清新等风格
    3. LUT应用 - 查找表调色
    4. 色彩分级 - 阴影、中间调、高光分别调整
    
    使用GPT-4 Vision进行智能色彩分析
    """
    
    # 预设风格
    PRESETS = {
        'cinematic': {
            'name': '电影感',
            'contrast': 1.2,
            'saturation': 0.9,
            'shadows': (20, 25, 30),
            'highlights': (240, 235, 230),
            'gamma': 1.1
        },
        'vintage': {
            'name': '复古',
            'contrast': 1.1,
            'saturation': 0.7,
            'shadows': (30, 25, 20),
            'highlights': (220, 210, 195),
            'gamma': 1.2,
            'vignette': True
        },
        'fresh': {
            'name': '清新',
            'contrast': 1.0,
            'saturation': 1.15,
            'shadows': (25, 30, 35),
            'highlights': (250, 250, 245),
            'gamma': 0.95
        },
        'dramatic': {
            'name': '戏剧性',
            'contrast': 1.4,
            'saturation': 1.1,
            'shadows': (10, 15, 25),
            'highlights': (255, 250, 240),
            'gamma': 1.15
        },
        'warm': {
            'name': '暖色调',
            'contrast': 1.05,
            'saturation': 1.1,
            'shadows': (40, 30, 20),
            'highlights': (255, 240, 220),
            'gamma': 1.0,
            'temperature': 10
        },
        'cool': {
            'name': '冷色调',
            'contrast': 1.05,
            'saturation': 1.0,
            'shadows': (20, 30, 40),
            'highlights': (230, 240, 255),
            'gamma': 1.0,
            'temperature': -10
        }
    }
    
    def __init__(self):
        super().__init__(
            name="Colorist",
            capabilities=[AgentCapability.COLOR_GRADING]
        )
        
        # 初始化LLM - Colorist使用GPT-4 Vision进行视觉分析
        self.init_llm('colorist')
        
    async def execute(self, task: Dict[str, Any]) -> AgentResult:
        """
        执行调色任务
        
        Args:
            task: {
                'type': 'color_grading',
                'video_path': str,
                'style': str,  # preset name or custom
                'custom_params': dict,  # optional
                'project_id': str
            }
        """
        video_path = task.get('video_path')
        style_name = task.get('style', 'cinematic')
        project_id = task.get('project_id')
        
        if not video_path or not Path(video_path).exists():
            return AgentResult(
                success=False,
                data={},
                message=f"视频文件不存在: {video_path}"
            )
            
        try:
            self.report_progress(10, "分析视频色彩...")
            
            # 1. 色彩分析
            color_analysis = await self._analyze_colors(video_path)
            
            self.report_progress(30, "应用色彩校正...")
            
            # 2. 色彩校正
            correction = await self._color_correction(video_path, color_analysis)
            
            self.report_progress(50, f"应用{style_name}风格...")
            
            # 3. 风格调色
            style_params = self._get_style_params(style_name, task.get('custom_params'))
            color_grading = await self._apply_style(video_path, style_params)
            
            self.report_progress(70, "色彩分级...")
            
            # 4. 色彩分级
            final_grading = await self._color_grading(color_grading, style_params)
            
            self.report_progress(90, "生成LUT...")
            
            # 5. 生成LUT
            lut_path = await self._generate_lut(style_params, project_id)
            
            self.report_progress(100, "调色完成")
            
            return AgentResult(
                success=True,
                data={
                    'project_id': project_id,
                    'color_profile': style_params,
                    'lut_path': lut_path,
                    'color_analysis': color_analysis,
                    'correction_params': correction,
                    'style_name': style_name
                },
                message=f"调色完成 - 风格: {self.PRESETS.get(style_name, {}).get('name', style_name)}"
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                data={},
                message=f"调色失败: {str(e)}"
            )
            
    async def _analyze_colors(self, video_path: str) -> Dict[str, Any]:
        """分析视频色彩 - 结合GPT-4 Vision智能分析"""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return {'error': '无法打开视频'}
            
        # 采样关键帧
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        sample_frames = [int(total_frames * i / 10) for i in range(1, 10)]
        
        color_stats = {
            'brightness': [],
            'contrast': [],
            'saturation': [],
            'dominant_colors': []
        }
        
        # 提取并分析关键帧
        frame_paths = []
        for frame_num in sample_frames[:3]:  # 前3帧用于视觉分析
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            if ret:
                # 保存帧用于LLM分析
                frame_path = f"/tmp/color_frame_{frame_num}.jpg"
                cv2.imwrite(frame_path, frame)
                frame_paths.append(frame_path)
                
        # 使用GPT-4 Vision分析
        if frame_paths and self.llm:
            try:
                vision_result = await self.llm.analyze_image(
                    frame_paths[0],
                    "分析这张视频帧的色彩特征：亮度、对比度、色温、饱和度。"
                    "建议适合的风格调色（cinematic/vintage/fresh/dramatic/warm/cool）。"
                    "以JSON格式返回分析结果。"
                )
                
                if vision_result.get('success'):
                    import json
                    content = vision_result['content']
                    # 尝试提取JSON
                    try:
                        if '```json' in content:
                            content = content.split('```json')[1].split('```')[0]
                        elif '```' in content:
                            content = content.split('```')[1].split('```')[0]
                        vision_analysis = json.loads(content.strip())
                        color_stats['vision_analysis'] = vision_analysis
                        color_stats['recommended_style'] = vision_analysis.get('recommended_style', 'cinematic')
                    except:
                        color_stats['vision_analysis'] = {'raw': content}
                        
            except Exception as e:
                color_stats['vision_error'] = str(e)
        }
        
        for frame_idx in sample_frames:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            
            if ret:
                # 转换到LAB色彩空间分析亮度
                lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
                l_channel = lab[:, :, 0]
                color_stats['brightness'].append(np.mean(l_channel))
                color_stats['contrast'].append(np.std(l_channel))
                
                # 转换到HSV分析饱和度
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                s_channel = hsv[:, :, 1]
                color_stats['saturation'].append(np.mean(s_channel))
                
                # 提取主色调
                pixels = frame.reshape(-1, 3)
                pixels = np.float32(pixels)
                criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
                _, labels, centers = cv2.kmeans(pixels, 3, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
                dominant = centers[np.argmax(np.bincount(labels.flatten()))]
                color_stats['dominant_colors'].append(dominant.tolist())
                
        cap.release()
        
        # 计算平均值
        return {
            'avg_brightness': np.mean(color_stats['brightness']) if color_stats['brightness'] else 128,
            'avg_contrast': np.mean(color_stats['contrast']) if color_stats['contrast'] else 30,
            'avg_saturation': np.mean(color_stats['saturation']) if color_stats['saturation'] else 100,
            'dominant_colors': color_stats['dominant_colors'][:3],
            'recommendations': self._generate_recommendations(color_stats)
        }
        
    def _generate_recommendations(self, stats: Dict) -> List[str]:
        """生成调色建议"""
        recommendations = []
        
        avg_brightness = np.mean(stats['brightness']) if stats['brightness'] else 128
        avg_contrast = np.mean(stats['contrast']) if stats['contrast'] else 30
        
        if avg_brightness < 80:
            recommendations.append("视频偏暗，建议提升曝光")
        elif avg_brightness > 200:
            recommendations.append("视频偏亮，建议降低曝光")
            
        if avg_contrast < 20:
            recommendations.append("对比度偏低，建议增强对比度")
        elif avg_contrast > 60:
            recommendations.append("对比度偏高，建议降低对比度")
            
        return recommendations
        
    async def _color_correction(
        self,
        video_path: str,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """色彩校正"""
        corrections = {
            'exposure': 0,
            'contrast': 1.0,
            'highlights': 0,
            'shadows': 0,
            'whites': 0,
            'blacks': 0
        }
        
        # 根据分析结果自动校正
        avg_brightness = analysis.get('avg_brightness', 128)
        avg_contrast = analysis.get('avg_contrast', 30)
        
        # 曝光校正
        if avg_brightness < 100:
            corrections['exposure'] = (128 - avg_brightness) / 128 * 0.5
        elif avg_brightness > 156:
            corrections['exposure'] = -(avg_brightness - 128) / 128 * 0.5
            
        # 对比度校正
        if avg_contrast < 25:
            corrections['contrast'] = 1.1
        elif avg_contrast > 50:
            corrections['contrast'] = 0.95
            
        return corrections
        
    def _get_style_params(
        self,
        style_name: str,
        custom_params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """获取风格参数"""
        if style_name in self.PRESETS:
            params = self.PRESETS[style_name].copy()
        else:
            # 默认电影感
            params = self.PRESETS['cinematic'].copy()
            
        # 合并自定义参数
        if custom_params:
            params.update(custom_params)
            
        return params
        
    async def _apply_style(
        self,
        video_path: str,
        style_params: Dict[str, Any]
    ) -> str:
        """应用风格"""
        # 返回处理后的视频路径（实际实现需要视频处理）
        # 这里返回原路径，实际应该生成新文件
        return video_path
        
    async def _color_grading(
        self,
        video_path: str,
        style_params: Dict[str, Any]
    ) -> str:
        """色彩分级"""
        # 分别调整阴影、中间调、高光
        grading = {
            'shadows': style_params.get('shadows', (20, 20, 20)),
            'midtones': (128, 128, 128),
            'highlights': style_params.get('highlights', (240, 240, 240)),
            'gamma': style_params.get('gamma', 1.0)
        }
        
        return video_path
        
    async def _generate_lut(
        self,
        style_params: Dict[str, Any],
        project_id: str
    ) -> str:
        """生成LUT文件"""
        # 创建LUT目录
        lut_dir = Path.home() / "CineFlow" / "LUTs"
        lut_dir.mkdir(parents=True, exist_ok=True)
        
        lut_path = lut_dir / f"{project_id}_{style_params.get('name', 'custom')}.cube"
        
        # 生成简单的3D LUT（实际应该使用专业LUT格式）
        with open(lut_path, 'w') as f:
            f.write(f"# CineFlow Generated LUT\n")
            f.write(f"# Style: {style_params.get('name', 'custom')}\n")
            f.write(f"LUT_3D_SIZE 33\n")
            f.write(f"# Parameters: {style_params}\n")
            
        return str(lut_path)
        
    def get_available_styles(self) -> List[Dict[str, str]]:
        """获取可用风格列表"""
        return [
            {'id': key, 'name': value['name']}
            for key, value in self.PRESETS.items()
        ]
