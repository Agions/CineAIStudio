#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
本地模型示例
演示如何使用 Ollama 运行国产及开源 LLM

前置条件:
1. 安装 Ollama: https://ollama.com
2. 下载模型: ollama pull qwen2.5
3. 启动服务: ollama serve
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.ai.providers.ollama import OllamaProvider
from app.services.ai.base_LLM_provider import LLMRequest


def print_section(title: str):
    """打印分节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


async def example_1_basic_generation():
    """示例 1: 基础文本生成"""
    print_section("📝 示例 1: 本地模型文本生成")

    provider = OllamaProvider()

    try:
        request = LLMRequest(
            prompt="用一句话介绍你自己",
            model="qwen2.5",
            max_tokens=100
        )

        response = await provider.generate(request)

        print(f"✅ 成功!")
        print(f"\n📋 回复:\n{response.content}")
        print(f"\n🤖 模型: {response.model}")
        print(f"📊 Tokens: {response.total_tokens}")

    except Exception as e:
        print(f"❌ 失败: {e}")
    finally:
        await provider.close()


async def example_2_list_models():
    """示例 2: 列出已安装模型"""
    print_section("🎮 示例 2: 已安装的模型")

    provider = OllamaProvider()

    try:
        models = await provider.list_models()

        if models:
            print(f"✅ 找到 {len(models)} 个模型:\n")
            for i, model in enumerate(models, 1):
                print(f"  {i}. {model['name']}")
                print(f"     大小: {model['size'] / (1024**3):.2f} GB")
        else:
            print("⚠️  没有找到已安装的模型")
            print("\n💡 下载模型: ollama pull qwen2.5\n")

    except Exception as e:
        print(f"❌ 失败: {e}")
    finally:
        await provider.close()


async def example_3_chinese_generation():
    """示例 3: 中文生成"""
    print_section("🇨🇳 示例 3: 中文内容生成")

    provider = OllamaProvider()

    try:
        request = LLMRequest(
            prompt="写一个简短的 Python 函数，用于反转字符串",
            model="qwen2.5",
            max_tokens=500,
            temperature=0.3
        )

        response = await provider.generate(request)

        print(f"✅ 成功!")
        print(f"\n📋 响应:\n{response.content}")

    except Exception as e:
        print(f"❌ 失败: {e}")
    finally:
        await provider.close()


async def example_4_system_prompt():
    """示例 4: 使用系统提示"""
    print_section("⚙️  示例 4: 系统提示")

    provider = OllamaProvider()

    try:
        request = LLMRequest(
            prompt="解释量子纠缠是什么",
            model="qwen2.5",
            system_prompt="你是一位物理教授，请用通俗易懂的语言解释科学概念",
            max_tokens=300
        )

        response = await provider.generate(request)

        print(f"✅ 成功!")
        print(f"\n🤓 教授解释:\n{response.content}")

    except Exception as e:
        print(f"❌ 失败: {e}")
    finally:
        await provider.close()


async def example_5_creative_writing():
    """示例 5: 创意写作"""
    print_section("✨ 示例 5: 创意写作")

    provider = OllamaProvider()

    try:
        request = LLMRequest(
            prompt="写一个关于时空穿越的科幻故事开头，500字左右",
            model="qwen2.5",
            temperature=0.8
        )

        response = await provider.generate(request)

        print(f"✅ 成功!")
        print(f"\n📖 故事:\n{response.content}")

    except Exception as e:
        print(f"❌ 失败: {e}")
    finally:
        await provider.close()


async def example_6_code_generation():
    """示例 6: 代码生成"""
    print_section("💻 示例 6: 代码生成")

    provider = OllamaProvider()

    try:
        # 使用代码专用模型
        request = LLMRequest(
            prompt="写一个 Python 装饰器，用于测量函数执行时间",
            model="qwen2.5-coder",
            max_tokens=400,
            temperature=0.2
        )

        response = await provider.generate(request)

        print(f"✅ 成功!")
        print(f"\n💻 代码:\n{response.content}")

    except Exception as e:
        print(f"❌ 失败: {e}")
    finally:
        await provider.close()


async def example_7_multiple_turns():
    """示例 7: 多轮对话模拟"""
    print_section("💬 示例 7: 多轮对话")

    provider = OllamaProvider()

    try:
        conversation = [
            "我想学 Python，从哪里开始？",
            "好的，我已经学会了基础语法，接下来学什么？"
        ]

        for i, user_input in enumerate(conversation, 1):
            print(f"\n👤 用户: {user_input}\n")

            request = LLMRequest(
                prompt=user_input,
                model="qwen2.5",
                max_tokens=200
            )

            response = await provider.generate(request)

            print(f"🤖 助手: {response.content}")
            print("-" * 60)

    except Exception as e:
        print(f"❌ 失败: {e}")
    finally:
        await provider.close()


async def example_8_model_comparison():
    """示例 8: 模型对比"""
    print_section("🔬 示例 8: 模型对比")

    provider = OllamaProvider()

    models_to_test = ["qwen2.5", "mistral"]
    test_prompt = "解释什么是熵（thermodynamics）"

    try:
        for model in models_to_test:
            print(f"\n🧪 测试模型: {model}")

            try:
                request = LLMRequest(
                    prompt=test_prompt,
                    model=model,
                    max_tokens=200
                )

                response = await provider.generate(request)

                print(f"✅ {response.total_tokens} tokens")
                print(f"\n{response.content[:150]}...")

            except Exception as e:
                print(f"❌ 模型 {model} 不可用")

    except Exception as e:
        print(f"❌ 失败: {e}")
    finally:
        await provider.close()


async def check_ollama_status():
    """检查 Ollama 状态"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║          CineFlow AI - 本地模型演示 (Ollama)                ║
╚══════════════════════════════════════════════════════════════╝
    """)

    print("🔍 检查 Ollama 状态...")

    provider = OllamaProvider()

    if provider.health_check():
        print("✅ Ollama 服务运行中")

        try:
            models = await provider.list_models()
            print(f"📦 已安装模型: {len(models)} 个")

            if models:
                print("\n可用模型:")
                for model in models[:5]:
                    print(f"  • {model['name']}")
        except:
            print("⚠️  无法列出模型")

        await provider.close()
        return True
    else:
        print("❌ Ollama 服务未运行")
        print("\n💡 安装步骤:")
        print("   1. 下载: https://ollama.com")
        print("   2. 安装后运行: ollama serve")
        print("   3. 下载模型: ollama pull qwen2.5")
        print("   4. 运行示例: python examples/local_models.py\n")
        return False


async def main():
    """运行示例"""
    if not await check_ollama_status():
        return

    examples = [
        ("基础文本生成", example_1_basic_generation),
        ("列出已安装模型", example_2_list_models),
        ("中文内容生成", example_3_chinese_generation),
        ("使用系统提示", example_4_system_prompt),
        ("创意写作", example_5_creative_writing),
        ("代码生成", example_6_code_generation),
        ("多轮对话", example_7_multiple_turns),
        ("模型对比", example_8_model_comparison),
    ]

    print("\n💡 可用示例:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"   {i}. {name}")

    print("\n运行示例 (取消下面的注释):")
    print("# await example_1_basic_generation()")
    print("# await example_3_chinese_generation()")


if __name__ == "__main__":
    asyncio.run(main())
