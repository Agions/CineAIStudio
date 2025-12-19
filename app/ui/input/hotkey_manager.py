#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI-EditX 快捷键管理系统
提供全局快捷键绑定、自定义快捷键和快捷键冲突检测
"""

import json
import os
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication, QShortcut, QKeySequence

from ...core.logger import Logger
from ...core.event_bus import EventBus


class KeyModifier(Enum):
    """键盘修饰符"""
    NONE = "none"
    CTRL = "ctrl"
    ALT = "alt"
    SHIFT = "shift"
    META = "meta"
    CMD = "cmd"  # macOS Command键


@dataclass
class HotkeyAction:
    """快捷键动作"""
    action_id: str
    name: str
    category: str
    description: str
    key_sequence: str
    modifier: KeyModifier
    callable: Optional[Callable] = None
    enabled: bool = True
    global_action: bool = True
    context: Optional[str] = None  # 动作上下文
    icon: Optional[str] = None


@dataclass
class HotkeyConflict:
    """快捷键冲突"""
    action1: HotkeyAction
    action2: HotkeyAction
    severity: str  # warning, error


class HotkeyManager(QObject):
    """快捷键管理器"""

    # 信号
    hotkey_triggered = pyqtSignal(str)  # action_id
    hotkey_conflict = pyqtSignal(HotkeyConflict)  # conflict

    def __init__(self, logger: Logger, event_bus: EventBus):
        super().__init__()
        self.logger = logger
        self.event_bus = event_bus

        # 快捷键注册
        self.actions: Dict[str, HotkeyAction] = {}
        self.shortcuts: Dict[str, QShortcut] = {}
        self.key_bindings: Dict[str, str] = {}  # key_sequence -> action_id

        # 冲突检测
        self.conflicts: List[HotkeyConflict] = []
        self.conflict_check_enabled = True

        # 配置
        self.config_file = Path("config/hotkeys.json")
        self.config = {
            "enabled": True,
            "global_shortcuts": True,
            "custom_shortcuts": {},
            "conflict_resolution": "warn",  # warn, error, ignore
        }

        # macOS特殊处理
        self.is_macos = os.name == 'darwin'

        # 统计信息
        self.stats = {
            "total_shortcuts": 0,
            "active_shortcuts": 0,
            "custom_shortcuts": 0,
            "conflicts_detected": 0,
            "most_used_shortcuts": {}
        }

        # 加载配置和快捷键
        self._load_config()
        self._register_default_shortcuts()

    def register_action(self, action: HotkeyAction) -> None:
        """注册快捷键动作"""
        # 检查冲突
        if self.conflict_check_enabled:
            conflict = self._check_conflict(action)
            if conflict:
                self.conflicts.append(conflict)
                self.hotkey_conflict.emit(conflict)

                if self.config["conflict_resolution"] == "error":
                    self.logger.error(f"Hotkey conflict detected: {action.action_id}")
                    return

        # 注册动作
        self.actions[action.action_id] = action

        # 创建快捷键
        key_sequence = self._build_key_sequence(action.key_sequence, action.modifier)
        shortcut = QShortcut(key_sequence, QApplication.activeWindow())

        # 连接信号
        shortcut.activated.connect(
            lambda: self._trigger_action(action.action_id)
        )

        self.shortcuts[action.action_id] = shortcut
        self.key_bindings[key_sequence.toString()] = action.action_id

        self.stats["total_shortcuts"] += 1
        if action.callable:
            action.shortcut = shortcut

        self.logger.debug(f"Registered hotkey: {action.key_sequence} ({action.action_id})")

        # 发布事件
        self.event_bus.publish("hotkey.registered", {
            "action_id": action.action_id,
            "name": action.name,
            "key_sequence": action.key_sequence
        })

    def unregister_action(self, action_id: str) -> bool:
        """取消注册快捷键动作"""
        if action_id not in self.actions:
            return False

        action = self.actions[action_id]

        # 移除快捷键
        if action_id in self.shortcuts:
            shortcut = self.shortcuts[action_id]
            shortcut.delete()
            del self.shortcuts[action_id]

        # 移除键绑定
        key_sequence = self._build_key_sequence(action.key_sequence, action.modifier)
        binding_key = key_sequence.toString()
        if binding_key in self.key_bindings:
            del self.key_bindings[binding_key]

        del self.actions[action_id]

        self.logger.debug(f"Unregistered hotkey: {action.key_sequence} ({action_id})")

        # 发布事件
        self.event_bus.publish("hotkey.unregistered", {
            "action_id": action_id,
            "name": action.name
        })

        return True

    def trigger_action(self, action_id: str) -> bool:
        """手动触发快捷键动作"""
        return self._trigger_action(action_id)

    def get_action(self, action_id: str) -> Optional[HotkeyAction]:
        """获取快捷键动作"""
        return self.actions.get(action_id)

    def get_actions_by_category(self, category: str) -> List[HotkeyAction]:
        """按类别获取快捷键动作"""
        return [action for action in self.actions.values() if action.category == category]

    def get_all_actions(self) -> List[HotkeyAction]:
        """获取所有快捷键动作"""
        return list(self.actions.values())

    def search_actions(self, query: str) -> List[HotkeyAction]:
        """搜索快捷键动作"""
        query_lower = query.lower()
        return [
            action for action in self.actions.values()
            if (query_lower in action.name.lower() or
                query_lower in action.description.lower() or
                query_lower in action.action_id.lower())
        ]

    def update_action_keybinding(self, action_id: str, key_sequence: str,
                                 modifier: KeyModifier = KeyModifier.NONE) -> bool:
        """更新快捷键绑定"""
        if action_id not in self.actions:
            return False

        action = self.actions[action_id]
        old_key_sequence = action.key_sequence
        old_modifier = action.modifier

        # 移除旧的键绑定
        if action_id in self.shortcuts:
            self.shortcuts[action_id].delete()

        old_binding_key = self._build_key_sequence(old_key_sequence, old_modifier).toString()
        if old_binding_key in self.key_bindings:
            del self.key_bindings[old_binding_key]

        # 更新动作
        action.key_sequence = key_sequence
        action.modifier = modifier

        # 检查新冲突
        if self.conflict_check_enabled:
            conflict = self._check_conflict(action)
            if conflict:
                self.conflicts.append(conflict)
                self.hotkey_conflict.emit(conflict)

                if self.config["conflict_resolution"] == "error":
                    self.logger.error(f"Hotkey conflict detected for update: {action_id}")
                    return False

        # 创建新快捷键
        new_key_sequence = self._build_key_sequence(key_sequence, modifier)
        shortcut = QShortcut(new_key_sequence, QApplication.activeWindow())
        shortcut.activated.connect(
            lambda: self._trigger_action(action_id)
        )

        self.shortcuts[action_id] = shortcut
        self.key_bindings[new_key_sequence.toString()] = action_id
        action.shortcut = shortcut

        self.logger.info(f"Updated hotkey binding: {old_key_sequence} -> {key_sequence} ({action_id})")

        # 发布事件
        self.event_bus.publish("hotkey.updated", {
            "action_id": action_id,
            "old_key_sequence": old_key_sequence,
            "new_key_sequence": key_sequence
        })

        return True

    def toggle_action(self, action_id: str, enabled: bool) -> bool:
        """启用/禁用快捷键动作"""
        if action_id not in self.actions:
            return False

        action = self.actions[action_id]
        action.enabled = enabled

        if action_id in self.shortcuts:
            self.shortcuts[action_id].setEnabled(enabled)

        if enabled:
            self.stats["active_shortcuts"] += 1
        else:
            self.stats["active_shortcuts"] -= 1

        self.logger.info(f"Hotkey {action_id} {'enabled' if enabled else 'disabled'}")

        # 发布事件
        self.event_bus.export("hotkey.toggled", {
            "action_id": action_id,
            "enabled": enabled
        })

        return True

    def export_shortcuts(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """导出快捷键配置"""
        if file_path is None:
            file_path = str(self.config_file)

        export_data = {
            "version": "1.0",
            "exported_at": time.time(),
            "shortcuts": {}
        }

        for action_id, action in self.actions.items():
            export_data["shortcuts"][action_id] = {
                "name": action.name,
                "category": action.category,
                "description": action.description,
                "key_sequence": action.key_sequence,
                "modifier": action.modifier.value,
                "enabled": action.enabled,
                "global_action": action.global_action,
                "context": action.context,
                "icon": action.icon
            }

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Hotkeys exported to {file_path}")
            return export_data

        except Exception as e:
            self.logger.error(f"Failed to export hotkeys: {e}")
            return {}

    def import_shortcuts(self, file_path: str) -> int:
        """导入快捷键配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            imported_count = 0
            custom_shortcuts = data.get("shortcuts", {})

            for action_id, shortcut_data in custom_shortcuts.items():
                if action_id in self.actions:
                    # 更新现有快捷键
                    self.update_action_keybinding(
                        action_id,
                        shortcut_data["key_sequence"],
                        KeyModifier(shortcut_data.get("modifier", "none"))
                    )
                else:
                    # 创建新快捷键
                    action = HotkeyAction(
                        action_id=action_id,
                        name=shortcut_data["name"],
                        category=shortcut_data.get("category", "custom"),
                        description=shortcut_data.get("description", ""),
                        key_sequence=shortcut_data["key_sequence"],
                        modifier=KeyModifier(shortcut_data.get("modifier", "none")),
                        enabled=shortcut_data.get("enabled", True),
                        global_action=shortcut_data.get("global_action", True),
                        context=shortcut_data.get("context"),
                        icon=shortcut_data.get("icon")
                    )
                    self.register_action(action)

                imported_count += 1

            self.stats["custom_shortcuts"] = len([a for a in self.actions.values() if a.category == "custom"])
            self.logger.info(f"Imported {imported_count} hotkeys from {file_path}")

            return imported_count

        except Exception as e:
            self.logger.error(f"Failed to import hotkeys: {e}")
            return 0

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "conflicts_count": len(self.conflicts),
            "enabled": self.config["enabled"],
            "platform": "macos" if self.is_macos else "windows/linux"
        }

    def resolve_conflicts(self, resolution: str = "prefer_new") -> int:
        """解决快捷键冲突"""
        resolved_count = 0

        for conflict in self.conflicts[:]:
            action1, action2 = conflict.action1, action2

            if resolution == "prefer_new":
                # 禁用旧快捷键
                if action1.action_id in self.actions:
                    self.toggle_action(action1.action_id, False)
                    resolved_count += 1
                # 启用新快捷键
                if action2.action_id in self.actions:
                    self.toggle_action(action2.action_id, True)
                    resolved_count += 1

            elif resolution == "prefer_old":
                # 禁用新快捷键
                if action2.action_id in self.actions:
                    self.toggle_action(action2.action_id, False)
                    resolved_count += 1

            elif resolution == "disable_all":
                # 禁用所有冲突的快捷键
                for action in [action1, action2]:
                    if action.action_id in self.actions:
                        self.toggle_action(action.action_id, False)
                        resolved_count += 1

        self.conflicts.clear()
        return resolved_count

    # 私有方法

    def _trigger_action(self, action_id: str) -> bool:
        """触发快捷键动作"""
        if action_id not in self.actions:
            return False

        action = self.actions[action_id]
        if not action.enabled:
            return False

        try:
            # 更新统计
            if action_id not in self.stats["most_used_shortcuts"]:
                self.stats["most_used_shortcuts"][action_id] = 0
            self.stats["most_used_shortcuts"][action_id] += 1

            # 执行回调
            if action.callable:
                action.callable()

            # 发布信号
            self.hotkey_triggered.emit(action_id)

            # 发布事件
            self.event_bus.publish("hotkey.triggered", {
                "action_id": action_id,
                "name": action.name,
                "category": action.category
            })

            return True

        except Exception as e:
            self.logger.error(f"Failed to trigger action {action_id}: {e}")
            return False

    def _check_conflict(self, action: HotkeyAction) -> Optional[HotkeyConflict]:
        """检查快捷键冲突"""
        key_sequence = self._build_key_sequence(action.key_sequence, action.modifier)
        binding_key = key_sequence.toString()

        for existing_action in self.actions.values():
            if existing_action.action_id == action.action_id:
                continue

            existing_key_sequence = self._build_key_sequence(
                existing_action.key_sequence, existing_action.modifier
            )
            existing_binding_key = existing_key_sequence.toString()

            # 检查键序列是否冲突（考虑修饰符组合）
            if self._keys_conflict(key_sequence, existing_key_sequence):
                severity = "warning" if action.category == existing_action.category else "error"
                return HotkeyConflict(action, existing_action, severity)

        return None

    def _keys_conflict(self, key1: QKeySequence, key2: QKeySequence) -> bool:
        """检查两个键序列是否冲突"""
        return key1.toString() == key2.toString()

    def _build_key_sequence(self, key_sequence: str, modifier: KeyModifier) -> QKeySequence:
        """构建键序列"""
        if self.is_macos:
            # macOS特殊处理：Ctrl = Cmd
            if modifier == KeyModifier.CTRL:
                key_sequence = key_sequence.replace("Ctrl", "Cmd")
            elif modifier == KeyModifier.META:
                key_sequence = key_sequence.replace("Meta", "Cmd")

        # 解析键序列
        keys = key_sequence.split("+")
        modifiers = 0

        if modifier != KeyModifier.NONE:
            modifier_map = {
                KeyModifier.CTRL: Qt.KeyboardModifier.ControlModifier,
                KeyModifier.ALT: Qt.KeyboardModifier.AltModifier,
                KeyModifier.SHIFT: Qt.KeyboardModifier.ShiftModifier,
                KeyModifier.META: Qt.KeyboardModifier.MetaModifier,
                KeyModifier.CMD: Qt.KeyboardModifier.ControlModifier  # macOS
            }

            if modifier in modifier_map:
                modifiers |= modifier_map[modifier]

        if len(keys) >= 2:
            key_str = keys[-1]  # 最后一部分是键
        else:
            key_str = keys[0]

        key_map = {
            "Space": Qt.Key.Key_Space,
            "Tab": Qt.Key.Key_Tab,
            "Return": Qt.Key.Key_Return,
            "Enter": Qt.Key.Key_Return,
            "Backspace": Qt.Key.Key_Backspace,
            "Delete": Qt.Key.Key_Delete,
            "Escape": Qt.Key.Key_Escape,
            "Left": Qt.Key.Key_Left,
            "Right": Qt.Key.Key_Right,
            "Up": Qt.Key.Key_Up,
            "Down": Qt.Key.Key_Down,
            "F1": Qt.Key.Key_F1,
            "F2": Qt.Key.Key_F2,
            "F3": Qt.Key.Key_F3,
            "F4": Qt.Key.Key_F4,
            "F5": Qt.Key.Key_F5,
            "F6": Qt.Key_Key_F6,
            "F7": Qt.Key.Key_F7,
            "F8": Qt.Key.Key_F8,
            "F9": Qt.Key_Key_F9,
            "F10": Qt.Key_Key_F10,
            "F11": Qt.Key_Key_F11,
            "F12": Qt.Key_Key_F12,
        }

        key = key_map.get(key_str, ord(key_str[-1]) if len(key_str) == 1 else 0)

        return QKeySequence(modifiers, key)

    def _register_default_shortcuts(self) -> None:
        """注册默认快捷键"""
        default_shortcuts = [
            # 文件操作
            HotkeyAction(
                action_id="file.new",
                name="新建项目",
                category="file",
                description="创建新的视频项目",
                key_sequence="Ctrl+N",
                modifier=KeyModifier.CTRL,
                callable=lambda: self.event_bus.publish("menu.action", {"action": "new_project"})
            ),
            HotkeyAction(
                action_id="file.open",
                name="打开项目",
                category="file",
                description="打开现有项目",
                key_sequence="Ctrl+O",
                modifier=KeyModifier.CTRL,
                callable=lambda: self.event_bus.publish("menu.action", {"action": "open_project"})
            ),
            HotkeyAction(
                action_id="file.save",
                name="保存项目",
                category="file",
                description="保存当前项目",
                key_sequence="Ctrl+S",
                modifier=KeyModifier.CTRL,
                callable=lambda: self.event_bus.publish("menu.action", {"action": "save_project"})
            ),
            HotkeyAction(
                action_id="file.export",
                name="导出视频",
                category="file",
                description="导出视频文件",
                key_sequence="Ctrl+E",
                modifier=KeyModifier.CTRL,
                callable=lambda: self.event_bus.publish("menu.action", {"action": "export_video"})
            ),

            # 编辑操作
            HotkeyAction(
                action_id="edit.undo",
                name="撤销",
                category="edit",
                description="撤销上一个操作",
                key_sequence="Ctrl+Z",
                modifier=KeyModifier.CTRL,
                callable=lambda: self.event_bus.publish("menu.action", {"action": "undo"})
            ),
            HotkeyAction(
                action_id="edit.redo",
                name="重做",
                category="edit",
                description="重做上一个撤销的操作",
                key_sequence="Ctrl+Y",
                modifier=KeyModifier.CTRL,
                callable=lambda: self.event_bus.publish("menu.action", {"action": "redo"})
            ),
            HotkeyAction(
                action_id="edit.cut",
                name="剪切",
                category="edit",
                description="剪切选中内容",
                key_sequence="Ctrl+X",
                modifier=KeyModifier.CTRL,
                callable=lambda: self.event_bus.publish("menu.action", {"action": "cut"})
            ),
            HotkeyAction(
                action_id="edit.copy",
                name="复制",
                category="edit",
                description="复制选中内容",
                key_sequence="Ctrl+C",
                modifier=KeyModifier.CTRL,
                callable=lambda: self.event_bus.publish("menu.action", {"action": "copy"})
            ),
            Hotkey(
                action_id="edit.paste",
                name="粘贴",
                category="edit",
                description="粘贴剪贴板内容",
                key_sequence="Ctrl+V",
                modifier=KeyModifier.CTRL,
                callable=lambda: self.event_bus.publish("menu.action", {"action": "paste"})
            ),

            # 播放控制
            HotkeyAction(
                action_id="playback.play",
                name="播放/暂停",
                category="playback",
                description="播放或暂停视频",
                key_sequence="Space",
                modifier=KeyModifier.NONE,
                callable=lambda: self.event_bus.publish("playback.action", {"action": "toggle_play"})
            ),
            HotkeyAction(
                action_id="playback.stop",
                name="停止",
                category="playback",
                description="停止播放",
                key_sequence=".",
                modifier=KeyModifier.NONE,
                callable=lambda: self.event_bus.publish("playback.action", {"action": "stop"})
            ),
            HotkeyAction(
                action_id="playback.skip_forward",
                name="快进",
                category="playback",
                description="快进5秒",
                key_sequence="Right",
                modifier=KeyModifier.NONE,
                callable=lambda: self.event_bus.publish("playback.action", {"action": "skip_forward", "amount": 5})
            ),
            HotkeyAction(
                action_id="playback.skip_backward",
                name="快退",
                category="playback",
                description="快退5秒",
                key_sequence="Left",
                modifier=KeyModifier.NONE,
                callable=lambda: self.event_bus.publish("playback.action", {"action": "skip_backward", "amount": 5})
            ),

            # 视频编辑
            HotkeyAction(
                action_id="video.cut",
                name="剪切",
                category="video",
                description="剪切选中部分",
                key_sequence="T",
                modifier=KeyModifier.NONE,
                callable=lambda: self.event_bus.publish("timeline.action", {"action": "cut"})
            ),
            HotkeyAction(
                action_id="video.copy",
                name="复制",
                category="video",
                description="复制选中部分",
                key_sequence="C",
                modifier=KeyModifier.NONE,
                callable=lambda: self.event_bus.publish("timeline.action", {"action": "copy"})
            ),
            Hotkey(
                action_id="video.paste",
                name="粘贴",
                category="video",
                description="粘贴剪贴板内容",
                key_sequence="V",
                modifier=KeyModifier.NONE,
                callable=lambda: self.event_bus.publish("timeline.action", {"action": "paste"})
            ),
            HotkeyAction(
                action_id="video.delete",
                name="删除",
                category="video",
                description="删除选中部分",
                key_sequence="Delete",
                modifier=KeyModifier.NONE,
                callable=lambda: self.event_bus.publish("timeline.action", {"action": "delete"})
            ),

            # 视图控制
            HotkeyAction(
                action_id="view.zoom_in",
                name="放大",
                category="view",
                description="放大视频预览",
                key_sequence="=",
                modifier=KeyModifier.CTRL,
                callable=lambda: self.event_bus.publish("view.action", {"action": "zoom_in"})
            ),
            Hotkey(
                action_id="view.zoom_out",
                name="缩小",
                category="view",
                description="缩小视频预览",
                key_sequence="-",
                modifier=KeyModifier.CTRL,
                callable=lambda: self.event_bus.publish("view.action", {"action": "zoom_out"})
            ),
            Hotkey(
                action_id="view.fit",
                name="适应窗口",
                category="view",
                description="适应窗口大小",
                key_sequence="0",
                modifier=KeyModifier.NONE,
                callable=lambda: self.event_bus.publish("view.action", {"action": "fit_window"})
            ),
        ]

        for action in default_shortcuts:
            self.register_action(action)

    def _load_config(self) -> None:
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                # 合并配置
                self.config.update(config_data.get("settings", {}))
                self.config["custom_shortcuts"] = config_data.get("custom_shortcuts", {})

            except Exception as e:
                self.logger.warning(f"Failed to load hotkey config: {e}")

        # 加载自定义快捷键
        custom_shortcuts = self.config.get("custom_shortcuts", {})
        for action_id, shortcut_data in custom_shortcuts.items():
            action = HotkeyAction(
                action_id=action_id,
                name=shortcut_data["name"],
                category=shortcut_data.get("category", "custom"),
                description=shortcut_data.get("description", ""),
                key_sequence=shortcut_data["key_sequence"],
                modifier=KeyModifier(shortcut_data.get("modifier", "none")),
                enabled=shortcut_data.get("enabled", True),
                global_action=shortcut_data.get("global_action", True)
            )
            self.register_action(action)
            self.stats["custom_shortcuts"] += 1

    def cleanup(self) -> None:
        """清理资源"""
        # 保存配置
        self._save_config()

        # 清理快捷键
        for shortcut in self.shortcuts.values():
            shortcut.delete()

        self.shortcuts.clear()
        self.actions.clear()
        self.key_bindings.clear()

    def _save_config(self) -> None:
        """保存配置"""
        try:
            config_data = {
                "settings": self.config,
                "custom_shortcuts": {
                    action_id: {
                        "name": action.name,
                        "category": action.category,
                        "description": action.description,
                        "key_sequence": action.key_sequence,
                        "modifier": action.modifier.value,
                        "enabled": action.enabled,
                        "global_action": action.global_action,
                        "context": action.context,
                        "icon": action.icon
                    }
                    for action_id, action in self.actions.items()
                    if action.category == "custom"
                },
                "version": "1.0"
            }

            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"Failed to save hotkey config: {e}")


# 全局快捷键管理器（需要在服务系统初始化后设置）
_hotkey_manager = None


def get_hotkey_manager() -> HotkeyManager:
    """获取全局快捷键管理器"""
    global _hotkey_manager
    if _hotkey_manager is None:
        raise RuntimeError("Hotkey manager not initialized")
    return _hotkey_manager


def set_hotkey_manager(manager: HotkeyManager) -> None:
    """设置全局快捷键管理器"""
    global _hotkey_manager
    _hotkey_manager = manager


# 便捷装饰器
def hotkey(key_sequence: str, modifier: KeyModifier = KeyModifier.NONE,
             name: str = "", description: str = "", category: str = "custom"):
    """快捷键装饰器"""
    def decorator(func):
        action_id = f"hotkey_{func.__name__}"
        action = HotkeyAction(
            action_id=action_id,
            name=name or func.__name__,
            category=category,
            description=description,
            key_sequence=key_sequence,
            modifier=modifier,
            callable=func
        )

        # 注册快捷键（如果管理器已初始化）
        try:
            get_hotkey_manager().register_action(action)
        except RuntimeError:
            pass  # 管理器未初始化，稍后注册

        return func
    return decorator


# 导入时间（为了在模块末尾导入）
import time