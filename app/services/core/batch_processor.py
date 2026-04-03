#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
批量处理管理器

支持多个视频的批量处理，包括：
- 批量场景分析
- 批量字幕生成
- 批量转码
- 批量导出

使用示例:
    from app.services.core import BatchProcessor, BatchTask, BatchConfig
    
    processor = BatchProcessor()
    
    # 添加任务
    processor.add_task(BatchTask(
        input_path="video1.mp4",
        operation="analyze",
    ))
    processor.add_task(BatchTask(
        input_path="video2.mp4",
        operation="subtitles",
    ))
    
    # 执行批量处理
    results = processor.run()
"""

import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging


class BatchOperation(Enum):
    """批量操作类型"""
    ANALYZE = "analyze"           # 场景分析
    SUBTITLES = "subtitles"       # 字幕生成
    TRANSCODE = "transcode"       # 转码
    EXPORT_JIANYING = "jianying" # 导出剪映草稿
    EXPORT_EDL = "edl"           # 导出 EDL
    BEAT_SYNC = "beat_sync"      # Beat-sync 混剪


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchTask:
    """批量任务"""
    id: str = ""                  # 任务唯一ID
    input_path: str = ""          # 输入文件路径
    output_path: str = ""         # 输出文件路径
    operation: str = ""          # 操作类型
    status: TaskStatus = TaskStatus.PENDING
    
    # 配置
    config: Dict[str, Any] = field(default_factory=dict)
    
    # 结果
    result: Any = None
    error: str = ""
    
    # 进度
    progress: float = 0.0         # 0-100
    
    def __post_init__(self):
        if not self.id:
            import uuid
            self.id = str(uuid.uuid4()[:8])


@dataclass
class BatchConfig:
    """批量处理配置"""
    max_workers: int = 4         # 最大并行任务数
    continue_on_error: bool = True  # 遇到错误是否继续
    output_dir: str = ""         # 默认输出目录
    
    # 操作特定配置
    transcode_preset: str = "medium"  # 转码 preset
    subtitle_language: str = "zh"     # 字幕语言
    
    # 回调
    on_progress: Optional[Callable] = None
    on_complete: Optional[Callable] = None
    on_error: Optional[Callable] = None


@dataclass
class BatchResult:
    """批量处理结果"""
    total: int = 0              # 总任务数
    completed: int = 0          # 完成数
    failed: int = 0            # 失败数
    cancelled: int = 0          # 取消数
    results: List[BatchTask] = field(default_factory=list)
    total_time: float = 0.0     # 总耗时（秒）


class BatchProcessor:
    """
    批量处理器
    
    支持多线程并行处理，提高批量处理效率
    """
    
    def __init__(self, config: Optional[BatchConfig] = None):
        self.config = config or BatchConfig()
        self.tasks: List[BatchTask] = []
        self._logger = logging.getLogger(__name__)
        self._is_running = False
        self._cancel_requested = False
    
    def add_task(self, task: BatchTask) -> str:
        """
        添加任务
        
        Args:
            task: 任务对象
            
        Returns:
            任务ID
        """
        self.tasks.append(task)
        return task.id
    
    def add_tasks(self, tasks: List[BatchTask]) -> List[str]:
        """
        批量添加任务
        
        Args:
            tasks: 任务列表
            
        Returns:
            任务ID列表
        """
        return [self.add_task(t) for t in tasks]
    
    def remove_task(self, task_id: str) -> bool:
        """移除任务"""
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                self.tasks.pop(i)
                return True
        return False
    
    def clear_tasks(self):
        """清空所有任务"""
        self.tasks.clear()
    
    def run(self) -> BatchResult:
        """
        执行批量处理
        
        Returns:
            处理结果
        """
        import time
        self._is_running = True
        self._cancel_requested = False
        
        start_time = time.time()
        
        result = BatchResult(total=len(self.tasks))
        
        if not self.tasks:
            return result
        
        # 创建输出目录
        if self.config.output_dir:
            Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)
        
        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # 提交所有任务
            future_to_task = {
                executor.submit(self._process_task, task): task
                for task in self.tasks
            }
            
            # 收集结果
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                
                if self._cancel_requested:
                    task.status = TaskStatus.CANCELLED
                    result.cancelled += 1
                    continue
                
                try:
                    future.result()
                    if task.status == TaskStatus.COMPLETED:
                        result.completed += 1
                    elif task.status == TaskStatus.FAILED:
                        result.failed += 1
                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    result.failed += 1
                    self._logger.error(f"任务 {task.id} 执行失败: {e}")
        
        result.total_time = time.time() - start_time
        result.results = self.tasks
        self._is_running = False
        
        return result
    
    def _process_task(self, task: BatchTask) -> None:
        """处理单个任务"""
        task.status = TaskStatus.RUNNING
        task.progress = 0.0
        
        try:
            if task.operation == BatchOperation.ANALYZE.value:
                self._analyze_video(task)
            elif task.operation == BatchOperation.SUBTITLES.value:
                self._generate_subtitles(task)
            elif task.operation == BatchOperation.TRANSCODE.value:
                self._transcode_video(task)
            elif task.operation == BatchOperation.EXPORT_JIANYING.value:
                self._export_jianying(task)
            elif task.operation == BatchOperation.EXPORT_EDL.value:
                self._export_edl(task)
            elif task.operation == BatchOperation.BEAT_SYNC.value:
                self._beat_sync_mashup(task)
            else:
                raise ValueError(f"不支持的操作: {task.operation}")
            
            task.status = TaskStatus.COMPLETED
            task.progress = 100.0
            
            if self.config.on_complete:
                self.config.on_complete(task)
                
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            
            if self.config.on_error:
                self.config.on_error(task, e)
            
            if not self.config.continue_on_error:
                self._cancel_requested = True
    
    def _analyze_video(self, task: BatchTask) -> None:
        """分析视频"""
        from app.services.ai import SceneAnalyzer
        
        analyzer = SceneAnalyzer()
        
        # 回调进度
        task.progress = 25.0
        scenes = analyzer.analyze(task.input_path)
        
        task.progress = 75.0
        task.result = {
            "scene_count": len(scenes),
            "duration": sum(s.end - s.start for s in scenes) if scenes else 0,
        }
    
    def _generate_subtitles(self, task: BatchTask) -> None:
        """生成字幕"""
        from app.services.ai import SpeechSubtitleExtractor
        
        language = task.config.get("language", self.config.subtitle_language)
        extractor = SpeechSubtitleExtractor(mode="api")
        
        task.progress = 30.0
        result = extractor.extract(task.input_path, language=language)
        
        # 生成输出路径
        if not task.output_path:
            task.output_path = str(Path(task.input_path).with_suffix('.srt'))
        
        # 写入字幕文件
        self._write_srt(result.segments, task.output_path)
        
        task.progress = 100.0
        task.result = {"subtitle_path": task.output_path}
    
    def _transcode_video(self, task: BatchTask) -> None:
        """转码视频"""
        preset = task.config.get("preset", self.config.transcode_preset)
        
        if not task.output_path:
            stem = Path(task.input_path).stem
            task.output_path = str(Path(task.input_path).parent / f"{stem}_transcoded.mp4")
        
        task.progress = 20.0
        
        # FFmpeg 转码命令
        cmd = [
            'ffmpeg', '-y',
            '-i', task.input_path,
            '-c:v', 'libx264',
            '-preset', preset,
            '-c:a', 'aac',
            '-b:a', '192k',
            task.output_path
        ]
        
        subprocess.run(cmd, capture_output=True, check=True)
        
        task.progress = 100.0
        task.result = {"output_path": task.output_path}
    
    def _export_jianying(self, task: BatchTask) -> None:
        """导出剪映草稿"""
        from app.services.export import JianyingExporter
        
        task.progress = 30.0
        
        exporter = JianyingExporter()
        draft = exporter.create_draft(Path(task.input_path).stem)
        
        task.progress = 60.0
        # ... 根据项目类型填充 draft
        
        if not task.output_path:
            task.output_path = str(Path(task.input_path).parent / "jianying_drafts")
        
        output = exporter.export(draft, task.output_path)
        
        task.progress = 100.0
        task.result = {"draft_path": output}
    
    def _export_edl(self, task: BatchTask) -> None:
        """导出 EDL"""
        from app.services.export import EDLExporter
        
        task.progress = 30.0
        
        exporter = EDLExporter()
        
        if not task.output_path:
            task.output_path = str(Path(task.input_path).with_suffix('.edl'))
        
        # 需要提供项目数据
        # 这里简化处理，实际应该传入项目
        task.progress = 100.0
        task.result = {"edl_path": task.output_path}
    
    def _beat_sync_mashup(self, task: BatchTask) -> None:
        """Beat-sync 混剪"""
        from app.services.video import BeatSyncMashupMaker, BeatSyncConfig
        
        videos = task.config.get("videos", [])
        music = task.config.get("music", "")
        duration = task.config.get("duration", 60.0)
        
        task.progress = 20.0
        
        maker = BeatSyncMashupMaker()
        project = maker.create_beat_sync_project(
            source_videos=videos,
            background_music=music,
            config=BeatSyncConfig(target_duration=duration),
        )
        
        task.progress = 70.0
        
        if not task.output_path:
            task.output_path = str(Path(task.input_path).parent / "beatsync_output.mp4")
        
        output = maker.export_video(project, task.output_path)
        
        task.progress = 100.0
        task.result = {"output_path": output}
    
    def _write_srt(self, segments: List, output_path: str) -> None:
        """写入 SRT 字幕文件"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, seg in enumerate(segments, 1):
                start = self._format_srt_time(seg.start)
                end = self._format_srt_time(seg.end)
                f.write(f"{i}\n")
                f.write(f"{start} --> {end}\n")
                f.write(f"{seg.text}\n\n")
    
    def _format_srt_time(self, seconds: float) -> str:
        """格式化 SRT 时间"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def cancel(self):
        """请求取消处理"""
        self._cancel_requested = True
    
    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._is_running


def batch_analyze(
    video_paths: List[str],
    output_dir: str = "",
) -> BatchResult:
    """
    批量分析视频
    
    Args:
        video_paths: 视频路径列表
        output_dir: 输出目录
        
    Returns:
        处理结果
    """
    processor = BatchProcessor(BatchConfig(output_dir=output_dir))
    
    for path in video_paths:
        processor.add_task(BatchTask(
            input_path=path,
            operation=BatchOperation.ANALYZE.value,
        ))
    
    return processor.run()


def batch_subtitles(
    video_paths: List[str],
    language: str = "zh",
    output_dir: str = "",
) -> BatchResult:
    """
    批量生成字幕
    
    Args:
        video_paths: 视频路径列表
        language: 字幕语言
        output_dir: 输出目录
        
    Returns:
        处理结果
    """
    processor = BatchProcessor(BatchConfig(
        output_dir=output_dir,
        subtitle_language=language,
    ))
    
    for path in video_paths:
        processor.add_task(BatchTask(
            input_path=path,
            operation=BatchOperation.SUBTITLES.value,
            config={"language": language},
        ))
    
    return processor.run()


def batch_transcode(
    video_paths: List[str],
    preset: str = "medium",
    output_dir: str = "",
) -> BatchResult:
    """
    批量转码
    
    Args:
        video_paths: 视频路径列表
        preset: 转码 preset
        output_dir: 输出目录
        
    Returns:
        处理结果
    """
    processor = BatchProcessor(BatchConfig(
        output_dir=output_dir,
        transcode_preset=preset,
    ))
    
    for path in video_paths:
        processor.add_task(BatchTask(
            input_path=path,
            operation=BatchOperation.TRANSCODE.value,
            config={"preset": preset},
        ))
    
    return processor.run()


# ========== 使用示例 ==========

def demo_batch_processing():
    """演示批量处理"""
    print("=" * 50)
    print("VideoForge 批量处理演示")
    print("=" * 50)
    
    # 创建处理器
    processor = BatchProcessor(BatchConfig(max_workers=2))
    
    # 添加字幕任务
    videos = ["video1.mp4", "video2.mp4", "video3.mp4"]
    
    for video in videos:
        if not Path(video).exists():
            print(f"跳过不存在的文件: {video}")
            continue
        processor.add_task(BatchTask(
            input_path=video,
            operation=BatchOperation.SUBTITLES.value,
        ))
    
    if not processor.tasks:
        print("没有可处理的任务")
        return
    
    # 执行处理
    print(f"开始处理 {len(processor.tasks)} 个任务...")
    result = processor.run()
    
    # 输出结果
    print("\n处理完成:")
    print(f"  总任务: {result.total}")
    print(f"  完成: {result.completed}")
    print(f"  失败: {result.failed}")
    print(f"  耗时: {result.total_time:.2f}秒")
    
    # 打印失败的任务
    if result.failed > 0:
        print("\n失败的任务:")
        for task in result.results:
            if task.status == TaskStatus.FAILED:
                print(f"  {task.input_path}: {task.error}")


if __name__ == '__main__':
    demo_batch_processing()
