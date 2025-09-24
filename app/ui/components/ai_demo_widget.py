#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI功能演示组件
展示AI功能的实际使用效果
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
    QListWidget, QListWidgetItem, QSizePolicy, QSpacerItem,
    QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize, QThread, pyqtSlot
from PyQt6.QtGui import QIcon, QFont, QPalette, QColor, QPixmap

from ...core.config_manager import ConfigManager
from ...core.logger import Logger
from ...core.icon_manager import get_icon
from ...services.ai_service_manager import AIServiceManager
from ...services.chinese_ai_services import ChineseAIServiceFactory


class AIDemoWidget(QWidget):
    """AI功能演示组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("aiDemoWidget")

        # 初始化组件
        self.config_manager = ConfigManager()
        self.logger = Logger("AIDemoWidget")
        self.ai_service_manager = AIServiceManager(self.logger)

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

        # 演示内容区域
        demo_tabs = QTabWidget()
        demo_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #e9ecef;
                border-radius: 8px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #1890ff;
            }
        """)

        # 脚本生成演示
        script_tab = self._create_script_demo_tab()
        demo_tabs.addTab(script_tab, "脚本生成")

        # 字幕生成演示
        subtitle_tab = self._create_subtitle_demo_tab()
        demo_tabs.addTab(subtitle_tab, "字幕生成")

        # 标题生成演示
        title_tab = self._create_title_demo_tab()
        demo_tabs.addTab(title_tab, "标题生成")

        # 内容分析演示
        analysis_tab = self._create_analysis_demo_tab()
        demo_tabs.addTab(analysis_tab, "内容分析")

        layout.addWidget(demo_tabs)

    def _create_title_section(self) -> QWidget:
        """创建标题区域"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # 图标和标题
        icon_label = QLabel()
        icon_label.setPixmap(get_icon("ai", 48).pixmap(48, 48))
        layout.addWidget(icon_label)

        title_layout = QVBoxLayout()
        title_label = QLabel("AI功能演示")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        title_layout.addWidget(title_label)

        desc_label = QLabel("体验AI驱动的视频内容生成和分析功能")
        desc_label.setStyleSheet("color: #666; font-size: 14px;")
        title_layout.addWidget(desc_label)

        layout.addLayout(title_layout)
        layout.addStretch()

        return widget

    def _create_script_demo_tab(self) -> QWidget:
        """创建脚本生成演示选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 输入区域
        input_group = QGroupBox("输入视频主题")
        input_group.setStyleSheet("""
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
        input_layout = QVBoxLayout(input_group)

        self.script_topic_input = QLineEdit()
        self.script_topic_input.setPlaceholderText("例如：制作一个关于AI技术科普的短视频")
        input_layout.addWidget(self.script_topic_input)

        # 参数选择
        param_layout = QHBoxLayout()
        param_layout.addWidget(QLabel("视频风格:"))

        self.script_style_combo = QComboBox()
        self.script_style_combo.addItems(["科普教育", "生活记录", "产品介绍", "教程演示", "娱乐搞笑"])
        param_layout.addWidget(self.script_style_combo)

        param_layout.addWidget(QLabel("时长:"))

        self.script_duration_combo = QComboBox()
        self.script_duration_combo.addItems(["1分钟以内", "1-3分钟", "3-5分钟", "5分钟以上"])
        param_layout.addWidget(self.script_duration_combo)

        param_layout.addStretch()
        input_layout.addLayout(param_layout)

        layout.addWidget(input_group)

        # 生成按钮
        self.script_generate_btn = QPushButton(get_icon("magic", 16), "生成脚本")
        self.script_generate_btn.setFixedSize(120, 36)
        self.script_generate_btn.clicked.connect(self._generate_script_demo)
        layout.addWidget(self.script_generate_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # 结果显示
        result_group = QGroupBox("生成的脚本")
        result_group.setStyleSheet(input_group.styleSheet())
        result_layout = QVBoxLayout(result_group)

        self.script_result_text = QTextEdit()
        self.script_result_text.setReadOnly(True)
        self.script_result_text.setMinimumHeight(200)
        self.script_result_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 15px;
                font-family: 'Courier New', monospace;
                font-size: 13px;
            }
        """)
        result_layout.addWidget(self.script_result_text)

        layout.addWidget(result_group)

        # 示例脚本
        example_group = QGroupBox("示例脚本")
        example_group.setStyleSheet(input_group.styleSheet())
        example_layout = QVBoxLayout(example_group)

        example_text = """
【开场】
大家好！今天我们来聊聊人工智能这个热门话题。

【主体】
AI技术正在改变我们的生活，从智能手机到自动驾驶，
从语音助手到医疗诊断，AI无处不在。

【结尾】
希望这个视频帮助大家更好地了解AI技术。
如果喜欢，请点赞关注！
        """
        example_label = QLabel(example_text.strip())
        example_label.setStyleSheet("""
            QLabel {
                background-color: #f0f8ff;
                border: 1px solid #b8daff;
                border-radius: 4px;
                padding: 15px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                color: #495057;
            }
        """)
        example_layout.addWidget(example_label)

        layout.addWidget(example_group)

        layout.addStretch()

        return widget

    def _create_subtitle_demo_tab(self) -> QWidget:
        """创建字幕生成演示选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 输入区域
        input_group = QGroupBox("输入视频内容")
        input_group.setStyleSheet("""
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
        input_layout = QVBoxLayout(input_group)

        self.subtitle_content_input = QTextEdit()
        self.subtitle_content_input.setPlaceholderText("请输入视频的音频内容或对话...")
        self.subtitle_content_input.setMaximumHeight(100)
        input_layout.addWidget(self.subtitle_content_input)

        layout.addWidget(input_group)

        # 生成按钮
        self.subtitle_generate_btn = QPushButton(get_icon("caption", 16), "生成字幕")
        self.subtitle_generate_btn.setFixedSize(120, 36)
        self.subtitle_generate_btn.clicked.connect(self._generate_subtitle_demo)
        layout.addWidget(self.subtitle_generate_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # 字幕格式选择
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("字幕格式:"))

        self.subtitle_format_combo = QComboBox()
        self.subtitle_format_combo.addItems(["SRT格式", "ASS格式", "纯文本"])
        format_layout.addWidget(self.subtitle_format_combo)

        format_layout.addStretch()
        layout.addLayout(format_layout)

        # 结果显示
        result_group = QGroupBox("生成的字幕")
        result_group.setStyleSheet(input_group.styleSheet())
        result_layout = QVBoxLayout(result_group)

        self.subtitle_result_text = QTextEdit()
        self.subtitle_result_text.setReadOnly(True)
        self.subtitle_result_text.setMinimumHeight(150)
        self.subtitle_result_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 15px;
                font-family: 'Courier New', monospace;
                font-size: 13px;
            }
        """)
        result_layout.addWidget(self.subtitle_result_text)

        layout.addWidget(result_group)

        layout.addStretch()

        return widget

    def _create_title_demo_tab(self) -> QWidget:
        """创建标题生成演示选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 输入区域
        input_group = QGroupBox("输入视频描述")
        input_group.setStyleSheet("""
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
        input_layout = QVBoxLayout(input_group)

        self.title_desc_input = QTextEdit()
        self.title_desc_input.setPlaceholderText("请描述视频的主要内容、特点、目标受众等...")
        self.title_desc_input.setMaximumHeight(80)
        input_layout.addWidget(self.title_desc_input)

        layout.addWidget(input_group)

        # 生成按钮
        self.title_generate_btn = QPushButton(get_icon("title", 16), "生成标题")
        self.title_generate_btn.setFixedSize(120, 36)
        self.title_generate_btn.clicked.connect(self._generate_title_demo)
        layout.addWidget(self.title_generate_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # 结果显示
        result_group = QGroupBox("生成的标题")
        result_group.setStyleSheet(input_group.styleSheet())
        result_layout = QVBoxLayout(result_group)

        self.title_result_list = QListWidget()
        self.title_result_list.setMaximumHeight(150)
        self.title_result_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e9ecef;
                border-radius: 4px;
                background-color: #f8f9fa;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #e9ecef;
            }
            QListWidget::item:hover {
                background-color: #e6f7ff;
            }
        """)
        result_layout.addWidget(self.title_result_list)

        layout.addWidget(result_group)

        layout.addStretch()

        return widget

    def _create_analysis_demo_tab(self) -> QWidget:
        """创建内容分析演示选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 分析类型选择
        type_group = QGroupBox("选择分析类型")
        type_group.setStyleSheet("""
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
        type_layout = QVBoxLayout(type_group)

        self.analysis_type_group = QButtonGroup(self)

        scene_radio = QRadioButton("场景检测")
        scene_radio.setChecked(True)
        self.analysis_type_group.addButton(scene_radio, 1)
        type_layout.addWidget(scene_radio)

        content_radio = QRadioButton("内容分析")
        self.analysis_type_group.addButton(content_radio, 2)
        type_layout.addWidget(content_radio)

        highlight_radio = QRadioButton("高光时刻")
        self.analysis_type_group.addButton(highlight_radio, 3)
        type_layout.addWidget(highlight_radio)

        layout.addWidget(type_group)

        # 视频信息输入
        info_group = QGroupBox("视频信息")
        info_group.setStyleSheet(type_group.styleSheet())
        info_layout = QFormLayout(info_group)

        self.video_duration_spin = QSpinBox()
        self.video_duration_spin.setRange(1, 3600)
        self.video_duration_spin.setValue(180)
        self.video_duration_spin.setSuffix(" 秒")
        info_layout.addRow("视频时长:", self.video_duration_spin)

        self.video_desc_edit = QLineEdit()
        self.video_desc_edit.setPlaceholderText("简要描述视频内容")
        info_layout.addRow("视频描述:", self.video_desc_edit)

        layout.addWidget(info_group)

        # 分析按钮
        self.analysis_btn = QPushButton(get_icon("analysis", 16), "开始分析")
        self.analysis_btn.setFixedSize(120, 36)
        self.analysis_btn.clicked.connect(self._generate_analysis_demo)
        layout.addWidget(self.analysis_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # 结果显示
        result_group = QGroupBox("分析结果")
        result_group.setStyleSheet(type_group.styleSheet())
        result_layout = QVBoxLayout(result_group)

        self.analysis_result_text = QTextEdit()
        self.analysis_result_text.setReadOnly(True)
        self.analysis_result_text.setMinimumHeight(200)
        self.analysis_result_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 15px;
                font-size: 13px;
            }
        """)
        result_layout.addWidget(self.analysis_result_text)

        layout.addWidget(result_group)

        layout.addStretch()

        return widget

    def _setup_connections(self):
        """设置信号连接"""
        pass

    def _load_ai_config(self):
        """加载AI配置"""
        try:
            configured_models = self.ai_service_manager.get_configured_models()
            has_ai_config = any(configured_models.values())

            if not has_ai_config:
                # 显示提示
                self._show_ai_config_hint()

        except Exception as e:
            self.logger.error(f"加载AI配置失败: {e}")

    def _show_ai_config_hint(self):
        """显示AI配置提示"""
        try:
            hint_layout = QVBoxLayout()
            hint_layout.setContentsMargins(20, 20, 20, 20)

            hint_label = QLabel(
                "⚠️ 您还未配置AI服务，请先配置AI服务后再使用演示功能。\n\n"
                "配置步骤：\n"
                "1. 点击'AI配置'按钮\n"
                "2. 选择AI服务提供商\n"
                "3. 申请并配置API密钥\n"
                "4. 测试连接"
            )
            hint_label.setStyleSheet("""
                QLabel {
                    color: #ff9800;
                    font-size: 14px;
                    padding: 15px;
                    background-color: #fff3e0;
                    border: 1px solid #ffcc02;
                    border-radius: 8px;
                }
            """)
            hint_label.setWordWrap(True)
            hint_layout.addWidget(hint_label)

            # 添加配置按钮
            config_btn = QPushButton(get_icon("settings", 16), "去配置AI服务")
            config_btn.setFixedSize(150, 36)
            config_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1890ff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #40a9ff;
                }
            """)
            hint_layout.addWidget(config_btn, alignment=Qt.AlignmentFlag.AlignCenter)

            # 将提示添加到每个选项卡
            for i in range(4):
                tab = self.parent().findChild(QTabWidget).widget(i)
                if tab:
                    tab.layout().insertLayout(0, hint_layout)

        except Exception as e:
            self.logger.error(f"显示AI配置提示失败: {e}")

    def _generate_script_demo(self):
        """生成脚本演示"""
        try:
            topic = self.script_topic_input.text().strip()
            if not topic:
                QMessageBox.warning(self, "提示", "请输入视频主题")
                return

            style = self.script_style_combo.currentText()
            duration = self.script_duration_combo.currentText()

            # 模拟AI生成脚本
            script = self._generate_sample_script(topic, style, duration)
            self.script_result_text.setText(script)

        except Exception as e:
            self.logger.error(f"生成脚本演示失败: {e}")
            QMessageBox.critical(self, "错误", f"生成失败: {e}")

    def _generate_sample_script(self, topic: str, style: str, duration: str) -> str:
        """生成示例脚本"""
        scripts = {
            "科普教育": f"""
【开场】
大家好！欢迎来到今天的科普时间。今天我们要聊的主题是：{topic}。

【主体】
{topic}是现代科技发展的重要成果。它不仅在实验室中展现出巨大的潜力，
更在日常生活中给我们带来了诸多便利。

通过深入浅出的讲解，希望能够帮助大家更好地理解{topic}的工作原理
和应用场景。

【结尾】
科技改变生活，知识照亮未来。感谢大家的观看，我们下期再见！

【互动提示】
如果觉得有用，请点赞关注！有疑问欢迎在评论区留言讨论。
            """,
            "生活记录": f"""
【开场】
哈喽大家好！今天想和大家分享一下关于{topic}的一些心得体会。

【主体】
最近在体验{topic}的过程中，发现它真的很有意思。
从一开始的好奇，到现在的逐渐熟悉，这个过程中有很多值得分享的点。

{topic}给我的生活带来了很多变化，无论是在工作效率还是生活品质上，
都能感受到它带来的便利。

【结尾】
这就是今天想和大家分享的内容，希望对大家有所帮助。
生活就是这样，在尝试和体验中不断成长。

【互动提示】
大家有什么想了解的，欢迎在评论区告诉我哦！
            """,
            "产品介绍": f"""
【开场】
大家好！今天给大家介绍一款非常实用的产品：{topic}。

【产品特点】
{topic}具有以下几个显著特点：
1. 设计简洁美观，使用体验流畅
2. 功能强大，满足多种需求
3. 性价比高，值得信赖

【使用场景】
无论是日常工作还是生活娱乐，{topic}都能为你提供优质的服务。
特别适合现代快节奏的生活方式。

【结尾】
如果你也在寻找这样一款产品，不妨考虑一下{topic}。
相信它会成为你的得力助手！

【购买提示】
感兴趣的朋友可以点击下方链接了解更多详情。
            """
        }

        return scripts.get(style, scripts["科普教育"])

    def _generate_subtitle_demo(self):
        """生成字幕演示"""
        try:
            content = self.subtitle_content_input.toPlainText().strip()
            if not content:
                content = "大家好！今天我们来聊聊人工智能这个话题。AI技术正在改变我们的生活，从智能手机到自动驾驶，从语音助手到医疗诊断，AI无处不在。希望这个视频帮助大家更好地了解AI技术。如果喜欢，请点赞关注！"

            # 模拟字幕生成
            subtitles = self._generate_sample_subtitles(content)
            self.subtitle_result_text.setText(subtitles)

        except Exception as e:
            self.logger.error(f"生成字幕演示失败: {e}")
            QMessageBox.critical(self, "错误", f"生成失败: {e}")

    def _generate_sample_subtitles(self, content: str) -> str:
        """生成示例字幕"""
        # 简单的字幕生成逻辑
        sentences = content.split('。')
        sentences = [s.strip() for s in sentences if s.strip()]

        subtitles = []
        for i, sentence in enumerate(sentences):
            start_time = i * 3
            end_time = start_time + 2
            subtitles.append(f"{i+1}\n00:00:{start_time:02d},000 --> 00:00:{end_time:02d},000\n{sentence}\n")

        return '\n'.join(subtitles)

    def _generate_title_demo(self):
        """生成标题演示"""
        try:
            desc = self.title_desc_input.toPlainText().strip()
            if not desc:
                desc = "介绍AI技术的科普视频"

            # 模拟标题生成
            titles = self._generate_sample_titles(desc)
            self.title_result_list.clear()

            for title in titles:
                item = QListWidgetItem(title)
                self.title_result_list.addItem(item)

        except Exception as e:
            self.logger.error(f"生成标题演示失败: {e}")
            QMessageBox.critical(self, "错误", f"生成失败: {e}")

    def _generate_sample_titles(self, desc: str) -> List[str]:
        """生成示例标题"""
        return [
            f"【深度解析】{desc}",
            f"让你秒懂{desc}",
            f"5分钟了解{desc}",
            f"{desc}完全指南",
            f"关于{desc}你必须知道的几件事",
            f"{desc}入门教程",
            f"为什么说{desc}很重要？",
            f"{desc}的10个实用技巧"
        ]

    def _generate_analysis_demo(self):
        """生成分析演示"""
        try:
            analysis_type = self.analysis_type_group.checkedId()
            duration = self.video_duration_spin.value()
            desc = self.video_desc_edit.text().strip()

            if not desc:
                desc = "科技科普视频"

            # 模拟分析结果
            result = self._generate_sample_analysis(analysis_type, duration, desc)
            self.analysis_result_text.setText(result)

        except Exception as e:
            self.logger.error(f"生成分析演示失败: {e}")
            QMessageBox.critical(self, "错误", f"生成失败: {e}")

    def _generate_sample_analysis(self, analysis_type: int, duration: int, desc: str) -> str:
        """生成示例分析结果"""
        if analysis_type == 1:  # 场景检测
            return f"""
场景分析结果：

视频总时长：{duration}秒
检测到 {max(3, duration // 30)} 个场景

场景1: 00:00 - 00:15
类型：开场介绍
内容：视频主题引入
置信度：95%

场景2: 00:15 - 01:30
类型：主要内容
内容：核心知识点讲解
置信度：92%

场景3: 01:30 - {duration//60:02d}:{duration%60:02d}
类型：总结收尾
内容：要点回顾和总结
置信度：88%

分析完成！视频结构清晰，适合观众理解。
            """
        elif analysis_type == 2:  # 内容分析
            return f"""
内容分析结果：

视频主题：{desc}
内容类型：教育科普
目标受众：普通观众

关键词权重：
- 技术：85%
- 科普：78%
- 教育：72%
- 创新：65%

情感倾向：积极正面
专业程度：中等
信息密度：适中

内容建议：
1. 适当增加实例说明
2. 考虑添加视觉辅助材料
3. 可以适当简化部分专业术语

整体评分：85/100
内容质量良好，具有教育价值。
            """
        else:  # 高光时刻
            return f"""
高光时刻分析结果：

视频时长：{duration}秒
检测到 {max(2, duration // 45)} 个高光时刻

高光1: 00:25 - 00:48
评分：92/100
内容：关键概念讲解
原因：内容重要，表达清晰

高光2: 01:15 - 01:38
评分：88/100
内容：实例演示
原因：生动形象，易于理解

高光3: 02:05 - 02:28
评分：85/100
内容：总结归纳
原因：要点突出，便于记忆

建议：
- 可以将高光1制作成短视频预告
- 高光2适合用于社交媒体推广
- 建议在高光时刻添加重点标记
            """

    def cleanup(self):
        """清理资源"""
        try:
            self.ai_service_manager.cleanup()
        except Exception as e:
            self.logger.error(f"清理资源失败: {e}")