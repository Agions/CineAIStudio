#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
项目导出管理器
负责项目管理与导出系统的集成，提供项目级别的导出管理功能
"""

import os
import json
import time
import shutil
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from pathlib import Path
import logging
from enum import Enum

from .logger import Logger
from .event_system import EventBus
from ..export.export_system import ExportSystem, ExportTask, ExportPreset, ExportFormat, ExportQuality
from ..export.jianying_draft_generator import JianyingDraftGenerator
from ..services.export_service import ExportService, ExportServiceMode


class ProjectExportStatus(Enum):
    """项目导出状态"""
    NOT_EXPORTED = "not_exported"
    EXPORTING = "exporting"
    EXPORTED = "exported"
    PARTIALLY_EXPORTED = "partially_exported"
    FAILED = "failed"


@dataclass
class ProjectExportInfo:
    """项目导出信息"""
    project_id: str
    project_name: str
    export_status: ProjectExportStatus = ProjectExportStatus.NOT_EXPORTED
    export_tasks: List[str] = field(default_factory=list)
    export_history: List[Dict[str, Any]] = field(default_factory=list)
    last_export_time: Optional[float] = None
    export_settings: Dict[str, Any] = field(default_factory=dict)
    output_paths: List[str] = field(default_factory=list)


@dataclass
class ProjectExportConfig:
    """项目导出配置"""
    default_preset_id: str = "youtube_1080p"
    default_output_dir: str = "./exports"
    auto_naming_pattern: str = "{project_name}_{preset_id}_{date}"
    backup_enabled: bool = True
    backup_count: int = 3
    export_metadata: bool = True
    optimize_for_platform: bool = True
    concurrent_exports: int = 2


class ProjectExportManager:
    """项目导出管理器"""

    def __init__(self, export_system: ExportSystem, export_service: ExportService):
        self.logger = Logger(__name__)
        self.export_system = export_system
        self.export_service = export_service
        self.event_system = EventBus()

        # 项目导出信息缓存
        self.project_exports: Dict[str, ProjectExportInfo] = {}

        # 配置
        self.config = ProjectExportConfig()

        # 初始化
        self._initialize_default_settings()

    def _initialize_default_settings(self):
        """初始化默认设置"""
        self.logger.info("Initializing project export manager")

        # 创建默认输出目录
        os.makedirs(self.config.default_output_dir, exist_ok=True)

        # 连接信号
        self._connect_signals()

    def _connect_signals(self):
        """连接信号"""
        self.export_system.export_started.connect(self._on_export_started)
        self.export_system.export_progress.connect(self._on_export_progress)
        self.export_system.export_completed.connect(self._on_export_completed)
        self.export_system.export_failed.connect(self._on_export_failed)

    def register_project(self, project_id: str, project_info: Dict[str, Any]) -> bool:
        """注册项目到导出管理器"""
        try:
            if project_id in self.project_exports:
                self.logger.warning(f"Project {project_id} already registered")
                return False

            project_export_info = ProjectExportInfo(
                project_id=project_id,
                project_name=project_info.get('name', 'Unknown Project'),
                export_status=ProjectExportStatus.NOT_EXPORTED
            )

            self.project_exports[project_id] = project_export_info
            self.logger.info(f"Registered project for export: {project_id}")

            # 发送事件
            self.event_system.emit("project_registered", {
                "project_id": project_id,
                "project_name": project_export_info.project_name
            })

            return True

        except Exception as e:
            self.logger.error(f"Failed to register project {project_id}: {e}")
            return False

    def unregister_project(self, project_id: str) -> bool:
        """注销项目"""
        try:
            if project_id not in self.project_exports:
                self.logger.warning(f"Project {project_id} not found")
                return False

            # 取消所有进行中的导出任务
            project_info = self.project_exports[project_id]
            for task_id in project_info.export_tasks:
                try:
                    self.export_system.cancel_export(task_id)
                except:
                    pass

            # 移除项目信息
            del self.project_exports[project_id]

            self.logger.info(f"Unregistered project: {project_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to unregister project {project_id}: {e}")
            return False

    def export_project(self,
                      project_id: str,
                      output_path: str = None,
                      preset_id: str = None,
                      config: Dict[str, Any] = None) -> Optional[str]:
        """导出单个项目"""
        try:
            # 验证项目
            if project_id not in self.project_exports:
                raise ValueError(f"Project {project_id} not registered")

            project_info = self.project_exports[project_id]

            # 使用默认设置
            if preset_id is None:
                preset_id = self.config.default_preset_id

            if output_path is None:
                output_path = self._generate_output_path(project_info, preset_id)

            # 更新项目状态
            project_info.export_status = ProjectExportStatus.EXPORTING

            # 创建导出任务
            task_id = self.export_system.export_project(
                project_id=project_id,
                output_path=output_path,
                preset_id=preset_id,
                metadata={
                    "project_name": project_info.project_name,
                    "export_manager": True,
                    "config": config or {}
                }
            )

            # 记录任务
            project_info.export_tasks.append(task_id)

            self.logger.info(f"Started export for project {project_id}: {task_id}")
            return task_id

        except Exception as e:
            self.logger.error(f"Failed to export project {project_id}: {e}")

            # 更新项目状态为失败
            if project_id in self.project_exports:
                self.project_exports[project_id].export_status = ProjectExportStatus.FAILED

            return None

    def export_project_batch(self,
                           project_id: str,
                           preset_ids: List[str],
                           output_dir: str = None) -> List[str]:
        """批量导出项目（多种格式）"""
        try:
            if project_id not in self.project_exports:
                raise ValueError(f"Project {project_id} not registered")

            project_info = self.project_exports[project_id]

            if output_dir is None:
                output_dir = self.config.default_output_dir

            task_ids = []

            for preset_id in preset_ids:
                output_path = self._generate_output_path(project_info, preset_id, output_dir)

                task_id = self.export_system.export_project(
                    project_id=project_id,
                    output_path=output_path,
                    preset_id=preset_id,
                    metadata={
                        "project_name": project_info.project_name,
                        "export_manager": True,
                        "batch_export": True
                    }
                )

                task_ids.append(task_id)
                project_info.export_tasks.append(task_id)

            # 更新状态
            project_info.export_status = ProjectExportStatus.EXPORTING

            self.logger.info(f"Started batch export for project {project_id}: {len(task_ids)} tasks")
            return task_ids

        except Exception as e:
            self.logger.error(f"Failed to batch export project {project_id}: {e}")
            return []

    def export_project_with_template(self,
                                  project_id: str,
                                  template_id: str,
                                  output_dir: str = None) -> List[str]:
        """使用模板导出项目"""
        try:
            if output_dir is None:
                output_dir = self.config.default_output_dir

            job_ids = self.export_service.export_with_template(
                project_id=project_id,
                template_id=template_id,
                output_dir=output_dir,
                project_name=self.project_exports[project_id].project_name
            )

            # 记录作业
            if project_id in self.project_exports:
                self.project_exports[project_id].export_tasks.extend(job_ids)
                self.project_exports[project_id].export_status = ProjectExportStatus.EXPORTING

            self.logger.info(f"Started template export for project {project_id}: {len(job_ids)} jobs")
            return job_ids

        except Exception as e:
            self.logger.error(f"Failed to template export project {project_id}: {e}")
            return []

    def export_jianying_draft(self,
                             project_id: str,
                             output_path: str = None,
                             draft_config: Dict[str, Any] = None) -> bool:
        """导出剪映Draft文件"""
        try:
            if project_id not in self.project_exports:
                raise ValueError(f"Project {project_id} not registered")

            project_info = self.project_exports[project_id]

            if output_path is None:
                output_path = os.path.join(
                    self.config.default_output_dir,
                    f"{project_info.project_name}_jianying_draft.json"
                )

            # 创建Draft生成器
            generator = JianyingDraftGenerator()

            # 这里需要从项目信息中提取素材和轨道信息
            # 暂时使用示例配置
            if draft_config is None:
                draft_config = {
                    "project_name": project_info.project_name,
                    "fps": 30,
                    "resolution": (1920, 1080)
                }

            # 添加示例素材（实际应用中需要从项目数据获取）
            generator.add_video_material(
                path=f"/path/to/{project_info.project_name}_main.mp4",
                name="主视频",
                duration=120
            )

            # 创建轨道
            video_track_id = generator.create_track("video")
            audio_track_id = generator.create_track("audio")

            # 生成Draft文件
            success = generator.generate_draft(
                project_name=draft_config["project_name"],
                output_path=output_path,
                fps=draft_config["fps"],
                resolution=draft_config["resolution"]
            )

            if success:
                # 记录导出历史
                export_record = {
                    "type": "jianying_draft",
                    "output_path": output_path,
                    "timestamp": time.time(),
                    "config": draft_config
                }
                project_info.export_history.append(export_record)
                project_info.output_paths.append(output_path)

                self.logger.info(f"Generated Jianying draft for project {project_id}: {output_path}")

            return success

        except Exception as e:
            self.logger.error(f"Failed to export Jianying draft for project {project_id}: {e}")
            return False

    def cancel_project_export(self, project_id: str) -> bool:
        """取消项目的所有导出任务"""
        try:
            if project_id not in self.project_exports:
                return False

            project_info = self.project_exports[project_id]
            cancelled_count = 0

            for task_id in project_info.export_tasks[:]:  # 使用副本遍历
                if self.export_system.cancel_export(task_id):
                    cancelled_count += 1
                    project_info.export_tasks.remove(task_id)

            # 更新状态
            if not project_info.export_tasks:
                project_info.export_status = ProjectExportStatus.NOT_EXPORTED

            self.logger.info(f"Cancelled {cancelled_count} export tasks for project {project_id}")
            return cancelled_count > 0

        except Exception as e:
            self.logger.error(f"Failed to cancel export for project {project_id}: {e}")
            return False

    def get_project_export_status(self, project_id: str) -> Optional[ProjectExportStatus]:
        """获取项目导出状态"""
        project_info = self.project_exports.get(project_id)
        return project_info.export_status if project_info else None

    def get_project_export_info(self, project_id: str) -> Optional[ProjectExportInfo]:
        """获取项目导出信息"""
        return self.project_exports.get(project_id)

    def get_all_projects_status(self) -> Dict[str, ProjectExportStatus]:
        """获取所有项目的导出状态"""
        return {pid: info.export_status for pid, info in self.project_exports.items()}

    def get_project_export_history(self, project_id: str) -> List[Dict[str, Any]]:
        """获取项目导出历史"""
        project_info = self.project_exports.get(project_id)
        return project_info.export_history if project_info else []

    def _generate_output_path(self,
                            project_info: ProjectExportInfo,
                            preset_id: str,
                            output_dir: str = None) -> str:
        """生成输出文件路径"""
        if output_dir is None:
            output_dir = self.config.default_output_dir

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        # 生成文件名
        filename = self.config.auto_naming_pattern.format(
            project_name=project_info.project_name,
            preset_id=preset_id,
            date=time.strftime("%Y%m%d"),
            time=time.strftime("%H%M%S")
        )

        # 确保有文件扩展名
        if not filename.endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm', '.json')):
            filename += '.mp4'  # 默认扩展名

        return os.path.join(output_dir, filename)

    def _on_export_started(self, task_id: str):
        """导出开始事件处理"""
        # 找到对应的项目
        for project_id, project_info in self.project_exports.items():
            if task_id in project_info.export_tasks:
                self.logger.info(f"Export started for project {project_id}: {task_id}")

                # 更新项目状态
                project_info.export_status = ProjectExportStatus.EXPORTING
                project_info.last_export_time = time.time()

                # 发送事件
                self.event_system.emit("project_export_started", {
                    "project_id": project_id,
                    "task_id": task_id
                })
                break

    def _on_export_progress(self, task_id: str, progress: float):
        """导出进度事件处理"""
        # 找到对应的项目
        for project_id, project_info in self.project_exports.items():
            if task_id in project_info.export_tasks:
                self.event_system.emit("project_export_progress", {
                    "project_id": project_id,
                    "task_id": task_id,
                    "progress": progress
                })
                break

    def _on_export_completed(self, task_id: str, output_path: str):
        """导出完成事件处理"""
        for project_id, project_info in self.project_exports.items():
            if task_id in project_info.export_tasks:
                # 移除完成的任务
                project_info.export_tasks.remove(task_id)

                # 记录导出历史
                export_record = {
                    "task_id": task_id,
                    "output_path": output_path,
                    "timestamp": time.time(),
                    "status": "completed"
                }
                project_info.export_history.append(export_record)
                project_info.output_paths.append(output_path)

                # 更新项目状态
                if not project_info.export_tasks:
                    project_info.export_status = ProjectExportStatus.EXPORTED
                else:
                    project_info.export_status = ProjectExportStatus.PARTIALLY_EXPORTED

                # 发送事件
                self.event_system.emit("project_export_completed", {
                    "project_id": project_id,
                    "task_id": task_id,
                    "output_path": output_path
                })

                self.logger.info(f"Export completed for project {project_id}: {output_path}")
                break

    def _on_export_failed(self, task_id: str, error_message: str):
        """导出失败事件处理"""
        for project_id, project_info in self.project_exports.items():
            if task_id in project_info.export_tasks:
                # 移除失败的任务
                project_info.export_tasks.remove(task_id)

                # 记录失败历史
                export_record = {
                    "task_id": task_id,
                    "error_message": error_message,
                    "timestamp": time.time(),
                    "status": "failed"
                }
                project_info.export_history.append(export_record)

                # 更新项目状态
                if not project_info.export_tasks:
                    project_info.export_status = ProjectExportStatus.FAILED
                else:
                    # 检查是否还有其他任务
                    active_tasks = [tid for tid in project_info.export_tasks
                                  if tid in [t.id for t in self.export_system.get_task_history()
                                           if t.status.value in ["processing", "queued", "pending"]]]
                    if not active_tasks:
                        project_info.export_status = ProjectExportStatus.PARTIALLY_EXPORTED

                # 发送事件
                self.event_system.emit("project_export_failed", {
                    "project_id": project_id,
                    "task_id": task_id,
                    "error_message": error_message
                })

                self.logger.error(f"Export failed for project {project_id}: {error_message}")
                break

    def get_project_statistics(self, project_id: str) -> Dict[str, Any]:
        """获取项目导出统计信息"""
        project_info = self.project_exports.get(project_id)
        if not project_info:
            return {}

        history = project_info.export_history

        total_exports = len(history)
        successful_exports = len([h for h in history if h.get("status") == "completed"])
        failed_exports = len([h for h in history if h.get("status") == "failed"])

        # 计算总大小（简化计算）
        total_size = sum(os.path.getsize(h.get("output_path", ""))
                        for h in history
                        if h.get("status") == "completed" and os.path.exists(h.get("output_path", "")))

        return {
            "project_id": project_id,
            "project_name": project_info.project_name,
            "current_status": project_info.export_status.value,
            "total_exports": total_exports,
            "successful_exports": successful_exports,
            "failed_exports": failed_exports,
            "success_rate": (successful_exports / total_exports * 100) if total_exports > 0 else 0,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "last_export_time": project_info.last_export_time,
            "active_tasks": len(project_info.export_tasks)
        }

    def get_all_statistics(self) -> Dict[str, Any]:
        """获取所有项目的统计信息"""
        all_stats = {
            "total_projects": len(self.project_exports),
            "projects_with_exports": 0,
            "total_exports": 0,
            "successful_exports": 0,
            "failed_exports": 0,
            "total_size_bytes": 0,
            "active_projects": 0,
            "project_statistics": []
        }

        for project_id in self.project_exports:
            stats = self.get_project_statistics(project_id)
            all_stats["project_statistics"].append(stats)

            if stats["total_exports"] > 0:
                all_stats["projects_with_exports"] += 1

            all_stats["total_exports"] += stats["total_exports"]
            all_stats["successful_exports"] += stats["successful_exports"]
            all_stats["failed_exports"] += stats["failed_exports"]
            all_stats["total_size_bytes"] += stats["total_size_bytes"]

            if stats["active_tasks"] > 0:
                all_stats["active_projects"] += 1

        return all_stats

    def cleanup_old_exports(self, max_age_days: int = 30):
        """清理旧的导出文件"""
        try:
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 3600
            cleaned_count = 0

            for project_info in self.project_exports.values():
                # 清理导出历史记录
                recent_history = []
                for record in project_info.export_history:
                    if current_time - record.get("timestamp", 0) <= max_age_seconds:
                        recent_history.append(record)
                    else:
                        # 删除旧文件
                        file_path = record.get("output_path")
                        if file_path and os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                                cleaned_count += 1
                            except:
                                pass

                project_info.export_history = recent_history

                # 清理输出路径列表
                recent_outputs = []
                for output_path in project_info.output_paths:
                    if os.path.exists(output_path):
                        recent_outputs.append(output_path)

                project_info.output_paths = recent_outputs

            self.logger.info(f"Cleaned up {cleaned_count} old export files")
            return cleaned_count

        except Exception as e:
            self.logger.error(f"Failed to cleanup old exports: {e}")
            return 0

    def backup_project_exports(self, project_id: str, backup_dir: str = None) -> bool:
        """备份项目导出文件"""
        try:
            project_info = self.project_exports.get(project_id)
            if not project_info or not project_info.output_paths:
                return False

            if backup_dir is None:
                backup_dir = os.path.join(self.config.default_output_dir, "backups", project_id)

            os.makedirs(backup_dir, exist_ok=True)

            # 生成备份文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{project_info.project_name}_exports_backup_{timestamp}.zip"
            backup_path = os.path.join(backup_dir, backup_filename)

            # 创建备份
            import zipfile
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for output_path in project_info.output_paths:
                    if os.path.exists(output_path):
                        arcname = os.path.basename(output_path)
                        zipf.write(output_path, arcname)

            self.logger.info(f"Created backup for project {project_id}: {backup_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to backup project exports {project_id}: {e}")
            return False

    def update_config(self, config: ProjectExportConfig):
        """更新配置"""
        self.config = config
        self.logger.info("Project export configuration updated")

    def save_project_export_settings(self, project_id: str, settings: Dict[str, Any]) -> bool:
        """保存项目导出设置"""
        try:
            if project_id in self.project_exports:
                self.project_exports[project_id].export_settings = settings
                self.logger.info(f"Saved export settings for project {project_id}")
                return True
            return False

        except Exception as e:
            self.logger.error(f"Failed to save export settings for project {project_id}: {e}")
            return False

    def load_project_export_settings(self, project_id: str) -> Dict[str, Any]:
        """加载项目导出设置"""
        project_info = self.project_exports.get(project_id)
        return project_info.export_settings if project_info else {}

    def export_project_report(self, project_id: str, output_path: str = None) -> bool:
        """导出项目报告"""
        try:
            project_info = self.project_exports.get(project_id)
            if not project_info:
                return False

            if output_path is None:
                output_dir = os.path.join(self.config.default_output_dir, "reports")
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, f"{project_info.project_name}_export_report.json")

            # 生成报告
            report = {
                "project_info": {
                    "id": project_info.project_id,
                    "name": project_info.project_name,
                    "export_status": project_info.export_status.value,
                    "last_export_time": project_info.last_export_time
                },
                "statistics": self.get_project_statistics(project_id),
                "export_history": project_info.export_history,
                "export_settings": project_info.export_settings,
                "output_paths": project_info.output_paths,
                "generated_at": time.time()
            }

            # 保存报告
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Generated export report for project {project_id}: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to generate export report for project {project_id}: {e}")
            return False

    def shutdown(self):
        """关闭管理器"""
        try:
            # 取消所有活动任务
            for project_id, project_info in self.project_exports.items():
                if project_info.export_tasks:
                    self.cancel_project_export(project_id)

            self.logger.info("Project export manager shutdown complete")

        except Exception as e:
            self.logger.error(f"Failed to shutdown project export manager: {e}")