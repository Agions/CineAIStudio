"""
并行处理器 (Parallel Processor)

提供视频处理的并行化能力，显著提升处理速度。

功能:
- 多线程并行处理
- 任务队列管理
- 进度跟踪
- 资源自动调度

使用示例:
    from app.services.video import ParallelProcessor
    
    processor = ParallelProcessor(max_workers=4)
    
    # 批量生成配音
    results = processor.parallel_generate_voice(
        texts=["你好", "世界", "测试"],
        output_dir="./audio"
    )
"""

import os
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable, TypeVar
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from queue import Queue
import threading


T = TypeVar('T')


@dataclass
class TaskResult:
    """任务结果"""
    task_id: str
    success: bool = True
    result: Any = None
    error: Optional[str] = None
    duration: float = 0.0


@dataclass
class ProcessingStats:
    """处理统计"""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_time: float = 0.0
    
    @property
    def success_rate(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return (self.total_tasks - self.failed_tasks) / self.total_tasks * 100
    
    @property
    def avg_task_time(self) -> float:
        if self.completed_tasks == 0:
            return 0.0
        return self.total_time / self.completed_tasks


class ParallelProcessor:
    """
    并行处理器
    
    提供多线程/多进程并行处理能力
    
    使用示例:
        processor = ParallelProcessor(max_workers=4)
        
        # 并行执行任务
        results = processor.map(
            func=process_video,
            items=video_list,
            desc="处理视频"
        )
    """
    
    def __init__(
        self,
        max_workers: Optional[int] = None,
        use_process: bool = False,
    ):
        """
        初始化并行处理器
        
        Args:
            max_workers: 最大工作线程/进程数（默认为 CPU 核心数）
            use_process: 是否使用多进程（用于 CPU 密集型任务）
        """
        self.max_workers = max_workers or os.cpu_count() or 4
        self.use_process = use_process
        
        self._executor = None
        self._progress_callback: Optional[Callable[[int, int, str], None]] = None
        self._stats = ProcessingStats()
    
    def set_progress_callback(
        self,
        callback: Callable[[int, int, str], None]
    ) -> None:
        """
        设置进度回调
        
        Args:
            callback: 回调函数 (completed, total, message)
        """
        self._progress_callback = callback
    
    def _report_progress(self, completed: int, total: int, message: str = "") -> None:
        """报告进度"""
        if self._progress_callback:
            self._progress_callback(completed, total, message)
    
    def map(
        self,
        func: Callable[[T], Any],
        items: List[T],
        desc: str = "处理中",
    ) -> List[TaskResult]:
        """
        并行执行函数
        
        Args:
            func: 要执行的函数
            items: 输入项列表
            desc: 任务描述
            
        Returns:
            结果列表
        """
        self._stats = ProcessingStats(total_tasks=len(items))
        results = []
        
        # 选择执行器
        ExecutorClass = ProcessPoolExecutor if self.use_process else ThreadPoolExecutor
        
        start_time = time.time()
        
        with ExecutorClass(max_workers=self.max_workers) as executor:
            # 提交任务
            futures = {}
            for i, item in enumerate(items):
                future = executor.submit(self._execute_task, func, item, f"task_{i}")
                futures[future] = i
            
            # 收集结果
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    result = future.result()
                    results.append((idx, result))
                    
                    if result.success:
                        self._stats.completed_tasks += 1
                    else:
                        self._stats.failed_tasks += 1
                    
                except Exception as e:
                    results.append((idx, TaskResult(
                        task_id=f"task_{idx}",
                        success=False,
                        error=str(e)
                    )))
                    self._stats.failed_tasks += 1
                
                # 报告进度
                completed = self._stats.completed_tasks + self._stats.failed_tasks
                self._report_progress(completed, len(items), desc)
        
        self._stats.total_time = time.time() - start_time
        
        # 按原始顺序排序
        results.sort(key=lambda x: x[0])
        return [r[1] for r in results]
    
    def _execute_task(
        self,
        func: Callable,
        item: Any,
        task_id: str,
    ) -> TaskResult:
        """执行单个任务"""
        start_time = time.time()
        
        try:
            result = func(item)
            return TaskResult(
                task_id=task_id,
                success=True,
                result=result,
                duration=time.time() - start_time,
            )
        except Exception as e:
            return TaskResult(
                task_id=task_id,
                success=False,
                error=str(e),
                duration=time.time() - start_time,
            )
    
    def parallel_generate_voice(
        self,
        texts: List[str],
        output_dir: str,
        voice_id: str = "zh-CN-XiaoxiaoNeural",
        rate: float = 1.0,
    ) -> List[TaskResult]:
        """
        并行生成配音
        
        Args:
            texts: 文本列表
            output_dir: 输出目录
            voice_id: 声音 ID
            rate: 语速
            
        Returns:
            结果列表
        """
        from ..ai.voice_generator import VoiceGenerator, VoiceConfig
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        generator = VoiceGenerator(provider="edge")
        config = VoiceConfig(voice_id=voice_id, rate=rate)
        
        def generate_one(args):
            idx, text = args
            audio_path = output_path / f"voice_{idx:03d}.mp3"
            result = generator.generate(text, str(audio_path), config)
            return result.audio_path
        
        items = list(enumerate(texts))
        return self.map(generate_one, items, desc="生成配音")
    
    def parallel_analyze_scenes(
        self,
        video_paths: List[str],
    ) -> List[TaskResult]:
        """
        并行分析视频场景
        
        Args:
            video_paths: 视频路径列表
            
        Returns:
            结果列表
        """
        from ..ai.scene_analyzer import SceneAnalyzer
        
        analyzer = SceneAnalyzer()
        
        def analyze_one(video_path):
            return analyzer.analyze(video_path)
        
        return self.map(analyze_one, video_paths, desc="分析场景")
    
    def parallel_export_segments(
        self,
        segments: List[Dict],
        source_video: str,
        output_dir: str,
    ) -> List[TaskResult]:
        """
        并行导出视频片段
        
        Args:
            segments: 片段配置列表 [{"start": 0, "duration": 5}, ...]
            source_video: 源视频路径
            output_dir: 输出目录
            
        Returns:
            结果列表
        """
        import subprocess
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        def export_one(args):
            idx, segment = args
            out_file = output_path / f"segment_{idx:03d}.mp4"
            
            cmd = [
                'ffmpeg', '-y',
                '-ss', str(segment['start']),
                '-t', str(segment['duration']),
                '-i', source_video,
                '-c', 'copy',
                str(out_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True)
            if result.returncode == 0:
                return str(out_file)
            else:
                raise RuntimeError(f"导出失败: {result.stderr.decode()}")
        
        items = list(enumerate(segments))
        return self.map(export_one, items, desc="导出片段")
    
    def get_stats(self) -> ProcessingStats:
        """获取处理统计"""
        return self._stats
    
    def print_stats(self) -> None:
        """打印处理统计"""
        stats = self._stats
        print("\n" + "=" * 40)
        print("并行处理统计")
        print("=" * 40)
        print(f"  总任务数: {stats.total_tasks}")
        print(f"  成功任务: {stats.completed_tasks}")
        print(f"  失败任务: {stats.failed_tasks}")
        print(f"  成功率: {stats.success_rate:.1f}%")
        print(f"  总耗时: {stats.total_time:.2f}秒")
        print(f"  平均每任务: {stats.avg_task_time:.2f}秒")
        print("=" * 40)


class TaskQueue:
    """
    任务队列
    
    支持异步任务提交和结果收集
    """
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self._queue = Queue()
        self._results = {}
        self._lock = threading.Lock()
        self._running = False
        self._workers = []
    
    def start(self) -> None:
        """启动任务队列"""
        self._running = True
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker_loop, daemon=True)
            worker.start()
            self._workers.append(worker)
    
    def stop(self) -> None:
        """停止任务队列"""
        self._running = False
        for _ in range(self.max_workers):
            self._queue.put(None)
        for worker in self._workers:
            worker.join(timeout=1)
        self._workers.clear()
    
    def submit(self, task_id: str, func: Callable, *args, **kwargs) -> None:
        """提交任务"""
        self._queue.put((task_id, func, args, kwargs))
    
    def get_result(self, task_id: str, timeout: float = None) -> Optional[TaskResult]:
        """获取任务结果"""
        start = time.time()
        while True:
            with self._lock:
                if task_id in self._results:
                    return self._results.pop(task_id)
            
            if timeout is not None and time.time() - start > timeout:
                return None
            
            time.sleep(0.1)
    
    def _worker_loop(self) -> None:
        """工作线程循环"""
        while self._running:
            try:
                item = self._queue.get(timeout=1)
                if item is None:
                    break
                
                task_id, func, args, kwargs = item
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    task_result = TaskResult(
                        task_id=task_id,
                        success=True,
                        result=result,
                        duration=time.time() - start_time,
                    )
                except Exception as e:
                    task_result = TaskResult(
                        task_id=task_id,
                        success=False,
                        error=str(e),
                        duration=time.time() - start_time,
                    )
                
                with self._lock:
                    self._results[task_id] = task_result
                    
            except Exception:
                continue


def demo_parallel():
    """演示并行处理"""
    print("=" * 50)
    print("并行处理器演示")
    print("=" * 50)
    
    processor = ParallelProcessor(max_workers=4)
    
    def on_progress(completed, total, desc):
        print(f"  [{desc}] {completed}/{total} ({completed/total*100:.0f}%)")
    
    processor.set_progress_callback(on_progress)
    
    # 模拟任务
    def slow_task(x):
        time.sleep(0.5)  # 模拟耗时操作
        return x * 2
    
    items = list(range(10))
    
    print("\n开始并行处理...")
    results = processor.map(slow_task, items, desc="计算")
    
    print("\n结果:")
    for r in results:
        print(f"  任务 {r.task_id}: {'成功' if r.success else '失败'} - {r.result}")
    
    processor.print_stats()


if __name__ == '__main__':
    demo_parallel()
