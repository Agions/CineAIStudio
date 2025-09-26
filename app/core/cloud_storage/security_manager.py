#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio 安全管理器
提供文件加密、权限控制、安全审计等安全功能
"""

import base64
import hashlib
import json
import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple, Set
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import sqlite3
import jwt
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from .cloud_storage_manager import FileMetadata, SyncStatus


class EncryptionAlgorithm(Enum):
    """加密算法"""
    AES_256_GCM = "aes_256_gcm"
    AES_256_CBC = "aes_256_cbc"
    CHACHA20_POLY1305 = "chacha20_poly1305"
    RSA_4096 = "rsa_4096"
    XCHACHA20_POLY1305 = "xchacha20_poly1305"


class AccessLevel(Enum):
    """访问级别"""
    PRIVATE = "private"          # 私有，仅所有者可访问
    SHARED = "shared"            # 共享，特定用户可访问
    TEAM = "team"                # 团队，团队成员可访问
    PUBLIC_READ = "public_read"  # 公开只读
    PUBLIC_WRITE = "public_write"  # 公开读写


class Permission(Enum):
    """权限类型"""
    READ = "read"                # 读取权限
    WRITE = "write"              # 写入权限
    DELETE = "delete"            # 删除权限
    SHARE = "share"              # 分享权限
    ADMIN = "admin"              # 管理权限


class SecurityEventType(Enum):
    """安全事件类型"""
    LOGIN = "login"
    LOGOUT = "logout"
    FILE_ACCESS = "file_access"
    FILE_UPLOAD = "file_upload"
    FILE_DOWNLOAD = "file_download"
    FILE_DELETE = "file_delete"
    PERMISSION_CHANGE = "permission_change"
    ENCRYPTION_CHANGE = "encryption_change"
    SECURITY_BREACH = "security_breach"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


@dataclass
class SecurityPolicy:
    """安全策略"""
    policy_id: str
    name: str
    description: str
    encryption_algorithm: EncryptionAlgorithm
    key_rotation_days: int = 90
    access_level: AccessLevel = AccessLevel.PRIVATE
    allowed_permissions: List[Permission] = field(default_factory=lambda: [Permission.READ, Permission.WRITE])
    password_policy: Dict[str, Any] = field(default_factory=lambda: {
        'min_length': 12,
        'require_uppercase': True,
        'require_lowercase': True,
        'require_numbers': True,
        'require_special_chars': True,
        'max_age_days': 90
    })
    session_timeout_minutes: int = 30
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    enable_two_factor: bool = True
    audit_enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class SecurityKey:
    """安全密钥"""
    key_id: str
    key_type: str
    key_data: bytes
    algorithm: EncryptionAlgorithm
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    is_active: bool = True
    key_version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityEvent:
    """安全事件"""
    event_id: str
    event_type: SecurityEventType
    user_id: str
    resource_id: str
    description: str
    timestamp: datetime = field(default_factory=datetime.now)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    severity: str = "info"
    status: str = "success"
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccessControl:
    """访问控制"""
    acl_id: str
    resource_id: str
    resource_type: str
    user_id: str
    permissions: List[Permission]
    granted_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    granted_by: str
    is_active: bool = True


class SecurityDatabase:
    """安全数据库"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_database()

    def _init_database(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            # 安全策略表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS security_policies (
                    policy_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    encryption_algorithm TEXT NOT NULL,
                    key_rotation_days INTEGER DEFAULT 90,
                    access_level TEXT DEFAULT 'private',
                    allowed_permissions TEXT DEFAULT '["read", "write"]',
                    password_policy TEXT DEFAULT '{}',
                    session_timeout_minutes INTEGER DEFAULT 30,
                    max_login_attempts INTEGER DEFAULT 5,
                    lockout_duration_minutes INTEGER DEFAULT 30,
                    enable_two_factor BOOLEAN DEFAULT 1,
                    audit_enabled BOOLEAN DEFAULT 1,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            ''')

            # 加密密钥表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS encryption_keys (
                    key_id TEXT PRIMARY KEY,
                    key_type TEXT NOT NULL,
                    key_data BLOB NOT NULL,
                    algorithm TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL,
                    is_active BOOLEAN DEFAULT 1,
                    key_version INTEGER DEFAULT 1,
                    metadata TEXT DEFAULT '{}'
                )
            ''')

            # 访问控制表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS access_controls (
                    acl_id TEXT PRIMARY KEY,
                    resource_id TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    permissions TEXT NOT NULL,
                    granted_at REAL NOT NULL,
                    expires_at REAL,
                    granted_by TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')

            # 安全事件表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS security_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    description TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    severity TEXT DEFAULT 'info',
                    status TEXT DEFAULT 'success',
                    details TEXT DEFAULT '{}'
                )
            ''')

            # 用户会话表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    token TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')

            # 失败登录尝试表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS failed_logins (
                    attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    ip_address TEXT,
                    attempt_time REAL NOT NULL,
                    reason TEXT
                )
            ''')

            # 创建索引
            conn.execute('CREATE INDEX IF NOT EXISTS idx_access_controls_resource ON access_controls (resource_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_access_controls_user ON access_controls (user_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_security_events_timestamp ON security_events (timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions (user_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_failed_logins_user ON failed_logins (user_id)')

            conn.commit()

    def add_security_policy(self, policy: SecurityPolicy) -> bool:
        """添加安全策略"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO security_policies
                    (policy_id, name, description, encryption_algorithm, key_rotation_days,
                     access_level, allowed_permissions, password_policy, session_timeout_minutes,
                     max_login_attempts, lockout_duration_minutes, enable_two_factor,
                     audit_enabled, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    policy.policy_id,
                    policy.name,
                    policy.description,
                    policy.encryption_algorithm.value,
                    policy.key_rotation_days,
                    policy.access_level.value,
                    json.dumps([p.value for p in policy.allowed_permissions]),
                    json.dumps(policy.password_policy),
                    policy.session_timeout_minutes,
                    policy.max_login_attempts,
                    policy.lockout_duration_minutes,
                    policy.enable_two_factor,
                    policy.audit_enabled,
                    policy.created_at.timestamp(),
                    policy.updated_at.timestamp()
                ))
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to add security policy: {e}")
            return False

    def get_security_policy(self, policy_id: str) -> Optional[SecurityPolicy]:
        """获取安全策略"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM security_policies WHERE policy_id = ?
                ''', (policy_id,))
                row = cursor.fetchone()

                if row:
                    return SecurityPolicy(
                        policy_id=row['policy_id'],
                        name=row['name'],
                        description=row['description'],
                        encryption_algorithm=EncryptionAlgorithm(row['encryption_algorithm']),
                        key_rotation_days=row['key_rotation_days'],
                        access_level=AccessLevel(row['access_level']),
                        allowed_permissions=[Permission(p) for p in json.loads(row['allowed_permissions'])],
                        password_policy=json.loads(row['password_policy']),
                        session_timeout_minutes=row['session_timeout_minutes'],
                        max_login_attempts=row['max_login_attempts'],
                        lockout_duration_minutes=row['lockout_duration_minutes'],
                        enable_two_factor=bool(row['enable_two_factor']),
                        audit_enabled=bool(row['audit_enabled']),
                        created_at=datetime.fromtimestamp(row['created_at']),
                        updated_at=datetime.fromtimestamp(row['updated_at'])
                    )
                return None
        except Exception as e:
            self.logger.error(f"Failed to get security policy: {e}")
            return None

    def add_encryption_key(self, key: SecurityKey) -> bool:
        """添加加密密钥"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO encryption_keys
                    (key_id, key_type, key_data, algorithm, created_at, expires_at,
                     is_active, key_version, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    key.key_id,
                    key.key_type,
                    key.key_data,
                    key.algorithm.value,
                    key.created_at.timestamp(),
                    key.expires_at.timestamp() if key.expires_at else None,
                    key.is_active,
                    key.key_version,
                    json.dumps(key.metadata)
                ))
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to add encryption key: {e}")
            return False

    def get_active_encryption_key(self, key_type: str) -> Optional[SecurityKey]:
        """获取活动加密密钥"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM encryption_keys
                    WHERE key_type = ? AND is_active = 1
                    ORDER BY key_version DESC
                    LIMIT 1
                ''', (key_type,))
                row = cursor.fetchone()

                if row:
                    return SecurityKey(
                        key_id=row['key_id'],
                        key_type=row['key_type'],
                        key_data=row['key_data'],
                        algorithm=EncryptionAlgorithm(row['algorithm']),
                        created_at=datetime.fromtimestamp(row['created_at']),
                        expires_at=datetime.fromtimestamp(row['expires_at']) if row['expires_at'] else None,
                        is_active=bool(row['is_active']),
                        key_version=row['key_version'],
                        metadata=json.loads(row['metadata'])
                    )
                return None
        except Exception as e:
            self.logger.error(f"Failed to get active encryption key: {e}")
            return None

    def add_access_control(self, acl: AccessControl) -> bool:
        """添加访问控制"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO access_controls
                    (acl_id, resource_id, resource_type, user_id, permissions,
                     granted_at, expires_at, granted_by, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    acl.acl_id,
                    acl.resource_id,
                    acl.resource_type,
                    acl.user_id,
                    json.dumps([p.value for p in acl.permissions]),
                    acl.granted_at.timestamp(),
                    acl.expires_at.timestamp() if acl.expires_at else None,
                    acl.granted_by,
                    acl.is_active
                ))
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to add access control: {e}")
            return False

    def check_permission(self, resource_id: str, user_id: str, permission: Permission) -> bool:
        """检查权限"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT permissions FROM access_controls
                    WHERE resource_id = ? AND user_id = ? AND is_active = 1
                    AND (expires_at IS NULL OR expires_at > ?)
                ''', (resource_id, user_id, datetime.now().timestamp()))
                row = cursor.fetchone()

                if row:
                    permissions = [Permission(p) for p in json.loads(row['permissions'])]
                    return permission in permissions

                return False
        except Exception as e:
            self.logger.error(f"Failed to check permission: {e}")
            return False

    def log_security_event(self, event: SecurityEvent) -> bool:
        """记录安全事件"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO security_events
                    (event_id, event_type, user_id, resource_id, description, timestamp,
                     ip_address, user_agent, severity, status, details)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event.event_id,
                    event.event_type.value,
                    event.user_id,
                    event.resource_id,
                    event.description,
                    event.timestamp.timestamp(),
                    event.ip_address,
                    event.user_agent,
                    event.severity,
                    event.status,
                    json.dumps(event.details)
                ))
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to log security event: {e}")
            return False

    def get_security_events(self, start_time: Optional[datetime] = None,
                           end_time: Optional[datetime] = None,
                           event_type: Optional[SecurityEventType] = None,
                           limit: int = 100) -> List[SecurityEvent]:
        """获取安全事件"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                query = '''
                    SELECT * FROM security_events
                    WHERE 1=1
                '''
                params = []

                if start_time:
                    query += ' AND timestamp >= ?'
                    params.append(start_time.timestamp())

                if end_time:
                    query += ' AND timestamp <= ?'
                    params.append(end_time.timestamp())

                if event_type:
                    query += ' AND event_type = ?'
                    params.append(event_type.value)

                query += ' ORDER BY timestamp DESC LIMIT ?'
                params.append(limit)

                cursor = conn.execute(query, params)
                rows = cursor.fetchall()

                events = []
                for row in rows:
                    events.append(SecurityEvent(
                        event_id=row['event_id'],
                        event_type=SecurityEventType(row['event_type']),
                        user_id=row['user_id'],
                        resource_id=row['resource_id'],
                        description=row['description'],
                        timestamp=datetime.fromtimestamp(row['timestamp']),
                        ip_address=row['ip_address'],
                        user_agent=row['user_agent'],
                        severity=row['severity'],
                        status=row['status'],
                        details=json.loads(row['details'])
                    ))

                return events
        except Exception as e:
            self.logger.error(f"Failed to get security events: {e}")
            return []


class EncryptionManager:
    """加密管理器"""

    def __init__(self, security_db: SecurityDatabase):
        self.security_db = security_db
        self.logger = logging.getLogger(__name__)
        self.key_cache: Dict[str, SecurityKey] = {}

    def generate_key_pair(self, algorithm: EncryptionAlgorithm = EncryptionAlgorithm.RSA_4096) -> Tuple[bytes, bytes]:
        """生成密钥对"""
        try:
            if algorithm == EncryptionAlgorithm.RSA_4096:
                private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=4096,
                    backend=default_backend()
                )
                public_key = private_key.public_key()

                private_pem = private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )

                public_pem = public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )

                return private_pem, public_pem

            elif algorithm in [EncryptionAlgorithm.AES_256_GCM, EncryptionAlgorithm.AES_256_CBC]:
                # 生成AES密钥
                key = os.urandom(32)  # 256位
                return key, key

            else:
                raise ValueError(f"Unsupported algorithm: {algorithm}")

        except Exception as e:
            self.logger.error(f"Failed to generate key pair: {e}")
            raise

    def generate_encryption_key(self, algorithm: EncryptionAlgorithm) -> SecurityKey:
        """生成加密密钥"""
        try:
            key_id = str(hash(str(time.time()) + str(os.urandom(16))))
            key_type = algorithm.value
            key_data, _ = self.generate_key_pair(algorithm)

            key = SecurityKey(
                key_id=key_id,
                key_type=key_type,
                key_data=key_data,
                algorithm=algorithm,
                expires_at=datetime.now() + timedelta(days=90),  # 90天过期
                metadata={'purpose': 'file_encryption'}
            )

            # 保存到数据库
            self.security_db.add_encryption_key(key)

            # 缓存密钥
            self.key_cache[key_id] = key

            return key

        except Exception as e:
            self.logger.error(f"Failed to generate encryption key: {e}")
            raise

    def encrypt_data(self, data: bytes, key_id: str, algorithm: Optional[EncryptionAlgorithm] = None) -> bytes:
        """加密数据"""
        try:
            # 获取密钥
            if key_id not in self.key_cache:
                key = self.security_db.get_active_encryption_key(key_id)
                if not key:
                    raise ValueError(f"Key not found: {key_id}")
                self.key_cache[key_id] = key
            else:
                key = self.key_cache[key_id]

            algorithm = algorithm or key.algorithm

            if algorithm == EncryptionAlgorithm.AES_256_GCM:
                return self._encrypt_aes_gcm(data, key.key_data)
            elif algorithm == EncryptionAlgorithm.AES_256_CBC:
                return self._encrypt_aes_cbc(data, key.key_data)
            elif algorithm == EncryptionAlgorithm.RSA_4096:
                return self._encrypt_rsa(data, key.key_data)
            else:
                raise ValueError(f"Unsupported encryption algorithm: {algorithm}")

        except Exception as e:
            self.logger.error(f"Failed to encrypt data: {e}")
            raise

    def decrypt_data(self, encrypted_data: bytes, key_id: str, algorithm: Optional[EncryptionAlgorithm] = None) -> bytes:
        """解密数据"""
        try:
            # 获取密钥
            if key_id not in self.key_cache:
                key = self.security_db.get_active_encryption_key(key_id)
                if not key:
                    raise ValueError(f"Key not found: {key_id}")
                self.key_cache[key_id] = key
            else:
                key = self.key_cache[key_id]

            algorithm = algorithm or key.algorithm

            if algorithm == EncryptionAlgorithm.AES_256_GCM:
                return self._decrypt_aes_gcm(encrypted_data, key.key_data)
            elif algorithm == EncryptionAlgorithm.AES_256_CBC:
                return self._decrypt_aes_cbc(encrypted_data, key.key_data)
            elif algorithm == EncryptionAlgorithm.RSA_4096:
                return self._decrypt_rsa(encrypted_data, key.key_data)
            else:
                raise ValueError(f"Unsupported decryption algorithm: {algorithm}")

        except Exception as e:
            self.logger.error(f"Failed to decrypt data: {e}")
            raise

    def _encrypt_aes_gcm(self, data: bytes, key: bytes) -> bytes:
        """AES-GCM加密"""
        try:
            iv = os.urandom(12)  # GCM推荐使用12字节IV
            cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
            encryptor = cipher.encryptor()

            ciphertext = encryptor.update(data) + encryptor.finalize()

            # 返回 IV + tag + ciphertext
            return iv + encryptor.tag + ciphertext

        except Exception as e:
            self.logger.error(f"AES-GCM encryption failed: {e}")
            raise

    def _decrypt_aes_gcm(self, encrypted_data: bytes, key: bytes) -> bytes:
        """AES-GCM解密"""
        try:
            iv = encrypted_data[:12]
            tag = encrypted_data[12:28]
            ciphertext = encrypted_data[28:]

            cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
            decryptor = cipher.decryptor()

            return decryptor.update(ciphertext) + decryptor.finalize()

        except Exception as e:
            self.logger.error(f"AES-GCM decryption failed: {e}")
            raise

    def _encrypt_aes_cbc(self, data: bytes, key: bytes) -> bytes:
        """AES-CBC加密"""
        try:
            iv = os.urandom(16)  # CBC使用16字节IV
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            encryptor = cipher.encryptor()

            # PKCS7填充
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(data) + padder.finalize()

            ciphertext = encryptor.update(padded_data) + encryptor.finalize()

            # 返回 IV + ciphertext
            return iv + ciphertext

        except Exception as e:
            self.logger.error(f"AES-CBC encryption failed: {e}")
            raise

    def _decrypt_aes_cbc(self, encrypted_data: bytes, key: bytes) -> bytes:
        """AES-CBC解密"""
        try:
            iv = encrypted_data[:16]
            ciphertext = encrypted_data[16:]

            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()

            padded_data = decryptor.update(ciphertext) + decryptor.finalize()

            # PKCS7去填充
            unpadder = padding.PKCS7(128).unpadder()
            data = unpadder.update(padded_data) + unpadder.finalize()

            return data

        except Exception as e:
            self.logger.error(f"AES-CBC decryption failed: {e}")
            raise

    def _encrypt_rsa(self, data: bytes, key: bytes) -> bytes:
        """RSA加密"""
        try:
            private_key = serialization.load_pem_private_key(key, password=None, backend=default_backend())
            public_key = private_key.public_key()

            # RSA只能加密少量数据，这里使用对称加密密钥
            if len(data) > 256:  # RSA-4096可以加密最多501字节
                # 生成临时AES密钥
                aes_key = os.urandom(32)
                # 用RSA加密AES密钥
                encrypted_key = public_key.encrypt(
                    aes_key,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                # 用AES加密数据
                encrypted_data = self._encrypt_aes_gcm(data, aes_key)
                # 返回加密的密钥 + 加密的数据
                return encrypted_key + encrypted_data
            else:
                return public_key.encrypt(
                    data,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )

        except Exception as e:
            self.logger.error(f"RSA encryption failed: {e}")
            raise

    def _decrypt_rsa(self, encrypted_data: bytes, key: bytes) -> bytes:
        """RSA解密"""
        try:
            private_key = serialization.load_pem_private_key(key, password=None, backend=default_backend())

            # 检查是否是混合加密
            if len(encrypted_data) > 512:  # RSA-4096加密的密钥是512字节
                encrypted_key = encrypted_data[:512]
                encrypted_data = encrypted_data[512:]

                # 解密AES密钥
                aes_key = private_key.decrypt(
                    encrypted_key,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )

                # 用AES解密数据
                return self._decrypt_aes_gcm(encrypted_data, aes_key)
            else:
                return private_key.decrypt(
                    encrypted_data,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )

        except Exception as e:
            self.logger.error(f"RSA decryption failed: {e}")
            raise

    def rotate_keys(self):
        """密钥轮换"""
        try:
            # 获取所有活动的密钥
            with sqlite3.connect(self.security_db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM encryption_keys WHERE is_active = 1
                ''')
                rows = cursor.fetchall()

                for row in rows:
                    key = SecurityKey(
                        key_id=row['key_id'],
                        key_type=row['key_type'],
                        key_data=row['key_data'],
                        algorithm=EncryptionAlgorithm(row['algorithm']),
                        created_at=datetime.fromtimestamp(row['created_at']),
                        expires_at=datetime.fromtimestamp(row['expires_at']) if row['expires_at'] else None,
                        is_active=bool(row['is_active']),
                        key_version=row['key_version'],
                        metadata=json.loads(row['metadata'])
                    )

                    # 检查是否需要轮换
                    if key.expires_at and datetime.now() >= key.expires_at - timedelta(days=7):
                        # 生成新密钥
                        new_key = self.generate_encryption_key(key.algorithm)
                        # 使旧密钥失效
                        key.is_active = False
                        self.security_db.add_encryption_key(key)

                        self.logger.info(f"Rotated key {key.key_id} to {new_key.key_id}")

        except Exception as e:
            self.logger.error(f"Key rotation failed: {e}")

    def cleanup_expired_keys(self):
        """清理过期密钥"""
        try:
            with sqlite3.connect(self.security_db.db_path) as conn:
                conn.execute('''
                    DELETE FROM encryption_keys
                    WHERE expires_at IS NOT NULL AND expires_at < ?
                ''', (datetime.now().timestamp(),))
                conn.commit()

        except Exception as e:
            self.logger.error(f"Failed to cleanup expired keys: {e}")


class SecurityManager(QObject):
    """安全管理器"""

    # 信号定义
    security_event = pyqtSignal(str, str)          # 安全事件信号
    permission_denied = pyqtSignal(str, str)      # 权限拒绝信号
    encryption_key_rotated = pyqtSignal(str)      # 加密密钥轮换信号
    security_breach_detected = pyqtSignal(str)    # 安全漏洞检测信号
    policy_updated = pyqtSignal(str)             # 策略更新信号

    def __init__(self):
        super().__init__()

        self.logger = logging.getLogger(__name__)

        # 初始化数据库
        self.security_db = SecurityDatabase(os.path.expanduser("~/.cineaistudio/security.db"))

        # 初始化组件
        self.encryption_manager = EncryptionManager(self.security_db)

        # 当前用户和会话
        self.current_user_id: Optional[str] = None
        self.current_session_id: Optional[str] = None
        self.user_permissions: Dict[str, List[Permission]] = {}

        # 安全配置
        self.security_policy: Optional[SecurityPolicy] = None
        self.encryption_enabled = True
        self.audit_enabled = True
        self.auto_key_rotation = True

        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=4)

        # 初始化默认策略
        self._init_default_policy()

        # 启动后台任务
        self._start_background_tasks()

    def _init_default_policy(self):
        """初始化默认安全策略"""
        try:
            default_policy = SecurityPolicy(
                policy_id="default",
                name="Default Security Policy",
                description="Default security policy for CineAIStudio",
                encryption_algorithm=EncryptionAlgorithm.AES_256_GCM,
                key_rotation_days=90,
                access_level=AccessLevel.PRIVATE,
                allowed_permissions=[Permission.READ, Permission.WRITE],
                password_policy={
                    'min_length': 12,
                    'require_uppercase': True,
                    'require_lowercase': True,
                    'require_numbers': True,
                    'require_special_chars': True,
                    'max_age_days': 90
                },
                session_timeout_minutes=30,
                max_login_attempts=5,
                lockout_duration_minutes=30,
                enable_two_factor=True,
                audit_enabled=True
            )

            self.security_db.add_security_policy(default_policy)
            self.security_policy = default_policy

        except Exception as e:
            self.logger.error(f"Failed to initialize default security policy: {e}")

    def _start_background_tasks(self):
        """启动后台任务"""
        # 启动密钥轮换检查
        self.key_rotation_timer = QTimer()
        self.key_rotation_timer.timeout.connect(self._check_key_rotation)
        self.key_rotation_timer.start(86400000)  # 24小时

        # 启动安全审计
        if self.audit_enabled:
            self.audit_timer = QTimer()
            self.audit_timer.timeout.connect(self._perform_security_audit)
            self.audit_timer.start(3600000)  # 1小时

    def _check_key_rotation(self):
        """检查密钥轮换"""
        try:
            if self.auto_key_rotation:
                self.encryption_manager.rotate_keys()
        except Exception as e:
            self.logger.error(f"Key rotation check failed: {e}")

    def _perform_security_audit(self):
        """执行安全审计"""
        try:
            # 检查异常登录尝试
            self._check_suspicious_logins()

            # 检查权限异常
            self._check_permission_anomalies()

            # 检查加密密钥状态
            self._check_encryption_keys()

            # 生成审计报告
            self._generate_audit_report()

        except Exception as e:
            self.logger.error(f"Security audit failed: {e}")

    def _check_suspicious_logins(self):
        """检查可疑登录"""
        try:
            with sqlite3.connect(self.security_db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT user_id, COUNT(*) as attempt_count,
                           MAX(attempt_time) as last_attempt
                    FROM failed_logins
                    WHERE attempt_time > ?
                    GROUP BY user_id
                    HAVING attempt_count > 5
                ''', ((datetime.now() - timedelta(hours=1)).timestamp(),))

                for row in cursor.fetchall():
                    # 记录可疑活动
                    event = SecurityEvent(
                        event_id=str(hash(str(time.time()) + row['user_id'])),
                        event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                        user_id=row['user_id'],
                        resource_id="system",
                        description=f"Suspicious login activity detected: {row['attempt_count']} failed attempts",
                        severity="warning",
                        details={
                            'failed_attempts': row['attempt_count'],
                            'last_attempt': row['last_attempt']
                        }
                    )

                    self.security_db.log_security_event(event)
                    self.security_breach_detected.emit(event.event_id)

        except Exception as e:
            self.logger.error(f"Failed to check suspicious logins: {e}")

    def _check_permission_anomalies(self):
        """检查权限异常"""
        try:
            # 检查权限提升
            with sqlite3.connect(self.security_db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT user_id, resource_id, permissions, granted_at
                    FROM access_controls
                    WHERE granted_at > ?
                    AND permissions LIKE '%admin%'
                ''', ((datetime.now() - timedelta(days=1)).timestamp(),))

                for row in cursor.fetchall():
                    # 记录权限变更
                    event = SecurityEvent(
                        event_id=str(hash(str(time.time()) + row['user_id'] + row['resource_id'])),
                        event_type=SecurityEventType.PERMISSION_CHANGE,
                        user_id=row['user_id'],
                        resource_id=row['resource_id'],
                        description=f"Admin permission granted to {row['user_id']} for {row['resource_id']}",
                        severity="info",
                        details={
                            'permissions': json.loads(row['permissions']),
                            'granted_at': row['granted_at']
                        }
                    )

                    self.security_db.log_security_event(event)

        except Exception as e:
            self.logger.error(f"Failed to check permission anomalies: {e}")

    def _check_encryption_keys(self):
        """检查加密密钥状态"""
        try:
            # 检查即将过期的密钥
            with sqlite3.connect(self.security_db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT key_id, key_type, expires_at
                    FROM encryption_keys
                    WHERE is_active = 1 AND expires_at IS NOT NULL
                    AND expires_at < ?
                ''', ((datetime.now() + timedelta(days=7)).timestamp(),))

                for row in cursor.fetchall():
                    self.logger.warning(f"Encryption key {row['key_id']} will expire soon")

        except Exception as e:
            self.logger.error(f"Failed to check encryption keys: {e}")

    def _generate_audit_report(self):
        """生成审计报告"""
        try:
            # 获取最近的安全事件
            recent_events = self.security_db.get_security_events(
                start_time=datetime.now() - timedelta(days=1),
                limit=1000
            )

            # 分析安全事件
            event_summary = {}
            for event in recent_events:
                event_type = event.event_type.value
                if event_type not in event_summary:
                    event_summary[event_type] = {
                        'count': 0,
                        'success_count': 0,
                        'failure_count': 0
                    }
                event_summary[event_type]['count'] += 1
                if event.status == 'success':
                    event_summary[event_type]['success_count'] += 1
                else:
                    event_summary[event_type]['failure_count'] += 1

            # 保存审计报告
            report_path = os.path.expanduser("~/.cineaistudio/audit_reports")
            os.makedirs(report_path, exist_ok=True)

            report_file = os.path.join(report_path, f"audit_{datetime.now().strftime('%Y%m%d')}.json")
            with open(report_file, 'w') as f:
                json.dump({
                    'generated_at': datetime.now().isoformat(),
                    'period': '24h',
                    'total_events': len(recent_events),
                    'event_summary': event_summary,
                    'events': [event.__dict__ for event in recent_events[:100]]  # 只保存最近100个事件
                }, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to generate audit report: {e}")

    def login(self, user_id: str, password: str, ip_address: Optional[str] = None,
              user_agent: Optional[str] = None) -> bool:
        """用户登录"""
        try:
            # 验证密码
            if not self._verify_password(user_id, password):
                # 记录失败登录
                with sqlite3.connect(self.security_db.db_path) as conn:
                    conn.execute('''
                        INSERT INTO failed_logins (user_id, ip_address, attempt_time, reason)
                        VALUES (?, ?, ?, ?)
                    ''', (user_id, ip_address, datetime.now().timestamp(), "invalid_password"))
                    conn.commit()

                # 检查是否需要锁定账户
                if self._is_account_locked(user_id):
                    event = SecurityEvent(
                        event_id=str(hash(str(time.time()) + user_id)),
                        event_type=SecurityEventType.LOGIN,
                        user_id=user_id,
                        resource_id="system",
                        description="Account locked due to too many failed attempts",
                        severity="error",
                        status="failure"
                    )
                    self.security_db.log_security_event(event)
                    return False

                return False

            # 创建会话
            session_id = self._create_session(user_id, ip_address, user_agent)

            if session_id:
                self.current_user_id = user_id
                self.current_session_id = session_id

                # 记录成功登录
                event = SecurityEvent(
                    event_id=str(hash(str(time.time()) + user_id)),
                    event_type=SecurityEventType.LOGIN,
                    user_id=user_id,
                    resource_id="system",
                    description="User logged in successfully",
                    ip_address=ip_address,
                    user_agent=user_agent,
                    severity="info",
                    status="success"
                )
                self.security_db.log_security_event(event)
                self.security_event.emit(event.event_id, event.description)

                return True

            return False

        except Exception as e:
            self.logger.error(f"Login failed for user {user_id}: {e}")
            return False

    def logout(self):
        """用户登出"""
        try:
            if self.current_user_id and self.current_session_id:
                # 记录登出事件
                event = SecurityEvent(
                    event_id=str(hash(str(time.time()) + self.current_user_id)),
                    event_type=SecurityEventType.LOGOUT,
                    user_id=self.current_user_id,
                    resource_id="system",
                    description="User logged out",
                    severity="info",
                    status="success"
                )
                self.security_db.log_security_event(event)
                self.security_event.emit(event.event_id, event.description)

                # 删除会话
                with sqlite3.connect(self.security_db.db_path) as conn:
                    conn.execute('''
                        DELETE FROM user_sessions WHERE session_id = ?
                    ''', (self.current_session_id,))
                    conn.commit()

                self.current_user_id = None
                self.current_session_id = None

        except Exception as e:
            self.logger.error(f"Logout failed: {e}")

    def _verify_password(self, user_id: str, password: str) -> bool:
        """验证密码"""
        # 这里实现实际的密码验证逻辑
        # 简化实现，返回True
        return True

    def _create_session(self, user_id: str, ip_address: Optional[str],
                       user_agent: Optional[str]) -> Optional[str]:
        """创建用户会话"""
        try:
            session_id = str(hash(str(time.time()) + user_id))
            token = self._generate_jwt_token(user_id)

            expires_at = datetime.now() + timedelta(minutes=self.security_policy.session_timeout_minutes)

            with sqlite3.connect(self.security_db.db_path) as conn:
                conn.execute('''
                    INSERT INTO user_sessions (session_id, user_id, token, created_at, expires_at, ip_address, user_agent)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session_id,
                    user_id,
                    token,
                    datetime.now().timestamp(),
                    expires_at.timestamp(),
                    ip_address,
                    user_agent
                ))
                conn.commit()

            return session_id

        except Exception as e:
            self.logger.error(f"Failed to create session: {e}")
            return None

    def _generate_jwt_token(self, user_id: str) -> str:
        """生成JWT令牌"""
        try:
            payload = {
                'user_id': user_id,
                'exp': datetime.now() + timedelta(hours=24),
                'iat': datetime.now()
            }
            # 这里需要一个密钥来签名JWT
            secret_key = "your-secret-key"  # 应该从安全配置中获取
            return jwt.encode(payload, secret_key, algorithm='HS256')
        except Exception as e:
            self.logger.error(f"Failed to generate JWT token: {e}")
            return ""

    def _is_account_locked(self, user_id: str) -> bool:
        """检查账户是否被锁定"""
        try:
            with sqlite3.connect(self.security_db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT COUNT(*) as failed_count
                    FROM failed_logins
                    WHERE user_id = ? AND attempt_time > ?
                ''', (user_id, (datetime.now() - timedelta(minutes=self.security_policy.lockout_duration_minutes)).timestamp()))

                row = cursor.fetchone()
                return row['failed_count'] >= self.security_policy.max_login_attempts

        except Exception as e:
            self.logger.error(f"Failed to check account lock status: {e}")
            return False

    def check_permission(self, resource_id: str, permission: Permission) -> bool:
        """检查用户权限"""
        try:
            if not self.current_user_id:
                return False

            return self.security_db.check_permission(resource_id, self.current_user_id, permission)

        except Exception as e:
            self.logger.error(f"Failed to check permission: {e}")
            return False

    def grant_permission(self, resource_id: str, user_id: str, permission: Permission) -> bool:
        """授予权限"""
        try:
            acl_id = str(hash(str(time.time()) + resource_id + user_id + permission.value))
            acl = AccessControl(
                acl_id=acl_id,
                resource_id=resource_id,
                resource_type="file",
                user_id=user_id,
                permissions=[permission],
                granted_by=self.current_user_id or "system"
            )

            success = self.security_db.add_access_control(acl)

            if success:
                # 记录权限变更事件
                event = SecurityEvent(
                    event_id=str(hash(str(time.time()) + acl_id)),
                    event_type=SecurityEventType.PERMISSION_CHANGE,
                    user_id=self.current_user_id or "system",
                    resource_id=resource_id,
                    description=f"Granted {permission.value} permission to {user_id}",
                    severity="info",
                    status="success"
                )
                self.security_db.log_security_event(event)
                self.security_event.emit(event.event_id, event.description)

            return success

        except Exception as e:
            self.logger.error(f"Failed to grant permission: {e}")
            return False

    def revoke_permission(self, resource_id: str, user_id: str, permission: Permission) -> bool:
        """撤销权限"""
        try:
            with sqlite3.connect(self.security_db.db_path) as conn:
                conn.execute('''
                    UPDATE access_controls
                    SET is_active = 0
                    WHERE resource_id = ? AND user_id = ? AND permissions LIKE ?
                ''', (resource_id, user_id, f'%{permission.value}%'))
                conn.commit()

            # 记录权限变更事件
            event = SecurityEvent(
                event_id=str(hash(str(time.time()) + resource_id + user_id)),
                event_type=SecurityEventType.PERMISSION_CHANGE,
                user_id=self.current_user_id or "system",
                resource_id=resource_id,
                description=f"Revoked {permission.value} permission from {user_id}",
                severity="info",
                status="success"
            )
            self.security_db.log_security_event(event)
            self.security_event.emit(event.event_id, event.description)

            return True

        except Exception as e:
            self.logger.error(f"Failed to revoke permission: {e}")
            return False

    def encrypt_file(self, file_path: str, output_path: str, key_id: Optional[str] = None) -> bool:
        """加密文件"""
        try:
            if not self.encryption_enabled:
                # 如果没有启用加密，直接复制文件
                shutil.copy2(file_path, output_path)
                return True

            # 生成或获取加密密钥
            if not key_id:
                key = self.encryption_manager.generate_encryption_key(
                    self.security_policy.encryption_algorithm
                )
                key_id = key.key_id
            else:
                key = self.security_db.get_active_encryption_key(key_id)
                if not key:
                    self.logger.error(f"Encryption key not found: {key_id}")
                    return False

            # 读取文件数据
            with open(file_path, 'rb') as f:
                data = f.read()

            # 加密数据
            encrypted_data = self.encryption_manager.encrypt_data(data, key_id)

            # 写入加密文件
            with open(output_path, 'wb') as f:
                f.write(encrypted_data)

            # 记录加密事件
            event = SecurityEvent(
                event_id=str(hash(str(time.time()) + file_path)),
                event_type=SecurityEventType.ENCRYPTION_CHANGE,
                user_id=self.current_user_id or "system",
                resource_id=file_path,
                description=f"File encrypted with key {key_id}",
                severity="info",
                status="success",
                details={
                    'file_size': len(data),
                    'encrypted_size': len(encrypted_data),
                    'key_id': key_id,
                    'algorithm': key.algorithm.value
                }
            )
            self.security_db.log_security_event(event)

            return True

        except Exception as e:
            self.logger.error(f"Failed to encrypt file {file_path}: {e}")
            return False

    def decrypt_file(self, encrypted_path: str, output_path: str, key_id: str) -> bool:
        """解密文件"""
        try:
            # 检查权限
            if not self.check_permission(encrypted_path, Permission.READ):
                self.permission_denied.emit(encrypted_path, "read permission denied")
                return False

            # 读取加密数据
            with open(encrypted_path, 'rb') as f:
                encrypted_data = f.read()

            # 解密数据
            decrypted_data = self.encryption_manager.decrypt_data(encrypted_data, key_id)

            # 写入解密文件
            with open(output_path, 'wb') as f:
                f.write(decrypted_data)

            # 记录解密事件
            event = SecurityEvent(
                event_id=str(hash(str(time.time()) + encrypted_path)),
                event_type=SecurityEventType.FILE_ACCESS,
                user_id=self.current_user_id or "system",
                resource_id=encrypted_path,
                description=f"File decrypted with key {key_id}",
                severity="info",
                status="success",
                details={
                    'encrypted_size': len(encrypted_data),
                    'decrypted_size': len(decrypted_data),
                    'key_id': key_id
                }
            )
            self.security_db.log_security_event(event)

            return True

        except Exception as e:
            self.logger.error(f"Failed to decrypt file {encrypted_path}: {e}")
            return False

    def log_security_event(self, event_type: SecurityEventType, resource_id: str,
                           description: str, severity: str = "info",
                           status: str = "success", details: Optional[Dict] = None):
        """记录安全事件"""
        try:
            event = SecurityEvent(
                event_id=str(hash(str(time.time()) + resource_id + event_type.value)),
                event_type=event_type,
                user_id=self.current_user_id or "system",
                resource_id=resource_id,
                description=description,
                severity=severity,
                status=status,
                details=details or {}
            )

            self.security_db.log_security_event(event)
            self.security_event.emit(event.event_id, description)

        except Exception as e:
            self.logger.error(f"Failed to log security event: {e}")

    def get_security_events(self, start_time: Optional[datetime] = None,
                           end_time: Optional[datetime] = None,
                           limit: int = 100) -> List[SecurityEvent]:
        """获取安全事件"""
        return self.security_db.get_security_events(start_time, end_time, limit=limit)

    def set_security_policy(self, policy: SecurityPolicy) -> bool:
        """设置安全策略"""
        try:
            success = self.security_db.add_security_policy(policy)
            if success:
                self.security_policy = policy
                self.policy_updated.emit(policy.policy_id)

                # 记录策略变更事件
                event = SecurityEvent(
                    event_id=str(hash(str(time.time()) + policy.policy_id)),
                    event_type=SecurityEventType.PERMISSION_CHANGE,
                    user_id=self.current_user_id or "system",
                    resource_id="system",
                    description=f"Security policy updated: {policy.name}",
                    severity="info",
                    status="success"
                )
                self.security_db.log_security_event(event)

            return success

        except Exception as e:
            self.logger.error(f"Failed to set security policy: {e}")
            return False

    def cleanup(self):
        """清理资源"""
        try:
            # 清理过期密钥
            self.encryption_manager.cleanup_expired_keys()

            # 关闭线程池
            self.executor.shutdown(wait=True)

            # 执行最后的审计
            self._perform_security_audit()

        except Exception as e:
            self.logger.error(f"Security cleanup failed: {e}")

    def get_current_user_permissions(self) -> List[Permission]:
        """获取当前用户权限"""
        if not self.current_user_id:
            return []

        try:
            with sqlite3.connect(self.security_db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT permissions FROM access_controls
                    WHERE user_id = ? AND is_active = 1
                    AND (expires_at IS NULL OR expires_at > ?)
                ''', (self.current_user_id, datetime.now().timestamp()))

                permissions = []
                for row in cursor.fetchall():
                    user_permissions = [Permission(p) for p in json.loads(row['permissions'])]
                    permissions.extend(user_permissions)

                return list(set(permissions))  # 去重

        except Exception as e:
            self.logger.error(f"Failed to get current user permissions: {e}")
            return []

    def is_user_logged_in(self) -> bool:
        """检查用户是否已登录"""
        if not self.current_user_id or not self.current_session_id:
            return False

        try:
            with sqlite3.connect(self.security_db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM user_sessions
                    WHERE session_id = ? AND is_active = 1 AND expires_at > ?
                ''', (self.current_session_id, datetime.now().timestamp()))

                return cursor.fetchone() is not None

        except Exception as e:
            self.logger.error(f"Failed to check login status: {e}")
            return False

    def force_key_rotation(self):
        """强制密钥轮换"""
        try:
            self.encryption_manager.rotate_keys()
            self.encryption_key_rotated.emit("manual_rotation")

        except Exception as e:
            self.logger.error(f"Force key rotation failed: {e}")

    def generate_security_report(self, report_type: str = "summary") -> Dict[str, Any]:
        """生成安全报告"""
        try:
            report = {
                'generated_at': datetime.now().isoformat(),
                'report_type': report_type,
                'encryption_enabled': self.encryption_enabled,
                'audit_enabled': self.audit_enabled,
                'auto_key_rotation': self.auto_key_rotation,
                'current_policy': self.security_policy.__dict__ if self.security_policy else None
            }

            if report_type == "detailed":
                # 获取详细的安全统计信息
                recent_events = self.security_db.get_security_events(
                    start_time=datetime.now() - timedelta(days=7),
                    limit=1000
                )

                event_stats = {}
                for event in recent_events:
                    event_type = event.event_type.value
                    if event_type not in event_stats:
                        event_stats[event_type] = {'total': 0, 'success': 0, 'failure': 0}
                    event_stats[event_type]['total'] += 1
                    if event.status == 'success':
                        event_stats[event_type]['success'] += 1
                    else:
                        event_stats[event_type]['failure'] += 1

                report.update({
                    'event_statistics': event_stats,
                    'total_events': len(recent_events),
                    'security_incidents': len([e for e in recent_events if e.severity in ['error', 'critical']])
                })

            return report

        except Exception as e:
            self.logger.error(f"Failed to generate security report: {e}")
            return {}