#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio 项目管理器UI组件
提供项目管理的用户界面组件
"""

import os
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QPushButton, QLabel, QFrame, QGroupBox, QSplitter, QDialog,
    QLineEdit, QTextEdit, QComboBox, QSpinBox, QCheckBox,
    QFileDialog, QMessageBox, QProgressBar, QTableWidget,
    QTableWidgetItem, QHeaderView, QTabWidget, QInputDialog
)
from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, QSize, QSettings
)
from PyQt6.QtGui import QFont, QIcon, QPixmap

from ...core.project import Project, ProjectType, ProjectStatus
from ...core.project_manager import ProjectManager
from ...core.application import Application
from ...core.config_manager import ConfigManager
from ...core.logger import Logger


class CreateProjectDialog(QDialog):
    """创建项目对话框"""

    project_created = pyqtSignal(dict)  # 项目创建信号

    def __init__(self, project_manager: ProjectManager, parent=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self.selected_template = None
        self._init_ui()

    def _init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("创建新项目")
        self.setModal(True)
        self.setFixedSize(500, 400)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # 项目名称
        name_layout = QHBoxLayout()
        name_label = QLabel("项目名称:")
        name_label.setFixedWidth(80)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("输入项目名称...")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # 项目类型
        type_layout = QHBoxLayout()
        type_label = QLabel("项目类型:")
        type_label.setFixedWidth(80)
        self.type_combo = QComboBox()
        for project_type in ProjectType:
            self.type_combo.addItem(project_type.value.replace('_', ' ').title(), project_type)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)

        # 项目描述
        desc_layout = QHBoxLayout()
        desc_label = QLabel("项目描述:")
        desc_label.setFixedWidth(80)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("输入项目描述...")
        self.desc_edit.setMaximumHeight(80)
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.desc_edit)
        layout.addLayout(desc_layout)

        # 模板选择
        template_group = QGroupBox("项目模板")
        template_layout = QVBoxLayout(template_group)

        self.template_combo = QComboBox()
        self.template_combo.addItem("无模板", None)

        # 加载可用模板
        templates = self.project_manager.get_templates()
        for template in templates:
            self.template_combo.addItem(template.metadata.name, template.id)

        template_layout.addWidget(self.template_combo)
        layout.addWidget(template_group)

        # 项目设置
        settings_group = QGroupBox("项目设置")
        settings_layout = QGridLayout(settings_group)

        # 视频分辨率
        settings_layout.addWidget(QLabel("视频分辨率:"), 0, 0)
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems([
            "1920x1080 (Full HD)",
            "1280x720 (HD)",
            "3840x2160 (4K)",
            "2560x1440 (2K)"
        ])
        settings_layout.addWidget(self.resolution_combo, 0, 1)

        # 帧率
        settings_layout.addWidget(QLabel("帧率:"), 1, 0)
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(15, 120)
        self.fps_spin.setValue(30)
        self.fps_spin.setSuffix(" fps")
        settings_layout.addWidget(self.fps_spin, 1, 1)

        # 自动保存
        self.auto_save_check = QCheckBox("启用自动保存")
        self.auto_save_check.setChecked(True)
        settings_layout.addWidget(self.auto_save_check, 2, 0, 1, 2)

        # 备份
        self.backup_check = QCheckBox("启用项目备份")
        self.backup_check.setChecked(True)
        settings_layout.addWidget(self.backup_check, 3, 0, 1, 2)

        layout.addWidget(settings_group)

        # 按钮
        button_layout = QHBoxLayout()

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)

        create_btn = QPushButton("创建项目")
        create_btn.clicked.connect(self._create_project)
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
        """)

        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(create_btn)
        layout.addLayout(button_layout)

    def _create_project(self):
        """创建项目"""
        try:
            name = self.name_edit.text().strip()
            if not name:
                QMessageBox.warning(self, "警告", "请输入项目名称")
                return

            project_type = self.type_combo.currentData()
            description = self.desc_edit.toPlainText().strip()
            template_id = self.template_combo.currentData()

            # 解析分辨率
            resolution_text = self.resolution_combo.currentText()
            resolution = resolution_text.split(' ')[0]

            # 创建项目
            project_id = self.project_manager.create_project(
                name=name,
                project_type=project_type,
                description=description,
                template_id=template_id
            )

            if project_id:
                # 更新项目设置
                project = self.project_manager.get_project(project_id)
                if project:
                    settings = {
                        'video_resolution': resolution,
                        'video_fps': self.fps_spin.value(),
                        'auto_save_interval': 300 if self.auto_save_check.isChecked() else 0,
                        'backup_enabled': self.backup_check.isChecked()
                    }
                    project.update_settings(settings)
                    project.save()

                # 发送信号
                self.project_created.emit({
                    'id': project_id,
                    'name': name,
                    'type': project_type.value,
                    'description': description
                })

                self.accept()
            else:
                QMessageBox.critical(self, "错误", "创建项目失败")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"创建项目时发生错误: {str(e)}")


class ProjectListWidget(QWidget):
    """项目列表组件"""

    project_selected = pyqtSignal(dict)    # 项目选择信号
    project_opened = pyqtSignal(dict)       # 项目打开信号
    project_deleted = pyqtSignal(dict)      # 项目删除信号

    def __init__(self, project_manager: ProjectManager, parent=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self.projects: List[dict] = []
        self._init_ui()
        self._load_projects()

    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 工具栏
        toolbar_layout = QHBoxLayout()

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索项目...")
        self.search_edit.textChanged.connect(self._filter_projects)
        toolbar_layout.addWidget(self.search_edit)

        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self._load_projects)
        refresh_btn.setFixedSize(80, 30)
        toolbar_layout.addWidget(refresh_btn)

        layout.addLayout(toolbar_layout)

        # 项目表格
        self.project_table = QTableWidget()
        self.project_table.setColumnCount(6)
        self.project_table.setHorizontalHeaderLabels([
            "项目名称", "类型", "状态", "修改时间", "媒体文件", "操作"
        ])

        # 设置表格属性
        self.project_table.setAlternatingRowColors(True)
        self.project_table.setSortingEnabled(True)
        self.project_table.horizontalHeader().setStretchLastSection(True)
        self.project_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.project_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.project_table.itemDoubleClicked.connect(self._on_item_double_clicked)

        # 设置列宽
        self.project_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.project_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.project_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.project_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.project_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.project_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.project_table)

    def _load_projects(self):
        """加载项目列表"""
        try:
            self.projects.clear()

            # 获取所有项目
            projects = self.project_manager.get_all_projects()
            for project in projects:
                self.projects.append(project.get_project_info())

            # 添加最近项目
            recent_projects = self.project_manager.get_recent_projects()
            for project_path in recent_projects:
                if os.path.exists(project_path):
                    # 尝试从项目路径获取项目信息
                    try:
                        with open(os.path.join(project_path, 'project.json'), 'r', encoding='utf-8') as f:
                            project_data = json.load(f)

                        project_info = {
                            'id': project_path,
                            'name': project_data['metadata']['name'],
                            'description': project_data['metadata'].get('description', ''),
                            'path': project_path,
                            'created_at': project_data['metadata']['created_at'],
                            'modified_at': project_data['metadata']['modified_at'],
                            'project_type': project_data['metadata']['project_type'],
                            'status': 'recent',
                            'media_count': 0,
                            'duration': 0,
                            'is_modified': False,
                            'is_loaded': False
                        }

                        if not any(p['id'] == project_info['id'] for p in self.projects):
                            self.projects.append(project_info)
                    except:
                        continue

            self._update_project_table()

        except Exception as e:
            print(f"加载项目列表失败: {e}")

    def _update_project_table(self):
        """更新项目表格"""
        self.project_table.setRowCount(len(self.projects))

        for row, project in enumerate(self.projects):
            # 项目名称
            name_item = QTableWidgetItem(project['name'])
            name_item.setData(Qt.ItemDataRole.UserRole, project)
            self.project_table.setItem(row, 0, name_item)

            # 项目类型
            type_text = project['project_type'].replace('_', ' ').title()
            self.project_table.setItem(row, 1, QTableWidgetItem(type_text))

            # 状态
            status_text = {
                'active': '活跃',
                'archived': '已归档',
                'template': '模板',
                'recent': '最近'
            }.get(project['status'], '未知')
            self.project_table.setItem(row, 2, QTableWidgetItem(status_text))

            # 修改时间
            if project.get('modified_at'):
                try:
                    modified_time = datetime.fromisoformat(project['modified_at'])
                    time_str = modified_time.strftime('%Y-%m-%d %H:%M')
                    self.project_table.setItem(row, 3, QTableWidgetItem(time_str))
                except:
                    self.project_table.setItem(row, 3, QTableWidgetItem('未知'))
            else:
                self.project_table.setItem(row, 3, QTableWidgetItem('未知'))

            # 媒体文件数量
            media_count = str(project.get('media_count', 0))
            self.project_table.setItem(row, 4, QTableWidgetItem(media_count))

            # 操作按钮
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)
            action_layout.setSpacing(2)

            # 打开按钮
            open_btn = QPushButton("打开")
            open_btn.setFixedSize(50, 25)
            open_btn.clicked.connect(lambda checked, p=project: self._open_project(p))
            action_layout.addWidget(open_btn)

            # 删除按钮
            if project['status'] != 'recent':
                delete_btn = QPushButton("删除")
                delete_btn.setFixedSize(50, 25)
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ff4d4f;
                        color: white;
                        border: none;
                        border-radius: 2px;
                        font-size: 10px;
                    }
                    QPushButton:hover {
                        background-color: #ff7875;
                    }
                """)
                delete_btn.clicked.connect(lambda checked, p=project: self._delete_project(p))
                action_layout.addWidget(delete_btn)

            action_layout.addStretch()
            self.project_table.setCellWidget(row, 5, action_widget)

    def _filter_projects(self):
        """过滤项目"""
        search_text = self.search_edit.text().lower()

        for row in range(self.project_table.rowCount()):
            item = self.project_table.item(row, 0)
            if item:
                project_name = item.text().lower()
                match = search_text in project_name
                self.project_table.setRowHidden(row, not match)

    def _on_item_double_clicked(self, item):
        """处理项目双击事件"""
        row = item.row()
        name_item = self.project_table.item(row, 0)
        if name_item:
            project = name_item.data(Qt.ItemDataRole.UserRole)
            self._open_project(project)

    def _open_project(self, project: dict):
        """打开项目"""
        try:
            if project['status'] == 'recent':
                # 最近项目需要先打开
                project_id = self.project_manager.open_project(project['path'])
                if project_id:
                    project = self.project_manager.get_project(project_id).get_project_info()
            else:
                project_id = project['id']

            self.project_opened.emit(project)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开项目失败: {str(e)}")

    def _delete_project(self, project: dict):
        """删除项目"""
        try:
            reply = QMessageBox.question(
                self,
                "确认删除",
                f"确定要删除项目 '{project['name']}' 吗？此操作不可撤销。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                success = self.project_manager.delete_project(project['id'])
                if success:
                    self.project_deleted.emit(project)
                    self._load_projects()
                else:
                    QMessageBox.critical(self, "错误", "删除项目失败")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除项目失败: {str(e)}")

    def refresh(self):
        """刷新项目列表"""
        self._load_projects()


class ProjectManagerWidget(QWidget):
    """项目管理器主组件"""

    project_created = pyqtSignal(dict)      # 项目创建信号
    project_opened = pyqtSignal(dict)       # 项目打开信号
    project_imported = pyqtSignal(dict)     # 项目导入信号
    project_exported = pyqtSignal(dict)     # 项目导出信号

    def __init__(self, application: Application, parent=None):
        super().__init__(parent)
        self.application = application
        self.project_manager = application.get_service_by_name("project_manager")
        self.logger = application.get_service_by_name("logger")
        self.config_manager = application.get_service_by_name("config_manager")

        if not self.project_manager:
            # 如果没有项目管理器，创建一个
            from ...core.project_manager import ProjectManager
            self.project_manager = ProjectManager(self.config_manager)

        self._init_ui()
        self._setup_connections()

    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 创建选项卡
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: transparent;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #b0b0b0;
                padding: 10px 20px;
                border: none;
                border-bottom: 2px solid transparent;
                margin-right: 2px;
                font-size: 13px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #3a3a3a;
                color: #ffffff;
                border-bottom-color: #1890ff;
            }
            QTabBar::tab:hover {
                background-color: #3a3a3a;
                color: #ffffff;
            }
        """)

        # 项目管理选项卡
        self.project_list_widget = ProjectListWidget(self.project_manager)
        self.tab_widget.addTab(self.project_list_widget, "项目管理")

        # 最近项目选项卡
        self.recent_projects_widget = QWidget()
        self._setup_recent_projects_tab()
        self.tab_widget.addTab(self.recent_projects_widget, "最近项目")

        # 项目模板选项卡
        self.templates_widget = QWidget()
        self._setup_templates_tab()
        self.tab_widget.addTab(self.templates_widget, "项目模板")

        layout.addWidget(self.tab_widget)

    def _setup_recent_projects_tab(self):
        """设置最近项目选项卡"""
        layout = QVBoxLayout(self.recent_projects_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题
        title_label = QLabel("最近项目")
        title_font = QFont("Arial", 16, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ffffff; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # 最近项目列表
        self.recent_list = ProjectListWidget(self.project_manager)
        layout.addWidget(self.recent_list)

    def _setup_templates_tab(self):
        """设置项目模板选项卡"""
        layout = QVBoxLayout(self.templates_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题
        title_label = QLabel("项目模板")
        title_font = QFont("Arial", 16, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ffffff; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # 模板描述
        desc_label = QLabel("选择项目模板可以快速开始特定类型的视频编辑项目")
        desc_label.setStyleSheet("color: #b0b0b0; font-size: 12px;")
        layout.addWidget(desc_label)

        # 模板网格
        template_grid = QGridLayout()
        template_grid.setSpacing(15)

        # 添加模板卡片
        templates = [
            ("空白项目", "创建一个空白的视频编辑项目", "video_editing"),
            ("AI增强", "使用AI功能增强视频项目", "ai_enhancement"),
            ("视频混剪", "创建视频混剪项目", "compilation"),
            ("解说视频", "创建解说视频项目", "commentary"),
            ("多媒体项目", "创建包含多种媒体的项目", "multimedia")
        ]

        for i, (name, desc, ptype) in enumerate(templates):
            template_card = self._create_template_card(name, desc, ptype)
            row = i // 2
            col = i % 2
            template_grid.addWidget(template_card, row, col)

        layout.addLayout(template_grid)
        layout.addStretch()

    def _create_template_card(self, name: str, description: str, project_type: str) -> QWidget:
        """创建模板卡片"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box)
        card.setObjectName(f"templateCard_{project_type}")
        card.setCursor(Qt.CursorShape.PointingHandCard)

        # 根据模板类型设置不同的颜色主题
        colors = {
            "video_editing": "#1890ff",
            "ai_enhancement": "#52c41a",
            "compilation": "#fa8c16",
            "commentary": "#722ed1",
            "multimedia": "#eb2f96"
        }
        color = colors.get(project_type, "#1890ff")

        card.setStyleSheet(f"""
            QFrame {{
                background-color: #2d2d2d;
                border: 2px solid #404040;
                border-radius: 12px;
                padding: 15px;
            }}
            QFrame:hover {{
                background-color: #3a3a3a;
                border-color: {color};
            }}
        """)
        card.setFixedSize(250, 120)

        layout = QVBoxLayout(card)
        layout.setSpacing(8)

        # 模板名称
        name_label = QLabel(name)
        name_font = QFont("Arial", 14, QFont.Weight.Bold)
        name_label.setFont(name_font)
        name_label.setStyleSheet("color: #ffffff;")
        layout.addWidget(name_label)

        # 模板描述
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #b0b0b0; font-size: 11px;")
        layout.addWidget(desc_label)

        layout.addStretch()

        # 创建按钮
        create_btn = QPushButton("创建项目")
        create_btn.setFixedSize(100, 25)
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
        """)
        create_btn.clicked.connect(lambda checked, t=project_type: self._create_project_from_template(t))
        layout.addWidget(create_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        return card

    def _setup_connections(self):
        """设置信号连接"""
        # 项目列表信号
        self.project_list_widget.project_opened.connect(self.project_opened)

        # 项目管理器信号
        if hasattr(self.project_manager, 'project_created'):
            self.project_manager.project_created.connect(self._on_project_created)
        if hasattr(self.project_manager, 'project_opened'):
            self.project_manager.project_opened.connect(self._on_project_opened)

    def _on_project_created(self, project_id: str):
        """处理项目创建信号"""
        project = self.project_manager.get_project(project_id)
        if project:
            self.project_created.emit(project.get_project_info())

    def _on_project_opened(self, project_id: str):
        """处理项目打开信号"""
        project = self.project_manager.get_project(project_id)
        if project:
            self.project_opened.emit(project.get_project_info())

    def _create_project_from_template(self, project_type: str):
        """从模板创建项目"""
        dialog = CreateProjectDialog(self.project_manager, self)
        dialog.project_created.connect(self.project_created)

        # 设置项目类型
        for i in range(dialog.type_combo.count()):
            if dialog.type_combo.itemData(i).value == project_type:
                dialog.type_combo.setCurrentIndex(i)
                break

        dialog.exec()

    def show_create_project_dialog(self):
        """显示创建项目对话框"""
        dialog = CreateProjectDialog(self.project_manager, self)
        dialog.project_created.connect(self.project_created)
        dialog.exec()

    def open_project(self):
        """打开项目"""
        try:
            project_file, _ = QFileDialog.getOpenFileName(
                self,
                "打开项目",
                os.path.expanduser("~"),
                "CineAIStudio项目文件 (project.json);;所有文件 (*)"
            )

            if project_file:
                project_dir = os.path.dirname(project_file)
                project_id = self.project_manager.open_project(project_dir)

                if project_id:
                    project = self.project_manager.get_project(project_id)
                    if project:
                        self.project_opened.emit(project.get_project_info())
                else:
                    QMessageBox.critical(self, "错误", "打开项目失败")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开项目失败: {str(e)}")

    def save_project(self):
        """保存当前项目"""
        current_project = self.project_manager.get_current_project()
        if current_project:
            success = self.project_manager.save_project(current_project.id)
            if success:
                QMessageBox.information(self, "成功", "项目保存成功")
            else:
                QMessageBox.critical(self, "错误", "保存项目失败")
        else:
            QMessageBox.warning(self, "警告", "没有打开的项目")

    def import_project(self):
        """导入项目"""
        try:
            import_file, _ = QFileDialog.getOpenFileName(
                self,
                "导入项目",
                os.path.expanduser("~"),
                "CineAIStudio项目包 (*.cineaiproj);;ZIP文件 (*.zip);;所有文件 (*)"
            )

            if import_file:
                project_id = self.project_manager.import_project(import_file)
                if project_id:
                    project = self.project_manager.get_project(project_id)
                    if project:
                        self.project_imported.emit(project.get_project_info())
                        QMessageBox.information(self, "成功", "项目导入成功")
                else:
                    QMessageBox.critical(self, "错误", "导入项目失败")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入项目失败: {str(e)}")

    def export_project(self):
        """导出项目"""
        current_project = self.project_manager.get_current_project()
        if not current_project:
            QMessageBox.warning(self, "警告", "没有打开的项目")
            return

        try:
            export_file, _ = QFileDialog.getSaveFileName(
                self,
                "导出项目",
                os.path.expanduser(f"~/{current_project.metadata.name}.cineaiproj"),
                "CineAIStudio项目包 (*.cineaiproj);;ZIP文件 (*.zip);;所有文件 (*)"
            )

            if export_file:
                success = self.project_manager.export_project(
                    current_project.id, export_file, include_media=True
                )
                if success:
                    self.project_exported.emit(current_project.get_project_info())
                    QMessageBox.information(self, "成功", "项目导出成功")
                else:
                    QMessageBox.critical(self, "错误", "导出项目失败")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出项目失败: {str(e)}")

    def refresh(self):
        """刷新项目管理器"""
        self.project_list_widget.refresh()
        if hasattr(self, 'recent_list'):
            self.recent_list.refresh()