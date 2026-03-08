#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UI 组件通用样式
减少 UI 代码重复
"""

from enum import Enum


class ColorPalette:
    """调色板"""
    # 主色
    PRIMARY = "#7C3AED"
    PRIMARY_LIGHT = "#A78BFA"
    PRIMARY_DARK = "#5B21B6"
    
    # 强调色
    ACCENT = "#06B6D4"
    SUCCESS = "#10B981"
    WARNING = "#F59E0B"
    ERROR = "#EF4444"
    INFO = "#3B82F6"
    
    # 背景
    BG_DEEPEST = "#060609"
    BG_DEEP = "#0C0C12"
    BG_SURFACE = "#14141C"
    BG_ELEVATED = "#1C1C28"
    BG_HOVER = "#262635"
    
    # 文字
    TEXT_PRIMARY = "#FAFAFA"
    TEXT_SECONDARY = "#A1A4B3"
    TEXT_TERTIARY = "#6B7280"


class Spacing:
    """间距"""
    XS = "4px"
    SM = "8px"
    MD = "16px"
    LG = "24px"
    XL = "32px"


class Radius:
    """圆角"""
    SM = "6px"
    MD = "10px"
    LG = "14px"
    XL = "20px"


class ButtonStyles:
    """按钮样式"""
    
    PRIMARY = f"""
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {ColorPalette.PRIMARY},
            stop:0.5 {ColorPalette.PRIMARY_LIGHT},
            stop:1 {ColorPalette.PRIMARY});
        color: white;
        border: none;
        border-radius: {Radius.LG};
        padding: 12px 24px;
        font-weight: 600;
        font-size: 14px;
        box-shadow: 0 4px 14px {ColorPalette.PRIMARY}55;
    """
    
    PRIMARY_HOVER = f"""
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {ColorPalette.PRIMARY_LIGHT},
            stop:1 #C084FC);
        transform: translateY(-2px);
        box-shadow: 0 8px 25px {ColorPalette.PRIMARY}80;
    """
    
    SECONDARY = f"""
        background: {ColorPalette.PRIMARY}15;
        border: 1px solid {ColorPalette.PRIMARY}40;
        color: {ColorPalette.PRIMARY_LIGHT};
        border-radius: {Radius.LG};
        padding: 12px 24px;
        font-weight: 500;
    """
    
    SECONDARY_HOVER = f"""
        background: {ColorPalette.PRIMARY}30;
        border-color: {ColorPalette.PRIMARY};
        color: {ColorPalette.TEXT_PRIMARY};
    """


class CardStyles:
    """卡片样式"""
    
    DEFAULT = f"""
        background: linear-gradient(145deg, #1A1A24 0%, #16161F 100%);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: {Radius.LG};
        padding: 20px;
    """
    
    HOVER = f"""
        border-color: {ColorPalette.PRIMARY}50;
        background: linear-gradient(145deg, #1E1E2A 0%, #1A1A24 100%);
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    """
    
    GLASS = f"""
        background: rgba(28, 28, 40, 0.7);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: {Radius.XL};
        padding: 24px;
    """


class InputStyles:
    """输入框样式"""
    
    DEFAULT = f"""
        background: rgba(12, 12, 18, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: {Radius.LG};
        padding: 14px 16px;
        color: {ColorPalette.TEXT_PRIMARY};
        font-size: 14px;
    """
    
    FOCUS = f"""
        border-color: {ColorPalette.PRIMARY};
        box-shadow: 0 0 0 4px {ColorPalette.PRIMARY}25;
    """


def get_button_styles(button_type: str = "primary") -> str:
    """获取按钮样式"""
    styles = {
        "primary": ButtonStyles.PRIMARY,
        "secondary": ButtonStyles.SECONDARY,
        "success": ButtonStyles.SECONDARY.replace(ColorPalette.PRIMARY, ColorPalette.SUCCESS),
        "danger": ButtonStyles.SECONDARY.replace(ColorPalette.PRIMARY, ColorPalette.ERROR),
    }
    return styles.get(button_type, ButtonStyles.PRIMARY)


def get_card_styles(card_type: str = "default") -> str:
    """获取卡片样式"""
    styles = {
        "default": CardStyles.DEFAULT,
        "glass": CardStyles.GLASS,
    }
    return styles.get(card_type, CardStyles.DEFAULT)
