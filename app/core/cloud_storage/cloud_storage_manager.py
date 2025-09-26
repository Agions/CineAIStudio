#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio 云端存储管理器
提供专业的云端存储和同步解决方案，支持TB级媒体文件的高效存储和同步
"""

import asyncio
import hashlib
import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, PriorityQueue

import aiohttp
import boto3
import redis
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread
from cryptography.fernet import Fernet
from tenacity import retry, stop_after_attempt, wait_exponential


class SyncStatus(Enum):
    """同步状态枚举"""
    SYNCED = "synced"
    SYNCING = "syncing"
    PENDING = "pending"
    FAILED = "failed"
    CONFLICT = "conflict"
    OFFLINE = "offline"


class FileOperationType(Enum):
    """文件操作类型"""
    UPLOAD = "upload"
    DOWNLOAD = "download"
    DELETE = "delete"
    MOVE = "move"
    COPY = "copy"


class StorageBackend(Enum):
    """存储后端类型"""
    AWS_S3 = "aws_s3"
    AZURE_BLOB = "azure_blob"
    GOOGLE_CLOUD = "google_cloud"
    ALIYUN_OSS = "aliyun_oss"
    MINIO = "minio"
    LOCAL_CACHE = "local_cache"


@dataclass
class FileMetadata:
    """文件元数据"""
    file_id: str
    filename: str
    file_path: str
    file_size: int
    file_hash: str
    mime_type: str
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    version: int = 1
    sync_status: SyncStatus = SyncStatus.PENDING
    chunk_size: int = 64 * 1024 * 1024  # 64MB
    total_chunks: int = 0
    uploaded_chunks: List[int] = field(default_factory=list)
    storage_backend: StorageBackend = StorageBackend.AWS_S3
    encryption_key: Optional[str] = None
    access_level: str = "private"
    tags: Dict[str, str] = field(default_factory=dict)
    custom_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'file_id': self.file_id,
            'filename': self.filename,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_hash': self.file_hash,
            'mime_type': self.mime_type,
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat(),
            'version': self.version,
            'sync_status': self.sync_status.value,
            'chunk_size': self.chunk_size,
            'total_chunks': self.total_chunks,
            'uploaded_chunks': self.uploaded_chunks,
            'storage_backend': self.storage_backend.value,
            'encryption_key': self.encryption_key,
            'access_level': self.access_level,
            'tags': self.tags,
            'custom_metadata': self.custom_metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileMetadata':
        """从字典创建实例"""
        data = data.copy()
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('modified_at'), str):
            data['modified_at'] = datetime.fromisoformat(data['modified_at'])
        if isinstance(data.get('sync_status'), str):
            data['sync_status'] = SyncStatus(data['sync_status'])
        if isinstance(data.get('storage_backend'), str):
            data['storage_backend'] = StorageBackend(data['storage_backend'])
        return cls(**data)


@dataclass
class SyncOperation:
    """同步操作"""
    operation_id: str
    operation_type: FileOperationType
    file_metadata: FileMetadata
    priority: int = 0
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress: float = 0.0
    dependencies: List[str] = field(default_factory=list)

    def __lt__(self, other: 'SyncOperation') -> bool:
        """优先级比较"""
        if self.priority == other.priority:
            return self.created_at < other.created_at
        return self.priority > other.priority


class CloudStorageConfig:
    """云端存储配置"""

    def __init__(self):
        # AWS S3 配置
        self.aws_access_key_id: Optional[str] = None
        self.aws_secret_access_key: Optional[str] = None
        self.aws_region: str = "us-east-1"
        self.aws_s3_bucket: str = "cineaistudio-storage"

        # Azure Blob 配置
        self.azure_connection_string: Optional[str] = None
        self.azure_container: str = "cineaistudio"

        # Google Cloud 配置
        self.google_credentials_path: Optional[str] = None
        self.google_bucket: str = "cineaistudio-storage"

        # 阿里云 OSS 配置
        self.aliyun_access_key_id: Optional[str] = None
        self.aliyun_access_key_secret: Optional[str] = None
        self.aliyun_bucket: str = "cineaistudio"
        self.aliyun_endpoint: str = "https://oss-cn-hangzhou.aliyuncs.com"

        # MinIO 配置
        self.minio_endpoint: str = "http://localhost:9000"
        self.minio_access_key: str = "minioadmin"
        self.minio_secret_key: str = "minioadmin"
        self.minio_bucket: str = "cineaistudio"

        # Redis 配置（用于缓存和队列）
        self.redis_host: str = "localhost"
        self.redis_port: int = 6379
        self.redis_db: int = 0
        self.redis_password: Optional[str] = None

        # 同步配置
        self.sync_chunk_size: int = 64 * 1024 * 1024  # 64MB
        self.max_concurrent_uploads: int = 4
        self.max_concurrent_downloads: int = 4
        self.retry_attempts: int = 3
        self.retry_delay: float = 1.0
        self.cache_size: int = 10 * 1024 * 1024 * 1024  # 10GB
        self.enable_compression: bool = True
        self.enable_encryption: bool = True
        self.auto_sync: bool = True
        self.sync_interval: int = 60  # 秒

        # 性能配置
        self.enable_cdn: bool = True
        self.cdn_endpoint: Optional[str] = None
        self.enable_accelerated_upload: bool = True
        self.enable_multi_part_upload: bool = True
        self.enable_deduplication: bool = True


class CloudStorageBackend:
    """云端存储后端基类"""

    def __init__(self, config: CloudStorageConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    async def upload_file(self, file_path: str, remote_path: str, metadata: FileMetadata) -> bool:
        """上传文件"""
        raise NotImplementedError

    async def download_file(self, remote_path: str, local_path: str, metadata: FileMetadata) -> bool:
        """下载文件"""
        raise NotImplementedError

    async def delete_file(self, remote_path: str) -> bool:
        """删除文件"""
        raise NotImplementedError

    async def file_exists(self, remote_path: str) -> bool:
        """检查文件是否存在"""
        raise NotImplementedError

    async def get_file_metadata(self, remote_path: str) -> Optional[FileMetadata]:
        """获取文件元数据"""
        raise NotImplementedError

    async def list_files(self, prefix: str = "") -> List[FileMetadata]:
        """列出文件"""
        raise NotImplementedError


class AWSS3Backend(CloudStorageBackend):
    """AWS S3 存储后端"""

    def __init__(self, config: CloudStorageConfig):
        super().__init__(config)
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=config.aws_access_key_id,
            aws_secret_access_key=config.aws_secret_access_key,
            region_name=config.aws_region
        )
        self.s3_resource = boto3.resource(
            's3',
            aws_access_key_id=config.aws_access_key_id,
            aws_secret_access_key=config.aws_secret_access_key,
            region_name=config.aws_region
        )

    async def upload_file(self, file_path: str, remote_path: str, metadata: FileMetadata) -> bool:
        """上传文件到S3"""
        try:
            if self.config.enable_multi_part_upload and metadata.file_size > 100 * 1024 * 1024:
                return await self._upload_multipart(file_path, remote_path, metadata)
            else:
                return await self._upload_single(file_path, remote_path, metadata)
        except Exception as e:
            self.logger.error(f"Failed to upload file {file_path} to S3: {e}")
            return False

    async def _upload_single(self, file_path: str, remote_path: str, metadata: FileMetadata) -> bool:
        """单文件上传"""
        extra_args = {
            'Metadata': {
                'file-hash': metadata.file_hash,
                'file-id': metadata.file_id,
                'version': str(metadata.version),
                'mime-type': metadata.mime_type
            }
        }

        if self.config.enable_encryption and metadata.encryption_key:
            extra_args['ServerSideEncryption'] = 'AES256'

        self.s3_client.upload_file(
            file_path,
            self.config.aws_s3_bucket,
            remote_path,
            ExtraArgs=extra_args
        )
        return True

    async def _upload_multipart(self, file_path: str, remote_path: str, metadata: FileMetadata) -> bool:
        """分块上传大文件"""
        file_size = metadata.file_size
        chunk_size = metadata.chunk_size
        parts = []

        # 初始化分块上传
        upload_id = self.s3_client.create_multipart_upload(
            Bucket=self.config.aws_s3_bucket,
            Key=remote_path,
            Metadata={
                'file-hash': metadata.file_hash,
                'file-id': metadata.file_id,
                'version': str(metadata.version),
                'mime-type': metadata.mime_type
            }
        )['UploadId']

        try:
            # 上传分块
            part_number = 1
            for offset in range(0, file_size, chunk_size):
                end = min(offset + chunk_size, file_size)
                part = self.s3_client.upload_part(
                    Bucket=self.config.aws_s3_bucket,
                    Key=remote_path,
                    PartNumber=part_number,
                    UploadId=upload_id,
                    Body=open(file_path, 'rb').read(offset, end - offset)
                )
                parts.append({
                    'PartNumber': part_number,
                    'ETag': part['ETag']
                })
                part_number += 1

            # 完成分块上传
            self.s3_client.complete_multipart_upload(
                Bucket=self.config.aws_s3_bucket,
                Key=remote_path,
                UploadId=upload_id,
                MultipartUpload={'Parts': parts}
            )
            return True

        except Exception as e:
            # 取消分块上传
            self.s3_client.abort_multipart_upload(
                Bucket=self.config.aws_s3_bucket,
                Key=remote_path,
                UploadId=upload_id
            )
            raise e

    async def download_file(self, remote_path: str, local_path: str, metadata: FileMetadata) -> bool:
        """从S3下载文件"""
        try:
            self.s3_client.download_file(
                self.config.aws_s3_bucket,
                remote_path,
                local_path
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to download file {remote_path} from S3: {e}")
            return False

    async def delete_file(self, remote_path: str) -> bool:
        """删除S3文件"""
        try:
            self.s3_client.delete_object(
                Bucket=self.config.aws_s3_bucket,
                Key=remote_path
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete file {remote_path} from S3: {e}")
            return False

    async def file_exists(self, remote_path: str) -> bool:
        """检查S3文件是否存在"""
        try:
            self.s3_client.head_object(
                Bucket=self.config.aws_s3_bucket,
                Key=remote_path
            )
            return True
        except Exception:
            return False

    async def get_file_metadata(self, remote_path: str) -> Optional[FileMetadata]:
        """获取S3文件元数据"""
        try:
            response = self.s3_client.head_object(
                Bucket=self.config.aws_s3_bucket,
                Key=remote_path
            )
            return FileMetadata(
                file_id=response['Metadata'].get('file-id', ''),
                filename=os.path.basename(remote_path),
                file_path=remote_path,
                file_size=response['ContentLength'],
                file_hash=response['Metadata'].get('file-hash', ''),
                mime_type=response['ContentType'] or response['Metadata'].get('mime-type', 'application/octet-stream'),
                version=int(response['Metadata'].get('version', 1))
            )
        except Exception as e:
            self.logger.error(f"Failed to get metadata for {remote_path}: {e}")
            return None

    async def list_files(self, prefix: str = "") -> List[FileMetadata]:
        """列出S3文件"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.config.aws_s3_bucket,
                Prefix=prefix
            )

            files = []
            for obj in response.get('Contents', []):
                metadata = await self.get_file_metadata(obj['Key'])
                if metadata:
                    files.append(metadata)

            return files
        except Exception as e:
            self.logger.error(f"Failed to list files with prefix {prefix}: {e}")
            return []


class CloudStorageManager(QObject):
    """云端存储管理器"""

    # 信号定义
    sync_started = pyqtSignal(str)                # 同步开始信号
    sync_progress = pyqtSignal(str, float)        # 同步进度信号
    sync_completed = pyqtSignal(str)              # 同步完成信号
    sync_failed = pyqtSignal(str, str)            # 同步失败信号
    file_uploaded = pyqtSignal(str)                # 文件上传完成信号
    file_downloaded = pyqtSignal(str)             # 文件下载完成信号
    file_deleted = pyqtSignal(str)                # 文件删除完成信号
    conflict_detected = pyqtSignal(str, str)      # 冲突检测信号
    cache_updated = pyqtSignal(str)               # 缓存更新信号
    storage_stats_updated = pyqtSignal(dict)      # 存储统计更新信号

    def __init__(self, config: CloudStorageConfig):
        super().__init__()

        self.config = config
        self.logger = logging.getLogger(__name__)

        # 存储后端
        self.backends: Dict[StorageBackend, CloudStorageBackend] = {}
        self.primary_backend = StorageBackend.AWS_S3

        # 文件元数据缓存
        self.file_metadata_cache: Dict[str, FileMetadata] = {}
        self.file_locks: Dict[str, threading.Lock] = {}

        # 同步队列
        self.sync_queue = PriorityQueue()
        self.active_operations: Dict[str, SyncOperation] = {}

        # 缓存系统
        self.local_cache_dir = os.path.expanduser("~/.cineaistudio/cache")
        self.cache_metadata: Dict[str, Dict] = {}

        # Redis 连接
        self.redis_client: Optional[redis.Redis] = None

        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=8)

        # 统计信息
        self.storage_stats = {
            'total_files': 0,
            'total_size': 0,
            'synced_files': 0,
            'synced_size': 0,
            'pending_files': 0,
            'failed_files': 0,
            'cache_usage': 0,
            'last_sync': None
        }

        # 初始化组件
        self._initialize_backends()
        self._initialize_cache()
        self._initialize_redis()

        # 启动后台任务
        self._start_background_tasks()

    def _initialize_backends(self):
        """初始化存储后端"""
        # AWS S3
        if self.config.aws_access_key_id and self.config.aws_secret_access_key:
            self.backends[StorageBackend.AWS_S3] = AWSS3Backend(self.config)

        # 其他后端可以在这里初始化...

    def _initialize_cache(self):
        """初始化缓存系统"""
        os.makedirs(self.local_cache_dir, exist_ok=True)
        self._load_cache_metadata()

    def _initialize_redis(self):
        """初始化Redis连接"""
        try:
            self.redis_client = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                password=self.config.redis_password,
                decode_responses=True
            )
            # 测试连接
            self.redis_client.ping()
            self.logger.info("Redis connection established")
        except Exception as e:
            self.logger.warning(f"Failed to connect to Redis: {e}")

    def _start_background_tasks(self):
        """启动后台任务"""
        # 启动同步处理器
        self.sync_processor_thread = threading.Thread(target=self._sync_processor, daemon=True)
        self.sync_processor_thread.start()

        # 启动缓存清理器
        self.cache_cleaner_thread = threading.Thread(target=self._cache_cleaner, daemon=True)
        self.cache_cleaner_thread.start()

        # 启动自动同步
        if self.config.auto_sync:
            self.auto_sync_timer = QTimer()
            self.auto_sync_timer.timeout.connect(self._auto_sync)
            self.auto_sync_timer.start(self.config.sync_interval * 1000)

    def _sync_processor(self):
        """同步处理器"""
        while True:
            try:
                if not self.sync_queue.empty():
                    operation = self.sync_queue.get()
                    asyncio.run(self._process_sync_operation(operation))
                    self.sync_queue.task_done()
                else:
                    time.sleep(1)
            except Exception as e:
                self.logger.error(f"Sync processor error: {e}")
                time.sleep(5)

    async def _process_sync_operation(self, operation: SyncOperation):
        """处理同步操作"""
        operation_id = operation.operation_id
        operation.started_at = datetime.now()
        self.active_operations[operation_id] = operation

        try:
            self.sync_started.emit(operation_id)

            if operation.operation_type == FileOperationType.UPLOAD:
                await self._upload_file_operation(operation)
            elif operation.operation_type == FileOperationType.DOWNLOAD:
                await self._download_file_operation(operation)
            elif operation.operation_type == FileOperationType.DELETE:
                await self._delete_file_operation(operation)

            operation.completed_at = datetime.now()
            operation.progress = 1.0
            self.sync_completed.emit(operation_id)

        except Exception as e:
            operation.error_message = str(e)
            operation.retry_count += 1

            if operation.retry_count < operation.max_retries:
                # 重新加入队列
                self.sync_queue.put(operation)
            else:
                self.sync_failed.emit(operation_id, str(e))

        finally:
            if operation_id in self.active_operations:
                del self.active_operations[operation_id]

    async def _upload_file_operation(self, operation: SyncOperation):
        """上传文件操作"""
        metadata = operation.file_metadata
        backend = self.backends.get(metadata.storage_backend)

        if not backend:
            raise Exception(f"Storage backend {metadata.storage_backend} not available")

        # 检查文件是否已存在
        remote_exists = await backend.file_exists(metadata.file_path)
        if remote_exists:
            remote_metadata = await backend.get_file_metadata(metadata.file_path)
            if remote_metadata and remote_metadata.file_hash == metadata.file_hash:
                # 文件相同，跳过上传
                metadata.sync_status = SyncStatus.SYNCED
                self.sync_completed.emit(operation.operation_id)
                return

        # 执行上传
        success = await backend.upload_file(metadata.file_path, metadata.file_path, metadata)

        if success:
            metadata.sync_status = SyncStatus.SYNCED
            metadata.uploaded_chunks = list(range(metadata.total_chunks))
            self.file_uploaded.emit(metadata.file_id)
            self._update_file_metadata_cache(metadata)
            self._update_storage_stats()
        else:
            metadata.sync_status = SyncStatus.FAILED
            raise Exception("Upload failed")

    async def _download_file_operation(self, operation: SyncOperation):
        """下载文件操作"""
        metadata = operation.file_metadata
        backend = self.backends.get(metadata.storage_backend)

        if not backend:
            raise Exception(f"Storage backend {metadata.storage_backend} not available")

        # 确保本地目录存在
        local_dir = os.path.dirname(metadata.file_path)
        os.makedirs(local_dir, exist_ok=True)

        # 执行下载
        success = await backend.download_file(metadata.file_path, metadata.file_path, metadata)

        if success:
            metadata.sync_status = SyncStatus.SYNCED
            self.file_downloaded.emit(metadata.file_id)
            self._update_file_metadata_cache(metadata)
            self._update_cache(metadata.file_path)
        else:
            metadata.sync_status = SyncStatus.FAILED
            raise Exception("Download failed")

    async def _delete_file_operation(self, operation: SyncOperation):
        """删除文件操作"""
        metadata = operation.file_metadata
        backend = self.backends.get(metadata.storage_backend)

        if not backend:
            raise Exception(f"Storage backend {metadata.storage_backend} not available")

        # 执行删除
        success = await backend.delete_file(metadata.file_path)

        if success:
            self.file_deleted.emit(metadata.file_id)
            if metadata.file_id in self.file_metadata_cache:
                del self.file_metadata_cache[metadata.file_id]
            self._remove_from_cache(metadata.file_path)
            self._update_storage_stats()
        else:
            raise Exception("Delete failed")

    def upload_file(self, file_path: str, remote_path: Optional[str] = None,
                   priority: int = 0) -> Optional[str]:
        """上传文件"""
        try:
            if not os.path.exists(file_path):
                raise Exception(f"File not found: {file_path}")

            # 生成文件元数据
            metadata = self._create_file_metadata(file_path, remote_path)

            # 创建同步操作
            operation = SyncOperation(
                operation_id=str(hash(file_path + str(time.time()))),
                operation_type=FileOperationType.UPLOAD,
                file_metadata=metadata,
                priority=priority
            )

            # 加入同步队列
            self.sync_queue.put(operation)

            return operation.operation_id

        except Exception as e:
            self.logger.error(f"Failed to enqueue upload for {file_path}: {e}")
            return None

    def download_file(self, remote_path: str, local_path: str,
                     priority: int = 0) -> Optional[str]:
        """下载文件"""
        try:
            # 获取远程文件元数据
            backend = self.backends.get(self.primary_backend)
            if not backend:
                raise Exception("No primary storage backend available")

            remote_metadata = await backend.get_file_metadata(remote_path)
            if not remote_metadata:
                raise Exception(f"Remote file not found: {remote_path}")

            # 创建本地元数据
            metadata = FileMetadata(
                file_id=remote_metadata.file_id,
                filename=remote_metadata.filename,
                file_path=local_path,
                file_size=remote_metadata.file_size,
                file_hash=remote_metadata.file_hash,
                mime_type=remote_metadata.mime_type,
                storage_backend=remote_metadata.storage_backend
            )

            # 创建同步操作
            operation = SyncOperation(
                operation_id=str(hash(remote_path + str(time.time()))),
                operation_type=FileOperationType.DOWNLOAD,
                file_metadata=metadata,
                priority=priority
            )

            # 加入同步队列
            self.sync_queue.put(operation)

            return operation.operation_id

        except Exception as e:
            self.logger.error(f"Failed to enqueue download for {remote_path}: {e}")
            return None

    def delete_file(self, remote_path: str, priority: int = 0) -> Optional[str]:
        """删除文件"""
        try:
            # 获取文件元数据
            backend = self.backends.get(self.primary_backend)
            if not backend:
                raise Exception("No primary storage backend available")

            metadata = await backend.get_file_metadata(remote_path)
            if not metadata:
                raise Exception(f"File not found: {remote_path}")

            # 创建同步操作
            operation = SyncOperation(
                operation_id=str(hash(remote_path + str(time.time()))),
                operation_type=FileOperationType.DELETE,
                file_metadata=metadata,
                priority=priority
            )

            # 加入同步队列
            self.sync_queue.put(operation)

            return operation.operation_id

        except Exception as e:
            self.logger.error(f"Failed to enqueue delete for {remote_path}: {e}")
            return None

    def _create_file_metadata(self, file_path: str, remote_path: Optional[str] = None) -> FileMetadata:
        """创建文件元数据"""
        stat = os.stat(file_path)

        # 计算文件哈希
        file_hash = self._calculate_file_hash(file_path)

        # 确定MIME类型
        mime_type = self._get_mime_type(file_path)

        # 计算分块信息
        file_size = stat.st_size
        chunk_size = self.config.sync_chunk_size
        total_chunks = (file_size + chunk_size - 1) // chunk_size

        return FileMetadata(
            file_id=str(hash(file_path + str(stat.st_mtime))),
            filename=os.path.basename(file_path),
            file_path=remote_path or file_path,
            file_size=file_size,
            file_hash=file_hash,
            mime_type=mime_type,
            created_at=datetime.fromtimestamp(stat.st_ctime),
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            chunk_size=chunk_size,
            total_chunks=total_chunks,
            storage_backend=self.primary_backend
        )

    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件哈希"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _get_mime_type(self, file_path: str) -> str:
        """获取MIME类型"""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or "application/octet-stream"

    def _update_file_metadata_cache(self, metadata: FileMetadata):
        """更新文件元数据缓存"""
        self.file_metadata_cache[metadata.file_id] = metadata

        # 保存到Redis
        if self.redis_client:
            try:
                self.redis_client.setex(
                    f"file_metadata:{metadata.file_id}",
                    3600,  # 1小时过期
                    json.dumps(metadata.to_dict())
                )
            except Exception as e:
                self.logger.warning(f"Failed to cache metadata in Redis: {e}")

    def _update_cache(self, file_path: str):
        """更新缓存"""
        try:
            stat = os.stat(file_path)
            cache_key = os.path.relpath(file_path, self.local_cache_dir)

            self.cache_metadata[cache_key] = {
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'accessed': time.time()
            }

            # 保存到Redis
            if self.redis_client:
                self.redis_client.setex(
                    f"cache:{cache_key}",
                    3600,
                    json.dumps(self.cache_metadata[cache_key])
                )

            self.cache_updated.emit(cache_key)

        except Exception as e:
            self.logger.warning(f"Failed to update cache for {file_path}: {e}")

    def _remove_from_cache(self, file_path: str):
        """从缓存中移除"""
        try:
            cache_key = os.path.relpath(file_path, self.local_cache_dir)

            if cache_key in self.cache_metadata:
                del self.cache_metadata[cache_key]

            # 从Redis中删除
            if self.redis_client:
                self.redis_client.delete(f"cache:{cache_key}")

            if os.path.exists(file_path):
                os.remove(file_path)

        except Exception as e:
            self.logger.warning(f"Failed to remove from cache: {e}")

    def _cache_cleaner(self):
        """缓存清理器"""
        while True:
            try:
                self._cleanup_cache()
                time.sleep(300)  # 5分钟清理一次
            except Exception as e:
                self.logger.error(f"Cache cleaner error: {e}")
                time.sleep(60)

    def _cleanup_cache(self):
        """清理缓存"""
        try:
            current_time = time.time()
            cache_usage = sum(info['size'] for info in self.cache_metadata.values())

            # 如果缓存超过限制，删除最旧的文件
            if cache_usage > self.config.cache_size:
                sorted_files = sorted(self.cache_metadata.items(),
                                    key=lambda x: x[1]['accessed'])

                for file_path, info in sorted_files:
                    if cache_usage <= self.config.cache_size * 0.8:  # 清理到80%
                        break

                    full_path = os.path.join(self.local_cache_dir, file_path)
                    self._remove_from_cache(full_path)
                    cache_usage -= info['size']

        except Exception as e:
            self.logger.error(f"Cache cleanup failed: {e}")

    def _update_storage_stats(self):
        """更新存储统计"""
        try:
            backend = self.backends.get(self.primary_backend)
            if backend:
                files = asyncio.run(backend.list_files())

                self.storage_stats.update({
                    'total_files': len(files),
                    'total_size': sum(f.file_size for f in files),
                    'synced_files': len([f for f in files if f.sync_status == SyncStatus.SYNCED]),
                    'synced_size': sum(f.file_size for f in files if f.sync_status == SyncStatus.SYNCED),
                    'pending_files': len([f for f in files if f.sync_status == SyncStatus.PENDING]),
                    'failed_files': len([f for f in files if f.sync_status == SyncStatus.FAILED]),
                    'cache_usage': sum(info['size'] for info in self.cache_metadata.values()),
                    'last_sync': datetime.now().isoformat()
                })

                self.storage_stats_updated.emit(self.storage_stats)

        except Exception as e:
            self.logger.error(f"Failed to update storage stats: {e}")

    def _auto_sync(self):
        """自动同步"""
        try:
            # 这里可以实现自动同步逻辑
            # 例如同步本地修改的文件
            pass
        except Exception as e:
            self.logger.error(f"Auto sync failed: {e}")

    def _load_cache_metadata(self):
        """加载缓存元数据"""
        try:
            metadata_file = os.path.join(self.local_cache_dir, 'cache_metadata.json')
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    self.cache_metadata = json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load cache metadata: {e}")

    def save_cache_metadata(self):
        """保存缓存元数据"""
        try:
            metadata_file = os.path.join(self.local_cache_dir, 'cache_metadata.json')
            with open(metadata_file, 'w') as f:
                json.dump(self.cache_metadata, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to save cache metadata: {e}")

    def get_sync_status(self, file_path: str) -> Optional[SyncStatus]:
        """获取文件同步状态"""
        for metadata in self.file_metadata_cache.values():
            if metadata.file_path == file_path:
                return metadata.sync_status
        return None

    def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        return self.storage_stats.copy()

    def get_active_operations(self) -> List[SyncOperation]:
        """获取活动操作列表"""
        return list(self.active_operations.values())

    def cancel_operation(self, operation_id: str) -> bool:
        """取消操作"""
        if operation_id in self.active_operations:
            operation = self.active_operations[operation_id]
            operation.error_message = "Cancelled by user"
            operation.completed_at = datetime.now()
            self.sync_failed.emit(operation_id, "Cancelled by user")
            return True
        return False

    def pause_sync(self) -> None:
        """暂停同步"""
        # 实现暂停逻辑
        pass

    def resume_sync(self) -> None:
        """恢复同步"""
        # 实现恢复逻辑
        pass

    def cleanup(self):
        """清理资源"""
        # 保存缓存元数据
        self.save_cache_metadata()

        # 关闭线程池
        self.executor.shutdown(wait=True)

        # 关闭Redis连接
        if self.redis_client:
            self.redis_client.close()

    def enable_compression(self, enable: bool) -> None:
        """启用/禁用压缩"""
        self.config.enable_compression = enable

    def enable_encryption(self, enable: bool) -> None:
        """启用/禁用加密"""
        self.config.enable_encryption = enable

    def set_sync_chunk_size(self, chunk_size: int) -> None:
        """设置同步分块大小"""
        self.config.sync_chunk_size = chunk_size

    def set_max_concurrent_operations(self, max_uploads: int, max_downloads: int) -> None:
        """设置最大并发操作数"""
        self.config.max_concurrent_uploads = max_uploads
        self.config.max_concurrent_downloads = max_downloads