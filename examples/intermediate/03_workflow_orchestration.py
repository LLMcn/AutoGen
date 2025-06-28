#!/usr/bin/env python3
"""
AutoGen 学习项目 - 中级示例3: 工作流编排

展示复杂工作流的编排和状态管理。

学习要点:
- 复杂工作流设计
- 状态管理和传递
- 条件分支和错误恢复
- 多阶段任务执行
- 工作流监控和控制
"""

import asyncio
import json
import os

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat, SelectorGroupChat
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


# 工作流状态管理工具
workflow_state = {}


def update_workflow_state(stage: str, status: str, data: str = "") -> str:
    """更新工作流状态"""
    global workflow_state
    workflow_state[stage] = {
        "status": status,
        "data": data,
        "timestamp": "2024-01-01 12:00:00",  # 模拟时间戳
    }
    return f"工作流状态已更新: {stage} -> {status}"


def get_workflow_state(stage: str = "") -> str:
    """获取工作流状态"""
    global workflow_state
    if stage and stage in workflow_state:
        return f"阶段 {stage}: {workflow_state[stage]}"
    return f"完整工作流状态: {json.dumps(workflow_state, ensure_ascii=False, indent=2)}"


def check_approval_status(request_id: str) -> str:
    """模拟审批状态检查"""
    # 模拟不同的审批结果
    if "urgent" in request_id.lower():
        return f"审批请求 {request_id}: 已批准 (紧急流程)"
    if "budget" in request_id.lower():
        return f"审批请求 {request_id}: 需要财务部门二次审核"
    return f"审批请求 {request_id}: 已批准"


def process_data_batch(batch_id: str, operation: str) -> str:
    """模拟数据批处理"""
    operations = {
        "validate": f"数据批次 {batch_id}: 验证完成，发现3个异常记录",
        "transform": f"数据批次 {batch_id}: 转换完成，处理了1000条记录",
        "load": f"数据批次 {batch_id}: 加载完成，成功导入数据库",
    }
    return operations.get(operation, f"数据批次 {batch_id}: 未知操作 {operation}")


async def demo_data_processing_workflow() -> None:
    """演示数据处理工作流"""
    print("\n📊 Data Processing Workflow Demo")
    print("-" * 50)

    # 创建数据处理团队
    workflow_coordinator = AssistantAgent(
        name="WorkflowCoordinator",
        model_client=create_model_client(temperature=0.2),
        tools=[
            FunctionTool(update_workflow_state, description="更新工作流状态"),
            FunctionTool(get_workflow_state, description="获取工作流状态"),
        ],
        system_message="""你是工作流协调员。
        职责：
        - 管理整个数据处理流程
        - 协调各个处理阶段
        - 监控工作流状态
        - 处理异常情况

        数据处理流程：验证 -> 转换 -> 加载
        当所有阶段完成时说"数据处理工作流完成"。""",
    )

    data_validator = AssistantAgent(
        name="DataValidator",
        model_client=create_model_client(temperature=0.3),
        tools=[FunctionTool(process_data_batch, description="处理数据批次")],
        system_message="""你是数据验证专家。
        职责：
        - 验证数据质量和完整性
        - 识别数据异常
        - 生成验证报告

        只在被要求进行数据验证时发言。""",
    )

    data_transformer = AssistantAgent(
        name="DataTransformer",
        model_client=create_model_client(temperature=0.3),
        tools=[FunctionTool(process_data_batch, description="处理数据批次")],
        system_message="""你是数据转换专家。
        职责：
        - 执行数据转换和清洗
        - 应用业务规则
        - 格式标准化

        只在数据验证完成后进行转换工作。""",
    )

    data_loader = AssistantAgent(
        name="DataLoader",
        model_client=create_model_client(temperature=0.3),
        tools=[FunctionTool(process_data_batch, description="处理数据批次")],
        system_message="""你是数据加载专家。
        职责：
        - 将转换后的数据加载到目标系统
        - 确保数据一致性
        - 生成加载报告

        只在数据转换完成后进行加载工作。""",
    )

    # 创建数据处理团队
    termination = TextMentionTermination("数据处理工作流完成")
    data_team = SelectorGroupChat(
        participants=[
            workflow_coordinator,
            data_validator,
            data_transformer,
            data_loader,
        ],
        model_client=create_model_client(temperature=0.2),
        termination_condition=termination,
    )

    # 开始数据处理工作流
    task = "处理批次ID为'batch_001'的客户数据，需要完成验证、转换和加载的完整流程。"
    result = await data_team.run(task=task)

    print("📊 数据处理工作流过程:")
    for i, message in enumerate(result.messages, 1):
        sender = message.source if hasattr(message, "source") else "Unknown"
        content = (
            message.content[:200] + "..."
            if len(message.content) > 200
            else message.content
        )
        print(f"   {i}. {sender}: {content}")


async def demo_approval_workflow() -> None:
    """演示审批工作流"""
    print("\n✅ Approval Workflow Demo")
    print("-" * 50)

    # 创建审批团队
    request_manager = AssistantAgent(
        name="RequestManager",
        model_client=create_model_client(temperature=0.3),
        tools=[
            FunctionTool(update_workflow_state, description="更新工作流状态"),
            FunctionTool(check_approval_status, description="检查审批状态"),
        ],
        system_message="""你是请求管理员。
        职责：
        - 接收和管理审批请求
        - 路由到合适的审批者
        - 跟踪审批状态
        - 处理审批结果

        审批流程：初审 -> 专业审批 -> 最终批准
        当审批完成时说"审批工作流完成"。""",
    )

    initial_reviewer = AssistantAgent(
        name="InitialReviewer",
        model_client=create_model_client(temperature=0.4),
        system_message="""你是初审员。
        职责：
        - 进行初步审查
        - 检查请求的完整性
        - 分类请求类型
        - 决定后续审批路径

        只在被要求进行初审时发言。""",
    )

    specialist_approver = AssistantAgent(
        name="SpecialistApprover",
        model_client=create_model_client(temperature=0.3),
        tools=[FunctionTool(check_approval_status, description="检查审批状态")],
        system_message="""你是专业审批员。
        职责：
        - 进行专业性审查
        - 评估风险和影响
        - 提供专业意见
        - 做出审批决定

        只在初审通过后进行专业审批。""",
    )

    final_approver = AssistantAgent(
        name="FinalApprover",
        model_client=create_model_client(temperature=0.2),
        system_message="""你是最终审批人。
        职责：
        - 最终审批决定
        - 综合考虑各方意见
        - 承担审批责任
        - 发布最终结果

        只在专业审批完成后进行最终审批。""",
    )

    # 创建审批团队
    termination = TextMentionTermination("审批工作流完成")
    approval_team = SelectorGroupChat(
        participants=[
            request_manager,
            initial_reviewer,
            specialist_approver,
            final_approver,
        ],
        model_client=create_model_client(temperature=0.2),
        termination_condition=termination,
    )

    # 开始审批工作流
    task = (
        "处理一个紧急的IT系统升级请求，"
        "请求ID为'urgent_upgrade_001'，需要完整的审批流程。"
    )
    result = await approval_team.run(task=task)

    print("✅ 审批工作流过程:")
    for i, message in enumerate(result.messages, 1):
        sender = message.source if hasattr(message, "source") else "Unknown"
        content = (
            message.content[:200] + "..."
            if len(message.content) > 200
            else message.content
        )
        print(f"   {i}. {sender}: {content}")


async def demo_error_recovery_workflow() -> None:
    """演示错误恢复工作流"""
    print("\n🔧 Error Recovery Workflow Demo")
    print("-" * 50)

    # 创建错误恢复团队
    incident_manager = AssistantAgent(
        name="IncidentManager",
        model_client=create_model_client(temperature=0.3),
        tools=[FunctionTool(update_workflow_state, description="更新工作流状态")],
        system_message="""你是事故管理员。
        职责：
        - 接收和分类事故报告
        - 协调恢复团队
        - 监控恢复进度
        - 确保服务恢复

        恢复流程：评估 -> 诊断 -> 修复 -> 验证
        当系统恢复时说"错误恢复工作流完成"。""",
    )

    system_analyst = AssistantAgent(
        name="SystemAnalyst",
        model_client=create_model_client(temperature=0.4),
        system_message="""你是系统分析师。
        职责：
        - 分析系统错误
        - 识别根本原因
        - 评估影响范围
        - 提供修复建议

        只在被要求进行系统分析时发言。""",
    )

    recovery_engineer = AssistantAgent(
        name="RecoveryEngineer",
        model_client=create_model_client(temperature=0.3),
        system_message="""你是恢复工程师。
        职责：
        - 执行系统修复
        - 实施恢复方案
        - 监控修复过程
        - 确保系统稳定

        只在系统分析完成后执行恢复操作。""",
    )

    qa_tester = AssistantAgent(
        name="QATester",
        model_client=create_model_client(temperature=0.3),
        system_message="""你是质量保证测试员。
        职责：
        - 验证系统修复效果
        - 执行回归测试
        - 确认功能正常
        - 签发恢复确认

        只在修复完成后进行验证测试。""",
    )

    # 创建错误恢复团队
    termination = TextMentionTermination("错误恢复工作流完成")
    recovery_team = SelectorGroupChat(
        participants=[incident_manager, system_analyst, recovery_engineer, qa_tester],
        model_client=create_model_client(temperature=0.2),
        termination_condition=termination,
    )

    # 开始错误恢复工作流
    task = "处理一个关键系统故障：用户登录服务出现间歇性错误，影响50%的用户访问。"
    result = await recovery_team.run(task=task)

    print("🔧 错误恢复工作流过程:")
    for i, message in enumerate(result.messages, 1):
        sender = message.source if hasattr(message, "source") else "Unknown"
        content = (
            message.content[:200] + "..."
            if len(message.content) > 200
            else message.content
        )
        print(f"   {i}. {sender}: {content}")


async def demo_conditional_workflow() -> None:
    """演示条件分支工作流"""
    print("\n🔀 Conditional Workflow Demo")
    print("-" * 50)

    # 创建条件工作流团队
    workflow_controller = AssistantAgent(
        name="WorkflowController",
        model_client=create_model_client(temperature=0.2),
        tools=[FunctionTool(get_workflow_state, description="获取工作流状态")],
        system_message="""你是工作流控制器。
        职责：
        - 根据条件选择执行路径
        - 管理分支逻辑
        - 协调不同处理路径
        - 合并处理结果

        根据请求类型选择处理路径：
        - 紧急请求 -> 快速通道
        - 常规请求 -> 标准流程
        - 复杂请求 -> 专家评估

        当处理完成时说"条件工作流完成"。""",
    )

    express_processor = AssistantAgent(
        name="ExpressProcessor",
        model_client=create_model_client(temperature=0.3),
        system_message="""你是快速处理专员。
        职责：
        - 处理紧急和简单请求
        - 快速响应和解决
        - 简化流程步骤
        - 及时反馈结果

        只处理紧急或简单的请求。""",
    )

    standard_processor = AssistantAgent(
        name="StandardProcessor",
        model_client=create_model_client(temperature=0.3),
        system_message="""你是标准流程处理员。
        职责：
        - 按标准流程处理请求
        - 完整的审查和验证
        - 规范的文档记录
        - 质量控制检查

        处理常规的标准请求。""",
    )

    expert_processor = AssistantAgent(
        name="ExpertProcessor",
        model_client=create_model_client(temperature=0.4),
        system_message="""你是专家处理员。
        职责：
        - 处理复杂和特殊请求
        - 深入分析和评估
        - 定制化解决方案
        - 风险评估和控制

        只处理复杂或需要专业判断的请求。""",
    )

    # 创建条件工作流团队
    termination = TextMentionTermination("条件工作流完成")
    conditional_team = SelectorGroupChat(
        participants=[
            workflow_controller,
            express_processor,
            standard_processor,
            expert_processor,
        ],
        model_client=create_model_client(temperature=0.2),
        termination_condition=termination,
    )

    # 测试不同类型的请求
    requests = [
        "紧急：服务器宕机需要立即重启",
        "常规：员工权限申请需要审批",
        "复杂：新系统架构设计评估",
    ]

    for request in requests:
        print(f"\n🔀 处理请求: {request}")
        result = await conditional_team.run(
            task=f"根据请求类型选择合适的处理路径：{request}",
        )

        # 显示最后几条消息
        for message in result.messages[-2:]:
            sender = message.source if hasattr(message, "source") else "Unknown"
            content = (
                message.content[:150] + "..."
                if len(message.content) > 150
                else message.content
            )
            print(f"   {sender}: {content}")


async def demo_workflow_monitoring() -> None:
    """演示工作流监控"""
    print("\n📈 Workflow Monitoring Demo")
    print("-" * 50)

    # 创建监控团队
    monitor = AssistantAgent(
        name="WorkflowMonitor",
        model_client=create_model_client(temperature=0.2),
        tools=[
            FunctionTool(get_workflow_state, description="获取工作流状态"),
            FunctionTool(update_workflow_state, description="更新工作流状态"),
        ],
        system_message="""你是工作流监控员。
        职责：
        - 监控所有工作流状态
        - 识别瓶颈和异常
        - 生成监控报告
        - 提供优化建议

        监控完成后说"工作流监控完成"。""",
    )

    # 设置一些模拟的工作流状态
    update_workflow_state("数据验证", "完成", "1000条记录验证通过")
    update_workflow_state("数据转换", "进行中", "已处理60%")
    update_workflow_state("审批流程", "等待", "等待专家审批")
    update_workflow_state("系统恢复", "完成", "服务已恢复正常")

    # 运行监控
    termination = TextMentionTermination("工作流监控完成")
    monitor_team = RoundRobinGroupChat([monitor], termination_condition=termination)

    task = "生成当前所有工作流的状态报告，识别需要关注的问题并提供建议。"
    result = await monitor_team.run(task=task)

    print("📈 工作流监控报告:")
    for message in result.messages:
        if hasattr(message, "source") and message.source == "WorkflowMonitor":
            print(f"   {message.content}")


async def main() -> None:
    """主演示函数"""
    print("🔄 AutoGen 工作流编排演示")
    print("=" * 60)

    try:
        await demo_data_processing_workflow()
        await demo_approval_workflow()
        await demo_error_recovery_workflow()
        await demo_conditional_workflow()
        await demo_workflow_monitoring()

        print("\n✨ 所有工作流编排演示完成!")
        print("\n📚 关键要点:")
        print("   • 复杂工作流可以通过智能体协作实现")
        print("   • 状态管理确保工作流的连续性")
        print("   • 条件分支支持灵活的业务逻辑")
        print("   • 错误恢复机制提高系统可靠性")
        print("   • 工作流监控帮助优化性能")
        print("   • SelectorGroupChat适合复杂的协作场景")

        # 清理全局状态
        global workflow_state
        workflow_state.clear()
        print("   • 已清理工作流状态")

    except Exception as e:
        print(f"❌ 演示失败: {e}")
        print("💡 检查API配置和网络连接")


if __name__ == "__main__":
    asyncio.run(main())
