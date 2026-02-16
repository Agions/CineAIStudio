"""
多Agent任务调度器
支持复杂任务编排、并行执行、依赖管理
"""

from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor

from PyQt6.QtCore import QObject, pyqtSignal

from .base_agent import BaseAgent, AgentState, AgentCapability


class TaskPriority(Enum):
    """任务优先级"""
    CRITICAL = 0    # 关键任务
    HIGH = 1        # 高优先级
    NORMAL = 2      # 普通
    LOW = 3         # 低优先级
    BACKGROUND = 4  # 后台任务


class TaskState(Enum):
    """任务状态"""
    PENDING = auto()      # 等待中
    WAITING = auto()      # 等待依赖
    SCHEDULED = auto()    # 已调度
    RUNNING = auto()      # 运行中
    COMPLETED = auto()    # 已完成
    FAILED = auto()       # 失败
    CANCELLED = auto()    # 已取消
    TIMEOUT = auto()      # 超时


@dataclass
class TaskDependency:
    """任务依赖"""
    task_id: str
    required_state: TaskState = TaskState.COMPLETED  # 依赖任务需要达到的状态
    optional: bool = False  # 是否为可选依赖


@dataclass
class ScheduledTask:
    """调度任务"""
    task_id: str
    name: str
    task_type: str
    params: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    
    # 执行配置
    agent_id: Optional[str] = None  # 指定Agent
    required_capabilities: List[AgentCapability] = field(default_factory=list)
    
    # 依赖管理
    dependencies: List[TaskDependency] = field(default_factory=list)
    
    # 超时配置
    timeout_seconds: Optional[float] = None
    
    # 重试配置
    max_retries: int = 0
    retry_count: int = 0
    
    # 状态
    state: TaskState = TaskState.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 结果
    result: Optional[Any] = None
    error: Optional[str] = None
    
    # 回调
    on_success: Optional[Callable] = None
    on_failure: Optional[Callable] = None
    on_progress: Optional[Callable] = None
    
    # 子任务（用于工作流）
    subtasks: List[str] = field(default_factory=list)
    parent_task: Optional[str] = None


@dataclass
class WorkflowDefinition:
    """工作流定义"""
    name: str
    description: str
    tasks: List[ScheduledTask]
    
    # 执行策略
    parallel: bool = False  # 是否并行执行
    max_parallel: int = 3   # 最大并行数
    
    # 全局配置
    default_timeout: float = 300.0
    default_retries: int = 1


class TaskScheduler(QObject):
    """
    多Agent任务调度器
    
    特性：
    1. 优先级队列
    2. 依赖管理
    3. 并行执行
    4. 超时控制
    5. 自动重试
    6. 工作流支持
    """
    
    # 信号
    task_created = pyqtSignal(str)  # task_id
    task_started = pyqtSignal(str, str)  # task_id, agent_id
    task_progress = pyqtSignal(str, int, str)  # task_id, progress, message
    task_completed = pyqtSignal(str, object)  # task_id, result
    task_failed = pyqtSignal(str, str)  # task_id, error
    task_cancelled = pyqtSignal(str)  # task_id
    
    workflow_started = pyqtSignal(str)  # workflow_id
    workflow_completed = pyqtSignal(str, object)  # workflow_id, results
    workflow_failed = pyqtSignal(str, str)  # workflow_id, error
    
    def __init__(self, agent_manager):
        super().__init__()
        
        self.agent_manager = agent_manager
        
        # 任务存储
        self.tasks: Dict[str, ScheduledTask] = {}
        self.task_queue: List[str] = []  # 按优先级排序的任务ID队列
        
        # 工作流存储
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.workflow_instances: Dict[str, Dict[str, Any]] = {}
        
        # 执行状态
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.is_running = False
        self._scheduler_task = None
        
        # 线程池（用于阻塞操作）
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # 锁
        self._lock = asyncio.Lock()
        
    async def start(self):
        """启动调度器"""
        if self.is_running:
            return
            
        self.is_running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        print("✅ 任务调度器已启动")
        
    async def stop(self):
        """停止调度器"""
        self.is_running = False
        
        # 取消所有运行中的任务
        for task_id, task in list(self.running_tasks.items()):
            task.cancel()
            
        if self._scheduler_task:
            self._scheduler_task.cancel()
            
        self.executor.shutdown(wait=True)
        print("⏹️  任务调度器已停止")
        
    def create_task(
        self,
        name: str,
        task_type: str,
        params: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        agent_id: Optional[str] = None,
        required_capabilities: Optional[List[AgentCapability]] = None,
        dependencies: Optional[List[TaskDependency]] = None,
        timeout_seconds: Optional[float] = None,
        max_retries: int = 0,
        on_success: Optional[Callable] = None,
        on_failure: Optional[Callable] = None,
        on_progress: Optional[Callable] = None
    ) -> str:
        """
        创建任务
        
        Args:
            name: 任务名称
            task_type: 任务类型
            params: 任务参数
            priority: 优先级
            agent_id: 指定Agent（可选）
            required_capabilities: 所需能力
            dependencies: 依赖任务
            timeout_seconds: 超时时间
            max_retries: 最大重试次数
            on_success: 成功回调
            on_failure: 失败回调
            on_progress: 进度回调
            
        Returns:
            task_id: 任务ID
        """
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            task_type=task_type,
            params=params,
            priority=priority,
            agent_id=agent_id,
            required_capabilities=required_capabilities or [],
            dependencies=dependencies or [],
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            on_success=on_success,
            on_failure=on_failure,
            on_progress=on_progress
        )
        
        self.tasks[task_id] = task
        
        # 检查依赖
        if self._check_dependencies_ready(task):
            task.state = TaskState.PENDING
            self._add_to_queue(task_id)
        else:
            task.state = TaskState.WAITING
            
        self.task_created.emit(task_id)
        return task_id
        
    def create_workflow(
        self,
        name: str,
        description: str,
        tasks_config: List[Dict[str, Any]],
        parallel: bool = False,
        max_parallel: int = 3
    ) -> str:
        """
        创建工作流
        
        Args:
            name: 工作流名称
            description: 描述
            tasks_config: 任务配置列表
            parallel: 是否并行执行
            max_parallel: 最大并行数
            
        Returns:
            workflow_id: 工作流ID
        """
        workflow_id = f"wf_{uuid.uuid4().hex[:8]}"
        
        tasks = []
        for config in tasks_config:
            task = ScheduledTask(
                task_id=f"{workflow_id}_{config['name']}",
                name=config['name'],
                task_type=config['task_type'],
                params=config.get('params', {}),
                priority=TaskPriority(config.get('priority', 2)),
                agent_id=config.get('agent_id'),
                required_capabilities=config.get('required_capabilities', []),
                dependencies=[
                    TaskDependency(**dep) for dep in config.get('dependencies', [])
                ],
                timeout_seconds=config.get('timeout_seconds'),
                max_retries=config.get('max_retries', 0)
            )
            tasks.append(task)
            
        workflow = WorkflowDefinition(
            name=name,
            description=description,
            tasks=tasks,
            parallel=parallel,
            max_parallel=max_parallel
        )
        
        self.workflows[workflow_id] = workflow
        return workflow_id
        
    async def start_workflow(self, workflow_id: str, global_params: Optional[Dict] = None) -> str:
        """启动工作流"""
        if workflow_id not in self.workflows:
            raise ValueError(f"工作流不存在: {workflow_id}")
            
        workflow = self.workflows[workflow_id]
        instance_id = f"{workflow_id}_run_{uuid.uuid4().hex[:6]}"
        
        # 创建工作流实例
        self.workflow_instances[instance_id] = {
            'workflow_id': workflow_id,
            'task_ids': [],
            'results': {},
            'state': 'running',
            'started_at': datetime.now(),
            'global_params': global_params or {}
        }
        
        self.workflow_started.emit(instance_id)
        
        try:
            if workflow.parallel:
                # 并行执行
                await self._run_workflow_parallel(instance_id, workflow, global_params)
            else:
                # 串行执行
                await self._run_workflow_sequential(instance_id, workflow, global_params)
                
        except Exception as e:
            self.workflow_instances[instance_id]['state'] = 'failed'
            self.workflow_failed.emit(instance_id, str(e))
            
        return instance_id
        
    async def _run_workflow_sequential(
        self,
        instance_id: str,
        workflow: WorkflowDefinition,
        global_params: Optional[Dict]
    ):
        """串行执行工作流"""
        instance = self.workflow_instances[instance_id]
        
        for task_template in workflow.tasks:
            # 合并全局参数
            params = {**(global_params or {}), **task_template.params}
            
            # 创建实际任务
            task_id = self.create_task(
                name=task_template.name,
                task_type=task_template.task_type,
                params=params,
                priority=task_template.priority,
                agent_id=task_template.agent_id,
                required_capabilities=task_template.required_capabilities,
                dependencies=task_template.dependencies,
                timeout_seconds=task_template.timeout_seconds or workflow.default_timeout,
                max_retries=task_template.max_retries or workflow.default_retries
            )
            
            instance['task_ids'].append(task_id)
            
            # 等待任务完成
            while True:
                task = self.tasks.get(task_id)
                if not task:
                    break
                    
                if task.state in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED]:
                    if task.state == TaskState.COMPLETED:
                        instance['results'][task_template.name] = task.result
                    else:
                        raise Exception(f"任务 {task_template.name} 失败: {task.error}")
                    break
                    
                await asyncio.sleep(0.5)
                
        instance['state'] = 'completed'
        instance['completed_at'] = datetime.now()
        self.workflow_completed.emit(instance_id, instance['results'])
        
    async def _run_workflow_parallel(
        self,
        instance_id: str,
        workflow: WorkflowDefinition,
        global_params: Optional[Dict]
    ):
        """并行执行工作流"""
        instance = self.workflow_instances[instance_id]
        
        # 创建所有任务
        task_map = {}  # name -> task_id
        for task_template in workflow.tasks:
            params = {**(global_params or {}), **task_template.params}
            
            # 更新依赖为实际task_id
            dependencies = []
            for dep in task_template.dependencies:
                if dep.task_id in task_map:
                    dependencies.append(TaskDependency(
                        task_id=task_map[dep.task_id],
                        required_state=dep.required_state,
                        optional=dep.optional
                    ))
                    
            task_id = self.create_task(
                name=task_template.name,
                task_type=task_template.task_type,
                params=params,
                priority=task_template.priority,
                agent_id=task_template.agent_id,
                required_capabilities=task_template.required_capabilities,
                dependencies=dependencies,
                timeout_seconds=task_template.timeout_seconds or workflow.default_timeout,
                max_retries=task_template.max_retries or workflow.default_retries
            )
            
            task_map[task_template.name] = task_id
            instance['task_ids'].append(task_id)
            
        # 等待所有任务完成
        semaphore = asyncio.Semaphore(workflow.max_parallel)
        
        async def wait_task(task_id: str, task_name: str):
            async with semaphore:
                while True:
                    task = self.tasks.get(task_id)
                    if not task:
                        break
                        
                    if task.state in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED]:
                        if task.state == TaskState.COMPLETED:
                            instance['results'][task_name] = task.result
                        break
                        
                    await asyncio.sleep(0.5)
                    
        # 并发等待
        await asyncio.gather(*[
            wait_task(task_id, task_template.name)
            for task_template, task_id in zip(workflow.tasks, instance['task_ids'])
        ])
        
        instance['state'] = 'completed'
        instance['completed_at'] = datetime.now()
        self.workflow_completed.emit(instance_id, instance['results'])
        
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self.tasks.get(task_id)
        if not task:
            return False
            
        if task.state in [TaskState.PENDING, TaskState.WAITING, TaskState.SCHEDULED]:
            task.state = TaskState.CANCELLED
            if task_id in self.task_queue:
                self.task_queue.remove(task_id)
            self.task_cancelled.emit(task_id)
            return True
            
        if task.state == TaskState.RUNNING and task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
            return True
            
        return False
        
    def cancel_workflow(self, instance_id: str) -> bool:
        """取消工作流"""
        instance = self.workflow_instances.get(instance_id)
        if not instance:
            return False
            
        for task_id in instance['task_ids']:
            self.cancel_task(task_id)
            
        instance['state'] = 'cancelled'
        return True
        
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        task = self.tasks.get(task_id)
        if not task:
            return None
            
        return {
            'task_id': task.task_id,
            'name': task.name,
            'state': task.state.name,
            'priority': task.priority.name,
            'agent_id': task.agent_id,
            'created_at': task.created_at.isoformat(),
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'progress': self._get_task_progress(task),
            'error': task.error
        }
        
    def get_workflow_status(self, instance_id: str) -> Optional[Dict]:
        """获取工作流状态"""
        instance = self.workflow_instances.get(instance_id)
        if not instance:
            return None
            
        workflow = self.workflows[instance['workflow_id']]
        
        total_tasks = len(instance['task_ids'])
        completed_tasks = sum(
            1 for tid in instance['task_ids']
            if self.tasks.get(tid) and self.tasks[tid].state == TaskState.COMPLETED
        )
        
        return {
            'instance_id': instance_id,
            'workflow_name': workflow.name,
            'state': instance['state'],
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'progress': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            'started_at': instance['started_at'].isoformat(),
            'completed_at': instance.get('completed_at', {}).isoformat() if instance.get('completed_at') else None
        }
        
    def get_scheduler_stats(self) -> Dict:
        """获取调度器统计"""
        return {
            'total_tasks': len(self.tasks),
            'pending_tasks': len(self.task_queue),
            'running_tasks': len(self.running_tasks),
            'completed_tasks': sum(
                1 for t in self.tasks.values() if t.state == TaskState.COMPLETED
            ),
            'failed_tasks': sum(
                1 for t in self.tasks.values() if t.state == TaskState.FAILED
            ),
            'workflows': len(self.workflows),
            'running_workflows': sum(
                1 for w in self.workflow_instances.values() if w['state'] == 'running'
            )
        }
        
    # ============ 内部方法 ============
    
    async def _scheduler_loop(self):
        """调度器主循环"""
        while self.is_running:
            try:
                await self._process_queue()
                await asyncio.sleep(0.5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"调度器错误: {e}")
                
    async def _process_queue(self):
        """处理任务队列"""
        async with self._lock:
            # 按优先级排序
            self.task_queue.sort(
                key=lambda tid: self.tasks[tid].priority.value
            )
            
            # 获取空闲Agent
            idle_agents = [
                agent for agent in self.agent_manager.agents.values()
                if agent.state == AgentState.IDLE
            ]
            
            if not idle_agents:
                return
                
            # 分配任务
            for task_id in self.task_queue[:]:
                if not idle_agents:
                    break
                    
                task = self.tasks[task_id]
                
                # 检查依赖
                if not self._check_dependencies_ready(task):
                    continue
                    
                # 查找合适的Agent
                agent = self._find_best_agent(task, idle_agents)
                if agent:
                    idle_agents.remove(agent)
                    self.task_queue.remove(task_id)
                    
                    # 启动任务
                    asyncio.create_task(self._execute_task(task, agent))
                    
    def _check_dependencies_ready(self, task: ScheduledTask) -> bool:
        """检查依赖是否就绪"""
        for dep in task.dependencies:
            dep_task = self.tasks.get(dep.task_id)
            if not dep_task:
                if dep.optional:
                    continue
                return False
                
            if dep_task.state != dep.required_state:
                return False
                
        return True
        
    def _find_best_agent(
        self,
        task: ScheduledTask,
        available_agents: List[BaseAgent]
    ) -> Optional[BaseAgent]:
        """查找最佳Agent"""
        # 如果指定了Agent
        if task.agent_id:
            for agent in available_agents:
                if agent.agent_id == task.agent_id:
                    return agent
            return None
            
        # 按能力匹配
        candidates = []
        for agent in available_agents:
            if all(agent.has_capability(cap) for cap in task.required_capabilities):
                candidates.append(agent)
                
        # 选择负载最低的
        if candidates:
            return min(candidates, key=lambda a: a.task_count if hasattr(a, 'task_count') else 0)
            
        return None
        
    async def _execute_task(self, task: ScheduledTask, agent: BaseAgent):
        """执行任务"""
        task_id = task.task_id
        task.state = TaskState.RUNNING
        task.started_at = datetime.now()
        task.agent_id = agent.agent_id
        
        self.task_started.emit(task_id, agent.agent_id)
        
        # 创建异步任务
        async def run_with_timeout():
            try:
                result = await asyncio.wait_for(
                    agent.run(task.params),
                    timeout=task.timeout_seconds or 300.0
                )
                return result
            except asyncio.TimeoutError:
                raise TimeoutError(f"任务超时 ({task.timeout_seconds}s)")
                
        # 执行
        try:
            coro = run_with_timeout()
            async_task = asyncio.create_task(coro)
            self.running_tasks[task_id] = async_task
            
            result = await async_task
            
            task.result = result
            task.state = TaskState.COMPLETED
            task.completed_at = datetime.now()
            
            self.task_completed.emit(task_id, result)
            
            # 回调
            if task.on_success:
                try:
                    task.on_success(result)
                except Exception as e:
                    print(f"成功回调错误: {e}")
                    
        except asyncio.CancelledError:
            task.state = TaskState.CANCELLED
            self.task_cancelled.emit(task_id)
            
        except Exception as e:
            task.error = str(e)
            task.retry_count += 1
            
            if task.retry_count <= task.max_retries:
                # 重试
                task.state = TaskState.PENDING
                self._add_to_queue(task_id)
                print(f"任务 {task_id} 失败，准备重试 ({task.retry_count}/{task.max_retries})")
            else:
                task.state = TaskState.FAILED
                self.task_failed.emit(task_id, str(e))
                
                # 回调
                if task.on_failure:
                    try:
                        task.on_failure(e)
                    except Exception as cb_e:
                        print(f"失败回调错误: {cb_e}")
                        
        finally:
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
                
    def _add_to_queue(self, task_id: str):
        """添加任务到队列"""
        if task_id not in self.task_queue:
            self.task_queue.append(task_id)
            
    def _get_task_progress(self, task: ScheduledTask) -> int:
        """获取任务进度"""
        if task.state == TaskState.COMPLETED:
            return 100
        elif task.state == TaskState.RUNNING:
            # 从Agent获取进度
            agent = self.agent_manager.agents.get(task.agent_id)
            if agent:
                return getattr(agent, 'progress', 0)
        return 0
