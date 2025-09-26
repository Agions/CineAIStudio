#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强AI内容生成器组件
集成异步AI操作处理，提供流畅的用户体验
"""

import os
import json
from typing import Optional, Dict, Any, Callable
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QComboBox, QSpinBox, QProgressBar, QGroupBox,
    QFrame, QScrollArea, QSplitter, QTextBrowser, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread, QDateTime
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QBrush, QPen

from .enhanced_interactions import EnhancedButton, LoadingIndicator, ToastNotification
from ...services.async_ai_processor import AsyncAIProcessor, OperationStatus


class GenerationResultWidget(QWidget):
    """生成结果展示组件"""

    result_selected = pyqtSignal(object)  # result data
    result_deleted = pyqtSignal(str)  # result id

    def __init__(self, result_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.result_data = result_data
        self.result_id = result_data.get("id", "")
        self.is_selected = False
        self.setup_ui()

    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # 结果标题
        title = self.result_data.get("title", f"结果 {self.result_id}")
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        # 结果预览
        preview = self.result_data.get("preview", "")
        if preview:
            preview_label = QLabel(preview[:100] + "..." if len(preview) > 100 else preview)
            preview_label.setWordWrap(True)
            preview_label.setStyleSheet("color: #666; font-size: 11px;")
            layout.addWidget(preview_label)

        # 结果类型标签
        result_type = self.result_data.get("type", "unknown")
        type_label = QLabel(result_type.upper())
        type_label.setStyleSheet("""
            QLabel {
                background-color: #2196F3;
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 10px;
                font-weight: bold;
            }
        """)
        layout.addWidget(type_label)

        # 操作按钮
        button_layout = QHBoxLayout()

        self.select_btn = EnhancedButton("选择")
        self.select_btn.setFixedSize(60, 25)
        self.select_btn.clicked.connect(self.on_select)
        button_layout.addWidget(self.select_btn)

        delete_btn = EnhancedButton("删除")
        delete_btn.setFixedSize(60, 25)
        delete_btn.clicked.connect(self.on_delete)
        button_layout.addWidget(delete_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # 设置样式
        self.setStyleSheet("""
            GenerationResultWidget {
                background-color: #f5f5f5;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin: 5px;
            }
            GenerationResultWidget:hover {
                background-color: #eeeeee;
                border-color: #2196F3;
            }
        """)

    def on_select(self):
        """选择结果"""
        self.is_selected = True
        self.result_selected.emit(self.result_data)
        self.update_selection_style()

    def on_delete(self):
        """删除结果"""
        self.result_deleted.emit(self.result_id)

    def update_selection_style(self):
        """更新选择状态样式"""
        if self.is_selected:
            self.setStyleSheet("""
                GenerationResultWidget {
                    background-color: #e3f2fd;
                    border: 2px solid #2196F3;
                    border-radius: 8px;
                    margin: 5px;
                }
            """)
        else:
            self.setStyleSheet("""
                GenerationResultWidget {
                    background-color: #f5f5f5;
                    border: 2px solid #e0e0e0;
                    border-radius: 8px;
                    margin: 5px;
                }
                GenerationResultWidget:hover {
                    background-color: #eeeeee;
                    border-color: #2196F3;
                }
            """)


class EnhancedAIContentGenerator(QWidget):
    """增强AI内容生成器"""

    # 信号定义
    content_generated = pyqtSignal(object)  # 生成的内容数据
    generation_started = pyqtSignal(str)  # 生成开始
    generation_progress = pyqtSignal(str, float)  # 生成进度
    generation_completed = pyqtSignal(str, object)  # 生成完成
    generation_failed = pyqtSignal(str, str)  # 生成失败

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ai_processor = AsyncAIProcessor(self)
        self.current_operation_id = None
        self.generation_results = []
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """设置用户界面"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        # 左侧：控制面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        # 内容类型选择
        type_group = QGroupBox("内容类型")
        type_layout = QVBoxLayout(type_group)

        self.content_type_combo = QComboBox()
        self.content_type_combo.addItems([
            "文本生成", "图像生成", "视频分析", "音频处理", "特效建议"
        ])
        type_layout.addWidget(self.content_type_combo)

        # 模型选择
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("模型:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["默认", "高级", "专业", "快速"])
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        type_layout.addLayout(model_layout)

        left_layout.addWidget(type_group)

        # 参数设置
        params_group = QGroupBox("参数设置")
        params_layout = QVBoxLayout(params_group)

        # 输入提示词
        params_layout.addWidget(QLabel("提示词:"))
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("请输入生成内容的描述...")
        self.prompt_input.setMaximumHeight(100)
        params_layout.addWidget(self.prompt_input)

        # 其他参数
        other_params_layout = QHBoxLayout()

        # 质量设置
        quality_layout = QVBoxLayout()
        quality_layout.addWidget(QLabel("质量:"))
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(80)
        quality_layout.addWidget(self.quality_spin)
        other_params_layout.addLayout(quality_layout)

        # 创意度设置
        creativity_layout = QVBoxLayout()
        creativity_layout.addWidget(QLabel("创意度:"))
        self.creativity_spin = QSpinBox()
        self.creativity_spin.setRange(1, 100)
        self.creativity_spin.setValue(70)
        creativity_layout.addWidget(self.creativity_spin)
        other_params_layout.addLayout(creativity_layout)

        params_layout.addLayout(other_params_layout)
        left_layout.addWidget(params_group)

        # 生成按钮
        self.generate_btn = EnhancedButton("生成内容")
        self.generate_btn.setFixedSize(120, 40)
        self.generate_btn.clicked.connect(self.on_generate)
        left_layout.addWidget(self.generate_btn)

        left_layout.addStretch()

        # 右侧：结果展示
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        right_layout.addWidget(self.progress_bar)

        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #666; font-size: 12px;")
        right_layout.addWidget(self.status_label)

        # 结果展示区域
        results_scroll = QScrollArea()
        results_scroll.setWidgetResizable(True)
        results_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout(self.results_widget)
        self.results_layout.setContentsMargins(10, 10, 10, 10)
        self.results_layout.setSpacing(10)

        results_scroll.setWidget(self.results_widget)
        right_layout.addWidget(results_scroll)

        # 添加到主布局
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 500])
        main_layout.addWidget(splitter)

        # 设置最小宽度
        left_panel.setMinimumWidth(280)
        right_panel.setMinimumWidth(400)

    def setup_connections(self):
        """设置信号连接"""
        # AI处理器信号
        self.ai_processor.operation_started.connect(self.on_operation_started)
        self.ai_processor.operation_progress.connect(self.on_operation_progress)
        self.ai_processor.operation_completed.connect(self.on_operation_completed)
        self.ai_processor.operation_failed.connect(self.on_operation_failed)

        # 内容类型变化
        self.content_type_combo.currentTextChanged.connect(self.on_content_type_changed)

    def on_content_type_changed(self, content_type: str):
        """处理内容类型变化"""
        # 根据不同类型更新界面
        if content_type == "文本生成":
            self.prompt_input.setPlaceholderText("请输入要生成的文本描述...")
        elif content_type == "图像生成":
            self.prompt_input.setPlaceholderText("请输入要生成的图像描述...")
        elif content_type == "视频分析":
            self.prompt_input.setPlaceholderText("请输入视频文件路径或描述...")
        else:
            self.prompt_input.setPlaceholderText("请输入生成内容的描述...")

    def on_generate(self):
        """生成内容"""
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            self.status_label.setText("请输入提示词")
            return

        content_type = self.content_type_combo.currentText()
        model = self.model_combo.currentText()

        # 禁用生成按钮
        self.generate_btn.setEnabled(False)
        self.generate_btn.setText("生成中...")

        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # 根据内容类型调用相应的AI服务
        if content_type == "文本生成":
            self.current_operation_id = self.ai_processor.generate_text(
                prompt=prompt,
                model=model,
                callback=self.on_generation_callback
            )
        elif content_type == "图像生成":
            self.current_operation_id = self.ai_processor.generate_image(
                prompt=prompt,
                style=model,
                callback=self.on_generation_callback
            )
        elif content_type == "视频分析":
            self.current_operation_id = self.ai_processor.analyze_video(
                video_path=prompt,
                callback=self.on_generation_callback
            )

        self.generation_started.emit(self.current_operation_id)

    def on_operation_started(self, operation_id: str, operation_type: str):
        """处理操作开始"""
        self.status_label.setText(f"正在{operation_type}...")

    def on_operation_progress(self, operation_id: str, progress: float, message: str):
        """处理操作进度更新"""
        self.progress_bar.setValue(int(progress))
        self.status_label.setText(message)
        self.generation_progress.emit(operation_id, progress)

    def on_operation_completed(self, operation_id: str, result: Any, error: Optional[str]):
        """处理操作完成"""
        # 隐藏进度条
        self.progress_bar.setVisible(False)

        # 启用生成按钮
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("生成内容")

        if error:
            self.status_label.setText(f"生成失败: {error}")
            self.generation_failed.emit(operation_id, error)
            return

        # 创建结果数据
        result_data = {
            "id": operation_id,
            "type": self.content_type_combo.currentText(),
            "title": f"{self.content_type_combo.currentText()} 结果",
            "preview": str(result)[:200] if result else "",
            "content": result,
            "timestamp": QDateTime.currentDateTime().toString()
        }

        # 添加到结果列表
        self.generation_results.append(result_data)
        self.add_result_widget(result_data)

        self.status_label.setText("生成完成")
        self.generation_completed.emit(operation_id, result)
        self.content_generated.emit(result_data)

    def on_operation_failed(self, operation_id: str, error_message: str):
        """处理操作失败"""
        self.progress_bar.setVisible(False)
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("生成内容")
        self.status_label.setText(f"生成失败: {error_message}")
        self.generation_failed.emit(operation_id, error_message)

    def on_generation_callback(self, operation_id: str, result: Any, error: Optional[str]):
        """生成回调函数"""
        # 这里可以添加额外的回调处理逻辑
        pass

    def add_result_widget(self, result_data: Dict[str, Any]):
        """添加结果组件"""
        result_widget = GenerationResultWidget(result_data)
        result_widget.result_selected.connect(self.on_result_selected)
        result_widget.result_deleted.connect(self.on_result_deleted)
        self.results_layout.addWidget(result_widget)

    def on_result_selected(self, result_data: Dict[str, Any]):
        """处理结果选择"""
        # 更新所有结果的选择状态
        for i in range(self.results_layout.count()):
            widget = self.results_layout.itemAt(i).widget()
            if isinstance(widget, GenerationResultWidget):
                widget.is_selected = (widget.result_data == result_data)
                widget.update_selection_style()

    def on_result_deleted(self, result_id: str):
        """处理结果删除"""
        # 从结果列表中移除
        self.generation_results = [r for r in self.generation_results if r.get("id") != result_id]

        # 从界面中移除
        for i in range(self.results_layout.count()):
            widget = self.results_layout.itemAt(i).widget()
            if isinstance(widget, GenerationResultWidget) and widget.result_id == result_id:
                widget.deleteLater()
                break

    def clear_results(self):
        """清空所有结果"""
        self.generation_results.clear()
        while self.results_layout.count():
            widget = self.results_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()

    def get_selected_result(self) -> Optional[Dict[str, Any]]:
        """获取选中的结果"""
        for result in self.generation_results:
            if result.get("id") == self.current_operation_id:
                return result
        return None

    def export_results(self, file_path: str):
        """导出结果"""
        export_data = {
            "results": self.generation_results,
            "export_time": QDateTime.currentDateTime().toString()
        }

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"导出失败: {e}")
            return False

    def import_results(self, file_path: str):
        """导入结果"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            imported_results = data.get("results", [])
            for result in imported_results:
                self.generation_results.append(result)
                self.add_result_widget(result)

            return True
        except Exception as e:
            print(f"导入失败: {e}")
            return False