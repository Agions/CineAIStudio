#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio 云端存储配置
云端存储系统的配置和初始化
"""

import os
import json
import logging
from typing import Dict, Any, Optional

from .cloud_storage import (
    CloudStorageIntegration,
    CloudStorageConfig,
    SecurityPolicy,
    EncryptionAlgorithm,
    AccessLevel,
    Permission
)

from .config_manager import ConfigManager
from .project_manager import ProjectManager


class CloudStorageConfigManager:
    """云端存储配置管理器"""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)

        # 默认配置
        self.default_config = {
            "enabled": False,
            "auto_sync": True,
            "sync_interval": 300,  # 5分钟
            "sync_mode": "bidirectional",
            "conflict_resolution": "newer_wins",
            "enable_compression": True,
            "enable_encryption": True,
            "cache_level": "hybrid",
            "max_concurrent_transfers": 4,
            "enable_cdn": True,
            "backup_enabled": True,
            "backup_interval": 3600,  # 1小时
            "version_control_enabled": True,
            "max_versions": 10,
            "storage_backend": {
                "provider": "aws_s3",
                "aws_access_key_id": "",
                "aws_secret_access_key": "",
                "aws_region": "us-east-1",
                "aws_s3_bucket": "cineaistudio-storage",
                "sync_chunk_size": 64 * 1024 * 1024,  # 64MB
                "max_concurrent_uploads": 4,
                "max_concurrent_downloads": 4,
                "retry_attempts": 3,
                "cache_size": 10 * 1024 * 1024 * 1024  # 10GB
            },
            "security": {
                "encryption_algorithm": "aes_256_gcm",
                "key_rotation_days": 90,
                "access_level": "private",
                "password_policy": {
                    "min_length": 12,
                    "require_uppercase": True,
                    "require_lowercase": True,
                    "require_numbers": True,
                    "require_special_chars": True,
                    "max_age_days": 90
                },
                "session_timeout_minutes": 30,
                "max_login_attempts": 5,
                "lockout_duration_minutes": 30,
                "enable_two_factor": True,
                "audit_enabled": True
            },
            "performance": {
                "memory_cache_size": 1024 * 1024 * 1024,  # 1GB
                "disk_cache_size": 10 * 1024 * 1024 * 1024,  # 10GB
                "compression_algorithm": "zstd",
                "compression_threshold": 1024 * 1024,  # 1MB
                "cdn_provider": "cloudflare",
                "cdn_routing_enabled": True,
                "bandwidth_throttling": 0,  # 0表示无限制
                "transfer_timeout": 300  # 5分钟
            }
        }

    def get_config(self) -> Dict[str, Any]:
        """获取云端存储配置"""
        return self.config_manager.get('cloud_storage', self.default_config)

    def save_config(self, config: Dict[str, Any]) -> bool:
        """保存云端存储配置"""
        try:
            self.config_manager.set('cloud_storage', config)
            self.config_manager.save()
            return True
        except Exception as e:
            self.logger.error(f"Failed to save cloud storage config: {e}")
            return False

    def update_config(self, updates: Dict[str, Any]) -> bool:
        """更新云端存储配置"""
        try:
            current_config = self.get_config()
            current_config.update(updates)
            return self.save_config(current_config)
        except Exception as e:
            self.logger.error(f"Failed to update cloud storage config: {e}")
            return False

    def create_cloud_storage_config(self) -> CloudStorageConfig:
        """创建云端存储配置对象"""
        config = self.get_config()
        storage_config = CloudStorageConfig()

        # 设置AWS S3配置
        if config['storage_backend']['provider'] == 'aws_s3':
            storage_config.aws_access_key_id = config['storage_backend']['aws_access_key_id']
            storage_config.aws_secret_access_key = config['storage_backend']['aws_secret_access_key']
            storage_config.aws_region = config['storage_backend']['aws_region']
            storage_config.aws_s3_bucket = config['storage_backend']['aws_s3_bucket']

        # 设置同步配置
        storage_config.sync_chunk_size = config['storage_backend']['sync_chunk_size']
        storage_config.max_concurrent_uploads = config['storage_backend']['max_concurrent_uploads']
        storage_config.max_concurrent_downloads = config['storage_backend']['max_concurrent_downloads']
        storage_config.retry_attempts = config['storage_backend']['retry_attempts']
        storage_config.cache_size = config['storage_backend']['cache_size']

        # 设置基本配置
        storage_config.enable_compression = config['enable_compression']
        storage_config.enable_encryption = config['enable_encryption']
        storage_config.auto_sync = config['auto_sync']
        storage_config.sync_interval = config['sync_interval']
        storage_config.enable_cdn = config['enable_cdn']

        return storage_config

    def create_security_policy(self) -> SecurityPolicy:
        """创建安全策略"""
        config = self.get_config()
        security_config = config['security']

        return SecurityPolicy(
            policy_id="default",
            name="CineAIStudio Security Policy",
            description="Security policy for CineAIStudio cloud storage",
            encryption_algorithm=EncryptionAlgorithm(security_config['encryption_algorithm']),
            key_rotation_days=security_config['key_rotation_days'],
            access_level=AccessLevel(security_config['access_level']),
            allowed_permissions=[
                Permission.READ,
                Permission.WRITE,
                Permission.DELETE
            ],
            password_policy=security_config['password_policy'],
            session_timeout_minutes=security_config['session_timeout_minutes'],
            max_login_attempts=security_config['max_login_attempts'],
            lockout_duration_minutes=security_config['lockout_duration_minutes'],
            enable_two_factor=security_config['enable_two_factor'],
            audit_enabled=security_config['audit_enabled']
        )

    def is_enabled(self) -> bool:
        """检查云端存储是否启用"""
        config = self.get_config()
        return config.get('enabled', False)

    def enable_cloud_storage(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """启用云端存储"""
        try:
            if config:
                updates = config.copy()
                updates['enabled'] = True
                return self.update_config(updates)
            else:
                return self.update_config({'enabled': True})
        except Exception as e:
            self.logger.error(f"Failed to enable cloud storage: {e}")
            return False

    def disable_cloud_storage(self) -> bool:
        """禁用云端存储"""
        try:
            return self.update_config({'enabled': False})
        except Exception as e:
            self.logger.error(f"Failed to disable cloud storage: {e}")
            return False

    def get_aws_credentials(self) -> Dict[str, str]:
        """获取AWS凭证"""
        config = self.get_config()
        return {
            'access_key_id': config['storage_backend']['aws_access_key_id'],
            'secret_access_key': config['storage_backend']['aws_secret_access_key'],
            'region': config['storage_backend']['aws_region'],
            'bucket': config['storage_backend']['aws_s3_bucket']
        }

    def set_aws_credentials(self, access_key_id: str, secret_access_key: str,
                           region: str, bucket: str) -> bool:
        """设置AWS凭证"""
        try:
            updates = {
                'storage_backend': {
                    'provider': 'aws_s3',
                    'aws_access_key_id': access_key_id,
                    'aws_secret_access_key': secret_access_key,
                    'aws_region': region,
                    'aws_s3_bucket': bucket
                }
            }
            return self.update_config(updates)
        except Exception as e:
            self.logger.error(f"Failed to set AWS credentials: {e}")
            return False

    def export_config(self, file_path: str) -> bool:
        """导出配置到文件"""
        try:
            config = self.get_config()
            # 移除敏感信息
            safe_config = self._sanitize_config(config)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(safe_config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(f"Failed to export config: {e}")
            return False

    def import_config(self, file_path: str) -> bool:
        """从文件导入配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)

            # 合并配置，保留敏感信息
            current_config = self.get_config()
            merged_config = self._merge_configs(current_config, imported_config)

            return self.save_config(merged_config)
        except Exception as e:
            self.logger.error(f"Failed to import config: {e}")
            return False

    def _sanitize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """清理配置中的敏感信息"""
        safe_config = config.copy()

        # 清理AWS凭证
        if 'storage_backend' in safe_config:
            safe_config['storage_backend'] = safe_config['storage_backend'].copy()
            safe_config['storage_backend']['aws_access_key_id'] = '***REDACTED***'
            safe_config['storage_backend']['aws_secret_access_key'] = '***REDACTED***'

        return safe_config

    def _merge_configs(self, current: Dict[str, Any], imported: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置"""
        merged = current.copy()

        # 保留敏感信息
        sensitive_keys = [
            'storage_backend.aws_access_key_id',
            'storage_backend.aws_secret_access_key'
        ]

        def set_nested_value(d: Dict[str, Any], key_path: str, value: Any):
            keys = key_path.split('.')
            current = d
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            current[keys[-1]] = value

        # 应用导入的配置
        for key, value in imported.items():
            if isinstance(value, dict) and key in merged:
                merged[key].update(value)
            else:
                merged[key] = value

        # 恢复敏感信息
        for key_path in sensitive_keys:
            value = get_nested_value(current, key_path)
            if value != '***REDACTED***':
                set_nested_value(merged, key_path, value)

        return merged

    def validate_config(self) -> Tuple[bool, List[str]]:
        """验证配置"""
        errors = []
        config = self.get_config()

        try:
            # 检查必需字段
            if config['enabled']:
                if not config['storage_backend']['provider']:
                    errors.append("Storage provider is required")

                if config['storage_backend']['provider'] == 'aws_s3':
                    if not config['storage_backend']['aws_access_key_id']:
                        errors.append("AWS access key ID is required")
                    if not config['storage_backend']['aws_secret_access_key']:
                        errors.append("AWS secret access key is required")
                    if not config['storage_backend']['aws_s3_bucket']:
                        errors.append("AWS S3 bucket is required")

                # 检查数值范围
                if config['sync_interval'] < 60:
                    errors.append("Sync interval must be at least 60 seconds")

                if config['max_concurrent_transfers'] < 1 or config['max_concurrent_transfers'] > 16:
                    errors.append("Max concurrent transfers must be between 1 and 16")

                if config['storage_backend']['sync_chunk_size'] < 1024 * 1024:  # 1MB
                    errors.append("Sync chunk size must be at least 1MB")

                # 检查密码策略
                password_policy = config['security']['password_policy']
                if password_policy['min_length'] < 8:
                    errors.append("Minimum password length must be at least 8 characters")

                if password_policy['max_age_days'] < 1:
                    errors.append("Password max age must be at least 1 day")

            return len(errors) == 0, errors

        except Exception as e:
            errors.append(f"Configuration validation error: {e}")
            return False, errors

    def get_performance_config(self) -> Dict[str, Any]:
        """获取性能配置"""
        config = self.get_config()
        return config.get('performance', {})

    def update_performance_config(self, performance_config: Dict[str, Any]) -> bool:
        """更新性能配置"""
        try:
            return self.update_config({'performance': performance_config})
        except Exception as e:
            self.logger.error(f"Failed to update performance config: {e}")
            return False

    def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        try:
            config = self.get_config()
            return {
                'enabled': config['enabled'],
                'provider': config['storage_backend']['provider'],
                'cache_size': config['storage_backend']['cache_size'],
                'sync_chunk_size': config['storage_backend']['sync_chunk_size'],
                'max_concurrent_transfers': config['max_concurrent_transfers'],
                'compression_enabled': config['enable_compression'],
                'encryption_enabled': config['enable_encryption'],
                'cdn_enabled': config['enable_cdn']
            }
        except Exception as e:
            self.logger.error(f"Failed to get storage stats: {e}")
            return {}

    def reset_to_defaults(self) -> bool:
        """重置为默认配置"""
        try:
            return self.save_config(self.default_config.copy())
        except Exception as e:
            self.logger.error(f"Failed to reset to defaults: {e}")
            return False


def get_nested_value(d: Dict[str, Any], key_path: str) -> Any:
    """获取嵌套字典值"""
    keys = key_path.split('.')
    current = d
    for key in keys:
        if key in current:
            current = current[key]
        else:
            return None
    return current


# 全局配置管理器实例
_config_manager: Optional[CloudStorageConfigManager] = None


def get_cloud_storage_config_manager() -> CloudStorageConfigManager:
    """获取全局云端存储配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        config_manager = ConfigManager()
        _config_manager = CloudStorageConfigManager(config_manager)
    return _config_manager


def initialize_cloud_storage(project_manager: ProjectManager) -> Optional[CloudStorageIntegration]:
    """初始化云端存储集成"""
    try:
        config_manager = get_cloud_storage_config_manager()

        if not config_manager.is_enabled():
            return None

        # 创建云端存储集成
        cloud_config = config_manager.create_cloud_storage_config()
        cloud_integration = CloudStorageIntegration(project_manager, config_manager.config_manager)

        return cloud_integration

    except Exception as e:
        logging.error(f"Failed to initialize cloud storage: {e}")
        return None


# 示例配置
EXAMPLE_CONFIG = {
    "enabled": True,
    "auto_sync": True,
    "sync_interval": 300,
    "sync_mode": "bidirectional",
    "conflict_resolution": "newer_wins",
    "enable_compression": True,
    "enable_encryption": True,
    "cache_level": "hybrid",
    "max_concurrent_transfers": 4,
    "enable_cdn": True,
    "backup_enabled": True,
    "backup_interval": 3600,
    "version_control_enabled": True,
    "max_versions": 10,
    "storage_backend": {
        "provider": "aws_s3",
        "aws_access_key_id": "YOUR_ACCESS_KEY_ID",
        "aws_secret_access_key": "YOUR_SECRET_ACCESS_KEY",
        "aws_region": "us-east-1",
        "aws_s3_bucket": "cineaistudio-storage",
        "sync_chunk_size": 67108864,  # 64MB
        "max_concurrent_uploads": 4,
        "max_concurrent_downloads": 4,
        "retry_attempts": 3,
        "cache_size": 10737418240  # 10GB
    },
    "security": {
        "encryption_algorithm": "aes_256_gcm",
        "key_rotation_days": 90,
        "access_level": "private",
        "password_policy": {
            "min_length": 12,
            "require_uppercase": True,
            "require_lowercase": True,
            "require_numbers": True,
            "require_special_chars": True,
            "max_age_days": 90
        },
        "session_timeout_minutes": 30,
        "max_login_attempts": 5,
        "lockout_duration_minutes": 30,
        "enable_two_factor": True,
        "audit_enabled": True
    },
    "performance": {
        "memory_cache_size": 1073741824,  # 1GB
        "disk_cache_size": 10737418240,  # 10GB
        "compression_algorithm": "zstd",
        "compression_threshold": 1048576,  # 1MB
        "cdn_provider": "cloudflare",
        "cdn_routing_enabled": True,
        "bandwidth_throttling": 0,
        "transfer_timeout": 300
    }
}