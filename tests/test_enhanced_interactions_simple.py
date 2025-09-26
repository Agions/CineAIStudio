#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化的增强交互组件测试
直接测试增强交互组件而不通过__init__.py导入
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton
from PyQt6.QtCore import QTimer, Qt

# 直接导入增强交互组件
from app.ui.components.enhanced_interactions import EnhancedButton, LoadingIndicator

def test_enhanced_button():
    """测试增强按钮"""
    print("测试增强按钮...")

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # 创建测试窗口
    window = QWidget()
    layout = QVBoxLayout(window)

    # 创建增强按钮
    button = EnhancedButton("测试按钮")
    button.clicked.connect(lambda: print("按钮被点击了！"))
    layout.addWidget(button)

    window.show()

    # 测试按钮状态
    print(f"按钮文本: {button.text()}")
    print(f"按钮是否激活: {button.is_active()}")

    # 测试激活状态
    button.set_active(True)
    print(f"设置激活后: {button.is_active()}")

    # 模拟点击
    button.click()

    # 关闭窗口
    window.close()

    print("✓ 增强按钮测试通过")
    return True

def test_loading_indicator():
    """测试加载指示器"""
    print("测试加载指示器...")

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # 创建测试窗口
    window = QWidget()
    layout = QVBoxLayout(window)

    # 创建加载指示器
    indicator = LoadingIndicator(window)
    layout.addWidget(indicator)

    window.show()

    # 测试显示/隐藏
    print("显示加载指示器...")
    indicator.show()
    indicator.set_message("正在加载...")
    QApplication.processEvents()
    time.sleep(1)

    print("隐藏加载指示器...")
    indicator.hide()
    QApplication.processEvents()

    # 关闭窗口
    window.close()

    print("✓ 加载指示器测试通过")
    return True

def test_async_processor():
    """测试异步处理器"""
    print("测试异步处理器...")

    from app.services.async_ai_processor import AsyncAIProcessor

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # 创建异步处理器
    processor = AsyncAIProcessor()

    # 测试文本生成
    operation_id = processor.generate_text("测试提示词", "default")
    print(f"创建操作: {operation_id}")

    # 检查操作状态
    status = processor.get_operation_status(operation_id)
    print(f"操作状态: {status}")

    # 清理
    processor.shutdown()

    print("✓ 异步处理器测试通过")
    return True

def main():
    """主测试函数"""
    print("CineAIStudio 增强交互组件测试")
    print("=" * 40)

    tests = [
        test_enhanced_button,
        test_loading_indicator,
        test_async_processor
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
            print()
        except Exception as e:
            print(f"✗ 测试失败: {e}")
            failed += 1
            print()

    print("=" * 40)
    print(f"测试结果: {passed} 通过, {failed} 失败")

    if failed == 0:
        print("✓ 所有测试通过！")
        return True
    else:
        print("✗ 部分测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)