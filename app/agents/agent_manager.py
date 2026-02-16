"""
Agent 管理器
管理所有Agent的生命周期和协作
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
import asyncio
import uuid

from PyQt6.QtCore import QObject, pyqtSignal

from .base_agent import BaseAgent, AgentState, AgentCapability
from .director_agent import DirectorAgent


class TaskStatus(Enum):
    """任务状态"""
    PENDING = auto()
    ASSIGNED = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass
class AgentTask:
    """Agent任务"""
    task_id: str
    task_type: str
    params: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None


class AgentManager(QObject):
    """
    Agent 管理器
    
    职责：
    1. Agent注册和注销
    2. 任务分配和调度
    3. 状态监控
    4. 资源管理
    """
    
    # 信号
    agent_registered = pyqtSignal(str)  # agent_id
    agent_unregistered = pyqtSignal(str)  # agent_id
    task_created = pyqtSignal(str)  # task_id
    task_started = pyqtSignal(str, str)  # task_id, agent_id
    task_completed = pyqtSignal(str, object)  # task_id, result
    task_failed = pyqtSignal(str, str)  # task_id, error
    system_status_changed = pyqtSignal(dict)  # status
    
    def __init__(self):
        super().__init__()
        
        # Agent注册表
        self.agents: Dict[str, BaseAgent] = {}
        
        # 任务队列
        self.task_queue: List[AgentTask] = []
        self.completed_tasks: List[AgentTask] = []
        
        # Director
        self.director: Optional[DirectorAgent] = None
        
        # 运行状态
        self.is_running = False
        self._scheduler_task = None
        
    def register_agent(self, agent: BaseAgent) -> str:
        """注册Agent"""
        self.agents[agent.agent_id] = agent
        
        # 如果是Director，特殊处理
        if isinstance(agent, DirectorAgent):
            self.director = agent
            # 注册所有现有Agent到Director
            for existing_agent in self.agents.values():
                if existing_agent.agent_id != agent.agent_id:
                    agent.register_agent(existing_agent)
        elif self.director:
            # 注册到Director
            self.director.register_agent(agent)
            
        self.agent_registered.emit(agent.agent_id)
        return agent.agent_id
        
    def unregister_agent(self, agent_id: str) -> bool:
        """注销Agent"""
        if agent_id not in self.agents:
            return False
            
        agent = self.agents[agent_id]
        
        # 如果是Director
        if agent == self.director:
            self.director = None
            
        del self.agents[agent_id]
        self.agent_unregistered.emit(agent_id)
        return True
        
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """获取Agent"""
        return self.agents.get(agent_id)
        
    def get_all_agents(self) -> List[BaseAgent]:
        """获取所有Agent"""
        return list(self.agents.values())
        
    def get_agents_by_capability(
        self,
        capability: AgentCapability
    ) -> List[BaseAgent]:
        """按能力获取Agent"""
        return [
            agent for agent in self.agents.values()
            if agent.has_capability(capability)
        ]
        
    def create_task(
        self,
        task_type: str,
        params: Dict[str, Any]
    ) -> str:
        """创建任务"""
        task_id = str(uuid.uuid4())[:8]
        
        task = AgentTask(
            task_id=task_id,
            task_type=task_type,
            params=params
        )
        
        self.task_queue.append(task)
        self.task_created.emit(task_id)
        
        return task_id
        
    def create_project_task(
        self,
        project_params: Dict[str, Any]
    ) -> str:
        """
        创建项目任务
        
        使用Director协调多个Agent
        """
        if not self.director:
            raise RuntimeError("Director未注册，无法创建项目任务")
            
        return self.create_task(
            'project',
            {
                'director': self.director.agent_id,
                'project': project_params,
                'agents': list(self.agents.keys())
            }
        )
        
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        for task in self.task_queue:
            if task.task_id == task_id:
                if task.status in [TaskStatus.PENDING, TaskStatus.ASSIGNED]:
                    task.status = TaskStatus.CANCELLED
                    return True
        return False
        
    def get_task(self, task_id: str) -> Optional[AgentTask]:
        """获取任务"""
        for task in self.task_queue:
            if task.task_id == task_id:
                return task
        for task in self.completed_tasks:
            if task.task_id == task_id:
                return task
        return None
        
    def get_all_tasks(self) -> List[AgentTask]:
        """获取所有任务"""
        return self.task_queue + self.completed_tasks
        
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计"""
        total = len(self.agents)
        working = sum(1 for a in self.agents.values() if a.state == AgentState.WORKING)
        idle = sum(1 for a in self.agents.values() if a.state == AgentState.IDLE)
        error = sum(1 for a in self.agents.values() if a.state == AgentState.ERROR)
        
        pending_tasks = sum(1 for t in self.task_queue if t.status == TaskStatus.PENDING)
        running_tasks = sum(1 for t in self.task_queue if t.status == TaskStatus.RUNNING)
        completed_tasks = len(self.completed_tasks)
        
        return {
            'total_agents': total,
            'working_agents': working,
            'idle_agents': idle,
            'error_agents': error,
            'pending_tasks': pending_tasks,
            'running_tasks': running_tasks,
            'completed_tasks': completed_tasks,
            'has_director': self.director is not None
        }
        
    def start(self):
        """启动管理器"""
        if self.is_running:
            return
            
        self.is_running = True
        
        # 启动调度器
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        
    def stop(self):
        """停止管理器"""
        self.is_running = False
        
        if self._scheduler_task:
            self._scheduler_task.cancel()
            
    async def _scheduler_loop(self):
        """调度器循环"""
        while self.is_running:
            try:
                await self._process_tasks()
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"调度器错误: {e}")
                
    async def _process_tasks(self):
        """处理任务队列"""
        for task in self.task_queue:
            if task.status == TaskStatus.PENDING:
                await self._assign_task(task)
            elif task.status == TaskStatus.ASSIGNED:
                # 检查Agent是否开始执行
                pass
                
    async def _assign_task(self, task: AgentTask):
        """分配任务给Agent"""
        task_type = task.task_type
        
        # 查找合适的Agent
        capability_map = {
            'editing': AgentCapability.EDITING,
            'color_grading': AgentCapability.COLOR_GRADING,
            'sound_design': AgentCapability.SOUND_DESIGN,
            'vfx': AgentCapability.VFX,
            'script': AgentCapability.SCRIPT_WRITING,
            'review': AgentCapability.REVIEW,
            'project': AgentCapability.PLANNING
        }
        
        capability = capability_map.get(task_type)
        
        if task_type == 'project' and self.director:
            # 项目任务分配给Director
            agent = self.director
        elif capability:
            # 查找有能力的空闲Agent
            candidates = [
                a for a in self.agents.values()
                if a.has_capability(capability) and a.state == AgentState.IDLE
            ]
            agent = candidates[0] if candidates else None
        else:
            agent = None
            
        if agent:
            task.assigned_agent = agent.agent_id
            task.status = TaskStatus.ASSIGNED
            task.started_at = datetime.now()
            
            self.task_started.emit(task.task_id, agent.agent_id)
            
            # 启动任务
            asyncio.create_task(self._execute_task(task, agent))
            
    async def _execute_task(self, task: AgentTask, agent: BaseAgent):
        """执行任务"""
        task.status = TaskStatus.RUNNING
        
        try:
            result = await agent.run(task.params)
            
            task.result = result
            task.completed_at = datetime.now()
            
            if result.success:
                task.status = TaskStatus.COMPLETED
                self.task_completed.emit(task.task_id, result)
            else:
                task.status = TaskStatus.FAILED
                task.error = result.message
                self.task_failed.emit(task.task_id, result.message)
                
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            self.task_failed.emit(task.task_id, str(e))
            
        # 移动到已完成列表
        self.task_queue.remove(task)
        self.completed_tasks.append(task)
        
    def reset_agent(self, agent_id: str):
        """重置Agent"""
        if agent_id in self.agents:
            self.agents[agent_id].reset()
            
    def start_all(self):
        """启动所有Agent"""
        for agent in self.agents.values():
            if agent.state == AgentState.IDLE:
                # Agent在空闲状态下等待任务
                pass
                
    def stop_all(self):
        """停止所有Agent"""
        for agent in self.agents.values():
            if agent.state == AgentState.WORKING:
                # 取消当前任务
                pass
                
    def reset_all(self):
        """重置所有Agent"""
        for agent in self.agents.values():
            agent.reset()
