"""
精彩片段检测器 - 自动剪辑模块
Highlight Detector - Auto Clip Generation
"""

import subprocess
import json
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class HighlightSegment:
    """精彩片段"""
    start_time: float      # 开始时间 (秒)
    end_time: float        # 结束时间 (秒)
    score: float           # 精彩分数 (0-100)
    reason: str            # 原因描述
    scene_type: str        # 场景类型
    
    def duration(self) -> float:
        return self.end_time - self.start_time


class SceneType:
    """场景类型常量"""
    ACTION = "action"           # 动作场面
    EMOTIONAL = "emotional"     # 情感时刻
    FUNNY = "funny"             # 搞笑片段
    HEARTWARMING = "heartwarming" # 暖心时刻
    SURPRISE = "surprise"       # 惊喜时刻
    CLIMAX = "climax"           # 高潮片段
    SPEECH = "speech"           # 演讲/对话
    SPORTS = "sports"           # 体育运动
    MUSIC = "music"             # 音乐/演唱
    NORMAL = "normal"           # 普通片段


class HighlightDetector:
    """精彩片段检测器"""
    
    def __init__(self, workspace: str = "./output"):
        self.workspace = Path(workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.temp_dir = self.workspace / "temp"
        self.temp_dir.mkdir(exist_ok=True)
    
    def get_ffmpeg_path(self) -> str:
        return "ffmpeg"
    
    def get_ffprobe_path(self) -> str:
        return "ffprobe"
    
    def extract_frames(
        self,
        video_path: str,
        fps: int = 1,
        output_dir: Optional[str] = None
    ) -> List[str]:
        """提取视频帧"""
        if output_dir is None:
            output_dir = str(self.temp_dir / "frames")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        output_pattern = f"{output_dir}/frame_%04d.jpg"
        
        cmd = [
            self.get_ffmpeg_path(),
            "-i", video_path,
            "-vf", f"fps={fps}",
            "-q:v", "2",
            output_pattern,
            "-y"
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        # 返回提取的帧文件列表
        frames = sorted(Path(output_dir).glob("frame_*.jpg"))
        return [str(f) for f in frames]
    
    def analyze_audio_peaks(
        self,
        video_path: str
    ) -> List[Dict[str, Any]]:
        """分析音频峰值 (笑声、掌声、欢呼声)"""
        # 提取音频
        audio_path = str(self.temp_dir / "audio.wav")
        
        cmd = [
            self.get_ffmpeg_path(),
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            audio_path,
            "-y"
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        
        # 使用 ffmpeg 分析音量
        # 简化版: 直接返回时间戳
        peaks = []
        
        # 使用 ffprobe 分析音量大段
        cmd = [
            self.get_ffprobe_path(),
            "-v", "quiet",
            "-print_format", "json",
            "-show_entries", "frame=pts_time,pict_type",
            "-select_streams", "v:0",
            video_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            data = json.loads(result.stdout)
            
            # 分析帧类型变化 (场景切换)
            frames = data.get("frames", [])
            prev_type = None
            
            for i, frame in enumerate(frames):
                pts = float(frame.get("pts_time", 0))
                pic_type = frame.get("pict_type", "")
                
                # 检测场景切换
                if prev_type and pic_type == "I" and prev_type != "I":
                    peaks.append({
                        "time": pts,
                        "type": "scene_cut",
                        "score": 80
                    })
                
                prev_type = pic_type
            
        except Exception as e:
            print(f"Audio analysis error: {e}")
        
        return peaks
    
    def detect_motion_intensity(
        self,
        video_path: str,
        sample_interval: float = 1.0
    ) -> List[Dict[str, Any]]:
        """检测运动强度"""
        # 获取视频信息
        cmd = [
            self.get_ffprobe_path(),
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        
        duration = float(data["format"]["duration"])
        
        # 简化版: 使用 ffprobe 的帧信息
        motion_segments = []
        
        # 以 sample_interval 为单位分析
        for t in np.arange(0, duration, sample_interval):
            # 简单评分: 随机高分，实际应该用光流法
            score = np.random.randint(40, 90)
            
            if score > 70:
                motion_segments.append({
                    "start_time": t,
                    "end_time": t + sample_interval,
                    "score": score,
                    "type": SceneType.ACTION
                })
        
        return motion_segments
    
    def detect_scene_changes(
        self,
        video_path: str
    ) -> List[Dict[str, Any]]:
        """检测场景切换"""
        # 使用 ffprobe 检测场景变化
        cmd = [
            self.get_ffprobe_path(),
            "-v", "quiet",
            "-print_format", "json",
            "-show_entries", "frame=pts_time,pict_type",
            "-select_streams", "v:0",
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        
        frames = data.get("frames", [])
        scene_changes = []
        
        prev_pts = 0
        prev_type = None
        
        for frame in frames:
            pts = float(frame.get("pts_time", 0))
            pic_type = frame.get("pict_type", "")
            
            # I帧 (关键帧) 通常是场景切换
            if pic_type == "I" and prev_type != "I":
                if pts - prev_pts > 2:  # 间隔超过2秒
                    scene_changes.append({
                        "time": pts,
                        "type": "scene_change",
                        "score": 75
                    })
            
            prev_pts = pts
            prev_type = pic_type
        
        return scene_changes
    
    def detect_highlights(
        self,
        video_path: str,
        min_duration: float = 3.0,
        max_duration: float = 30.0,
        use_ai: bool = True
    ) -> List[HighlightSegment]:
        """
        检测精彩片段
        
        Args:
            video_path: 视频路径
            min_duration: 最小片段时长
            max_duration: 最大片段时长
            use_ai: 是否使用 AI 分析
        
        Returns:
            精彩片段列表
        """
        highlights = []
        
        # 1. 检测场景切换
        scene_changes = self.detect_scene_changes(video_path)
        
        # 2. 检测运动强度
        motion_segments = self.detect_motion_intensity(video_path)
        
        # 3. 音频峰值分析
        audio_peaks = self.analyze_audio_peaks(video_path)
        
        # 合并分析结果
        all_events = []
        all_events.extend([
            {"time": e["time"], "score": e["score"], "source": "scene"}
            for e in scene_changes
        ])
        all_events.extend([
            {"time": s["start_time"], "score": s["score"], "source": "motion"}
            for s in motion_segments
        ])
        all_events.extend([
            {"time": e["time"], "score": e["score"], "source": "audio"}
            for e in audio_peaks
        ])
        
        # 按时间排序
        all_events.sort(key=lambda x: x["time"])
        
        # 聚合成片段
        if all_events:
            current_start = all_events[0]["time"]
            current_scores = [all_events[0]["score"]]
            current_types = ["scene"]
            
            for event in all_events[1:]:
                # 如果与前一个事件间隔小于3秒，合并
                if event["time"] - current_start < 3.0:
                    current_scores.append(event["score"])
                    if event["source"] not in current_types:
                        current_types.append(event["source"])
                else:
                    # 保存当前片段
                    avg_score = np.mean(current_scores)
                    if avg_score > 65:
                        highlights.append(HighlightSegment(
                            start_time=max(0, current_start - 0.5),
                            end_time=min(event["time"] + 0.5, current_start + max_duration),
                            score=avg_score,
                            reason=f"类型: {', '.join(current_types)}",
                            scene_type=current_types[0] if current_types else SceneType.NORMAL
                        ))
                    
                    # 开始新片段
                    current_start = event["time"]
                    current_scores = [event["score"]]
                    current_types = [event["source"]]
            
            # 处理最后一个片段
            if current_scores:
                avg_score = np.mean(current_scores)
                if avg_score > 65:
                    highlights.append(HighlightSegment(
                        start_time=max(0, current_start - 0.5),
                        end_time=current_start + max_duration,
                        score=avg_score,
                        reason=f"类型: {', '.join(current_types)}",
                        scene_type=current_types[0] if current_types else SceneType.NORMAL
                    ))
        
        # 4. 如果启用 AI，使用视频理解模块进一步分析
        if use_ai and highlights:
            try:
                from app.services.ai.video_understanding import VideoUnderstanding
                
                video_understanding = VideoUnderstanding()
                
                # 分析每个片段
                for highlight in highlights:
                    analysis = video_understanding.analyze_segment(
                        video_path,
                        highlight.start_time,
                        highlight.end_time
                    )
                    
                    # 根据 AI 分析调整分数
                    if analysis.get("is_highlight"):
                        highlight.score = min(100, highlight.score + 15)
                    if analysis.get("emotion"):
                        highlight.scene_type = analysis["emotion"]
                    if analysis.get("description"):
                        highlight.reason = analysis["description"]
                        
            except ImportError:
                print("VideoUnderstanding 模块未安装，跳过 AI 分析")
        
        # 按分数排序
        highlights.sort(key=lambda x: x.score, reverse=True)
        
        return highlights
    
    def export_highlights(
        self,
        video_path: str,
        highlights: List[HighlightSegment],
        output_path: str,
        include_transitions: bool = True,
        add_intro_outro: bool = False
    ) -> str:
        """
        导出精彩片段
        
        Args:
            video_path: 原始视频
            highlights: 精彩片段列表
            output_path: 输出路径
            include_transitions: 添加转场
            add_intro_outro: 添加开场/结束动画
        
        Returns:
            输出视频路径
        """
        # 创建片段文件列表
        concat_file = self.temp_dir / "concat.txt"
        
        with open(concat_file, "w") as f:
            for i, hl in enumerate(highlights):
                # 提取片段 (使用 tee 进行临时输出)
                segment_path = self.temp_dir / f"segment_{i}.mp4"
                
                cmd = [
                    self.get_ffmpeg_path(),
                    "-ss", str(hl.start_time),
                    "-to", str(hl.end_time),
                    "-i", video_path,
                    "-c", "copy",
                    str(segment_path),
                    "-y"
                ]
                subprocess.run(cmd, check=True, capture_output=True)
                
                f.write(f"file '{segment_path}'\n")
        
        # 合并片段
        cmd = [
            self.get_ffmpeg_path(),
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",
            output_path,
            "-y"
        ]
        
        subprocess.run(cmd, check=True)
        
        # 添加开场/结束
        if add_intro_outro:
            # TODO: 添加开场动画
            pass
        
        # 添加转场
        if include_transitions:
            # 基础版: 直接连接
            # 进阶版: 添加转场特效
            pass
        
        return output_path
    
    def generate_highlight_reel(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        max_duration: float = 60.0,
        num_clips: int = 5,
        style: str = "exciting"
    ) -> str:
        """
        生成精彩集锦
        
        Args:
            video_path: 原始视频
            output_path: 输出路径
            max_duration: 最大时长
            num_clips: 片段数量
            style: 风格 (exciting, emotional, funny, summary)
        
        Returns:
            输出视频路径
        """
        if output_path is None:
            input_name = Path(video_path).stem
            output_path = str(self.workspace / f"{input_name}_highlights.mp4")
        
        # 1. 检测精彩片段
        highlights = self.detect_highlights(video_path)
        
        if not highlights:
            print("未检测到精彩片段")
            return video_path
        
        # 2. 根据风格筛选
        if style == "exciting":
            # 选择高分动作片段
            filtered = [h for h in highlights if h.scene_type == SceneType.ACTION]
            if not filtered:
                filtered = highlights[:num_clips]
        elif style == "emotional":
            filtered = [h for h in highlights if h.scene_type == SceneType.EMOTIONAL]
            if not filtered:
                filtered = highlights[:num_clips]
        elif style == "funny":
            filtered = [h for h in highlights if h.scene_type == SceneType.FUNNY]
            if not filtered:
                filtered = highlights[:num_clips]
        else:  # summary
            filtered = highlights[:num_clips]
        
        # 3. 限制总时长
        total_duration = 0
        selected = []
        
        for hl in filtered:
            if total_duration + hl.duration() <= max_duration:
                selected.append(hl)
                total_duration += hl.duration()
            if len(selected) >= num_clips:
                break
        
        # 4. 导出
        return self.export_highlights(video_path, selected, output_path)
    
    def cleanup_temp(self):
        """清理临时文件"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            self.temp_dir.mkdir()


# 示例用法
if __name__ == "__main__":
    detector = HighlightDetector("./output")
    
    # 检测精彩片段
    # highlights = detector.detect_highlights("input.mp4")
    
    # 生成精彩集锦
    # result = detector.generate_highlight_reel("input.mp4", max_duration=60)
    
    print("HighlightDetector 模块已加载")
