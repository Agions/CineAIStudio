"""
AI模块 - CineAIStudio人工智能集成系统

提供完整的AI功能，包括：
- 6个中文AI模型的统一管理
- 智能负载均衡和故障转移
- 成本管理和优化
- 内容审核和过滤
- AI功能接口统一化
"""

# 核心管理器
from .ai_manager import AIManager, create_ai_manager

# 模型基类
from .models.base_model import BaseAIModel, AIModelConfig, AIResponse

# 具体模型
from .models.qianwen_model import QianwenModel
from .models.wenxin_model import WenxinModel
from .models.zhipu_model import ZhipuModel
from .models.xunfei_model import XunfeiModel
from .models.hunyuan_model import HunyuanModel
from .models.deepseek_model import DeepSeekModel

# 保持向后兼容
from .ai_manager import AIManager

__version__ = "2.0.0"
__author__ = "CineAIStudio Team"

# 主要导出
__all__ = [
    # 核心管理器
    'AIManager',
    'create_ai_manager',
    
    # 模型基类
    'BaseAIModel',
    'AIModelConfig',
    'AIResponse',
    
    # 具体模型
    'QianwenModel',
    'WenxinModel',
    'ZhipuModel',
    'XunfeiModel',
    'HunyuanModel',
    'DeepSeekModel',
    
    # 向后兼容
    'AIManager'
]
