#!/usr/bin/env python3
"""
AutoGen 学习项目 - 示例2: 助手智能体深入探索

展示AssistantAgent的各种配置选项和功能特性。

学习要点:
- AssistantAgent的详细配置
- 系统消息的重要性
- 不同的模型参数设置
- 消息历史管理
- 错误处理和重试机制
"""

import asyncio
import os

from autogen_agentchat.agents import AssistantAgent
from autogen_core.models import ModelInfo
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

load_dotenv()


class AgentDemo:
    """Demonstration class for AssistantAgent capabilities"""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

    def create_model_client(
        self,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> OpenAIChatCompletionClient:
        """Create a configured DeepSeek-compatible model client"""
        return OpenAIChatCompletionClient(
            model=os.getenv("OPENAI_MODEL", "deepseek-chat"),
            api_key=self.api_key,
            base_url=os.getenv("OPENAI_API_BASE", "https://api.deepseek.com/v1"),
            # Model parameters for controlling behavior
            temperature=temperature,  # Creativity level (0.0-1.0)
            max_tokens=max_tokens,  # Maximum response length
            top_p=0.9,  # Nucleus sampling parameter
            model_info=ModelInfo(
                family="openai",
                vision=False,
                function_calling=True,
                json_output=True,
                structured_output=False,
            ),
        )

    async def demo_basic_assistant(self) -> None:
        """Demonstrate basic assistant creation and usage"""
        print("\n🔧 Basic Assistant Agent Demo")
        print("-" * 40)

        model_client = self.create_model_client(temperature=0.3)

        # Create a specialized assistant
        coding_assistant = AssistantAgent(
            name="CodingMentor",
            model_client=model_client,
            system_message="""你是一位专业的Python编程导师。
            你的职责是:
            1. 清晰地解释编程概念
            2. 提供带注释的代码示例
            3. 建议最佳实践
            4. 帮助调试问题

            总是用markdown格式化代码，并解释你的推理过程。""",
        )

        # Ask a coding question
        task = "解释Python中列表推导式和生成器表达式的区别，并提供示例。"
        result = await coding_assistant.run(task=task)

        print(f"🤖 {coding_assistant.name} 说:")
        print(f"   {result.messages[-1].content[:200]}...")
        print(f"   [回复长度: {len(result.messages[-1].content)} 字符]")

    async def demo_creative_assistant(self) -> None:
        """Demonstrate creative assistant with higher temperature"""
        print("\n🎨 Creative Assistant Demo")
        print("-" * 40)

        # Higher temperature for more creative responses
        model_client = self.create_model_client(temperature=0.9)

        creative_writer = AssistantAgent(
            name="CreativeWriter",
            model_client=model_client,
            system_message="""你是一位富有创意的写作助手。
            你擅长:
            - 创作引人入胜的故事
            - 创造生动的描述
            - 开发独特的角色
            - 以各种风格和类型写作

            在回复中要富有想象力和表现力。""",
        )

        task = "写一个关于AI发现自己能够做梦的科幻故事开头。"
        result = await creative_writer.run(task=task)

        print(f"✨ {creative_writer.name} 创作:")
        print(f"   {result.messages[-1].content[:300]}...")

    async def demo_conversation_memory(self) -> None:
        """Demonstrate conversation memory and context"""
        print("\n🧠 Conversation Memory Demo")
        print("-" * 40)

        model_client = self.create_model_client(temperature=0.5)

        memory_assistant = AssistantAgent(
            name="MemoryKeeper",
            model_client=model_client,
            system_message="""你是一个拥有出色记忆力的助手。
            你能记住所有之前的对话，并可以引用它们。
            总是确认你从之前的互动中记住了什么。""",
        )

        # First interaction
        print("💬 第一次对话:")
        result1 = await memory_assistant.run(task="我的名字是Alice，我喜欢Python编程。")
        print(f"   助手: {result1.messages[-1].content}")

        # Second interaction - testing memory
        print("\n💬 第二次对话 (测试记忆):")
        result2 = await memory_assistant.run(task="我的名字是什么？我喜欢什么？")
        print(f"   助手: {result2.messages[-1].content}")

        # Show conversation history
        print(f"\n📊 对话中总消息数: {len(result2.messages)}")

    async def demo_error_handling(self) -> None:
        """Demonstrate error handling with invalid requests"""
        print("\n⚠️  Error Handling Demo")
        print("-" * 40)

        model_client = self.create_model_client()

        assistant = AssistantAgent(
            name="RobustAssistant",
            model_client=model_client,
            system_message="你是一个优雅处理错误的助手。",
        )

        try:
            # This should work fine
            result = await assistant.run(task="2 + 2 等于多少？")
            print(f"✅ 正常请求: {result.messages[-1].content}")

            # Test with very long input (might hit token limits)
            long_task = "解释这个: " + "非常 " * 1000 + "关于AutoGen的长问题"
            result = await assistant.run(task=long_task)
            print(f"✅ 长请求处理: 回复长度 {len(result.messages[-1].content)}")

        except Exception as e:
            print(f"❌ 捕获错误: {e}")
            print("💡 这展示了在生产代码中错误处理的重要性")


async def main() -> None:
    """Main demonstration function"""
    print("🤖 AutoGen AssistantAgent 深入探索")
    print("=" * 50)

    try:
        demo = AgentDemo()

        # Run all demonstrations
        await demo.demo_basic_assistant()
        await demo.demo_creative_assistant()
        await demo.demo_conversation_memory()
        await demo.demo_error_handling()

        print("\n✨ 所有演示成功完成!")
        print("\n📚 关键要点:")
        print("   • AssistantAgent 高度可配置")
        print("   • 系统消息定义智能体行为")
        print("   • Temperature 控制创造性与一致性")
        print("   • 智能体维护对话记忆")
        print("   • 适当的错误处理至关重要")

    except Exception as e:
        print(f"❌ 演示失败: {e}")
        print("💡 确保你的API密钥设置正确且有效")


if __name__ == "__main__":
    asyncio.run(main())
