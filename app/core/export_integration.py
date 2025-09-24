#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
导出系统集成
将完整的导出系统集成到CineAIStudio应用程序中
"""

import os
import json
import time
from typing import Dict, List, Optional, Any
import logging

from PyQt6.QtCore import QObject, pyqtSignal

from .logger import Logger
from .event_system import EventBus
from .application import Application
from .project_export_manager import ProjectExportManager, ProjectExportConfig
from ..export.export_system import ExportSystem
from ..export.jianying_draft_generator import JianyingDraftGenerator
from ..export.performance_optimizer import ExportOptimizer, ExportOptimizationConfig, OptimizationLevel
from ..services.export_service import ExportService, ExportServiceMode


class ExportIntegration(QObject):
    """导出系统集成"""

    # 信号定义
    export_system_ready = pyqtSignal()
    export_system_error = pyqtSignal(str)

    def __init__(self, application: Application):
        super().__init__()
        self.application = application
        self.logger = Logger(__name__)
        self.event_system = EventBus()

        # 导出系统组件
        self.export_system = None
        self.export_service = None
        self.performance_optimizer = None
        self.project_export_manager = None

        # 配置文件路径
        self.config_dir = os.path.join(os.path.expanduser("~"), ".cineaistudio", "export")
        self.presets_file = os.path.join(self.config_dir, "export_presets.json")
        self.settings_file = os.path.join(self.config_dir, "export_settings.json")

        # 初始化状态
        self.is_initialized = False

    def initialize(self) -> bool:
        """初始化导出系统"""
        try:
            self.logger.info("Initializing export system integration")

            # 创建配置目录
            os.makedirs(self.config_dir, exist_ok=True)

            # 初始化各个组件
            self._initialize_export_system()
            self._initialize_export_service()
            self._initialize_performance_optimizer()
            self._initialize_project_export_manager()

            # 加载配置
            self._load_configurations()

            # 连接信号
            self._connect_signals()

            # 启动服务
            self._start_services()

            # 集成到应用程序
            self._integrate_with_application()

            self.is_initialized = True
            self.logger.info("Export system integration initialized successfully")
            self.export_system_ready.emit()

            return True

        except Exception as e:
            error_msg = f"Failed to initialize export system: {e}"
            self.logger.error(error_msg)
            self.export_system_error.emit(error_msg)
            return False

    def _initialize_export_system(self):
        """初始化导出系统"""
        self.export_system = ExportSystem()
        self.logger.info("Export system initialized")

    def _initialize_export_service(self):
        """初始化导出服务"""
        self.export_service = ExportService()
        self.export_service.start()
        self.logger.info("Export service started")

    def _initialize_performance_optimizer(self):
        """初始化性能优化器"""
        self.performance_optimizer = ExportOptimizer()
        self.performance_optimizer.initialize()
        self.logger.info("Performance optimizer initialized")

    def _initialize_project_export_manager(self):
        """初始化项目导出管理器"""
        self.project_export_manager = ProjectExportManager(
            self.export_system,
            self.export_service
        )
        self.logger.info("Project export manager initialized")

    def _load_configurations(self):
        """加载配置文件"""
        try:
            # 加载导出预设
            if os.path.exists(self.presets_file):
                self.export_system.preset_manager.load_presets(self.presets_file)
                self.logger.info(f"Loaded export presets from {self.presets_file}")

            # 加载设置
            if os.path.exists(self.settings_file):
                self._load_settings()
                self.logger.info(f"Loaded export settings from {self.settings_file}")

        except Exception as e:
            self.logger.warning(f"Failed to load configurations: {e}")

    def _load_settings(self):
        """加载设置"""
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)

            # 应用项目导出配置
            if 'project_export' in settings:
                project_config = ProjectExportConfig(**settings['project_export'])
                self.project_export_manager.update_config(project_config)

            # 应用性能优化配置
            if 'performance_optimization' in settings:
                perf_config_data = settings['performance_optimization']
                perf_config = ExportOptimizationConfig(
                    optimization_level=OptimizationLevel(perf_config_data.get('optimization_level', 'auto')),
                    max_cpu_usage=perf_config_data.get('max_cpu_usage', 80.0),
                    max_memory_usage=perf_config_data.get('max_memory_usage', 70.0),
                    max_concurrent_tasks=perf_config_data.get('max_concurrent_tasks', 2),
                    use_gpu_acceleration=perf_config_data.get('use_gpu_acceleration', True),
                    use_multi_threading=perf_config_data.get('use_multi_threading', True),
                    enable_io_optimization=perf_config_data.get('enable_io_optimization', True),
                    enable_memory_optimization=perf_config_data.get('enable_memory_optimization', True)
                )
                self.performance_optimizer.update_config(perf_config)

        except Exception as e:
            self.logger.error(f"Failed to load settings: {e}")

    def _connect_signals(self):
        """连接信号"""
        # 连接事件系统
        self.event_system.subscribe("project_opened", self._on_project_opened)
        self.event_system.subscribe("project_closed", self._on_project_closed)
        self.event_system.subscribe("application_shutdown", self._on_application_shutdown)

        # 连接导出系统信号
        self.export_system.export_started.connect(self._on_export_started)
        self.export_system.export_completed.connect(self._on_export_completed)

    def _start_services(self):
        """启动服务"""
        # 启动性能监控
        if self.performance_optimizer:
            self.performance_optimizer.monitor.start_monitoring()

        self.logger.info("Export services started")

    def _integrate_with_application(self):
        """集成到应用程序"""
        try:
            # 设置应用程序的导出系统引用
            self.application.export_system = self.export_system
            self.application.export_service = self.export_service
            self.application.performance_optimizer = self.performance_optimizer
            self.application.project_export_manager = self.project_export_manager

            # 注册项目到导出管理器
            if hasattr(self.application, 'project_manager'):
                self._register_existing_projects()

            self.logger.info("Export system integrated with application")

        except Exception as e:
            self.logger.error(f"Failed to integrate with application: {e}")

    def _register_existing_projects(self):
        """注册现有项目到导出管理器"""
        try:
            projects = self.application.project_manager.get_projects()
            for project in projects:
                self.project_export_manager.register_project(
                    project['id'],
                    project
                )
            self.logger.info(f"Registered {len(projects)} existing projects")

        except Exception as e:
            self.logger.error(f"Failed to register existing projects: {e}")

    def save_configurations(self):
        """保存配置文件"""
        try:
            # 保存导出预设
            self.export_system.preset_manager.save_presets(self.presets_file)

            # 保存设置
            self._save_settings()

            self.logger.info("Export configurations saved")

        except Exception as e:
            self.logger.error(f"Failed to save configurations: {e}")

    def _save_settings(self):
        """保存设置"""
        try:
            settings = {
                "project_export": {
                    "default_preset_id": self.project_export_manager.config.default_preset_id,
                    "default_output_dir": self.project_export_manager.config.default_output_dir,
                    "auto_naming_pattern": self.project_export_manager.config.auto_naming_pattern,
                    "backup_enabled": self.project_export_manager.config.backup_enabled,
                    "backup_count": self.project_export_manager.config.backup_count,
                    "export_metadata": self.project_export_manager.config.export_metadata,
                    "optimize_for_platform": self.project_export_manager.config.optimize_for_platform,
                    "concurrent_exports": self.project_export_manager.config.concurrent_exports
                },
                "performance_optimization": {
                    "optimization_level": self.performance_optimizer.config.optimization_level.value,
                    "max_cpu_usage": self.performance_optimizer.config.max_cpu_usage,
                    "max_memory_usage": self.performance_optimizer.config.max_memory_usage,
                    "max_concurrent_tasks": self.performance_optimizer.config.max_concurrent_tasks,
                    "use_gpu_acceleration": self.performance_optimizer.config.use_gpu_acceleration,
                    "use_multi_threading": self.performance_optimizer.config.use_multi_threading,
                    "enable_io_optimization": self.performance_optimizer.config.enable_io_optimization,
                    "enable_memory_optimization": self.performance_optimizer.config.enable_memory_optimization
                },
                "last_saved": time.time()
            }

            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")

    def _on_project_opened(self, data: Dict[str, Any]):
        """项目打开事件处理"""
        try:
            project_id = data.get('project_id')
            project_info = data.get('project_info', {})

            if project_id and project_info:
                # 注册项目到导出管理器
                self.project_export_manager.register_project(project_id, project_info)

                # 加载项目特定的导出设置
                project_settings = self.project_export_manager.load_project_export_settings(project_id)
                if project_settings:
                    self.logger.info(f"Loaded export settings for project {project_id}")

        except Exception as e:
            self.logger.error(f"Failed to handle project opened event: {e}")

    def _on_project_closed(self, data: Dict[str, Any]):
        """项目关闭事件处理"""
        try:
            project_id = data.get('project_id')

            if project_id:
                # 保存项目特定的导出设置
                current_settings = {}  # 这里应该从UI获取当前设置
                self.project_export_manager.save_project_export_settings(project_id, current_settings)

                # 注销项目
                self.project_export_manager.unregister_project(project_id)

        except Exception as e:
            self.logger.error(f"Failed to handle project closed event: {e}")

    def _on_application_shutdown(self, data: Dict[str, Any]):
        """应用程序关闭事件处理"""
        try:
            self.shutdown()

        except Exception as e:
            self.logger.error(f"Failed to handle application shutdown event: {e}")

    def _on_export_started(self, task_id: str):
        """导出开始事件处理"""
        self.logger.info(f"Export started: {task_id}")
        self.event_system.emit("export_started", {"task_id": task_id})

    def _on_export_completed(self, task_id: str, output_path: str):
        """导出完成事件处理"""
        self.logger.info(f"Export completed: {task_id} -> {output_path}")
        self.event_system.emit("export_completed", {
            "task_id": task_id,
            "output_path": output_path
        })

    def get_export_statistics(self) -> Dict[str, Any]:
        """获取导出统计信息"""
        try:
            statistics = {
                "export_system": {},
                "project_manager": {},
                "performance": {},
                "services": {}
            }

            # 导出系统统计
            if self.export_system:
                queue_status = self.export_system.get_queue_status()
                statistics["export_system"] = {
                    "queue_size": queue_status["queue_size"],
                    "active_tasks": queue_status["active_tasks"],
                    "completed_tasks": queue_status["completed_tasks"],
                    "total_presets": len(self.export_system.get_presets())
                }

            # 项目管理器统计
            if self.project_export_manager:
                all_stats = self.project_export_manager.get_all_statistics()
                statistics["project_manager"] = all_stats

            # 性能统计
            if self.performance_optimizer:
                statistics["performance"] = self.performance_optimizer.get_performance_stats()

            # 服务统计
            if self.export_service:
                statistics["services"] = self.export_service.get_statistics()

            return statistics

        except Exception as e:
            self.logger.error(f"Failed to get export statistics: {e}")
            return {}

    def get_system_health(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        try:
            health = {
                "export_system": {"status": "healthy", "details": {}},
                "performance_optimizer": {"status": "healthy", "details": {}},
                "export_service": {"status": "healthy", "details": {}},
                "project_manager": {"status": "healthy", "details": {}}
            }

            # 检查导出系统
            if self.export_system:
                try:
                    queue_status = self.export_system.get_queue_status()
                    health["export_system"]["details"] = queue_status
                except Exception as e:
                    health["export_system"]["status"] = "error"
                    health["export_system"]["details"]["error"] = str(e)

            # 检查性能优化器
            if self.performance_optimizer:
                try:
                    perf_stats = self.performance_optimizer.get_performance_stats()
                    health["performance_optimizer"]["details"] = perf_stats
                except Exception as e:
                    health["performance_optimizer"]["status"] = "error"
                    health["performance_optimizer"]["details"]["error"] = str(e)

            # 检查导出服务
            if self.export_service:
                try:
                    service_stats = self.export_service.get_statistics()
                    health["export_service"]["details"] = service_stats
                except Exception as e:
                    health["export_service"]["status"] = "error"
                    health["export_service"]["details"]["error"] = str(e)

            # 检查项目管理器
            if self.project_export_manager:
                try:
                    manager_stats = self.project_export_manager.get_all_statistics()
                    health["project_manager"]["details"] = manager_stats
                except Exception as e:
                    health["project_manager"]["status"] = "error"
                    health["project_manager"]["details"]["error"] = str(e)

            return health

        except Exception as e:
            self.logger.error(f"Failed to get system health: {e}")
            return {"overall_status": "error", "error": str(e)}

    def optimize_system(self) -> bool:
        """优化系统"""
        try:
            # 获取性能建议
            if self.performance_optimizer:
                recommendations = self.performance_optimizer.get_resource_recommendations()

                # 应用建议
                config = ExportOptimizationConfig(OptimizationLevel.AUTO)
                self.performance_optimizer.update_config(config)

                # 清理临时文件
                self.performance_optimizer.cleanup_temp_files()

                self.logger.info("System optimization completed")
                return True

        except Exception as e:
            self.logger.error(f"Failed to optimize system: {e}")
            return False

    def create_export_report(self, output_path: str = None) -> bool:
        """创建导出系统报告"""
        try:
            if output_path is None:
                output_path = os.path.join(self.config_dir, "export_report.json")

            report = {
                "generated_at": time.time(),
                "generated_by": "CineAIStudio Export System",
                "version": "1.0",
                "statistics": self.get_export_statistics(),
                "system_health": self.get_system_health(),
                "configuration": {
                    "presets_count": len(self.export_system.get_presets()) if self.export_system else 0,
                    "active_projects": len(self.project_export_manager.project_exports) if self.project_export_manager else 0,
                    "performance_enabled": self.performance_optimizer is not None
                }
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Export report created: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create export report: {e}")
            return False

    def shutdown(self):
        """关闭导出系统"""
        try:
            self.logger.info("Shutting down export system")

            # 保存配置
            self.save_configurations()

            # 停止服务
            if self.export_service:
                self.export_service.stop()

            if self.performance_optimizer:
                self.performance_optimizer.shutdown()

            if self.export_system:
                self.export_system.shutdown()

            if self.project_export_manager:
                self.project_export_manager.shutdown()

            # 清理临时文件
            self._cleanup_temp_files()

            self.logger.info("Export system shutdown completed")

        except Exception as e:
            self.logger.error(f"Failed to shutdown export system: {e}")

    def _cleanup_temp_files(self):
        """清理临时文件"""
        try:
            temp_dir = os.path.join(self.config_dir, "temp")
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)
                self.logger.info("Cleaned up temporary files")

        except Exception as e:
            self.logger.error(f"Failed to cleanup temp files: {e}")

    def is_ready(self) -> bool:
        """检查系统是否就绪"""
        return self.is_initialized and all([
            self.export_system is not None,
            self.export_service is not None,
            self.performance_optimizer is not None,
            self.project_export_manager is not None
        ])

    def get_component(self, component_name: str):
        """获取指定组件"""
        components = {
            "export_system": self.export_system,
            "export_service": self.export_service,
            "performance_optimizer": self.performance_optimizer,
            "project_export_manager": self.project_export_manager
        }
        return components.get(component_name)


# 全局导出集成实例
export_integration = None


def initialize_export_integration(application: Application) -> ExportIntegration:
    """初始化导出系统集成"""
    global export_integration
    export_integration = ExportIntegration(application)
    export_integration.initialize()
    return export_integration


def get_export_integration() -> Optional[ExportIntegration]:
    """获取导出系统集成实例"""
    return export_integration