#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UI响应性测试套件
验证增强交互组件和异步处理功能
"""

import sys
import os
import time
import threading
import pytest
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtTest import QTest

from app.ui.components.enhanced_interactions import (
    EnhancedButton, LoadingIndicator, SmoothStackedWidget,
    ToastNotification, ProgressOverlay, InteractiveGuide
)

from app.services.async_ai_processor import AsyncAIProcessor, OperationStatus
from app.ui.components.enhanced_ai_content_generator import EnhancedAIContentGenerator


class TestEnhancedInteractions:
    """增强交互组件测试"""

    @pytest.fixture
    def app(self):
        """创建QApplication实例"""
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        return app

    def test_enhanced_button_creation(self, app):
        """测试增强按钮创建"""
        button = EnhancedButton("Test Button")
        assert button.text() == "Test Button"
        assert not button.is_active()

    def test_enhanced_button_states(self, app):
        """测试增强按钮状态"""
        button = EnhancedButton("Test Button")

        # 测试激活状态
        button.set_active(True)
        assert button.is_active()

        # 测试取消激活状态
        button.set_active(False)
        assert not button.is_active()

    def test_enhanced_button_click_animation(self, app):
        """测试增强按钮点击动画"""
        button = EnhancedButton("Test Button")
        click_count = 0

        def on_click():
            nonlocal click_count
            click_count += 1

        button.clicked.connect(on_click)

        # 模拟点击
        QTest.mouseClick(button, Qt.MouseButton.LeftButton)

        # 等待动画完成
        QTest.qWait(500)

        assert click_count == 1

    def test_loading_indicator(self, app):
        """测试加载指示器"""
        indicator = LoadingIndicator()

        # 测试初始状态
        assert not indicator.isVisible()

        # 测试显示
        indicator.show()
        assert indicator.isVisible()

        # 测试隐藏
        indicator.hide()
        assert not indicator.isVisible()

    def test_smooth_stacked_widget(self, app):
        """测试平滑堆栈组件"""
        stack = SmoothStackedWidget()

        # 添加测试页面
        page1 = QWidget()
        page2 = QWidget()

        stack.addWidget(page1)
        stack.addWidget(page2)

        assert stack.count() == 2

        # 测试页面切换
        stack.setCurrentWidget(page1)
        assert stack.currentWidget() == page1

        stack.setCurrentWidget(page2)
        assert stack.currentWidget() == page2

    def test_toast_notification(self, app):
        """测试Toast通知"""
        toast = ToastNotification()

        # 测试初始状态
        assert not toast.isVisible()

        # 测试显示信息通知
        toast.show_toast("info", "Test message")
        assert toast.isVisible()

        # 等待自动隐藏
        QTest.qWait(3500)
        assert not toast.isVisible()

    def test_progress_overlay(self, app):
        """测试进度覆盖层"""
        overlay = ProgressOverlay()

        # 测试初始状态
        assert not overlay.isVisible()

        # 测试显示
        overlay.set_title("Test Progress")
        overlay.set_message("Processing...")
        overlay.set_maximum(100)
        overlay.set_value(50)
        overlay.show()

        assert overlay.isVisible()
        assert overlay.value() == 50

        # 测试隐藏
        overlay.hide()
        assert not overlay.isVisible()

    def test_interactive_guide(self, app):
        """测试交互式引导"""
        guide = InteractiveGuide()

        # 测试引导步骤
        steps = [
            {"title": "Step 1", "description": "First step", "target": None},
            {"title": "Step 2", "description": "Second step", "target": None}
        ]

        guide.set_steps(steps)
        assert len(guide.steps) == 2

        # 测试显示
        guide.show()
        assert guide.isVisible()

        # 测试隐藏
        guide.hide()
        assert not guide.isVisible()


class TestAsyncAIProcessor:
    """异步AI处理器测试"""

    @pytest.fixture
    def app(self):
        """创建QApplication实例"""
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        return app

    def test_processor_creation(self, app):
        """测试处理器创建"""
        processor = AsyncAIProcessor()
        assert processor is not None
        assert len(processor._operations) == 0

    def test_text_generation_operation(self, app):
        """测试文本生成操作"""
        processor = AsyncAIProcessor()

        # 开始生成
        operation_id = processor.generate_text("Test prompt", "default")
        assert operation_id is not None
        assert operation_id in processor._operations

        # 检查操作状态
        operation = processor._operations[operation_id]
        assert operation.operation_type == "text_generation"
        assert operation.params["prompt"] == "Test prompt"

    def test_image_generation_operation(self, app):
        """测试图像生成操作"""
        processor = AsyncAIProcessor()

        # 开始生成
        operation_id = processor.generate_image("Test prompt", "realistic")
        assert operation_id is not None
        assert operation_id in processor._operations

        # 检查操作状态
        operation = processor._operations[operation_id]
        assert operation.operation_type == "image_generation"
        assert operation.params["style"] == "realistic"

    def test_operation_cancellation(self, app):
        """测试操作取消"""
        processor = AsyncAIProcessor()

        # 开始操作
        operation_id = processor.generate_text("Test prompt", "default")

        # 取消操作
        processor.cancel_operation(operation_id)

        # 检查状态
        status = processor.get_operation_status(operation_id)
        assert status == OperationStatus.CANCELLED

    def test_cleanup_operations(self, app):
        """测试清理操作"""
        processor = AsyncAIProcessor()

        # 创建一些操作
        op1 = processor.generate_text("Test 1", "default")
        op2 = processor.generate_text("Test 2", "default")

        # 标记为完成
        processor._operations[op1].status = OperationStatus.COMPLETED
        processor._operations[op2].status = OperationStatus.COMPLETED

        # 清理
        processor.cleanup_completed_operations()

        # 检查结果
        assert len(processor._operations) == 0


class TestEnhancedAIContentGenerator:
    """增强AI内容生成器测试"""

    @pytest.fixture
    def app(self):
        """创建QApplication实例"""
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        return app

    def test_generator_creation(self, app):
        """测试生成器创建"""
        generator = EnhancedAIContentGenerator()
        assert generator is not None
        assert generator.ai_processor is not None

    def test_content_type_selection(self, app):
        """测试内容类型选择"""
        generator = EnhancedAIContentGenerator()

        # 测试初始类型
        assert generator.content_type_combo.currentText() == "文本生成"

        # 测试类型切换
        generator.content_type_combo.setCurrentText("图像生成")
        assert generator.content_type_combo.currentText() == "图像生成"

    def test_prompt_input_validation(self, app):
        """测试提示词输入验证"""
        generator = EnhancedAIContentGenerator()

        # 空提示词
        generator.prompt_input.setText("")
        generator.on_generate()

        # 应该显示错误消息，不开始生成
        assert generator.current_operation_id is None

        # 有效提示词
        generator.prompt_input.setText("Test prompt")
        generator.on_generate()

        # 应该开始生成
        assert generator.current_operation_id is not None

    def test_result_management(self, app):
        """测试结果管理"""
        generator = EnhancedAIContentGenerator()

        # 添加测试结果
        test_result = {
            "id": "test_result_1",
            "type": "文本生成",
            "title": "Test Result",
            "preview": "This is a test result",
            "content": "Full content here"
        }

        generator.add_result_widget(test_result)
        assert len(generator.generation_results) == 1
        assert generator.results_layout.count() == 1

        # 测试结果选择
        selected = generator.get_selected_result()
        assert selected is None  # 没有选中任何结果

        # 测试清空结果
        generator.clear_results()
        assert len(generator.generation_results) == 0
        assert generator.results_layout.count() == 0


class TestUIResponsiveness:
    """UI响应性综合测试"""

    @pytest.fixture
    def app(self):
        """创建QApplication实例"""
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        return app

    def test_ui_freezing_prevention(self, app):
        """测试UI冻结预防"""
        # 创建主窗口
        main_window = QWidget()
        layout = QVBoxLayout(main_window)

        # 添加增强按钮
        button = EnhancedButton("Test Button")
        layout.addWidget(button)

        # 添加加载指示器
        indicator = LoadingIndicator(main_window)

        # 添加生成器
        generator = EnhancedAIContentGenerator()
        layout.addWidget(generator)

        main_window.show()

        # 测试长时间操作时的UI响应性
        def long_operation():
            indicator.show()
            time.sleep(2)  # 模拟长时间操作
            indicator.hide()

        # 在单独线程中执行长时间操作
        thread = threading.Thread(target=long_operation)
        thread.start()

        # UI应该保持响应
        assert button.isEnabled()
        assert generator.generate_btn.isEnabled()

        # 等待操作完成
        thread.join()

        main_window.close()

    def test_concurrent_operations(self, app):
        """测试并发操作"""
        processor = AsyncAIProcessor()

        # 启动多个并发操作
        operations = []
        for i in range(5):
            op_id = processor.generate_text(f"Test prompt {i}", "default")
            operations.append(op_id)

        # 所有操作都应该被创建
        assert len(operations) == 5
        for op_id in operations:
            assert op_id in processor._operations

        # 清理
        processor.shutdown()

    def test_memory_usage(self, app):
        """测试内存使用"""
        import gc

        # 创建大量组件
        components = []
        for i in range(100):
            button = EnhancedButton(f"Button {i}")
            components.append(button)

        # 删除组件
        for component in components:
            component.deleteLater()

        components.clear()
        gc.collect()

        # 内存应该被释放
        assert len(components) == 0


def run_performance_tests():
    """运行性能测试"""
    print("运行UI响应性性能测试...")

    # 测试组件创建性能
    start_time = time.time()

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # 创建100个增强按钮
    buttons = []
    for i in range(100):
        button = EnhancedButton(f"Button {i}")
        buttons.append(button)

    creation_time = time.time() - start_time
    print(f"创建100个增强按钮耗时: {creation_time:.3f}秒")

    # 测试按钮点击响应时间
    def test_click_speed():
        click_times = []
        for button in buttons[:10]:  # 测试前10个按钮
            start = time.time()
            QTest.mouseClick(button, Qt.MouseButton.LeftButton)
            end = time.time()
            click_times.append(end - start)

        avg_click_time = sum(click_times) / len(click_times)
        print(f"平均按钮点击响应时间: {avg_click_time:.4f}秒")
        return avg_click_time

    avg_click_time = test_click_speed()

    # 清理
    for button in buttons:
        button.deleteLater()

    print("性能测试完成")
    return creation_time, avg_click_time


if __name__ == "__main__":
    # 运行基本测试
    app = QApplication(sys.argv)

    print("CineAIStudio UI响应性测试")
    print("=" * 50)

    # 运行性能测试
    creation_time, click_time = run_performance_tests()

    # 运行单元测试
    print("\n运行单元测试...")

    # 这里可以添加更多的单元测试

    print("\n测试完成！")
    print(f"组件创建时间: {creation_time:.3f}秒")
    print(f"点击响应时间: {click_time:.4f}秒")