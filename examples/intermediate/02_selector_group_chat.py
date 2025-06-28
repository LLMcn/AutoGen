#!/usr/bin/env python3
"""
AutoGen 学习项目 - 中级示例2: 智能选择器群组聊天

展示SelectorGroupChat的高级功能，智能选择发言者。

学习要点:
- SelectorGroupChat vs RoundRobinGroupChat
- 智能发言者选择机制
- 专业化智能体团队
- 复杂对话管理
- 动态角色分配
"""

import asyncio
import os

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import SelectorGroupChat
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


async def demo_research_team() -> None:
    """演示研究团队的智能协作"""
    print("\n🔬 Research Team Demo")
    print("-" * 50)

    # 创建研究团队成员
    research_lead = AssistantAgent(
        name="ResearchLead",
        model_client=create_model_client(temperature=0.3),
        system_message="""你是研究团队负责人。
        职责：
        - 制定研究计划和方向
        - 分配任务给团队成员
        - 协调不同专业领域的工作
        - 总结研究成果

        当需要具体的技术分析时，请技术专家发言。
        当需要数据分析时，请数据科学家发言。
        当研究完成时说"研究项目完成"。""",
    )

    tech_expert = AssistantAgent(
        name="TechExpert",
        model_client=create_model_client(temperature=0.4),
        system_message="""你是技术专家。
        专长：
        - 深度学习和机器学习算法
        - 系统架构设计
        - 技术可行性分析
        - 性能优化建议

        只在被询问技术问题时发言，提供专业的技术见解。""",
    )

    data_scientist = AssistantAgent(
        name="DataScientist",
        model_client=create_model_client(temperature=0.4),
        system_message="""你是数据科学家。
        专长：
        - 数据分析和统计建模
        - 数据可视化
        - 实验设计
        - 结果解释

        只在被询问数据相关问题时发言，提供数据驱动的洞察。""",
    )

    # 创建选择器群组
    termination = TextMentionTermination("研究项目完成")
    research_team = SelectorGroupChat(
        participants=[research_lead, tech_expert, data_scientist],
        model_client=create_model_client(temperature=0.2),
        termination_condition=termination,
    )

    # 开始研究项目
    task = (
        "我们需要研究如何提高推荐系统的准确性和用户满意度。"
        "请制定研究计划并分析关键技术挑战。"
    )
    result = await research_team.run(task=task)

    print("🔬 研究团队协作过程:")
    for i, message in enumerate(result.messages, 1):
        sender = message.source if hasattr(message, "source") else "Unknown"
        content = (
            message.content[:200] + "..."
            if len(message.content) > 200
            else message.content
        )
        print(f"   {i}. {sender}: {content}")

    print("\n📊 研究统计:")
    print(f"   总消息数: {len(result.messages)}")
    print(f"   停止原因: {result.stop_reason}")


async def demo_creative_team() -> None:
    """演示创意团队的协作"""
    print("\n🎨 Creative Team Demo")
    print("-" * 50)

    # 创建创意团队
    creative_director = AssistantAgent(
        name="CreativeDirector",
        model_client=create_model_client(temperature=0.8),
        system_message="""你是创意总监。
        职责：
        - 把控整体创意方向
        - 协调不同创意角色
        - 确保创意的一致性和质量
        - 做最终的创意决策

        当需要文案时请文案专家发言，需要设计时请设计师发言。
        当创意方案完成时说"创意项目完成"。""",
    )

    copywriter = AssistantAgent(
        name="Copywriter",
        model_client=create_model_client(temperature=0.9),
        system_message="""你是文案专家。
        专长：
        - 创作吸引人的广告文案
        - 品牌故事叙述
        - 营销内容策划
        - 用户心理洞察

        只在被要求创作文案时发言，提供创意和有说服力的文字内容。""",
    )

    designer = AssistantAgent(
        name="Designer",
        model_client=create_model_client(temperature=0.8),
        system_message="""你是视觉设计师。
        专长：
        - 视觉概念设计
        - 色彩和排版建议
        - 用户体验设计
        - 品牌视觉识别

        只在被询问设计相关问题时发言，提供专业的视觉设计建议。""",
    )

    # 创建创意团队
    termination = TextMentionTermination("创意项目完成")
    creative_team = SelectorGroupChat(
        participants=[creative_director, copywriter, designer],
        model_client=create_model_client(temperature=0.3),
        termination_condition=termination,
    )

    # 开始创意项目
    task = "为一个新的环保科技产品设计营销活动，包括核心信息、文案和视觉风格建议。"
    result = await creative_team.run(task=task)

    print("🎨 创意团队协作过程:")
    for i, message in enumerate(result.messages, 1):
        sender = message.source if hasattr(message, "source") else "Unknown"
        content = (
            message.content[:200] + "..."
            if len(message.content) > 200
            else message.content
        )
        print(f"   {i}. {sender}: {content}")


async def demo_business_analysis_team() -> None:
    """演示商业分析团队"""
    print("\n💼 Business Analysis Team Demo")
    print("-" * 50)

    # 创建商业分析团队
    business_analyst = AssistantAgent(
        name="BusinessAnalyst",
        model_client=create_model_client(temperature=0.3),
        system_message="""你是首席商业分析师。
        职责：
        - 分析商业问题和机会
        - 协调不同专业分析
        - 整合各方面洞察
        - 提供最终建议

        当需要市场分析时请市场专家发言，需要财务分析时请财务专家发言。
        当分析完成时说"商业分析完成"。""",
    )

    market_analyst = AssistantAgent(
        name="MarketAnalyst",
        model_client=create_model_client(temperature=0.4),
        system_message="""你是市场分析专家。
        专长：
        - 市场趋势分析
        - 竞争对手研究
        - 用户需求洞察
        - 市场机会识别

        只在被询问市场相关问题时发言，提供专业的市场分析。""",
    )

    financial_analyst = AssistantAgent(
        name="FinancialAnalyst",
        model_client=create_model_client(temperature=0.2),
        system_message="""你是财务分析专家。
        专长：
        - 财务模型构建
        - 投资回报分析
        - 风险评估
        - 成本效益分析

        只在被询问财务问题时发言，提供专业的财务分析和建议。""",
    )

    # 创建商业分析团队
    termination = TextMentionTermination("商业分析完成")
    business_team = SelectorGroupChat(
        participants=[business_analyst, market_analyst, financial_analyst],
        model_client=create_model_client(temperature=0.2),
        termination_condition=termination,
    )

    # 开始商业分析
    task = "分析进入在线教育市场的商业机会，包括市场潜力、竞争状况和财务可行性。"
    result = await business_team.run(task=task)

    print("💼 商业分析团队协作过程:")
    for i, message in enumerate(result.messages, 1):
        sender = message.source if hasattr(message, "source") else "Unknown"
        content = (
            message.content[:200] + "..."
            if len(message.content) > 200
            else message.content
        )
        print(f"   {i}. {sender}: {content}")


async def demo_selector_vs_roundrobin() -> None:
    """演示SelectorGroupChat与RoundRobinGroupChat的区别"""
    print("\n🔄 Selector vs RoundRobin Comparison")
    print("-" * 50)

    # 创建相同的智能体
    manager = AssistantAgent(
        name="ProjectManager",
        model_client=create_model_client(temperature=0.3),
        system_message="""你是项目经理，负责协调团队工作。
        根据任务需要选择合适的团队成员发言。""",
    )

    developer = AssistantAgent(
        name="Developer",
        model_client=create_model_client(temperature=0.4),
        system_message="""你是开发工程师，专注于技术实现。
        只在被询问技术问题时发言。""",
    )

    tester = AssistantAgent(
        name="Tester",
        model_client=create_model_client(temperature=0.4),
        system_message="""你是测试工程师，专注于质量保证。
        只在被询问测试相关问题时发言。""",
    )

    # 使用SelectorGroupChat
    print("🎯 使用SelectorGroupChat:")
    termination = MaxMessageTermination(6)
    selector_team = SelectorGroupChat(
        participants=[manager, developer, tester],
        model_client=create_model_client(temperature=0.2),
        termination_condition=termination,
    )

    task = "我们需要开发一个新功能，请制定开发和测试计划。"
    result = await selector_team.run(task=task)

    for i, message in enumerate(result.messages, 1):
        sender = message.source if hasattr(message, "source") else "Unknown"
        print(f"   {i}. {sender}: {message.content[:100]}...")

    print("\n📊 SelectorGroupChat统计:")
    print(f"   总消息数: {len(result.messages)}")

    # 对比说明
    print("\n🔍 SelectorGroupChat的优势:")
    print("   • 智能选择最合适的发言者")
    print("   • 避免不必要的轮换发言")
    print("   • 更自然的对话流程")
    print("   • 基于内容的动态角色分配")


async def demo_complex_project_team() -> None:
    """演示复杂项目团队协作"""
    print("\n🏗️ Complex Project Team Demo")
    print("-" * 50)

    # 创建复杂项目团队
    project_lead = AssistantAgent(
        name="ProjectLead",
        model_client=create_model_client(temperature=0.3),
        system_message="""你是项目负责人。
        职责：
        - 整体项目规划和管理
        - 协调各个专业团队
        - 风险识别和管理
        - 项目进度控制

        根据讨论内容选择合适的专家发言。
        当项目规划完成时说"项目规划完成"。""",
    )

    architect = AssistantAgent(
        name="Architect",
        model_client=create_model_client(temperature=0.4),
        system_message="""你是系统架构师。
        专长：
        - 系统架构设计
        - 技术选型建议
        - 可扩展性规划
        - 性能优化策略

        只在被询问架构相关问题时发言。""",
    )

    product_manager = AssistantAgent(
        name="ProductManager",
        model_client=create_model_client(temperature=0.5),
        system_message="""你是产品经理。
        专长：
        - 产品需求分析
        - 用户体验设计
        - 功能优先级排序
        - 市场需求洞察

        只在被询问产品相关问题时发言。""",
    )

    security_expert = AssistantAgent(
        name="SecurityExpert",
        model_client=create_model_client(temperature=0.2),
        system_message="""你是安全专家。
        专长：
        - 安全风险评估
        - 安全架构设计
        - 合规性检查
        - 安全最佳实践

        只在被询问安全相关问题时发言。""",
    )

    # 创建复杂项目团队
    termination = TextMentionTermination("项目规划完成")
    project_team = SelectorGroupChat(
        participants=[project_lead, architect, product_manager, security_expert],
        model_client=create_model_client(temperature=0.2),
        termination_condition=termination,
    )

    # 开始复杂项目规划
    task = (
        "规划一个企业级的客户数据管理平台，"
        "需要考虑技术架构、产品功能、安全合规等各个方面。"
    )
    result = await project_team.run(task=task)

    print("🏗️ 复杂项目团队协作过程:")
    for i, message in enumerate(result.messages, 1):
        sender = message.source if hasattr(message, "source") else "Unknown"
        content = (
            message.content[:150] + "..."
            if len(message.content) > 150
            else message.content
        )
        print(f"   {i}. {sender}: {content}")


async def main() -> None:
    """主演示函数"""
    print("🎯 AutoGen 智能选择器群组聊天演示")
    print("=" * 60)

    try:
        await demo_research_team()
        await demo_creative_team()
        await demo_business_analysis_team()
        await demo_selector_vs_roundrobin()
        await demo_complex_project_team()

        print("\n✨ 所有选择器群组聊天演示完成!")
        print("\n📚 关键要点:")
        print("   • SelectorGroupChat 智能选择最合适的发言者")
        print("   • 专业化智能体提高团队协作效率")
        print("   • 基于内容的动态角色分配更自然")
        print("   • 复杂项目可以通过多专家协作完成")
        print("   • 智能选择器减少不必要的轮换发言")
        print("   • 适合需要专业分工的复杂任务")

    except Exception as e:
        print(f"❌ 演示失败: {e}")
        print("💡 检查API配置和网络连接")


if __name__ == "__main__":
    asyncio.run(main())
