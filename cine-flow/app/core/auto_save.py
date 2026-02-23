#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClipFlow 自动保存系统
提供项目自动保存、恢复和备份功能
"""

import os
import json
import shutil
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path

from .logger import Logger
from .event_bus import EventBus
from .undo_system import UndoManager


class SaveTrigger(Enum):
    """保存触发条件"""
    INTERVAL = "interval"     # 定时保存
    CHANGE_COUNT = "count"   # 变更次数
    MANUAL = "manual"       # 手动保存
    FOCUS_LOSS = "focus"     # 失去焦点
    ERROR = "error"          # 错误时保存


@dataclass
class AutoSaveConfig:
    """自动保存配置"""
    enabled: bool = True
    interval: int = 300                    # 保存间隔（秒）
    change_threshold: int = 10            # 变更阈值
    max_backup_files: int = 10            # 最大备份文件数
    backup_interval: int = 1800           # 备份间隔（秒）
    save_on_error: bool = True            # 错误时保存
    save_on_focus_loss: bool = True       # 失去焦点时保存
    compression: bool = True               # 启用压缩
    incremental: bool = True              # 启用增量保存
    temp_dir: str = "temp/auto_save"      # 临时目录


@dataclass
class SaveState:
    """保存状态"""
    timestamp: float
    trigger: SaveTrigger
    change_count: int
    file_size: int
    checksum: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class AutoSaveManager:
    """自动保存管理器"""

    def __init__(self, config: AutoSaveConfig, logger: Logger, event_bus: EventBus):
        self.config = config
        self.logger = logger
        self.event_bus = event_bus

        # 状态管理
        self.is_enabled = config.enabled
        self.change_count = 0
        self.last_save_time = 0.0
        self.last_backup_time = 0.0
        self.current_project: Optional[str] = None
        self.save_in_progress = False

        # 文件路径
        self.save_dir = Path("projects/.auto_save")
        self.backup_dir = Path("projects/.backups")
        self.temp_dir = Path(config.temp_dir)

        # 确保目录存在
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # 定时器
        self.save_timer: Optional[threading.Timer] = None
        self.backup_timer: Optional[threading.Timer] = None

        # 线程安全
        self._lock = threading.RLock()

        # 统计信息
        self.stats = {
            "total_saves": 0,
            "total_backups": 0,
            "error_saves": 0,
            "manual_saves": 0,
            "auto_saves": 0,
            "last_save_time": 0.0,
            "last_backup_time": 0.0,
            "recovered_projects": 0
        }

        # 启动定时器
        if self.is_enabled:
            self._start_timers()

    def set_project(self, project_path: str) -> None:
        """设置当前项目"""
        with self._lock:
            self.current_project = project_path
            self.change_count = 0
            self.last_save_time = time.time()

            self.logger.info(f"Auto-save enabled for project: {project_path}")
            self.event_bus.publish("auto_save.project_changed", {
                "project_path": project_path
            })

    def unset_project(self) -> None:
        """取消项目设置"""
        with self._lock:
            self.current_project = None
            self.change_count = 0

            self.logger.info("Auto-save project unset")

    def notify_change(self) -> None:
        """通知变更"""
        with self._lock:
            if not self.is_enabled or not self.current_project:
                return

            self.change_count += 1

            # 检查是否需要保存
            if self.change_count >= self.config.change_threshold:
                self._trigger_save(SaveTrigger.CHANGE_COUNT)

    def save_now(self, trigger: SaveTrigger = SaveTrigger.MANUAL) -> bool:
        """立即保存"""
        if not self.is_enabled or not self.current_project:
            return False

        return self._trigger_save(trigger)

    def force_backup(self) -> bool:
        """强制备份"""
        if not self.current_project:
            return False

        return self._create_backup()

    def get_save_history(self, project_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取保存历史"""
        target_project = project_path or self.current_project
        if not target_project:
            return []

        history = []

        # 查找自动保存文件
        save_pattern = f"{os.path.basename(target_project)}_auto_save_*.json"
        for save_file in self.save_dir.glob(save_pattern):
            try:
                save_state = self._load_save_state(save_file)
                if save_state:
                    history.append({
                        "file_path": str(save_file),
                        "timestamp": save_state.timestamp,
                        "trigger": save_state.trigger.value,
                        "change_count": save_state.change_count,
                        "file_size": save_state.file_size,
                        "checksum": save_state.checksum
                    })
            except Exception as e:
                self.logger.warning(f"Failed to load save state from {save_file}: {e}")

        # 按时间排序（最新的在前）
        history.sort(key=lambda x: x["timestamp"], reverse=True)

        return history

    def recover_project(self, project_path: str, save_file: str) -> bool:
        """恢复项目"""
        try:
            # 复制保存文件到项目位置
            save_path = Path(save_file)
            if not save_path.exists():
                return False

            # 验证保存文件
            save_state = self._load_save_state(save_path)
            if not save_state:
                return False

            # 备份当前项目文件（如果存在）
            project_path_obj = Path(project_path)
            if project_path_obj.exists():
                backup_path = project_path_obj.with_suffix(f".backup_{int(time.time())}")
                shutil.copy2(project_path_obj, backup_path)

            # 恢复项目文件
            shutil.copy2(save_path, project_path_obj)

            self.stats["recovered_projects"] += 1
            self.logger.info(f"Project recovered from {save_file}")

            self.event_bus.publish("auto_save.project_recovered", {
                "project_path": project_path,
                "save_file": save_file,
                "timestamp": save_state.timestamp
            })

            return True

        except Exception as e:
            self.logger.error(f"Failed to recover project: {e}")
            return False

    def cleanup_old_saves(self, days: int = 7) -> int:
        """清理旧的保存文件"""
        cleaned_count = 0
        cutoff_time = time.time() - (days * 24 * 60 * 60)

        try:
            # 清理自动保存文件
            for save_file in self.save_dir.glob("*.json"):
                if save_file.stat().st_mtime < cutoff_time:
                    save_file.unlink()
                    cleaned_count += 1

            # 清理备份文件
            for backup_file in self.backup_dir.glob("*.json"):
                if backup_file.stat().st_mtime < cutoff_time:
                    backup_file.unlink()
                    cleaned_count += 1

            self.logger.info(f"Cleaned up {cleaned_count} old save files")
            return cleaned_count

        except Exception as e:
            self.logger.error(f"Failed to cleanup old saves: {e}")
            return 0

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "enabled": self.is_enabled,
            "current_project": self.current_project,
            "change_count": self.change_count,
            "save_dir": str(self.save_dir),
            "backup_dir": str(self.backup_dir)
        }

    def set_config(self, config: Dict[str, Any]) -> None:
        """设置配置"""
        for key, value in config.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

        # 更新启用状态
        if self.config.enabled != self.is_enabled:
            self.is_enabled = self.config.enabled
            if self.is_enabled:
                self._start_timers()
            else:
                self._stop_timers()

    def cleanup(self) -> None:
        """清理资源"""
        self._stop_timers()

    # 私有方法

    def _start_timers(self) -> None:
        """启动定时器"""
        self._stop_timers()

        # 保存定时器
        self.save_timer = threading.Timer(
            self.config.interval,
            self._on_save_timer
        )
        self.save_timer.daemon = True
        self.save_timer.start()

        # 备份定时器
        self.backup_timer = threading.Timer(
            self.config.backup_interval,
            self._on_backup_timer
        )
        self.backup_timer.daemon = True
        self.backup_timer.start()

    def _stop_timers(self) -> None:
        """停止定时器"""
        if self.save_timer:
            self.save_timer.cancel()
            self.save_timer = None

        if self.backup_timer:
            self.backup_timer.cancel()
            self.backup_timer = None

    def _on_save_timer(self) -> None:
        """定时保存回调"""
        try:
            self._trigger_save(SaveTrigger.INTERVAL)
        except Exception as e:
            self.logger.error(f"Auto-save timer error: {e}")

        # 重新启动定时器
        if self.is_enabled:
            self.save_timer = threading.Timer(
                self.config.interval,
                self._on_save_timer
            )
            self.save_timer.daemon = True
            self.save_timer.start()

    def _on_backup_timer(self) -> None:
        """定时备份回调"""
        try:
            self._create_backup()
        except Exception as e:
            self.logger.error(f"Auto-backup timer error: {e}")

        # 重新启动定时器
        if self.is_enabled:
            self.backup_timer = threading.Timer(
                self.config.backup_interval,
                self._on_backup_timer
            )
            self.backup_timer.daemon = True
            self.backup_timer.start()

    def _trigger_save(self, trigger: SaveTrigger) -> bool:
        """触发保存"""
        if self.save_in_progress or not self.current_project:
            return False

        self.save_in_progress = True

        try:
            success = self._perform_save(trigger)
            if success:
                self.last_save_time = time.time()
                self.change_count = 0

                # 更新统计
                self.stats["last_save_time"] = self.last_save_time
                self.stats["total_saves"] += 1

                if trigger == SaveTrigger.MANUAL:
                    self.stats["manual_saves"] += 1
                else:
                    self.stats["auto_saves"] += 1

                self.event_bus.publish("auto_save.saved", {
                    "project_path": self.current_project,
                    "trigger": trigger.value,
                    "timestamp": self.last_save_time
                })

            return success

        except Exception as e:
            self.logger.error(f"Auto-save failed: {e}")
            self.stats["error_saves"] += 1
            return False

        finally:
            self.save_in_progress = False

    def _perform_save(self, trigger: SaveTrigger) -> bool:
        """执行保存操作"""
        if not self.current_project:
            return False

        project_path = Path(self.current_project)
        if not project_path.exists():
            return False

        try:
            # 读取当前项目文件
            with open(project_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)

            # 创建保存状态
            save_state = SaveState(
                timestamp=time.time(),
                trigger=trigger,
                change_count=self.change_count,
                file_size=project_path.stat().st_size,
                checksum=self._calculate_checksum(project_data),
                metadata={
                    "project_name": project_data.get("name", ""),
                    "version": project_data.get("version", "1.0"),
                    "last_modified": project_path.stat().st_mtime
                }
            )

            # 保存自动保存文件
            save_filename = f"{project_path.stem}_auto_save_{int(time.time())}.json"
            save_path = self.save_dir / save_filename

            save_data = {
                "project_data": project_data,
                "save_state": save_state.__dict__
            }

            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)

            self.logger.debug(f"Auto-saved project to {save_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to perform auto-save: {e}")
            return False

    def _create_backup(self) -> bool:
        """创建备份"""
        if not self.current_project:
            return False

        try:
            project_path = Path(self.current_project)
            if not project_path.exists():
                return False

            # 生成备份文件名
            backup_filename = f"{project_path.stem}_backup_{int(time.time())}.json"
            backup_path = self.backup_dir / backup_filename

            # 复制项目文件
            shutil.copy2(project_path, backup_path)

            # 清理旧备份
            self._cleanup_old_backups()

            self.last_backup_time = time.time()
            self.stats["last_backup_time"] = self.last_backup_time
            self.stats["total_backups"] += 1

            self.logger.debug(f"Created backup: {backup_path}")
            self.event_bus.publish("auto_save.backup_created", {
                "project_path": self.current_project,
                "backup_path": str(backup_path),
                "timestamp": self.last_backup_time
            })

            return True

        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return False

    def _cleanup_old_backups(self) -> None:
        """清理旧备份文件"""
        try:
            backup_files = list(self.backup_dir.glob(f"{Path(self.current_project).stem}_backup_*.json"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # 保留最新的备份文件
            if len(backup_files) > self.config.max_backup_files:
                for old_backup in backup_files[self.config.max_backup_files:]:
                    old_backup.unlink()
                    self.logger.debug(f"Removed old backup: {old_backup}")

        except Exception as e:
            self.logger.warning(f"Failed to cleanup old backups: {e}")

    def _load_save_state(self, save_file: Path) -> Optional[SaveState]:
        """加载保存状态"""
        try:
            with open(save_file, 'r', encoding='utf-8') as f:
                save_data = json.load(f)

            save_state_dict = save_data.get("save_state", {})
            return SaveState(**save_state_dict)

        except Exception as e:
            self.logger.warning(f"Failed to load save state from {save_file}: {e}")
            return None

    def _calculate_checksum(self, data: Any) -> str:
        """计算数据校验和"""
        import hashlib
        json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(json_str.encode('utf-8')).hexdigest()


# 全局自动保存管理器（需要在服务系统初始化后设置）
_auto_save_manager = None


def get_auto_save_manager() -> AutoSaveManager:
    """获取全局自动保存管理器"""
    global _auto_save_manager
    if _auto_save_manager is None:
        raise RuntimeError("Auto-save manager not initialized")
    return _auto_save_manager


def set_auto_save_manager(manager: AutoSaveManager) -> None:
    """设置全局自动保存管理器"""
    global _auto_save_manager
    _auto_save_manager = manager


def enable_auto_save(project_path: str) -> None:
    """启用自动保存"""
    get_auto_save_manager().set_project(project_path)


def disable_auto_save() -> None:
    """禁用自动保存"""
    get_auto_save_manager().unset_project()


def notify_change() -> None:
    """通知变更"""
    get_auto_save_manager().notify_change()


def save_now() -> bool:
    """立即保存"""
    return get_auto_save_manager().save_now(SaveTrigger.MANUAL)