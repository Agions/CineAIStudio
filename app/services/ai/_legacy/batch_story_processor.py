"""
批量剧情处理器 (Batch Story Processor)

支持同时处理多个视频文件的剧情分析任务，
具有队列管理、并发控制、进度跟踪和取消功能。
"""

import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, Future
import threading

logger = logging.getLogger(__name__)


class BatchStatus(Enum):
    """批量处理状态"""
    PENDING = "pending"           # 等待中
    PROCESSING = "processing"     # 处理中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 失败
    CANCELLED = "cancelled"     # 已取消


@dataclass
class VideoTask:
    """视频任务"""
    id: str
    video_path: str
    status: BatchStatus = BatchStatus.PENDING
    progress: float = 0.0  # 0-100
    error_message: str = ""
    result: Optional['StoryAnalysisResult'] = None  # noqa: F821
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    style: str = "narrative"
    template_id: Optional[str] = None

    @property
    def duration(self) -> float:
        """任务耗时（秒）"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0


@dataclass
class BatchResult:
    """批量处理结果"""
    batch_id: str
    total_count: int
    success_count: int = 0
    failed_count: int = 0
    total_duration: float = 0.0  # 总耗时（秒）
    results: List[VideoTask] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class BatchStoryProcessor:
    """批量剧情处理器"""

    # 默认并发数
    DEFAULT_CONCURRENCY = 2

    def __init__(
        self,
        max_concurrency: int = DEFAULT_CONCURRENCY,
        output_dir: Optional[str] = None
    ):
        """
        初始化批量处理器

        Args:
            max_concurrency: 最大并发处理数
            output_dir: 结果输出目录
        """
        self.max_concurrency = max_concurrency
        self.output_dir = Path(output_dir) if output_dir else None
        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)

        self._tasks: Dict[str, VideoTask] = {}
        self._executor: Optional[ThreadPoolExecutor] = None
        self._futures: Dict[str, Future] = {}
        self._lock = threading.Lock()
        self._cancelled = False

        logger.info(f"BatchStoryProcessor initialized (concurrency={max_concurrency})")

    def add_task(
        self,
        video_path: str,
        style: str = "narrative",
        template_id: Optional[str] = None
    ) -> str:
        """
        添加视频任务

        Args:
            video_path: 视频文件路径
            style: 剪辑风格
            template_id: 模板 ID

        Returns:
            任务 ID
        """
        import uuid

        task_id = str(uuid.uuid4())[:8]
        task = VideoTask(
            id=task_id,
            video_path=video_path,
            style=style,
            template_id=template_id
        )

        with self._lock:
            self._tasks[task_id] = task

        logger.info(f"Added task {task_id}: {os.path.basename(video_path)}")
        return task_id

    def add_tasks(
        self,
        video_paths: List[str],
        style: str = "narrative",
        template_id: Optional[str] = None
    ) -> List[str]:
        """批量添加任务"""
        task_ids = []
        for path in video_paths:
            task_id = self.add_task(path, style, template_id)
            task_ids.append(task_id)
        return task_ids

    def get_task(self, task_id: str) -> Optional[VideoTask]:
        """获取任务状态"""
        with self._lock:
            return self._tasks.get(task_id)

    def get_all_tasks(self) -> List[VideoTask]:
        """获取所有任务"""
        with self._lock:
            return list(self._tasks.values())

    def get_pending_tasks(self) -> List[VideoTask]:
        """获取等待中的任务"""
        with self._lock:
            return [t for t in self._tasks.values() if t.status == BatchStatus.PENDING]

    def get_completed_tasks(self) -> List[VideoTask]:
        """获取已完成的任务"""
        with self._lock:
            return [t for t in self._tasks.values() if t.status == BatchStatus.COMPLETED]

    def get_failed_tasks(self) -> List[VideoTask]:
        """获取失败的任务"""
        with self._lock:
            return [t for t in self._tasks.values() if t.status == BatchStatus.FAILED]

    def cancel_task(self, task_id: str) -> bool:
        """取消单个任务"""
        with self._lock:
            task = self._tasks.get(task_id)
            if task and task.status == BatchStatus.PENDING:
                task.status = BatchStatus.CANCELLED
                logger.info(f"Cancelled task {task_id}")
                return True
        return False

    def cancel_all(self):
        """取消所有任务"""
        self._cancelled = True
        with self._lock:
            for task in self._tasks.values():
                if task.status in [BatchStatus.PENDING, BatchStatus.PROCESSING]:
                    task.status = BatchStatus.CANCELLED
        logger.info("All tasks cancelled")

    def process_all(
        self,
        analyzer: 'StoryAnalyzer',  # noqa: F821
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> BatchResult:
        """
        处理所有任务

        Args:
            analyzer: StoryAnalyzer 实例
            progress_callback: 进度回调 (task_id, progress)

        Returns:
            批量处理结果
        """
        import uuid

        batch_id = str(uuid.uuid4())[:8]
        logger.info(f"Starting batch processing: {batch_id}")

        self._cancelled = False
        batch_result = BatchResult(batch_id=batch_id, total_count=len(self._tasks))

        # 启动执行器
        self._executor = ThreadPoolExecutor(max_workers=self.max_concurrency)

        # 提交所有任务
        with self._lock:
            pending_tasks = [t for t in self._tasks.values()
                          if t.status == BatchStatus.PENDING]

        futures = {}
        for task in pending_tasks:
            future = self._executor.submit(
                self._process_single,
                task.id,
                analyzer
            )
            futures[task.id] = future

        # 等待所有任务完成
        import time
        while futures:
            if self._cancelled:
                break

            # 检查完成的任务
            completed = []
            for task_id, future in futures.items():
                if future.done():
                    completed.append(task_id)

            for task_id in completed:
                try:
                    future = futures.pop(task_id)
                    future.result()  # 触发异常以确保任务完成
                except Exception as e:
                    logger.error(f"Task {task_id} failed: {e}")

                # 回调
                if progress_callback:
                    task = self.get_task(task_id)
                    if task:
                        progress_callback(task_id, 100.0)

            time.sleep(0.1)

        # 关闭执行器
        self._executor.shutdown(wait=True)
        self._executor = None

        # 汇总结果
        with self._lock:
            batch_result.results = list(self._tasks.values())
            batch_result.success_count = len([t for t in self._tasks.values()
                                             if t.status == BatchStatus.COMPLETED])
            batch_result.failed_count = len([t for t in self._tasks.values()
                                           if t.status == BatchStatus.FAILED])
            batch_result.completed_at = datetime.now()
            batch_result.total_duration = (
                batch_result.completed_at - batch_result.created_at
            ).total_seconds()

        logger.info(f"Batch processing complete: {batch_result.success_count}/{batch_result.total_count} succeeded")
        return batch_result

    def _process_single(self, task_id: str, analyzer: 'StoryAnalyzer') -> None:  # noqa: F821
        """处理单个任务"""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return

            if task.status == BatchStatus.CANCELLED:
                return

            task.status = BatchStatus.PROCESSING
            task.started_at = datetime.now()

        try:
            logger.info(f"Processing task {task_id}: {os.path.basename(task.video_path)}")

            # 使用分析器分析
            result = analyzer.analyze(task.video_path)

            # 获取剪辑建议
            cuts = analyzer.get_cut_recommendations(
                result,
                style=task.style,
                template_id=task.template_id
            )
            result.recommended_cuts = cuts

            # 更新任务
            with self._lock:
                task.result = result
                task.status = BatchStatus.COMPLETED
                task.progress = 100.0
                task.completed_at = datetime.now()

            logger.info(f"Task {task_id} completed successfully")

        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            with self._lock:
                task.status = BatchStatus.FAILED
                task.error_message = str(e)
                task.completed_at = datetime.now()

    def export_results(
        self,
        batch_result: BatchResult,
        output_dir: Optional[str] = None
    ) -> str:
        """
        导出批量结果

        Args:
            batch_result: 批量处理结果
            output_dir: 输出目录

        Returns:
            导出文件路径
        """
        import json

        output_path = output_dir or self.output_dir
        if not output_path:
            output_path = Path.home() / ".narrafiilm" / "exports"
        else:
            output_path = Path(output_path)

        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_path / f"batch_results_{batch_result.batch_id}_{timestamp}.json"

        # 转换为可序列化格式
        results_data = []
        for task in batch_result.results:
            task_data = {
                "id": task.id,
                "video_path": task.video_path,
                "video_name": os.path.basename(task.video_path),
                "status": task.status.value,
                "progress": task.progress,
                "error": task.error_message,
                "duration_seconds": task.duration,
                "style": task.style,
                "template_id": task.template_id,
            }

            if task.result:
                task_data["analysis"] = {
                    "plot_type": task.result.plot_type.value,
                    "duration": task.result.duration,
                    "summary": task.result.summary,
                    "themes": task.result.themes,
                    "segment_count": len(task.result.segments),
                    "emotional_point_count": len(task.result.emotional_curve),
                    "highlight_count": len(task.result.highlight_moments),
                    "coherence_score": task.result.coherence_score,
                    "pacing_score": task.result.pacing_score,
                    "engagement_score": task.result.engagement_score,
                }
                task_data["cuts"] = task.result.recommended_cuts

            results_data.append(task_data)

        batch_data = {
            "batch_id": batch_result.batch_id,
            "total_count": batch_result.total_count,
            "success_count": batch_result.success_count,
            "failed_count": batch_result.failed_count,
            "total_duration_seconds": batch_result.total_duration,
            "created_at": batch_result.created_at.isoformat(),
            "completed_at": batch_result.completed_at.isoformat() if batch_result.completed_at else None,
            "results": results_data
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(batch_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Exported batch results to: {output_file}")
        return str(output_file)

    def export_cuts_for_ffmpeg(
        self,
        batch_result: BatchResult,
        output_dir: Optional[str] = None
    ) -> Dict[str, str]:
        """
        导出 FFmpeg 可用的剪辑点文件

        Args:
            batch_result: 批量处理结果
            output_dir: 输出目录

        Returns:
            {task_id: file_path} 映射
        """
        output_path = output_dir or self.output_dir
        if not output_path:
            output_path = Path.home() / ".narrafiilm" / "exports"
        else:
            output_path = Path(output_path)

        output_path.mkdir(parents=True, exist_ok=True)

        files = {}
        for task in batch_result.results:
            if task.status != BatchStatus.COMPLETED or not task.result:
                continue

            # 生成 FFmpeg concat 文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_path / f"cuts_{task.id}_{timestamp}.txt"

            with open(output_file, 'w', encoding='utf-8') as f:
                for cut in task.result.recommended_cuts:
                    if cut.get("type") == "keep":
                        start = cut.get("start", 0)
                        end = cut.get("end", 0)
                        # FFmpeg concat demuxer 格式
                        f.write(f"file '{task.video_path}'\n")
                        f.write(f"inpoint={start}\n")
                        f.write(f"outpoint={end}\n")

            files[task.id] = str(output_file)

        return files

    def clear_completed(self):
        """清除已完成的任务"""
        with self._lock:
            completed_ids = [
                tid for tid, t in self._tasks.items()
                if t.status in [BatchStatus.COMPLETED, BatchStatus.FAILED, BatchStatus.CANCELLED]
            ]
            for tid in completed_ids:
                del self._tasks[tid]

        logger.info(f"Cleared {len(completed_ids)} completed tasks")
