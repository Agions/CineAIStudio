#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio 文件同步引擎
提供高效的文件同步、版本控制和增量同步功能
"""

import asyncio
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
from queue import Queue, PriorityQueue
import hashlib
import shutil
import sqlite3
import uuid
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .cloud_storage_manager import CloudStorageManager, SyncStatus, FileOperationType, FileMetadata


class SyncMode(Enum):
    """同步模式"""
    BIDIRECTIONAL = "bidirectional"  # 双向同步
    UPLOAD_ONLY = "upload_only"      # 仅上传
    DOWNLOAD_ONLY = "download_only"  # 仅下载
    MIRROR = "mirror"               # 镜像模式


class ConflictResolution(Enum):
    """冲突解决策略"""
    NEWER_WINS = "newer_wins"       # 新文件获胜
    LARGER_WINS = "larger_wins"      # 大文件获胜
    MANUAL_RESOLUTION = "manual"     # 手动解决
    KEEP_BOTH = "keep_both"         # 保留两个版本


@dataclass
class SyncConflict:
    """同步冲突"""
    conflict_id: str
    local_path: str
    remote_path: str
    local_metadata: FileMetadata
    remote_metadata: FileMetadata
    conflict_type: str
    detected_at: datetime = field(default_factory=datetime.now)
    resolution: Optional[ConflictResolution] = None
    resolved_at: Optional[datetime] = None


@dataclass
class SyncVersion:
    """同步版本"""
    version_id: str
    file_id: str
    version_number: int
    file_path: str
    file_hash: str
    file_size: int
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "local"
    parent_version: Optional[str] = None
    delta_info: Optional[Dict] = None
    storage_path: Optional[str] = None


class FileSyncDatabase:
    """文件同步数据库"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_database()

    def _init_database(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sync_metadata (
                    file_id TEXT PRIMARY KEY,
                    local_path TEXT UNIQUE NOT NULL,
                    remote_path TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    last_modified REAL NOT NULL,
                    sync_status TEXT NOT NULL,
                    version_number INTEGER DEFAULT 1,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS sync_versions (
                    version_id TEXT PRIMARY KEY,
                    file_id TEXT NOT NULL,
                    version_number INTEGER NOT NULL,
                    file_hash TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    created_at REAL NOT NULL,
                    created_by TEXT NOT NULL,
                    parent_version TEXT,
                    delta_info TEXT,
                    storage_path TEXT,
                    FOREIGN KEY (file_id) REFERENCES sync_metadata (file_id)
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS sync_operations (
                    operation_id TEXT PRIMARY KEY,
                    file_id TEXT NOT NULL,
                    operation_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    priority INTEGER DEFAULT 0,
                    retry_count INTEGER DEFAULT 0,
                    created_at REAL NOT NULL,
                    completed_at REAL,
                    error_message TEXT,
                    FOREIGN KEY (file_id) REFERENCES sync_metadata (file_id)
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS sync_conflicts (
                    conflict_id TEXT PRIMARY KEY,
                    file_id TEXT NOT NULL,
                    local_path TEXT NOT NULL,
                    remote_path TEXT NOT NULL,
                    local_hash TEXT NOT NULL,
                    remote_hash TEXT NOT NULL,
                    conflict_type TEXT NOT NULL,
                    detected_at REAL NOT NULL,
                    resolution TEXT,
                    resolved_at REAL,
                    FOREIGN KEY (file_id) REFERENCES sync_metadata (file_id)
                )
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_sync_metadata_local_path
                ON sync_metadata (local_path)
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_sync_metadata_remote_path
                ON sync_metadata (remote_path)
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_sync_versions_file_id
                ON sync_versions (file_id)
            ''')

            conn.commit()

    def add_file_metadata(self, metadata: FileMetadata) -> bool:
        """添加文件元数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO sync_metadata
                    (file_id, local_path, remote_path, file_hash, file_size,
                     last_modified, sync_status, version_number, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metadata.file_id,
                    metadata.file_path,
                    metadata.file_path,  # 假设远程路径与本地路径相同
                    metadata.file_hash,
                    metadata.file_size,
                    metadata.modified_at.timestamp(),
                    metadata.sync_status.value,
                    metadata.version,
                    metadata.created_at.timestamp(),
                    datetime.now().timestamp()
                ))
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to add file metadata: {e}")
            return False

    def get_file_metadata(self, file_id: str) -> Optional[FileMetadata]:
        """获取文件元数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM sync_metadata WHERE file_id = ?
                ''', (file_id,))
                row = cursor.fetchone()

                if row:
                    return FileMetadata(
                        file_id=row['file_id'],
                        filename=os.path.basename(row['local_path']),
                        file_path=row['local_path'],
                        file_size=row['file_size'],
                        file_hash=row['file_hash'],
                        mime_type="application/octet-stream",
                        created_at=datetime.fromtimestamp(row['created_at']),
                        modified_at=datetime.fromtimestamp(row['last_modified']),
                        version=row['version_number'],
                        sync_status=SyncStatus(row['sync_status'])
                    )
                return None
        except Exception as e:
            self.logger.error(f"Failed to get file metadata: {e}")
            return None

    def get_file_by_local_path(self, local_path: str) -> Optional[FileMetadata]:
        """根据本地路径获取文件元数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM sync_metadata WHERE local_path = ?
                ''', (local_path,))
                row = cursor.fetchone()

                if row:
                    return FileMetadata(
                        file_id=row['file_id'],
                        filename=os.path.basename(row['local_path']),
                        file_path=row['local_path'],
                        file_size=row['file_size'],
                        file_hash=row['file_hash'],
                        mime_type="application/octet-stream",
                        created_at=datetime.fromtimestamp(row['created_at']),
                        modified_at=datetime.fromtimestamp(row['last_modified']),
                        version=row['version_number'],
                        sync_status=SyncStatus(row['sync_status'])
                    )
                return None
        except Exception as e:
            self.logger.error(f"Failed to get file by local path: {e}")
            return None

    def update_file_metadata(self, metadata: FileMetadata) -> bool:
        """更新文件元数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    UPDATE sync_metadata
                    SET file_hash = ?, file_size = ?, last_modified = ?,
                        sync_status = ?, version_number = ?, updated_at = ?
                    WHERE file_id = ?
                ''', (
                    metadata.file_hash,
                    metadata.file_size,
                    metadata.modified_at.timestamp(),
                    metadata.sync_status.value,
                    metadata.version,
                    datetime.now().timestamp(),
                    metadata.file_id
                ))
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to update file metadata: {e}")
            return False

    def add_version(self, version: SyncVersion) -> bool:
        """添加版本"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO sync_versions
                    (version_id, file_id, version_number, file_hash, file_size,
                     created_at, created_by, parent_version, delta_info, storage_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    version.version_id,
                    version.file_id,
                    version.version_number,
                    version.file_hash,
                    version.file_size,
                    version.created_at.timestamp(),
                    version.created_by,
                    version.parent_version,
                    json.dumps(version.delta_info) if version.delta_info else None,
                    version.storage_path
                ))
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to add version: {e}")
            return False

    def get_file_versions(self, file_id: str) -> List[SyncVersion]:
        """获取文件版本历史"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM sync_versions
                    WHERE file_id = ?
                    ORDER BY version_number DESC
                ''', (file_id,))
                rows = cursor.fetchall()

                versions = []
                for row in rows:
                    versions.append(SyncVersion(
                        version_id=row['version_id'],
                        file_id=row['file_id'],
                        version_number=row['version_number'],
                        file_path="",  # 需要从sync_metadata获取
                        file_hash=row['file_hash'],
                        file_size=row['file_size'],
                        created_at=datetime.fromtimestamp(row['created_at']),
                        created_by=row['created_by'],
                        parent_version=row['parent_version'],
                        delta_info=json.loads(row['delta_info']) if row['delta_info'] else None,
                        storage_path=row['storage_path']
                    ))
                return versions
        except Exception as e:
            self.logger.error(f"Failed to get file versions: {e}")
            return []

    def add_conflict(self, conflict: SyncConflict) -> bool:
        """添加冲突"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO sync_conflicts
                    (conflict_id, file_id, local_path, remote_path, local_hash,
                     remote_hash, conflict_type, detected_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    conflict.conflict_id,
                    conflict.local_metadata.file_id,
                    conflict.local_path,
                    conflict.remote_path,
                    conflict.local_metadata.file_hash,
                    conflict.remote_metadata.file_hash,
                    conflict.conflict_type,
                    conflict.detected_at.timestamp()
                ))
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to add conflict: {e}")
            return False

    def get_conflicts(self) -> List[SyncConflict]:
        """获取所有冲突"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM sync_conflicts WHERE resolution IS NULL
                ''')
                rows = cursor.fetchall()

                conflicts = []
                for row in rows:
                    # 这里需要获取本地和远程元数据
                    local_metadata = self.get_file_metadata(row['file_id'])
                    if local_metadata:
                        conflict = SyncConflict(
                            conflict_id=row['conflict_id'],
                            local_path=row['local_path'],
                            remote_path=row['remote_path'],
                            local_metadata=local_metadata,
                            remote_metadata=local_metadata,  # 简化处理
                            conflict_type=row['conflict_type'],
                            detected_at=datetime.fromtimestamp(row['detected_at'])
                        )
                        conflicts.append(conflict)
                return conflicts
        except Exception as e:
            self.logger.error(f"Failed to get conflicts: {e}")
            return []

    def resolve_conflict(self, conflict_id: str, resolution: ConflictResolution) -> bool:
        """解决冲突"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    UPDATE sync_conflicts
                    SET resolution = ?, resolved_at = ?
                    WHERE conflict_id = ?
                ''', (
                    resolution.value,
                    datetime.now().timestamp(),
                    conflict_id
                ))
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to resolve conflict: {e}")
            return False


class FileSystemWatcher(FileSystemEventHandler):
    """文件系统监视器"""

    def __init__(self, sync_engine: 'FileSyncEngine'):
        self.sync_engine = sync_engine
        self.logger = logging.getLogger(__name__)
        self.observer = Observer()
        self.watched_paths: Set[str] = set()

    def watch_directory(self, directory: str):
        """监视目录"""
        if directory not in self.watched_paths:
            self.observer.schedule(self, directory, recursive=True)
            self.watched_paths.add(directory)
            self.logger.info(f"Watching directory: {directory}")

    def start(self):
        """启动监视器"""
        self.observer.start()

    def stop(self):
        """停止监视器"""
        self.observer.stop()
        self.observer.join()

    def on_modified(self, event):
        """文件修改事件"""
        if not event.is_directory:
            self.sync_engine.queue_file_sync(event.src_path)

    def on_created(self, event):
        """文件创建事件"""
        if not event.is_directory:
            self.sync_engine.queue_file_sync(event.src_path)

    def on_deleted(self, event):
        """文件删除事件"""
        if not event.is_directory:
            self.sync_engine.queue_file_delete(event.src_path)

    def on_moved(self, event):
        """文件移动事件"""
        if not event.is_directory:
            self.sync_engine.queue_file_move(event.src_path, event.dest_path)


class DeltaCalculator:
    """增量计算器"""

    def __init__(self, chunk_size: int = 1024 * 1024):
        self.chunk_size = chunk_size

    def calculate_delta(self, old_file: str, new_file: str) -> Dict[str, Any]:
        """计算文件差异"""
        try:
            old_hash = self._calculate_file_hash(old_file)
            new_hash = self._calculate_file_hash(new_file)

            if old_hash == new_hash:
                return {"delta_type": "unchanged"}

            # 使用rsync算法计算差异
            delta_blocks = self._rsync_delta(old_file, new_file)

            return {
                "delta_type": "modified",
                "old_hash": old_hash,
                "new_hash": new_hash,
                "delta_blocks": delta_blocks,
                "delta_size": sum(len(block) for block in delta_blocks)
            }

        except Exception as e:
            logging.error(f"Failed to calculate delta: {e}")
            return {"delta_type": "error", "error": str(e)}

    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件哈希"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _rsync_delta(self, old_file: str, new_file: str) -> List[bytes]:
        """使用rsync算法计算差异"""
        # 简化的rsync实现
        old_chunks = {}
        with open(old_file, "rb") as f:
            offset = 0
            while True:
                chunk = f.read(self.chunk_size)
                if not chunk:
                    break
                chunk_hash = hashlib.md5(chunk).hexdigest()
                old_chunks[chunk_hash] = (offset, len(chunk))
                offset += len(chunk)

        delta_blocks = []
        with open(new_file, "rb") as f:
            offset = 0
            while True:
                chunk = f.read(self.chunk_size)
                if not chunk:
                    break
                chunk_hash = hashlib.md5(chunk).hexdigest()
                if chunk_hash in old_chunks:
                    # 匹配的块
                    delta_blocks.append({
                        "type": "copy",
                        "offset": old_chunks[chunk_hash][0],
                        "length": len(chunk)
                    })
                else:
                    # 新数据
                    delta_blocks.append({
                        "type": "data",
                        "data": chunk.hex()
                    })
                offset += len(chunk)

        return delta_blocks

    def apply_delta(self, base_file: str, delta_info: Dict[str, Any], output_file: str) -> bool:
        """应用增量更新"""
        try:
            if delta_info["delta_type"] == "unchanged":
                shutil.copy2(base_file, output_file)
                return True

            with open(base_file, "rb") as base_f:
                with open(output_file, "wb") as out_f:
                    for block in delta_info["delta_blocks"]:
                        if block["type"] == "copy":
                            base_f.seek(block["offset"])
                            data = base_f.read(block["length"])
                            out_f.write(data)
                        elif block["type"] == "data":
                            data = bytes.fromhex(block["data"])
                            out_f.write(data)

            return True

        except Exception as e:
            logging.error(f"Failed to apply delta: {e}")
            return False


class FileSyncEngine:
    """文件同步引擎"""

    def __init__(self, cloud_manager: CloudStorageManager, sync_root: str):
        self.cloud_manager = cloud_manager
        self.sync_root = sync_root
        self.logger = logging.getLogger(__name__)

        # 数据库
        self.db = FileSyncDatabase(os.path.expanduser("~/.cineaistudio/sync.db"))

        # 同步配置
        self.sync_mode = SyncMode.BIDIRECTIONAL
        self.conflict_resolution = ConflictResolution.NEWER_WINS
        self.sync_interval = 60  # 秒
        self.max_concurrent_syncs = 4

        # 组件
        self.file_watcher = FileSystemWatcher(self)
        self.delta_calculator = DeltaCalculator()

        # 同步队列
        self.sync_queue = PriorityQueue()
        self.active_syncs: Dict[str, Any] = {}

        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=self.max_concurrent_syncs)

        # 启动同步引擎
        self._start_sync_engine()

    def _start_sync_engine(self):
        """启动同步引擎"""
        # 启动文件系统监视器
        self.file_watcher.watch_directory(self.sync_root)
        self.file_watcher.start()

        # 启动同步处理器
        self.sync_processor_thread = threading.Thread(target=self._sync_processor, daemon=True)
        self.sync_processor_thread.start()

        # 启动定期同步
        self.periodic_sync_thread = threading.Thread(target=self._periodic_sync, daemon=True)
        self.periodic_sync_thread.start()

    def _sync_processor(self):
        """同步处理器"""
        while True:
            try:
                if not self.sync_queue.empty():
                    sync_task = self.sync_queue.get()
                    self._process_sync_task(sync_task)
                    self.sync_queue.task_done()
                else:
                    time.sleep(1)
            except Exception as e:
                self.logger.error(f"Sync processor error: {e}")
                time.sleep(5)

    def _periodic_sync(self):
        """定期同步"""
        while True:
            try:
                time.sleep(self.sync_interval)
                self.perform_full_sync()
            except Exception as e:
                self.logger.error(f"Periodic sync error: {e}")

    def _process_sync_task(self, task: Dict[str, Any]):
        """处理同步任务"""
        try:
            task_type = task.get('type')
            file_path = task.get('file_path')

            if task_type == 'sync':
                self._sync_file(file_path)
            elif task_type == 'delete':
                self._delete_file(file_path)
            elif task_type == 'move':
                self._move_file(task.get('from_path'), task.get('to_path'))

        except Exception as e:
            self.logger.error(f"Failed to process sync task: {e}")

    def queue_file_sync(self, file_path: str):
        """队列文件同步"""
        task = {
            'type': 'sync',
            'file_path': file_path,
            'priority': 0,
            'timestamp': time.time()
        }
        self.sync_queue.put((0, task))

    def queue_file_delete(self, file_path: str):
        """队列文件删除"""
        task = {
            'type': 'delete',
            'file_path': file_path,
            'priority': 1,
            'timestamp': time.time()
        }
        self.sync_queue.put((1, task))

    def queue_file_move(self, from_path: str, to_path: str):
        """队列文件移动"""
        task = {
            'type': 'move',
            'from_path': from_path,
            'to_path': to_path,
            'priority': 0,
            'timestamp': time.time()
        }
        self.sync_queue.put((0, task))

    def _sync_file(self, file_path: str):
        """同步文件"""
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                self.logger.warning(f"File not found: {file_path}")
                return

            # 获取文件信息
            stat = os.stat(file_path)
            current_hash = self._calculate_file_hash(file_path)

            # 检查是否已在数据库中
            metadata = self.db.get_file_by_local_path(file_path)

            if metadata:
                # 检查是否有变化
                if metadata.file_hash == current_hash:
                    return  # 文件未变化

                # 文件已修改，检查是否有冲突
                await self._check_and_resolve_conflict(metadata, file_path, current_hash)

                # 创建新版本
                await self._create_new_version(metadata, file_path, current_hash)
            else:
                # 新文件
                metadata = self._create_file_metadata(file_path)
                self.db.add_file_metadata(metadata)

            # 执行同步
            if self.sync_mode in [SyncMode.BIDIRECTIONAL, SyncMode.UPLOAD_ONLY]:
                operation_id = self.cloud_manager.upload_file(file_path)
                if operation_id:
                    self.logger.info(f"Queued upload for {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to sync file {file_path}: {e}")

    async def _check_and_resolve_conflict(self, metadata: FileMetadata, file_path: str, current_hash: str):
        """检查并解决冲突"""
        try:
            # 获取远程文件信息
            remote_metadata = await self.cloud_manager.backends.get(
                self.cloud_manager.primary_backend
            ).get_file_metadata(metadata.file_path)

            if remote_metadata and remote_metadata.file_hash != metadata.file_hash:
                # 存在冲突
                conflict = SyncConflict(
                    conflict_id=str(uuid.uuid4()),
                    local_path=file_path,
                    remote_path=metadata.file_path,
                    local_metadata=metadata,
                    remote_metadata=remote_metadata,
                    conflict_type="content_mismatch"
                )

                self.db.add_conflict(conflict)

                # 自动解决冲突
                if self.conflict_resolution == ConflictResolution.NEWER_WINS:
                    if metadata.modified_at > remote_metadata.modified_at:
                        # 本地文件更新，保留本地
                        resolution = ConflictResolution.NEWER_WINS
                    else:
                        # 远程文件更新，下载远程
                        resolution = ConflictResolution.NEWER_WINS
                        await self._download_remote_file(remote_metadata, file_path)

                elif self.conflict_resolution == ConflictResolution.LARGER_WINS:
                    if metadata.file_size > remote_metadata.file_size:
                        resolution = ConflictResolution.LARGER_WINS
                    else:
                        resolution = ConflictResolution.LARGER_WINS
                        await self._download_remote_file(remote_metadata, file_path)

                self.db.resolve_conflict(conflict.conflict_id, resolution)

        except Exception as e:
            self.logger.error(f"Failed to check conflict: {e}")

    async def _create_new_version(self, old_metadata: FileMetadata, file_path: str, new_hash: str):
        """创建新版本"""
        try:
            # 计算增量
            delta_info = self.delta_calculator.calculate_delta(
                old_metadata.file_path, file_path
            )

            # 创建版本记录
            version = SyncVersion(
                version_id=str(uuid.uuid4()),
                file_id=old_metadata.file_id,
                version_number=old_metadata.version + 1,
                file_path=file_path,
                file_hash=new_hash,
                file_size=os.path.getsize(file_path),
                created_by="local",
                parent_version=f"v{old_metadata.version}",
                delta_info=delta_info
            )

            # 保存版本
            self.db.add_version(version)

            # 更新文件元数据
            old_metadata.version = version.version_number
            old_metadata.file_hash = new_hash
            old_metadata.modified_at = datetime.now()
            self.db.update_file_metadata(old_metadata)

        except Exception as e:
            self.logger.error(f"Failed to create new version: {e}")

    def _create_file_metadata(self, file_path: str) -> FileMetadata:
        """创建文件元数据"""
        stat = os.stat(file_path)
        file_hash = self._calculate_file_hash(file_path)

        return FileMetadata(
            file_id=str(uuid.uuid4()),
            filename=os.path.basename(file_path),
            file_path=file_path,
            file_size=stat.st_size,
            file_hash=file_hash,
            mime_type=self._get_mime_type(file_path),
            created_at=datetime.fromtimestamp(stat.st_ctime),
            modified_at=datetime.fromtimestamp(stat.st_mtime)
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

    async def _download_remote_file(self, remote_metadata: FileMetadata, local_path: str):
        """下载远程文件"""
        try:
            operation_id = self.cloud_manager.download_file(
                remote_metadata.file_path, local_path
            )
            if operation_id:
                self.logger.info(f"Queued download for {remote_metadata.file_path}")
        except Exception as e:
            self.logger.error(f"Failed to download remote file: {e}")

    def perform_full_sync(self):
        """执行完整同步"""
        try:
            # 同步本地文件到远程
            if self.sync_mode in [SyncMode.BIDIRECTIONAL, SyncMode.UPLOAD_ONLY]:
                self._sync_local_to_remote()

            # 同步远程文件到本地
            if self.sync_mode in [SyncMode.BIDIRECTIONAL, SyncMode.DOWNLOAD_ONLY]:
                self._sync_remote_to_local()

        except Exception as e:
            self.logger.error(f"Full sync failed: {e}")

    def _sync_local_to_remote(self):
        """同步本地文件到远程"""
        try:
            for root, dirs, files in os.walk(self.sync_root):
                for file in files:
                    file_path = os.path.join(root, file)
                    self.queue_file_sync(file_path)
        except Exception as e:
            self.logger.error(f"Failed to sync local to remote: {e}")

    def _sync_remote_to_local(self):
        """同步远程文件到本地"""
        try:
            backend = self.cloud_manager.backends.get(self.cloud_manager.primary_backend)
            if backend:
                remote_files = asyncio.run(backend.list_files())
                for remote_file in remote_files:
                    local_path = os.path.join(self.sync_root, remote_file.file_path)
                    if not os.path.exists(local_path):
                        self.cloud_manager.download_file(
                            remote_file.file_path, local_path
                        )
        except Exception as e:
            self.logger.error(f"Failed to sync remote to local: {e}")

    def _delete_file(self, file_path: str):
        """删除文件"""
        try:
            metadata = self.db.get_file_by_local_path(file_path)
            if metadata:
                # 删除远程文件
                self.cloud_manager.delete_file(metadata.file_path)
                # 从数据库删除
                # 注意：这里可能需要更复杂的逻辑来处理删除
        except Exception as e:
            self.logger.error(f"Failed to delete file {file_path}: {e}")

    def _move_file(self, from_path: str, to_path: str):
        """移动文件"""
        try:
            # 获取旧文件元数据
            old_metadata = self.db.get_file_by_local_path(from_path)
            if old_metadata:
                # 更新元数据
                old_metadata.file_path = to_path
                old_metadata.filename = os.path.basename(to_path)
                self.db.update_file_metadata(old_metadata)

                # 在远程存储中移动文件
                # 这里需要具体的实现

        except Exception as e:
            self.logger.error(f"Failed to move file from {from_path} to {to_path}: {e}")

    def get_sync_status(self, file_path: str) -> Optional[SyncStatus]:
        """获取文件同步状态"""
        metadata = self.db.get_file_by_local_path(file_path)
        return metadata.sync_status if metadata else None

    def get_file_versions(self, file_path: str) -> List[SyncVersion]:
        """获取文件版本历史"""
        metadata = self.db.get_file_by_local_path(file_path)
        if metadata:
            return self.db.get_file_versions(metadata.file_id)
        return []

    def get_conflicts(self) -> List[SyncConflict]:
        """获取所有冲突"""
        return self.db.get_conflicts()

    def resolve_conflict(self, conflict_id: str, resolution: ConflictResolution) -> bool:
        """解决冲突"""
        return self.db.resolve_conflict(conflict_id, resolution)

    def set_sync_mode(self, mode: SyncMode):
        """设置同步模式"""
        self.sync_mode = mode

    def set_conflict_resolution(self, resolution: ConflictResolution):
        """设置冲突解决策略"""
        self.conflict_resolution = resolution

    def cleanup(self):
        """清理资源"""
        self.file_watcher.stop()
        self.executor.shutdown(wait=True)

    def get_sync_statistics(self) -> Dict[str, Any]:
        """获取同步统计信息"""
        try:
            stats = {
                'total_files': 0,
                'synced_files': 0,
                'pending_files': 0,
                'failed_files': 0,
                'conflicts': len(self.get_conflicts()),
                'last_sync': None
            }

            # 这里需要从数据库获取统计信息
            # 简化实现

            return stats
        except Exception as e:
            self.logger.error(f"Failed to get sync statistics: {e}")
            return {}