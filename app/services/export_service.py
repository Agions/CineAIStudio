#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
导出服务管理器
提供高级导出功能和API接口
"""

import os
import json
import asyncio
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging
import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..export.export_system import ExportSystem, ExportTask, ExportPreset, ExportFormat, ExportQuality
from ..export.jianying_draft_generator import JianyingDraftGenerator
from ..core.logger import Logger
from ..core.event_system import EventBus


class ExportServiceMode(Enum):
    """导出服务模式"""
    SYNC = "sync"          # 同步模式
    ASYNC = "async"        # 异步模式
    BATCH = "batch"        # 批量模式
    SCHEDULED = "scheduled"  # 定时模式


@dataclass
class ExportJob:
    """导出作业"""
    id: str
    name: str
    project_id: str
    output_path: str
    preset_id: str
    mode: ExportServiceMode
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    priority: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExportTemplate:
    """导出模板"""
    id: str
    name: str
    description: str
    preset_configs: List[Dict[str, Any]]
    output_pattern: str
    post_actions: List[Dict[str, Any]] = field(default_factory=list)
    conditions: List[Dict[str, Any]] = field(default_factory=dict)


class ExportService:
    """导出服务管理器"""

    def __init__(self):
        self.logger = Logger(__name__)
        self.export_system = ExportSystem()
        self.event_system = EventBus()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.jobs: Dict[str, ExportJob] = {}
        self.templates: Dict[str, ExportTemplate] = {}
        self.is_running = False
        self.worker_thread = None

        # 初始化
        self._initialize_templates()

    def _initialize_templates(self):
        """初始化导出模板"""
        default_templates = [
            ExportTemplate(
                id="youtube_multi_format",
                name="YouTube多格式导出",
                description="同时导出多种格式用于YouTube",
                preset_configs=[
                    {"preset_id": "youtube_1080p", "suffix": "_1080p"},
                    {"preset_id": "youtube_4k", "suffix": "_4k"}
                ],
                output_pattern="{project_name}{suffix}.mp4",
                post_actions=[
                    {"type": "upload", "platform": "youtube", "privacy": "private"}
                ]
            ),
            ExportTemplate(
                id="social_media_package",
                name="社交媒体套件",
                description="导出适合各社交媒体平台的格式",
                preset_configs=[
                    {"preset_id": "tiktok_video", "suffix": "_tiktok"},
                    {"preset_id": "instagram_reel", "suffix": "_instagram"},
                    {"preset_id": "youtube_1080p", "suffix": "_youtube"}
                ],
                output_pattern="{project_name}{suffix}.mp4"
            ),
            ExportTemplate(
                id="backup_archive",
                name="备份存档",
                description="高质量备份和存档",
                preset_configs=[
                    {"preset_id": "master_quality", "suffix": "_master"},
                    {"preset_id": "youtube_1080p", "suffix": "_preview"}
                ],
                output_pattern="{project_name}{suffix}.{ext}",
                post_actions=[
                    {"type": "compress", "format": "zip"},
                    {"type": "move", "destination": "/backup/"}
                ]
            )
        ]

        for template in default_templates:
            self.templates[template.id] = template

    def start(self):
        """启动导出服务"""
        if self.is_running:
            return

        self.is_running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        self.logger.info("Export service started")

    def stop(self):
        """停止导出服务"""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        self.export_system.shutdown()
        self.logger.info("Export service stopped")

    def _worker_loop(self):
        """工作线程主循环"""
        while self.is_running:
            try:
                # 处理作业队列
                self._process_jobs()
                threading.Event().wait(1.0)
            except Exception as e:
                self.logger.error(f"Worker loop error: {e}")
                threading.Event().wait(5.0)

    def _process_jobs(self):
        """处理作业队列"""
        # 获取待处理的作业
        pending_jobs = [job for job in self.jobs.values() if self._is_job_ready(job)]

        for job in pending_jobs:
            try:
                self._execute_job(job)
            except Exception as e:
                self.logger.error(f"Failed to execute job {job.id}: {e}")
                job.retry_count += 1
                if job.retry_count >= job.max_retries:
                    self._mark_job_failed(job, str(e))

    def _is_job_ready(self, job: ExportJob) -> bool:
        """检查作业是否准备就绪"""
        # 检查依赖
        for dep_id in job.dependencies:
            dep_job = self.jobs.get(dep_id)
            if dep_job and dep_job.metadata.get("status") != "completed":
                return False

        return True

    def _execute_job(self, job: ExportJob):
        """执行导出作业"""
        try:
            self.logger.info(f"Executing export job: {job.name} ({job.id})")
            job.metadata["status"] = "processing"
            job.metadata["started_at"] = asyncio.get_event_loop().time()

            if job.mode == ExportServiceMode.SYNC:
                self._execute_sync_job(job)
            elif job.mode == ExportServiceMode.ASYNC:
                self._execute_async_job(job)
            elif job.mode == ExportServiceMode.BATCH:
                self._execute_batch_job(job)
            elif job.mode == ExportServiceMode.SCHEDULED:
                self._execute_scheduled_job(job)

            job.metadata["status"] = "completed"
            job.metadata["completed_at"] = asyncio.get_event_loop().time()
            self.logger.info(f"Export job completed: {job.name}")

        except Exception as e:
            self.logger.error(f"Job execution failed: {e}")
            raise

    def _execute_sync_job(self, job: ExportJob):
        """执行同步作业"""
        task_id = self.export_system.export_project(
            project_id=job.project_id,
            output_path=job.output_path,
            preset_id=job.preset_id,
            metadata=job.metadata
        )

        # 等待任务完成
        while True:
            tasks = self.export_system.get_task_history()
            task = next((t for t in tasks if t.id == task_id), None)
            if task and task.status.value in ["completed", "failed"]:
                break
            threading.Event().wait(0.5)

    def _execute_async_job(self, job: ExportJob):
        """执行异步作业"""
        task_id = self.export_system.export_project(
            project_id=job.project_id,
            output_path=job.output_path,
            preset_id=job.preset_id,
            metadata=job.metadata
        )
        job.metadata["task_id"] = task_id

    def _execute_batch_job(self, job: ExportJob):
        """执行批量作业"""
        batch_configs = []

        # 根据作业参数生成批量配置
        for config in job.parameters.get("batch_configs", []):
            output_path = self._generate_output_path(
                job.output_path,
                config.get("suffix", ""),
                config.get("ext", "mp4")
            )

            batch_configs.append({
                "project_id": job.project_id,
                "output_path": output_path,
                "preset_id": config.get("preset_id", job.preset_id),
                "metadata": {**job.metadata, **config.get("metadata", {})}
            })

        task_ids = self.export_system.export_batch(batch_configs)
        job.metadata["task_ids"] = task_ids

    def _execute_scheduled_job(self, job: ExportJob):
        """执行定时作业"""
        # 检查是否到达执行时间
        scheduled_time = job.parameters.get("scheduled_time")
        if scheduled_time:
            current_time = asyncio.get_event_loop().time()
            if current_time < scheduled_time:
                return  # 还未到执行时间

        # 执行导出
        self._execute_sync_job(job)

    def _generate_output_path(self, base_path: str, suffix: str, ext: str) -> str:
        """生成输出路径"""
        if suffix:
            path_obj = Path(base_path)
            new_name = f"{path_obj.stem}{suffix}.{ext}"
            return str(path_obj.parent / new_name)
        return base_path

    def _mark_job_failed(self, job: ExportJob, error: str):
        """标记作业失败"""
        job.metadata["status"] = "failed"
        job.metadata["error"] = error
        job.metadata["failed_at"] = asyncio.get_event_loop().time()

    # 公共API方法

    def export_project(self,
                      project_id: str,
                      output_path: str,
                      preset_id: str,
                      mode: ExportServiceMode = ExportServiceMode.ASYNC,
                      **kwargs) -> str:
        """导出项目"""
        job_id = f"job_{int(asyncio.get_event_loop().time() * 1000)}"

        job = ExportJob(
            id=job_id,
            name=kwargs.get("name", f"Export {project_id}"),
            project_id=project_id,
            output_path=output_path,
            preset_id=preset_id,
            mode=mode,
            parameters=kwargs.get("parameters", {}),
            metadata=kwargs.get("metadata", {})
        )

        self.jobs[job_id] = job
        self.logger.info(f"Created export job: {job_id}")

        return job_id

    def export_with_template(self,
                           project_id: str,
                           template_id: str,
                           output_dir: str,
                           **kwargs) -> List[str]:
        """使用模板导出"""
        template = self.templates.get(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        job_ids = []

        # 为每个预设配置创建作业
        for config in template.preset_configs:
            output_path = self._generate_template_output_path(
                template.output_pattern,
                config,
                output_dir,
                kwargs.get("project_name", "project")
            )

            job_id = self.export_project(
                project_id=project_id,
                output_path=output_path,
                preset_id=config["preset_id"],
                mode=ExportServiceMode.BATCH,
                parameters={
                    "template_id": template_id,
                    "template_config": config
                },
                **kwargs
            )

            job_ids.append(job_id)

        return job_ids

    def _generate_template_output_path(self,
                                     pattern: str,
                                     config: Dict[str, Any],
                                     output_dir: str,
                                     project_name: str) -> str:
        """生成模板输出路径"""
        # 替换模式中的变量
        output_path = pattern.format(
            project_name=project_name,
            suffix=config.get("suffix", ""),
            ext=config.get("ext", "mp4")
        )

        return os.path.join(output_dir, output_path)

    def schedule_export(self,
                       project_id: str,
                       output_path: str,
                       preset_id: str,
                       scheduled_time: float,
                       **kwargs) -> str:
        """定时导出"""
        return self.export_project(
            project_id=project_id,
            output_path=output_path,
            preset_id=preset_id,
            mode=ExportServiceMode.SCHEDULED,
            parameters={"scheduled_time": scheduled_time},
            **kwargs
        )

    def create_batch_export(self,
                           project_configs: List[Dict[str, Any]],
                           output_dir: str,
                           preset_id: str,
                           **kwargs) -> str:
        """创建批量导出"""
        job_id = f"batch_{int(asyncio.get_event_loop().time() * 1000)}"

        batch_configs = []
        for config in project_configs:
            output_path = os.path.join(
                output_dir,
                f"{config['project_name']}_{preset_id}.mp4"
            )
            batch_configs.append({
                "project_id": config["project_id"],
                "output_path": output_path,
                "preset_id": preset_id,
                "metadata": config.get("metadata", {})
            })

        job = ExportJob(
            id=job_id,
            name=kwargs.get("name", "Batch Export"),
            project_id="batch",
            output_path=output_dir,
            preset_id=preset_id,
            mode=ExportServiceMode.BATCH,
            parameters={"batch_configs": batch_configs},
            metadata=kwargs.get("metadata", {})
        )

        self.jobs[job_id] = job
        return job_id

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """获取作业状态"""
        job = self.jobs.get(job_id)
        if not job:
            return {"error": "Job not found"}

        return {
            "id": job.id,
            "name": job.name,
            "status": job.metadata.get("status", "pending"),
            "progress": self._calculate_job_progress(job),
            "started_at": job.metadata.get("started_at"),
            "completed_at": job.metadata.get("completed_at"),
            "error": job.metadata.get("error"),
            "retry_count": job.retry_count
        }

    def _calculate_job_progress(self, job: ExportJob) -> float:
        """计算作业进度"""
        if job.mode == ExportServiceMode.BATCH:
            task_ids = job.metadata.get("task_ids", [])
            if not task_ids:
                return 0.0

            tasks = self.export_system.get_task_history()
            job_tasks = [t for t in tasks if t.id in task_ids]

            if not job_tasks:
                return 0.0

            total_progress = sum(t.progress for t in job_tasks)
            return total_progress / len(job_tasks)
        else:
            task_id = job.metadata.get("task_id")
            if task_id:
                tasks = self.export_system.get_task_history()
                task = next((t for t in tasks if t.id == task_id), None)
                return task.progress if task else 0.0
            return 0.0

    def cancel_job(self, job_id: str) -> bool:
        """取消作业"""
        job = self.jobs.get(job_id)
        if not job:
            return False

        try:
            if job.mode == ExportServiceMode.BATCH:
                task_ids = job.metadata.get("task_ids", [])
                for task_id in task_ids:
                    self.export_system.cancel_export(task_id)
            else:
                task_id = job.metadata.get("task_id")
                if task_id:
                    self.export_system.cancel_export(task_id)

            job.metadata["status"] = "cancelled"
            return True
        except Exception as e:
            self.logger.error(f"Failed to cancel job {job_id}: {e}")
            return False

    def get_jobs_list(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取作业列表"""
        jobs_list = []
        for job in self.jobs.values():
            jobs_list.append(self.get_job_status(job.id))

        # 按开始时间排序
        jobs_list.sort(key=lambda x: x.get("started_at", 0), reverse=True)
        return jobs_list[:limit]

    def get_templates(self) -> List[Dict[str, Any]]:
        """获取模板列表"""
        return [
            {
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "preset_count": len(template.preset_configs)
            }
            for template in self.templates.values()
        ]

    def add_template(self, template: ExportTemplate) -> bool:
        """添加模板"""
        try:
            self.templates[template.id] = template
            self.logger.info(f"Added export template: {template.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add template: {e}")
            return False

    def remove_template(self, template_id: str) -> bool:
        """删除模板"""
        if template_id in self.templates:
            del self.templates[template_id]
            return True
        return False

    def cleanup_completed_jobs(self, max_age: float = 86400):
        """清理已完成的作业"""
        current_time = asyncio.get_event_loop().time()
        jobs_to_remove = []

        for job_id, job in self.jobs.items():
            if (job.metadata.get("status") == "completed" and
                job.metadata.get("completed_at", 0) < current_time - max_age):
                jobs_to_remove.append(job_id)

        for job_id in jobs_to_remove:
            del self.jobs[job_id]

        self.logger.info(f"Cleaned up {len(jobs_to_remove)} completed jobs")

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_jobs = len(self.jobs)
        completed_jobs = len([j for j in self.jobs.values() if j.metadata.get("status") == "completed"])
        failed_jobs = len([j for j in self.jobs.values() if j.metadata.get("status") == "failed"])
        processing_jobs = len([j for j in self.jobs.values() if j.metadata.get("status") == "processing"])

        return {
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "processing_jobs": processing_jobs,
            "success_rate": (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
        }

    def validate_export_config(self, config: Dict[str, Any]) -> bool:
        """验证导出配置"""
        required_fields = ["project_id", "output_path", "preset_id"]
        for field in required_fields:
            if field not in config:
                return False

        # 验证输出路径
        output_path = config["output_path"]
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except:
                return False

        return True

    def estimate_export_time(self, project_id: str, preset_id: str) -> float:
        """估算导出时间"""
        # 这里可以实现基于历史数据的导出时间估算
        # 为演示目的，返回一个估算值
        return 300.0  # 5分钟


# 全局导出服务实例
export_service = ExportService()