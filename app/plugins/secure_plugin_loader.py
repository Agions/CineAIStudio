"""
安全插件加载器
在加载前验证插件代码安全性
"""

import os
import sys
import hashlib
import importlib.util
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass

from .plugin_interface import PluginInterface, PluginContext, PluginStatus
from .plugin_registry import PluginRegistry
from .plugin_loader import PluginLoader as BaseLoader

logger = logging.getLogger(__name__)


# 允许的 API 白名单
ALLOWED_PLUGIN_API = {
    # 核心 API
    'os.path', 'os.makedirs', 'os.listdir', 'os.path.exists',
    'sys.modules', 'sys.path',
    'logging', 'logging.getLogger',
    'json', 'json.loads', 'json.dumps',
    
    # PyQt6 安全 API
    'PyQt6.QtWidgets', 'PyQt6.QtCore', 'PyQt6.QtGui',
    
    # 应用 API（受限）
    'app.core',
    'app.services',
}

# 危险代码模式
DANGEROUS_PATTERNS = [
    r'eval\s*\(',
    r'exec\s*\(',
    r'__import__\s*\(',
    r'subprocess',
    r'os\.system',
    r'socket\.',
    r'urllib',
    r'requests\.',
    r'open\s*\(\s*["\']\/',
    r'write\s*\(',
    r'mkdir\s*\(\s*["\']\/',
    r'rmdir\s*\(',
    r'remove\s*\(',
    r'unlink\s*\(',
]


@dataclass
class PluginSecurityCheckResult:
    """插件安全检查结果"""
    passed: bool
    message: str
    issues: List[str] = None


class PluginSecurityValidator:
    """插件安全验证器"""
    
    def __init__(self, allowed_plugins_dir: str = None):
        """
        初始化验证器
        
        Args:
            allowed_plugins_dir: 允许加载插件的目录
        """
        self.allowed_plugins_dir = allowed_plugins_dir or os.path.join(
            os.path.dirname(__file__), '..', 'plugins'
        )
        self.allowed_plugins_dir = os.path.abspath(self.allowed_plugins_dir)
    
    def validate_plugin(self, plugin_path: str) -> PluginSecurityCheckResult:
        """
        验证插件安全性
        
        Args:
            plugin_path: 插件文件路径
            
        Returns:
            安全检查结果
        """
        issues = []
        
        # 1. 检查路径是否在允许目录
        abs_path = os.path.abspath(plugin_path)
        if not abs_path.startswith(self.allowed_plugins_dir):
            return PluginSecurityCheckResult(
                False,
                f"插件不在允许目录: {self.allowed_plugins_dir}",
                ["路径不在白名单"]
            )
        
        # 2. 检查插件文件是否存在
        if not os.path.exists(abs_path):
            return PluginSecurityCheckResult(
                False,
                "插件文件不存在",
                ["文件不存在"]
            )
        
        # 3. 检查文件扩展名
        if not abs_path.endswith('.py'):
            return PluginSecurityCheckResult(
                False,
                "只允许加载 Python 插件",
                ["非 Python 文件"]
            )
        
        # 4. 读取并检查代码
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                code = f.read()
        except Exception as e:
            return PluginSecurityCheckResult(
                False,
                f"无法读取插件代码: {e}",
                ["文件读取失败"]
            )
        
        # 5. 检查危险代码模式
        for pattern in DANGEROUS_PATTERNS:
            import re
            matches = re.findall(pattern, code, re.IGNORECASE)
            if matches:
                issues.append(f"发现危险模式: {pattern}")
        
        # 6. 检查文件大小（防止恶意大文件）
        file_size = os.path.getsize(abs_path)
        if file_size > 1024 * 1024:  # 1MB
            issues.append(f"插件文件过大: {file_size} bytes")
        
        if issues:
            return PluginSecurityCheckResult(
                False,
                "插件安全检查未通过",
                issues
            )
        
        return PluginSecurityCheckResult(
            True,
            "插件安全检查通过",
            []
        )
    
    def compute_checksum(self, plugin_path: str) -> str:
        """计算插件文件校验和"""
        sha256 = hashlib.sha256()
        
        with open(plugin_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        
        return sha256.hexdigest()


class SecurePluginLoader:
    """安全的插件加载器"""
    
    def __init__(self, base_loader: BaseLoader):
        """
        初始化安全插件加载器
        
        Args:
            base_loader: 基础插件加载器
        """
        self.base_loader = base_loader
        self.validator = PluginSecurityValidator()
        self._loaded_checksums: Dict[str, str] = {}
    
    def load_plugin(
        self, 
        plugin_id: str, 
        context: PluginContext,
        config: Dict[str, Any] = None
    ) -> Optional[PluginInterface]:
        """
        安全加载插件
        
        Args:
            plugin_id: 插件 ID
            context: 插件上下文
            config: 插件配置
            
        Returns:
            插件实例，失败返回 None
        """
        # 获取插件路径
        entry = self.base_loader.registry.get_plugin_info(plugin_id)
        if not entry:
            logger.error(f"插件未注册: {plugin_id}")
            return None
        
        # 获取插件文件路径
        plugin_path = entry.info.entry_point
        
        # 安全检查
        check_result = self.validator.validate_plugin(plugin_path)
        if not check_result.passed:
            logger.error(f"插件安全检查失败: {plugin_id}")
            logger.error(f"原因: {check_result.message}")
            for issue in check_result.issues:
                logger.error(f"  - {issue}")
            return None
        
        # 校验和检查（检测篡改）
        checksum = self.validator.compute_checksum(plugin_path)
        if plugin_id in self._loaded_checksums:
            if self._loaded_checksums[plugin_id] != checksum:
                logger.error(f"插件已被篡改: {plugin_id}")
                return None
        
        # 保存校验和
        self._loaded_checksums[plugin_id] = checksum
        
        # 调用基础加载器
        plugin = self.base_loader.load_plugin(plugin_id, context, config)
        
        if plugin:
            logger.info(f"安全加载插件成功: {plugin_id}")
        else:
            logger.error(f"插件加载失败: {plugin_id}")
        
        return plugin
    
    def validate_loaded_plugin(self, plugin_id: str) -> bool:
        """
        验证已加载插件的完整性
        
        Args:
            plugin_id: 插件 ID
            
        Returns:
            是否通过验证
        """
        entry = self.base_loader.registry.get_plugin_info(plugin_id)
        if not entry:
            return False
        
        plugin_path = entry.info.entry_point
        
        if not os.path.exists(plugin_path):
            return False
        
        current_checksum = self.validator.compute_checksum(plugin_path)
        
        if plugin_id not in self._loaded_checksums:
            return False
        
        return current_checksum == self._loaded_checksums[plugin_id]
    
    def validate_all_loaded(self) -> Dict[str, bool]:
        """验证所有已加载插件"""
        results = {}
        
        for plugin_id in self.base_loader._loaded_plugins.keys():
            results[plugin_id] = self.validate_loaded_plugin(plugin_id)
        
        return results


# 便捷函数
def create_secure_plugin_loader(base_loader: BaseLoader) -> SecurePluginLoader:
    """创建安全的插件加载器"""
    return SecurePluginLoader(base_loader)
