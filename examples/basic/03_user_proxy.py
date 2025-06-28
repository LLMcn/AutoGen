#!/usr/bin/env python3
"""
AutoGen 学习项目 - 示例3: 用户代理智能体

展示UserProxyAgent的功能，包括人机交互模式。

学习要点:
- UserProxyAgent的配置
- 人机交互模式
- 与AssistantAgent的协作
- 工作流控制
"""

import asyncio
import os

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_core.models import ModelInfo
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

load_dotenv()


def create_model_client() -> OpenAIChatCompletionClient:
    """Create a DeepSeek-compatible model client"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")

    return OpenAIChatCompletionClient(
        model=os.getenv("OPENAI_MODEL", "deepseek-chat"),
        api_key=api_key,
        base_url=os.getenv("OPENAI_API_BASE", "https://api.deepseek.com/v1"),
        temperature=0.3,
        model_info=ModelInfo(
            family="openai",
            vision=False,
            function_calling=True,
            json_output=True,
            structured_output=False,
        ),
    )


async def demo_basic_user_proxy() -> None:
    """Demonstrate basic UserProxyAgent functionality"""
    print("\n🤖 Basic UserProxy Demo")
    print("-" * 40)

    # Create assistant
    assistant = AssistantAgent(
        name="PythonHelper",
        model_client=create_model_client(),
        system_message="""你是一个Python编程助手。
        当用户需要代码时，提供完整的、可运行的Python代码。
        用中文解释你的代码逻辑。""",
    )

    # Create user proxy with basic configuration
    user_proxy = UserProxyAgent(name="User", description="代表用户进行交互的代理")

    # Create a simple task
    task = "写一个Python函数来计算斐波那契数列的前n项，并展示如何使用它。"

    # Create team and run conversation
    termination = MaxMessageTermination(3)
    team = RoundRobinGroupChat(
        [assistant, user_proxy],
        termination_condition=termination,
    )
    result = await team.run(task=task)

    print("📝 对话结果:")
    for i, message in enumerate(result.messages[-3:], 1):
        sender = message.source if hasattr(message, "source") else "Unknown"
        content = (
            message.content[:200] + "..."
            if len(message.content) > 200
            else message.content
        )
        print(f"   {i}. {sender}: {content}")


async def demo_custom_input_function() -> None:
    """Demonstrate UserProxy with custom input function"""
    print("\n🎯 Custom Input Function Demo")
    print("-" * 40)

    # Predefined responses to simulate user interaction
    responses = [
        "我想学习数据分析",
        "我是初学者，主要想处理CSV文件",
        "好的，请给我一个简单的例子",
    ]
    response_index = 0

    def custom_input_func(prompt: str) -> str:
        nonlocal response_index
        if response_index < len(responses):
            response = responses[response_index]
            response_index += 1
            print(f"👤 模拟用户输入: {response}")
            return response
        return "谢谢你的帮助！"

    assistant = AssistantAgent(
        name="InteractiveHelper",
        model_client=create_model_client(),
        system_message="""你是一个交互式助手。
        你会提出问题来更好地理解用户需求。
        当你需要更多信息时，明确询问。
        保持对话自然和有帮助。""",
    )

    user_proxy = UserProxyAgent(
        name="SimulatedUser",
        description="模拟用户交互的代理",
        input_func=custom_input_func,
    )

    task = "我需要帮助，但不确定具体要什么。"

    termination = MaxMessageTermination(6)
    team = RoundRobinGroupChat(
        [assistant, user_proxy],
        termination_condition=termination,
    )
    result = await team.run(task=task)

    print("\n💬 交互式对话摘要:")
    conversation_count = 0
    for message in result.messages:
        if hasattr(message, "source"):
            conversation_count += 1
            if conversation_count <= 4:  # Show first few exchanges
                print(f"   {message.source}: {message.content[:100]}...")


async def demo_collaborative_workflow() -> None:
    """Demonstrate collaborative workflow between agents"""
    print("\n🤝 Collaborative Workflow Demo")
    print("-" * 40)

    # Create specialized assistant
    planner = AssistantAgent(
        name="TaskPlanner",
        model_client=create_model_client(),
        system_message="""你是一个任务规划专家。
        你的职责是：
        1. 分析用户需求
        2. 制定详细的执行计划
        3. 将复杂任务分解为简单步骤
        4. 提供清晰的指导""",
    )

    # Create user proxy to represent project manager
    project_manager = UserProxyAgent(
        name="ProjectManager",
        description="项目经理，负责审核和指导任务执行",
    )

    task = "规划一个数据科学项目：分析电商网站的用户行为数据，找出提升转化率的机会。"

    termination = MaxMessageTermination(4)
    team = RoundRobinGroupChat(
        [planner, project_manager],
        termination_condition=termination,
    )
    result = await team.run(task=task)

    print("📊 协作工作流结果:")
    print(f"   总轮次: {len(result.messages)}")
    for i, message in enumerate(result.messages[-2:], 1):
        sender = message.source if hasattr(message, "source") else "Unknown"
        print(f"   {i}. {sender}: {message.content[:150]}...")


async def demo_role_based_interaction() -> None:
    """Demonstrate role-based interaction patterns"""
    print("\n🎭 Role-Based Interaction Demo")
    print("-" * 40)

    # Create teacher assistant
    teacher = AssistantAgent(
        name="PythonTeacher",
        model_client=create_model_client(),
        system_message="""你是一位耐心的Python编程老师。
        你的教学方式：
        1. 先解释概念
        2. 提供简单例子
        3. 询问学生是否理解
        4. 根据反馈调整教学节奏""",
    )

    # Simulate student responses
    student_responses = [
        "我想学习Python的列表操作",
        "能举个具体例子吗？",
        "明白了，那字典怎么用？",
    ]
    response_idx = 0

    def student_input(prompt: str) -> str:
        nonlocal response_idx
        if response_idx < len(student_responses):
            response = student_responses[response_idx]
            response_idx += 1
            print(f"🎓 学生说: {response}")
            return response
        return "我理解了，谢谢老师！"

    student = UserProxyAgent(
        name="Student",
        description="正在学习Python的学生",
        input_func=student_input,
    )

    # Start the lesson
    task = "开始一节关于Python数据结构的课程。"

    termination = MaxMessageTermination(6)
    team = RoundRobinGroupChat([teacher, student], termination_condition=termination)
    result = await team.run(task=task)

    print("\n📚 教学互动总结:")
    print(f"   教学轮次: {len(result.messages)}")
    print("   最后的师生对话:")
    for message in result.messages[-2:]:
        sender = message.source if hasattr(message, "source") else "Unknown"
        print(f"   {sender}: {message.content[:120]}...")


async def main() -> None:
    """Main demonstration function"""
    print("🤖 AutoGen UserProxyAgent 功能展示")
    print("=" * 50)

    try:
        await demo_basic_user_proxy()
        await demo_custom_input_function()
        await demo_collaborative_workflow()
        await demo_role_based_interaction()

        print("\n✨ 所有UserProxy演示完成!")
        print("\n📚 关键要点:")
        print("   • UserProxyAgent 代表人类用户进行交互")
        print("   • 可以配置自定义输入函数模拟用户行为")
        print("   • 在团队中充当重要的协调角色")
        print("   • 支持各种角色扮演和工作流模式")
        print("   • 是人机协作的重要桥梁")

    except Exception as e:
        print(f"❌ 演示失败: {e}")
        print("💡 检查API配置和网络连接")


if __name__ == "__main__":
    asyncio.run(main())
