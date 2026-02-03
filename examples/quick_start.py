#!/usr/bin/env python3
"""
CineAIStudio 快速使用示例

演示三大核心功能的完整使用流程:
1. AI 视频解说
2. AI 视频混剪
3. AI 第一人称独白

所有功能都支持导出为剪映草稿格式。
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def demo_commentary():
    """
    演示 AI 视频解说
    
    将原视频转换为带有 AI 解说的视频
    """
    print("\n" + "=" * 60)
    print("🎬 AI 视频解说 (Commentary)")
    print("=" * 60)
    
    from app.services.video.commentary_maker import (
        CommentaryMaker, CommentaryStyle
    )
    
    # 创建制作器
    maker = CommentaryMaker(
        voice_provider="edge",  # 使用免费的 Edge TTS
    )
    
    # 进度回调
    def on_progress(stage: str, progress: float):
        print(f"  [{stage}] {progress * 100:.0f}%")
    
    maker.set_progress_callback(on_progress)
    
    # 创建项目
    # 注意: 需要准备一个测试视频
    source_video = "test_assets/sample_video.mp4"
    
    if not Path(source_video).exists():
        print(f"\n⚠️  示例视频不存在: {source_video}")
        print("请创建 test_assets 目录并放入测试视频")
        return
    
    project = maker.create_project(
        source_video=source_video,
        topic="这是一段自然风光视频，让我们一起欣赏大自然的美丽",
        style=CommentaryStyle.STORYTELLING,
    )
    
    print(f"\n📁 项目: {project.name}")
    print(f"   视频时长: {project.video_duration:.1f}秒")
    print(f"   场景数量: {len(project.scenes)}")
    
    # 使用自定义文案（避免调用 OpenAI API）
    custom_script = """
    欢迎来到大自然的怀抱。
    
    看那连绵起伏的山峦，每一座都诉说着古老的故事。
    
    阳光穿过云层，洒落在大地上，仿佛是大自然最温柔的馈赠。
    
    让我们放慢脚步，用心感受这份美好。
    """
    
    # 生成解说
    maker.generate_script(project, custom_script=custom_script)
    print(f"\n✅ 文案已生成，共 {len(project.segments)} 个片段")
    
    # 生成配音
    maker.generate_voice(project)
    print(f"✅ 配音已生成，总时长: {project.total_duration:.1f}秒")
    
    # 生成字幕
    maker.generate_captions(project)
    print("✅ 字幕已生成")
    
    # 导出到剪映
    output_dir = "./output/jianying_drafts"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    draft_path = maker.export_to_jianying(project, output_dir)
    print(f"\n🎉 剪映草稿已导出: {draft_path}")
    
    return draft_path


def demo_mashup():
    """
    演示 AI 视频混剪
    
    将多个视频素材智能混剪成一个视频
    """
    print("\n" + "=" * 60)
    print("🎵 AI 视频混剪 (Mashup)")
    print("=" * 60)
    
    from app.services.video.mashup_maker import (
        MashupMaker, MashupStyle
    )
    
    maker = MashupMaker()
    
    def on_progress(stage: str, progress: float):
        print(f"  [{stage}] {progress * 100:.0f}%")
    
    maker.set_progress_callback(on_progress)
    
    # 检查测试素材
    test_videos = [
        "test_assets/clip1.mp4",
        "test_assets/clip2.mp4",
        "test_assets/clip3.mp4",
    ]
    test_music = "test_assets/bgm.mp3"
    
    missing = [f for f in test_videos + [test_music] if not Path(f).exists()]
    if missing:
        print(f"\n⚠️  缺少测试文件:")
        for f in missing:
            print(f"   - {f}")
        print("请创建 test_assets 目录并放入测试素材")
        return
    
    # 创建项目
    project = maker.create_project(
        source_videos=test_videos,
        background_music=test_music,
        target_duration=30.0,
        style=MashupStyle.FAST_PACED,
    )
    
    print(f"\n📁 项目: {project.name}")
    print(f"   素材数量: {len(project.source_videos)}")
    print(f"   可用片段: {len(project.all_clips)}")
    print(f"   节拍数量: {len(project.beats)}")
    
    # 自动混剪
    maker.auto_mashup(project)
    
    print(f"\n✅ 混剪完成")
    print(f"   选中片段: {len(project.selected_clips)}")
    print(f"   总时长: {project.total_duration:.1f}秒")
    
    # 显示剪辑点
    print("\n   剪辑点:")
    for i, clip in enumerate(project.selected_clips[:5]):
        print(f"   {i+1}. 来源{clip.source_index} "
              f"[{clip.start:.1f}s] -> 时间轴[{clip.target_start:.1f}s, {clip.target_duration:.1f}s]")
    if len(project.selected_clips) > 5:
        print(f"   ... 共 {len(project.selected_clips)} 个片段")
    
    # 导出
    output_dir = "./output/jianying_drafts"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    draft_path = maker.export_to_jianying(project, output_dir)
    print(f"\n🎉 剪映草稿已导出: {draft_path}")
    
    return draft_path


def demo_monologue():
    """
    演示 AI 第一人称独白
    
    为视频添加沉浸式第一人称独白
    """
    print("\n" + "=" * 60)
    print("🎭 AI 第一人称独白 (Monologue)")
    print("=" * 60)
    
    from app.services.video.monologue_maker import (
        MonologueMaker, MonologueStyle
    )
    
    maker = MonologueMaker(
        voice_provider="edge",
    )
    
    def on_progress(stage: str, progress: float):
        print(f"  [{stage}] {progress * 100:.0f}%")
    
    maker.set_progress_callback(on_progress)
    
    # 检查测试视频
    source_video = "test_assets/night_walk.mp4"
    
    if not Path(source_video).exists():
        print(f"\n⚠️  示例视频不存在: {source_video}")
        print("请创建 test_assets 目录并放入测试视频")
        return
    
    # 创建项目
    project = maker.create_project(
        source_video=source_video,
        context="深夜独自走在下过雨的街道上，霓虹灯倒映在积水中",
        emotion="惆怅",
        style=MonologueStyle.MELANCHOLIC,
    )
    
    print(f"\n📁 项目: {project.name}")
    print(f"   视频时长: {project.video_duration:.1f}秒")
    print(f"   情感风格: {project.emotion}")
    
    # 自定义独白
    custom_script = """
    有些路，只能一个人走。
    
    夜深了，霓虹灯还在闪烁，我的影子被拉得很长很长。
    
    这座城市从不缺少热闹，只是热闹从来都不属于我。
    
    但我知道，总有一盏灯，会为我而亮。
    """
    
    # 生成独白
    maker.generate_script(project, custom_script=custom_script)
    print(f"\n✅ 独白已生成，共 {len(project.segments)} 个片段")
    
    # 生成配音
    maker.generate_voice(project)
    print(f"✅ 配音已生成，总时长: {project.total_duration:.1f}秒")
    
    # 生成字幕
    maker.generate_captions(project, style="cinematic")
    print("✅ 字幕已生成 (电影级风格)")
    
    # 导出
    output_dir = "./output/jianying_drafts"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    draft_path = maker.export_to_jianying(project, output_dir)
    print(f"\n🎉 剪映草稿已导出: {draft_path}")
    
    return draft_path


def demo_jianying_export():
    """
    演示直接创建剪映草稿
    
    不依赖视频素材，直接展示剪映草稿的创建流程
    """
    print("\n" + "=" * 60)
    print("📦 剪映草稿导出 (Jianying Export)")
    print("=" * 60)
    
    from app.services.export.jianying_exporter import (
        JianyingExporter, JianyingConfig,
        Track, TrackType, Segment, TimeRange,
        VideoMaterial, AudioMaterial, TextMaterial,
    )
    
    # 创建导出器
    exporter = JianyingExporter(JianyingConfig(
        canvas_ratio="9:16",  # 竖屏短视频
        copy_materials=False,  # 演示模式不复制素材
    ))
    
    # 创建草稿
    draft = exporter.create_draft("示例项目 - CineAIStudio")
    
    print(f"\n📁 草稿: {draft.name}")
    print(f"   ID: {draft.id}")
    print(f"   画布: {draft.canvas_config.width}x{draft.canvas_config.height}")
    
    # 添加视频轨道
    video_track = Track(type=TrackType.VIDEO, attribute=1)
    draft.add_track(video_track)
    
    # 模拟视频素材
    video_material = VideoMaterial(
        path="/path/to/video.mp4",
        duration=30_000_000,  # 30秒（微秒）
        width=1920,
        height=1080,
    )
    draft.add_video(video_material)
    
    # 添加视频片段
    for i in range(3):
        segment = Segment(
            material_id=video_material.id,
            source_timerange=TimeRange.from_seconds(i * 10, 10),
            target_timerange=TimeRange.from_seconds(i * 10, 10),
        )
        video_track.add_segment(segment)
    
    print(f"\n✅ 视频轨道已添加 ({len(video_track.segments)} 个片段)")
    
    # 添加音频轨道
    audio_track = Track(type=TrackType.AUDIO)
    draft.add_track(audio_track)
    
    audio_material = AudioMaterial(
        path="/path/to/voiceover.mp3",
        duration=30_000_000,
        name="AI配音",
    )
    draft.add_audio(audio_material)
    
    audio_segment = Segment(
        material_id=audio_material.id,
        source_timerange=TimeRange.from_seconds(0, 30),
        target_timerange=TimeRange.from_seconds(0, 30),
    )
    audio_track.add_segment(audio_segment)
    
    print(f"✅ 音频轨道已添加")
    
    # 添加字幕轨道
    text_track = Track(type=TrackType.TEXT)
    draft.add_track(text_track)
    
    captions = [
        ("欢迎观看这个视频", 0, 3),
        ("这是 CineAIStudio 生成的内容", 3, 4),
        ("支持导出为剪映草稿", 7, 3),
    ]
    
    for text, start, duration in captions:
        text_material = TextMaterial(
            content=text,
            font_size=8.0,
            font_color="#FFFFFF",
        )
        draft.add_text(text_material)
        
        text_segment = Segment(
            material_id=text_material.id,
            source_timerange=TimeRange.from_seconds(0, duration),
            target_timerange=TimeRange.from_seconds(start, duration),
        )
        text_track.add_segment(text_segment)
    
    print(f"✅ 字幕轨道已添加 ({len(text_track.segments)} 条字幕)")
    
    # 导出
    output_dir = "./output/jianying_drafts"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    draft_path = exporter.export(draft, output_dir)
    
    print(f"\n🎉 剪映草稿已导出: {draft_path}")
    print("\n📂 草稿结构:")
    for item in Path(draft_path).iterdir():
        size = item.stat().st_size
        print(f"   - {item.name} ({size} bytes)")
    
    return draft_path


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("🎬 CineAIStudio - AI 视频创作工具")
    print("=" * 60)
    print("\n核心功能:")
    print("  1. AI 视频解说 - 原视频 + AI解说 + 动态字幕")
    print("  2. AI 视频混剪 - 多素材智能剪辑 + 节奏匹配")
    print("  3. AI 第一人称独白 - 原视频 + 情感独白 + 电影字幕")
    print("  4. 剪映草稿导出 - 完美适配剪映")
    
    # 创建测试素材目录
    test_dir = Path("test_assets")
    test_dir.mkdir(exist_ok=True)
    
    print("\n" + "-" * 60)
    print("运行演示...")
    
    # 演示剪映导出（不需要素材）
    demo_jianying_export()
    
    # 以下演示需要准备测试素材
    # demo_commentary()
    # demo_mashup()
    # demo_monologue()
    
    print("\n" + "=" * 60)
    print("✅ 演示完成!")
    print("=" * 60)
    print("\n提示:")
    print("  1. 完整功能需要准备视频素材到 test_assets 目录")
    print("  2. AI 文案生成需要设置 OPENAI_API_KEY 环境变量")
    print("  3. 导出的草稿可直接在剪映中打开编辑")


if __name__ == '__main__':
    main()
