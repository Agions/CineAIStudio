#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Narrafiilm 创作台页面
三步流程：上传视频 → 配置风格 → 生成解说
"""

import os
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QFrame, QLabel, QPushButton, QProgressBar, QComboBox,
    QLineEdit, QSlider, QListWidget, QFileDialog,
    QMessageBox, QListWidgetItem
)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QFont, QColor

from .base_page import BasePage
from app.services.ai._legacy.first_person_narrator import FirstPersonNarrator


# ============================================================================
# 生成线程（避免阻塞 UI）
# ============================================================================

class GenerationWorker(QThread):
    """后台生成线程"""
    log_signal = Signal(str)
    progress_signal = Signal(int, str)
    finished_signal = Signal(str)  # output path
    error_signal = Signal(str)

    def __init__(self, video_path: str, output_dir: str, config: dict):
        super().__init__()
        self.video_path = video_path
        self.output_dir = output_dir
        self.config = config

    def run(self):
        try:
            self.log_signal.emit("🚀 开始生成第一人称解说...")

            # 配置 Narrator
            narrator = FirstPersonNarrator()

            def progress_callback(stage: str, pct: float):
                self.progress_signal.emit(int(pct * 100), stage)

            self.progress_signal.emit(0, "初始化...")
            self.log_signal.emit("⚡ 场景理解 (Qwen2.5-VL)...")
            self.progress_signal.emit(5, "场景理解...")

            # 构建项目
            from app.services.ai._legacy.first_person_narrator import NarrationProject
            project = NarrationProject(
                video_path=self.video_path,
                output_dir=self.output_dir,
                emotion_style=self.config.get("emotion", "auto"),
                voice_id=self.config.get("voice_id", "zh-CN-XiaoxiaoNeural"),
                voice_rate=self.config.get("voice_rate", 1.0),
            )

            # Step 1: 场景分析
            narrator.analyze_scenes(project, progress_callback)
            self.log_signal.emit("✅ 场景理解完成")
            self.progress_signal.emit(25, "生成解说...")

            # Step 2: 文案生成
            self.log_signal.emit("✍️  解说文案生成 (DeepSeek-V3)...")
            narrator.generate_narration(project, progress_callback)
            self.log_signal.emit("✅ 解说文案生成完成")
            self.progress_signal.emit(50, "配音合成...")

            # Step 3: 配音合成
            self.log_signal.emit("🎙️  配音合成 (Edge-TTS)...")
            narrator.generate_voice(project, progress_callback)
            self.log_signal.emit("✅ 配音合成完成")
            self.progress_signal.emit(75, "字幕生成...")

            # Step 4: 字幕
            self.log_signal.emit("📝 字幕生成 (TTS Word Timing)...")
            narrator.generate_subtitles(project, progress_callback)
            self.log_signal.emit("✅ 字幕生成完成")
            self.progress_signal.emit(90, "导出视频...")

            # Step 5: 导出
            self.log_signal.emit("🎬 视频导出中...")
            output_path = narrator.export(project, progress_callback)

            self.progress_signal.emit(100, "完成")
            self.log_signal.emit(f"✅ 导出完成: {os.path.basename(output_path)}")
            self.finished_signal.emit(output_path)

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error_signal.emit(str(e))


# ============================================================================
# 创作台页面
# ============================================================================

class CreatorPage(BasePage):
    """Narrafiilm 创作台页面"""

    def __init__(self, page_id: str, title: str, application):
        super().__init__(page_id, title, application)
        self.worker: Optional[GenerationWorker] = None
        self.current_video_path: Optional[str] = None

        # 情感风格映射
        self.emotion_map = {
            "😌 惆怅": "惆怅",
            "💪 励志": "励志",
            "💕 浪漫": "浪漫",
            "🔮 悬疑": "悬疑",
            "🌿 治愈": "治愈",
            "🤔 哲思": "哲思",
        }

        # 声音映射
        self.voice_map = {
            "晓晓（女声·温柔）": "zh-CN-XiaoxiaoNeural",
            "云扬（男声·磁性）": "zh-CN-YunyeNeural",
            "云希（男声·年轻）": "zh-CN-YunxiNeural",
            "晓墨（女声·知性）": "zh-CN-XiaomoNeural",
        }

    def initialize(self) -> bool:
        return True

    def create_content(self):
        self.set_main_layout_margins(32, 24, 32, 24)
        self.set_main_layout_spacing(20)
        self._build_header()
        self._build_steps()
        self._build_body()

    def _build_header(self):
        """顶部标题区"""
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        title_block = QWidget()
        title_layout = QVBoxLayout(title_block)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)

        title_main = QLabel("第一人称解说")
        title_main.setObjectName("creator_title")
        title_main.setStyleSheet("color: #E8EDF5; font-size: 22px; font-weight: 700; letter-spacing: -0.01em;")

        title_sub = QLabel("上传视频，AI 代入主角视角，一键生成配音解说")
        title_sub.setStyleSheet("color: #4A6080; font-size: 12px;")

        title_layout.addWidget(title_main)
        title_layout.addWidget(title_sub)
        header_layout.addWidget(title_block)
        header_layout.addStretch()

        # 状态
        self.status_badge = QLabel("● 就绪")
        self.status_badge.setStyleSheet(self._badge_style("#0A1A2A", "#10B981", "#0F3020"))
        header_layout.addWidget(self.status_badge)

        self.add_widget_to_main_layout(header)

    def _build_steps(self):
        """步骤指示器"""
        self.step_widgets = []
        steps_data = [
            ("1", "上传视频", True),
            ("2", "配置风格", False),
            ("3", "生成解说", False),
        ]

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        for num, label, active in steps_data:
            sw = QFrame()
            sw.setFixedHeight(48)
            sw.setStyleSheet(self._card_style())
            sw_layout = QHBoxLayout(sw)
            sw_layout.setContentsMargins(16, 0, 16, 0)

            num_lbl = QLabel(num)
            num_lbl.setFixedSize(24, 24)
            num_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            active_color = "#0A84FF" if active else "#1E3A5F"
            num_lbl.setStyleSheet(
                f"background: {active_color}; color: white; "
                "border-radius: 12px; font-size: 12px; font-weight: 700;"
            )

            lbl = QLabel(label)
            lbl.setStyleSheet("color: #8098B0; font-size: 12px; font-weight: 500;")

            sw_layout.addWidget(num_lbl)
            sw_layout.addWidget(lbl)
            sw_layout.addStretch()

            self.step_widgets.append(sw)
            layout.addWidget(sw)

        layout.addStretch()
        self.add_widget_to_main_layout(container)

    def _build_body(self):
        """主体三栏"""
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(16)

        body_layout.addWidget(self._build_upload_card(), 1)
        body_layout.addWidget(self._build_config_card(), 1)
        body_layout.addWidget(self._build_action_card(), 1)

        self.add_widget_to_main_layout(body)

    def _build_upload_card(self) -> QFrame:
        """上传区卡片"""
        card = self._make_card()
        layout = QVBoxLayout(card)
        layout.setSpacing(16)

        layout.addWidget(QLabel("📹 上传视频").重新设置样式("color: #E8EDF5; font-size: 14px; font-weight: 600;"))

        # 拖放区
        self.drop_zone = QFrame()
        self.drop_zone.setMinimumHeight(220)
        self.drop_zone.setObjectName("drop_zone")
        self.drop_zone.setStyleSheet(self._dropzone_style())
        dz_layout = QVBoxLayout(self.drop_zone)
        dz_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dz_layout.setSpacing(8)

        dz_layout.addWidget(QLabel("🎬").重新设置样式("font-size: 40px;"))
        dz_layout.addWidget(QLabel("拖拽视频文件到这里").重新设置样式("color: #4A6080; font-size: 13px; font-weight: 500;"))
        dz_layout.addWidget(QLabel("支持 MP4 / MOV / AVI / MKV").重新设置样式("color: #2A3A50; font-size: 11px;"))
        dz_layout.addWidget(QLabel("— 或 —").重新设置样式("color: #2A3A50; font-size: 11px; padding: 8px 0;"))

        browse_btn = QPushButton("浏览文件")
        browse_btn.setFixedWidth(120)
        browse_btn.setStyleSheet(self._secondary_btn_style())
        browse_btn.clicked.connect(self._on_browse)
        dz_layout.addWidget(browse_btn)

        layout.addWidget(self.drop_zone)

        # 文件信息
        self.file_info_widget = QWidget()
        fi_layout = QHBoxLayout(self.file_info_widget)
        fi_layout.setContentsMargins(0, 0, 0, 0)
        fi_layout.addWidget(QLabel("✅").重新设置样式("font-size: 14px;"))
        self.file_name_label = QLabel("未选择文件")
        self.file_name_label.setStyleSheet("color: #4A6080; font-size: 12px;")
        fi_layout.addWidget(self.file_name_label, 1)
        self.file_info_widget.setVisible(False)
        layout.addWidget(self.file_info_widget)

        layout.addStretch()
        return card

    def _build_config_card(self) -> QFrame:
        """配置卡片"""
        card = self._make_card()
        layout = QVBoxLayout(card)
        layout.setSpacing(14)

        layout.addWidget(QLabel("🎨 风格配置").重新设置样式("color: #E8EDF5; font-size: 14px; font-weight: 600;"))

        # 情感风格
        layout.addWidget(self._section_label("情感风格"))

        emotion_grid = QWidget()
        egl = QGridLayout(emotion_grid)
        egl.setSpacing(8)
        self.emotion_btns = {}
        emotions = list(self.emotion_map.keys())
        for i, emoji_text in enumerate(emotions):
            row, col = i // 3, i % 3
            btn = QPushButton(emoji_text)
            btn.setCheckable(True)
            btn.setFixedHeight(36)
            btn.setStyleSheet(self._emotion_btn_style())
            btn.clicked.connect(lambda _, b=btn: self._on_emotion_selected(b))
            egl.addWidget(btn, row, col)
            self.emotion_btns[emoji_text] = btn

        layout.addWidget(emotion_grid)

        # 叙事角度
        layout.addWidget(self._section_label("叙事角度"))
        self.narrative_combo = self._make_combo([
            "沉浸式（主角视角）",
            "编年体（回忆叙事）",
            "反思式（感悟叙述）",
            "点评式（边做边说）",
        ])
        layout.addWidget(self.narrative_combo)

        # 配音声音
        layout.addWidget(self._section_label("配音声音"))
        self.voice_combo = self._make_combo(list(self.voice_map.keys()))
        layout.addWidget(self.voice_combo)

        # 语速
        layout.addWidget(self._section_label("语速"))
        speed_w = QWidget()
        sl = QHBoxLayout(speed_w)
        sl.setContentsMargins(0, 0, 0, 0)
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(50, 200)
        self.speed_slider.setValue(100)
        self.speed_slider.setFixedHeight(20)
        self.speed_slider.setStyleSheet(self._slider_style())
        self.speed_slider.valueChanged.connect(lambda v: setattr(self, '_speed', v/100))
        sl.addWidget(self.speed_slider)
        self.speed_label = QLabel("1.0x")
        self.speed_label.setFixedWidth(36)
        self.speed_label.setStyleSheet("color: #8098B0; font-size: 12px; font-weight: 600;")
        self.speed_slider.valueChanged.connect(
            lambda v: self.speed_label.setText(f"{v/100:.1f}x")
        )
        sl.addWidget(self.speed_label)
        layout.addWidget(speed_w)

        layout.addStretch()

        # 生成按钮
        self.generate_btn = QPushButton("🚀 开始生成解说")
        self.generate_btn.setFixedHeight(48)
        self.generate_btn.setStyleSheet(self._primary_btn_style())
        self.generate_btn.clicked.connect(self._on_generate)
        self.generate_btn.setEnabled(False)
        layout.addWidget(self.generate_btn)

        return card

    def _build_action_card(self) -> QFrame:
        """操作/预览卡片"""
        card = self._make_card()
        layout = QVBoxLayout(card)
        layout.setSpacing(14)

        layout.addWidget(QLabel("📋 操作").重新设置样式("color: #E8EDF5; font-size: 14px; font-weight: 600;"))

        # 进度
        ph_layout = QVBoxLayout()
        ph_layout.setSpacing(6)
        ph_header = QHBoxLayout()
        ph_label = QLabel("生成进度")
        ph_label.setStyleSheet("color: #6A8098; font-size: 11px; font-weight: 600;")
        self.progress_label = QLabel("0%")
        self.progress_label.setStyleSheet("color: #0A84FF; font-size: 11px; font-weight: 700;")
        ph_header.addWidget(ph_label)
        ph_header.addStretch()
        ph_header.addWidget(self.progress_label)
        ph_layout.addLayout(ph_header)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet(self._progress_style())
        ph_layout.addWidget(self.progress_bar)
        layout.addLayout(ph_layout)

        # 日志
        self.log_list = QListWidget()
        self.log_list.setFixedHeight(130)
        self.log_list.setStyleSheet(self._log_list_style())
        layout.addWidget(self.log_list)

        # 模型流水线
        pipeline = [
            ("⚡", "场景理解", "Qwen2.5-VL 72B"),
            ("✍️", "解说生成", "DeepSeek-V3"),
            ("🎙️", "配音合成", "Edge-TTS"),
            ("📝", "字幕对齐", "TTS Word Timing"),
            ("🎬", "视频导出", "FFmpeg"),
        ]
        for icon, name, model in pipeline:
            row = QWidget()
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.addWidget(QLabel(icon).重新设置样式("font-size: 14px;"))
            rl.addWidget(QLabel(name).重新设置样式("color: #8098B0; font-size: 12px; font-weight: 500;"))
            rl.addStretch()
            rl.addWidget(QLabel(model).重新设置样式("color: #2A3A50; font-size: 10px;"))
            self._step_indicator = QLabel("○")
            self._step_indicator.setFixedWidth(20)
            self._step_indicator.setStyleSheet("color: #2A4060; font-size: 12px;")
            rl.addWidget(self._step_indicator)
            layout.addWidget(row)

        layout.addStretch()

        # 导出按钮组
        export_layout = QHBoxLayout()
        export_layout.setSpacing(8)
        self.export_mp4_btn = QPushButton("📦 导出 MP4")
        self.export_mp4_btn.setFixedHeight(40)
        self.export_mp4_btn.setStyleSheet(self._secondary_btn_style())
        self.export_mp4_btn.setEnabled(False)

        self.export_jianying_btn = QPushButton("🎬 剪映草稿")
        self.export_jianying_btn.setFixedHeight(40)
        self.export_jianying_btn.setStyleSheet(self._secondary_btn_style())
        self.export_jianying_btn.setEnabled(False)

        export_layout.addWidget(self.export_mp4_btn)
        export_layout.addWidget(self.export_jianying_btn)
        layout.addLayout(export_layout)

        return card

    # ====================================================================
    # 事件处理
    # ====================================================================

    def _on_browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "",
            "视频文件 (*.mp4 *.mov *.avi *.mkv *.flv);;所有文件 (*)"
        )
        if path:
            self._set_video(path)

    def _set_video(self, path: str):
        self.current_video_path = path
        from pathlib import Path
        name = Path(path).name
        self.file_name_label.setText(name)
        self.file_name_label.setStyleSheet("color: #10B981; font-size: 12px; font-weight: 500;")
        self.file_info_widget.setVisible(True)
        self.generate_btn.setEnabled(True)
        self.log_list.clear()
        self.log_list.addItem(f"📹 已选择: {name}")

    def _on_emotion_selected(self, clicked_btn: QPushButton):
        for btn in self.emotion_btns.values():
            if btn != clicked_btn:
                btn.setChecked(False)

    def _on_generate(self):
        if not self.current_video_path:
            QMessageBox.warning(self, "提示", "请先上传视频文件")
            return

        # 获取配置
        selected_emotion = None
        for emoji_text, emotion in self.emotion_map.items():
            if self.emotion_btns[emoji_text].isChecked():
                selected_emotion = emotion
                break
        selected_emotion = selected_emotion or "auto"

        selected_voice = list(self.voice_map.values())[
            self.voice_map_keys_index()
        ]

        config = {
            "emotion": selected_emotion,
            "voice_id": selected_voice,
            "voice_rate": getattr(self, '_speed', 1.0),
        }

        output_dir = os.path.join(
            os.path.expanduser("~"), "Narrafiilm", "output"
        )
        os.makedirs(output_dir, exist_ok=True)

        self._set_generating(True)

        self.worker = GenerationWorker(
            self.current_video_path, output_dir, config
        )
        self.worker.log_signal.connect(self._on_log)
        self.worker.progress_signal.connect(self._on_progress)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.error_signal.connect(self._on_error)
        self.worker.start()

    def _voice_map_keys_index(self) -> int:
        return list(self.voice_map.keys()).index(self.voice_combo.currentText())

    def _on_log(self, msg: str):
        self.log_list.addItem(msg)
        self.log_list.scrollToBottom()

    def _on_progress(self, pct: int, stage: str):
        self.progress_bar.setValue(pct)
        self.progress_label.setText(f"{pct}%")

    def _on_finished(self, output_path: str):
        self._set_generating(False)
        self.status_badge.setText("● 完成")
        self.status_badge.setStyleSheet(self._badge_style("#0A1A2A", "#10B981", "#0F3020"))
        self.export_mp4_btn.setEnabled(True)
        self.export_jianying_btn.setEnabled(True)
        self.log_list.addItem("")
        self.log_list.addItem("🎉 生成完成！")
        self.log_list.addItem(f"📁 {output_path}")

    def _on_error(self, err: str):
        self._set_generating(False)
        self.status_badge.setText("● 失败")
        self.status_badge.setStyleSheet(self._badge_style("#1A0A0A", "#EF4444", "#2A1010"))
        self.log_list.addItem(f"❌ 错误: {err}")

    def _set_generating(self, generating: bool):
        self.generate_btn.setEnabled(not generating)
        self.status_badge.setText("● 生成中" if generating else "● 完成")
        self.status_badge.setStyleSheet(
            self._badge_style("#0A1A2A", "#F59E0B", "#2A1A08") if generating
            else self._badge_style("#0A1A2A", "#10B981", "#0F3020")
        )

    # ====================================================================
    # 样式辅助
    # ====================================================================

    @staticmethod
    def _section_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "color: #5A7088; font-size: 11px; font-weight: 600; "
            "letter-spacing: 0.08em; text-transform: uppercase; padding-bottom: 4px;"
        )
        return lbl

    @staticmethod
    def _make_card() -> QFrame:
        f = QFrame()
        f.setStyleSheet(
            "background: #0D1520; border: 1px solid #1A2332; "
            "border-radius: 16px; padding: 20px;"
        )
        return f

    @staticmethod
    def _card_style() -> str:
        return (
            "background: #0A0F1A; border: 1px solid #141E2E; "
            "border-radius: 12px; padding: 0px 16px;"
        )

    @staticmethod
    def _dropzone_style() -> str:
        return (
            "background: #0A0F1A; border: 2px dashed #1E2D42; "
            "border-radius: 16px;"
        )

    @staticmethod
    def _secondary_btn_style() -> str:
        return (
            "background: #0F1929; color: #8098B0; border: 1px solid #1E2D42; "
            "border-radius: 10px; font-size: 12px; font-weight: 500; padding: 8px 16px;"
            "QPushButton:hover { background: #141F32; color: #A0B8D0; border-color: #2A3A55; }"
        )

    @staticmethod
    def _primary_btn_style() -> str:
        return (
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #0A60FF, stop:1 #00A0FF); "
            "color: white; border: none; border-radius: 14px; "
            "font-size: 14px; font-weight: 700; letter-spacing: 0.02em;"
            "QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #1A70FF, stop:1 #10B0FF); } "
            "QPushButton:disabled { background: #1A2740; color: #3A5070; }"
        )

    @staticmethod
    def _emotion_btn_style() -> str:
        return (
            "background: #0A0F1A; border: 1px solid #1A2332; border-radius: 10px; "
            "color: #5A7088; font-size: 12px; font-weight: 500;"
            "QPushButton:hover { border-color: #0A84FF; color: #A0C0E8; } "
            "QPushButton:checked { background: #0A1A3A; border-color: #0A84FF; color: #0A84FF; font-weight: 600; }"
        )

    @staticmethod
    def _slider_style() -> str:
        return (
            "QSlider::groove:horizontal { border: none; height: 4px; background: #1A2332; border-radius: 2px; } "
            "QSlider::handle:horizontal { background: #0A84FF; width: 16px; height: 16px; margin: -6px 0; border-radius: 8px; } "
            "QSlider::sub-page:horizontal { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #0A60FF, stop:1 #00C0FF); border-radius: 2px; }"
        )

    @staticmethod
    def _progress_style() -> str:
        return (
            "QProgressBar { background: #0F1929; border: none; border-radius: 3px; text-align: center; color: transparent; } "
            "QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #0A84FF, stop:1 #00D4FF); border-radius: 3px; }"
        )

    @staticmethod
    def _log_list_style() -> str:
        return (
            "QListWidget { background: #0A0F1A; border: 1px solid #141E2E; "
            "border-radius: 12px; color: #6A8098; font-size: 11px; padding: 8px; } "
            "QListWidget::item { padding: 4px 0px; border-radius: 4px; }"
        )

    @staticmethod
    def _badge_style(bg: str, fg: str, border: str) -> str:
        return f"background: {bg}; color: {fg}; border: 1px solid {border}; border-radius: 8px; padding: 5px 14px; font-size: 12px; font-weight: 600;"

    @staticmethod
    def _make_combo(items) -> QComboBox:
        cb = QComboBox()
        cb.addItems(items)
        cb.setFixedHeight(38)
        cb.setStyleSheet(
            "QComboBox { background: #0A0F1A; color: #C0D0E0; border: 1px solid #1A2332; "
            "border-radius: 10px; padding: 8px 16px; font-size: 13px; } "
            "QComboBox:hover { border-color: #2A4060; } "
            "QComboBox:focus { border-color: #0A84FF; } "
            "QComboBox::down-arrow { border-left: 4px solid transparent; border-right: 4px solid transparent; "
            "border-top: 5px solid #4A6080; margin-right: 8px; } "
            "QComboBox QAbstractItemView { background: #0F1929; border: 1px solid #1E2D42; "
            "border-radius: 10px; color: #C0D0E0; selection-background-color: #0F2640; padding: 4px; }"
        )
        return cb


# 给 QLabel 添加便捷方法
def _reload_style(label: QLabel, style: str):
    label.setStyleSheet(style)

QLabel.重新设置样式 = _reload_style
