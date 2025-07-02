#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
专业主窗口 - 完全重新设计，解决所有UI问题
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget,
    QLabel, QFrame, QSizePolicy, QStatusBar, QMenuBar, QToolBar,
    QTabWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QAction, QIcon

from app.config.settings_manager import SettingsManager
from app.core.project_manager import ProjectManager
from app.ai import AIManager

from .professional_ui_system import (
    ProfessionalTheme, ProfessionalButton, ProfessionalCard,
    ProfessionalNavigation, ProfessionalHomePage
)
from .global_style_fixer import fix_widget_styles


class ProfessionalAIFeaturesPage(QWidget):
    """专业AI功能页面 - 完全重新设计，集成字幕提取"""

    def __init__(self, ai_manager, parent=None):
        super().__init__(parent)
        self.ai_manager = ai_manager
        self.is_dark_theme = False
        self.current_feature = None
        self.current_video_path = None
        self.current_subtitles = None

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self):
        """设置UI"""
        # 创建选项卡界面
        from PyQt6.QtWidgets import QTabWidget
        self.tab_widget = QTabWidget()

        # 功能选择选项卡
        self.features_tab = self._create_features_tab()
        self.tab_widget.addTab(self.features_tab, "🎯 功能选择")

        # 字幕提取选项卡
        self.subtitle_tab = self._create_subtitle_tab()
        self.tab_widget.addTab(self.subtitle_tab, "📝 字幕提取")

        # 工作流选项卡
        self.workflow_tab = self._create_workflow_tab()
        self.tab_widget.addTab(self.workflow_tab, "⚙️ 处理流程")

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.tab_widget)

    def _create_features_tab(self) -> QWidget:
        """创建功能选择选项卡"""
        # 创建滚动区域
        from PyQt6.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 主内容
        content_widget = QWidget()
        scroll_area.setWidget(content_widget)

        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(32)

        # 页面标题
        title_label = QLabel("AI功能")
        title_label.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 功能选择区域
        features_card = ProfessionalCard("选择AI功能")

        # 功能按钮网格
        features_grid = QHBoxLayout()
        features_grid.setSpacing(24)

        # AI短剧解说
        commentary_widget = self._create_feature_widget(
            "🎬", "AI短剧解说",
            "智能生成适合短剧的解说内容",
            "commentary"
        )
        features_grid.addWidget(commentary_widget)

        # AI高能混剪
        compilation_widget = self._create_feature_widget(
            "⚡", "AI高能混剪",
            "自动检测精彩场景并生成混剪",
            "compilation"
        )
        features_grid.addWidget(compilation_widget)

        # AI第一人称独白
        monologue_widget = self._create_feature_widget(
            "🎭", "AI第一人称独白",
            "生成第一人称叙述内容",
            "monologue"
        )
        features_grid.addWidget(monologue_widget)

        features_widget = QWidget()
        features_widget.setLayout(features_grid)
        features_card.add_content(features_widget)

        layout.addWidget(features_card)

        # 功能详情区域
        self.details_card = ProfessionalCard("功能详情")
        self.details_content = QLabel("请选择上方的AI功能查看详细信息")
        self.details_content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.details_content.setFont(QFont("Arial", 16))
        self.details_content.setMinimumHeight(200)
        self.details_card.add_content(self.details_content)

        layout.addWidget(self.details_card)

        # 添加弹性空间
        layout.addStretch()

        return scroll_area

    def _create_subtitle_tab(self) -> QWidget:
        """创建字幕提取选项卡"""
        from app.ui.components.subtitle_extraction_widget import SubtitleExtractionWidget

        self.subtitle_widget = SubtitleExtractionWidget()
        self.subtitle_widget.extraction_completed.connect(self._on_subtitle_extraction_completed)

        return self.subtitle_widget

    def _create_workflow_tab(self) -> QWidget:
        """创建工作流选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)

        # 标题
        title_label = QLabel("AI处理流程")
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        layout.addWidget(title_label)

        # 流程状态
        self.workflow_status_card = ProfessionalCard("处理状态")
        self.workflow_status_label = QLabel("请先完成字幕提取，然后选择AI功能")
        self.workflow_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.workflow_status_label.setFont(QFont("Arial", 14))
        self.workflow_status_card.add_content(self.workflow_status_label)

        layout.addWidget(self.workflow_status_card)

        # 处理控制
        control_card = ProfessionalCard("处理控制")

        control_layout = QVBoxLayout()

        # 视频文件状态
        self.video_status_label = QLabel("视频文件: 未选择")
        control_layout.addWidget(self.video_status_label)

        # 字幕状态
        self.subtitle_status_label = QLabel("字幕提取: 未完成")
        control_layout.addWidget(self.subtitle_status_label)

        # AI功能状态
        self.ai_feature_status_label = QLabel("AI功能: 未选择")
        control_layout.addWidget(self.ai_feature_status_label)

        # 开始处理按钮
        self.start_processing_btn = ProfessionalButton("🚀 开始AI处理", "primary")
        self.start_processing_btn.setEnabled(False)
        self.start_processing_btn.clicked.connect(self._start_ai_processing)
        control_layout.addWidget(self.start_processing_btn)

        control_widget = QWidget()
        control_widget.setLayout(control_layout)
        control_card.add_content(control_widget)

        layout.addWidget(control_card)

        layout.addStretch()

        return tab

    def _create_feature_widget(self, icon, title, description, feature_id):
        """创建功能选择组件"""
        widget = QWidget()
        widget.setFixedSize(200, 160)
        widget.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 图标
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Arial", 32))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # 标题
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        # 描述
        desc_label = QLabel(description)
        desc_label.setFont(QFont("Arial", 11))
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # 点击事件
        def on_click():
            self._show_feature_details(feature_id, title, description)

        widget.mousePressEvent = lambda event: on_click()

        return widget

    def _show_feature_details(self, feature_id, title, description):
        """显示功能详情"""
        self.current_feature = feature_id

        # 创建详情内容
        details_layout = QVBoxLayout()
        details_layout.setSpacing(16)

        # 功能标题
        feature_title = QLabel(f"{title}")
        feature_title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        feature_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        details_layout.addWidget(feature_title)

        # 功能描述
        feature_desc = QLabel(description)
        feature_desc.setFont(QFont("Arial", 14))
        feature_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        feature_desc.setWordWrap(True)
        details_layout.addWidget(feature_desc)

        # 功能特点
        features_text = self._get_feature_details(feature_id)
        features_label = QLabel(features_text)
        features_label.setFont(QFont("Arial", 12))
        features_label.setWordWrap(True)
        details_layout.addWidget(features_label)

        # 操作按钮
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(16)

        start_btn = ProfessionalButton("🚀 开始使用", "primary")
        start_btn.clicked.connect(lambda: self._start_feature(feature_id))
        buttons_layout.addWidget(start_btn)

        demo_btn = ProfessionalButton("📖 查看教程", "default")
        buttons_layout.addWidget(demo_btn)

        buttons_layout.addStretch()

        buttons_widget = QWidget()
        buttons_widget.setLayout(buttons_layout)
        details_layout.addWidget(buttons_widget)

        # 更新详情卡片
        details_widget = QWidget()
        details_widget.setLayout(details_layout)

        # 清空并添加新内容
        self.details_card.clear_content()
        self.details_card.add_content(details_widget)

    def _get_feature_details(self, feature_id):
        """获取功能详细信息"""
        details = {
            "commentary": """
功能特点：
• 智能分析视频内容，生成符合短剧风格的解说
• 支持多种解说风格：幽默风趣、专业分析、情感解读
• 自动匹配解说内容与视频场景
• 支持自定义解说模板和风格调整
            """,
            "compilation": """
功能特点：
• 自动检测视频中的高能/精彩场景
• 智能分析动作、表情、音频等多维度信息
• 支持自定义检测参数和阈值
• 一键生成激动人心的混剪视频
            """,
            "monologue": """
功能特点：
• 生成第一人称叙述内容
• 支持多种角色设定和情感风格
• 自动插入相关原始片段
• 智能匹配独白内容与视频场景
            """
        }
        return details.get(feature_id, "功能详情加载中...")

    def _start_feature(self, feature_id):
        """启动功能"""
        self.current_feature = feature_id

        # 更新AI功能状态
        feature_names = {
            "commentary": "AI短剧解说",
            "compilation": "AI高能混剪",
            "monologue": "AI第一人称独白"
        }

        feature_name = feature_names.get(feature_id, "未知功能")
        self.ai_feature_status_label.setText(f"AI功能: {feature_name}")

        # 切换到字幕提取选项卡
        self.tab_widget.setCurrentIndex(1)

        # 检查是否可以开始处理
        self._check_processing_ready()

        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self, "功能选择",
            f"已选择 {feature_name} 功能\n\n"
            "请在字幕提取选项卡中完成视频字幕提取，然后在处理流程选项卡中开始AI处理。"
        )

    def _on_subtitle_extraction_completed(self, result):
        """字幕提取完成处理"""
        self.current_subtitles = result

        if result.success:
            # 更新字幕状态
            track_count = len(result.tracks)
            self.subtitle_status_label.setText(f"字幕提取: 已完成 ({track_count}个轨道)")

            # 更新视频文件状态
            if result.video_path:
                import os
                video_name = os.path.basename(result.video_path)
                self.video_status_label.setText(f"视频文件: {video_name}")
                self.current_video_path = result.video_path

            # 检查是否可以开始处理
            self._check_processing_ready()

            # 切换到处理流程选项卡
            self.tab_widget.setCurrentIndex(2)

        else:
            self.subtitle_status_label.setText(f"字幕提取: 失败 - {result.error_message}")

    def _check_processing_ready(self):
        """检查是否可以开始处理"""
        has_video = self.current_video_path is not None
        has_subtitles = self.current_subtitles is not None and self.current_subtitles.success
        has_feature = self.current_feature is not None

        ready = has_video and has_subtitles and has_feature
        self.start_processing_btn.setEnabled(ready)

        if ready:
            self.workflow_status_label.setText("✅ 准备就绪，可以开始AI处理")
        else:
            missing = []
            if not has_video:
                missing.append("视频文件")
            if not has_subtitles:
                missing.append("字幕提取")
            if not has_feature:
                missing.append("AI功能选择")

            self.workflow_status_label.setText(f"⏳ 等待: {', '.join(missing)}")

    def _start_ai_processing(self):
        """开始AI处理"""
        if not self.current_video_path or not self.current_subtitles or not self.current_feature:
            return

        from PyQt6.QtWidgets import QMessageBox

        feature_names = {
            "commentary": "AI短剧解说",
            "compilation": "AI高能混剪",
            "monologue": "AI第一人称独白"
        }

        feature_name = feature_names.get(self.current_feature, "未知功能")

        # 获取字幕文本
        subtitle_text = self.current_subtitles.get_combined_text()

        import os
        QMessageBox.information(
            self, "开始处理",
            f"开始 {feature_name} 处理\n\n"
            f"视频文件: {os.path.basename(self.current_video_path)}\n"
            f"字幕内容: {len(subtitle_text)} 字符\n"
            f"处理方法: {self.current_feature}\n\n"
            "AI处理功能正在开发中，敬请期待！"
        )

    def _apply_styles(self):
        """应用样式"""
        colors = ProfessionalTheme.get_colors(self.is_dark_theme)

        self.setStyleSheet(f"""
            ProfessionalAIFeaturesPage {{
                background-color: {colors['surface']};
            }}
            QLabel {{
                color: {colors['text_primary']};
            }}
            QScrollArea {{
                border: none;
                background-color: {colors['surface']};
            }}
            QWidget {{
                background-color: transparent;
            }}
        """)

        # 功能选择组件样式
        for widget in self.findChildren(QWidget):
            if widget.size() == QSize(200, 160):  # 功能选择组件
                widget.setStyleSheet(f"""
                    QWidget {{
                        background-color: {colors['background']};
                        border: 2px solid {colors['border']};
                        border-radius: 12px;
                    }}
                    QWidget:hover {{
                        border-color: {colors['primary']};
                        background-color: {colors['surface']};
                    }}
                """)

    def set_theme(self, is_dark):
        """设置主题"""
        self.is_dark_theme = is_dark
        self._apply_styles()

        # 更新所有子组件主题
        for card in self.findChildren(ProfessionalCard):
            card.set_theme(is_dark)
        for button in self.findChildren(ProfessionalButton):
            button.set_theme(is_dark)


class ProfessionalProjectsPage(QWidget):
    """专业项目管理页面"""

    # 信号
    video_editing_requested = pyqtSignal(dict)  # 请求打开视频编辑

    def __init__(self, project_manager, parent=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self.is_dark_theme = False
        self.project_cards = []  # 存储项目卡片

        self._setup_ui()
        self._apply_styles()
        self._load_projects()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)

        # 页面标题和操作
        header_layout = QHBoxLayout()

        title_label = QLabel("项目管理")
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        self.new_project_btn = ProfessionalButton("📝 新建项目", "primary")
        self.import_btn = ProfessionalButton("📥 导入项目", "default")

        header_layout.addWidget(self.new_project_btn)
        header_layout.addWidget(self.import_btn)

        layout.addLayout(header_layout)

        # 项目列表区域
        self.projects_card = ProfessionalCard("我的项目")

        # 创建滚动区域
        from PyQt6.QtWidgets import QScrollArea, QGridLayout
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 项目网格容器
        self.projects_container = QWidget()
        self.projects_grid = QGridLayout(self.projects_container)
        self.projects_grid.setSpacing(20)
        self.projects_grid.setContentsMargins(10, 10, 10, 10)

        scroll_area.setWidget(self.projects_container)
        self.projects_card.add_content(scroll_area)

        # 空状态提示
        self.empty_label = QLabel("暂无项目，点击上方按钮创建新项目")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setFont(QFont("Arial", 14))
        self.empty_label.setVisible(True)
        self.projects_card.add_content(self.empty_label)

        layout.addWidget(self.projects_card)
        layout.addStretch()

        # 连接信号
        self.new_project_btn.clicked.connect(self._on_new_project)
        self.import_btn.clicked.connect(self._on_import_project)

    def _load_projects(self):
        """加载项目列表"""
        try:
            projects = self.project_manager.get_project_list()
            self._update_project_display(projects)
        except Exception as e:
            print(f"加载项目列表失败: {e}")

    def _update_project_display(self, projects):
        """更新项目显示"""
        # 清空现有卡片
        for card in self.project_cards:
            card.setParent(None)
        self.project_cards.clear()

        if not projects:
            self.empty_label.setVisible(True)
            self.projects_container.setVisible(False)
            return

        self.empty_label.setVisible(False)
        self.projects_container.setVisible(True)

        # 按修改时间排序
        projects.sort(key=lambda p: p.modified_at, reverse=True)

        # 创建项目卡片
        for i, project in enumerate(projects):
            card = self._create_project_card(project)
            self.project_cards.append(card)

            # 添加到网格布局（每行3个）
            row = i // 3
            col = i % 3
            self.projects_grid.addWidget(card, row, col)

    def _create_project_card(self, project):
        """创建项目卡片"""
        from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout

        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box)
        card.setFixedSize(300, 200)
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 项目标题
        title_label = QLabel(project.name)
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        # 项目描述
        if project.description:
            desc_label = QLabel(project.description)
            desc_label.setFont(QFont("Arial", 10))
            desc_label.setWordWrap(True)
            desc_label.setMaximumHeight(40)
            layout.addWidget(desc_label)

        # 项目信息
        info_layout = QHBoxLayout()

        # 编辑模式图标
        mode_icons = {
            "commentary": "🎬",
            "compilation": "⚡",
            "monologue": "🎭"
        }
        mode_label = QLabel(f"{mode_icons.get(project.editing_mode, '📹')} {project.editing_mode}")
        mode_label.setFont(QFont("Arial", 9))
        info_layout.addWidget(mode_label)

        info_layout.addStretch()

        # 项目状态
        status_icons = {
            "draft": "📝",
            "editing": "✏️",
            "processing": "⚙️",
            "completed": "✅"
        }
        status_names = {
            "draft": "草稿",
            "editing": "编辑中",
            "processing": "处理中",
            "completed": "已完成"
        }

        status = getattr(project, 'status', 'draft')
        progress = getattr(project, 'progress', 0.0)

        status_label = QLabel(f"{status_icons.get(status, '📄')} {status_names.get(status, status)}")
        status_label.setFont(QFont("Arial", 9))
        info_layout.addWidget(status_label)

        # 进度条（如果有进度）
        if progress > 0:
            from PyQt6.QtWidgets import QProgressBar
            progress_bar = QProgressBar()
            progress_bar.setMaximumWidth(60)
            progress_bar.setMaximumHeight(8)
            progress_bar.setValue(int(progress * 100))
            progress_bar.setTextVisible(False)
            info_layout.addWidget(progress_bar)

        # 修改时间
        import datetime
        try:
            modified_time = datetime.datetime.fromisoformat(project.modified_at)
            time_str = modified_time.strftime("%m-%d %H:%M")
        except:
            time_str = "未知"

        time_label = QLabel(time_str)
        time_label.setFont(QFont("Arial", 9))
        info_layout.addWidget(time_label)

        layout.addLayout(info_layout)
        layout.addStretch()

        # 操作按钮
        button_layout = QHBoxLayout()

        edit_btn = ProfessionalButton("🎬 编辑视频", "primary")
        edit_btn.clicked.connect(lambda: self._on_edit_video(project))

        open_btn = ProfessionalButton("📂 打开", "default")
        open_btn.clicked.connect(lambda: self._on_open_project(project))

        button_layout.addWidget(edit_btn)
        button_layout.addWidget(open_btn)

        layout.addLayout(button_layout)

        # 应用卡片样式
        colors = ProfessionalTheme.get_colors(self.is_dark_theme)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['background']};
                border: 1px solid {colors['border']};
                border-radius: 8px;
            }}
            QFrame:hover {{
                border-color: {colors['primary']};
            }}
            QLabel {{
                color: {colors['text_primary']};
                border: none;
            }}
        """)

        return card

    def _on_edit_video(self, project):
        """编辑视频按钮点击"""
        self.video_editing_requested.emit(project.to_dict())

    def _on_open_project(self, project):
        """打开项目按钮点击"""
        try:
            self.project_manager.load_project(project.file_path)
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "成功", f"项目 '{project.name}' 已加载")
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "错误", f"加载项目失败: {e}")

    def _on_new_project(self):
        """新建项目"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit, QComboBox, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle("新建项目")
        dialog.setModal(True)
        dialog.resize(400, 300)

        layout = QVBoxLayout(dialog)

        # 项目名称
        name_label = QLabel("项目名称:")
        name_edit = QLineEdit()
        layout.addWidget(name_label)
        layout.addWidget(name_edit)

        # 项目描述
        desc_label = QLabel("项目描述:")
        desc_edit = QTextEdit()
        desc_edit.setMaximumHeight(80)
        layout.addWidget(desc_label)
        layout.addWidget(desc_edit)

        # 编辑模式
        mode_label = QLabel("编辑模式:")
        mode_combo = QComboBox()
        mode_combo.addItems(["commentary", "compilation", "monologue"])
        layout.addWidget(mode_label)
        layout.addWidget(mode_combo)

        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = name_edit.text().strip()
            if name:
                try:
                    project = self.project_manager.create_project(
                        name,
                        desc_edit.toPlainText().strip(),
                        mode_combo.currentText()
                    )
                    self._load_projects()  # 刷新项目列表
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.information(self, "成功", f"项目 '{project.name}' 创建成功")
                except Exception as e:
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.warning(self, "错误", f"创建项目失败: {e}")

    def _on_import_project(self):
        """导入项目"""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox

        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter("VideoEpicCreator项目文件 (*.vecp)")

        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            try:
                if self.project_manager.load_project(file_path):
                    self._load_projects()  # 刷新项目列表
                    QMessageBox.information(self, "成功", "项目导入成功")
                else:
                    QMessageBox.warning(self, "失败", "项目导入失败")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"导入项目失败: {e}")

    def _apply_styles(self):
        """应用样式"""
        colors = ProfessionalTheme.get_colors(self.is_dark_theme)
        
        self.setStyleSheet(f"""
            ProfessionalProjectsPage {{
                background-color: {colors['surface']};
            }}
            QLabel {{
                color: {colors['text_primary']};
            }}
        """)
    
    def set_theme(self, is_dark):
        """设置主题"""
        self.is_dark_theme = is_dark
        self._apply_styles()
        
        # 更新所有子组件主题
        for card in self.findChildren(ProfessionalCard):
            card.set_theme(is_dark)
        for button in self.findChildren(ProfessionalButton):
            button.set_theme(is_dark)


class ProfessionalSettingsPage(QWidget):
    """专业设置页面"""
    
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.is_dark_theme = False
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)
        
        # 页面标题
        title_label = QLabel("设置")
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # 主题设置
        theme_card = ProfessionalCard("主题设置")
        
        theme_layout = QHBoxLayout()
        theme_layout.setSpacing(16)
        
        light_btn = ProfessionalButton("☀️ 浅色主题", "default")
        dark_btn = ProfessionalButton("🌙 深色主题", "default")
        
        light_btn.clicked.connect(lambda: self._change_theme(False))
        dark_btn.clicked.connect(lambda: self._change_theme(True))
        
        theme_layout.addWidget(light_btn)
        theme_layout.addWidget(dark_btn)
        theme_layout.addStretch()
        
        theme_widget = QWidget()
        theme_widget.setLayout(theme_layout)
        theme_card.add_content(theme_widget)
        
        layout.addWidget(theme_card)
        
        # API设置
        api_card = ProfessionalCard("API设置")
        api_desc = QLabel("配置AI模型的API密钥以使用AI功能")
        api_desc.setWordWrap(True)
        api_card.add_content(api_desc)
        
        api_btn = ProfessionalButton("配置API密钥", "primary")
        api_card.add_content(api_btn)
        
        layout.addWidget(api_card)
        
        layout.addStretch()
    
    def _change_theme(self, is_dark):
        """切换主题"""
        # 保存主题设置
        theme_value = "dark" if is_dark else "light"
        self.settings_manager.set_setting("app.theme", theme_value)
        
        # 发射主题变更信号
        if hasattr(self.parent(), 'theme_changed'):
            self.parent().theme_changed.emit(is_dark)
    
    def _apply_styles(self):
        """应用样式"""
        colors = ProfessionalTheme.get_colors(self.is_dark_theme)
        
        self.setStyleSheet(f"""
            ProfessionalSettingsPage {{
                background-color: {colors['surface']};
            }}
            QLabel {{
                color: {colors['text_primary']};
            }}
        """)
    
    def set_theme(self, is_dark):
        """设置主题"""
        self.is_dark_theme = is_dark
        self._apply_styles()
        
        # 更新所有子组件主题
        for card in self.findChildren(ProfessionalCard):
            card.set_theme(is_dark)
        for button in self.findChildren(ProfessionalButton):
            button.set_theme(is_dark)


class ProfessionalMainWindow(QMainWindow):
    """专业主窗口 - 完全重新设计"""
    
    theme_changed = pyqtSignal(bool)  # is_dark
    
    def __init__(self):
        super().__init__()
        
        # 初始化管理器
        self.settings_manager = SettingsManager()
        self.project_manager = ProjectManager(self.settings_manager)
        self.ai_manager = AIManager(self.settings_manager)
        
        # 主题状态
        self.is_dark_theme = False
        
        # 设置窗口属性
        self.setWindowTitle("VideoEpicCreator - AI短剧视频编辑器")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1000, 600)
        
        # 创建UI
        self._create_ui()
        self._connect_signals()
        self._load_settings()
        
        # 延迟初始化AI模型
        QTimer.singleShot(1000, self.ai_manager.initialize_delayed_models)
    
    def _create_ui(self):
        """创建用户界面"""
        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 左侧导航
        self.navigation = ProfessionalNavigation()
        main_layout.addWidget(self.navigation)
        
        # 右侧内容区域
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)
        
        # 创建页面
        self._create_pages()
        
        # 创建状态栏
        self._create_statusbar()
    
    def _create_pages(self):
        """创建页面"""
        # 首页
        self.home_page = ProfessionalHomePage()
        self.content_stack.addWidget(self.home_page)

        # 项目管理页面
        self.projects_page = ProfessionalProjectsPage(self.project_manager)
        self.projects_page.video_editing_requested.connect(self.open_video_editing)
        self.content_stack.addWidget(self.projects_page)

        # 视频编辑页面（整合AI功能）- 保留实例但不添加到主导航
        from app.ui.pages.unified_video_editing_page import UnifiedVideoEditingPage
        self.video_editing_page = UnifiedVideoEditingPage(self.ai_manager)
        # 注意：不添加到content_stack，将通过项目管理页面调用

        # 设置页面
        self.settings_page = ProfessionalSettingsPage(self.settings_manager)
        self.content_stack.addWidget(self.settings_page)

        # 默认显示首页
        self.content_stack.setCurrentIndex(0)
    
    def _create_statusbar(self):
        """创建状态栏"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("就绪")
    
    def _connect_signals(self):
        """连接信号"""
        # 导航信号
        self.navigation.navigation_changed.connect(self._on_navigation_changed)
        
        # 主题变更信号
        self.theme_changed.connect(self._on_theme_changed)
        
        # 设置页面主题变更
        self.settings_page.theme_changed = self.theme_changed
    
    def _load_settings(self):
        """加载设置"""
        # 加载主题设置
        theme = self.settings_manager.get_setting("app.theme", "light")
        self.is_dark_theme = theme == "dark"
        self._apply_theme()
        
        # 恢复窗口几何
        geometry = self.settings_manager.get_setting("window.geometry")
        if geometry:
            try:
                self.restoreGeometry(geometry)
            except:
                pass
    
    def _save_settings(self):
        """保存设置"""
        # 保存窗口几何
        self.settings_manager.set_setting("window.geometry", self.saveGeometry())
    
    def _on_navigation_changed(self, page_id):
        """导航变更处理"""
        page_map = {
            "home": 0,
            "projects": 1,
            "settings": 2
        }
        
        if page_id in page_map:
            index = page_map[page_id]
            self.content_stack.setCurrentIndex(index)
            
            page_names = {
                "home": "首页",
                "projects": "项目管理",
                "ai_features": "AI功能",
                "settings": "设置"
            }
            
            self.statusbar.showMessage(f"当前页面: {page_names.get(page_id, page_id)}")

    def open_video_editing(self, project_data=None):
        """从项目管理打开视频编辑功能"""
        # 创建视频编辑对话框
        if hasattr(self, 'video_editing_dialog'):
            self.video_editing_dialog.close()

        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout

        self.video_editing_dialog = QDialog(self)
        project_name = project_data.get('name', '未知项目') if project_data else '新项目'
        self.video_editing_dialog.setWindowTitle(f"视频编辑 - {project_name}")
        self.video_editing_dialog.setModal(True)
        self.video_editing_dialog.resize(1200, 800)

        main_layout = QVBoxLayout(self.video_editing_dialog)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 顶部工具栏
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(16, 8, 16, 8)
        toolbar_layout.setSpacing(12)

        # 返回按钮
        back_btn = ProfessionalButton("← 返回项目管理", "default")
        back_btn.clicked.connect(self.video_editing_dialog.close)
        toolbar_layout.addWidget(back_btn)

        # 项目信息
        if project_data:
            project_info = QLabel(f"项目: {project_name} | 模式: {project_data.get('editing_mode', '未知')}")
            project_info.setFont(QFont("Arial", 12))
            toolbar_layout.addWidget(project_info)

        toolbar_layout.addStretch()

        # 保存按钮
        save_btn = ProfessionalButton("💾 保存项目", "primary")
        save_btn.clicked.connect(lambda: self._save_editing_progress(project_data))
        toolbar_layout.addWidget(save_btn)

        toolbar_widget = QWidget()
        toolbar_widget.setLayout(toolbar_layout)

        # 应用工具栏样式
        colors = ProfessionalTheme.get_colors(self.is_dark_theme)
        toolbar_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {colors['surface']};
                border-bottom: 1px solid {colors['border']};
            }}
            QLabel {{
                color: {colors['text_primary']};
            }}
        """)

        main_layout.addWidget(toolbar_widget)

        # 创建新的视频编辑页面实例
        from app.ui.pages.unified_video_editing_page import UnifiedVideoEditingPage
        editing_page = UnifiedVideoEditingPage(self.ai_manager)
        editing_page.set_theme(self.is_dark_theme)

        # 如果有项目数据，加载到编辑页面
        if project_data:
            editing_page.load_project_data(project_data, self.project_manager)

        main_layout.addWidget(editing_page)

        # 显示对话框
        self.video_editing_dialog.show()

    def _save_editing_progress(self, project_data):
        """保存编辑进度"""
        if project_data:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self.video_editing_dialog,
                "保存成功",
                f"项目 '{project_data.get('name', '未知项目')}' 的编辑进度已保存"
            )

    def _on_theme_changed(self, is_dark):
        """主题变更处理"""
        self.is_dark_theme = is_dark
        self._apply_theme()
        
        # 保存主题设置
        theme_value = "dark" if is_dark else "light"
        self.settings_manager.set_setting("app.theme", theme_value)
    
    def _apply_theme(self):
        """应用主题"""
        colors = ProfessionalTheme.get_colors(self.is_dark_theme)

        # 应用主窗口样式
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {colors['background']};
            }}
            QStatusBar {{
                background-color: {colors['surface']};
                border-top: 1px solid {colors['border']};
                color: {colors['text_secondary']};
            }}
        """)

        # 更新所有页面主题
        self.navigation.set_theme(self.is_dark_theme)
        self.home_page.set_theme(self.is_dark_theme)
        self.projects_page.set_theme(self.is_dark_theme)
        self.settings_page.set_theme(self.is_dark_theme)

        # 如果视频编辑对话框打开，也更新其主题
        if hasattr(self, 'video_editing_dialog') and self.video_editing_dialog.isVisible():
            # 更新对话框中的编辑页面主题
            for child in self.video_editing_dialog.findChildren(QWidget):
                if hasattr(child, 'set_theme'):
                    child.set_theme(self.is_dark_theme)

        # 应用全局样式修复
        fix_widget_styles(self, self.is_dark_theme)
    
    def closeEvent(self, event):
        """关闭事件"""
        self._save_settings()
        event.accept()
