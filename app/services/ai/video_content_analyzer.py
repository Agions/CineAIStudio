"""
视频内容分析器 (Video Content Analyzer)

深度分析视频画面内容，为 AI 解说、混剪、独白提供素材理解。

功能:
- 提取关键帧
- 分析画面内容（支持 OpenAI Vision / 本地模型）
- 识别场景类型
- 提取文字（OCR）
- 检测人脸和表情

使用示例:
    from app.services.ai import VideoContentAnalyzer
    
    analyzer = VideoContentAnalyzer(vision_api_key="your-key")
    
    # 分析视频
    result = analyzer.analyze("video.mp4")
    
    logger.info(f"视频主题: {result.summary}")
    for frame in result.keyframes:
"""

import os
import logging
import subprocess
import base64
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """内容类型"""
    PERSON = "person"              # 人物
    LANDSCAPE = "landscape"        # 风景
    INDOOR = "indoor"              # 室内
    OUTDOOR = "outdoor"            # 室外
    TEXT = "text"                  # 文字/字幕
    PRODUCT = "product"            # 产品
    ANIMAL = "animal"              # 动物
    FOOD = "food"                  # 美食
    VEHICLE = "vehicle"            # 车辆
    BUILDING = "building"          # 建筑
    ACTION = "action"              # 动作场景
    UNKNOWN = "unknown"


class Emotion(Enum):
    """情感类型"""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    EXCITED = "excited"
    CALM = "calm"
    TENSE = "tense"
    ROMANTIC = "romantic"


@dataclass
class KeyframeInfo:
    """关键帧信息"""
    index: int                     # 帧序号
    timestamp: float               # 时间戳（秒）
    image_path: str = ""           # 图片路径
    
    # 画面分析
    description: str = ""          # 画面描述
    content_type: ContentType = ContentType.UNKNOWN
    objects: List[str] = field(default_factory=list)  # 检测到的物体
    text_content: str = ""         # OCR 识别的文字
    
    # 情感和氛围
    emotion: Emotion = Emotion.NEUTRAL
    color_tone: str = ""           # 色调（暖/冷/中性）
    brightness: float = 0.5        # 亮度 (0-1)
    
    # 适用性
    suitability: Dict[str, float] = field(default_factory=dict)  # 不同用途的适用性分数


@dataclass
class VideoAnalysisResult:
    """视频分析结果"""
    video_path: str
    duration: float                # 视频时长
    resolution: Tuple[int, int]    # 分辨率
    fps: float                     # 帧率
    
    # 关键帧
    keyframes: List[KeyframeInfo] = field(default_factory=list)
    
    # 整体分析
    summary: str = ""              # 视频内容摘要
    main_topics: List[str] = field(default_factory=list)  # 主要主题
    main_emotion: Emotion = Emotion.NEUTRAL  # 主要情感
    suggested_style: str = ""      # 建议的解说/独白风格
    
    # 关键词
    keywords: List[str] = field(default_factory=list)
    
    # 脚本建议
    script_suggestion: str = ""    # 文案建议


@dataclass
class AnalyzerConfig:
    """分析器配置"""
    # 关键帧提取
    keyframe_interval: float = 2.0  # 每隔多少秒提取一帧
    max_keyframes: int = 30         # 最大关键帧数
    keyframe_quality: int = 95      # JPEG 质量
    
    # 分析选项
    use_vision_api: bool = True     # 是否使用视觉API分析
    use_ocr: bool = True            # 是否OCR识别文字
    parallel_analysis: bool = True  # 是否并行分析
    
    # API 配置
    vision_provider: str = "openai"  # openai / local / qwen


class VideoContentAnalyzer:
    """
    视频内容分析器
    
    深度分析视频画面内容，理解视频主题和情感
    
    使用示例:
        analyzer = VideoContentAnalyzer(
            vision_api_key="sk-xxx",
            config=AnalyzerConfig(keyframe_interval=3.0)
        )
        
        result = analyzer.analyze("video.mp4")
        
        print(f"视频摘要: {result.summary}")
        print(f"主要主题: {result.main_topics}")
        print(f"建议风格: {result.suggested_style}")
    """
    
    def __init__(
        self,
        vision_api_key: Optional[str] = None,
        config: Optional[AnalyzerConfig] = None,
    ):
        """
        初始化分析器
        
        Args:
            vision_api_key: 视觉API密钥（OpenAI/通义千问）
            config: 分析配置
        """
        self.api_key = vision_api_key or os.getenv("OPENAI_API_KEY")
        self.config = config or AnalyzerConfig()
        
        # 临时目录
        self._temp_dir = Path("./temp/keyframes")
        self._temp_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze(self, video_path: str) -> VideoAnalysisResult:
        """
        分析视频内容
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            视频分析结果
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        # 获取视频信息
        duration, width, height, fps = self._get_video_info(str(video_path))
        
        result = VideoAnalysisResult(
            video_path=str(video_path),
            duration=duration,
            resolution=(width, height),
            fps=fps,
        )
        
        # 提取关键帧
        keyframes = self._extract_keyframes(str(video_path), duration)
        
        # 分析关键帧
        if self.config.use_vision_api and self.api_key:
            if self.config.parallel_analysis:
                self._analyze_keyframes_parallel(keyframes)
            else:
                self._analyze_keyframes_sequential(keyframes)
        else:
            # 使用本地分析（基于 FFmpeg）
            self._analyze_keyframes_local(keyframes)
        
        result.keyframes = keyframes
        
        # 生成整体分析
        self._generate_summary(result)
        
        return result
    
    def _get_video_info(self, video_path: str) -> Tuple[float, int, int, float]:
        """获取视频信息"""
        cmd = [
            'ffprobe', '-v', 'quiet',
            '-show_entries', 'format=duration:stream=width,height,r_frame_rate',
            '-of', 'json',
            video_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                duration = float(data.get('format', {}).get('duration', 0))
                
                stream = data.get('streams', [{}])[0]
                width = int(stream.get('width', 1920))
                height = int(stream.get('height', 1080))
                
                # 解析帧率
                fps_str = stream.get('r_frame_rate', '30/1')
                if '/' in fps_str:
                    num, den = fps_str.split('/')
                    fps = float(num) / float(den) if float(den) > 0 else 30.0
                else:
                    fps = float(fps_str)
                
                return duration, width, height, fps
        except Exception as e:
            logger.error(f"获取视频信息失败: {e}")
        
        return 0.0, 1920, 1080, 30.0
    
    def _extract_keyframes(
        self,
        video_path: str,
        duration: float,
    ) -> List[KeyframeInfo]:
        """提取关键帧"""
        keyframes = []
        
        # 计算提取间隔
        interval = self.config.keyframe_interval
        num_frames = min(
            int(duration / interval) + 1,
            self.config.max_keyframes
        )
        
        # 调整间隔以均匀分布
        if num_frames > 1:
            interval = duration / (num_frames - 1)
        
        video_name = Path(video_path).stem
        output_dir = self._temp_dir / video_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for i in range(num_frames):
            timestamp = i * interval
            if timestamp > duration:
                break
            
            output_path = output_dir / f"frame_{i:04d}.jpg"
            
            # 使用 FFmpeg 提取帧
            cmd = [
                'ffmpeg', '-y',
                '-ss', str(timestamp),
                '-i', video_path,
                '-vframes', '1',
                '-q:v', str(100 - self.config.keyframe_quality),
                str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True)
            
            if result.returncode == 0 and output_path.exists():
                keyframe = KeyframeInfo(
                    index=i,
                    timestamp=timestamp,
                    image_path=str(output_path),
                )
                keyframes.append(keyframe)
        
        return keyframes
    
    def _analyze_keyframes_parallel(self, keyframes: List[KeyframeInfo]) -> None:
        """并行分析关键帧"""
        with ThreadPoolExecutor(max_workers=4) as executor:
            list(executor.map(self._analyze_single_keyframe, keyframes))
    
    def _analyze_keyframes_sequential(self, keyframes: List[KeyframeInfo]) -> None:
        """顺序分析关键帧"""
        for keyframe in keyframes:
            self._analyze_single_keyframe(keyframe)
    
    def _analyze_single_keyframe(self, keyframe: KeyframeInfo) -> None:
        """分析单个关键帧"""
        if not keyframe.image_path or not Path(keyframe.image_path).exists():
            return
        
        # 读取图片并转为 base64
        with open(keyframe.image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        # 调用视觉API分析
        try:
            if self.config.vision_provider == "openai":
                analysis = self._analyze_with_openai(image_data)
            else:
                analysis = self._analyze_with_local(keyframe.image_path)
            
            # 解析结果
            keyframe.description = analysis.get("description", "")
            keyframe.objects = analysis.get("objects", [])
            keyframe.text_content = analysis.get("text", "")
            keyframe.content_type = self._parse_content_type(analysis.get("content_type", ""))
            keyframe.emotion = self._parse_emotion(analysis.get("emotion", ""))
            keyframe.color_tone = analysis.get("color_tone", "neutral")
            
        except Exception as e:
            logger.warning(f"分析帧 {keyframe.index} 失败: {e}")
    
    def _analyze_with_openai(self, image_base64: str) -> Dict[str, Any]:
        """使用 OpenAI Vision API 分析"""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.api_key)
            
            prompt = """分析这张视频截图，返回JSON格式：
{
    "description": "详细描述画面内容（50-100字）",
    "content_type": "person/landscape/indoor/outdoor/text/product/animal/food/action",
    "objects": ["检测到的主要物体列表"],
    "text": "画面中出现的文字（如果有）",
    "emotion": "neutral/happy/sad/excited/calm/tense/romantic",
    "color_tone": "warm/cold/neutral",
    "suitable_for": {
        "commentary": 0-100,
        "monologue": 0-100,
        "mashup": 0-100
    }
}
只返回JSON，不要其他内容。"""
            
            response = client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}",
                                    "detail": "low"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
            )
            
            content = response.choices[0].message.content
            
            # 尝试解析 JSON
            try:
                # 移除可能的 markdown 代码块标记
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                
                return json.loads(content.strip())
            except json.JSONDecodeError:
                return {"description": content}
            
        except Exception as e:
            logger.error(f"OpenAI Vision 分析失败: {e}")
            return {}
    
    def _analyze_with_local(self, image_path: str) -> Dict[str, Any]:
        """使用本地方法分析（FFmpeg信号统计）"""
        # 使用 FFmpeg 获取图像统计信息
        cmd = [
            'ffprobe', '-v', 'quiet',
            '-show_entries', 'frame=pkt_pts_time',
            '-show_entries', 'frame_tags=lavfi.signalstats.YAVG,lavfi.signalstats.SATAVG',
            '-of', 'json',
            image_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            # 基于亮度和饱和度做简单判断
            # 这是降级方案，准确度有限
            return {
                "description": "画面内容（需要视觉API获取详细描述）",
                "content_type": "unknown",
                "objects": [],
                "emotion": "neutral",
            }
        except Exception:
            return {}
    
    def _analyze_keyframes_local(self, keyframes: List[KeyframeInfo]) -> None:
        """使用本地方法分析（不使用API）"""
        for keyframe in keyframes:
            if not keyframe.image_path:
                continue
            
            # 使用 FFmpeg 获取亮度信息
            brightness = self._get_image_brightness(keyframe.image_path)
            keyframe.brightness = brightness
            
            # 基于亮度简单判断
            if brightness < 0.3:
                keyframe.color_tone = "dark"
                keyframe.emotion = Emotion.TENSE
            elif brightness > 0.7:
                keyframe.color_tone = "bright"
                keyframe.emotion = Emotion.HAPPY
            else:
                keyframe.color_tone = "neutral"
                keyframe.emotion = Emotion.NEUTRAL
            
            keyframe.description = f"画面亮度 {brightness:.1%}"
    
    def _get_image_brightness(self, image_path: str) -> float:
        """获取图像亮度"""
        cmd = [
            'ffmpeg', '-i', image_path,
            '-vf', 'signalstats,metadata=print:file=-',
            '-f', 'null', '-'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            # 解析 YAVG (亮度平均值)
            import re
            match = re.search(r'YAVG=(\d+\.?\d*)', result.stderr)
            if match:
                return float(match.group(1)) / 255.0
        except Exception:
            pass
        
        return 0.5
    
    def _parse_content_type(self, type_str: str) -> ContentType:
        """解析内容类型"""
        type_map = {
            "person": ContentType.PERSON,
            "landscape": ContentType.LANDSCAPE,
            "indoor": ContentType.INDOOR,
            "outdoor": ContentType.OUTDOOR,
            "text": ContentType.TEXT,
            "product": ContentType.PRODUCT,
            "animal": ContentType.ANIMAL,
            "food": ContentType.FOOD,
            "vehicle": ContentType.VEHICLE,
            "building": ContentType.BUILDING,
            "action": ContentType.ACTION,
        }
        return type_map.get(type_str.lower(), ContentType.UNKNOWN)
    
    def _parse_emotion(self, emotion_str: str) -> Emotion:
        """解析情感类型"""
        emotion_map = {
            "neutral": Emotion.NEUTRAL,
            "happy": Emotion.HAPPY,
            "sad": Emotion.SAD,
            "excited": Emotion.EXCITED,
            "calm": Emotion.CALM,
            "tense": Emotion.TENSE,
            "romantic": Emotion.ROMANTIC,
        }
        return emotion_map.get(emotion_str.lower(), Emotion.NEUTRAL)
    
    def _generate_summary(self, result: VideoAnalysisResult) -> None:
        """生成整体分析摘要"""
        if not result.keyframes:
            return
        
        # 统计内容类型
        type_counts = {}
        for kf in result.keyframes:
            t = kf.content_type.value
            type_counts[t] = type_counts.get(t, 0) + 1
        
        # 找出主要类型
        if type_counts:
            main_type = max(type_counts, key=type_counts.get)
            result.main_topics = [main_type]
        
        # 统计情感
        emotion_counts = {}
        for kf in result.keyframes:
            e = kf.emotion.value
            emotion_counts[e] = emotion_counts.get(e, 0) + 1
        
        if emotion_counts:
            main_emotion_str = max(emotion_counts, key=emotion_counts.get)
            result.main_emotion = self._parse_emotion(main_emotion_str)
        
        # 收集描述
        descriptions = [kf.description for kf in result.keyframes if kf.description]
        
        # 收集关键词
        all_objects = []
        for kf in result.keyframes:
            all_objects.extend(kf.objects)
        result.keywords = list(set(all_objects))[:20]
        
        # 生成摘要
        if descriptions:
            result.summary = " ".join(descriptions[:5])
        else:
            result.summary = f"视频时长 {result.duration:.1f}秒，包含 {len(result.keyframes)} 个关键场景"
        
        # 建议风格
        if result.main_emotion == Emotion.SAD:
            result.suggested_style = "melancholic"
        elif result.main_emotion == Emotion.HAPPY:
            result.suggested_style = "cheerful"
        elif result.main_emotion == Emotion.EXCITED:
            result.suggested_style = "energetic"
        elif result.main_emotion == Emotion.CALM:
            result.suggested_style = "peaceful"
        else:
            result.suggested_style = "neutral"
        
        # 生成脚本建议
        result.script_suggestion = self._generate_script_suggestion(result)
    
    def _generate_script_suggestion(self, result: VideoAnalysisResult) -> str:
        """生成脚本建议"""
        if not self.api_key:
            return ""
        
        # 收集关键帧描述
        descriptions = [
            f"[{kf.timestamp:.1f}s] {kf.description}"
            for kf in result.keyframes[:10]
            if kf.description
        ]
        
        if not descriptions:
            return ""
        
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.api_key)
            
            prompt = f"""基于以下视频内容分析，生成一段适合这个视频的解说/独白文案建议。

视频信息:
- 时长: {result.duration:.1f}秒
- 主要主题: {', '.join(result.main_topics)}
- 情感基调: {result.main_emotion.value}
- 关键词: {', '.join(result.keywords[:10])}

画面描述:
{chr(10).join(descriptions)}

请生成:
1. 一段约100字的解说文案（客观、信息化）
2. 一段约100字的独白文案（第一人称、情感化）

格式：
【解说文案】
...

【独白文案】
..."""
            
            response = client.chat.completions.create(
                model="gpt-5-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"生成脚本建议失败: {e}")
            return ""
    
    def cleanup(self) -> None:
        """清理临时文件"""
        import shutil
        if self._temp_dir.exists():
            shutil.rmtree(self._temp_dir, ignore_errors=True)


def analyze_video(video_path: str, api_key: Optional[str] = None) -> VideoAnalysisResult:
    """
    分析视频内容的便捷函数
    
    Args:
        video_path: 视频路径
        api_key: 视觉API密钥
        
    Returns:
        分析结果
    """
    analyzer = VideoContentAnalyzer(vision_api_key=api_key)
    return analyzer.analyze(video_path)


def demo_analyze():
    """演示视频分析"""
    print("=" * 50)
    print("视频内容分析器演示")
    print("=" * 50)
    
    analyzer = VideoContentAnalyzer()
    
    # 检查是否有测试视频
    test_videos = list(Path("test_assets").glob("*.mp4"))
    
    if not test_videos:
        print("\n⚠️ 没有找到测试视频")
        print("请将 .mp4 文件放入 test_assets 目录")
        return
    
    video = str(test_videos[0])
    print(f"\n分析视频: {video}")
    
    result = analyzer.analyze(video)
    
    print(f"\n📊 分析结果:")
    print(f"   时长: {result.duration:.1f}秒")
    print(f"   分辨率: {result.resolution[0]}x{result.resolution[1]}")
    print(f"   帧率: {result.fps:.1f}")
    print(f"   关键帧: {len(result.keyframes)} 个")
    print(f"   主要情感: {result.main_emotion.value}")
    print(f"   建议风格: {result.suggested_style}")
    
    if result.keywords:
        print(f"   关键词: {', '.join(result.keywords[:10])}")
    
    print(f"\n📝 摘要:")
    print(f"   {result.summary[:200]}...")
    
    if result.script_suggestion:
        print(f"\n✍️ 脚本建议:")
        print(result.script_suggestion)


if __name__ == '__main__':
    demo_analyze()
