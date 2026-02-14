#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
快速开始: 视觉分析功能
演示如何使用千问 VL 进行图像理解
"""

# 1. 配置 API Key (替换下面两行)
import os
os.environ["QWEN_API_KEY"] = "your-actual-api-key-here"

# 2. 导入服务
import asyncio
from pathlib import Path
from app.services.ai.vision_service import VisionService

# 3. 创建配置
config = {
    "VL": {
        "enabled": True,
        "qwen_vl": {
            "api_key": os.getenv("QWEN_API_KEY"),
            "model": "qwen-vl-plus",
        }
    }
}

# 4. 运行示例
async def quick_test():
    """快速测试"""
    print("""
╔════════════════════════════════════════╗
║   CineFlow - 视觉分析快速测试           ║
╚════════════════════════════════════════╝
    """)

    # 创建服务
    vision = VisionService(config)

    # 替换为实际图像路径
    image_path = "test_image.jpg"

    try:
        print("🔍 正在分析图像...\n")

        # 场景理解
        result = await vision.understand_scene(image_path)

        if result['success']:
            desc = result['data']['description']
            tokens = result['data']['tokens']

            print(f"✅ 分析成功!")
            print(f"\n📋 场景描述:")
            print(f"─" * 50)
            print(desc)
            print(f"─" * 50)
            print(f"\n📊 Token 使用: {tokens['input']} + {tokens['output']} = {tokens['total']}")
        else:
            print(f"❌ 失败: {result.get('error')}")

    finally:
        await vision.close()


if __name__ == "__main__":
    print("\n⚠️  请先:")
    print("   1. 替换上面的 API key")
    print("   2.准备一张测试图片")
    print("   3. 修改 image_path 指向你的图片\n")

    # 取消下面的注释来运行
    # asyncio.run(quick_test())
