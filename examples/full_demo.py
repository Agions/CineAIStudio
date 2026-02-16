#!/usr/bin/env python3
"""
CineFlow 完整功能演示

此脚本演示如何使用真实视频素材创建 AI 视频内容。
运行前请确保 test_assets 目录中有测试素材。

用法:
    python examples/full_demo.py commentary  # 演示解说功能
    python examples/full_demo.py mashup      # 演示混剪功能
    python examples/full_demo.py monologue   # 演示独白功能
    python examples/full_demo.py all         # 演示所有功能
"""

import os
import sys
import argparse
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def setup_test_environment():
    """设置测试环境"""
    # 创建必要目录
    dirs = [
        "test_assets",
        "output/jianying_drafts",
        "output/videos",
        "output/audio",
    ]
    
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    
    print("📁 测试环境已准备")
    print(f"   项目目录: {project_root}")
    print(f"   素材目录: test_assets/")
    print(f"   输出目录: output/")


def check_assets():
    """检查测试素材"""
    assets = {
        "video": list(Path("test_assets").glob("*.mp4")),
        "audio": list(Path("test_assets").glob("*.mp3")),
    }
    
    print("\n📦 可用素材:")
    print(f"   视频: {len(assets['video'])} 个")
    for v in assets['video'][:5]:
        print(f"      - {v.name}")
    
    print(f"   音频: {len(assets['audio'])} 个")
    for a in assets['audio'][:3]:
        print(f"      - {a.name}")
    
    return assets


def demo_commentary(video_path: str = None):
    """
    演示 AI 视频解说功能
    """
    print("\n" + "=" * 60)
    print("🎙️ AI 视频解说演示")
    print("=" * 60)
    
    from app.services.video import CommentaryMaker, CommentaryStyle
    
    # 查找或使用指定视频
    if not video_path:
        videos = list(Path("test_assets").glob("*.mp4"))
        if not videos:
            print("\n⚠️ 没有找到视频素材，请将 .mp4 文件放入 test_assets 目录")
            return None
        video_path = str(videos[0])
    
    print(f"\n📹 使用视频: {video_path}")
    
    # 创建制作器
    maker = CommentaryMaker(voice_provider="edge")
    
    # 进度回调
    def on_progress(stage: str, progress: float):
        bar = "█" * int(progress * 20) + "░" * (20 - int(progress * 20))
        print(f"\r  [{stage}] {bar} {progress*100:.0f}%", end="", flush=True)
        if progress >= 1.0:
            print()
    
    maker.set_progress_callback(on_progress)
    
    # 创建项目
    print("\n🔍 分析视频...")
    project = maker.create_project(
        source_video=video_path,
        topic="分析这段视频的精彩内容",
        style=CommentaryStyle.EXPLAINER,
        output_dir="./output/commentary",
    )
    
    print(f"   视频时长: {project.video_duration:.1f}秒")
    print(f"   检测场景: {len(project.scenes)} 个")
    
    # 自定义解说文案
    custom_script = """
大家好，欢迎来到今天的视频。

让我们一起来分析这段精彩的内容。

首先，我们可以看到画面中呈现了...

接下来，让我们关注一下...

总的来说，这是一段非常有趣的内容，希望大家喜欢。
"""
    
    # 生成解说
    print("\n📝 生成解说文案...")
    maker.generate_script(project, custom_script=custom_script)
    print(f"   文案片段: {len(project.segments)} 个")
    
    # 生成配音
    print("\n🎤 生成 AI 配音...")
    maker.generate_voice(project)
    print(f"   配音时长: {project.total_duration:.1f}秒")
    
    # 生成字幕
    print("\n📜 生成动态字幕...")
    maker.generate_captions(project)
    
    # 导出
    print("\n📦 导出剪映草稿...")
    draft_path = maker.export_to_jianying(project, "./output/jianying_drafts")
    
    print(f"\n✅ 解说视频项目完成!")
    print(f"   草稿路径: {draft_path}")
    print(f"   音频目录: {project.output_dir}/audio")
    
    return draft_path


def demo_mashup(video_paths: list = None, music_path: str = None):
    """
    演示 AI 视频混剪功能
    """
    print("\n" + "=" * 60)
    print("🎵 AI 视频混剪演示")
    print("=" * 60)
    
    from app.services.video import MashupMaker, MashupStyle
    
    # 查找素材
    if not video_paths:
        videos = list(Path("test_assets").glob("*.mp4"))
        if len(videos) < 2:
            print("\n⚠️ 混剪需要至少 2 个视频，请将更多 .mp4 文件放入 test_assets 目录")
            return None
        video_paths = [str(v) for v in videos[:5]]  # 最多使用5个
    
    if not music_path:
        audios = list(Path("test_assets").glob("*.mp3"))
        if audios:
            music_path = str(audios[0])
    
    print(f"\n📹 使用 {len(video_paths)} 个视频素材")
    for v in video_paths:
        print(f"   - {Path(v).name}")
    
    if music_path:
        print(f"\n🎵 背景音乐: {Path(music_path).name}")
    
    # 创建制作器
    maker = MashupMaker()
    
    def on_progress(stage: str, progress: float):
        bar = "█" * int(progress * 20) + "░" * (20 - int(progress * 20))
        print(f"\r  [{stage}] {bar} {progress*100:.0f}%", end="", flush=True)
        if progress >= 1.0:
            print()
    
    maker.set_progress_callback(on_progress)
    
    # 创建项目
    print("\n🔍 分析素材...")
    project = maker.create_project(
        source_videos=video_paths,
        background_music=music_path,
        target_duration=30.0,
        style=MashupStyle.FAST_PACED,
        output_dir="./output/mashup",
    )
    
    print(f"   可用片段: {len(project.all_clips)} 个")
    print(f"   检测节拍: {len(project.beats)} 个")
    
    # 自动混剪
    print("\n🎬 智能混剪...")
    maker.auto_mashup(project)
    
    print(f"   选中片段: {len(project.selected_clips)} 个")
    print(f"   总时长: {project.total_duration:.1f}秒")
    
    # 显示剪辑点
    print("\n   剪辑时间线:")
    for i, clip in enumerate(project.selected_clips[:8]):
        source_name = Path(clip.source_video).stem[:15]
        print(f"   {i+1:2d}. [{clip.target_start:5.1f}s] {source_name}... ({clip.target_duration:.1f}s)")
    if len(project.selected_clips) > 8:
        print(f"   ... 共 {len(project.selected_clips)} 个片段")
    
    # 导出
    print("\n📦 导出剪映草稿...")
    draft_path = maker.export_to_jianying(project, "./output/jianying_drafts")
    
    print(f"\n✅ 混剪视频项目完成!")
    print(f"   草稿路径: {draft_path}")
    
    return draft_path


def demo_monologue(video_path: str = None):
    """
    演示 AI 第一人称独白功能
    """
    print("\n" + "=" * 60)
    print("🎭 AI 第一人称独白演示")
    print("=" * 60)
    
    from app.services.video import MonologueMaker, MonologueStyle
    
    # 查找视频
    if not video_path:
        videos = list(Path("test_assets").glob("*.mp4"))
        if not videos:
            print("\n⚠️ 没有找到视频素材，请将 .mp4 文件放入 test_assets 目录")
            return None
        video_path = str(videos[0])
    
    print(f"\n📹 使用视频: {video_path}")
    
    # 创建制作器
    maker = MonologueMaker(voice_provider="edge")
    
    def on_progress(stage: str, progress: float):
        bar = "█" * int(progress * 20) + "░" * (20 - int(progress * 20))
        print(f"\r  [{stage}] {bar} {progress*100:.0f}%", end="", flush=True)
        if progress >= 1.0:
            print()
    
    maker.set_progress_callback(on_progress)
    
    # 创建项目
    print("\n🔍 分析视频...")
    project = maker.create_project(
        source_video=video_path,
        context="独自走在城市的街头，回忆涌上心头",
        emotion="惆怅",
        style=MonologueStyle.MELANCHOLIC,
        output_dir="./output/monologue",
    )
    
    print(f"   视频时长: {project.video_duration:.1f}秒")
    
    # 自定义独白
    custom_script = """
有时候，我会想起过去的日子。

那些阳光灿烂的午后，那些无忧无虑的笑容。

时光荏苒，我们都在成长，也在逐渐遗忘。

但有些记忆，永远不会褪色。

它们像是心底最柔软的角落，每次触碰，都会泛起涟漪。
"""
    
    # 生成独白
    print("\n📝 生成独白文案...")
    maker.generate_script(project, custom_script=custom_script)
    print(f"   独白片段: {len(project.segments)} 个")
    
    # 生成配音
    print("\n🎤 生成情感配音...")
    maker.generate_voice(project)
    print(f"   配音时长: {project.total_duration:.1f}秒")
    
    # 生成字幕
    print("\n📜 生成电影级字幕...")
    maker.generate_captions(project, style="cinematic")
    
    # 导出
    print("\n📦 导出剪映草稿...")
    draft_path = maker.export_to_jianying(project, "./output/jianying_drafts")
    
    print(f"\n✅ 独白视频项目完成!")
    print(f"   草稿路径: {draft_path}")
    print(f"   音频目录: {project.output_dir}/audio")
    
    return draft_path


def demo_transitions():
    """
    演示转场效果
    """
    print("\n" + "=" * 60)
    print("✨ 视频转场效果演示")
    print("=" * 60)
    
    from app.services.video import TransitionEffects, TransitionType
    
    effects = TransitionEffects()
    
    print("\n可用转场效果:")
    transitions = effects.list_available_transitions()
    for i, t in enumerate(transitions, 1):
        print(f"  {i:2d}. {t}")
    
    print(f"\n共 {len(transitions)} 种转场效果")
    print("\nFFmpeg xfade 原生支持的转场:")
    xfade = effects.get_xfade_transitions()
    print(f"  共 {len(xfade)} 种")


def demo_parallel():
    """
    演示并行处理
    """
    print("\n" + "=" * 60)
    print("⚡ 并行处理器演示")
    print("=" * 60)
    
    from app.services.video import ParallelProcessor
    import time
    
    processor = ParallelProcessor(max_workers=4)
    
    def on_progress(completed, total, desc):
        bar = "█" * int(completed/total * 20) + "░" * (20 - int(completed/total * 20))
        print(f"\r  [{desc}] {bar} {completed}/{total}", end="", flush=True)
        if completed >= total:
            print()
    
    processor.set_progress_callback(on_progress)
    
    # 模拟任务
    def simulate_task(x):
        time.sleep(0.3)
        return x * 2
    
    print("\n模拟并行处理 10 个任务...")
    items = list(range(10))
    
    start = time.time()
    results = processor.map(simulate_task, items, desc="处理中")
    elapsed = time.time() - start
    
    print(f"\n处理完成:")
    print(f"  - 顺序执行预计: {0.3 * 10:.1f}秒")
    print(f"  - 并行执行实际: {elapsed:.1f}秒")
    print(f"  - 加速比: {(0.3 * 10) / elapsed:.1f}x")
    
    processor.print_stats()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="CineFlow 完整功能演示"
    )
    parser.add_argument(
        "mode",
        choices=["commentary", "mashup", "monologue", "transitions", "parallel", "all"],
        nargs="?",
        default="all",
        help="演示模式"
    )
    parser.add_argument(
        "--video",
        type=str,
        help="指定视频文件路径"
    )
    parser.add_argument(
        "--music",
        type=str,
        help="指定背景音乐路径 (用于混剪)"
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("🎬 CineFlow - AI 视频创作工具 完整演示")
    print("=" * 60)
    
    # 设置环境
    setup_test_environment()
    
    # 检查素材
    assets = check_assets()
    
    # 根据模式运行演示
    if args.mode in ["commentary", "all"]:
        if assets["video"]:
            demo_commentary(args.video)
        else:
            print("\n⚠️ 跳过解说演示 - 缺少视频素材")
    
    if args.mode in ["mashup", "all"]:
        if len(assets["video"]) >= 2:
            demo_mashup(music_path=args.music)
        else:
            print("\n⚠️ 跳过混剪演示 - 需要至少2个视频")
    
    if args.mode in ["monologue", "all"]:
        if assets["video"]:
            demo_monologue(args.video)
        else:
            print("\n⚠️ 跳过独白演示 - 缺少视频素材")
    
    if args.mode in ["transitions", "all"]:
        demo_transitions()
    
    if args.mode in ["parallel", "all"]:
        demo_parallel()
    
    print("\n" + "=" * 60)
    print("🎉 演示完成!")
    print("=" * 60)
    print("\n📌 下一步:")
    print("  1. 将视频素材放入 test_assets/ 目录")
    print("  2. 运行: python examples/full_demo.py all")
    print("  3. 在剪映中打开 output/jianying_drafts/ 下的草稿")


if __name__ == '__main__':
    main()
