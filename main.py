#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import atexit
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from app.ui.professional_main_window import ProfessionalMainWindow
from app.ui.global_style_fixer import apply_global_style_fixes


def cleanup():
    """清理资源"""
    # 这里可以添加应用退出时需要执行的清理操作
    print("正在清理资源...")


def setup_app_icon(app):
    """设置应用程序图标"""
    # 尝试不同尺寸的图标
    icon_paths = [
        "resources/icons/app_icon_64.png",
        "resources/icons/app_icon_32.png",
        "resources/icons/app_icon_128.png"
    ]

    for icon_path in icon_paths:
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
            break


def main():
    """主程序入口函数"""
    # 注册退出处理函数
    atexit.register(cleanup)
    
    # 创建应用实例
    app = QApplication(sys.argv)
    app.setApplicationName("VideoEpicCreator")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("Agions")
    
    # 设置应用图标
    setup_app_icon(app)
    
    # 专业UI系统不需要外部CSS文件
    # 所有样式都通过Python代码内联定义，避免CSS兼容性问题
    print("✅ 使用专业UI系统 - 无需外部CSS文件")

    # 应用全局样式修复
    apply_global_style_fixes(app, is_dark=False)
    print("✅ 应用全局样式修复")

    # 创建并显示主窗口
    window = ProfessionalMainWindow()
    window.show()
    
    # 进入事件循环
    exit_code = app.exec()
    
    # 返回退出码
    return exit_code


if __name__ == "__main__":
    sys.exit(main()) 