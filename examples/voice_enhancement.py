#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
语音增强示例
演示阿里云 TTS 的 10+ 种语音风格和精细参数控制
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.ai.voice_generator import (
    VoiceGenerator,
    VoiceConfig,
    VoiceStyle,
    VoiceGender,
)
from app.services.ai.providers.aliyun_tts import AliyunTTSProvider


def print_section(title: str):
    """打印分节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def example_1_voices_list():
    """示例 1: 列出所有可用声音"""
    print_section("🎙️  示例 1: 可用声音列表")

    # 使用 Edge TTS（免费）
    print("使用 Edge TTS 列表:")
    edge_gen = VoiceGenerator(provider="edge")
    voices = edge_gen.list_voices()

    print(f"\n共 {len(voices)} 个声音:\n")

    # 按性别分组
    female = [v for v in voices if v.gender == VoiceGender.FEMALE]
    male = [v for v in voices if v.gender == VoiceGender.MALE]

    print("👩 女声:")
    for v in female:
        print(f"  • {v.id}: {v.name}")

    print("\n👨 男声:")
    for v in male:
        print(f"  • {v.id}: {v.name}")


def example_2_styles_demo():
    """示例 2: 不同风格演示"""
    print_section("🎭 示例 2: 语音风格演示")

    # 定义演示文本
    test_text = "欢迎来到 CineFlow，我们要开始一段精彩的视频创作之旅！"

    print(f"测试文本: {test_text}\n")

    # 尝试不同的风格
    styles_to_test = [
        (VoiceStyle.NARRATION, "旁白/解说"),
        (VoiceStyle.NEWSCAST, "新闻播报"),
        (VoiceStyle.CHEERFUL, "欢快活泼"),
        (VoiceStyle.CONVERSATIONAL, "自然对话"),
    ]

    for style, style_name in styles_to_test:
        print(f"\n🎭 风格: {style_name}")
        print(f"   ID: {style.value}")

        try:
            generator = VoiceGenerator(provider="edge")
            config = VoiceConfig(
                style=style,
                rate=1.0,
            )

            output_path = f"style_{style.value}.mp3"
            result = generator.generate(test_text, output_path, config)

            print(f"   ✅ 生成成功: {result.audio_path}")
            print(f"   ⏱️  时长: {result.duration:.2f}秒")

        except Exception as e:
            print(f"   ❌ 失败: {e}")


def example_3_speed_control():
    """示例 3: 语速控制"""
    print_section("⏱️  示例 3: 语速控制")

    test_text = "人工智能正在改变我们创作视频的方式，让每个人都能轻松制作专业内容。"

    # 不同的语速
    speeds = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]

    print(f"测试文本: {test_text}\n")

    for speed in speeds:
        print(f"\n🚀 语速: {speed}x")

        try:
            generator = VoiceGenerator(provider="edge")
            config = VoiceConfig(rate=speed)

            output_path = f"speed_{speed}.mp3"
            result = generator.generate(test_text, output_path, config)

            print(f"   ⏱️  时长: {result.duration:.2f}秒")

        except Exception as e:
            print(f"   ❌ 失败: {e}")


def example_4_pitch_control():
    """示例 4: 音调控制"""
    print_section("🎵 示例 4: 音调控制")

    test_text = "你好，这是一段音调测试。"

    # 不同的音调
    pitches = [0.5, 0.75, 1.0, 1.25, 1.5]

    print(f"测试文本: {test_text}\n")

    for pitch in pitches:
        print(f"\n🎵 音调: {pitch}x ({'低沉' if pitch < 1 else '高亢' if pitch > 1 else '正常'})")

        try:
            generator = VoiceGenerator(provider="edge")
            config = VoiceConfig(pitch=pitch)

            output_path = f"pitch_{pitch}.mp3"
            result = generator.generate(test_text, output_path, config)

            print(f"   ✅ 生成成功: {result.audio_path}")

        except Exception as e:
            print(f"   ❌ 失败: {e}")


def example_5_volume_control():
    """示例 5: 音量控制"""
    print_section("🔊 示例 5: 音量控制")

    test_text = "这是一段音量测试。"

    # 不同的音量
    volumes = [0.25, 0.5, 0.75, 1.0]

    print(f"测试文本: {test_text}\n")

    for volume in volumes:
        print(f"\n🔊 音量: {volume * 100}%")

        try:
            generator = VoiceGenerator(provider="edge")
            config = VoiceConfig(volume=volume)

            output_path = f"volume_{volume}.mp3"
            result = generator.generate(test_text, output_path, config)

            print(f"   ✅ 生成成功: {result.audio_path}")

        except Exception as e:
            print(f"   ❌ 失败: {e}")


def example_6_combined_control():
    """示例 6: 综合参数控制"""
    print_section("🎛️  示例 6: 综合参数控制")

    test_text = "这是一段使用了多种参数调整的语音测试文本。"

    # 不同场景的配置
    scenarios = [
        ("快速新闻播报", VoiceConfig(
            style=VoiceStyle.NEWSCAST,
            rate=1.3,
            pitch=1.1,
            volume=0.9,
        )),
        ("情感丰富的旁白", VoiceConfig(
            style=VoiceStyle.NARRATION,
            rate=0.9,
            pitch=1.0,
            volume=1.0,
        )),
        ("欢快的对话", VoiceConfig(
            style=VoiceStyle.CHEERFUL,
            rate=1.2,
            pitch=1.2,
            volume=1.0,
        )),
        ("低沉的解说", VoiceConfig(
            style=VoiceStyle.NARRATION,
            rate=0.85,
            pitch=0.8,
            volume=1.0,
        )),
    ]

    for scenario_name, config in scenarios:
        print(f"\n🎬 场景: {scenario_name}")
        print(f"   风格: {config.style.value}")
        print(f"   语速: {config.rate}x, 音调: {config.pitch}x, 音量: {config.volume * 100}%")

        try:
            generator = VoiceGenerator(provider="edge")
            output_path = f"scenario_{scenario_name}.mp3"
            result = generator.generate(test_text, output_path, config)

            print(f"   ✅ 生成成功: {result.audio_path}")
            print(f"   ⏱️  时长: {result.duration:.2f}秒")

        except Exception as e:
            print(f"   ❌ 失败: {e}")


def example_7_voice_comparison():
    """示例 7: 声音对比"""
    print_section("🔍 示例 7: 不同声音对比")

    test_text = "这句话用来对比不同声音的效果。"

    # 使用不同的声音
    voices_to_test = [
        ("晓晓", "zh-CN-XiaoxiaoNeural"),
        ("晓依", "zh-CN-XiaoyiNeural"),
        ("晓涵", "zh-CN-XiaohanNeural"),
        ("晓墨", "zh-CN-XiaomoNeural"),
        ("云希", "zh-CN-YunxiNeural"),
        ("云健", "zh-CN-YunjianNeural"),
    ]

    print(f"测试文本: {test_text}\n")

    for voice_name, voice_id in voices_to_test:
        print(f"\n🎙️  声音: {voice_name} ({voice_id})")

        try:
            generator = VoiceGenerator(provider="edge")
            config = VoiceConfig(voice_id=voice_id)

            output_path = f"voice_{voice_name}.mp3"
            result = generator.generate(test_text, output_path, config)

            print(f"   ✅ 生成成功: {result.audio_path}")

        except Exception as e:
            print(f"   ❌ 失败: {e}")


def example_8_batch_generation():
    """示例 8: 批量生成"""
    print_section("📦 示例 8: 批量生成字幕配音")

    # 模拟字幕片段
    segments = [
        {"text": "大家好，欢迎观看", "start": 0.0, "duration": 2.5},
        {"text": "今天我们要演示", "start": 2.5, "duration": 2.0},
        {"text": "AI 配音的批量生成功能", "start": 4.5, "duration": 3.5},
        {"text": "非常方便快捷", "start": 8.0, "duration": 2.0},
    ]

    print("字幕片段:")
    for i, seg in enumerate(segments, 1):
        print(f"  {i}. {seg['text']}")

    print("\n正在生成...\n")

    try:
        generator = VoiceGenerator(provider="edge")
        config = VoiceConfig(
            rate=1.1,
            voice_id="zh-CN-XiaoxiaoNeural",
        )

        results = generator.generate_segments(segments, "output_segments", config)

        print(f"✅ 成功生成 {len(results)} 个片段:\n")

        for i, result in enumerate(results, 1):
            print(f"  {i}. {result.audio_path}")
            print(f"     时长: {result.duration:.2f}秒")
            print(f"     文本: {result.text[:20]}...")

    except Exception as e:
        print(f"❌ 失败: {e}")


def example_9_aliyun_advanced():
    """示例 9: 阿里云高级功能（需要 API Key）"""
    print_section("☁️  示例 9: 阿里云高级功能")

    print("⚠️  此示例需要阿里云 API Key\n")

    # 展示阿里云 TTS 的功能
    print("阿里云 TTS 提供商功能:\n")

    provider_info = [
        "✅ 20+ 种声音风格",
        "✅ 情感语音合成",
        "✅ SSML 标记支持",
        "✅ 多语言支持（中文、英文、方言）",
        "✅ 方言支持（东北话、四川话、粤语）",
        "✅ 精细参数控制（语速、音调、音量）",
    ]

    for info in provider_info:
        print(f"  {info}")

    print("\n可用的方言:")
    provider = AliyunTTSProvider("test", "test", "test")
    dialects = provider.get_available_dialects()

    for d in dialects:
        print(f"  • {d['name']} ({d['voice']})")

    print("\n可用的情感:")
    emotions = provider.get_available_emotions()

    for e in emotions:
        print(f"  • {e['name']} ({e['emotion']})")


def main():
    """运行所有示例"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║        CineFlow AI - 语音增强演示 (TTS v2.2.0)               ║
║                    10+ 种语音风格 + 细粒度控制                ║
╚══════════════════════════════════════════════════════════════╝
    """)

    examples = [
        ("列出可用声音", example_1_voices_list),
        ("语音风格演示", example_2_styles_demo),
        ("语速控制", example_3_speed_control),
        ("音调控制", example_4_pitch_control),
        ("音量控制", example_5_volume_control),
        ("综合参数控制", example_6_combined_control),
        ("声音对比", example_7_voice_comparison),
        ("批量生成", example_8_batch_generation),
        ("阿里云高级功能", example_9_aliyun_advanced),
    ]

    print("💡 可用示例:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"   {i}. {name}")

    print("\n运行示例 (取消下面的注释):")
    print("# example_1_voices_list()")
    print("# example_2_styles_demo()")
    print("# example_5_volume_control()")


if __name__ == "__main__":
    main()
