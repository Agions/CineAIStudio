#!/usr/bin/env python3
"""
VideoForge 主程序入口
专业的AI视频编辑器
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置日志
logger = logging.getLogger("VideoForge")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def main():
    """主函数"""
    from app.utils.version import __version__

    logger.info("=" * 50)
    logger.info("🎬 VideoForge - AI 视频创作工具")
    logger.info("=" * 50)
    logger.info(f"版本: {__version__}")
    logger.info("作者: Agions")

    # 检查依赖
    check_dependencies()

    # 启动 GUI
    try:
        from app.ui.main.main_window import MainWindow
        from app.core.application import Application
        from PySide6.QtWidgets import QApplication

        qt_app = QApplication(sys.argv)
        qt_app.setApplicationName("VideoForge")
        qt_app.setApplicationVersion(str(__version__))
        
        # 初始化核心应用程序实例
        # 这里传入简单的配置字典作为示例，实际可从配置文件加载
        app_config = {}
        application = Application(app_config)
        
        # 初始化应用程序服务
        if not application.initialize(sys.argv):
            logger.error("应用程序初始化失败")
            sys.exit(1)
            
        # 启动应用程序
        if not application.start():
            logger.error("应用程序启动失败")
            sys.exit(1)
        
        # 创建主窗口并注入 application 实例
        window = MainWindow(application)
        window.show()
        
        exit_code = qt_app.exec()
        
        # 关闭应用程序
        application.shutdown()
        
        sys.exit(exit_code)
        
    except ImportError as e:
        logger.warning(f"GUI 模块未找到: {e}")
        logger.info("正在启动命令行模式...")
        run_cli_mode()


def check_dependencies():
    """检查依赖"""
    logger.info("检查依赖...")
    
    required = {
        'ffmpeg': 'FFmpeg 视频处理',
        'ffprobe': 'FFprobe 视频分析',
    }
    
    import shutil
    
    missing = []
    for cmd, desc in required.items():
        if shutil.which(cmd):
            logger.info(f"  ✅ {desc}")
        else:
            logger.error(f"  ❌ {desc} - 未找到")
            missing.append(cmd)
    
    if missing:
        logger.warning(f"缺少依赖: {', '.join(missing)}")
        logger.info("请安装 FFmpeg: https://ffmpeg.org/download.html")


def run_cli_mode():
    """命令行模式"""
    print("VideoForge 命令行模式")
    print("-" * 30)
    print("可用功能:")
    print("  1. AI 视频解说")
    print("  2. AI 视频混剪")
    print("  3. AI 第一人称独白")
    print("  4. 剪映草稿导出")
    print("  5. 退出")
    print()
    
    while True:
        try:
            choice = input("请选择功能 (1-5): ").strip()
            
            if choice == '1':
                run_commentary()
            elif choice == '2':
                run_mashup()
            elif choice == '3':
                run_monologue()
            elif choice == '4':
                run_export()
            elif choice == '5':
                print("\n再见! 👋")
                break
            else:
                print("无效选择，请输入 1-5")
                
        except KeyboardInterrupt:
            print("\n\n再见! 👋")
            break
        except Exception as e:
            print(f"错误: {e}")


def run_commentary():
    """运行解说功能"""
    print("\n--- AI 视频解说 ---")
    
    video_path = input("输入视频路径: ").strip()
    if not video_path or not Path(video_path).exists():
        print("视频文件不存在")
        return
    
    topic = input("输入解说主题: ").strip() or "分析这段视频内容"
    
    from app.services.video import CommentaryMaker, CommentaryStyle
    
    maker = CommentaryMaker(voice_provider="edge")
    
    def on_progress(stage, progress):
        print(f"  [{stage}] {progress*100:.0f}%")
    
    maker.set_progress_callback(on_progress)
    
    print("\n创建项目...")
    project = maker.create_project(
        source_video=video_path,
        topic=topic,
        style=CommentaryStyle.EXPLAINER,
    )
    
    print(f"视频时长: {project.video_duration:.1f}秒")
    print(f"场景数量: {len(project.scenes)}")
    
    # 询问是否使用自定义文案
    use_custom = input("\n使用自定义文案? (y/n): ").strip().lower() == 'y'
    
    if use_custom:
        print("输入文案 (输入空行结束):")
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        custom_script = "\n".join(lines)
        maker.generate_script(project, custom_script=custom_script)
    else:
        print("注意: 自动生成文案需要设置 OPENAI_API_KEY")
        try:
            maker.generate_script(project)
        except ValueError as e:
            print(f"错误: {e}")
            print("使用默认文案...")
            maker.generate_script(project, custom_script="欢迎观看这段视频。这是一段精彩的内容。希望大家喜欢。")
    
    print("\n生成配音...")
    maker.generate_voice(project)
    
    print("生成字幕...")
    maker.generate_captions(project)
    
    output_dir = input("\n输入剪映草稿目录 (默认 ./output/jianying_drafts): ").strip()
    output_dir = output_dir or "./output/jianying_drafts"
    
    print("导出草稿...")
    draft_path = maker.export_to_jianying(project, output_dir)
    
    print(f"\n✅ 完成! 草稿路径: {draft_path}")


def run_mashup():
    """运行混剪功能"""
    print("\n--- AI 视频混剪 ---")
    
    print("输入视频路径 (每行一个，空行结束):")
    videos = []
    while True:
        path = input().strip()
        if not path:
            break
        if Path(path).exists():
            videos.append(path)
        else:
            print(f"  文件不存在: {path}")
    
    if len(videos) < 2:
        print("至少需要 2 个视频")
        return
    
    music = input("输入背景音乐路径 (可选): ").strip()
    if music and not Path(music).exists():
        print("音乐文件不存在，将不使用背景音乐")
        music = None
    
    duration = input("目标时长 (默认 30秒): ").strip()
    duration = float(duration) if duration else 30.0
    
    from app.services.video import MashupMaker, MashupStyle
    
    maker = MashupMaker()
    
    def on_progress(stage, progress):
        print(f"  [{stage}] {progress*100:.0f}%")
    
    maker.set_progress_callback(on_progress)
    
    print("\n创建项目...")
    project = maker.create_project(
        source_videos=videos,
        background_music=music,
        target_duration=duration,
        style=MashupStyle.FAST_PACED,
    )
    
    print(f"可用片段: {len(project.all_clips)}")
    print(f"检测节拍: {len(project.beats)}")
    
    print("\n智能混剪...")
    maker.auto_mashup(project)
    
    print(f"选中片段: {len(project.selected_clips)}")
    print(f"总时长: {project.total_duration:.1f}秒")
    
    output_dir = input("\n输入剪映草稿目录 (默认 ./output/jianying_drafts): ").strip()
    output_dir = output_dir or "./output/jianying_drafts"
    
    print("导出草稿...")
    draft_path = maker.export_to_jianying(project, output_dir)
    
    print(f"\n✅ 完成! 草稿路径: {draft_path}")


def run_monologue():
    """运行独白功能"""
    print("\n--- AI 第一人称独白 ---")
    
    video_path = input("输入视频路径: ").strip()
    if not video_path or not Path(video_path).exists():
        print("视频文件不存在")
        return
    
    context = input("输入场景描述: ").strip() or "独自一人，思绪万千"
    emotion = input("输入情感 (惆怅/开心/平静): ").strip() or "惆怅"
    
    from app.services.video import MonologueMaker, MonologueStyle
    
    maker = MonologueMaker(voice_provider="edge")
    
    def on_progress(stage, progress):
        print(f"  [{stage}] {progress*100:.0f}%")
    
    maker.set_progress_callback(on_progress)
    
    print("\n创建项目...")
    project = maker.create_project(
        source_video=video_path,
        context=context,
        emotion=emotion,
        style=MonologueStyle.MELANCHOLIC,
    )
    
    print(f"视频时长: {project.video_duration:.1f}秒")
    
    # 询问自定义独白
    use_custom = input("\n使用自定义独白? (y/n): ").strip().lower() == 'y'
    
    if use_custom:
        print("输入独白 (输入空行结束):")
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        custom_script = "\n".join(lines)
        maker.generate_script(project, custom_script=custom_script)
    else:
        try:
            maker.generate_script(project)
        except ValueError:
            default = """
有些事情，只有自己知道。
那些藏在心底的话，从未对人说起。
也许，沉默才是最好的表达。
"""
            maker.generate_script(project, custom_script=default)
    
    print("\n生成配音...")
    maker.generate_voice(project)
    
    print("生成字幕...")
    maker.generate_captions(project, style="cinematic")
    
    output_dir = input("\n输入剪映草稿目录: ").strip() or "./output/jianying_drafts"
    
    print("导出草稿...")
    draft_path = maker.export_to_jianying(project, output_dir)
    
    print(f"\n✅ 完成! 草稿路径: {draft_path}")


def run_export():
    """运行导出功能"""
    print("\n--- 剪映草稿导出 ---")
    
    from app.services.export import (
        JianyingExporter, JianyingConfig,
        Track, TrackType, Segment, TimeRange,
        VideoMaterial,
    )
    
    video_path = input("输入视频路径: ").strip()
    if not video_path or not Path(video_path).exists():
        print("视频文件不存在")
        return
    
    project_name = input("项目名称: ").strip() or "新建项目"
    
    exporter = JianyingExporter(JianyingConfig(
        canvas_ratio="9:16",
        copy_materials=True,
    ))
    
    draft = exporter.create_draft(project_name)
    
    # 添加视频
    video_track = Track(type=TrackType.VIDEO, attribute=1)
    draft.add_track(video_track)
    
    video_material = VideoMaterial(path=video_path)
    draft.add_video(video_material)
    
    segment = Segment(
        material_id=video_material.id,
        source_timerange=TimeRange.from_seconds(0, 30),
        target_timerange=TimeRange.from_seconds(0, 30),
    )
    video_track.add_segment(segment)
    
    output_dir = input("\n输入剪映草稿目录: ").strip() or "./output/jianying_drafts"
    
    draft_path = exporter.export(draft, output_dir)
    
    print(f"\n✅ 完成! 草稿路径: {draft_path}")


if __name__ == '__main__':
    main()
