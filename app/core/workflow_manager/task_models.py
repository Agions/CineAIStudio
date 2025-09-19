#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
任务和工作流数据模型
"""

import uuid
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"      # 等待中
    RUNNING = "running"      # 运行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 已取消


@dataclass
class TaskResult:
    """任务结果"""
    success: bool = True
    data: Any = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Task:
    """任务模型"""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0  # 0-100
    
    # 执行相关
    executor: Optional[Callable] = None
    params: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # 依赖的任务ID
    
    # 时间信息
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 结果
    result: Optional[TaskResult] = None
    
    # 回调函数
    progress_callback: Optional[Callable[[float, str], None]] = None
    completion_callback: Optional[Callable[['Task'], None]] = None
    
    def start(self):
        """开始任务"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()
        self.progress = 0.0
    
    def complete(self, result: TaskResult):
        """完成任务"""
        self.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.progress = 100.0
        self.result = result
        
        if self.completion_callback:
            self.completion_callback(self)
    
    def cancel(self):
        """取消任务"""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now()
    
    def update_progress(self, progress: float, message: str = ""):
        """更新进度"""
        self.progress = max(0.0, min(100.0, progress))
        
        if self.progress_callback:
            self.progress_callback(progress, message)
    
    @property
    def duration(self) -> Optional[float]:
        """获取任务执行时长(秒)"""
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.now()
        return (end_time - self.started_at).total_seconds()
    
    @property
    def is_finished(self) -> bool:
        """检查任务是否已结束"""
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "progress": self.progress,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration": self.duration,
            "result": {
                "success": self.result.success,
                "error_message": self.result.error_message,
                "metadata": self.result.metadata
            } if self.result else None
        }


@dataclass
class WorkflowStep:
    """工作流步骤"""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    tasks: List[Task] = field(default_factory=list)
    
    # 步骤配置
    parallel: bool = False  # 是否并行执行任务
    optional: bool = False  # 是否可选步骤
    retry_count: int = 0    # 重试次数
    
    def add_task(self, task: Task):
        """添加任务"""
        self.tasks.append(task)
    
    @property
    def status(self) -> TaskStatus:
        """获取步骤状态"""
        if not self.tasks:
            return TaskStatus.COMPLETED
        
        # 检查所有任务状态
        statuses = [task.status for task in self.tasks]
        
        if any(status == TaskStatus.FAILED for status in statuses):
            return TaskStatus.FAILED
        elif any(status == TaskStatus.CANCELLED for status in statuses):
            return TaskStatus.CANCELLED
        elif any(status == TaskStatus.RUNNING for status in statuses):
            return TaskStatus.RUNNING
        elif all(status == TaskStatus.COMPLETED for status in statuses):
            return TaskStatus.COMPLETED
        else:
            return TaskStatus.PENDING
    
    @property
    def progress(self) -> float:
        """获取步骤进度"""
        if not self.tasks:
            return 100.0
        
        total_progress = sum(task.progress for task in self.tasks)
        return total_progress / len(self.tasks)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "progress": self.progress,
            "parallel": self.parallel,
            "optional": self.optional,
            "tasks": [task.to_dict() for task in self.tasks]
        }


class WorkflowTemplate:
    """工作流模板"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.steps: List[WorkflowStep] = []
        self.metadata: Dict[str, Any] = {}
    
    def add_step(self, step: WorkflowStep):
        """添加步骤"""
        self.steps.append(step)
    
    def create_workflow(self, params: Dict[str, Any]) -> 'Workflow':
        """创建工作流实例"""
        workflow = Workflow(
            name=f"{self.name}_{int(time.time())}",
            template=self
        )
        
        # 复制步骤和任务
        for step_template in self.steps:
            step = WorkflowStep(
                name=step_template.name,
                description=step_template.description,
                parallel=step_template.parallel,
                optional=step_template.optional,
                retry_count=step_template.retry_count
            )
            
            # 复制任务（这里需要根据具体需求实现任务创建逻辑）
            for task_template in step_template.tasks:
                task = Task(
                    name=task_template.name,
                    description=task_template.description,
                    executor=task_template.executor,
                    params={**task_template.params, **params}
                )
                step.add_task(task)
            
            workflow.add_step(step)
        
        return workflow


@dataclass
class Workflow:
    """工作流实例"""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    steps: List[WorkflowStep] = field(default_factory=list)
    
    # 工作流状态
    status: TaskStatus = TaskStatus.PENDING
    current_step_index: int = 0
    
    # 时间信息
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 配置
    template: Optional[WorkflowTemplate] = None
    params: Dict[str, Any] = field(default_factory=dict)
    
    # 回调函数
    progress_callback: Optional[Callable[[float, str], None]] = None
    step_callback: Optional[Callable[[WorkflowStep], None]] = None
    completion_callback: Optional[Callable[['Workflow'], None]] = None
    
    def add_step(self, step: WorkflowStep):
        """添加步骤"""
        self.steps.append(step)
    
    def start(self):
        """开始工作流"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()
        self.current_step_index = 0
    
    def complete(self, success: bool = True):
        """完成工作流"""
        self.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        self.completed_at = datetime.now()
        
        if self.completion_callback:
            self.completion_callback(self)
    
    def cancel(self):
        """取消工作流"""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now()
        
        # 取消所有未完成的任务
        for step in self.steps:
            for task in step.tasks:
                if not task.is_finished:
                    task.cancel()
    
    @property
    def current_step(self) -> Optional[WorkflowStep]:
        """获取当前步骤"""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None
    
    @property
    def progress(self) -> float:
        """获取工作流总进度"""
        if not self.steps:
            return 100.0
        
        completed_steps = self.current_step_index
        current_step_progress = 0.0
        
        if self.current_step:
            current_step_progress = self.current_step.progress / 100.0
        
        total_progress = (completed_steps + current_step_progress) / len(self.steps) * 100.0
        return min(100.0, total_progress)
    
    @property
    def duration(self) -> Optional[float]:
        """获取工作流执行时长(秒)"""
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.now()
        return (end_time - self.started_at).total_seconds()
    
    @property
    def is_finished(self) -> bool:
        """检查工作流是否已结束"""
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
    
    def get_all_tasks(self) -> List[Task]:
        """获取所有任务"""
        all_tasks = []
        for step in self.steps:
            all_tasks.extend(step.tasks)
        return all_tasks
    
    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """根据ID获取任务"""
        for task in self.get_all_tasks():
            if task.id == task_id:
                return task
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "progress": self.progress,
            "current_step_index": self.current_step_index,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration": self.duration,
            "steps": [step.to_dict() for step in self.steps],
            "params": self.params
        }
