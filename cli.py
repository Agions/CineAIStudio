#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineFlow AI CLI - 命令行界面
用于无 GUI 环境的轻量级客户端
"""

import sys
import json
import asyncio
from pathlib import Path
from typing import Optional, List
from dataclasses import asdict

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.ai.llm_manager import LLMManager
from app.services.ai.providers.qwen import QwenProvider
from app.services.ai.providers.kimi import KimiProvider
from app.services.ai.providers.glm5 import GLM5Provider
from app.services.ai.cache import get_global_cache, get_global_monitor
from app.core.config_manager import get_config_manager, AppConfig
from app.core.models.llm_models import LLMRequest, LLMResponse
from app.core.exceptions import LLMError, ConfigError


class CineFlowCLI:
    """CineFlow AI 命令行客户端"""

    def __init__(self):
        self.config_manager = get_config_manager()
        self.config: Optional[AppConfig] = None
        self.llm_manager: Optional[LLMManager] = None
        self.cache = get_global_cache()
        self.monitor = get_global_monitor()

    def load_config(self) -> None:
        """加载配置"""
        print("📋 加载配置...")
        self.config = self.config_manager.load_config()
        print(f"✅ 配置已加载")
        print(f"   - 默认提供商: {self.config.default_provider}")
        print(f"   - 缓存: {self.cache.enabled if hasattr(self.cache, 'enabled') else '启用'}")
        print()

    def init_llm_manager(self) -> None:
        """初始化 LLM 管理器"""
        print("🤖 初始化 LLM 管理器...")

        providers = {}

        # 检查可用提供商
        for name, llm_config in self.config.llm_providers.items():
            if llm_config.is_valid():
                print(f"  ✓ {name}: {llm_config.model}")

                if name == "qwen":
                    providers[name] = QwenProvider(
                        api_key=llm_config.api_key,
                        model=llm_config.model
                    )
                elif name == "kimi":
                    providers[name] = KimiProvider(
                        api_key=llm_config.api_key,
                        model=llm_config.model
                    )
                elif name == "glm5":
                    providers[name] = GLM5Provider(
                        api_key=llm_config.api_key,
                        model=llm_config.model
                    )

        if not providers:
            print("\n❌ 错误: 没有可用的 LLM 提供商")
            print("   请在 config/app_config.yaml 中配置 API 密钥")
            sys.exit(1)

        self.llm_manager = LLMManager(
            providers=providers,
            default_provider=self.config.default_provider
        )

        print(f"✅ LLM 管理器已初始化")
        print(f"   - 可用提供商: {', '.join(providers.keys())}")
        print(f"   - 默认提供商: {self.config.default_provider}")
        print()

    async def complete_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        文本补全

        Args:
            prompt: 提示词
            model: 模型名称
            provider: 提供商
            temperature: 温度
            max_tokens: 最大 token 数

        Returns:
            生成的文本
        """
        try:
            request = LLMRequest(
                messages=[{"role": "user", "content": prompt}],
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )

            print(f"🔄 发送请求到 {provider or self.config.default_provider}...")

            response = await self.llm_manager.complete(request, provider_name=provider)

            if response.success:
                print(f"✅ 响应成功 ({response.tokens} tokens)")
                return response.text
            else:
                print(f"❌ 请求失败: {response.error}")
                raise LLMError(response.error or "Unknown error")

        except Exception as e:
            print(f"❌ 错误: {e}")
            raise

    def show_stats(self) -> None:
        """显示性能统计"""
        stats = self.monitor.get_stats()

        print("📊 性能统计")
        print("=" * 50)
        print(f"总请求数: {stats['total_requests']}")
        print(f"成功请求: {stats['successful_requests']}")
        print(f"失败请求: {stats['failed_requests']}")

        if "success_rate" in stats:
            print(f"成功率: {stats['success_rate']:.1%}")

        print(f"\n缓存命中: {stats['cache_hits']}")
        print(f"缓存未命中: {stats['cache_misses']}")

        if "cache_hit_rate" in stats:
            print(f"缓存命中率: {stats['cache_hit_rate']:.1%}")

        print(f"\n总 Token 数: {stats['total_tokens']}")
        print(f"估计成本: ¥{stats['estimated_cost']:.2f}")

        if stats['avg_response_time'] > 0:
            print(f"平均响应时间: {stats['avg_response_time']:.2f} 秒")

        print("=" * 50)

    def show_cache_stats(self) -> None:
        """显示缓存统计"""
        stats = self.cache.get_stats()

        print("📦 缓存统计")
        print("=" * 50)
        print(f"缓存大小: {stats['size']}/{stats['max_size']}")
        print(f"TTL: {stats['ttl']} 秒")
        print("=" * 50)


async def main():
    """主程序"""
    print("\n" + "=" * 50)
    print("CineFlow AI CLI v2.0.0")
    print("=" * 50)

    # 创建 CLI 实例
    cli = CineFlowCLI()

    # 加载配置
    cli.load_config()

    # 初始化 LLM 管理器
    cli.init_llm_manager()

    # 交互式命令行
    print("💡 输入 /help 查看帮助，/quit 退出\n")

    while True:
        try:
            # 读取用户输入
            command = input("CineFlow> ").strip()

            if not command:
                continue

            # 解析命令
            if command == "/quit" or command == "/exit":
                print("\n👋 再见!")
                cli.show_stats()
                break

            elif command == "/help":
                print("\n📖 命令帮助")
                print("-" * 50)
                print("  /quit      - 退出程序")
                print("  /stats     - 显示性能统计")
                print("  /cache     - 显示缓存统计")
                print("  /clear     - 清空缓存")
                print("  @provider  - 切换提供商 (例: @qwen)")
                print("  其他输入   - 发送到 LLM")
                print("-" * 50)

            elif command == "/stats":
                cli.show_stats()

            elif command == "/cache":
                cli.show_cache_stats()

            elif command == "/clear":
                cli.cache.clear()
                print("✅ 缓存已清空")

            elif command.startswith("@"):
                # 切换提供商
                provider = command[1:].strip()
                try:
                    cli.config_manager.set_default_provider(provider)
                    cli.config = cli.config_manager.load_config()
                    print(f"✅ 已切换到 {provider}")
                except ConfigError as e:
                    print(f"❌ {e}")

            else:
                # 发送到 LLM
                try:
                    response = await cli.complete_text(command)
                    print("\n" + response + "\n")
                except Exception:
                    pass

        except KeyboardInterrupt:
            print("\n\n👋 再见!")
            cli.show_stats()
            break
        except Exception as e:
            print(f"❌ 错误: {e}")


if __name__ == "__main__":
    # Windows 事件循环策略
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())
