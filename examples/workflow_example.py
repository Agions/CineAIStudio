"""
多Agent任务调度示例
展示如何使用TaskScheduler安排多个Agent完成任务
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agents import (
    AgentManager, TaskScheduler, TaskPriority, TaskDependency,
    DirectorAgent, EditorAgent, ColoristAgent, SoundAgent, VFXAgent, ReviewerAgent
)
from app.workflows import VideoEditingWorkflow


async def example_single_task():
    """示例1: 创建单个任务"""
    print("\n" + "="*60)
    print("示例1: 创建单个任务")
    print("="*60)
    
    # 创建Agent管理器
    agent_manager = AgentManager()
    
    # 注册Agent
    agent_manager.register_agent(EditorAgent())
    agent_manager.register_agent(ColoristAgent())
    agent_manager.start()
    
    # 创建任务调度器
    scheduler = TaskScheduler(agent_manager)
    await scheduler.start()
    
    # 创建剪辑任务
    task_id = scheduler.create_task(
        name="剪辑任务1",
        task_type="editing",
        params={
            'video_path': '/path/to/video.mp4',
            'cuts': [(0, 10), (20, 30)]
        },
        priority=TaskPriority.HIGH,
        timeout_seconds=300,
        max_retries=1
    )
    
    print(f"✅ 任务已创建: {task_id}")
    
    # 等待任务完成
    while True:
        status = scheduler.get_task_status(task_id)
        if status['state'] in ['COMPLETED', 'FAILED', 'CANCELLED']:
            print(f"任务完成: {status}")
            break
        await asyncio.sleep(1)
    
    await scheduler.stop()
    agent_manager.stop()


async def example_dependent_tasks():
    """示例2: 创建有依赖关系的任务"""
    print("\n" + "="*60)
    print("示例2: 创建有依赖关系的任务")
    print("="*60)
    
    agent_manager = AgentManager()
    agent_manager.register_agent(EditorAgent())
    agent_manager.register_agent(ColoristAgent())
    agent_manager.start()
    
    scheduler = TaskScheduler(agent_manager)
    await scheduler.start()
    
    # 任务1: 粗剪
    task1_id = scheduler.create_task(
        name="粗剪",
        task_type="editing",
        params={'mode': 'rough'},
        priority=TaskPriority.HIGH
    )
    print(f"✅ 任务1创建: {task1_id}")
    
    # 任务2: 调色（依赖任务1完成）
    task2_id = scheduler.create_task(
        name="调色",
        task_type="color_grading",
        params={'style': 'cinematic'},
        priority=TaskPriority.NORMAL,
        dependencies=[
            TaskDependency(task_id=task1_id, required_state='COMPLETED')
        ]
    )
    print(f"✅ 任务2创建: {task2_id} (依赖 {task1_id})")
    
    # 等待所有任务完成
    task_ids = [task1_id, task2_id]
    while True:
        all_done = True
        for tid in task_ids:
            status = scheduler.get_task_status(tid)
            print(f"  {tid}: {status['state']}")
            if status['state'] not in ['COMPLETED', 'FAILED', 'CANCELLED']:
                all_done = False
        
        if all_done:
            break
        await asyncio.sleep(1)
    
    print("✅ 所有任务完成!")
    
    await scheduler.stop()
    agent_manager.stop()


async def example_workflow():
    """示例3: 使用工作流"""
    print("\n" + "="*60)
    print("示例3: 使用工作流")
    print("="*60)
    
    # 创建Agent管理器并注册所有Agent
    agent_manager = AgentManager()
    agent_manager.register_agent(DirectorAgent())
    agent_manager.register_agent(EditorAgent())
    agent_manager.register_agent(ColoristAgent())
    agent_manager.register_agent(SoundAgent())
    agent_manager.register_agent(VFXAgent())
    agent_manager.register_agent(ReviewerAgent())
    agent_manager.start()
    
    # 创建调度器
    scheduler = TaskScheduler(agent_manager)
    await scheduler.start()
    
    # 创建工作流
    workflow = VideoEditingWorkflow(scheduler)
    
    # 启动标准剪辑工作流
    instance_id = await workflow.start(
        video_path='/path/to/input.mp4',
        output_path='/path/to/output.mp4',
        style='standard'
    )
    
    print(f"✅ 工作流已启动: {instance_id}")
    
    # 监控进度
    while True:
        status = workflow.get_progress(instance_id)
        print(f"\r进度: {status['progress']:.1f}% | 完成: {status['completed_tasks']}/{status['total_tasks']}", end='')
        
        if status['state'] in ['completed', 'failed', 'cancelled']:
            print(f"\n工作流完成: {status['state']}")
            break
            
        await asyncio.sleep(1)
    
    await scheduler.stop()
    agent_manager.stop()


async def example_parallel_workflow():
    """示例4: 并行工作流"""
    print("\n" + "="*60)
    print("示例4: 并行工作流")
    print("="*60)
    
    agent_manager = AgentManager()
    agent_manager.register_agent(DirectorAgent())
    agent_manager.register_agent(EditorAgent())
    agent_manager.register_agent(ColoristAgent())
    agent_manager.register_agent(SoundAgent())
    agent_manager.register_agent(VFXAgent())
    agent_manager.register_agent(ReviewerAgent())
    agent_manager.start()
    
    scheduler = TaskScheduler(agent_manager)
    await scheduler.start()
    
    workflow = VideoEditingWorkflow(scheduler)
    
    # 启动并行工作流（调色和音效同时进行）
    instance_id = await workflow.start(
        video_path='/path/to/input.mp4',
        output_path='/path/to/output.mp4',
        style='parallel'  # 并行模式
    )
    
    print(f"✅ 并行工作流已启动: {instance_id}")
    
    # 监控进度
    while True:
        status = workflow.get_progress(instance_id)
        print(f"\r进度: {status['progress']:.1f}% | 状态: {status['state']}", end='')
        
        if status['state'] in ['completed', 'failed']:
            print(f"\n✅ 工作流完成!")
            break
            
        await asyncio.sleep(1)
    
    await scheduler.stop()
    agent_manager.stop()


async def example_with_callbacks():
    """示例5: 使用回调函数"""
    print("\n" + "="*60)
    print("示例5: 使用回调函数")
    print("="*60)
    
    agent_manager = AgentManager()
    agent_manager.register_agent(EditorAgent())
    agent_manager.start()
    
    scheduler = TaskScheduler(agent_manager)
    await scheduler.start()
    
    # 回调函数
    def on_success(result):
        print(f"✅ 任务成功完成: {result}")
        
    def on_failure(error):
        print(f"❌ 任务失败: {error}")
        
    def on_progress(progress, message):
        print(f"📊 进度: {progress}% - {message}")
    
    # 创建带回调的任务
    task_id = scheduler.create_task(
        name="带回调的任务",
        task_type="editing",
        params={'video_path': '/path/to/video.mp4'},
        on_success=on_success,
        on_failure=on_failure,
        on_progress=on_progress
    )
    
    print(f"✅ 任务已创建: {task_id}")
    
    # 等待完成
    while True:
        status = scheduler.get_task_status(task_id)
        if status['state'] in ['COMPLETED', 'FAILED', 'CANCELLED']:
            break
        await asyncio.sleep(1)
    
    await scheduler.stop()
    agent_manager.stop()


async def main():
    """运行所有示例"""
    print("\n" + "🎬 CineFlow 多Agent任务调度示例")
    print("="*60)
    
    try:
        # 运行示例（选择要运行的示例）
        # await example_single_task()
        # await example_dependent_tasks()
        # await example_workflow()
        # await example_parallel_workflow()
        # await example_with_callbacks()
        
        print("\n💡 请取消注释要运行的示例")
        print("示例代码在 examples/workflow_example.py")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
