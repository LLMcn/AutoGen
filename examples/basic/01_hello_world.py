#!/usr/bin/env python3
"""
AutoGen 学习项目 - 示例1: Hello World

这是最基础的AutoGen示例，展示如何创建和使用单个智能体。
支持DeepSeek API（OpenAI兼容）。

学习要点:
- 创建AssistantAgent
- 使用OpenAI兼容的模型客户端
- 异步编程模式
- 基本任务执行
"""

import asyncio
import os
import sys

# 检查必要的包是否安装
try:
    from autogen_agentchat.agents import AssistantAgent
    from autogen_core.models import ModelInfo
    from autogen_ext.models.openai import OpenAIChatCompletionClient
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ 缺少必要的包: {e}")
    print(
        "💡 请先安装: pip install autogen-agentchat autogen-ext[openai] python-dotenv",
    )
    sys.exit(1)

# Load environment variables
load_dotenv()


async def main() -> None:
    """Main function demonstrating basic AutoGen usage"""

    print("🤖 AutoGen Hello World Example (DeepSeek Compatible)")
    print("=" * 60)

    # Check if API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ 错误: 请在 .env 文件中设置 OPENAI_API_KEY")
        print("💡 提示: 复制 env.example 为 .env 并填入你的DeepSeek API密钥")
        return

    # Get API configuration
    api_base = os.getenv("OPENAI_API_BASE", "https://api.deepseek.com/v1")
    model_name = os.getenv("OPENAI_MODEL", "deepseek-chat")

    print("🔧 配置信息:")
    print(f"   API Base: {api_base}")
    print(f"   Model: {model_name}")
    print(
        f"   API Key: "
        f"{'*' * (len(api_key) - 8) + api_key[-8:] if len(api_key) > 8 else '***'}",
    )

    try:
        # Create model client (compatible with DeepSeek)
        model_client = OpenAIChatCompletionClient(
            model=model_name,
            api_key=api_key,
            base_url=api_base,  # DeepSeek API endpoint
            model_info=ModelInfo(
                family="openai",
                vision=False,
                function_calling=True,
                json_output=True,
                structured_output=False,
            ),
        )

        # Create an assistant agent
        assistant = AssistantAgent(
            name="HelloWorldAssistant",
            model_client=model_client,
            system_message="你是一个友好的AI助手，帮助用户学习AutoGen。"
            "请用中文回答，并且要简洁明了。",
        )

        # Simple task execution
        print("\n🚀 运行第一个任务...")
        result = await assistant.run(
            task="请说'Hello World!'并用一句话解释什么是AutoGen。",
        )

        print("✅ 助手回复:")
        print(f"   {result.messages[-1].content}")

        # Another task to show conversation capability
        print("\n🔄 运行第二个任务...")
        result2 = await assistant.run(task="AutoGen在多智能体系统方面有什么特别之处？")

        print("✅ 助手回复:")
        print(f"   {result2.messages[-1].content}")

        print("\n📊 对话总结:")
        print(f"   总消息数: {len(result2.messages)}")
        print(f"   智能体名称: {assistant.name}")
        print("   ✅ 测试成功! AutoGen与DeepSeek API兼容良好")

    except Exception as e:
        print(f"❌ 错误: {e}")
        print("💡 提示:")
        print("   1. 确保DeepSeek API密钥有效且有余额")
        print("   2. 检查网络连接")
        print("   3. 确认API配置正确")
        print(f"   4. 错误详情: {type(e).__name__}")


if __name__ == "__main__":
    print("启动AutoGen Hello World示例...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 用户中断，程序退出")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
    finally:
        print("✨ 示例完成!")
