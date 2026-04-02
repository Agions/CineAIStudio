#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VideoForge - 剪辑模板编辑器页面
用于创建、编辑和管理自定义剪辑模板
"""

import logging
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QComboBox, QSpinBox,
    QListWidget, QListWidgetItem, QSplitter,
    QCheckBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from .base_page import BasePage
from app.ui.components import (
    MacCard, MacElevatedCard, MacPrimaryButton,
    MacSecondaryButton, MacLabel, MacScrollArea,
    MacPageToolbar
)
from app.services.ai.cut_template import (
    CutTemplateManager, CutTemplate, TemplateStyle, SegmentRule, SegmentConfig
)


logger = logging.getLogger(__name__)


class TemplateEditorDialog(QDialog):
    """模板编辑对话框"""

    def __init__(self, template: Optional[CutTemplate] = None, parent=None):
        super().__init__(parent)
        self.template = template
        self._setup_ui()
        self._load_template()

    def _setup_ui(self):
        """设置 UI"""
        self.setWindowTitle("编辑模板" if self.template else "新建模板")
        self.setMinimumSize(600, 700)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # 基础信息卡片
        basic_card = MacCard("📝 基础信息")
        basic_layout = basic_card.layout()

        # 模板名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("模板名称："))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("输入模板名称...")
        name_layout.addWidget(self.name_edit)
        basic_layout.addLayout(name_layout)

        # 模板描述
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("模板描述："))
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("输入模板描述...")
        self.desc_edit.setMaximumHeight(60)
        desc_layout.addWidget(self.desc_edit)
        basic_layout.addLayout(desc_layout)

        layout.addWidget(basic_card)

        # 风格设置卡片
        style_card = MacCard("⚙️ 风格设置")
        style_layout = style_card.layout()

        # 剪辑风格
        style_row = QHBoxLayout()
        style_row.addWidget(QLabel("剪辑风格："))
        self.style_combo = QComboBox()
        self.style_combo.addItems([
            "narrative - 叙事完整",
            "highlight - 高光集锦",
            "trailer - 悬念预告",
            "custom - 自定义"
        ])
        style_row.addWidget(self.style_combo)
        style_layout.addLayout(style_row)

        # 目标时长
        duration_row = QHBoxLayout()
        duration_row.addWidget(QLabel("目标时长（秒）："))
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(0, 3600)
        self.duration_spin.setValue(0)
        self.duration_spin.setSuffix(" (0=保持原长)")
        duration_row.addWidget(self.duration_spin)
        style_layout.addLayout(duration_row)

        layout.addWidget(style_card)

        # 保留设置卡片
        keep_card = MacCard("✂️ 保留设置")
        keep_layout = keep_card.layout()

        self.keep_opening_cb = QCheckBox("保留开场")
        self.keep_opening_cb.setChecked(True)
        keep_layout.addWidget(self.keep_opening_cb)

        self.keep_climax_cb = QCheckBox("保留高潮")
        self.keep_climax_cb.setChecked(True)
        keep_layout.addWidget(self.keep_climax_cb)

        self.keep_ending_cb = QCheckBox("保留结局")
        self.keep_ending_cb.setChecked(True)
        keep_layout.addWidget(self.keep_ending_cb)

        layout.addWidget(keep_card)

        # 片段规则卡片
        rules_card = MacCard("📋 片段规则")
        rules_layout = rules_card.layout()

        # 片段规则表
        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(4)
        self.rules_table.setHorizontalHeaderLabels(["场景类型", "规则", "最小时长", "最大时长"])
        self.rules_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.rules_table.setRowCount(0)
        rules_layout.addWidget(self.rules_table)

        # 添加/删除规则按钮
        rules_btn_layout = QHBoxLayout()
        add_rule_btn = MacSecondaryButton("➕ 添加规则")
        add_rule_btn.clicked.connect(self._add_rule)
        rules_btn_layout.addWidget(add_rule_btn)

        remove_rule_btn = MacSecondaryButton("➖ 删除规则")
        remove_rule_btn.clicked.connect(self._remove_rule)
        rules_btn_layout.addWidget(remove_rule_btn)

        rules_btn_layout.addStretch()
        rules_layout.addLayout(rules_btn_layout)

        layout.addWidget(rules_card)

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = MacSecondaryButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = MacPrimaryButton("💾 保存")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _load_template(self):
        """加载模板数据"""
        if not self.template:
            # 添加默认规则行
            self._add_rule()
            return

        self.name_edit.setText(self.template.name)
        self.desc_edit.setText(self.template.description)

        # 设置风格
        style_map = {
            TemplateStyle.NARRATIVE: 0,
            TemplateStyle.HIGHLIGHT: 1,
            TemplateStyle.TRAILER: 2,
            TemplateStyle.CUSTOM: 3
        }
        self.style_combo.setCurrentIndex(style_map.get(self.template.style, 0))

        self.duration_spin.setValue(int(self.template.target_duration))
        self.keep_opening_cb.setChecked(self.template.keep_opening)
        self.keep_climax_cb.setChecked(self.template.keep_climax)
        self.keep_ending_cb.setChecked(self.template.keep_ending)

        # 加载片段规则
        self.rules_table.setRowCount(len(self.template.segment_rules))
        for i, rule in enumerate(self.template.segment_rules):
            self.rules_table.setItem(i, 0, QTableWidgetItem(rule.scene_type))
            self.rules_table.setItem(i, 1, QTableWidgetItem(rule.rule.value))
            self.rules_table.setItem(i, 2, QTableWidgetItem(str(rule.min_duration)))
            self.rules_table.setItem(i, 3, QTableWidgetItem(str(rule.max_duration)))

    def _add_rule(self):
        """添加规则"""
        row = self.rules_table.rowCount()
        self.rules_table.insertRow(row)
        self.rules_table.setItem(row, 0, QTableWidgetItem(""))
        self.rules_table.setItem(row, 1, QTableWidgetItem("keep"))
        self.rules_table.setItem(row, 2, QTableWidgetItem("0"))
        self.rules_table.setItem(row, 3, QTableWidgetItem("0"))

    def _remove_rule(self):
        """删除规则"""
        current_row = self.rules_table.currentRow()
        if current_row >= 0:
            self.rules_table.removeRow(current_row)

    def _save(self):
        """保存模板"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "警告", "请输入模板名称")
            return

        # 构建模板对象
        style_index = self.style_combo.currentIndex()
        style_map = [
            TemplateStyle.NARRATIVE,
            TemplateStyle.HIGHLIGHT,
            TemplateStyle.TRAILER,
            TemplateStyle.CUSTOM
        ]

        # 构建片段规则
        rules = []
        for i in range(self.rules_table.rowCount()):
            scene_type_item = self.rules_table.item(i, 0)
            rule_item = self.rules_table.item(i, 1)
            min_item = self.rules_table.item(i, 2)
            max_item = self.rules_table.item(i, 3)

            if scene_type_item and scene_type_item.text():
                rule = SegmentConfig(
                    scene_type=scene_type_item.text(),
                    rule=SegmentRule(rule_item.text() if rule_item else "keep"),
                    min_duration=float(min_item.text() if min_item else "0"),
                    max_duration=float(max_item.text() if max_item else "0")
                )
                rules.append(rule)

        # 创建或更新模板
        if self.template:
            self.template.name = name
            self.template.description = self.desc_edit.toPlainText().strip()
            self.template.style = style_map[style_index]
            self.template.target_duration = float(self.duration_spin.value())
            self.template.keep_opening = self.keep_opening_cb.isChecked()
            self.template.keep_climax = self.keep_climax_cb.isChecked()
            self.template.keep_ending = self.keep_ending_cb.isChecked()
            self.template.segment_rules = rules
        else:
            import uuid
            self.template = CutTemplate(
                id=str(uuid.uuid4())[:8],
                name=name,
                description=self.desc_edit.toPlainText().strip(),
                style=style_map[style_index],
                target_duration=float(self.duration_spin.value()),
                keep_opening=self.keep_opening_cb.isChecked(),
                keep_climax=self.keep_climax_cb.isChecked(),
                keep_ending=self.keep_ending_cb.isChecked(),
                segment_rules=rules,
                is_preset=False
            )

        self.accept()

    def get_template(self) -> Optional[CutTemplate]:
        return self.template


class TemplateEditorPage(BasePage):
    """模板编辑器页面"""

    def __init__(self, application):
        super().__init__("template_editor", "模板管理", application)
        self.logger = logging.getLogger(__name__)
        self._init_services()

    def _init_services(self):
        """初始化服务"""
        self.template_manager = CutTemplateManager()

    def create_content(self) -> None:
        """创建页面内容"""
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(16)

        # 工具栏
        toolbar = MacPageToolbar("📋 剪辑模板管理")

        new_btn = MacPrimaryButton("➕ 新建模板")
        new_btn.clicked.connect(self._on_new_template)
        toolbar.add_action(new_btn)

        self.edit_btn = MacSecondaryButton("✏️ 编辑")
        self.edit_btn.clicked.connect(self._on_edit_template)
        self.edit_btn.setEnabled(False)
        toolbar.add_action(self.edit_btn)

        delete_btn = MacSecondaryButton("🗑️ 删除")
        delete_btn.clicked.connect(self._on_delete_template)
        toolbar.add_action(delete_btn)

        refresh_btn = MacSecondaryButton("🔄 刷新")
        refresh_btn.clicked.connect(self._load_templates)
        toolbar.add_action(refresh_btn)

        self.main_layout.addWidget(toolbar)

        # 主内容区域
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.setSizes([350, 550])
        content_splitter.setCollapsible(0, False)

        # 左侧：模板列表
        left_panel = self._create_template_list_panel()
        content_splitter.addWidget(left_panel)

        # 右侧：模板详情
        right_panel = self._create_template_detail_panel()
        content_splitter.addWidget(right_panel)

        self.main_layout.addWidget(content_splitter, 1)

        # 加载模板
        self._load_templates()

    def _create_template_list_panel(self) -> QWidget:
        """创建模板列表面板"""
        card = MacCard("📋 模板列表")
        layout = card.layout()

        self.template_list = QListWidget()
        self.template_list.currentItemChanged.connect(self._on_template_selected)
        layout.addWidget(self.template_list)

        return card

    def _create_template_detail_panel(self) -> QWidget:
        """创建模板详情面板"""
        scroll = MacScrollArea()
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(16)

        # 模板信息卡片
        self.info_card = MacElevatedCard("📝 模板信息")
        info_layout = self.info_card.layout()
        info_layout.setSpacing(8)

        self.template_name_label = MacLabel("未选择")
        name_font = QFont("", 16, QFont.Weight.Bold)
        self.template_name_label.setFont(name_font)
        info_layout.addWidget(self.template_name_label)

        self.template_desc_label = MacLabel("")
        self.template_desc_label.setWordWrap(True)
        info_layout.addWidget(self.template_desc_label)

        self.template_style_label = MacLabel("")
        info_layout.addWidget(self.template_style_label)

        layout.addWidget(self.info_card)

        # 设置卡片
        self.settings_card = MacCard("⚙️ 设置")
        settings_layout = self.settings_card.layout()
        settings_layout.setSpacing(8)

        self.keep_opening_label = MacLabel("保留开场：-")
        settings_layout.addWidget(self.keep_opening_label)

        self.keep_climax_label = MacLabel("保留高潮：-")
        settings_layout.addWidget(self.keep_climax_label)

        self.keep_ending_label = MacLabel("保留结局：-")
        settings_layout.addWidget(self.keep_ending_label)

        self.target_duration_label = MacLabel("目标时长：-")
        settings_layout.addWidget(self.target_duration_label)

        layout.addWidget(self.settings_card)

        # 片段规则卡片
        self.rules_card = MacCard("📋 片段规则")
        rules_layout = self.rules_card.layout()

        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(4)
        self.rules_table.setHorizontalHeaderLabels(["场景类型", "规则", "最小时长", "最大时长"])
        self.rules_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.rules_table.setMaximumHeight(250)
        rules_layout.addWidget(self.rules_table)

        layout.addWidget(self.rules_card)

        layout.addStretch()
        scroll.setWidget(content)
        scroll.setWidgetResizable(True)
        return scroll

    def _load_templates(self):
        """加载模板列表"""
        self.template_list.clear()
        self.templates = self.template_manager.get_all_templates()

        for template in self.templates:
            # 创建列表项
            item = QListWidgetItem()
            if template.is_preset:
                item.setText(f"🏷️ {template.name}")
            else:
                item.setText(f"📄 {template.name}")
            item.setData(Qt.ItemDataRole.UserRole, template)
            self.template_list.addItem(item)

        self._update_detail_view(None)

    def _on_template_selected(self, current: QListWidgetItem, previous: QListWidgetItem):
        """模板选择变化"""
        if current:
            template = current.data(Qt.ItemDataRole.UserRole)
            self._update_detail_view(template)
            self.edit_btn.setEnabled(not template.is_preset)
        else:
            self._update_detail_view(None)
            self.edit_btn.setEnabled(False)

    def _update_detail_view(self, template: Optional[CutTemplate]):
        """更新详情视图"""
        if not template:
            self.template_name_label.setText("未选择")
            self.template_desc_label.setText("")
            self.template_style_label.setText("")
            self.keep_opening_label.setText("保留开场：-")
            self.keep_climax_label.setText("保留高潮：-")
            self.keep_ending_label.setText("保留结局：-")
            self.target_duration_label.setText("目标时长：-")
            self.rules_table.setRowCount(0)
            return

        self.template_name_label.setText(template.name)
        self.template_desc_label.setText(template.description or "无描述")
        self.template_style_label.setText(f"风格：{template.style.value}")

        self.keep_opening_label.setText(f"保留开场：{'是' if template.keep_opening else '否'}")
        self.keep_climax_label.setText(f"保留高潮：{'是' if template.keep_climax else '否'}")
        self.keep_ending_label.setText(f"保留结局：{'是' if template.keep_ending else '否'}")

        duration_text = "保持原长" if template.target_duration == 0 else f"{int(template.target_duration)}秒"
        self.target_duration_label.setText(f"目标时长：{duration_text}")

        # 更新规则表
        self.rules_table.setRowCount(len(template.segment_rules))
        for i, rule in enumerate(template.segment_rules):
            self.rules_table.setItem(i, 0, QTableWidgetItem(rule.scene_type))
            self.rules_table.setItem(i, 1, QTableWidgetItem(rule.rule.value))
            self.rules_table.setItem(i, 2, QTableWidgetItem(str(rule.min_duration)))
            self.rules_table.setItem(i, 3, QTableWidgetItem(str(rule.max_duration)))
        self.rules_table.resizeRowsToContents()

    def _on_new_template(self):
        """新建模板"""
        dialog = TemplateEditorDialog(parent=self)
        if dialog.exec():
            template = dialog.get_template()
            if template:
                success = self.template_manager.save_template(template)
                if success:
                    QMessageBox.information(self, "成功", "模板已保存")
                    self._load_templates()
                else:
                    QMessageBox.warning(self, "失败", "模板保存失败")

    def _on_edit_template(self):
        """编辑模板"""
        current = self.template_list.currentItem()
        if not current:
            return

        template = current.data(Qt.ItemDataRole.UserRole)
        if template.is_preset:
            QMessageBox.information(self, "提示", "预设模板不可编辑")
            return

        dialog = TemplateEditorDialog(template=template, parent=self)
        if dialog.exec():
            updated_template = dialog.get_template()
            if updated_template:
                success = self.template_manager.save_template(updated_template)
                if success:
                    QMessageBox.information(self, "成功", "模板已更新")
                    self._load_templates()
                else:
                    QMessageBox.warning(self, "失败", "模板更新失败")

    def _on_delete_template(self):
        """删除模板"""
        current = self.template_list.currentItem()
        if not current:
            return

        template = current.data(Qt.ItemDataRole.UserRole)
        if template.is_preset:
            QMessageBox.information(self, "提示", "预设模板不可删除")
            return

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除模板「{template.name}」吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success = self.template_manager.delete_template(template.id)
            if success:
                QMessageBox.information(self, "成功", "模板已删除")
                self._load_templates()
            else:
                QMessageBox.warning(self, "失败", "模板删除失败")
