#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio v2.0 文件操作错误处理模块
专门处理文件系统相关的错误，提供自动恢复和用户友好的错误消息
"""

import os
import shutil
from enum import Enum
import json
import zipfile
import tempfile
import time
from typing import Optional, Dict, Any, List, Union, Callable
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from contextlib import contextmanager
from .error_handler import (
    ErrorHandler, ErrorInfo, ErrorType, ErrorSeverity,
    RecoveryAction, ErrorContext, error_context
)


@dataclass
class FileOperationResult:
    """文件操作结果"""
    success: bool
    file_path: Optional[str] = None
    backup_path: Optional[str] = None
    error_message: Optional[str] = None
    recovery_action: Optional[RecoveryAction] = None


class FileOperationType(Enum):
    """文件操作类型"""
    READ = "read"
    WRITE = "write"
    CREATE = "create"
    DELETE = "delete"
    COPY = "copy"
    MOVE = "move"
    RENAME = "rename"
    COMPRESS = "compress"
    DECOMPRESS = "decompress"


class FileOperationError(Exception):
    """文件操作错误"""
    def __init__(self, message: str, operation: str = None, file_path: str = None):
        super().__init__(message)
        self.operation = operation
        self.file_path = file_path


class FileErrorHandler(ErrorHandler):
    """文件操作错误处理器"""

    def __init__(self, logger=None, backup_dir: Optional[str] = None):
        """初始化文件错误处理器"""
        super().__init__(logger)
        self.backup_dir = backup_dir or os.path.expanduser("~/CineAIStudio/Backups")
        self.temp_dir = os.path.expanduser("~/CineAIStudio/Temp")
        self.max_retries = 3
        self.retry_delay = 1  # 秒

        # 确保目录存在
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)

    @contextmanager
    def safe_file_operation(
        self,
        file_path: str,
        operation: FileOperationType,
        create_backup: bool = True,
        component: str = "FileOperation"
    ):
        """安全的文件操作上下文管理器"""
        backup_path = None

        try:
            # 如果需要，创建备份
            if create_backup and operation in [FileOperationType.WRITE, FileOperationType.DELETE]:
                backup_path = self._create_backup(file_path, operation)

            yield FileOperationResult(
                success=True,
                file_path=file_path,
                backup_path=backup_path
            )

        except PermissionError as e:
            error_info = ErrorInfo(
                error_type=ErrorType.PERMISSION,
                severity=ErrorSeverity.HIGH,
                message=f"文件权限错误: {file_path} - {str(e)}",
                exception=e,
                context=ErrorContext(
                    component=component,
                    operation=operation.value,
                    system_state={"file_path": file_path, "operation": operation.value}
                ),
                recovery_action=RecoveryAction.CONTACT_SUPPORT,
                user_message=f"无法访问文件 {file_path}，请检查文件权限"
            )
            self.handle_error(error_info)
            raise

        except FileNotFoundError as e:
            error_info = ErrorInfo(
                error_type=ErrorType.FILE,
                severity=ErrorSeverity.MEDIUM,
                message=f"文件不存在: {file_path}",
                exception=e,
                context=ErrorContext(
                    component=component,
                    operation=operation.value,
                    system_state={"file_path": file_path, "operation": operation.value}
                ),
                recovery_action=RecoveryAction.SKIP,
                user_message=f"文件 {file_path} 不存在"
            )
            self.handle_error(error_info)
            raise

        except OSError as e:
            error_info = ErrorInfo(
                error_type=ErrorType.FILE,
                severity=ErrorSeverity.HIGH,
                message=f"文件系统错误: {file_path} - {str(e)}",
                exception=e,
                context=ErrorContext(
                    component=component,
                    operation=operation.value,
                    system_state={"file_path": file_path, "operation": operation.value}
                ),
                recovery_action=RecoveryAction.RETRY,
                user_message=f"文件操作失败: {str(e)}"
            )
            self.handle_error(error_info)

            # 尝试恢复
            if backup_path and os.path.exists(backup_path):
                if self._restore_from_backup(backup_path, file_path):
                    error_info.recovery_action = RecoveryAction.RETRY
                    self.logger.info(f"已从备份恢复文件: {file_path}")

            raise

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.FILE,
                severity=ErrorSeverity.CRITICAL,
                message=f"未知文件错误: {file_path} - {str(e)}",
                exception=e,
                context=ErrorContext(
                    component=component,
                    operation=operation.value,
                    system_state={"file_path": file_path, "operation": operation.value}
                ),
                recovery_action=RecoveryAction.CONTACT_SUPPORT,
                user_message=f"文件操作遇到未知错误: {str(e)}"
            )
            self.handle_error(error_info)
            raise

    def safe_read_file(
        self,
        file_path: str,
        encoding: str = 'utf-8',
        component: str = "FileRead",
        retries: int = None
    ) -> Optional[str]:
        """安全读取文件"""
        retries = retries or self.max_retries

        for attempt in range(retries):
            try:
                with self.safe_file_operation(file_path, FileOperationType.READ, component=component):
                    with open(file_path, 'r', encoding=encoding) as f:
                        return f.read()

            except Exception as e:
                if attempt == retries - 1:
                    raise

                self.logger.warning(f"文件读取失败，重试 {attempt + 1}/{retries}: {file_path}")
                time.sleep(self.retry_delay * (attempt + 1))

        return None

    def safe_write_file(
        self,
        file_path: str,
        content: str,
        encoding: str = 'utf-8',
        component: str = "FileWrite",
        create_backup: bool = True,
        retries: int = None
    ) -> FileOperationResult:
        """安全写入文件"""
        retries = retries or self.max_retries

        for attempt in range(retries):
            try:
                with self.safe_file_operation(
                    file_path,
                    FileOperationType.WRITE,
                    create_backup=create_backup,
                    component=component
                ) as result:
                    # 确保目录存在
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)

                    # 写入临时文件
                    temp_path = f"{file_path}.tmp"
                    with open(temp_path, 'w', encoding=encoding) as f:
                        f.write(content)

                    # 重命名为目标文件
                    if os.path.exists(file_path):
                        os.replace(temp_path, file_path)
                    else:
                        shutil.move(temp_path, file_path)

                    result.success = True
                    result.file_path = file_path
                    return result

            except Exception as e:
                if attempt == retries - 1:
                    error_info = ErrorInfo(
                        error_type=ErrorType.FILE,
                        severity=ErrorSeverity.HIGH,
                        message=f"文件写入失败: {file_path} - {str(e)}",
                        exception=e,
                        context=ErrorContext(
                            component=component,
                            operation="write_file",
                            system_state={"file_path": file_path, "attempts": attempt + 1}
                        ),
                        recovery_action=RecoveryAction.RETRY,
                        user_message=f"无法写入文件 {file_path}"
                    )
                    self.handle_error(error_info)
                    return FileOperationResult(
                        success=False,
                        file_path=file_path,
                        error_message=str(e),
                        recovery_action=RecoveryAction.RETRY
                    )

                self.logger.warning(f"文件写入失败，重试 {attempt + 1}/{retries}: {file_path}")
                time.sleep(self.retry_delay * (attempt + 1))

        return FileOperationResult(success=False, error_message="Max retries exceeded")

    def safe_copy_file(
        self,
        src_path: str,
        dst_path: str,
        component: str = "FileCopy"
    ) -> FileOperationResult:
        """安全复制文件"""
        try:
            with self.safe_file_operation(src_path, FileOperationType.READ, component=component):
                with self.safe_file_operation(dst_path, FileOperationType.WRITE, component=component):
                    # 确保目标目录存在
                    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                    shutil.copy2(src_path, dst_path)

                    return FileOperationResult(
                        success=True,
                        file_path=dst_path
                    )

        except Exception as e:
            return FileOperationResult(
                success=False,
                file_path=dst_path,
                error_message=str(e)
            )

    def safe_delete_file(
        self,
        file_path: str,
        component: str = "FileDelete"
    ) -> FileOperationResult:
        """安全删除文件"""
        try:
            with self.safe_file_operation(file_path, FileOperationType.DELETE, component=component):
                if os.path.exists(file_path):
                    # 先移动到临时目录，再删除
                    temp_path = os.path.join(self.temp_dir, f"delete_{int(time.time())}_{os.path.basename(file_path)}")
                    shutil.move(file_path, temp_path)
                    os.remove(temp_path)

                return FileOperationResult(
                    success=True,
                    file_path=file_path
                )

        except Exception as e:
            return FileOperationResult(
                success=False,
                file_path=file_path,
                error_message=str(e)
            )

    def safe_json_load(
        self,
        file_path: str,
        component: str = "JSONLoad"
    ) -> Optional[Dict[str, Any]]:
        """安全加载JSON文件"""
        try:
            content = self.safe_read_file(file_path, component=component)
            if content:
                return json.loads(content)
        except json.JSONDecodeError as e:
            error_info = ErrorInfo(
                error_type=ErrorType.VALIDATION,
                severity=ErrorSeverity.MEDIUM,
                message=f"JSON解析错误: {file_path} - {str(e)}",
                exception=e,
                context=ErrorContext(
                    component=component,
                    operation="json_load",
                    system_state={"file_path": file_path}
                ),
                recovery_action=RecoveryAction.ROLLBACK,
                user_message=f"文件 {file_path} 格式错误，无法解析"
            )
            self.handle_error(error_info)
        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.FILE,
                severity=ErrorSeverity.HIGH,
                message=f"JSON加载错误: {file_path} - {str(e)}",
                exception=e,
                context=ErrorContext(
                    component=component,
                    operation="json_load",
                    system_state={"file_path": file_path}
                ),
                recovery_action=RecoveryAction.CONTACT_SUPPORT,
                user_message=f"无法加载配置文件 {file_path}"
            )
            self.handle_error(error_info)

        return None

    def safe_json_dump(
        self,
        data: Dict[str, Any],
        file_path: str,
        component: str = "JSONDump",
        indent: int = 2
    ) -> FileOperationResult:
        """安全保存JSON文件"""
        try:
            content = json.dumps(data, indent=indent, ensure_ascii=False)
            return self.safe_write_file(file_path, content, component=component)
        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.FILE,
                severity=ErrorSeverity.HIGH,
                message=f"JSON保存错误: {file_path} - {str(e)}",
                exception=e,
                context=ErrorContext(
                    component=component,
                    operation="json_dump",
                    system_state={"file_path": file_path}
                ),
                recovery_action=RecoveryAction.CONTACT_SUPPORT,
                user_message=f"无法保存配置文件 {file_path}"
            )
            self.handle_error(error_info)
            return FileOperationResult(success=False, error_message=str(e))

    def safe_zip_create(
        self,
        zip_path: str,
        files_to_add: List[str],
        component: str = "ZipCreate"
    ) -> FileOperationResult:
        """安全创建ZIP文件"""
        try:
            with self.safe_file_operation(zip_path, FileOperationType.WRITE, component=component):
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in files_to_add:
                        if os.path.exists(file_path):
                            arcname = os.path.relpath(file_path, os.path.dirname(file_path))
                            zipf.write(file_path, arcname)

                return FileOperationResult(
                    success=True,
                    file_path=zip_path
                )

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.FILE,
                severity=ErrorSeverity.HIGH,
                message=f"ZIP创建错误: {zip_path} - {str(e)}",
                exception=e,
                context=ErrorContext(
                    component=component,
                    operation="zip_create",
                    system_state={"zip_path": zip_path, "file_count": len(files_to_add)}
                ),
                recovery_action=RecoveryAction.RETRY,
                user_message=f"创建压缩文件失败: {str(e)}"
            )
            self.handle_error(error_info)
            return FileOperationResult(success=False, error_message=str(e))

    def safe_zip_extract(
        self,
        zip_path: str,
        extract_dir: str,
        component: str = "ZipExtract"
    ) -> FileOperationResult:
        """安全解压ZIP文件"""
        try:
            with self.safe_file_operation(zip_path, FileOperationType.READ, component=component):
                with self.safe_file_operation(extract_dir, FileOperationType.WRITE, component=component):
                    os.makedirs(extract_dir, exist_ok=True)
                    with zipfile.ZipFile(zip_path, 'r') as zipf:
                        zipf.extractall(extract_dir)

                return FileOperationResult(
                    success=True,
                    file_path=extract_dir
                )

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.FILE,
                severity=ErrorSeverity.HIGH,
                message=f"ZIP解压错误: {zip_path} - {str(e)}",
                exception=e,
                context=ErrorContext(
                    component=component,
                    operation="zip_extract",
                    system_state={"zip_path": zip_path, "extract_dir": extract_dir}
                ),
                recovery_action=RecoveryAction.RETRY,
                user_message=f"解压文件失败: {str(e)}"
            )
            self.handle_error(error_info)
            return FileOperationResult(success=False, error_message=str(e))

    def _create_backup(self, file_path: str, operation: FileOperationType) -> Optional[str]:
        """创建文件备份"""
        if not os.path.exists(file_path):
            return None

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{os.path.basename(file_path)}_{operation.value}_{timestamp}.backup"
            backup_path = os.path.join(self.backup_dir, backup_name)

            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            shutil.copy2(file_path, backup_path)

            self.logger.info(f"创建文件备份: {file_path} -> {backup_path}")
            return backup_path

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.FILE,
                severity=ErrorSeverity.LOW,
                message=f"备份创建失败: {file_path} - {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="FileErrorHandler",
                    operation="create_backup",
                    system_state={"file_path": file_path, "operation": operation.value}
                ),
                recovery_action=RecoveryAction.NONE,
                user_message=""
            )
            self.handle_error(error_info, show_dialog=False)
            return None

    def _restore_from_backup(self, backup_path: str, target_path: str) -> bool:
        """从备份恢复文件"""
        try:
            if os.path.exists(backup_path):
                # 确保目标目录存在
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                shutil.copy2(backup_path, target_path)
                self.logger.info(f"从备份恢复文件: {backup_path} -> {target_path}")
                return True
        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.FILE,
                severity=ErrorSeverity.MEDIUM,
                message=f"备份恢复失败: {backup_path} -> {target_path} - {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="FileErrorHandler",
                    operation="restore_backup",
                    system_state={"backup_path": backup_path, "target_path": target_path}
                ),
                recovery_action=RecoveryAction.CONTACT_SUPPORT,
                user_message="备份恢复失败"
            )
            self.handle_error(error_info)

        return False

    def cleanup_old_backups(self, days: int = 30) -> None:
        """清理旧备份文件"""
        try:
            cutoff_time = time.time() - (days * 24 * 60 * 60)
            cleaned_count = 0

            for backup_file in os.listdir(self.backup_dir):
                backup_path = os.path.join(self.backup_dir, backup_file)
                if os.path.isfile(backup_path) and os.path.getmtime(backup_path) < cutoff_time:
                    os.remove(backup_path)
                    cleaned_count += 1

            if cleaned_count > 0:
                self.logger.info(f"清理了 {cleaned_count} 个旧备份文件")

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.FILE,
                severity=ErrorSeverity.LOW,
                message=f"备份清理失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="FileErrorHandler",
                    operation="cleanup_backups",
                    system_state={"days": days}
                ),
                recovery_action=RecoveryAction.NONE,
                user_message=""
            )
            self.handle_error(error_info, show_dialog=False)

    def get_backup_info(self) -> Dict[str, Any]:
        """获取备份信息"""
        try:
            backup_files = []
            total_size = 0

            for backup_file in os.listdir(self.backup_dir):
                backup_path = os.path.join(self.backup_dir, backup_file)
                if os.path.isfile(backup_path):
                    stat = os.stat(backup_path)
                    backup_files.append({
                        "filename": backup_file,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                    total_size += stat.st_size

            return {
                "backup_count": len(backup_files),
                "total_size": total_size,
                "backup_dir": self.backup_dir,
                "backups": sorted(backup_files, key=lambda x: x["modified"], reverse=True)
            }

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.FILE,
                severity=ErrorSeverity.LOW,
                message=f"获取备份信息失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="FileErrorHandler",
                    operation="get_backup_info"
                ),
                recovery_action=RecoveryAction.NONE,
                user_message=""
            )
            self.handle_error(error_info, show_dialog=False)
            return {"backup_count": 0, "total_size": 0, "backup_dir": self.backup_dir, "backups": []}


# 全局文件错误处理器实例
_global_file_error_handler: Optional[FileErrorHandler] = None


def get_file_error_handler() -> FileErrorHandler:
    """获取全局文件错误处理器"""
    global _global_file_error_handler
    if _global_file_error_handler is None:
        _global_file_error_handler = FileErrorHandler()
    return _global_file_error_handler


def set_file_error_handler(handler: FileErrorHandler) -> None:
    """设置全局文件错误处理器"""
    global _global_file_error_handler
    _global_file_error_handler = handler