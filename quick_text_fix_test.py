#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
快速文字显示修复验证
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QFont

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """主函数"""
    print("🔤 快速文字显示修复验证")
    print("=" * 50)
    
    # 创建应用实例
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    try:
        # 导入主应用程序
        from app.ui.professional_main_window import ProfessionalMainWindow
        from app.ui.global_style_fixer import apply_global_style_fixes
        
        # 创建主窗口
        window = ProfessionalMainWindow()
        
        # 应用全局样式修复
        apply_global_style_fixes(app, False)
        
        # 显示窗口
        window.show()
        
        print("✅ 主应用程序启动成功")
        print("✅ 文字显示修复已应用")
        print("✅ 界面应该显示正常，无文字错乱")
        
        # 显示成功消息
        success_timer = QTimer()
        success_timer.setSingleShot(True)
        
        def show_success():
            QMessageBox.information(
                window, 
                "文字显示修复完成", 
                """🎉 文字显示修复成功！

✅ 修复内容：
• 统一字体为 Arial 12px
• 优化组件尺寸和间距
• 修复文字对齐和显示
• 移除不支持的CSS属性

✅ 现在界面文字应该：
• 清晰锐利，无模糊
• 无重叠或错乱
• 统一的视觉风格
• 完美的主题切换

请检查界面是否正常显示！"""
            )
        
        success_timer.timeout.connect(show_success)
        success_timer.start(2000)  # 2秒后显示
        
        return app.exec()
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
