#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试增强版UI的脚本
验证主题切换、导航功能、组件可见性等
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_theme_manager():
    """测试主题管理器"""
    print("🧪 测试主题管理器...")
    
    try:
        from app.ui.theme_manager import get_theme_manager, ThemeType
        
        theme_manager = get_theme_manager()
        
        # 测试主题切换
        print("  - 测试浅色主题...")
        theme_manager.set_theme("light")
        assert theme_manager.get_current_theme() == ThemeType.LIGHT
        
        print("  - 测试深色主题...")
        theme_manager.set_theme("dark")
        assert theme_manager.get_current_theme() == ThemeType.DARK
        
        # 测试颜色获取
        colors = theme_manager.get_theme_colors()
        assert 'primary' in colors
        assert 'background' in colors
        
        print("  ✅ 主题管理器测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 主题管理器测试失败: {e}")
        return False


def test_navigation_component():
    """测试导航组件"""
    print("🧪 测试导航组件...")
    
    try:
        from app.ui.components.modern_navigation import ModernNavigation
        
        nav = ModernNavigation()
        
        # 测试导航按钮
        assert "home" in nav.nav_buttons
        assert "projects" in nav.nav_buttons
        assert "ai_features" in nav.nav_buttons
        assert "settings" in nav.nav_buttons
        
        # 测试页面切换
        nav.set_current_page("projects")
        assert nav.get_current_page() == "projects"
        
        print("  ✅ 导航组件测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 导航组件测试失败: {e}")
        return False


def test_theme_toggle():
    """测试主题切换组件"""
    print("🧪 测试主题切换组件...")
    
    try:
        from app.ui.components.theme_toggle import ThemeToggle, CompactThemeToggle
        
        # 测试完整主题切换组件
        theme_toggle = ThemeToggle()
        theme_toggle.set_theme("light")
        
        # 测试紧凑主题切换组件
        compact_toggle = CompactThemeToggle()
        
        print("  ✅ 主题切换组件测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 主题切换组件测试失败: {e}")
        return False


def test_enhanced_main_window():
    """测试增强版主窗口"""
    print("🧪 测试增强版主窗口...")
    
    try:
        from app.ui.enhanced_main_window import EnhancedMainWindow
        
        window = EnhancedMainWindow()
        
        # 检查基本组件
        assert hasattr(window, 'navigation')
        assert hasattr(window, 'stacked_widget')
        assert hasattr(window, 'theme_manager')
        assert hasattr(window, 'settings_manager')
        
        # 检查页面数量
        assert window.stacked_widget.count() >= 4  # 至少4个页面
        
        print("  ✅ 增强版主窗口测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 增强版主窗口测试失败: {e}")
        return False


def test_ui_pages():
    """测试UI页面"""
    print("🧪 测试UI页面...")
    
    try:
        # 测试首页
        from app.ui.pages.home_page import HomePage
        from app.core.project_manager import ProjectManager
        from app.config.settings_manager import SettingsManager
        from app.ai import AIManager
        
        settings_manager = SettingsManager()
        project_manager = ProjectManager(settings_manager)
        ai_manager = AIManager(settings_manager)
        
        home_page = HomePage(project_manager, ai_manager)
        
        # 测试AI功能页面
        from app.ui.pages.ai_features_page import AIFeaturesPage
        ai_page = AIFeaturesPage(ai_manager)
        
        print("  ✅ UI页面测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ UI页面测试失败: {e}")
        return False


def test_button_visibility():
    """测试按钮可见性"""
    print("🧪 测试按钮可见性...")

    try:
        from PyQt6.QtWidgets import QPushButton, QWidget, QVBoxLayout
        from app.ui.theme_manager import get_theme_manager

        # 创建测试按钮
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 主要按钮
        primary_btn = QPushButton("主要按钮")
        primary_btn.setObjectName("primary_button")
        layout.addWidget(primary_btn)

        # 默认按钮
        default_btn = QPushButton("默认按钮")
        layout.addWidget(default_btn)

        # 危险按钮
        danger_btn = QPushButton("危险按钮")
        danger_btn.setObjectName("danger_button")
        layout.addWidget(danger_btn)

        # 应用主题
        theme_manager = get_theme_manager()
        theme_manager.set_theme("light")

        # 显示widget以确保按钮可见
        widget.show()

        # 检查按钮是否可见（基本检查）
        assert primary_btn.isVisible()
        assert default_btn.isVisible()
        assert danger_btn.isVisible()

        # 检查按钮是否有正确的样式
        assert primary_btn.objectName() == "primary_button"
        assert danger_btn.objectName() == "danger_button"

        widget.close()

        print("  ✅ 按钮可见性测试通过")
        return True

    except Exception as e:
        print(f"  ❌ 按钮可见性测试失败: {e}")
        return False


def run_visual_test():
    """运行可视化测试"""
    print("🎨 启动可视化测试...")
    
    try:
        from app.ui.enhanced_main_window import EnhancedMainWindow
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 创建主窗口
        window = EnhancedMainWindow()
        window.show()
        
        # 显示测试信息
        QMessageBox.information(
            window, 
            "UI测试", 
            "请测试以下功能：\n\n"
            "1. 左侧导航切换\n"
            "2. 主题切换（浅色/深色）\n"
            "3. 按钮可见性和点击\n"
            "4. 各个页面的显示\n"
            "5. 设置面板功能\n\n"
            "关闭此对话框后，应用将保持运行以供测试。"
        )
        
        return window
        
    except Exception as e:
        print(f"❌ 可视化测试启动失败: {e}")
        return None


def main():
    """主测试函数"""
    print("🚀 开始VideoEpicCreator增强UI测试")
    print("=" * 50)
    
    # 创建应用实例
    app = QApplication(sys.argv)
    app.setApplicationName("VideoEpicCreator UI Test")
    
    # 运行单元测试
    tests = [
        test_theme_manager,
        test_navigation_component,
        test_theme_toggle,
        test_enhanced_main_window,
        test_ui_pages,
        test_button_visibility
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        print("🎉 所有测试通过！启动可视化测试...")
        
        # 启动可视化测试
        window = run_visual_test()
        if window:
            # 设置定时器自动切换主题进行演示
            def demo_theme_switch():
                theme_manager = window.theme_manager
                current = theme_manager.get_current_theme().value
                new_theme = "dark" if current == "light" else "light"
                theme_manager.set_theme(new_theme)
                print(f"🎨 演示: 切换到{new_theme}主题")
            
            # 每10秒自动切换主题
            timer = QTimer()
            timer.timeout.connect(demo_theme_switch)
            timer.start(10000)  # 10秒
            
            return app.exec()
    else:
        print("❌ 存在测试失败，请检查代码")
        return 1


if __name__ == "__main__":
    sys.exit(main())
