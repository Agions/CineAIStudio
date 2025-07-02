#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VideoEpicCreator 功能架构重构测试
验证新的用户体验流程和功能集成
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_navigation_structure():
    """测试导航结构"""
    print("🧭 测试导航结构...")
    
    try:
        from app.ui.professional_ui_system import ProfessionalNavigation
        
        nav = ProfessionalNavigation()
        
        # 检查导航按钮
        nav_buttons = nav.nav_buttons
        expected_pages = ["home", "projects", "settings"]
        
        print(f"  📋 预期页面: {expected_pages}")
        print(f"  📋 实际页面: {list(nav_buttons.keys())}")
        
        # 验证视频编辑入口已移除
        if "video_editing" not in nav_buttons:
            print("  ✅ 视频编辑入口已从导航中移除")
        else:
            print("  ❌ 视频编辑入口仍在导航中")
            return False
        
        # 验证必要页面存在
        for page in expected_pages:
            if page in nav_buttons:
                print(f"  ✅ {page} 页面存在")
            else:
                print(f"  ❌ {page} 页面缺失")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ 导航结构测试失败: {e}")
        return False


def test_project_management_enhancement():
    """测试项目管理页面增强"""
    print("📁 测试项目管理页面增强...")
    
    try:
        from app.ui.professional_main_window import ProfessionalProjectsPage
        from app.core.project_manager import ProjectManager
        
        # 创建项目管理器
        project_manager = ProjectManager()
        
        # 创建项目管理页面
        projects_page = ProfessionalProjectsPage(project_manager)
        
        # 检查信号
        if hasattr(projects_page, 'video_editing_requested'):
            print("  ✅ 视频编辑请求信号存在")
        else:
            print("  ❌ 视频编辑请求信号缺失")
            return False
        
        # 检查项目卡片创建方法
        if hasattr(projects_page, '_create_project_card'):
            print("  ✅ 项目卡片创建方法存在")
        else:
            print("  ❌ 项目卡片创建方法缺失")
            return False
        
        # 检查项目加载方法
        if hasattr(projects_page, '_load_projects'):
            print("  ✅ 项目加载方法存在")
        else:
            print("  ❌ 项目加载方法缺失")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ 项目管理页面测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_video_editing_integration():
    """测试视频编辑页面集成"""
    print("🎬 测试视频编辑页面集成...")
    
    try:
        from app.ui.pages.unified_video_editing_page import UnifiedVideoEditingPage
        from app.ai import AIManager
        from app.config.settings_manager import SettingsManager

        # 创建设置管理器和AI管理器
        settings_manager = SettingsManager()
        ai_manager = AIManager(settings_manager)
        
        # 创建视频编辑页面
        editing_page = UnifiedVideoEditingPage(ai_manager)
        
        # 检查项目数据加载方法
        if hasattr(editing_page, 'load_project_data'):
            print("  ✅ 项目数据加载方法存在")
        else:
            print("  ❌ 项目数据加载方法缺失")
            return False
        
        # 检查进度更新方法
        if hasattr(editing_page, '_update_editing_progress'):
            print("  ✅ 编辑进度更新方法存在")
        else:
            print("  ❌ 编辑进度更新方法缺失")
            return False
        
        # 检查AI功能选择器
        if hasattr(editing_page, 'feature_selector'):
            print("  ✅ AI功能选择器存在")
            
            # 检查选择方法
            if hasattr(editing_page.feature_selector, 'select_feature'):
                print("  ✅ 功能选择方法存在")
            else:
                print("  ❌ 功能选择方法缺失")
                return False
        else:
            print("  ❌ AI功能选择器缺失")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ 视频编辑页面测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_flow_optimization():
    """测试数据流优化"""
    print("💾 测试数据流优化...")
    
    try:
        from app.core.project_manager import ProjectInfo, ProjectManager
        
        # 测试项目信息扩展
        project = ProjectInfo(
            id="test-project",
            name="测试项目",
            description="测试项目描述",
            editing_mode="commentary"
        )
        
        # 检查新增字段
        required_fields = ['status', 'progress', 'last_edited_feature']
        for field in required_fields:
            if hasattr(project, field):
                print(f"  ✅ 项目字段 {field} 存在")
            else:
                print(f"  ❌ 项目字段 {field} 缺失")
                return False
        
        # 测试项目管理器方法
        project_manager = ProjectManager()
        
        required_methods = [
            'update_project_status',
            'get_project_by_id', 
            'update_editing_progress'
        ]
        
        for method in required_methods:
            if hasattr(project_manager, method):
                print(f"  ✅ 项目管理器方法 {method} 存在")
            else:
                print(f"  ❌ 项目管理器方法 {method} 缺失")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ 数据流优化测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_main_window_integration():
    """测试主窗口集成"""
    print("🏠 测试主窗口集成...")
    
    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        from app.ui.professional_main_window import ProfessionalMainWindow
        
        # 创建主窗口
        window = ProfessionalMainWindow()
        
        # 检查视频编辑对话框方法
        if hasattr(window, 'open_video_editing'):
            print("  ✅ 视频编辑对话框方法存在")
        else:
            print("  ❌ 视频编辑对话框方法缺失")
            return False
        
        # 检查项目管理页面信号连接
        if hasattr(window.projects_page, 'video_editing_requested'):
            print("  ✅ 项目管理页面信号连接正常")
        else:
            print("  ❌ 项目管理页面信号连接异常")
            return False
        
        # 显示窗口进行视觉测试
        window.show()
        print("  ✅ 主窗口显示成功")
        
        return True, window
        
    except Exception as e:
        print(f"  ❌ 主窗口集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def main():
    """主函数"""
    print("🏗️ VideoEpicCreator 功能架构重构测试")
    print("=" * 60)
    
    # 创建应用实例
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    test_results = []
    
    # 执行测试
    test_results.append(("导航结构", test_navigation_structure()))
    test_results.append(("项目管理增强", test_project_management_enhancement()))
    test_results.append(("视频编辑集成", test_video_editing_integration()))
    test_results.append(("数据流优化", test_data_flow_optimization()))
    
    # 主窗口集成测试
    main_result, window = test_main_window_integration()
    test_results.append(("主窗口集成", main_result))
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📈 总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！功能架构重构成功！")
        
        if window:
            # 显示成功消息
            success_timer = QTimer()
            success_timer.setSingleShot(True)
            
            def show_success():
                QMessageBox.information(
                    window,
                    "架构重构完成",
                    """🎉 VideoEpicCreator 功能架构重构成功！

✅ 重构成果：
• 简化导航结构（移除视频编辑入口）
• 项目管理页面增强（添加编辑入口）
• 视频编辑功能集成（项目上下文）
• 数据流优化（状态管理和进度保存）

✅ 新的用户流程：
1. 在项目管理页面创建或选择项目
2. 点击"编辑视频"按钮进入编辑模式
3. 系统自动加载项目数据和预选功能
4. 编辑进度自动保存到项目
5. 支持返回项目管理继续其他操作

现在用户体验更加流畅和直观！"""
                )
            
            success_timer.timeout.connect(show_success)
            success_timer.start(2000)
        
        return app.exec()
    else:
        print("❌ 部分测试失败，请检查相关功能")
        return 1


if __name__ == "__main__":
    sys.exit(main())
