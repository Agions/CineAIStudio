#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI 视频创作 ViewModel
管理 AI 视频创作页面的状态与业务逻辑
"""

from typing import Any, Dict, List, Optional
from PyQt6.QtCore import pyqtSignal

from .base_viewmodel import BaseViewModel
from ..core.async_bridge import get_async_bridge, AsyncWorker


class AIVideoCreatorViewModel(BaseViewModel):
    """AI 视频创作 ViewModel"""

    # 专用信号
    analysis_completed = pyqtSignal(dict)       # 视频分析完成
    script_generated = pyqtSignal(str)          # 文案生成完成
    voice_generated = pyqtSignal(str)           # 配音生成完成
    export_completed = pyqtSignal(str)          # 导出完成
    progress_updated = pyqtSignal(int, str)     # 进度更新

    def __init__(self, llm_manager=None, scene_analyzer=None,
                 script_generator=None, voice_generator=None,
                 parent=None):
        super().__init__(parent)
        self._llm_manager = llm_manager
        self._scene_analyzer = scene_analyzer
        self._script_generator = script_generator
        self._voice_generator = voice_generator
        self._current_worker = None

        # 状态
        self._video_path = None
        self._analysis_result = None
        self._script = None

    def set_video(self, path: str):
        """设置待处理的视频路径"""
        self._video_path = path
        self.status_message.emit(f"已选择视频: {path}")

    def analyze_video(self):
        """分析视频内容（后台执行）"""
        if not self._video_path:
            self.error_occurred.emit("请先选择视频文件")
            return

        if not self._scene_analyzer:
            self.error_occurred.emit("场景分析服务不可用")
            return

        self.is_loading = True
        self.progress_updated.emit(0, "正在分析视频...")

        self._current_worker = AsyncWorker(
            self._do_analyze, self._video_path
        )
        self._current_worker.finished.connect(self._on_analysis_done)
        self._current_worker.error.connect(self._on_analysis_error)
        self._current_worker.start()

    def _do_analyze(self, video_path: str) -> Dict:
        """执行视频分析（在工作线程中）"""
        return self._scene_analyzer.analyze(video_path)

    def _on_analysis_done(self, result):
        """分析完成回调"""
        self._analysis_result = result
        self.is_loading = False
        self.progress_updated.emit(100, "分析完成")
        self.analysis_completed.emit(result)

    def _on_analysis_error(self, error_msg: str):
        """分析失败回调"""
        self.is_loading = False
        self.error_occurred.emit(f"视频分析失败: {error_msg}")

    def generate_script(self, style: str = "commentary",
                       custom_prompt: str = ""):
        """生成文案"""
        if not self._analysis_result:
            self.error_occurred.emit("请先分析视频")
            return

        if not self._script_generator:
            self.error_occurred.emit("文案生成服务不可用")
            return

        self.is_loading = True
        self.progress_updated.emit(0, "正在生成文案...")

        self._current_worker = AsyncWorker(
            self._do_generate_script,
            self._analysis_result, style, custom_prompt
        )
        self._current_worker.finished.connect(self._on_script_done)
        self._current_worker.error.connect(
            lambda e: self._handle_error(Exception(e), "文案生成")
        )
        self._current_worker.start()

    def _do_generate_script(self, analysis: Dict, style: str,
                           prompt: str) -> str:
        """执行文案生成"""
        return self._script_generator.generate(
            analysis=analysis, style=style, custom_prompt=prompt
        )

    def _on_script_done(self, script):
        """文案生成完成"""
        self._script = script
        self.is_loading = False
        self.progress_updated.emit(100, "文案生成完成")
        self.script_generated.emit(script)

    def cancel_current_task(self):
        """取消当前任务"""
        if self._current_worker and self._current_worker.isRunning():
            self._current_worker.terminate()
            self._current_worker.wait(3000)
            self.is_loading = False
            self.status_message.emit("任务已取消")

    def dispose(self):
        """清理"""
        self.cancel_current_task()
        super().dispose()
