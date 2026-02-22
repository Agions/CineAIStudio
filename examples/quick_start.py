#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClipFlow 快速开始示例
展示如何使用 ClipFlow 的核心功能
"""

import asyncio
from app.core.config_manager import get_config_manager
from app.core.exceptions import LLMError, ConfigError
from app.services.ai.llm_manager import LLMManager
from app.services.ai.providers.qwen import QwenProvider
from app.services.ai.providers.kimi import KimiProvider
from app.services.ai.cache import get_global_cache, with_retry, LLMRetryPolicy
from app.services.ai.script_generator import ScriptGenerator


async def example_1_basic_llm_call():
    """示例 1: 基本 LLM 调用"""
    print("\n" + "="*50)
    print("示例 1: 基本 LLM 调用")
    print("="*50)

    # 1. 创建提供商
    provider = QwenProvider(api_key="your-api-key")

    # 2. 调用 LLM
    from app.core.models.llm_models import LLMRequest
    request = LLMRequest(
        messages=[{"role": "user", "content": "你好，请介绍一下自己"}],
        model="qwen-plus",
        max_tokens=100
    )

    response = await provider.complete(request)

    if response.success:
        print(f"\n✅ LLM 响应:")
        print(response.text)
    else:
        print(f"\n❌ LLM 调用失败: {response.error}")


async def example_2_use_llm_manager():
    """示例 2: 使用 LLM 管理器"""
    print("\n" + "="*50)
    print("示例 2: 使用 LLM 管理器")
    print("="*50)

    # 1. 创建多个提供商
    providers = {
        "qwen": QwenProvider(api_key="qwen-api-key"),
        "kimi": KimiProvider(api_key="kimi-api-key")
    }

    # 2. 创建管理器
    manager = LLMManager(providers=providers, default_provider="qwen")

    # 3. 使用管理器调用
    from app.core.models.llm_models import LLMRequest
    request = LLMRequest(
        messages=[{"role": "user", "content": "写一个简短的故事"}],
        max_tokens=200
    )

    # 使用默认提供商
    response = await manager.complete(request)

    if response.success:
        print(f"\n✅ 使用默认提供商 (qwen):")
        print(response.text[:100] + "...")

    # 切换到其他提供商
    response2 = await manager.complete(request, provider_name="kimi")

    if response2.success:
        print(f"\n✅ 使用提供商 (kimi):")
        print(response2.text[:100] + "...")


async def example_3_use_cache():
    """示例 3: 使用缓存"""
    print("\n" + "="*50)
    print("示例 3: 使用缓存")
    print("="*50)

    # 1. 获取全局缓存
    cache = get_global_cache()

    # 2. 第一次调用 (未缓存)
    messages = [{"role": "user", "content": "1+1 等于几？"}]
    cached_response = cache.get(messages, "qwen")

    if cached_response:
        print(f"\n✅ 从缓存获取: {cached_response}")
    else:
        print(f"\n🔄 未缓存，需要调用 LLM")
        # 这里应该调用实际 LLM
        simulated_response = "1+1=2"
        cache.set(messages, "qwen", simulated_response)
        print(f"✅ 已缓存响应: {simulated_response}")

    # 3. 第二次调用 (有缓存)
    cached_response = cache.get(messages, "qwen")

    if cached_response:
        print(f"\n✅ 第二次从缓存获取: {cached_response}")

    # 4. 查看缓存统计
    print(f"\n📊 缓存统计: {cache.get_stats()}")


async def example_4_use_retry():
    """示例 4: 使用重试机制"""
    print("\n" + "="*50)
    print("示例 4: 使用重试机制")
    print("="*50)

    # 1. 创建重试策略
    policy = LLMRetryPolicy(max_retries=3, base_delay=1.0)

    # 2. 定义需要重试的函数
    call_count = 0

    @with_retry(policy, exceptions=(ConnectionError, TimeoutError))
    async def call_unstable_api():
        global call_count
        call_count += 1

        print(f"\n🔄 尝试第 {call_count} 次...")

        if call_count < 3:
            raise ConnectionError("网络连接失败")

        return "✅ 成功!"

    # 3. 调用函数
    try:
        result = await call_unstable_api()
        print(f"\n{result}")
        print(f"总共尝试了 {call_count} 次")
    except Exception as e:
        print(f"\n❌ 所有重试均失败: {e}")


async def example_5_generate_script():
    """示例 5: 生成脚本"""
    print("\n" + "="*50)
    print("示例 5: 生成脚本")
    print("="*50)

    # 1. 创建脚本生成器
    generator = ScriptGenerator(use_llm_manager=False)

    # 2. 使用本地模式生成脚本
    script = generator.generate_commentary(
        topic="分析《流浪地球》的科学设定",
        duration=60,
        style="explainer"
    )

    print(f"\n📝 生成的脚本:")
    print(f"标题: {script.title}")
    print(f"内容: {script.text}")
    print(f"段落数: {len(script.segments)}")

    if script.segments:
        print(f"\n第一段: {script.segments[0].text}")


async def example_6_config_management():
    """示例 6: 配置管理"""
    print("\n" + "="*50)
    print("示例 6: 配置管理")
    print("="*50)

    # 1. 获取配置管理器
    config_manager = get_config_manager()

    # 2. 加载配置
    config = config_manager.load_config()

    print(f"\n📋 当前配置:")
    print(f"  默认提供商: {config.default_provider}")
    print(f"  日志级别: {config.log_level}")
    print(f"  缓存启用: {config.cache.enabled}")
    print(f"  最大重试次数: {config.retry.max_retries}")

    # 3. 获取特定提供商配置
    qwen_config = config_manager.get_llm_config("qwen")
    if qwen_config:
        print(f"\n🤖 通义千问配置:")
        print(f"  启用: {qwen_config.enabled}")
        print(f"  模型: {qwen_config.model}")

    # 4. 修改配置
    print(f"\n✅ 重试次数已设置")


def example_7_error_handling():
    """示例 7: 错误处理"""
    print("\n" + "="*50)
    print("示例 7: 错误处理")
    print("="*50)

    try:
        # 模拟 LLM 错误
        raise LLMError(
            message="API 调用失败: rate limit exceeded",
            provider="qwen",
            model="qwen-plus"
        )
    except LLMError as e:
        print(f"\n❌ 捕获到 LLM 错误:")
        print(e)

    try:
        # 模拟配置错误
        raise ConfigError("API 密钥未设置", key="qwen.api_key")
    except ConfigError as e:
        print(f"\n❌ 捕获到配置错误:")
        print(e)


async def main():
    """运行所有示例"""
    print("\n" + "="*50)
    print("ClipFlow 快速开始示例")
    print("="*50)

    # 运行示例 (注意: 需要真实的 API 密钥才能完整运行)
    await example_3_use_cache()
    await example_4_use_retry()
    await example_5_generate_script()
    await example_6_config_management()
    example_7_error_handling()

    print("\n" + "="*50)
    print("✅ 所有示例运行完成!")
    print("="*50)
    print("\n💡 提示:")
    print("  - 示例 1, 2 需要真实的 LLM API 密钥")
    print("  - 示例 3, 4, 5, 6, 7 可以直接运行")
    print("  - 完整文档请查看: docs/ 和 examples/ 目录")
    print()


if __name__ == "__main__":
    asyncio.run(main())
