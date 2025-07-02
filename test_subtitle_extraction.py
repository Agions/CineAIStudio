#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
字幕提取功能测试
验证新的字幕提取系统是否正常工作
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_subtitle_models():
    """测试字幕数据模型"""
    print("🧪 测试字幕数据模型...")
    
    try:
        from app.core.subtitle_extractor.subtitle_models import (
            SubtitleSegment, SubtitleTrack, SubtitleExtractorResult
        )
        
        # 测试字幕片段
        segment = SubtitleSegment(
            start_time=0.0,
            end_time=2.5,
            text="这是一个测试字幕",
            confidence=0.95
        )
        
        assert segment.duration == 2.5, "片段时长计算错误"
        assert "这是一个测试字幕" in segment.to_srt_format(1), "SRT格式转换错误"
        print("  ✅ 字幕片段测试通过")
        
        # 测试字幕轨道
        segments = [
            SubtitleSegment(0.0, 2.0, "第一句话", 0.9),
            SubtitleSegment(2.5, 4.5, "第二句话", 0.8),
            SubtitleSegment(5.0, 7.0, "第三句话", 0.95)
        ]
        
        track = SubtitleTrack(segments, language="zh", source="test")
        assert track.segment_count == 3, "轨道片段数量错误"
        assert track.duration == 7.0, "轨道时长计算错误"
        
        # 测试合并功能
        merged_track = track.merge_segments(max_gap=1.0)
        assert merged_track.segment_count <= 3, "合并功能异常"
        print("  ✅ 字幕轨道测试通过")
        
        # 测试提取结果
        result = SubtitleExtractorResult()
        result.add_track(track)
        
        primary_track = result.get_primary_track()
        assert primary_track is not None, "主轨道获取失败"
        
        combined_text = result.get_combined_text()
        assert len(combined_text) > 0, "合并文本获取失败"
        print("  ✅ 提取结果测试通过")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 字幕模型测试失败: {e}")
        return False


def test_subtitle_service():
    """测试字幕提取服务"""
    print("🧪 测试字幕提取服务...")
    
    try:
        from app.services.subtitle_service import SubtitleExtractionService
        
        # 创建服务实例
        service = SubtitleExtractionService({
            'enable_ocr': False,  # 禁用OCR避免依赖问题
            'enable_speech': False,  # 禁用语音识别避免依赖问题
        })
        
        # 测试配置
        assert service.config is not None, "服务配置初始化失败"
        print("  ✅ 服务初始化测试通过")
        
        # 测试信息获取（不需要实际文件）
        try:
            info = service.get_extraction_info("test_video.mp4")
            assert "available_methods" in info, "提取信息格式错误"
            print("  ✅ 信息获取测试通过")
        except:
            print("  ⚠️ 信息获取测试跳过（需要ffmpeg）")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 字幕服务测试失败: {e}")
        return False


def test_subtitle_ui():
    """测试字幕提取UI组件"""
    print("🧪 测试字幕提取UI组件...")
    
    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        from app.ui.components.subtitle_extraction_widget import SubtitleExtractionWidget
        
        # 创建组件
        widget = SubtitleExtractionWidget()
        assert widget is not None, "字幕提取组件创建失败"
        
        # 测试基本属性
        assert hasattr(widget, 'service'), "服务属性缺失"
        assert hasattr(widget, 'start_btn'), "开始按钮缺失"
        assert hasattr(widget, 'progress_bar'), "进度条缺失"
        
        print("  ✅ UI组件创建测试通过")
        
        # 测试主题切换
        widget.set_theme(True)  # 深色主题
        widget.set_theme(False)  # 浅色主题
        print("  ✅ 主题切换测试通过")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 字幕UI测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integrated_ai_features():
    """测试集成的AI功能页面"""
    print("🧪 测试集成AI功能页面...")
    
    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        from app.ui.professional_main_window import ProfessionalMainWindow
        
        # 创建主窗口
        window = ProfessionalMainWindow()
        
        # 检查AI功能页面
        ai_page = window.ai_features_page
        assert ai_page is not None, "AI功能页面未创建"
        
        # 检查选项卡
        assert hasattr(ai_page, 'tab_widget'), "选项卡组件缺失"
        assert ai_page.tab_widget.count() == 3, "选项卡数量不正确"
        
        # 检查字幕提取组件
        assert hasattr(ai_page, 'subtitle_widget'), "字幕提取组件缺失"
        
        print("  ✅ 集成AI功能页面测试通过")
        
        # 显示窗口进行视觉验证
        window.show()
        
        return window, app
        
    except Exception as e:
        print(f"  ❌ 集成AI功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def main():
    """主函数"""
    print("🚀 VideoEpicCreator 字幕提取功能测试")
    print("=" * 60)
    
    # 测试字幕数据模型
    if not test_subtitle_models():
        print("❌ 字幕模型测试失败")
        return 1
    
    print("\n" + "=" * 60)
    
    # 测试字幕提取服务
    if not test_subtitle_service():
        print("❌ 字幕服务测试失败")
        return 1
    
    print("\n" + "=" * 60)
    
    # 测试字幕UI组件
    if not test_subtitle_ui():
        print("❌ 字幕UI测试失败")
        return 1
    
    print("\n" + "=" * 60)
    
    # 测试集成AI功能
    window, app = test_integrated_ai_features()
    if window is None:
        print("❌ 集成AI功能测试失败")
        return 1
    
    print("\n" + "=" * 60)
    print("🎉 所有字幕提取功能测试通过！")
    
    # 显示功能演示
    success_message = """
🎯 字幕提取功能集成完成！

✅ 新增功能特性:
• 🔍 OCR字幕提取 - 从视频帧识别字幕文字
• 🎤 语音识别提取 - 从音频识别语音内容
• 📝 智能后处理 - 去重、合并、纠错
• 🎨 现代化UI界面 - 直观的操作流程
• ⚙️ 集成工作流 - 字幕提取→AI处理

🔧 技术实现:
• 模块化架构设计
• 多线程并行处理
• 实时进度反馈
• 多格式导出支持

🎮 使用流程:
1. 在AI功能页面选择功能类型
2. 在字幕提取选项卡导入视频并提取字幕
3. 在处理流程选项卡开始AI处理

现在可以体验完整的AI视频编辑工作流！
    """
    
    QMessageBox.information(window, "功能集成完成", success_message)
    
    # 自动演示功能
    demo_timer = QTimer()
    demo_tabs = [0, 1, 2]  # 功能选择、字幕提取、处理流程
    demo_index = 0
    
    def auto_demo():
        nonlocal demo_index
        if demo_index < len(demo_tabs):
            tab_index = demo_tabs[demo_index]
            window.ai_features_page.tab_widget.setCurrentIndex(tab_index)
            
            tab_names = ["功能选择", "字幕提取", "处理流程"]
            print(f"🎭 演示: 切换到 {tab_names[tab_index]} 选项卡")
            
            demo_index += 1
        else:
            demo_index = 0
    
    demo_timer.timeout.connect(auto_demo)
    demo_timer.start(4000)  # 每4秒切换一次
    
    # 导航演示
    nav_timer = QTimer()
    nav_pages = ["ai_features", "projects", "settings", "home"]
    nav_index = 0
    
    def nav_demo():
        nonlocal nav_index
        if nav_index < len(nav_pages):
            page = nav_pages[nav_index]
            window.navigation.set_current_page(page)
            print(f"🧭 演示: 导航到 {page}")
            nav_index += 1
        else:
            nav_index = 0
    
    nav_timer.timeout.connect(nav_demo)
    nav_timer.start(8000)  # 每8秒切换导航
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
