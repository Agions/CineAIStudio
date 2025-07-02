#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VideoEpicCreator 综合UI测试
测试所有增强功能的完整性和稳定性
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_complete_application():
    """测试完整应用程序"""
    print("🚀 启动VideoEpicCreator完整应用测试")
    print("=" * 60)
    
    try:
        from app.ui.enhanced_main_window import EnhancedMainWindow
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 创建主窗口
        window = EnhancedMainWindow()
        window.show()
        
        print("✅ 主窗口创建成功")
        
        # 测试导航功能
        def test_navigation():
            print("🧪 测试导航功能...")
            
            # 测试切换到不同页面
            pages = ["home", "projects", "ai_features", "settings"]
            for page in pages:
                window.navigation.set_current_page(page)
                current = window.navigation.get_current_page()
                assert current == page, f"导航切换失败: 期望 {page}, 实际 {current}"
                print(f"  ✅ 导航到 {page} 成功")
            
            print("✅ 导航功能测试通过")
        
        # 测试主题切换
        def test_theme_switching():
            print("🧪 测试主题切换...")
            
            theme_manager = window.theme_manager
            
            # 测试浅色主题
            theme_manager.set_theme("light")
            current = theme_manager.get_current_theme().value
            assert current == "light", f"主题切换失败: 期望 light, 实际 {current}"
            print("  ✅ 浅色主题切换成功")
            
            # 测试深色主题
            theme_manager.set_theme("dark")
            current = theme_manager.get_current_theme().value
            assert current == "dark", f"主题切换失败: 期望 dark, 实际 {current}"
            print("  ✅ 深色主题切换成功")
            
            print("✅ 主题切换功能测试通过")
        
        # 测试设置面板
        def test_settings_panel():
            print("🧪 测试设置面板...")
            
            # 切换到设置页面
            window.navigation.set_current_page("settings")
            
            # 检查设置面板是否正确加载
            settings_page = window.settings_page
            assert settings_page is not None, "设置面板未正确加载"
            
            # 检查主题切换组件
            assert hasattr(settings_page, 'general_card'), "通用设置卡片未找到"
            
            print("✅ 设置面板测试通过")
        
        # 测试AI功能面板
        def test_ai_features():
            print("🧪 测试AI功能面板...")
            
            # 切换到AI功能页面
            window.navigation.set_current_page("ai_features")
            
            # 检查AI功能页面
            ai_page = window.ai_features_page
            assert ai_page is not None, "AI功能页面未正确加载"
            
            # 检查选项卡
            assert hasattr(ai_page, 'tab_widget'), "AI功能选项卡未找到"
            assert ai_page.tab_widget.count() >= 3, "AI功能选项卡数量不足"
            
            print("✅ AI功能面板测试通过")
        
        # 测试项目管理
        def test_project_management():
            print("🧪 测试项目管理...")
            
            # 切换到项目管理页面
            window.navigation.set_current_page("projects")
            
            # 检查项目管理页面
            projects_page = window.projects_page
            assert projects_page is not None, "项目管理页面未正确加载"
            
            print("✅ 项目管理测试通过")
        
        # 运行所有测试
        test_navigation()
        test_theme_switching()
        test_settings_panel()
        test_ai_features()
        test_project_management()
        
        print("\n" + "=" * 60)
        print("🎉 所有功能测试通过！")
        print("📱 应用程序界面现代化升级完成")
        
        # 显示功能演示信息
        demo_info = """
🎨 VideoEpicCreator UI/UX 升级完成！

✨ 新功能特性:
• 🎨 现代化主题系统 (浅色/深色主题)
• 🧭 简洁优雅的左侧导航
• ⚙️ 重新设计的设置界面
• 🎬 增强的AI功能面板
• 📁 现代化项目管理界面
• 🎯 专业的Ant Design设计风格

🔧 技术改进:
• 统一的主题管理系统
• 响应式布局设计
• 组件化架构
• 更好的用户体验
• 稳定的功能实现

🎮 使用指南:
1. 使用左侧导航切换功能模块
2. 在设置中切换主题
3. 体验三大核心AI功能
4. 管理视频和项目文件

享受全新的视频编辑体验！
        """
        
        QMessageBox.information(window, "升级完成", demo_info)
        
        # 设置自动演示
        demo_timer = QTimer()
        demo_pages = ["home", "ai_features", "projects", "settings"]
        demo_index = 0
        
        def auto_demo():
            nonlocal demo_index
            if demo_index < len(demo_pages):
                page = demo_pages[demo_index]
                window.navigation.set_current_page(page)
                print(f"🎭 演示: 切换到 {page}")
                demo_index += 1
            else:
                demo_index = 0
        
        demo_timer.timeout.connect(auto_demo)
        demo_timer.start(3000)  # 每3秒切换一次
        
        return app.exec()
        
    except Exception as e:
        print(f"❌ 应用程序测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


def test_stability():
    """测试应用稳定性"""
    print("🔧 测试应用稳定性...")
    
    try:
        # 测试导入所有模块
        modules_to_test = [
            "app.ui.enhanced_main_window",
            "app.ui.theme_manager",
            "app.ui.components.modern_navigation",
            "app.ui.components.theme_toggle",
            "app.ui.modern_settings_panel",
            "app.ui.modern_video_management",
            "app.ui.pages.home_page",
            "app.ui.pages.ai_features_page",
        ]
        
        for module_name in modules_to_test:
            try:
                __import__(module_name)
                print(f"  ✅ {module_name} 导入成功")
            except Exception as e:
                print(f"  ❌ {module_name} 导入失败: {e}")
                return False
        
        print("✅ 所有模块导入测试通过")
        
        # 测试配置文件
        from app.config.settings_manager import SettingsManager
        settings = SettingsManager()
        
        # 测试基本设置操作
        settings.set_setting("test.key", "test_value")
        value = settings.get_setting("test.key")
        assert value == "test_value", "设置读写测试失败"
        
        print("✅ 配置系统测试通过")
        
        return True
        
    except Exception as e:
        print(f"❌ 稳定性测试失败: {e}")
        return False


def main():
    """主函数"""
    print("🎯 VideoEpicCreator 综合测试套件")
    print("=" * 60)
    
    # 稳定性测试
    if not test_stability():
        print("❌ 稳定性测试失败，退出")
        return 1
    
    print("\n" + "=" * 60)
    
    # 完整应用测试
    return test_complete_application()


if __name__ == "__main__":
    sys.exit(main())
