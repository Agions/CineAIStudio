"""
ClipFlow 核心模块

新增（v2.0 架构优化）：
- async_bridge: 异步桥接，解决 PyQt6 同步 UI 与 async 服务的交互
- unified_config: 统一配置加载器，合并 YAML/.env/默认值
- task_queue: 任务队列，管理耗时任务不阻塞 UI
"""
