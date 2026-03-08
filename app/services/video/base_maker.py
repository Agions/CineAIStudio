#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
视频制作基类
统一进度跟踪和错误处理
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging


class MakerStatus(Enum):
    """制作状态"""
    IDLE = "idle"
    PREPARING = "preparing"
    PROCESSING = "processing"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class MakerProgress:
    """制作进度"""
    status: MakerStatus = MakerStatus.IDLE
    progress: float = 0.0
    current_step: str = ""
    message: str = ""
    total_steps: int = 0
    current_step_num: int = 0
    elapsed_time: float = 0.0
    eta: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update(
        self,
        progress: float = None,
        message: str = None,
        step: str = None,
    ):
        """更新进度"""
        if progress is not None:
            self.progress = progress
        if message is not None:
            self.message = message
        if step is not None:
            self.current_step = step


class BaseVideoMaker(ABC):
    """
    视频制作基类
    
    提供进度跟踪、错误处理、状态回调等通用功能
    """
    
    def __init__(self):
        self._progress = MakerProgress()
        self._progress_callback: Optional[Callable] = None
        self._cancel_requested = False
        self._start_time: Optional[datetime] = None
        self._logger = logging.getLogger(self.__class__.__name__)
        
    @property
    def progress(self) -> MakerProgress:
        """获取当前进度"""
        return self._progress
    
    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._progress.status in [
            MakerStatus.PREPARING,
            MakerStatus.PROCESSING,
            MakerStatus.RENDERING,
        ]
    
    @property
    def is_cancelled(self) -> bool:
        """是否已取消"""
        return self._progress.status == MakerStatus.CANCELLED
    
    def set_progress_callback(self, callback: Callable[[MakerProgress], None]):
        """设置进度回调"""
        self._progress_callback = callback
    
    def _emit_progress(self, **kwargs):
        """发送进度更新"""
        self._progress.update(**kwargs)
        
        if self._progress_callback:
            self._progress_callback(self._progress)
    
    def _check_cancelled(self):
        """检查是否取消"""
        if self._cancel_requested:
            self._progress.status = MakerStatus.CANCELLED
            raise asyncio.CancelledError("制作已取消")
    
    def request_cancel(self):
        """请求取消"""
        self._cancel_requested = True
        self._logger.info("Cancel requested")
    
    def reset(self):
        """重置状态"""
        self._progress = MakerProgress()
        self._cancel_requested = False
        self._start_time = None
    
    async def make(
        self,
        input_path: str,
        output_path: str,
        options: Dict[str, Any] = None,
    ) -> str:
        """
        执行制作
        
        Args:
            input_path: 输入路径
            output_path: 输出路径
            options: 选项
            
        Returns:
            输出路径
        """
        self.reset()
        self._start_time = datetime.now()
        options = options or {}
        
        try:
            self._emit_progress(
                status=MakerStatus.PREPARING,
                progress=0,
                message="准备中...",
            )
            
            # 准备阶段
            await self._prepare(input_path, output_path, options)
            self._check_cancelled()
            
            # 处理阶段
            self._emit_progress(
                status=MakerStatus.PROCESSING,
                progress=20,
                message="处理中...",
            )
            
            await self._process(input_path, output_path, options)
            self._check_cancelled()
            
            # 渲染阶段
            self._emit_progress(
                status=MakerStatus.RENDERING,
                progress=80,
                message="渲染中...",
            )
            
            await self._render(input_path, output_path, options)
            self._check_cancelled()
            
            # 完成
            self._emit_progress(
                status=MakerStatus.COMPLETED,
                progress=100,
                message="完成!",
            )
            
            return output_path
            
        except asyncio.CancelledError:
            self._emit_progress(
                status=MakerStatus.CANCELLED,
                message="已取消",
            )
            raise
            
        except Exception as e:
            self._logger.exception("制作失败")
            self._emit_progress(
                status=MakerStatus.FAILED,
                error=str(e),
                message="失败",
            )
            raise
    
    # 子类实现的方法
    
    @abstractmethod
    async def _prepare(
        self,
        input_path: str,
        output_path: str,
        options: Dict,
    ):
        """准备阶段"""
        pass
    
    @abstractmethod
    async def _process(
        self,
        input_path: str,
        output_path: str,
        options: Dict,
    ):
        """处理阶段"""
        pass
    
    @abstractmethod
    async def _render(
        self,
        input_path: str,
        output_path: str,
        options: Dict,
    ):
        """渲染阶段"""
        pass
    
    async def _estimate_time(self, progress: float) -> float:
        """估算剩余时间"""
        if not self._start_time:
            return 0
        
        elapsed = (datetime.now() - self._start_time).total_seconds()
        
        if progress > 0:
            total = elapsed / (progress / 100)
            return max(0, total - elapsed)
        return 0


class BatchVideoMaker(BaseVideoMaker):
    """批量视频制作"""
    
    def __init__(self, max_concurrent: int = 2):
        super().__init__()
        self.max_concurrent = max_concurrent
        self._results: List[Dict] = []
    
    async def make_batch(
        self,
        inputs: List[str],
        output_dir: str,
        options: Dict[str, Any] = None,
    ) -> List[Dict]:
        """
        批量制作
        
        Args:
            inputs: 输入路径列表
            output_dir: 输出目录
            options: 选项
            
        Returns:
            结果列表
        """
        self.reset()
        results = []
        
        # 使用信号量控制并发
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def process_one(idx: int, input_path: str):
            async with semaphore:
                output_path = f"{output_dir}/output_{idx}.mp4"
                try:
                    await self.make(input_path, output_path, options)
                    results.append({
                        "input": input_path,
                        "output": output_path,
                        "status": "success",
                    })
                except Exception as e:
                    results.append({
                        "input": input_path,
                        "error": str(e),
                        "status": "failed",
                    })
        
        # 并发执行
        tasks = [
            process_one(i, inp)
            for i, inp in enumerate(inputs)
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return results
