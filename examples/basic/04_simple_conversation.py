#!/usr/bin/env python3
"""
AutoGen 学习项目 - 示例4: 简单对话系统

展示两个智能体之间的对话，以及如何控制对话流程。

学习要点:
- 双智能体对话
- RoundRobinGroupChat的使用
- 终止条件设置
- 不同的对话场景
- 对话控制和管理
"""

import asyncio
import os

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_core.models import ModelInfo
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

load_dotenv()


def create_model_client(temperature: float = 0.7) -> OpenAIChatCompletionClient:
    """Create a DeepSeek-compatible model client"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")

    return OpenAIChatCompletionClient(
        model=os.getenv("OPENAI_MODEL", "deepseek-chat"),
        api_key=api_key,
        base_url=os.getenv("OPENAI_API_BASE", "https://api.deepseek.com/v1"),
        temperature=temperature,
        model_info=ModelInfo(
            family="openai",
            vision=False,
            function_calling=True,
            json_output=True,
            structured_output=False,
        ),
    )


async def demo_teacher_student_conversation() -> None:
    """Demonstrate a teacher-student conversation"""
    print("\n👨‍🏫 Teacher-Student Conversation Demo")
    print("-" * 50)

    # Create teacher agent
    teacher = AssistantAgent(
        name="PythonTeacher",
        model_client=create_model_client(temperature=0.3),
        system_message="""你是一位耐心的Python编程老师。
        你的特点：
        - 用简单易懂的语言解释概念
        - 提供具体的代码示例
        - 鼓励学生提问
        - 循序渐进地教学

        当学生说"我明白了"时，结束这个话题。""",
    )

    # Create student agent
    student = AssistantAgent(
        name="Student",
        model_client=create_model_client(temperature=0.8),
        system_message="""你是一个好学的Python初学者。
        你的特点：
        - 对编程概念好奇
        - 会提出具体的问题
        - 需要例子来理解概念
        - 学会后会说"我明白了"

        保持学习的热情，但不要问太多问题。""",
    )

    # Set up conversation with termination condition
    termination = TextMentionTermination("我明白了")
    team = RoundRobinGroupChat([teacher, student], termination_condition=termination)

    # Start the lesson
    task = "老师，请教我Python中的列表是什么，怎么使用？"
    result = await team.run(task=task)

    print("📚 教学对话记录:")
    for i, message in enumerate(result.messages, 1):
        sender = message.source if hasattr(message, "source") else "Unknown"
        content = (
            message.content[:150] + "..."
            if len(message.content) > 150
            else message.content
        )
        print(f"   {i}. {sender}: {content}")

    print("\n📊 对话统计:")
    print(f"   总消息数: {len(result.messages)}")
    print(f"   停止原因: {result.stop_reason}")


async def demo_debate_conversation() -> None:
    """Demonstrate a debate between two agents"""
    print("\n🗣️ Debate Conversation Demo")
    print("-" * 50)

    # Create pro-Python agent
    python_advocate = AssistantAgent(
        name="PythonAdvocate",
        model_client=create_model_client(temperature=0.6),
        system_message="""你是Python编程语言的支持者。
        你的观点：
        - Python简单易学
        - 生态系统丰富
        - 适合快速开发
        - 在AI/ML领域领先

        进行友好的辩论，提出有力的论据。当对方说"好吧，你说得有道理"时停止辩论。""",
    )

    # Create JavaScript advocate
    js_advocate = AssistantAgent(
        name="JSAdvocate",
        model_client=create_model_client(temperature=0.6),
        system_message="""你是JavaScript编程语言的支持者。
        你的观点：
        - JavaScript无处不在
        - 前后端都能用
        - 性能在不断提升
        - 社区活跃度高

        进行友好的辩论，但要保持开放的心态。如果对方论据充分，可以说"好吧，你说得有道理"。""",
    )

    # Set up debate with termination condition
    termination = TextMentionTermination("好吧，你说得有道理")
    team = RoundRobinGroupChat(
        [python_advocate, js_advocate],
        termination_condition=termination,
    )

    # Start the debate
    task = "让我们讨论一下：Python和JavaScript哪个更适合初学者学习编程？"
    result = await team.run(task=task)

    print("🎭 辩论记录:")
    for i, message in enumerate(result.messages, 1):
        sender = message.source if hasattr(message, "source") else "Unknown"
        content = (
            message.content[:200] + "..."
            if len(message.content) > 200
            else message.content
        )
        print(f"   {i}. {sender}: {content}")

    print("\n📊 辩论统计:")
    print(f"   总轮次: {len(result.messages)}")
    print(
        f"   获胜者: "
        f"{result.messages[-2].source if len(result.messages) > 1 else 'Unknown'}",
    )


async def demo_creative_collaboration() -> None:
    """Demonstrate creative collaboration between agents"""
    print("\n🎨 Creative Collaboration Demo")
    print("-" * 50)

    # Create story writer
    writer = AssistantAgent(
        name="StoryWriter",
        model_client=create_model_client(temperature=0.9),
        system_message="""你是一位创意作家。
        你的任务：
        - 开始一个有趣的故事
        - 创造生动的场景和角色
        - 留下悬念让编辑续写
        - 保持故事的连贯性

        每次写2-3句话，然后说"请编辑继续"。""",
    )

    # Create editor
    editor = AssistantAgent(
        name="Editor",
        model_client=create_model_client(temperature=0.8),
        system_message="""你是一位故事编辑。
        你的任务：
        - 继续作家开始的故事
        - 发展情节和角色
        - 保持故事风格一致
        - 推进故事发展

        每次写2-3句话。如果故事达到高潮，说"故事完成"。""",
    )

    # Set up collaboration
    termination = TextMentionTermination("故事完成")
    team = RoundRobinGroupChat([writer, editor], termination_condition=termination)

    # Start creative writing
    task = "让我们一起创作一个关于时间旅行者的短篇科幻故事。"
    result = await team.run(task=task)

    print("📖 创作过程:")
    for i, message in enumerate(result.messages, 1):
        sender = message.source if hasattr(message, "source") else "Unknown"
        print(f"   {i}. {sender}:")
        print(f"      {message.content}")
        print()

    print("📊 创作统计:")
    print(f"   总段落: {len(result.messages)}")
    print(
        f"   最终作者: "
        f"{result.messages[-2].source if len(result.messages) > 1 else 'Unknown'}",
    )


async def demo_problem_solving_team() -> None:
    """Demonstrate problem-solving collaboration"""
    print("\n🧩 Problem Solving Team Demo")
    print("-" * 50)

    # Create analyst
    analyst = AssistantAgent(
        name="DataAnalyst",
        model_client=create_model_client(temperature=0.3),
        system_message="""你是一位数据分析师。
        你的职责：
        - 分析问题和数据
        - 提出分析方法
        - 识别关键指标
        - 提供客观的见解

        分析完成后说"分析完成，请解决方案专家提出建议"。""",
    )

    # Create solution architect
    solution_expert = AssistantAgent(
        name="SolutionExpert",
        model_client=create_model_client(temperature=0.5),
        system_message="""你是解决方案专家。
        你的职责：
        - 基于分析结果提出解决方案
        - 考虑实施的可行性
        - 提供具体的行动步骤
        - 评估风险和收益

        方案完成后说"解决方案已制定完成"。""",
    )

    # Set up problem-solving session
    termination = TextMentionTermination("解决方案已制定完成")
    team = RoundRobinGroupChat(
        [analyst, solution_expert],
        termination_condition=termination,
    )

    # Present the problem
    task = "我们的电商网站转化率下降了15%，需要分析原因并提出解决方案。"
    result = await team.run(task=task)

    print("🔍 问题解决过程:")
    for i, message in enumerate(result.messages, 1):
        sender = message.source if hasattr(message, "source") else "Unknown"
        content = (
            message.content[:300] + "..."
            if len(message.content) > 300
            else message.content
        )
        print(f"   {i}. {sender}:")
        print(f"      {content}")
        print()

    print("📊 解决方案统计:")
    print(f"   分析轮次: {len(result.messages)}")


async def demo_max_message_termination() -> None:
    """Demonstrate conversation with max message limit"""
    print("\n⏱️ Max Message Termination Demo")
    print("-" * 50)

    # Create chatty agents
    agent1 = AssistantAgent(
        name="ChatterBox1",
        model_client=create_model_client(temperature=0.7),
        system_message="你是一个健谈的聊天机器人，喜欢讨论技术话题。每次回复要简短。",
    )

    agent2 = AssistantAgent(
        name="ChatterBox2",
        model_client=create_model_client(temperature=0.7),
        system_message="你是另一个健谈的聊天机器人，也喜欢技术讨论。每次回复要简短。",
    )

    # Limit conversation to 6 messages
    termination = MaxMessageTermination(6)
    team = RoundRobinGroupChat([agent1, agent2], termination_condition=termination)

    # Start unlimited chat
    task = "聊聊人工智能的发展趋势吧！"
    result = await team.run(task=task)

    print("💬 限制消息数的对话:")
    for i, message in enumerate(result.messages, 1):
        sender = message.source if hasattr(message, "source") else "Unknown"
        print(f"   {i}. {sender}: {message.content}")

    print("\n📊 对话统计:")
    print(f"   实际消息数: {len(result.messages)}")
    print(f"   停止原因: {result.stop_reason}")
    print("   ✅ 成功在达到消息限制时停止")


async def main() -> None:
    """Main demonstration function"""
    print("🤖 AutoGen 简单对话系统演示")
    print("=" * 60)

    try:
        await demo_teacher_student_conversation()
        await demo_debate_conversation()
        await demo_creative_collaboration()
        await demo_problem_solving_team()
        await demo_max_message_termination()

        print("\n✨ 所有对话演示完成!")
        print("\n📚 关键要点:")
        print("   • RoundRobinGroupChat 管理双智能体对话")
        print("   • 不同的终止条件控制对话流程")
        print("   • 系统消息定义智能体的角色和行为")
        print("   • Temperature 影响回复的创造性")
        print("   • 对话可以有各种应用场景")
        print("   • 适当的终止条件确保对话有意义地结束")

    except Exception as e:
        print(f"❌ 演示失败: {e}")
        print("💡 检查API配置和网络连接")


if __name__ == "__main__":
    asyncio.run(main())
