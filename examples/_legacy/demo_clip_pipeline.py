#!/usr/bin/env python3
"""
Narrafiilm v3.2.0 — ClipRepurposingPipeline 示例

展示如何使用长视频转短片段自动化管线。

使用方式：
    python examples/demo_clip_pipeline.py /path/to/video.mp4

依赖：
    pip install faster-whisper  # 可选，不装则跳过转录

说明：
    - 只需要 FFmpeg（视频处理）
    - Faster-Whisper 用于语音转录（不装则使用无文本评分模式）
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.services.video_tools import ClipRepurposingPipeline, AspectRatio, SubtitleStyle
from app.services.video_tools.clip_scorer import ClipScorer, ClipSegment, HIGH_ENGAGEMENT_KEYWORDS


def demo_scorer():
    """演示 ClipScorer 独立使用（无需视频文件）"""
    print("\n" + "=" * 60)
    print("Demo 1: ClipScorer 多维评分引擎")
    print("=" * 60)

    scorer = ClipScorer()

    # 构造测试片段
    test_segments = [
        ClipSegment(
            start_time=0.0,
            end_time=45.0,
            transcript="今天我要揭秘一个很多人不知道的秘密！"
                     "这个技巧学会了，你一定会后悔没早点知道。",
            scene_type="dialogue",
        ),
        ClipSegment(
            start_time=120.0,
            end_time=180.0,
            transcript="然后我们看到这个参数设置，默认是关闭的。"
                     "打开之后效果会好很多。",
            scene_type="tutorial",
        ),
        ClipSegment(
            start_time=300.0,
            end_time=340.0,
            transcript="哈哈哈哈，笑死我了这个场景。"
                     "大家记得一键三连支持一下！",
            scene_type="entertainment",
        ),
        ClipSegment(
            start_time=450.0,
            end_time=470.0,
            transcript="好。",
            scene_type="unknown",
        ),
        ClipSegment(
            start_time=500.0,
            end_time=560.0,
            transcript="第一次做这种事情其实挺紧张的，但是完成之后感觉非常有成就感。"
                     "给大家分享一下我的经验。",
            scene_type="monologue",
        ),
    ]

    print(f"\n评分 {len(test_segments)} 个候选片段...")
    scores = scorer.score_segments(test_segments)

    print(f"\n{'排名':<4} {'时长':<8} {'总分':<6} {'理由'}")
    print("-" * 60)
    for i, score in enumerate(scores, 1):
        duration = score.segment.end_time - score.segment.start_time
        reasons = " / ".join(score.reasons[:3])
        print(f"#{i:<3} {duration:>5.0f}s  {score.total_score:>5.1f}  {reasons}")

    print(f"\n内置高吸引力关键词库：{len(HIGH_ENGAGEMENT_KEYWORDS)} 个")
    print("部分关键词：", HIGH_ENGAGEMENT_KEYWORDS[:10])


def demo_pipeline(video_path: str):
    """演示完整管线（需要真实视频文件）"""
    print("\n" + "=" * 60)
    print(f"Demo 2: ClipRepurposingPipeline 完整管线")
    print("=" * 60)
    print(f"输入视频：{video_path}")

    if not os.path.exists(video_path):
        print(f"⚠️  视频文件不存在，跳过管线演示")
        print("   管线需要真实视频文件才能运行。")
        print("   将你的视频路径作为第一个参数传入即可运行。")
        return

    output_dir = str(project_root / "output" / "demo_clips")
    os.makedirs(output_dir, exist_ok=True)

    pipeline = ClipRepurposingPipeline(output_dir=output_dir)

    def progress_callback(step: str, progress: float):
        bar = "█" * int(progress * 30) + "░" * (30 - int(progress * 30))
        print(f"\r  [{bar}] {step} ({progress:.0%})", end="", flush=True)

    print(f"\n开始处理（输出目录: {output_dir}）...")
    try:
        results = pipeline.run(
            video_path=video_path,
            output_dir=output_dir,
            platform="douyin",        # 抖音预设
            languages=["zh", "en"],
            max_clips=3,
        )
        print()  # newline after progress bar

        if results:
            print(f"\n✅ 生成 {len(results)} 条短片段：")
            for clip in results:
                print(f"  → {clip.output_path}")
                print(f"     评分: {clip.score.total_score:.1f} | "
                      f"时长: {clip.duration:.0f}s | "
                      f"比例: {clip.aspect_ratio.value}")
        else:
            print("\n⚠️  未生成任何片段（可能是视频太短或转录失败）")

    except Exception as e:
        print(f"\n❌ 管线执行失败: {e}")
        print("   常见问题：")
        print("   - FFmpeg 未安装：brew install ffmpeg 或 apt install ffmpeg")
        print("   - 视频格式不支持：转换为 MP4 格式")
        print("   - Faster-Whisper 未安装：pip install faster-whisper（可选）")


def demo_platform_presets():
    """展示支持的平台预设"""
    print("\n" + "=" * 60)
    print("Demo 3: 平台预设")
    print("=" * 60)

    from app.services.video_tools import PLATFORM_PRESETS

    print(f"\n{'平台':<20} {'宽高比':<10} {'最大时长':<10} {'码率'}")
    print("-" * 55)
    for key, preset in PLATFORM_PRESETS.items():
        print(f"{preset.name:<20} {preset.aspect_ratio.value:<10} "
              f"{preset.max_duration:.0f}s{'':<5} {preset.bitrate}")


if __name__ == "__main__":
    print("Narrafiilm v3.2.0 — ClipRepurposingPipeline 示例")
    print()

    # Demo 1: 独立评分引擎（无需视频文件）
    demo_scorer()

    # Demo 3: 平台预设（无需视频文件）
    demo_platform_presets()

    # Demo 2: 完整管线（需要视频文件）
    video_path = sys.argv[1] if len(sys.argv) > 1 else ""
    demo_pipeline(video_path)

    print("\n" + "=" * 60)
    print("示例完成！")
    print()
    print("进一步探索：")
    print("  1. 调整评分权重：ClipScorer(weights={...})")
    print("  2. 自定义裁剪策略：修改 crop_strategy='face'|'center'|'sound'")
    print("  3. 字幕样式：SubtitleStyle.CINEMATIC / .SOCIAL / .DEFAULT")
    print("  4. 注册新平台：在 clip_repurposing.py 的 PLATFORM_PRESETS 中添加")
