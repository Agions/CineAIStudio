#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

logger = logging.getLogger(__name__)

"""
撤销/重做管理器 (Undo Manager)

实现命令模式，支持无限级撤销和重做。

功能:
- 命令模式封装操作
- 无限级撤销/重做
- 操作分组（事务）
- 状态快照
- 历史记录持久化

使用示例:
    from app.services.core import UndoManager, Command

    # 创建命令
    class AddTextCommand(Command):
        def execute(self):
            self.project.add_text(self.text)

        def undo(self):
            self.project.remove_text(self.text)

    # 使用
    undo_manager = UndoManager()
    undo_manager.execute(AddTextCommand(project, "Hello"))
    undo_manager.undo()  # 撤销
    undo_manager.redo()  # 重做
"""

import json
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import copy


class CommandStatus(Enum):
    """命令状态"""
    PENDING = "pending"
    EXECUTED = "executed"
    UNDONE = "undone"
    FAILED = "failed"


@dataclass
class CommandMetadata:
    """命令元数据"""
    timestamp: float = field(default_factory=time.time)
    description: str = ""
    tags: List[str] = field(default_factory=list)
    user_id: Optional[str] = None


class Command(ABC):
    """
    命令基类

    所有可撤销操作必须继承此类
    """

    def __init__(
        self,
        description: str = "",
        tags: Optional[List[str]] = None,
    ):
        self.description = description
        self.tags = tags or []
        self.status = CommandStatus.PENDING
        self.metadata = CommandMetadata(
            description=description,
            tags=tags or [],
        )
        self._executed = False

    @abstractmethod
    def execute(self) -> Any:
        """执行命令"""
        pass

    @abstractmethod
    def undo(self) -> Any:
        """撤销命令"""
        pass

    def redo(self) -> Any:
        """重做命令（默认调用 execute）"""
        return self.execute()

    def can_execute(self) -> bool:
        """检查是否可以执行"""
        return not self._executed

    def can_undo(self) -> bool:
        """检查是否可以撤销"""
        return self._executed

    def get_description(self) -> str:
        """获取命令描述"""
        return self.description


class CompoundCommand(Command):
    """
    复合命令

    将多个命令组合为一个原子操作
    """

    def __init__(
        self,
        description: str = "复合操作",
        commands: Optional[List[Command]] = None,
    ):
        super().__init__(description)
        self.commands = commands or []

    def add_command(self, command: Command) -> None:
        """添加子命令"""
        self.commands.append(command)

    def execute(self) -> Any:
        """执行所有子命令"""
        results = []
        for cmd in self.commands:
            result = cmd.execute()
            results.append(result)
        self._executed = True
        return results

    def undo(self) -> Any:
        """撤销所有子命令（逆序）"""
        results = []
        for cmd in reversed(self.commands):
            result = cmd.undo()
            results.append(result)
        self._executed = False
        return results


class SnapshotCommand(Command):
    """
    快照命令

    基于状态快照的撤销/重做
    """

    def __init__(
        self,
        target: Any,
        apply_state: Callable[[Any, Any], None],
        description: str = "状态变更",
    ):
        super().__init__(description)
        self.target = target
        self.apply_state = apply_state
        self._before_state: Optional[Any] = None
        self._after_state: Optional[Any] = None

    def capture_before(self) -> None:
        """捕获执行前的状态"""
        self._before_state = copy.deepcopy(self._get_state())

    def capture_after(self) -> None:
        """捕获执行后的状态"""
        self._after_state = copy.deepcopy(self._get_state())

    def _get_state(self) -> Any:
        """获取目标对象的状态"""
        if hasattr(self.target, '__dict__'):
            return copy.deepcopy(self.target.__dict__)
        return copy.deepcopy(self.target)

    def execute(self) -> Any:
        """执行（应用新状态）"""
        if self._after_state is not None:
            self.apply_state(self.target, self._after_state)
        self._executed = True
        return self.target

    def undo(self) -> Any:
        """撤销（恢复旧状态）"""
        if self._before_state is not None:
            self.apply_state(self.target, self._before_state)
        self._executed = False
        return self.target


@dataclass
class UndoGroup:
    """撤销分组（事务）"""
    name: str
    commands: List[Command] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def add(self, command: Command) -> None:
        """添加命令"""
        self.commands.append(command)

    def execute(self) -> None:
        """执行所有命令"""
        for cmd in self.commands:
            cmd.execute()

    def undo(self) -> None:
        """撤销所有命令"""
        for cmd in reversed(self.commands):
            cmd.undo()


class UndoManager:
    """
    撤销/重做管理器

    管理命令历史，支持无限级撤销和重做

    使用示例:
        manager = UndoManager(max_history=100)

        # 执行命令
        cmd = AddTextCommand(project, "Hello")
        manager.execute(cmd)

        # 撤销
        if manager.can_undo():
            manager.undo()

        # 重做
        if manager.can_redo():
            manager.redo()

        # 查看历史
        for entry in manager.get_history():
            print(f"{entry['index']}: {entry['description']}")
    """

    def __init__(
        self,
        max_history: int = 100,
        auto_save: bool = False,
        save_path: Optional[str] = None,
    ):
        """
        初始化管理器

        Args:
            max_history: 最大历史记录数
            auto_save: 是否自动保存历史
            save_path: 历史记录保存路径
        """
        self.max_history = max_history
        self.auto_save = auto_save
        self.save_path = save_path

        self._history: List[Command] = []
        self._current_index: int = -1
        self._groups: List[UndoGroup] = []
        self._current_group: Optional[UndoGroup] = None

        self._on_undo: Optional[Callable[[Command], None]] = None
        self._on_redo: Optional[Callable[[Command], None]] = None
        self._on_execute: Optional[Callable[[Command], None]] = None

    def set_callbacks(
        self,
        on_execute: Optional[Callable[[Command], None]] = None,
        on_undo: Optional[Callable[[Command], None]] = None,
        on_redo: Optional[Callable[[Command], None]] = None,
    ) -> None:
        """设置回调函数"""
        self._on_execute = on_execute
        self._on_undo = on_undo
        self._on_redo = on_redo

    def execute(self, command: Command) -> Any:
        """
        执行命令

        Args:
            command: 要执行的命令

        Returns:
            命令执行结果
        """
        # 如果有重做历史，清除它
        if self._current_index < len(self._history) - 1:
            self._history = self._history[:self._current_index + 1]

        # 执行命令
        result = command.execute()
        command.status = CommandStatus.EXECUTED
        command._executed = True

        # 添加到历史
        self._history.append(command)
        self._current_index += 1

        # 限制历史大小
        if len(self._history) > self.max_history:
            self._history.pop(0)
            self._current_index -= 1

        # 如果在分组中，添加到分组
        if self._current_group is not None:
            self._current_group.add(command)

        # 回调
        if self._on_execute:
            self._on_execute(command)

        # 自动保存
        if self.auto_save and self.save_path:
            self.save_history()

        return result

    def undo(self) -> Optional[Any]:
        """
        撤销上一个命令

        Returns:
            撤销的命令，如果没有可撤销的则返回 None
        """
        if not self.can_undo():
            return None

        command = self._history[self._current_index]
        result = command.undo()
        command.status = CommandStatus.UNDONE
        command._executed = False

        self._current_index -= 1

        if self._on_undo:
            self._on_undo(command)

        if self.auto_save and self.save_path:
            self.save_history()

        return result

    def redo(self) -> Optional[Any]:
        """
        重做下一个命令

        Returns:
            重做的命令，如果没有可重做的则返回 None
        """
        if not self.can_redo():
            return None

        self._current_index += 1
        command = self._history[self._current_index]
        result = command.redo()
        command.status = CommandStatus.EXECUTED
        command._executed = True

        if self._on_redo:
            self._on_redo(command)

        if self.auto_save and self.save_path:
            self.save_history()

        return result

    def can_undo(self) -> bool:
        """检查是否可以撤销"""
        return self._current_index >= 0

    def can_redo(self) -> bool:
        """检查是否可以重做"""
        return self._current_index < len(self._history) - 1

    def undo_all(self) -> None:
        """撤销所有命令"""
        while self.can_undo():
            self.undo()

    def redo_all(self) -> None:
        """重做所有命令"""
        while self.can_redo():
            self.redo()

    def clear(self) -> None:
        """清空历史"""
        self._history.clear()
        self._current_index = -1
        self._groups.clear()
        self._current_group = None

    def get_history(self) -> List[Dict[str, Any]]:
        """
        获取历史记录

        Returns:
            历史记录列表
        """
        history = []
        for i, cmd in enumerate(self._history):
            history.append({
                'index': i,
                'description': cmd.get_description(),
                'status': cmd.status.value,
                'timestamp': cmd.metadata.timestamp,
                'tags': cmd.tags,
                'is_current': i == self._current_index,
            })
        return history

    def get_current_command(self) -> Optional[Command]:
        """获取当前命令"""
        if 0 <= self._current_index < len(self._history):
            return self._history[self._current_index]
        return None

    def jump_to(self, index: int) -> bool:
        """
        跳转到指定历史位置

        Args:
            index: 目标索引

        Returns:
            是否成功跳转
        """
        if index < -1 or index >= len(self._history):
            return False

        # 撤销到目标位置之前
        while self._current_index > index:
            self.undo()

        # 重做到目标位置
        while self._current_index < index:
            self.redo()

        return True

    def begin_group(self, name: str) -> None:
        """
        开始命令分组（事务）

        Args:
            name: 分组名称
        """
        self._current_group = UndoGroup(name=name)

    def end_group(self) -> Optional[CompoundCommand]:
        """
        结束命令分组

        Returns:
            复合命令，如果没有命令则返回 None
        """
        if self._current_group is None:
            return None

        group = self._current_group
        self._current_group = None

        if not group.commands:
            return None

        # 创建复合命令
        compound = CompoundCommand(
            description=group.name,
            commands=group.commands,
        )

        # 替换历史中的分组命令
        # 简化实现：直接执行复合命令
        return compound

    def cancel_group(self) -> None:
        """取消当前分组并撤销已执行的命令"""
        if self._current_group is None:
            return

        # 撤销分组中的命令
        for cmd in reversed(self._current_group.commands):
            cmd.undo()
            # 从历史中移除
            if cmd in self._history:
                self._history.remove(cmd)
                self._current_index -= 1

        self._current_group = None

    def save_history(self, path: Optional[str] = None) -> bool:
        """
        保存历史记录

        Args:
            path: 保存路径

        Returns:
            是否成功保存
        """
        save_path = path or self.save_path
        if not save_path:
            return False

        try:
            data = {
                'current_index': self._current_index,
                'commands': [
                    {
                        'description': cmd.description,
                        'status': cmd.status.value,
                        'timestamp': cmd.metadata.timestamp,
                        'tags': cmd.tags,
                    }
                    for cmd in self._history
                ],
            }

            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            logger.error(f"保存历史失败: {e}")
            return False

    def load_history(self, path: Optional[str] = None) -> bool:
        """
        加载历史记录

        Args:
            path: 加载路径

        Returns:
            是否成功加载
        """
        load_path = path or self.save_path
        if not load_path or not Path(load_path).exists():
            return False

        try:
            with open(load_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 注意：这里只加载元数据，命令对象需要重新创建
            # 实际应用中可能需要更复杂的序列化
            return True
        except Exception as e:
            logger.error(f"加载历史失败: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total_commands': len(self._history),
            'current_index': self._current_index,
            'can_undo': self.can_undo(),
            'can_redo': self.can_redo(),
            'max_history': self.max_history,
        }


# =========== 常用命令 ===========

class PropertyChangeCommand(Command):
    """
    属性变更命令

    用于修改对象属性的通用命令
    """

    def __init__(
        self,
        target: Any,
        property_name: str,
        new_value: Any,
        description: Optional[str] = None,
    ):
        desc = description or f"修改 {property_name}"
        super().__init__(desc)
        self.target = target
        self.property_name = property_name
        self.new_value = new_value
        self._old_value: Optional[Any] = None

    def execute(self) -> Any:
        """执行"""
        self._old_value = getattr(self.target, self.property_name)
        setattr(self.target, self.property_name, self.new_value)
        self._executed = True
        return self.new_value

    def undo(self) -> Any:
        """撤销"""
        setattr(self.target, self.property_name, self._old_value)
        self._executed = False
        return self._old_value


class ListAddCommand(Command):
    """列表添加命令"""

    def __init__(
        self,
        target_list: List,
        item: Any,
        index: Optional[int] = None,
        description: Optional[str] = None,
    ):
        desc = description or f"添加 {type(item).__name__}"
        super().__init__(desc)
        self.target_list = target_list
        self.item = item
        self.index = index

    def execute(self) -> Any:
        """执行"""
        if self.index is not None:
            self.target_list.insert(self.index, self.item)
        else:
            self.target_list.append(self.item)
        self._executed = True
        return self.item

    def undo(self) -> Any:
        """撤销"""
        if self.item in self.target_list:
            self.target_list.remove(self.item)
        self._executed = False
        return self.item


class ListRemoveCommand(Command):
    """列表移除命令"""

    def __init__(
        self,
        target_list: List,
        item: Any,
        description: Optional[str] = None,
    ):
        desc = description or f"移除 {type(item).__name__}"
        super().__init__(desc)
        self.target_list = target_list
        self.item = item
        self._index: Optional[int] = None

    def execute(self) -> Any:
        """执行"""
        if self.item in self.target_list:
            self._index = self.target_list.index(self.item)
            self.target_list.remove(self.item)
        self._executed = True
        return self.item

    def undo(self) -> Any:
        """撤销"""
        if self._index is not None:
            self.target_list.insert(self._index, self.item)
        else:
            self.target_list.append(self.item)
        self._executed = False
        return self.item


# =========== 便捷函数 ===========

def create_undo_manager(max_history: int = 100) -> UndoManager:
    """创建撤销管理器"""
    return UndoManager(max_history=max_history)


def demo_undo():
    """演示撤销功能"""
    print("=" * 60)
    print("🔄 撤销/重做管理器")
    print("=" * 60)

    # 创建一个简单的列表操作
    my_list = []

    # 创建撤销管理器
    undo_manager = UndoManager(max_history=10)

    # 定义回调
    def on_execute(cmd):
        print(f"  执行: {cmd.description}")

    def on_undo(cmd):
        print(f"  撤销: {cmd.description}")

    undo_manager.set_callbacks(on_execute=on_execute, on_undo=on_undo)

    # 执行一些操作
    print("\n执行操作:")
    undo_manager.execute(ListAddCommand(my_list, "A", description="添加 A"))
    undo_manager.execute(ListAddCommand(my_list, "B", description="添加 B"))
    undo_manager.execute(ListAddCommand(my_list, "C", description="添加 C"))

    print(f"\n当前列表: {my_list}")

    # 撤销
    print("\n撤销操作:")
    undo_manager.undo()
    print(f"撤销后: {my_list}")

    undo_manager.undo()
    print(f"撤销后: {my_list}")

    # 重做
    print("\n重做操作:")
    undo_manager.redo()
    print(f"重做后: {my_list}")

    # 查看历史
    print("\n历史记录:")
    for entry in undo_manager.get_history():
        marker = " <-- 当前" if entry['is_current'] else ""
        print(f"  [{entry['index']}] {entry['description']}{marker}")

    # 统计信息
    print(f"\n统计: {undo_manager.get_statistics()}")


if __name__ == '__main__':
    demo_undo()
