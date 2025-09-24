#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI内容生成组件
为视频编辑提供智能内容生成功能
"""

import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QTextEdit, QTabWidget, QFrame, QScrollArea,
    QMessageBox, QProgressBar, QGroupBox, QSplitter,
    QListWidget, QListWidgetItem, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize, QThread, pyqtSlot
from PyQt6.QtGui import QIcon, QFont, QPalette, QColor

from ...core.config_manager import ConfigManager
from ...core.logger import Logger
from ...core.icon_manager import get_icon
from ...services.ai_service_manager import AIServiceManager
from ...services.ai_video_processing_service import (
    AIVideoProcessingService, VideoAnalysisRequest, VideoGenerationRequest
)
from ...services.chinese_ai_services import ChineseAIServiceFactory


@dataclass
class GenerationTask:
    """生成任务"""
    task_id: str
    task_type: str
    content: str
    model_id: str
    status: str = "pending"
    result: Optional[str] = None
    error: Optional[str] = None
    timestamp: float = 0.0
    cost: float = 0.0


class AIContentGenerator(QWidget):
    """AI内容生成器"""

    content_generated = pyqtSignal(str, str)  # 内容类型, 生成内容
    task_completed = pyqtSignal(str, bool)    # 任务ID, 是否成功

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("aiContentGenerator")

        # 初始化组件
        self.config_manager = ConfigManager()
        self.logger = Logger("AIContentGenerator")
        self.ai_service_manager = AIServiceManager(self.logger)
        self.ai_video_service = AIVideoProcessingService(self.ai_service_manager)

        # 任务管理
        self.tasks: Dict[str, GenerationTask] = {}
        self.current_task_id = None

        # 初始化UI
        self._init_ui()
        self._setup_connections()

        # 加载配置
        self._load_ai_config()

    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # 标题区域
        title_widget = self._create_title_section()
        layout.addWidget(title_widget)

        # 主要内容区域
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 2)

        # 左侧功能选择
        function_widget = self._create_function_section()
        main_splitter.addWidget(function_widget)

        # 右侧生成区域
        generator_widget = self._create_generator_section()
        main_splitter.addWidget(generator_widget)

        layout.addWidget(main_splitter)

        # 任务列表区域
        task_widget = self._create_task_section()
        layout.addWidget(task_widget)

    def _create_title_section(self) -> QWidget:
        """创建标题区域"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # 图标和标题
        icon_label = QLabel()
        icon_label.setPixmap(get_icon("ai", 32).pixmap(32, 32))
        layout.addWidget(icon_label)

        title_label = QLabel("AI内容生成")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        layout.addWidget(title_label)

        layout.addStretch()

        # 状态指示
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #52c41a; font-size: 14px;")
        layout.addWidget(self.status_label)

        return widget

    def _create_function_section(self) -> QWidget:
        """创建功能选择区域"""
        widget = QFrame()
        widget.setFrameShape(QFrame.Shape.Box)
        widget.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
            }
        """)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # 功能标题
        function_title = QLabel("生成功能")
        function_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057;")
        layout.addWidget(function_title)

        # 功能列表
        self.function_list = QListWidget()
        self.function_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e9ecef;
                border-radius: 4px;
                background-color: white;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #e6f7ff;
                color: #1890ff;
            }
        """)

        functions = [
            {"name": "视频脚本", "desc": "根据主题生成视频脚本", "icon": "document"},
            {"name": "配音文案", "desc": "生成视频配音文本", "icon": "microphone"},
            {"name": "字幕内容", "desc": "自动生成视频字幕", "icon": "caption"},
            {"name": "标题生成", "desc": "生成吸引人的视频标题", "icon": "title"},
            {"name": "标签生成", "desc": "生成视频标签和关键词", "icon": "tag"},
            {"name": "描述生成", "desc": "生成视频描述文字", "icon": "description"},
            {"name": "场景分析", "desc": "分析视频场景内容", "icon": "analysis"},
            {"name": "高光时刻", "desc": "识别视频精彩片段", "icon": "highlight"}
        ]

        for func in functions:
            item = QListWidgetItem(self.function_list)
            item.setText(func["name"])
            item.setToolTip(func["desc"])
            item.setData(Qt.ItemDataRole.UserRole, func)

        self.function_list.currentRowChanged.connect(self._on_function_selected)
        layout.addWidget(self.function_list)

        return widget

    def _create_generator_section(self) -> QWidget:
        """创建生成区域"""
        widget = QScrollArea()
        widget.setWidgetResizable(True)
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 生成配置
        config_group = QGroupBox("生成配置")
        config_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #495057;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        config_layout = QFormLayout(config_group)

        # 输入内容
        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("请输入要生成的内容描述或主题...")
        self.content_input.setMinimumHeight(100)
        config_layout.addRow("输入内容:", self.content_input)

        # 模型选择
        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(200)
        config_layout.addRow("选择模型:", self.model_combo)

        # 生成参数
        param_layout = QGridLayout()

        # 创意程度
        param_layout.addWidget(QLabel("创意程度:"), 0, 0)
        self.creativity_spin = QDoubleSpinBox()
        self.creativity_spin.setRange(0.0, 2.0)
        self.creativity_spin.setValue(0.7)
        self.creativity_spin.setSingleStep(0.1)
        param_layout.addWidget(self.creativity_spin, 0, 1)

        # 生成长度
        param_layout.addWidget(QLabel("生成长度:"), 1, 0)
        self.length_combo = QComboBox()
        self.length_combo.addItems(["短", "中", "长"])
        self.length_combo.setCurrentIndex(1)
        param_layout.addWidget(self.length_combo, 1, 1)

        # 语言风格
        param_layout.addWidget(QLabel("语言风格:"), 2, 0)
        self.style_combo = QComboBox()
        self.style_combo.addItems(["正式", "轻松", "专业", "创意", "幽默"])
        param_layout.addWidget(self.style_combo, 2, 1)

        config_layout.addRow("参数设置:", param_layout)

        layout.addWidget(config_group)

        # 预览区域
        preview_group = QGroupBox("生成预览")
        preview_group.setStyleSheet(config_group.styleSheet())
        preview_layout = QVBoxLayout(preview_group)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMinimumHeight(150)
        self.preview_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        preview_layout.addWidget(self.preview_text)

        layout.addWidget(preview_group)

        # 操作按钮
        button_layout = QHBoxLayout()

        self.generate_btn = QPushButton(get_icon("magic", 16), "生成内容")
        self.generate_btn.setFixedSize(120, 36)
        self.generate_btn.clicked.connect(self._generate_content)
        button_layout.addWidget(self.generate_btn)

        self.save_btn = QPushButton(get_icon("save", 16), "保存结果")
        self.save_btn.setFixedSize(120, 36)
        self.save_btn.clicked.connect(self._save_result)
        self.save_btn.setEnabled(False)
        button_layout.addWidget(self.save_btn)

        button_layout.addStretch()

        layout.addLayout(button_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        layout.addStretch()

        widget.setWidget(content_widget)
        return widget

    def _create_task_section(self) -> QWidget:
        """创建任务区域"""
        widget = QFrame()
        widget.setFrameShape(QFrame.Shape.Box)
        widget.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
            }
        """)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # 任务标题
        task_title = QLabel("任务队列")
        task_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057;")
        layout.addWidget(task_title)

        # 任务列表
        self.task_list = QListWidget()
        self.task_list.setMaximumHeight(150)
        self.task_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e9ecef;
                border-radius: 4px;
                background-color: white;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #f0f0f0;
            }
        """)
        layout.addWidget(self.task_list)

        return widget

    def _setup_connections(self):
        """设置信号连接"""
        pass

    def _load_ai_config(self):
        """加载AI配置"""
        try:
            configured_models = self.ai_service_manager.get_configured_models()
            self.model_combo.clear()

            for service_name, models in configured_models.items():
                if models:
                    service_info = ChineseAIServiceFactory.get_service_info(service_name)
                    for model in models:
                        display_name = f"{service_info['name']} - {model}"
                        self.model_combo.addItem(display_name, f"{service_name}:{model}")

            if self.model_combo.count() == 0:
                self.model_combo.addItem("未配置AI模型", "")
                self.model_combo.setEnabled(False)
                self.generate_btn.setEnabled(False)
            else:
                self.model_combo.setEnabled(True)
                self.generate_btn.setEnabled(True)

        except Exception as e:
            self.logger.error(f"加载AI配置失败: {e}")

    def _on_function_selected(self, row: int):
        """功能选择处理"""
        try:
            item = self.function_list.item(row)
            if not item:
                return

            func_data = item.data(Qt.ItemDataRole.UserRole)
            if func_data:
                # 更新输入提示
                placeholders = {
                    "视频脚本": "请描述视频的主题、风格、目标受众等...",
                    "配音文案": "请描述视频的内容和配音要求...",
                    "字幕内容": "请上传视频或描述视频内容...",
                    "标题生成": "请描述视频的主要内容...",
                    "标签生成": "请描述视频的主题和内容...",
                    "描述生成": "请描述视频的主要信息...",
                    "场景分析": "请上传视频文件...",
                    "高光时刻": "请上传视频文件..."
                }

                self.content_input.setPlaceholderText(placeholders.get(func_data["name"], "请输入内容..."))

        except Exception as e:
            self.logger.error(f"选择功能失败: {e}")

    def _generate_content(self):
        """生成内容"""
        try:
            # 检查输入
            content = self.content_input.toPlainText().strip()
            if not content:
                QMessageBox.warning(self, "警告", "请输入生成内容")
                return

            # 检查模型
            model_data = self.model_combo.currentData()
            if not model_data:
                QMessageBox.warning(self, "警告", "请选择AI模型")
                return

            service_name, model_id = model_data.split(":")
            function_item = self.function_list.currentItem()
            if not function_item:
                QMessageBox.warning(self, "警告", "请选择生成功能")
                return

            func_data = function_item.data(Qt.ItemDataRole.UserRole)
            function_name = func_data["name"]

            # 创建任务
            task_id = f"task_{int(time.time() * 1000)}"
            task = GenerationTask(
                task_id=task_id,
                task_type=function_name,
                content=content,
                model_id=model_id,
                status="processing",
                timestamp=time.time()
            )

            self.tasks[task_id] = task
            self.current_task_id = task_id

            # 添加到任务列表
            self._add_task_to_list(task)

            # 显示进度
            self.status_label.setText("正在生成...")
            self.generate_btn.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)

            # 根据功能类型生成内容
            if function_name in ["场景分析", "高光时刻"]:
                self._analyze_video_content(task, service_name, content)
            else:
                self._generate_text_content(task, service_name, content)

        except Exception as e:
            self.logger.error(f"生成内容失败: {e}")
            QMessageBox.critical(self, "错误", f"生成失败: {e}")

    def _generate_text_content(self, task: GenerationTask, service_name: str, content: str):
        """生成文本内容"""
        try:
            # 构建提示词
            prompt = self._build_prompt(task.task_type, content)

            # 发送AI请求
            request_id = self.ai_service_manager.send_request(
                service_name,
                task.model_id,
                prompt,
                max_tokens=self._get_max_tokens(),
                temperature=self.creativity_spin.value(),
                callback=lambda response: self._on_generation_complete(task.task_id, response)
            )

            if request_id:
                # 模拟进度更新
                self._simulate_progress()

        except Exception as e:
            self.logger.error(f"生成文本内容失败: {e}")
            self._on_generation_error(task.task_id, str(e))

    def _analyze_video_content(self, task: GenerationTask, service_name: str, content: str):
        """分析视频内容"""
        try:
            # 模拟视频分析（实际应用中需要处理视频文件）
            if task.task_type == "场景分析":
                analysis_request = VideoAnalysisRequest(
                    video_path=content,  # 这里应该是视频文件路径
                    analysis_type="scene_detection",
                    model_id=task.model_id,
                    max_duration=300
                )
            else:  # 高光时刻
                analysis_request = VideoAnalysisRequest(
                    video_path=content,
                    analysis_type="highlight_detection",
                    model_id=task.model_id,
                    max_duration=300
                )

            # 执行分析
            def callback(result):
                if result and "error" not in result.results:
                    formatted_result = self._format_analysis_result(task.task_type, result)
                    self._on_generation_complete(task.task_id, formatted_result)
                else:
                    error_msg = result.results.get("error", "分析失败") if result else "分析失败"
                    self._on_generation_error(task.task_id, error_msg)

            self.ai_video_service.analyze_video(analysis_request, callback)
            self._simulate_progress()

        except Exception as e:
            self.logger.error(f"分析视频内容失败: {e}")
            self._on_generation_error(task.task_id, str(e))

    def _build_prompt(self, task_type: str, content: str) -> str:
        """构建提示词"""
        style = self.style_combo.currentText()
        length = self.length_combo.currentText()

        prompts = {
            "视频脚本": f"请根据以下主题生成一个视频脚本：\n\n主题：{content}\n\n风格：{style}\n长度：{length}\n\n要求：\n1. 包含开场、主体、结尾\n2. 语言自然流畅\n3. 适合口头表达",
            "配音文案": f"请为以下视频内容生成配音文案：\n\n内容：{content}\n\n风格：{style}\n长度：{length}\n\n要求：\n1. 语言简洁明了\n2. 节奏感强\n3. 符合画面内容",
            "字幕内容": f"请为以下视频生成字幕内容：\n\n内容：{content}\n\n风格：{style}\n\n要求：\n1. 准确表达内容\n2. 控制字数\n3. 便于阅读",
            "标题生成": f"请为以下视频生成吸引人的标题：\n\n内容：{content}\n\n风格：{style}\n\n要求：\n1. 吸引眼球\n2. 简洁有力\n3. 包含关键词",
            "标签生成": f"请为以下视频生成标签和关键词：\n\n内容：{content}\n\n要求：\n1. 相关性强\n2. 覆盖面广\n3. 按重要性排序",
            "描述生成": f"请为以下视频生成描述文字：\n\n内容：{content}\n\n风格：{style}\n长度：{length}\n\n要求：\n1. 内容完整\n2. 语言流畅\n3. 吸引用户"
        }

        return prompts.get(task_type, f"请根据以下内容生成{task_type}：\n\n{content}")

    def _get_max_tokens(self) -> int:
        """获取最大令牌数"""
        length_map = {"短": 500, "中": 1000, "长": 2000}
        return length_map.get(self.length_combo.currentText(), 1000)

    def _simulate_progress(self):
        """模拟进度更新"""
        def update_progress():
            for i in range(1, 101):
                if self.progress_bar.isVisible():
                    self.progress_bar.setValue(i)
                    time.sleep(0.02)  # 模拟处理时间
                else:
                    break

        import threading
        progress_thread = threading.Thread(target=update_progress, daemon=True)
        progress_thread.start()

    def _on_generation_complete(self, task_id: str, response):
        """生成完成处理"""
        try:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = "completed"
                task.result = response
                task.timestamp = time.time()

                # 更新UI
                self.preview_text.setText(response)
                self.save_btn.setEnabled(True)
                self.status_label.setText("生成完成")
                self.generate_btn.setEnabled(True)
                self.progress_bar.setVisible(False)

                # 更新任务列表
                self._update_task_in_list(task)

                # 发送信号
                self.content_generated.emit(task.task_type, response)
                self.task_completed.emit(task_id, True)

        except Exception as e:
            self.logger.error(f"处理生成完成失败: {e}")

    def _on_generation_error(self, task_id: str, error_message: str):
        """生成错误处理"""
        try:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = "error"
                task.error = error_message

                # 更新UI
                self.status_label.setText("生成失败")
                self.generate_btn.setEnabled(True)
                self.progress_bar.setVisible(False)

                # 更新任务列表
                self._update_task_in_list(task)

                # 发送信号
                self.task_completed.emit(task_id, False)

                QMessageBox.critical(self, "错误", f"生成失败: {error_message}")

        except Exception as e:
            self.logger.error(f"处理生成错误失败: {e}")

    def _format_analysis_result(self, analysis_type: str, result) -> str:
        """格式化分析结果"""
        try:
            if analysis_type == "场景分析":
                scenes = result.results.get("scenes", [])
                formatted = "场景分析结果：\n\n"
                for i, scene in enumerate(scenes, 1):
                    formatted += f"场景{i}: {scene['start_time']}s - {scene['end_time']}s\n"
                    formatted += f"描述: {scene['description']}\n"
                    formatted += f"置信度: {scene['confidence']:.2f}\n\n"
                return formatted

            elif analysis_type == "高光时刻":
                highlights = result.results.get("highlights", [])
                formatted = "高光时刻分析结果：\n\n"
                for i, highlight in enumerate(highlights, 1):
                    formatted += f"高光{i}: {highlight['start_time']}s - {highlight['end_time']}s\n"
                    formatted += f"描述: {highlight['description']}\n"
                    formatted += f"评分: {highlight['score']:.2f}\n\n"
                return formatted

            return str(result.results)

        except Exception as e:
            self.logger.error(f"格式化分析结果失败: {e}")
            return "分析结果格式化失败"

    def _add_task_to_list(self, task: GenerationTask):
        """添加任务到列表"""
        try:
            item = QListWidgetItem(self.task_list)
            item.setText(f"{task.task_type} - {task.status}")
            item.setData(Qt.ItemDataRole.UserRole, task.task_id)

            # 根据状态设置颜色
            if task.status == "completed":
                item.setForeground(QColor("#52c41a"))
            elif task.status == "error":
                item.setForeground(QColor("#ff4d4f"))
            else:
                item.setForeground(QColor("#1890ff"))

        except Exception as e:
            self.logger.error(f"添加任务到列表失败: {e}")

    def _update_task_in_list(self, task: GenerationTask):
        """更新任务列表中的任务"""
        try:
            for i in range(self.task_list.count()):
                item = self.task_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == task.task_id:
                    item.setText(f"{task.task_type} - {task.status}")

                    # 根据状态设置颜色
                    if task.status == "completed":
                        item.setForeground(QColor("#52c41a"))
                    elif task.status == "error":
                        item.setForeground(QColor("#ff4d4f"))
                    else:
                        item.setForeground(QColor("#1890ff"))

                    break

        except Exception as e:
            self.logger.error(f"更新任务列表失败: {e}")

    def _save_result(self):
        """保存生成结果"""
        try:
            result = self.preview_text.toPlainText()
            if not result:
                QMessageBox.warning(self, "警告", "没有可保存的内容")
                return

            # 这里可以添加保存逻辑，比如保存到文件或复制到剪贴板
            from PyQt6.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存生成结果", "", "文本文件 (*.txt);;所有文件 (*)"
            )

            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(result)
                QMessageBox.information(self, "成功", "结果已保存")

        except Exception as e:
            self.logger.error(f"保存结果失败: {e}")
            QMessageBox.critical(self, "错误", f"保存失败: {e}")

    def get_recent_tasks(self, limit: int = 10) -> List[GenerationTask]:
        """获取最近的任务"""
        try:
            sorted_tasks = sorted(
                self.tasks.values(),
                key=lambda x: x.timestamp,
                reverse=True
            )
            return sorted_tasks[:limit]
        except Exception as e:
            self.logger.error(f"获取最近任务失败: {e}")
            return []

    def clear_completed_tasks(self):
        """清理已完成的任务"""
        try:
            completed_tasks = [
                task_id for task_id, task in self.tasks.items()
                if task.status in ["completed", "error"]
            ]

            for task_id in completed_tasks:
                del self.tasks[task_id]

            # 刷新任务列表
            self.task_list.clear()
            for task in self.tasks.values():
                self._add_task_to_list(task)

        except Exception as e:
            self.logger.error(f"清理已完成任务失败: {e}")

    def cleanup(self):
        """清理资源"""
        try:
            self.tasks.clear()
            self.ai_video_service.cleanup()
            self.ai_service_manager.cleanup()
        except Exception as e:
            self.logger.error(f"清理资源失败: {e}")