#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio 云端存储集成模块
提供完整的云端存储系统集成方案，与现有系统的无缝对接
"""

import json
import logging
import os
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from .cloud_storage_manager import CloudStorageManager, CloudStorageConfig, FileMetadata, SyncStatus
from .file_sync_engine import FileSyncEngine, SyncMode, ConflictResolution
from .performance_optimizer import PerformanceOptimizer, CacheLevel, CompressionAlgorithm
from .security_manager import SecurityManager, SecurityPolicy, EncryptionAlgorithm, AccessLevel, Permission

from ..project_manager import ProjectManager, Project
from ..config_manager import ConfigManager


class CloudIntegrationStatus(Enum):
    """云端集成状态"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    SYNCING = "syncing"
    ERROR = "error"


@dataclass
class CloudIntegrationConfig:
    """云端集成配置"""
    enabled: bool = False
    auto_sync: bool = True
    sync_interval: int = 300  # 5分钟
    sync_mode: str = "bidirectional"
    conflict_resolution: str = "newer_wins"
    enable_compression: bool = True
    enable_encryption: bool = True
    cache_level: str = "hybrid"
    max_concurrent_transfers: int = 4
    enable_cdn: bool = True
    backup_enabled: bool = True
    backup_interval: int = 3600  # 1小时
    version_control_enabled: bool = True
    max_versions: int = 10


class CloudStorageIntegration(QObject):
    """云端存储集成"""

    # 信号定义
    integration_status_changed = pyqtSignal(CloudIntegrationStatus)    # 集成状态变化
    project_sync_started = pyqtSignal(str)                           # 项目同步开始
    project_sync_progress = pyqtSignal(str, float)                    # 项目同步进度
    project_sync_completed = pyqtSignal(str)                          # 项目同步完成
    project_sync_failed = pyqtSignal(str, str)                        # 项目同步失败
    backup_created = pyqtSignal(str)                                  # 备份创建完成
    backup_restored = pyqtSignal(str)                                 # 备份恢复完成
    version_created = pyqtSignal(str, int)                            # 版本创建完成
    storage_quota_updated = pyqtSignal(dict)                          # 存储配额更新
    error_occurred = pyqtSignal(str, str)                             # 错误发生

    def __init__(self, project_manager: ProjectManager, config_manager: ConfigManager):
        super().__init__()

        self.project_manager = project_manager
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)

        # 集成状态
        self.status = CloudIntegrationStatus.DISCONNECTED
        self.integration_config = CloudIntegrationConfig()

        # 核心组件
        self.cloud_manager: Optional[CloudStorageManager] = None
        self.sync_engine: Optional[FileSyncEngine] = None
        self.performance_optimizer: Optional[PerformanceOptimizer] = None
        self.security_manager: Optional[SecurityManager] = None

        # 项目云端映射
        self.project_cloud_mappings: Dict[str, Dict[str, Any]] = {}

        # 同步统计
        self.sync_statistics = {
            'total_projects': 0,
            'synced_projects': 0,
            'failed_projects': 0,
            'last_sync': None,
            'total_size': 0,
            'synced_size': 0
        }

        # 初始化集成
        self._initialize_integration()

        # 启动后台任务
        self._start_background_tasks()

    def _initialize_integration(self):
        """初始化云端存储集成"""
        try:
            # 加载配置
            self._load_integration_config()

            if not self.integration_config.enabled:
                self.logger.info("Cloud storage integration is disabled")
                return

            # 初始化云端存储配置
            cloud_config = self._create_cloud_storage_config()

            # 初始化云端存储管理器
            self.cloud_manager = CloudStorageManager(cloud_config)

            # 初始化同步引擎
            sync_root = os.path.expanduser("~/CineAIStudio/CloudSync")
            self.sync_engine = FileSyncEngine(self.cloud_manager, sync_root)

            # 初始化性能优化器
            self.performance_optimizer = PerformanceOptimizer(self.cloud_manager)

            # 初始化安全管理器
            self.security_manager = SecurityManager()

            # 连接信号
            self._connect_signals()

            # 设置连接状态
            self.status = CloudIntegrationStatus.CONNECTED
            self.integration_status_changed.emit(self.status)

            self.logger.info("Cloud storage integration initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize cloud storage integration: {e}")
            self.status = CloudIntegrationStatus.ERROR
            self.integration_status_changed.emit(self.status)
            self.error_occurred.emit("INIT_ERROR", str(e))

    def _load_integration_config(self):
        """加载集成配置"""
        try:
            config = self.config_manager.get('cloud_storage', {})

            self.integration_config = CloudIntegrationConfig(
                enabled=config.get('enabled', False),
                auto_sync=config.get('auto_sync', True),
                sync_interval=config.get('sync_interval', 300),
                sync_mode=config.get('sync_mode', 'bidirectional'),
                conflict_resolution=config.get('conflict_resolution', 'newer_wins'),
                enable_compression=config.get('enable_compression', True),
                enable_encryption=config.get('enable_encryption', True),
                cache_level=config.get('cache_level', 'hybrid'),
                max_concurrent_transfers=config.get('max_concurrent_transfers', 4),
                enable_cdn=config.get('enable_cdn', True),
                backup_enabled=config.get('backup_enabled', True),
                backup_interval=config.get('backup_interval', 3600),
                version_control_enabled=config.get('version_control_enabled', True),
                max_versions=config.get('max_versions', 10)
            )

        except Exception as e:
            self.logger.error(f"Failed to load integration config: {e}")
            self.integration_config = CloudIntegrationConfig()

    def _create_cloud_storage_config(self) -> CloudStorageConfig:
        """创建云端存储配置"""
        config = CloudStorageConfig()

        # 从配置管理器加载云端存储配置
        cloud_config = self.config_manager.get('cloud_storage_backend', {})

        # AWS S3 配置
        if cloud_config.get('backend') == 'aws_s3':
            config.aws_access_key_id = cloud_config.get('aws_access_key_id')
            config.aws_secret_access_key = cloud_config.get('aws_secret_access_key')
            config.aws_region = cloud_config.get('aws_region', 'us-east-1')
            config.aws_s3_bucket = cloud_config.get('aws_s3_bucket', 'cineaistudio-storage')

        # 同步配置
        config.sync_chunk_size = cloud_config.get('sync_chunk_size', 64 * 1024 * 1024)
        config.max_concurrent_uploads = self.integration_config.max_concurrent_transfers
        config.max_concurrent_downloads = self.integration_config.max_concurrent_transfers
        config.enable_compression = self.integration_config.enable_compression
        config.enable_encryption = self.integration_config.enable_encryption
        config.auto_sync = self.integration_config.auto_sync
        config.sync_interval = self.integration_config.sync_interval

        # 性能配置
        config.enable_cdn = self.integration_config.enable_cdn
        config.cache_size = 10 * 1024 * 1024 * 1024  # 10GB

        return config

    def _connect_signals(self):
        """连接信号"""
        if self.cloud_manager:
            self.cloud_manager.sync_started.connect(self._on_sync_started)
            self.cloud_manager.sync_progress.connect(self._on_sync_progress)
            self.cloud_manager.sync_completed.connect(self._on_sync_completed)
            self.cloud_manager.sync_failed.connect(self._on_sync_failed)

        if self.sync_engine:
            # 连接同步引擎信号
            pass

        if self.security_manager:
            self.security_manager.security_event.connect(self._on_security_event)

    def _start_background_tasks(self):
        """启动后台任务"""
        # 启动定期同步
        if self.integration_config.auto_sync:
            self.auto_sync_timer = QTimer()
            self.auto_sync_timer.timeout.connect(self._auto_sync_projects)
            self.auto_sync_timer.start(self.integration_config.sync_interval * 1000)

        # 启动定期备份
        if self.integration_config.backup_enabled:
            self.backup_timer = QTimer()
            self.backup_timer.timeout.connect(self._auto_backup_projects)
            self.backup_timer.start(self.integration_config.backup_interval * 1000)

        # 启动状态监控
        self.status_monitor_timer = QTimer()
        self.status_monitor_timer.timeout.connect(self._monitor_status)
        self.status_monitor_timer.start(30000)  # 30秒

    def enable_cloud_integration(self, config: Dict[str, Any]) -> bool:
        """启用云端集成"""
        try:
            # 更新配置
            self.integration_config.enabled = True
            for key, value in config.items():
                if hasattr(self.integration_config, key):
                    setattr(self.integration_config, key, value)

            # 保存配置
            self._save_integration_config()

            # 重新初始化集成
            self._initialize_integration()

            return True

        except Exception as e:
            self.logger.error(f"Failed to enable cloud integration: {e}")
            self.error_occurred.emit("ENABLE_ERROR", str(e))
            return False

    def disable_cloud_integration(self) -> bool:
        """禁用云端集成"""
        try:
            self.integration_config.enabled = False
            self._save_integration_config()

            # 清理资源
            self._cleanup_integration()

            self.status = CloudIntegrationStatus.DISCONNECTED
            self.integration_status_changed.emit(self.status)

            return True

        except Exception as e:
            self.logger.error(f"Failed to disable cloud integration: {e}")
            self.error_occurred.emit("DISABLE_ERROR", str(e))
            return False

    def _cleanup_integration(self):
        """清理集成资源"""
        try:
            if self.cloud_manager:
                self.cloud_manager.cleanup()

            if self.sync_engine:
                self.sync_engine.cleanup()

            if self.performance_optimizer:
                self.performance_optimizer.cleanup()

            if self.security_manager:
                self.security_manager.cleanup()

            # 停止定时器
            if hasattr(self, 'auto_sync_timer'):
                self.auto_sync_timer.stop()

            if hasattr(self, 'backup_timer'):
                self.backup_timer.stop()

            if hasattr(self, 'status_monitor_timer'):
                self.status_monitor_timer.stop()

        except Exception as e:
            self.logger.error(f"Failed to cleanup integration: {e}")

    def _save_integration_config(self):
        """保存集成配置"""
        try:
            config = {
                'enabled': self.integration_config.enabled,
                'auto_sync': self.integration_config.auto_sync,
                'sync_interval': self.integration_config.sync_interval,
                'sync_mode': self.integration_config.sync_mode,
                'conflict_resolution': self.integration_config.conflict_resolution,
                'enable_compression': self.integration_config.enable_compression,
                'enable_encryption': self.integration_config.enable_encryption,
                'cache_level': self.integration_config.cache_level,
                'max_concurrent_transfers': self.integration_config.max_concurrent_transfers,
                'enable_cdn': self.integration_config.enable_cdn,
                'backup_enabled': self.integration_config.backup_enabled,
                'backup_interval': self.integration_config.backup_interval,
                'version_control_enabled': self.integration_config.version_control_enabled,
                'max_versions': self.integration_config.max_versions
            }

            self.config_manager.set('cloud_storage', config)
            self.config_manager.save()

        except Exception as e:
            self.logger.error(f"Failed to save integration config: {e}")

    def sync_project(self, project_id: str, force: bool = False) -> bool:
        """同步项目"""
        try:
            if not self.cloud_manager or not self.sync_engine:
                self.error_occurred.emit("SYNC_ERROR", "Cloud storage not initialized")
                return False

            project = self.project_manager.get_project(project_id)
            if not project:
                self.error_occurred.emit("SYNC_ERROR", f"Project not found: {project_id}")
                return False

            self.project_sync_started.emit(project_id)

            # 设置同步模式
            sync_mode = SyncMode(self.integration_config.sync_mode)

            # 设置冲突解决策略
            conflict_resolution = ConflictResolution(self.integration_config.conflict_resolution)

            if self.sync_engine:
                self.sync_engine.set_sync_mode(sync_mode)
                self.sync_engine.set_conflict_resolution(conflict_resolution)

            # 创建项目云端目录
            cloud_path = self._get_project_cloud_path(project)

            # 同步项目文件
            success = self._sync_project_files(project, cloud_path)

            if success:
                # 更新项目映射
                self.project_cloud_mappings[project_id] = {
                    'cloud_path': cloud_path,
                    'last_sync': datetime.now().isoformat(),
                    'sync_status': 'synced'
                }

                # 更新统计
                self._update_sync_statistics()

                self.project_sync_completed.emit(project_id)
                return True
            else:
                self.project_sync_failed.emit(project_id, "Sync failed")
                return False

        except Exception as e:
            self.logger.error(f"Failed to sync project {project_id}: {e}")
            self.project_sync_failed.emit(project_id, str(e))
            return False

    def _sync_project_files(self, project: Project, cloud_path: str) -> bool:
        """同步项目文件"""
        try:
            # 同步项目文件
            project_files = [
                os.path.join(project.path, 'project.json'),
                *[os.path.join(project.path, f'media/{media_id}')
                  for media_id in project.media_files.keys()],
                *[os.path.join(project.path, f'assets/{asset}')
                  for asset in os.listdir(os.path.join(project.path, 'assets'))
                  if os.path.isfile(os.path.join(project.path, f'assets/{asset}'))]
            ]

            # 启用加密
            if self.integration_config.enable_encryption and self.security_manager:
                for file_path in project_files:
                    if os.path.exists(file_path):
                        encrypted_path = file_path + '.encrypted'
                        self.security_manager.encrypt_file(file_path, encrypted_path)

            # 上传文件到云端
            if self.cloud_manager:
                for file_path in project_files:
                    if os.path.exists(file_path):
                        relative_path = os.path.relpath(file_path, project.path)
                        remote_path = os.path.join(cloud_path, relative_path)
                        self.cloud_manager.upload_file(file_path, remote_path)

            return True

        except Exception as e:
            self.logger.error(f"Failed to sync project files: {e}")
            return False

    def _get_project_cloud_path(self, project: Project) -> str:
        """获取项目云端路径"""
        return f"projects/{project.metadata.name}_{project.id[:8]}"

    def create_project_backup(self, project_id: str) -> Optional[str]:
        """创建项目备份"""
        try:
            project = self.project_manager.get_project(project_id)
            if not project:
                self.error_occurred.emit("BACKUP_ERROR", f"Project not found: {project_id}")
                return None

            # 创建备份
            backup_path = project.create_backup()
            if not backup_path:
                self.error_occurred.emit("BACKUP_ERROR", "Failed to create backup")
                return None

            # 上传备份到云端
            if self.cloud_manager:
                cloud_backup_path = f"backups/{project.metadata.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self.cloud_manager.upload_file(backup_path, cloud_backup_path)

            self.backup_created.emit(project_id)
            return backup_path

        except Exception as e:
            self.logger.error(f"Failed to create backup for project {project_id}: {e}")
            self.error_occurred.emit("BACKUP_ERROR", str(e))
            return None

    def restore_project_backup(self, backup_path: str, project_id: Optional[str] = None) -> Optional[str]:
        """恢复项目备份"""
        try:
            # 从云端下载备份
            if self.cloud_manager:
                local_backup_path = os.path.join(os.path.expanduser("~"), "CineAIStudio", "temp_backup.zip")
                # 这里需要实现从云端下载备份的逻辑

            # 恢复项目
            if project_id:
                project = self.project_manager.get_project(project_id)
                if project:
                    # 恢复到现有项目
                    pass
            else:
                # 创建新项目
                pass

            self.backup_restored.emit(project_id or "new_project")
            return project_id or "new_project"

        except Exception as e:
            self.logger.error(f"Failed to restore backup from {backup_path}: {e}")
            self.error_occurred.emit("RESTORE_ERROR", str(e))
            return None

    def create_project_version(self, project_id: str, version_name: str) -> Optional[int]:
        """创建项目版本"""
        try:
            project = self.project_manager.get_project(project_id)
            if not project:
                self.error_occurred.emit("VERSION_ERROR", f"Project not found: {project_id}")
                return None

            # 保存项目当前状态
            project.save()

            # 创建版本快照
            version_path = os.path.join(project.path, 'versions', f"v{len(self._get_project_versions(project_id)) + 1}")
            os.makedirs(version_path, exist_ok=True)

            # 复制项目文件
            import shutil
            shutil.copy2(os.path.join(project.path, 'project.json'), version_path)

            # 更新版本信息
            versions = self._get_project_versions(project_id)
            version_number = len(versions) + 1

            self.version_created.emit(project_id, version_number)
            return version_number

        except Exception as e:
            self.logger.error(f"Failed to create version for project {project_id}: {e}")
            self.error_occurred.emit("VERSION_ERROR", str(e))
            return None

    def _get_project_versions(self, project_id: str) -> List[Dict[str, Any]]:
        """获取项目版本"""
        project = self.project_manager.get_project(project_id)
        if not project:
            return []

        versions = []
        version_dir = os.path.join(project.path, 'versions')
        if os.path.exists(version_dir):
            for version_name in os.listdir(version_dir):
                version_path = os.path.join(version_dir, version_name)
                if os.path.isdir(version_path):
                    versions.append({
                        'name': version_name,
                        'path': version_path,
                        'created': datetime.fromtimestamp(os.path.getctime(version_path)).isoformat()
                    })

        return sorted(versions, key=lambda x: x['created'], reverse=True)

    def _auto_sync_projects(self):
        """自动同步项目"""
        try:
            if not self.integration_config.auto_sync:
                return

            # 获取所有项目
            projects = self.project_manager.get_all_projects()

            for project in projects:
                # 检查是否需要同步
                if self._should_sync_project(project):
                    self.sync_project(project.id)

        except Exception as e:
            self.logger.error(f"Auto sync failed: {e}")

    def _auto_backup_projects(self):
        """自动备份项目"""
        try:
            if not self.integration_config.backup_enabled:
                return

            # 获取所有项目
            projects = self.project_manager.get_all_projects()

            for project in projects:
                # 检查是否需要备份
                if self._should_backup_project(project):
                    self.create_project_backup(project.id)

        except Exception as e:
            self.logger.error(f"Auto backup failed: {e}")

    def _should_sync_project(self, project: Project) -> bool:
        """检查是否需要同步项目"""
        try:
            if project.id in self.project_cloud_mappings:
                mapping = self.project_cloud_mappings[project.id]
                last_sync = datetime.fromisoformat(mapping['last_sync'])
                # 如果项目在最后同步后有修改，则需要同步
                return project.metadata.modified_at > last_sync
            else:
                # 新项目需要同步
                return True
        except Exception as e:
            self.logger.error(f"Failed to check if project should sync: {e}")
            return False

    def _should_backup_project(self, project: Project) -> bool:
        """检查是否需要备份项目"""
        try:
            # 检查上次备份时间
            last_backup = self._get_last_backup_time(project.id)
            if not last_backup:
                return True

            # 如果距离上次备份超过间隔时间，则需要备份
            time_since_last_backup = (datetime.now() - last_backup).total_seconds()
            return time_since_last_backup > self.integration_config.backup_interval

        except Exception as e:
            self.logger.error(f"Failed to check if project should backup: {e}")
            return False

    def _get_last_backup_time(self, project_id: str) -> Optional[datetime]:
        """获取上次备份时间"""
        try:
            project = self.project_manager.get_project(project_id)
            if not project:
                return None

            backup_dir = os.path.join(project.path, 'backups')
            if not os.path.exists(backup_dir):
                return None

            # 获取最新的备份
            backups = []
            for backup_name in os.listdir(backup_dir):
                backup_path = os.path.join(backup_dir, backup_name)
                if os.path.isdir(backup_path):
                    backups.append(backup_path)

            if not backups:
                return None

            latest_backup = max(backups, key=os.path.getctime)
            return datetime.fromtimestamp(os.path.getctime(latest_backup))

        except Exception as e:
            self.logger.error(f"Failed to get last backup time: {e}")
            return None

    def _monitor_status(self):
        """监控状态"""
        try:
            # 更新存储统计
            if self.cloud_manager:
                storage_stats = self.cloud_manager.get_storage_stats()
                self.storage_quota_updated.emit(storage_stats)

            # 检查连接状态
            self._check_connection_status()

        except Exception as e:
            self.logger.error(f"Status monitoring failed: {e}")

    def _check_connection_status(self):
        """检查连接状态"""
        try:
            # 检查云端存储连接状态
            if self.cloud_manager:
                # 这里可以实现连接检查逻辑
                pass

        except Exception as e:
            self.logger.error(f"Connection status check failed: {e}")

    def _update_sync_statistics(self):
        """更新同步统计"""
        try:
            projects = self.project_manager.get_all_projects()
            self.sync_statistics['total_projects'] = len(projects)
            self.sync_statistics['synced_projects'] = len(self.project_cloud_mappings)
            self.sync_statistics['last_sync'] = datetime.now().isoformat()

            # 计算总大小
            total_size = 0
            synced_size = 0
            for project in projects:
                project_size = self._calculate_project_size(project)
                total_size += project_size
                if project.id in self.project_cloud_mappings:
                    synced_size += project_size

            self.sync_statistics['total_size'] = total_size
            self.sync_statistics['synced_size'] = synced_size

        except Exception as e:
            self.logger.error(f"Failed to update sync statistics: {e}")

    def _calculate_project_size(self, project: Project) -> int:
        """计算项目大小"""
        try:
            total_size = 0
            for root, dirs, files in os.walk(project.path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
            return total_size
        except Exception as e:
            self.logger.error(f"Failed to calculate project size: {e}")
            return 0

    def get_sync_statistics(self) -> Dict[str, Any]:
        """获取同步统计信息"""
        return self.sync_statistics.copy()

    def get_project_sync_status(self, project_id: str) -> Dict[str, Any]:
        """获取项目同步状态"""
        if project_id in self.project_cloud_mappings:
            return self.project_cloud_mappings[project_id].copy()
        else:
            return {
                'sync_status': 'not_synced',
                'last_sync': None,
                'cloud_path': None
            }

    def get_available_backups(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取可用备份"""
        try:
            backups = []

            if project_id:
                project = self.project_manager.get_project(project_id)
                if project:
                    backup_dir = os.path.join(project.path, 'backups')
                    if os.path.exists(backup_dir):
                        for backup_name in os.listdir(backup_dir):
                            backup_path = os.path.join(backup_dir, backup_name)
                            if os.path.isdir(backup_path):
                                backups.append({
                                    'name': backup_name,
                                    'path': backup_path,
                                    'project_id': project_id,
                                    'created': datetime.fromtimestamp(os.path.getctime(backup_path)).isoformat(),
                                    'size': self._get_directory_size(backup_path)
                                })

            # 按创建时间排序
            return sorted(backups, key=lambda x: x['created'], reverse=True)

        except Exception as e:
            self.logger.error(f"Failed to get available backups: {e}")
            return []

    def _get_directory_size(self, directory: str) -> int:
        """获取目录大小"""
        try:
            total_size = 0
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
            return total_size
        except Exception as e:
            self.logger.error(f"Failed to get directory size: {e}")
            return 0

    def get_project_versions(self, project_id: str) -> List[Dict[str, Any]]:
        """获取项目版本"""
        return self._get_project_versions(project_id)

    def configure_cloud_storage(self, config: Dict[str, Any]) -> bool:
        """配置云端存储"""
        try:
            # 保存配置
            self.config_manager.set('cloud_storage_backend', config)
            self.config_manager.save()

            # 重新初始化集成
            self._cleanup_integration()
            self._initialize_integration()

            return True

        except Exception as e:
            self.logger.error(f"Failed to configure cloud storage: {e}")
            self.error_occurred.emit("CONFIG_ERROR", str(e))
            return False

    def get_cloud_storage_status(self) -> Dict[str, Any]:
        """获取云端存储状态"""
        status = {
            'integration_enabled': self.integration_config.enabled,
            'connection_status': self.status.value,
            'cloud_manager_available': self.cloud_manager is not None,
            'sync_engine_available': self.sync_engine is not None,
            'performance_optimizer_available': self.performance_optimizer is not None,
            'security_manager_available': self.security_manager is not None
        }

        if self.cloud_manager:
            status['storage_stats'] = self.cloud_manager.get_storage_stats()

        if self.performance_optimizer:
            status['performance_stats'] = self.performance_optimizer.get_performance_stats()

        return status

    def resolve_conflict(self, conflict_id: str, resolution: str) -> bool:
        """解决冲突"""
        try:
            if self.sync_engine:
                conflict_resolution = ConflictResolution(resolution)
                return self.sync_engine.resolve_conflict(conflict_id, conflict_resolution)
            return False
        except Exception as e:
            self.logger.error(f"Failed to resolve conflict {conflict_id}: {e}")
            return False

    def get_conflicts(self) -> List[Dict[str, Any]]:
        """获取冲突列表"""
        try:
            if self.sync_engine:
                conflicts = self.sync_engine.get_conflicts()
                return [{
                    'conflict_id': conflict.conflict_id,
                    'local_path': conflict.local_path,
                    'remote_path': conflict.remote_path,
                    'conflict_type': conflict.conflict_type,
                    'detected_at': conflict.detected_at.isoformat(),
                    'resolution': conflict.resolution.value if conflict.resolution else None
                } for conflict in conflicts]
            return []
        except Exception as e:
            self.logger.error(f"Failed to get conflicts: {e}")
            return []

    def force_sync(self, project_id: str) -> bool:
        """强制同步项目"""
        return self.sync_project(project_id, force=True)

    def pause_sync(self, project_id: str) -> bool:
        """暂停同步"""
        try:
            if project_id in self.project_cloud_mappings:
                self.project_cloud_mappings[project_id]['sync_status'] = 'paused'
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to pause sync for project {project_id}: {e}")
            return False

    def resume_sync(self, project_id: str) -> bool:
        """恢复同步"""
        try:
            if project_id in self.project_cloud_mappings:
                self.project_cloud_mappings[project_id]['sync_status'] = 'synced'
                return self.sync_project(project_id)
            return False
        except Exception as e:
            self.logger.error(f"Failed to resume sync for project {project_id}: {e}")
            return False

    def cleanup_old_versions(self, project_id: str, keep_count: Optional[int] = None):
        """清理旧版本"""
        try:
            keep_count = keep_count or self.integration_config.max_versions
            versions = self._get_project_versions(project_id)

            if len(versions) > keep_count:
                # 删除最旧的版本
                for version in versions[keep_count:]:
                    version_path = version['path']
                    if os.path.exists(version_path):
                        import shutil
                        shutil.rmtree(version_path)

        except Exception as e:
            self.logger.error(f"Failed to cleanup old versions for project {project_id}: {e}")

    def cleanup_old_backups(self, project_id: str, keep_count: Optional[int] = None):
        """清理旧备份"""
        try:
            project = self.project_manager.get_project(project_id)
            if not project:
                return

            keep_count = keep_count or 10  # 默认保留10个备份
            project.cleanup_old_backups(keep_count)

        except Exception as e:
            self.logger.error(f"Failed to cleanup old backups for project {project_id}: {e}")

    def _on_sync_started(self, operation_id: str):
        """同步开始事件处理"""
        self.logger.info(f"Sync started: {operation_id}")

    def _on_sync_progress(self, operation_id: str, progress: float):
        """同步进度事件处理"""
        self.logger.debug(f"Sync progress: {operation_id} - {progress:.2%}")

    def _on_sync_completed(self, operation_id: str):
        """同步完成事件处理"""
        self.logger.info(f"Sync completed: {operation_id}")

    def _on_sync_failed(self, operation_id: str, error: str):
        """同步失败事件处理"""
        self.logger.error(f"Sync failed: {operation_id} - {error}")

    def _on_security_event(self, event_id: str, description: str):
        """安全事件处理"""
        self.logger.warning(f"Security event: {event_id} - {description}")

    def cleanup(self):
        """清理资源"""
        try:
            self._cleanup_integration()
        except Exception as e:
            self.logger.error(f"Failed to cleanup cloud storage integration: {e}")

    def get_integration_config(self) -> CloudIntegrationConfig:
        """获取集成配置"""
        return self.integration_config

    def set_integration_config(self, config: CloudIntegrationConfig):
        """设置集成配置"""
        self.integration_config = config
        self._save_integration_config()

    def is_cloud_enabled(self) -> bool:
        """检查云端是否启用"""
        return self.integration_config.enabled and self.status == CloudIntegrationStatus.CONNECTED

    def get_storage_usage(self) -> Dict[str, Any]:
        """获取存储使用情况"""
        try:
            if self.cloud_manager:
                stats = self.cloud_manager.get_storage_stats()
                return {
                    'total_files': stats.get('total_files', 0),
                    'total_size': stats.get('total_size', 0),
                    'synced_files': stats.get('synced_files', 0),
                    'synced_size': stats.get('synced_size', 0),
                    'cache_usage': stats.get('cache_usage', 0),
                    'usage_percentage': (stats.get('synced_size', 0) / max(stats.get('total_size', 1), 1)) * 100
                }
            return {}
        except Exception as e:
            self.logger.error(f"Failed to get storage usage: {e}")
            return {}