#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClipFlow 日志记录器模块
提供日志记录和管理功能
"""

import logging
import sys
from typing import Optional
from enum import Enum


class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LogFormat(Enum):
    """日志格式枚举"""
    SIMPLE = "simple"
    DETAILED = "detailed"
    STRUCTURED = "structured"


class Logger:
    """简化日志记录器"""

    def __init__(self, name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    @classmethod
    def get_logger(cls, name: str) -> 'Logger':
        """获取日志记录器实例"""
        return cls(name)

    def debug(self, message: str) -> None:
        """调试日志"""
        self.logger.debug(message)

    def info(self, message: str) -> None:
        """信息日志"""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """警告日志"""
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """错误日志"""
        self.logger.error(message)

    def critical(self, message: str) -> None:
        """严重错误日志"""
        self.logger.critical(message)


def setup_logging(
    level: LogLevel = LogLevel.INFO,
    format_type: LogFormat = LogFormat.DETAILED,
    enable_console: bool = True,
    enable_file: bool = True
) -> None:
    """设置全局日志配置"""
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(level.value)

    # 清除现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 创建格式化器
    if format_type == LogFormat.SIMPLE:
        formatter = logging.Formatter('%(levelname)s - %(message)s')
    elif format_type == LogFormat.DETAILED:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    else:  # STRUCTURED
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )

    # 控制台处理器
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # 文件处理器
    if enable_file:
        try:
            from pathlib import Path
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)

            file_handler = logging.FileHandler(
                log_dir / "ClipFlow.log",
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            print(f"无法创建日志文件: {e}")


def get_logger(name: str) -> Logger:
    """获取日志记录器实例"""
    return Logger(name)