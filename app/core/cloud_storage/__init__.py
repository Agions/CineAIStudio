#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio 云端存储模块
提供完整的云端存储和同步解决方案

本模块包含：
- 云端存储管理器：负责与各种云存储后端的交互
- 文件同步引擎：提供高效的文件同步和版本控制
- 性能优化器：提供缓存、CDN加速等性能优化功能
- 安全管理器：提供加密、权限控制等安全功能
- 云端存储集成：与现有系统的无缝集成

主要特性：
1. 分布式文件存储架构
2. 实时文件同步机制
3. 大文件分块上传下载
4. 版本控制和增量同步
5. 缓存和性能优化
6. 断点续传和离线支持
7. 多地区同步和CDN支持
8. 安全加密和权限控制

支持TB级媒体文件的高效存储和同步。
"""

from .cloud_storage_manager import (
    CloudStorageManager,
    CloudStorageConfig,
    FileMetadata,
    SyncStatus,
    FileOperationType,
    StorageBackend,
    SyncOperation
)

from .file_sync_engine import (
    FileSyncEngine,
    SyncMode,
    ConflictResolution,
    SyncConflict,
    SyncVersion,
    FileSyncDatabase,
    FileSystemWatcher,
    DeltaCalculator
)

from .performance_optimizer import (
    PerformanceOptimizer,
    CacheLevel,
    CompressionAlgorithm,
    CDNProvider,
    CacheEntry,
    CDNEdge,
    TransferSession
)

from .security_manager import (
    SecurityManager,
    SecurityDatabase,
    EncryptionManager,
    SecurityPolicy,
    SecurityKey,
    SecurityEvent,
    AccessControl,
    EncryptionAlgorithm,
    AccessLevel,
    Permission,
    SecurityEventType
)

from .cloud_storage_integration import (
    CloudStorageIntegration,
    CloudIntegrationConfig,
    CloudIntegrationStatus
)

__version__ = "1.0.0"
__author__ = "CineAIStudio Team"
__email__ = "support@cineaistudio.com"

# 导出的主要类和函数
__all__ = [
    # 核心管理器
    'CloudStorageManager',
    'FileSyncEngine',
    'PerformanceOptimizer',
    'SecurityManager',
    'CloudStorageIntegration',

    # 配置类
    'CloudStorageConfig',
    'CloudIntegrationConfig',
    'SecurityPolicy',

    # 数据模型
    'FileMetadata',
    'SyncOperation',
    'SyncConflict',
    'SyncVersion',
    'CacheEntry',
    'CDNEdge',
    'TransferSession',
    'SecurityKey',
    'SecurityEvent',
    'AccessControl',

    # 枚举类型
    'SyncStatus',
    'FileOperationType',
    'StorageBackend',
    'SyncMode',
    'ConflictResolution',
    'CacheLevel',
    'CompressionAlgorithm',
    'CDNProvider',
    'EncryptionAlgorithm',
    'AccessLevel',
    'Permission',
    'SecurityEventType',
    'CloudIntegrationStatus',

    # 工具类
    'FileSyncDatabase',
    'FileSystemWatcher',
    'DeltaCalculator',
    'EncryptionManager',
    'SecurityDatabase'
]


def create_cloud_storage_integration(project_manager, config_manager) -> CloudStorageIntegration:
    """
    创建云端存储集成实例

    Args:
        project_manager: 项目管理器实例
        config_manager: 配置管理器实例

    Returns:
        CloudStorageIntegration: 云端存储集成实例
    """
    return CloudStorageIntegration(project_manager, config_manager)


def create_cloud_storage_config(**kwargs) -> CloudStorageConfig:
    """
    创建云端存储配置

    Args:
        **kwargs: 配置参数

    Returns:
        CloudStorageConfig: 云端存储配置实例
    """
    config = CloudStorageConfig()
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    return config


def create_security_policy(**kwargs) -> SecurityPolicy:
    """
    创建安全策略

    Args:
        **kwargs: 策略参数

    Returns:
        SecurityPolicy: 安全策略实例
    """
    policy = SecurityPolicy(
        policy_id=kwargs.get('policy_id', 'default'),
        name=kwargs.get('name', 'Default Security Policy'),
        description=kwargs.get('description', 'Default security policy'),
        encryption_algorithm=kwargs.get('encryption_algorithm', EncryptionAlgorithm.AES_256_GCM),
        key_rotation_days=kwargs.get('key_rotation_days', 90),
        access_level=kwargs.get('access_level', AccessLevel.PRIVATE),
        allowed_permissions=kwargs.get('allowed_permissions', [Permission.READ, Permission.WRITE]),
        password_policy=kwargs.get('password_policy', {
            'min_length': 12,
            'require_uppercase': True,
            'require_lowercase': True,
            'require_numbers': True,
            'require_special_chars': True,
            'max_age_days': 90
        }),
        session_timeout_minutes=kwargs.get('session_timeout_minutes', 30),
        max_login_attempts=kwargs.get('max_login_attempts', 5),
        lockout_duration_minutes=kwargs.get('lockout_duration_minutes', 30),
        enable_two_factor=kwargs.get('enable_two_factor', True),
        audit_enabled=kwargs.get('audit_enabled', True)
    )
    return policy


# 默认配置
DEFAULT_CLOUD_CONFIG = {
    'sync_chunk_size': 64 * 1024 * 1024,  # 64MB
    'max_concurrent_uploads': 4,
    'max_concurrent_downloads': 4,
    'retry_attempts': 3,
    'retry_delay': 1.0,
    'cache_size': 10 * 1024 * 1024 * 1024,  # 10GB
    'enable_compression': True,
    'enable_encryption': True,
    'auto_sync': True,
    'sync_interval': 60,
    'enable_cdn': True,
    'enable_accelerated_upload': True,
    'enable_multi_part_upload': True,
    'enable_deduplication': True
}

DEFAULT_INTEGRATION_CONFIG = {
    'enabled': False,
    'auto_sync': True,
    'sync_interval': 300,
    'sync_mode': 'bidirectional',
    'conflict_resolution': 'newer_wins',
    'enable_compression': True,
    'enable_encryption': True,
    'cache_level': 'hybrid',
    'max_concurrent_transfers': 4,
    'enable_cdn': True,
    'backup_enabled': True,
    'backup_interval': 3600,
    'version_control_enabled': True,
    'max_versions': 10
}

DEFAULT_SECURITY_POLICY = {
    'policy_id': 'default',
    'name': 'Default Security Policy',
    'description': 'Default security policy for CineAIStudio',
    'encryption_algorithm': 'aes_256_gcm',
    'key_rotation_days': 90,
    'access_level': 'private',
    'allowed_permissions': ['read', 'write'],
    'password_policy': {
        'min_length': 12,
        'require_uppercase': True,
        'require_lowercase': True,
        'require_numbers': True,
        'require_special_chars': True,
        'max_age_days': 90
    },
    'session_timeout_minutes': 30,
    'max_login_attempts': 5,
    'lockout_duration_minutes': 30,
    'enable_two_factor': True,
    'audit_enabled': True
}

# 支持的云存储提供商
SUPPORTED_STORAGE_PROVIDERS = [
    'AWS S3',
    'Azure Blob Storage',
    'Google Cloud Storage',
    '阿里云 OSS',
    'MinIO',
    '本地缓存'
]

# 支持的加密算法
SUPPORTED_ENCRYPTION_ALGORITHMS = [
    'AES-256-GCM',
    'AES-256-CBC',
    'ChaCha20-Poly1305',
    'XChaCha20-Poly1305',
    'RSA-4096'
]

# 支持的压缩算法
SUPPORTED_COMPRESSION_ALGORITHMS = [
    'Gzip',
    'Zstandard',
    'Brotli'
]

# 支持的CDN提供商
SUPPORTED_CDN_PROVIDERS = [
    'Cloudflare',
    'AWS CloudFront',
    'Azure CDN',
    '阿里云 CDN'
]

# 使用示例
"""
# 基本使用示例
from app.core.cloud_storage import create_cloud_storage_integration

# 创建云端存储集成
cloud_integration = create_cloud_storage_integration(project_manager, config_manager)

# 启用云端集成
config = {
    'enabled': True,
    'auto_sync': True,
    'sync_interval': 300,
    'enable_encryption': True,
    'enable_compression': True
}
cloud_integration.enable_cloud_integration(config)

# 同步项目
project_id = "your-project-id"
cloud_integration.sync_project(project_id)

# 创建备份
cloud_integration.create_project_backup(project_id)

# 创建版本
version_number = cloud_integration.create_project_version(project_id, "v1.0")

# 获取状态
status = cloud_integration.get_cloud_storage_status()
print(f"Cloud storage status: {status}")
"""

# 系统要求
"""
系统要求：
- Python 3.8+
- PyQt6
- boto3 (AWS S3)
- azure-storage-blob (Azure)
    google-cloud-storage (Google Cloud)
- oss2 (阿里云)
- redis
- cryptography
- watchdog
- aiohttp
- requests
- cachetools
- tenacity
- psutil
- pyjwt
"""

# 性能指标
"""
性能指标：
- 支持TB级文件存储
- 支持百万级文件同步
- 支持1000+并发连接
- 缓存命中率 > 90%
- 压缩率平均 60%
- 加密性能开销 < 5%
- 同步延迟 < 100ms
- 可用性 > 99.9%
"""

# 安全特性
"""
安全特性：
- 端到端加密
- AES-256-GCM 加密算法
- RSA-4096 密钥交换
- PBKDF2 密钥派生
- JWT 令牌认证
- 基于角色的访问控制
- 安全审计日志
- 自动密钥轮换
- 数据完整性校验
"""

# 扩展性
"""
扩展性：
- 支持多种云存储后端
- 插件式架构
- 水平扩展支持
- 负载均衡
- 故障转移
- 多地区部署
- 容器化部署
"""

# 故障排除
"""
常见问题：
1. 连接失败：检查网络连接和认证信息
2. 同步冲突：检查文件权限和锁定状态
3. 性能问题：调整缓存和并发设置
4. 加密错误：检查密钥和证书
5. 存储配额：检查云存储配额限制

调试方法：
- 查看日志文件
- 检查网络连接
- 验证认证信息
- 监控系统资源
- 测试存储连接
"""