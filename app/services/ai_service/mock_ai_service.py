"""
Mock AI Service - 模拟 AI 服务

用于测试和开发环境
"""

from typing import Any, Dict, Optional
import time


class MockAIService:
    """模拟 AI 服务"""

    def __init__(self):
        self.name = "mock_ai_service"
        self._connected = True

    def connect(self) -> bool:
        """连接服务"""
        self._connected = True
        return True

    def disconnect(self):
        """断开连接"""
        self._connected = False

    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._connected

    def process(self, input_data: Any) -> Any:
        """处理输入"""
        time.sleep(0.1)  # 模拟处理时间
        return {"status": "ok", "result": "mock response"}

    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "connected": self._connected,
            "service": self.name,
        }


__all__ = ["MockAIService"]
