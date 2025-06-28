#!/usr/bin/env python3
"""
AutoGen 学习项目 - 中级示例1: 工具集成

展示如何为智能体添加工具功能，让AI能够执行具体的操作。

学习要点:
- 工具函数的定义和注册
- 智能体如何调用工具
- 工具链的协作
- 错误处理和工具安全
- 多工具智能体的设计
"""

import asyncio
import json
import os
import random

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_core.models import ModelInfo
from autogen_core.tools import FunctionTool
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

load_dotenv()


def create_model_client(temperature: float = 0.3) -> OpenAIChatCompletionClient:
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


# 定义各种工具函数
def calculator(expression: str) -> str:
    """
    安全的计算器工具

    Args:
        expression: 数学表达式字符串

    Returns:
        计算结果或错误信息
    """
    try:
        # 只允许安全的数学运算
        allowed_chars = set("0123456789+-*/()., ")
        if not all(c in allowed_chars for c in expression):
            return "错误：表达式包含不允许的字符"

        # 使用ast.literal_eval进行安全计算
        import ast
        import operator

        # 定义允许的操作
        ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }

        def safe_eval(node):
            if isinstance(node, ast.Constant):  # Python 3.8+
                return node.value
            if isinstance(node, ast.Num):  # Python < 3.8
                return node.n
            if isinstance(node, ast.BinOp):
                return ops[type(node.op)](safe_eval(node.left), safe_eval(node.right))
            if isinstance(node, ast.UnaryOp):
                return ops[type(node.op)](safe_eval(node.operand))
            raise ValueError(f"不支持的操作: {type(node)}")

        # 解析并计算表达式
        tree = ast.parse(expression, mode="eval")
        result = safe_eval(tree.body)
        return f"计算结果: {result}"
    except Exception as e:
        return f"计算错误: {e!s}"


def weather_simulator(city: str) -> str:
    """
    模拟天气查询工具

    Args:
        city: 城市名称

    Returns:
        模拟的天气信息
    """
    # 模拟不同城市的天气
    weather_conditions = ["晴朗", "多云", "小雨", "大雨", "雪", "雾"]
    temperature = random.randint(-10, 35)
    condition = random.choice(weather_conditions)
    humidity = random.randint(30, 90)

    return f"{city}当前天气: {condition}, 温度: {temperature}°C, 湿度: {humidity}%"


def text_analyzer(text: str) -> str:
    """
    文本分析工具

    Args:
        text: 要分析的文本

    Returns:
        文本分析结果
    """
    word_count = len(text.split())
    char_count = len(text)
    sentence_count = text.count(".") + text.count("!") + text.count("?")

    # 简单的情感分析
    positive_words = ["好", "棒", "优秀", "喜欢", "高兴", "满意", "成功"]
    negative_words = ["坏", "差", "失败", "讨厌", "难过", "失望", "错误"]

    positive_count = sum(1 for word in positive_words if word in text)
    negative_count = sum(1 for word in negative_words if word in text)

    if positive_count > negative_count:
        sentiment = "积极"
    elif negative_count > positive_count:
        sentiment = "消极"
    else:
        sentiment = "中性"

    return f"""文本分析结果:
- 字数: {word_count}
- 字符数: {char_count}
- 句子数: {sentence_count}
- 情感倾向: {sentiment}
- 积极词汇: {positive_count}个
- 消极词汇: {negative_count}个"""


def data_storage(action: str, key: str, value: str = "") -> str:
    """
    简单的数据存储工具

    Args:
        action: 操作类型 (store/retrieve/list)
        key: 数据键
        value: 数据值 (仅在store时需要)

    Returns:
        操作结果
    """
    # 使用文件模拟数据存储
    storage_file = "tool_storage.json"

    try:
        # 读取现有数据
        if os.path.exists(storage_file):
            with open(storage_file, encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}

        if action == "store":
            data[key] = value
            with open(storage_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return f"已存储: {key} = {value}"

        if action == "retrieve":
            if key in data:
                return f"检索到: {key} = {data[key]}"
            return f"未找到键: {key}"

        if action == "list":
            if data:
                items = [f"{k}: {v}" for k, v in data.items()]
                return "存储的数据:\n" + "\n".join(items)
            return "存储为空"

        return f"不支持的操作: {action}"

    except Exception as e:
        return f"存储操作错误: {e!s}"


async def demo_single_tool_agent() -> None:
    """演示单工具智能体"""
    print("\n🔧 Single Tool Agent Demo")
    print("-" * 50)

    # 创建计算器工具
    calc_tool = FunctionTool(calculator, description="执行数学计算")

    # 创建带计算器工具的智能体
    calculator_agent = AssistantAgent(
        name="CalculatorAgent",
        model_client=create_model_client(),
        tools=[calc_tool],
        system_message="""你是一个数学计算助手。
        你可以使用计算器工具来执行数学运算。
        当用户要求计算时，使用calculator工具来完成。
        用中文解释计算过程和结果。""",
    )

    # 测试计算功能
    tasks = ["计算 25 * 4 + 15", "计算 (100 - 25) / 3", "计算 2 ** 10"]

    for task in tasks:
        print(f"\n📊 任务: {task}")
        result = await calculator_agent.run(task=task)
        print(f"🤖 回复: {result.messages[-1].content}")


async def demo_multi_tool_agent() -> None:
    """演示多工具智能体"""
    print("\n🛠️ Multi-Tool Agent Demo")
    print("-" * 50)

    # 创建多个工具
    tools = [
        FunctionTool(calculator, description="执行数学计算"),
        FunctionTool(weather_simulator, description="查询城市天气"),
        FunctionTool(text_analyzer, description="分析文本内容"),
        FunctionTool(data_storage, description="存储和检索数据"),
    ]

    # 创建多工具智能体
    multi_tool_agent = AssistantAgent(
        name="MultiToolAgent",
        model_client=create_model_client(),
        tools=tools,
        system_message="""你是一个多功能助手，拥有以下工具：
        1. calculator - 数学计算
        2. weather_simulator - 天气查询
        3. text_analyzer - 文本分析
        4. data_storage - 数据存储

        根据用户请求选择合适的工具来完成任务。
        用中文回复并解释你的操作。""",
    )

    # 测试多种工具功能
    tasks = [
        "帮我计算一下北京今天的气温是多少度，如果加上15度会是多少？",
        "分析这段文本的情感：'今天天气很好，我很高兴能完成这个项目'",
        "存储一个记录：项目进度=90%",
        "检索刚才存储的项目进度",
    ]

    for task in tasks:
        print(f"\n📋 任务: {task}")
        result = await multi_tool_agent.run(task=task)
        print(f"🤖 回复: {result.messages[-1].content}")


async def demo_tool_chain_collaboration() -> None:
    """演示工具链协作"""
    print("\n🔗 Tool Chain Collaboration Demo")
    print("-" * 50)

    # 创建数据分析师
    analyst = AssistantAgent(
        name="DataAnalyst",
        model_client=create_model_client(),
        tools=[
            FunctionTool(calculator, description="执行数学计算"),
            FunctionTool(text_analyzer, description="分析文本内容"),
        ],
        system_message="""你是数据分析师，专门负责数据分析和计算。
        使用工具来分析数据并提供洞察。
        分析完成后，将结果传递给存储专家。""",
    )

    # 创建存储专家
    storage_expert = AssistantAgent(
        name="StorageExpert",
        model_client=create_model_client(),
        tools=[FunctionTool(data_storage, description="存储和检索数据")],
        system_message="""你是存储专家，负责数据的存储和管理。
        接收分析结果并妥善存储，确保数据的完整性。
        当任务完成时说"数据已安全存储"。""",
    )

    # 创建协作团队
    termination = MaxMessageTermination(8)
    team = RoundRobinGroupChat(
        [analyst, storage_expert],
        termination_condition=termination,
    )

    # 执行协作任务
    task = """请分析以下销售数据并存储结果：
    销售额数据：第一季度120万，第二季度150万，第三季度180万
    客户反馈：'产品质量很好，服务态度优秀，会继续购买'

    请计算总销售额、平均季度销售额，分析客户反馈情感，并存储这些结果。"""

    result = await team.run(task=task)

    print("🔗 工具链协作过程:")
    for i, message in enumerate(result.messages, 1):
        sender = message.source if hasattr(message, "source") else "Unknown"
        content = (
            message.content[:200] + "..."
            if len(message.content) > 200
            else message.content
        )
        print(f"   {i}. {sender}: {content}")


async def demo_error_handling() -> None:
    """演示工具错误处理"""
    print("\n⚠️ Tool Error Handling Demo")
    print("-" * 50)

    # 创建带错误处理的智能体
    robust_agent = AssistantAgent(
        name="RobustAgent",
        model_client=create_model_client(),
        tools=[
            FunctionTool(calculator, description="执行数学计算"),
            FunctionTool(weather_simulator, description="查询城市天气"),
        ],
        system_message="""你是一个具有错误处理能力的助手。
        当工具执行失败时，要：
        1. 识别错误原因
        2. 提供替代方案
        3. 给出有用的建议

        始终保持友好和有帮助的态度。""",
    )

    # 测试错误场景
    error_tasks = [
        "计算 10 / 0",  # 除零错误
        "计算 import os",  # 非法表达式
        "查询火星的天气",  # 这个应该能正常工作，因为是模拟器
    ]

    for task in error_tasks:
        print(f"\n🧪 错误测试: {task}")
        try:
            result = await robust_agent.run(task=task)
            print(f"🤖 处理结果: {result.messages[-1].content}")
        except Exception as e:
            print(f"❌ 异常: {e}")


async def main() -> None:
    """主演示函数"""
    print("🛠️ AutoGen 工具集成演示")
    print("=" * 60)

    try:
        await demo_single_tool_agent()
        await demo_multi_tool_agent()
        await demo_tool_chain_collaboration()
        await demo_error_handling()

        print("\n✨ 所有工具集成演示完成!")
        print("\n📚 关键要点:")
        print("   • FunctionTool 让智能体具备具体操作能力")
        print("   • 工具函数需要适当的错误处理")
        print("   • 多工具智能体可以处理复杂任务")
        print("   • 工具链协作提高任务处理效率")
        print("   • 安全性是工具设计的重要考虑")

        # 清理临时文件
        if os.path.exists("tool_storage.json"):
            os.remove("tool_storage.json")
            print("   • 已清理临时存储文件")

    except Exception as e:
        print(f"❌ 演示失败: {e}")
        print("💡 检查API配置和网络连接")


if __name__ == "__main__":
    asyncio.run(main())
