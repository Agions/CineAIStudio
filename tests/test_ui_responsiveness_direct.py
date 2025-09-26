#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
直接测试UI响应性组件
避免导入有问题的组件
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_enhanced_interactions_direct():
    """直接测试增强交互组件"""
    print("测试增强交互组件...")

    from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout
    from PyQt6.QtCore import QTimer, Qt

    # 直接导入增强交互组件文件
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app', 'ui', 'components'))

    # 导入单个组件
    from enhanced_interactions import EnhancedButton, LoadingIndicator

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # 创建测试窗口
    window = QWidget()
    layout = QVBoxLayout(window)

    # 测试增强按钮
    button = EnhancedButton("测试按钮")
    button.set_active(True)
    layout.addWidget(button)

    # 测试加载指示器
    indicator = LoadingIndicator(window)
    indicator.set_message("加载中...")
    layout.addWidget(indicator)

    window.show()

    # 测试组件功能
    print(f"按钮激活状态: {button.is_active()}")
    print(f"指示器消息: {indicator.message}")

    # 短暂显示
    QTimer.singleShot(1000, window.close)

    # 运行应用
    app.exec()

    print("✓ 增强交互组件测试通过")
    return True

def test_async_processor_direct():
    """直接测试异步处理器"""
    print("测试异步处理器...")

    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer

    # 直接导入异步处理器
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app', 'services'))
    from async_ai_processor import AsyncAIProcessor

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # 创建处理器
    processor = AsyncAIProcessor()

    # 测试创建操作
    operation_id = processor.generate_text("测试提示词", "default")
    print(f"创建操作ID: {operation_id}")

    # 等待操作完成
    def check_status():
        status = processor.get_operation_status(operation_id)
        print(f"操作状态: {status}")
        if status and status.value in ["completed", "failed"]:
            processor.shutdown()
            app.quit()
        else:
            QTimer.singleShot(100, check_status)

    QTimer.singleShot(100, check_status)

    # 运行应用
    app.exec()

    print("✓ 异步处理器测试通过")
    return True

def test_main_window_integration():
    """测试主窗口集成"""
    print("测试主窗口集成...")

    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer

    # 导入主窗口
    from app.ui.main.main_window import MainWindow
    from app.core.application import Application

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # 创建应用和主窗口
    application = Application()
    main_window = MainWindow(application)

    main_window.show()

    # 测试增强功能
    print("测试显示加载...")
    main_window.show_loading("正在测试...")

    # 测试Toast通知
    QTimer.singleShot(500, lambda: main_window.show_toast("info", "测试消息"))

    # 测试进度条
    QTimer.singleShot(1000, lambda: main_window.show_progress("测试进度", "处理中...", 100))

    # 更新进度
    def update_progress(value=0):
        if value <= 100:
            main_window.update_progress(value, f"进度: {value}%")
            QTimer.singleShot(50, lambda: update_progress(value + 10))
        else:
            main_window.hide_progress()
            main_window.hide_loading()
            QTimer.singleShot(500, app.quit)

    QTimer.singleShot(1500, update_progress)

    # 运行应用
    app.exec()

    print("✓ 主窗口集成测试通过")
    return True

def main():
    """主测试函数"""
    print("CineAIStudio UI响应性直接测试")
    print("=" * 50)

    tests = [
        ("增强交互组件", test_enhanced_interactions_direct),
        ("异步处理器", test_async_processor_direct),
        ("主窗口集成", test_main_window_integration)
    ]

    for test_name, test_func in tests:
        print(f"\n测试: {test_name}")
        try:
            if test_func():
                print(f"✓ {test_name} 测试通过")
            else:
                print(f"✗ {test_name} 测试失败")
        except Exception as e:
            print(f"✗ {test_name} 测试异常: {e}")
            import traceback
            traceback.print_exc()

    print("\n测试完成！")

if __name__ == "__main__":
    main()