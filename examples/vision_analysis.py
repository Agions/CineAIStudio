#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
视觉分析示例
演示如何使用国产视觉-语言模型进行图像理解
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.ai.vision_service import VisionService


def print_section(title: str):
    """打印分节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_result(result: dict):
    """打印结果"""
    if result.get("success"):
        print(f"✅ 成功 (模型: {result.get('model')})")
        print(f"📊 Token 使用: 输入 {result['data']['tokens']['input']} / "
              f"输出 {result['data']['tokens']['output']} / "
              f"总计 {result['data']['tokens']['total']}")
        print(f"\n📋 内容:\n{result['data']['description']}")
    else:
        print(f"❌ 失败: {result.get('error')}")


async def print_text_result(result: dict):
    """打印 OCR 结果"""
    if result.get("success"):
        print(f"✅ 成功 (模型: {result.get('model')})")
        print(f"📊 Token 使用: {result['data']['tokens']['total']}")
        print(f"\n📝 识别的文字:\n{result['data']['text']}")
    else:
        print(f"❌ 失败: {result.get('error')}")


async def print_tags_result(result: dict):
    """打印标签结果"""
    if result.get("success"):
        tags = result['data']['tags']
        print(f"✅ 成功 (模型: {result.get('model')})")
        print(f"🏷️  生成 {result['data']['count']} 个标签:\n")
        for i, tag in enumerate(tags, 1):
            print(f"  {i:2d}. {tag}")
    else:
        print(f"❌ 失败: {result.get('error')}")


async def example_1_scene_understanding():
    """示例 1: 场景理解"""
    print_section("🎬 示例 1: 场景理解")

    # 配置
    config = {
        "VL": {
            "enabled": True,
            "qwen_vl": {
                "api_key": "your-qwen-api-key",  # 替换为你的 API key
                "model": "qwen-vl-plus",
            }
        }
    }

    # 创建服务
    vision = VisionService(config)

    # 测试图像（请替换为实际图像路径）
    image_path = "test_image.jpg"

    try:
        result = await vision.understand_scene(image_path)
        print_result(result)
    finally:
        await vision.close()


async def example_2_text_extraction():
    """示例 2: 文字提取"""
    print_section("📝 示例 2: OCR 文字提取")

    config = {
        "VL": {
            "enabled": True,
            "qwen_vl": {
                "api_key": "your-qwen-api-key",
            }
        }
    }

    vision = VisionService(config)

    image_path = "subtitle_image.jpg"  # 包含字幕的图像

    try:
        result = await vision.extract_text(image_path)
        await print_text_result(result)
    finally:
        await vision.close()


async def example_3_generate_tags():
    """示例 3: 生成标签"""
    print_section("🏷️  示例 3: 生成视觉标签")

    config = {
        "VL": {
            "enabled": True,
            "qwen_vl": {
                "api_key": "your-qwen-api-key",
            }
        }
    }

    vision = VisionService(config)

    image_path = "movie_scene.jpg"  # 电影场景

    try:
        result = await vision.generate_tags(image_path)
        await print_tags_result(result)
    finally:
        await vision.close()


async def example_4_subtitle_suggestion():
    """示例 4: 字幕建议"""
    print_section("💬 示例 4: 字幕台词建议")

    config = {
        "VL": {
            "enabled": True,
            "qwen_vl": {
                "api_key": "your-qwen-api-key",
            }
        }
    }

    vision = VisionService(config)

    image_path = "dramatic_scene.jpg"
    context = "主角正在与反派对峙，气氛紧张"

    try:
        result = await vision.suggest_subtitle(image_path, context)
        if result.get("success"):
            print(f"✅ 成功 (模型: {result.get('model')})")
            print(f"\n💡 字幕建议:\n{result['data']['suggestions']}")
        else:
            print(f"❌ 失败: {result.get('error')}")
    finally:
        await vision.close()


async def example_5_shot_analysis():
    """示例 5: 镜头分析"""
    print_section("📷 示例 5: 镜头和构图分析")

    config = {
        "VL": {
            "enabled": True,
            "qwen_vl": {
                "api_key": "your-qwen-api-key",
            }
        }
    }

    vision = VisionService(config)

    image_path = "cinematic_shot.jpg"

    try:
        result = await vision.analyze_shot(image_path)
        if result.get("success"):
            print(f"✅ 成功 (模型: {result.get('model')})")
            print(f"\n🎥 镜头和构图:\n{result['data']}")
        else:
            print(f"❌ 失败: {result.get('error')}")
    finally:
        await vision.close()


async def example_6_color_analysis():
    """示例 6: 颜色分析"""
    print_section("🎨 示例 6: 色调分析")

    config = {
        "VL": {
            "enabled": True,
            "qwen_vl": {
                "api_key": "your-qwen-api-key",
            }
        }
    }

    vision = VisionService(config)

    image_path = "stylized_scene.jpg"

    try:
        result = await vision.color_analysis(image_path)
        if result.get("success"):
            print(f"✅ 成功 (模型: {result.get('model')})")
            print(f"\n🎨 色彩风格:\n{result['data']}")
        else:
            print(f"❌ 失败: {result.get('error')}")
    finally:
        await vision.close()


async def example_7_batch_analyze():
    """示例 7: 批量分析"""
    print_section("📦 示例 7: 批量分析多张图片")

    config = {
        "VL": {
            "enabled": True,
            "qwen_vl": {
                "api_key": "your-qwen-api-key",
            }
        }
    }

    vision = VisionService(config)

    # 假设有一个图片序列
    image_paths = [
        "frame_001.jpg",
        "frame_002.jpg",
        "frame_003.jpg",
    ]

    try:
        # 批量生成标签
        results = await vision.batch_analyze(image_paths, task="tags")

        print(f"📊 批量分析完成: {len(results)} 张图片\n")

        for i, (path, result) in enumerate(zip(image_paths, results), 1):
            print(f"[{i}] {path}")
            if result.get("success"):
                tags = result["data"]["tags"]
                print(f"    ✅ {', '.join(tags[:3])}... ({len(tags)} 标签)")
            else:
                print(f"    ❌ {result.get('error')}")
            print()
    finally:
        await vision.close()


async def example_8_custom_analysis():
    """示例 8: 自定义分析"""
    print_section("🔧 示例 8: 自定义提问")

    config = {
        "VL": {
            "enabled": True,
            "qwen_vl": {
                "api_key": "your-qwen-api-key",
            }
        }
    }

    vision = VisionService(config)

    image_path = "custom_scene.jpg"

    try:
        # 使用provider直接自定义提问
        result = await vision.provider.analyze_image(
            image_path,
            prompt="请回答：这张图片适合用什么类型的背景音乐？为什么？",
            model="qwen-vl-plus"
        )

        print(f"✅ 成功")
        print(f"\n🎵 音乐建议:\n{result.content}")
        print(f"\n📊 Tokens: {result.total_tokens}")

    finally:
        await vision.close()


async def main():
    """运行所有示例"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║          CineFlow AI - 视觉分析演示 (国产 LLM)              ║
║                    通义千问 VL Plus                          ║
╚══════════════════════════════════════════════════════════════╝
    """)

    print("\n⚠️  注意:")
    print("   - 请先替换 'your-qwen-api-key' 为实际的 API key")
    print("   - 请提供实际的图像文件路径")
    print("   - 这些示例展示了可以做什么，但需要真实输入才能运行\n")

    examples = [
        ("场景理解", example_1_scene_understanding),
        ("OCR 文字提取", example_2_text_extraction),
        ("生成视觉标签", example_3_generate_tags),
        ("字幕台词建议", example_4_subtitle_suggestion),
        ("镜头构图分析", example_5_shot_analysis),
        ("色调分析", example_6_color_analysis),
        ("批量分析", example_7_batch_analyze),
        ("自定义提问", example_8_custom_analysis),
    ]

    print("💡 可用示例:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"   {i}. {name}")

    print("\n要运行示例，请修改此文件中的配置和图片路径后取消注释。")
    print("当前为演示模式，不会执行实际操作。")

    # 如果想运行示例，取消下面的注释:
    # await example_1_scene_understanding()


if __name__ == "__main__":
    asyncio.run(main())
