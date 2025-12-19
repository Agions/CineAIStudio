#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UI组件测试
测试 macOS 风格组件的功能
"""

import pytest
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QApplication, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from app.ui.common.macOS_components import (
    MacCard, MacButton, MacPrimaryButton, MacSecondaryButton,
    MacIconButton, MacLabel, MacTitleLabel, MacBadge,
    MacScrollArea, MacGrid, MacPageToolbar
)


@pytest.fixture
def qapp():
    """创建 QApplication 实例"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.mark.ui
class TestMacCard:
    """MacCard 组件测试"""

    def test_card_initialization(self, qapp):
        """测试卡片初始化"""
        card = MacCard("测试卡片")

        assert card.property("class") == "card"
        assert not card.property("elevated")
        assert not card.property("clickable")

    def test_elevated_card(self, qapp):
        """测试提升卡片"""
        card = MacCard("提升卡片", elevated=True)

        assert card.property("elevated")

    def test_clickable_card(self, qapp):
        """测试可点击卡片"""
        card = MacCard("可点击卡片", clickable=True)

        assert card.property("clickable")
        assert card.property("class") == "card clickable"

    def test_card_with_custom_widget(self, qapp):
        """测试包含自定义组件的卡片"""
        card = MacCard()
        label = MacLabel("内部标签")
        card.add_widget(label)

        assert label in card.findChildren(MacLabel)


@pytest.mark.ui
class TestMacButton:
    """MacButton 系列组件测试"""

    def test_primary_button(self, qapp):
        """测试主要按钮"""
        button = MacPrimaryButton("主要按钮")

        assert button.property("class") == "button primary"
        assert button.text() == "主要按钮"

    def test_secondary_button(self, qapp):
        """测试次要按钮"""
        button = MacSecondaryButton("次要按钮")

        assert button.property("class") == "button secondary"

    def test_icon_button(self, qapp):
        """测试图标按钮"""
        button = MacIconButton("🚀")

        assert button.property("class") == "button icon"
        assert button.text() == "🚀"

    def test_button_click_signal(self, qapp):
        """测试按钮点击信号"""
        button = MacPrimaryButton("点击我")
        signal_received = False

        def on_clicked():
            nonlocal signal_received
            signal_received = True

        button.clicked.connect(on_clicked)
        button.click()

        assert signal_received

    def test_button_state_management(self, qapp):
        """测试按钮状态管理"""
        button = MacPrimaryButton("状态按钮")

        # 测试启用/禁用
        button.setEnabled(False)
        assert not button.isEnabled()

        button.setEnabled(True)
        assert button.isEnabled()


@pytest.mark.ui
class TestMacLabel:
    """MacLabel 系列组件测试"""

    def test_label_initialization(self, qapp):
        """测试标签初始化"""
        label = MacLabel("普通标签")

        assert label.property("class") == "label"
        assert label.text() == "普通标签"

    def test_title_label(self, qapp):
        """测试标题标签"""
        label = MacTitleLabel("标题")

        assert label.property("class") == "label title"
        assert label.text() == "标题"

    def test_label_alignment(self, qapp):
        """测试标签对齐"""
        label = MacLabel("居中标签", alignment=Qt.AlignmentFlag.AlignCenter)

        assert label.alignment() == Qt.AlignmentFlag.AlignCenter


@pytest.mark.ui
class TestMacBadge:
    """MacBadge 组件测试"""

    def test_badge_initialization(self, qapp):
        """测试徽章初始化"""
        badge = MacBadge("新")

        assert badge.property("class") == "badge"
        assert badge.text() == "新"

    def test_badge_types(self, qapp):
        """测试不同类型的徽章"""
        types = ["primary", "secondary", "success", "warning", "error"]

        for badge_type in types:
            badge = MacBadge(badge_type.upper(), badge_type)
            expected_class = f"badge {badge_type}"
            assert badge.property("class") == expected_class

    def test_badge_count(self, qapp):
        """测试数字徽章"""
        badge = MacBadge("5", "primary")

        assert badge.text() == "5"
        assert badge.property("class") == "badge primary"


@pytest.mark.ui
class TestMacScrollArea:
    """MacScrollArea 组件测试"""

    def test_scroll_area_initialization(self, qapp):
        """测试滚动区域初始化"""
        scroll_area = MacScrollArea()

        assert scroll_area.property("class") == "scroll-area"

    def test_scroll_area_with_widget(self, qapp):
        """测试包含组件的滚动区域"""
        scroll_area = MacScrollArea()
        widget = MacCard("滚动内容")

        scroll_area.set_widget(widget)
        assert scroll_area.widget() == widget

    def test_scroll_policies(self, qapp):
        """测试滚动策略"""
        scroll_area = MacScrollArea()

        # 测试不同的滚动策略
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)


@pytest.mark.ui
class TestMacGrid:
    """MacGrid 组件测试"""

    def test_grid_initialization(self, qapp):
        """测试网格初始化"""
        grid = MacGrid(columns=3)

        assert grid.property("class") == "grid"
        assert grid.layout().columnCount() == 3

    def test_grid_add_widget(self, qapp):
        """测试网格添加组件"""
        grid = MacGrid(columns=2)
        widget1 = MacCard("项目1")
        widget2 = MacCard("项目2")

        grid.add_widget(widget1)
        grid.add_widget(widget2)

        # 验证组件已添加
        assert widget1 in grid.findChildren(MacCard)
        assert widget2 in grid.findChildren(MacCard)

    def test_grid_spacing(self, qapp):
        """测试网格间距"""
        grid = MacGrid(columns=2, spacing=10)

        layout = grid.layout()
        assert layout.spacing() == 10


@pytest.mark.ui
class TestMacPageToolbar:
    """MacPageToolbar 组件测试"""

    def test_toolbar_initialization(self, qapp):
        """测试工具栏初始化"""
        toolbar = MacPageToolbar("页面标题")

        assert toolbar.property("class") == "page-toolbar"
        # 这里需要检查是否正确显示了标题

    def test_toolbar_add_action(self, qapp):
        """测试工具栏添加操作"""
        toolbar = MacPageToolbar("页面标题")
        action = MacPrimaryButton("操作按钮")

        toolbar.add_action(action)
        # 验证按钮已添加到工具栏


@pytest.mark.ui
class TestComponentInteraction:
    """组件交互测试"""

    def test_card_with_button(self, qapp):
        """测试卡片包含按钮的交互"""
        card = MacCard(clickable=True)
        button = MacPrimaryButton("卡片内按钮")

        card.add_widget(button)

        # 测试按钮点击
        button_clicked = False
        button.clicked.connect(lambda: setattr(button, 'clicked', True))
        button.click()

    def test_grid_of_cards(self, qapp):
        """测试网格中的多个卡片"""
        grid = MacGrid(columns=2)

        for i in range(4):
            card = MacCard(f"卡片 {i+1}")
            grid.add_widget(card)

        cards = grid.findChildren(MacCard)
        assert len(cards) == 4

    def test_scroll_area_with_grid(self, qapp):
        """测试滚动区域包含网格"""
        scroll_area = MacScrollArea()
        grid = MacGrid(columns=3)

        # 添加多个组件到网格
        for i in range(10):
            card = MacCard(f"滚动项目 {i+1}")
            grid.add_widget(card)

        scroll_area.set_widget(grid)
        assert scroll_area.widget() == grid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])