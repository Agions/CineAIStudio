#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClipFlowCut 主程序入口
专业的AI视频编辑器
"""

import sys
import os
import traceback
from pathlib import Path

# Force imports to help PyInstaller
try:
    from PyQt6 import sip
    from PyQt6.QtWidgets import QApplication
except ImportError:
    sip = None
    QApplication = None

# Explicitly import cryptography to ensure it's bundled
try:
    import cryptography
    import cryptography.fernet
    import cryptography.hazmat
    import cryptography.hazmat.primitives
    import cryptography.hazmat.backends
except ImportError:
    pass

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入核心模块
from app.core.application import Application
from app.config.config import AppConfig, ThemeConfig, WindowConfig, EditorConfig, PerformanceConfig, AIConfig
from app.ui.main.main_window import MainWindow
from app.core.logger import Logger, LogLevel, LogFormat
from app.utils.error_handler import setup_global_exception_handler


def create_application_config() -> AppConfig:
    """创建应用程序配置"""
    return AppConfig(
        version="2.0.0",
        language="zh-CN",
        theme=ThemeConfig(),
        window=WindowConfig(),
        editor=EditorConfig(),
        performance=PerformanceConfig(),
        ai=AIConfig(),
        recent_files=[],
        custom_settings={}
    )


def setup_logging() -> Logger:
    """设置日志系统"""
    from app.core.logger import setup_logging

    # 设置全局日志配置
    setup_logging(
        level=LogLevel.INFO,
        format_type=LogFormat.DETAILED,
        enable_console=True,
        enable_file=True
    )

    # 获取主日志记录器
    return Logger("ClipFlow")


def main() -> int:
    """主程序入口函数"""
    try:
        print("🎬 启动 ClipFlow...")

        # 创建QApplication实例 - 必须在任何Qt组件之前创建
        qt_app = QApplication(sys.argv)
        qt_app.setApplicationName("ClipFlow")
        qt_app.setApplicationVersion("2.0.0")
        qt_app.setOrganizationName("Agions")
        qt_app.setStyle("Fusion")

        # 设置日志系统
        logger = setup_logging()
        logger.info("=== ClipFlow 启动 ===")

        # 设置全局异常处理
        error_handler = setup_global_exception_handler(logger)

        # 创建应用程序配置
        config = create_application_config()
        logger.info(f"应用程序配置: ClipFlow v{config.version}")

        # 创建应用程序核心
        application = Application(config)

        # 连接错误信号以获取详细错误信息
        def on_error(code, msg):
            import traceback
            logger.error(f"应用程序初始化失败: {code} - {msg}")
            traceback.print_stack()

        application.error_occurred.connect(on_error)

        # 初始化应用程序
        if not application.initialize(sys.argv):
            logger.error("应用程序初始化失败")
            return 1

        logger.info("应用程序初始化完成")

        # 创建主窗口
        main_window = MainWindow(application)
        logger.info("主窗口创建完成")

        # 启动应用程序
        if not application.start():
            logger.error("应用程序启动失败")
            return 1

        logger.info("应用程序启动完成")

        # 显示主窗口
        main_window.show()

        # 运行应用程序
        exit_code = qt_app.exec()

        logger.info(f"应用程序退出，退出码: {exit_code}")
        return exit_code

    except KeyboardInterrupt:
        print("\n用户中断程序")
        return 0

    except Exception as e:
        print(f"程序启动失败: {e}")
        traceback.print_exc()
        return 1

    finally:
        print("👋 ClipFlow 已退出")


def show_splash_screen():
    """显示启动画面"""
    try:
        from PyQt6.QtWidgets import QApplication, QSplashScreen
        from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont
        from PyQt6.QtCore import Qt, QTimer

        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)

        # 创建启动画面
        splash = QSplashScreen()
        splash.setFixedSize(600, 400)

        # 创建启动画面内容
        pixmap = QPixmap(600, 400)
        pixmap.fill(QColor("#1a1a1a"))

        painter = QPainter(pixmap)
        painter.setPen(QColor("#00BCD4"))

        # 绘制Logo
        logo_font = QFont("Arial", 48, QFont.Weight.Bold)
        painter.setFont(logo_font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "ClipFlow")

        # 绘制版本信息
        version_font = QFont("Arial", 14)
        painter.setFont(version_font)
        painter.setPen(QColor("#B0BEC5"))
        version_rect = pixmap.rect().adjusted(0, 50, 0, -50)
        painter.drawText(version_rect, Qt.AlignmentFlag.AlignCenter, "专业AI视频编辑器 v2.0.0")

        # 绘制加载信息
        loading_font = QFont("Arial", 12)
        painter.setFont(loading_font)
        painter.setPen(QColor("#90A4AE"))
        loading_rect = pixmap.rect().adjusted(0, 100, 0, -100)
        painter.drawText(loading_rect, Qt.AlignmentFlag.AlignCenter, "正在加载组件...")

        painter.end()

        splash.setPixmap(pixmap)
        splash.show()

        # 确保启动画面显示
        app.processEvents()

        return splash

    except Exception as e:
        print(f"创建启动画面失败: {e}")
        return None


def run_with_splash():
    """带启动画面的运行方式"""
    splash = show_splash_screen()

    try:
        # 运行主程序
        exit_code = main()

        # 关闭启动画面
        if splash:
            try:
                if sip and hasattr(sip, 'isdeleted') and not sip.isdeleted(splash):
                    splash.finish(None)
                else:
                    splash.finish(None)
            except:
                pass  # 忽略启动画面关闭错误

        return exit_code

    except Exception as e:
        print(f"程序运行失败: {e}")
        traceback.print_exc()

        try:
            if splash:
                if sip and hasattr(sip, 'isdeleted') and not sip.isdeleted(splash):
                    splash.finish(None)
                else:
                    splash.finish(None)
        except:
            pass  # 忽略启动画面关闭错误

        return 1


if __name__ == "__main__":
    # 运行程序
    exit_code = run_with_splash()
    sys.exit(exit_code)