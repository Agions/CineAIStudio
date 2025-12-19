#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI-EditX 撤销/重做系统
提供完整的撤销和重做功能支持
"""

from dataclasses import dataclass
from typing import Any, List, Optional, Callable, Dict
from abc import ABC, abstractmethod
from enum import Enum
import uuid
import time

from .event_bus import EventBus
from .logger import Logger


class CommandType(Enum):
    """命令类型"""
    MODIFY = "modify"      # 修改操作
    CREATE = "create"      # 创建操作
    DELETE = "delete"      # 删除操作
    MOVE = "move"         # 移动操作
    BATCH = "batch"       # 批量操作


@dataclass
class CommandInfo:
    """命令信息"""
    command_id: str
    command_type: CommandType
    description: str
    timestamp: float
    target_object: Optional[str] = None  # 目标对象ID
    metadata: Dict[str, Any] = None  # 额外元数据


class Command(ABC):
    """命令基类"""

    def __init__(self, description: str, target_object: Optional[str] = None):
        self.command_id = str(uuid.uuid4())
        self.description = description
        self.target_object = target_object
        self.timestamp = time.time()
        self.executed = False

    @abstractmethod
    def execute(self) -> Any:
        """执行命令"""
        pass

    @abstractmethod
    def undo(self) -> Any:
        """撤销命令"""
        pass

    @abstractmethod
    def redo(self) -> Any:
        """重做命令"""
        pass

    def get_info(self) -> CommandInfo:
        """获取命令信息"""
        return CommandInfo(
            command_id=self.command_id,
            command_type=self.get_command_type(),
            description=self.description,
            timestamp=self.timestamp,
            target_object=self.target_object
        )

    @abstractmethod
    def get_command_type(self) -> CommandType:
        """获取命令类型"""
        pass


class BatchCommand(Command):
    """批量命令"""

    def __init__(self, commands: List[Command], description: str = "Batch Operation"):
        super().__init__(description)
        self.commands = commands
        self.executed_commands: List[Command] = []

    def execute(self) -> List[Any]:
        """执行批量命令"""
        results = []
        try:
            for command in self.commands:
                result = command.execute()
                command.executed = True
                self.executed_commands.append(command)
                results.append(result)
        except Exception as e:
            # 如果失败，撤销已执行的命令
            self._undo_executed_commands()
            raise e
        return results

    def undo(self) -> List[Any]:
        """撤销批量命令"""
        results = []
        # 按相反顺序撤销
        for command in reversed(self.executed_commands):
            if command.executed:
                result = command.undo()
                command.executed = False
                results.append(result)
        self.executed_commands.clear()
        return results

    def redo(self) -> List[Any]:
        """重做批量命令"""
        return self.execute()

    def get_command_type(self) -> CommandType:
        return CommandType.BATCH

    def _undo_executed_commands(self) -> None:
        """撤销已执行的命令"""
        for command in reversed(self.executed_commands):
            if command.executed:
                try:
                    command.undo()
                    command.executed = False
                except Exception:
                    pass  # 忽略撤销时的错误


class UndoManager:
    """撤销管理器"""

    def __init__(self, max_history: int = 1000, logger: Optional[Logger] = None,
                 event_bus: Optional[EventBus] = None):
        self.max_history = max_history
        self.logger = logger
        self.event_bus = event_bus

        # 命令历史
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []

        # 当前状态
        self.current_position = -1
        self.is_modified = False

        # 统计信息
        self.stats = {
            "total_commands": 0,
            "undo_count": 0,
            "redo_count": 0,
            "batch_commands": 0
        }

    def execute_command(self, command: Command) -> Any:
        """执行命令"""
        try:
            # 执行命令
            result = command.execute()
            command.executed = True

            # 清空重做栈
            self.redo_stack.clear()

            # 添加到撤销栈
            self.undo_stack.append(command)
            self.current_position += 1

            # 限制历史记录数量
            if len(self.undo_stack) > self.max_history:
                removed_command = self.undo_stack.pop(0)
                self.current_position -= 1

            # 更新状态
            self.is_modified = True
            self.stats["total_commands"] += 1

            if isinstance(command, BatchCommand):
                self.stats["batch_commands"] += 1

            # 发布事件
            if self.event_bus:
                self.event_bus.publish("undo.command_executed", {
                    "command_id": command.command_id,
                    "description": command.description
                })

            return result

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to execute command {command.command_id}: {e}")
            raise

    def undo(self) -> Optional[Any]:
        """撤销"""
        if not self.can_undo():
            return None

        command = self.undo_stack.pop()
        self.current_position -= 1

        try:
            result = command.undo()
            command.executed = False

            # 添加到重做栈
            self.redo_stack.append(command)

            # 更新统计
            self.stats["undo_count"] += 1

            # 发布事件
            if self.event_bus:
                self.event_bus.publish("undo.command_undone", {
                    "command_id": command.command_id,
                    "description": command.description
                })

            return result

        except Exception as e:
            # 撤销失败，重新添加到撤销栈
            self.undo_stack.append(command)
            self.current_position += 1

            if self.logger:
                self.logger.error(f"Failed to undo command {command.command_id}: {e}")
            raise

    def redo(self) -> Optional[Any]:
        """重做"""
        if not self.can_redo():
            return None

        command = self.redo_stack.pop()

        try:
            result = command.redo()
            command.executed = True

            # 添加到撤销栈
            self.undo_stack.append(command)
            self.current_position += 1

            # 更新统计
            self.stats["redo_count"] += 1

            # 发布事件
            if self.event_bus:
                self.event_bus.publish("undo.command_redone", {
                    "command_id": command.command_id,
                    "description": command.description
                })

            return result

        except Exception as e:
            # 重做失败，重新添加到重做栈
            self.redo_stack.append(command)

            if self.logger:
                self.logger.error(f"Failed to redo command {command.command_id}: {e}")
            raise

    def can_undo(self) -> bool:
        """是否可以撤销"""
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        """是否可以重做"""
        return len(self.redo_stack) > 0

    def clear(self) -> None:
        """清空历史"""
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.current_position = -1
        self.is_modified = False

        # 发布事件
        if self.event_bus:
            self.event_bus.publish("undo.history_cleared", {})

    def mark_saved(self) -> None:
        """标记为已保存状态"""
        self.is_modified = False

    def is_unsaved(self) -> bool:
        """检查是否有未保存的更改"""
        return self.is_modified

    def get_undo_history(self) -> List[CommandInfo]:
        """获取撤销历史"""
        return [cmd.get_info() for cmd in self.undo_stack]

    def get_redo_history(self) -> List[CommandInfo]:
        """获取重做历史"""
        return [cmd.get_info() for cmd in self.redo_stack]

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "undo_stack_size": len(self.undo_stack),
            "redo_stack_size": len(self.redo_stack),
            "current_position": self.current_position,
            "is_modified": self.is_modified,
            "memory_usage": self._estimate_memory_usage()
        }

    def set_max_history(self, max_history: int) -> None:
        """设置最大历史记录数量"""
        self.max_history = max_history

        # 裁剪超出的记录
        while len(self.undo_stack) > max_history:
            self.undo_stack.pop(0)
            self.current_position -= 1

    def get_last_command(self) -> Optional[CommandInfo]:
        """获取最后执行的命令"""
        if self.undo_stack:
            return self.undo_stack[-1].get_info()
        return None

    def find_command_by_id(self, command_id: str) -> Optional[Command]:
        """根据ID查找命令"""
        for cmd in self.undo_stack:
            if cmd.command_id == command_id:
                return cmd
        for cmd in self.redo_stack:
            if cmd.command_id == command_id:
                return cmd
        return None

    def _estimate_memory_usage(self) -> int:
        """估算内存使用量"""
        import sys

        total_size = 0
        for cmd in self.undo_stack + self.redo_stack:
            total_size += sys.getsizeof(cmd)

        return total_size


# 具体的命令实现示例
class ModifyPropertyCommand(Command):
    """修改属性命令"""

    def __init__(self, obj: Any, property_name: str, new_value: Any,
                 old_value: Optional[Any] = None, description: Optional[str] = None):
        if description is None:
            description = f"修改属性 {property_name}"
        super().__init__(description, str(id(obj)))

        self.obj = obj
        self.property_name = property_name
        self.new_value = new_value
        self.old_value = old_value if old_value is not None else getattr(obj, property_name, None)

    def execute(self) -> Any:
        """执行修改"""
        setattr(self.obj, self.property_name, self.new_value)
        return self.new_value

    def undo(self) -> Any:
        """撤销修改"""
        setattr(self.obj, self.property_name, self.old_value)
        return self.old_value

    def redo(self) -> Any:
        """重做修改"""
        return self.execute()

    def get_command_type(self) -> CommandType:
        return CommandType.MODIFY


class CreateObjectCommand(Command):
    """创建对象命令"""

    def __init__(self, container: List[Any], obj: Any, index: int = -1,
                 description: Optional[str] = None):
        if description is None:
            description = f"创建 {type(obj).__name__}"
        super().__init__(description, str(id(obj)))

        self.container = container
        self.obj = obj
        self.index = index

    def execute(self) -> Any:
        """执行创建"""
        if self.index == -1:
            self.container.append(self.obj)
        else:
            self.container.insert(self.index, self.obj)
        return self.obj

    def undo(self) -> Any:
        """撤销创建"""
        if self.obj in self.container:
            self.container.remove(self.obj)
        return self.obj

    def redo(self) -> Any:
        """重做创建"""
        return self.execute()

    def get_command_type(self) -> CommandType:
        return CommandType.CREATE


class DeleteObjectCommand(Command):
    """删除对象命令"""

    def __init__(self, container: List[Any], obj: Any,
                 description: Optional[str] = None):
        if description is None:
            description = f"删除 {type(obj).__name__}"
        super().__init__(description, str(id(obj)))

        self.container = container
        self.obj = obj
        self.index = container.index(obj) if obj in container else -1

    def execute(self) -> Any:
        """执行删除"""
        if self.obj in self.container:
            self.index = self.container.index(self.obj)
            self.container.remove(self.obj)
        return self.obj

    def undo(self) -> Any:
        """撤销删除"""
        if self.index == -1:
            self.container.append(self.obj)
        else:
            self.container.insert(self.index, self.obj)
        return self.obj

    def redo(self) -> Any:
        """重做删除"""
        return self.execute()

    def get_command_type(self) -> CommandType:
        return CommandType.DELETE


class MoveObjectCommand(Command):
    """移动对象命令"""

    def __init__(self, container: List[Any], obj: Any, new_index: int,
                 description: Optional[str] = None):
        if description is None:
            description = f"移动 {type(obj).__name__}"
        super().__init__(description, str(id(obj)))

        self.container = container
        self.obj = obj
        self.new_index = new_index
        self.old_index = container.index(obj) if obj in container else -1

    def execute(self) -> Any:
        """执行移动"""
        if self.obj in self.container:
            self.old_index = self.container.index(self.obj)
            self.container.remove(self.obj)
            self.container.insert(self.new_index, self.obj)
        return self.obj

    def undo(self) -> Any:
        """撤销移动"""
        if self.obj in self.container:
            self.container.remove(self.obj)
            if self.old_index != -1:
                self.container.insert(self.old_index, self.obj)
            else:
                self.container.append(self.obj)
        return self.obj

    def redo(self) -> Any:
        """重做移动"""
        return self.execute()

    def get_command_type(self) -> CommandType:
        return CommandType.MOVE


# 便捷函数
def create_undo_manager(max_history: int = 1000,
                      logger: Optional[Logger] = None,
                      event_bus: Optional[EventBus] = None) -> UndoManager:
    """创建撤销管理器"""
    return UndoManager(max_history, logger, event_bus)


def create_batch_command(commands: List[Command],
                        description: str = "Batch Operation") -> BatchCommand:
    """创建批量命令"""
    return BatchCommand(commands, description)


# 全局撤销管理器（需要在服务系统初始化后设置）
_undo_manager = None


def get_undo_manager() -> UndoManager:
    """获取全局撤销管理器"""
    global _undo_manager
    if _undo_manager is None:
        raise RuntimeError("Undo manager not initialized")
    return _undo_manager


def set_undo_manager(manager: UndoManager) -> None:
    """设置全局撤销管理器"""
    global _undo_manager
    _undo_manager = manager


def execute_command(command: Command) -> Any:
    """执行全局命令"""
    return get_undo_manager().execute_command(command)


def undo() -> Optional[Any]:
    """全局撤销"""
    return get_undo_manager().undo()


def redo() -> Optional[Any]:
    """全局重做"""
    return get_undo_manager().redo()