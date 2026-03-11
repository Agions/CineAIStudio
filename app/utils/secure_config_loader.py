"""
安全配置加载器
安全地加载 YAML/JSON 配置文件
"""

import os
import json
import logging
from typing import Any, Dict, Optional
from pathlib import Path
import yaml

from ..utils.security import (
    PathValidator,
    InputSanitizer,
    SecurityError,
    ALLOWED_DOCUMENT_EXTENSIONS
)

logger = logging.getLogger(__name__)


class SecureConfigLoader:
    """安全配置加载器"""
    
    def __init__(self, allowed_dirs: list = None):
        """
        初始化安全配置加载器
        
        Args:
            allowed_dirs: 允许加载配置的目录列表
        """
        self.allowed_dirs = allowed_dirs or [
            os.path.expanduser("~/.clipflowcut"),
            os.path.expanduser("~/ClipFlowCut"),
            "/etc/clipflowcut",
            os.path.join(os.path.dirname(__file__), '..', '..', 'config')
        ]
        self.allowed_dirs = [os.path.abspath(d) for d in self.allowed_dirs]
        
        self.path_validator = PathValidator(self.allowed_dirs)
        self.sanitizer = InputSanitizer()
    
    def load_yaml(self, config_path: str) -> Dict[str, Any]:
        """
        安全加载 YAML 配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
            
        Raises:
            SecurityError: 安全验证失败
        """
        # 验证路径
        clean_path = self.sanitizer.sanitize_path(config_path)
        result = self.path_validator.validate(clean_path)
        if not result.passed:
            raise SecurityError(f"配置路径验证失败: {result.message}")
        
        # 验证扩展名
        ext_result = self.path_validator.validate_extension(
            clean_path, 
            {'.yaml', '.yml'}
        )
        if not ext_result.passed:
            raise SecurityError(f"配置文件类型不支持: {ext_result.message}")
        
        # 检查文件大小
        try:
            size = os.path.getsize(clean_path)
            if size > 10 * 1024 * 1024:  # 10MB
                raise SecurityError(f"配置文件过大: {size} bytes")
        except Exception as e:
            raise SecurityError(f"无法检查文件大小: {e}")
        
        # 安全加载 YAML
        try:
            with open(clean_path, 'r', encoding='utf-8') as f:
                # 使用 safe_load 防止代码执行
                config = yaml.safe_load(f)
                
            # 验证配置结构
            config = self._validate_config(config)
            
            logger.info(f"安全加载配置: {clean_path}")
            return config
            
        except yaml.YAMLError as e:
            raise SecurityError(f"YAML 解析错误: {e}")
        except Exception as e:
            raise SecurityError(f"配置加载失败: {e}")
    
    def load_json(self, config_path: str) -> Dict[str, Any]:
        """
        安全加载 JSON 配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        # 验证路径
        clean_path = self.sanitizer.sanitize_path(config_path)
        result = self.path_validator.validate(clean_path)
        if not result.passed:
            raise SecurityError(f"配置路径验证失败: {result.message}")
        
        # 验证扩展名
        ext_result = self.path_validator.validate_extension(
            clean_path, 
            {'.json'}
        )
        if not ext_result.passed:
            raise SecurityError(f"配置文件类型不支持: {ext_result.message}")
        
        # 加载 JSON
        try:
            with open(clean_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            config = self._validate_config(config)
            
            logger.info(f"安全加载 JSON 配置: {clean_path}")
            return config
            
        except json.JSONDecodeError as e:
            raise SecurityError(f"JSON 解析错误: {e}")
        except Exception as e:
            raise SecurityError(f"配置加载失败: {e}")
    
    def _validate_config(self, config: Any) -> Dict[str, Any]:
        """
        验证配置结构
        
        Args:
            config: 配置数据
            
        Returns:
            验证后的配置
            
        Raises:
            SecurityError: 配置验证失败
        """
        if config is None:
            return {}
        
        if not isinstance(config, dict):
            raise SecurityError("配置根元素必须是对象")
        
        # 递归清理配置值
        return self._sanitize_config(config)
    
    def _sanitize_config(self, obj: Any) -> Any:
        """递归清理配置值"""
        if isinstance(obj, dict):
            return {k: self._sanitize_config(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize_config(item) for item in obj]
        elif isinstance(obj, str):
            # 清理字符串配置值
            return self.sanitizer.sanitize_text(obj, max_length=10000)
        else:
            return obj
    
    def save_yaml(self, config: Dict[str, Any], config_path: str) -> None:
        """
        安全保存 YAML 配置
        
        Args:
            config: 配置字典
            config_path: 保存路径
        """
        # 验证路径
        clean_path = self.sanitizer.sanitize_path(config_path)
        result = self.path_validator.validate(clean_path)
        if not result.passed:
            raise SecurityError(f"保存路径验证失败: {result.message}")
        
        # 验证扩展名
        ext_result = self.path_validator.validate_extension(
            clean_path, 
            {'.yaml', '.yml'}
        )
        if not ext_result.passed:
            raise SecurityError(f"配置文件类型不支持: {ext_result.message}")
        
        # 确保目录存在
        dir_path = os.path.dirname(clean_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        # 安全保存
        try:
            with open(clean_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(
                    config, 
                    f, 
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False
                )
            logger.info(f"安全保存配置: {clean_path}")
        except Exception as e:
            raise SecurityError(f"配置保存失败: {e}")


# 全局实例
_config_loader: Optional[SecureConfigLoader] = None


def get_config_loader() -> SecureConfigLoader:
    """获取全局配置加载器"""
    global _config_loader
    if _config_loader is None:
        _config_loader = SecureConfigLoader()
    return _config_loader


def safe_load_yaml(config_path: str) -> Dict[str, Any]:
    """安全加载 YAML 配置的便捷函数"""
    return get_config_loader().load_yaml(config_path)


def safe_load_json(config_path: str) -> Dict[str, Any]:
    """安全加载 JSON 配置的便捷函数"""
    return get_config_loader().load_json(config_path)


def safe_save_yaml(config: Dict[str, Any], config_path: str) -> None:
    """安全保存 YAML 配置的便捷函数"""
    get_config_loader().save_yaml(config, config_path)
