#!/usr/bin/env python3
"""
AutoGen 学习项目 - 高级示例2: 企业级多智能体系统

展示大规模企业级AutoGen系统的架构和实现。

学习要点:
- 企业级系统架构
- 智能体角色分层
- 工作流编排
- 负载均衡
- 状态管理
- 企业集成
"""

import asyncio
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat, SelectorGroupChat
from autogen_core.models import ModelInfo
from autogen_core.tools import FunctionTool
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

load_dotenv()


class Priority(Enum):
    """任务优先级"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(Enum):
    """任务状态"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentRole(Enum):
    """智能体角色"""

    COORDINATOR = "coordinator"
    SPECIALIST = "specialist"
    REVIEWER = "reviewer"
    EXECUTOR = "executor"
    MONITOR = "monitor"


@dataclass
class Task:
    """任务数据类"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    priority: Priority = Priority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    assigned_agents: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    deadline: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status.value,
            "assigned_agents": self.assigned_agents,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "metadata": self.metadata,
        }


class TaskManager:
    """任务管理器"""

    def __init__(self):
        self.tasks: dict[str, Task] = {}
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_task(
        self,
        title: str,
        description: str,
        priority: Priority = Priority.MEDIUM,
        deadline: datetime | None = None,
    ) -> Task:
        """创建任务"""
        task = Task(
            title=title,
            description=description,
            priority=priority,
            deadline=deadline,
        )
        self.tasks[task.id] = task
        self.logger.info(f"创建任务: {task.id} - {title}")
        return task

    def assign_task(self, task_id: str, agent_names: list[str]) -> bool:
        """分配任务"""
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]
        task.assigned_agents = agent_names
        task.status = TaskStatus.IN_PROGRESS
        task.updated_at = datetime.now()

        self.logger.info(f"任务 {task_id} 已分配给: {', '.join(agent_names)}")
        return True

    def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """更新任务状态"""
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]
        old_status = task.status
        task.status = status
        task.updated_at = datetime.now()

        self.logger.info(
            f"任务 {task_id} 状态更新: {old_status.value} -> {status.value}",
        )
        return True

    def get_task(self, task_id: str) -> Task | None:
        """获取任务"""
        return self.tasks.get(task_id)

    def get_tasks_by_priority(self, priority: Priority) -> list[Task]:
        """按优先级获取任务"""
        return [task for task in self.tasks.values() if task.priority == priority]

    def get_pending_tasks(self) -> list[Task]:
        """获取待处理任务"""
        return [
            task for task in self.tasks.values() if task.status == TaskStatus.PENDING
        ]


def create_model_client(temperature: float = 0.3) -> OpenAIChatCompletionClient:
    """创建模型客户端"""
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


class EnterpriseAgentSystem:
    """企业级智能体系统"""

    def __init__(self):
        self.task_manager = TaskManager()
        self.agents: dict[str, AssistantAgent] = {}
        self.agent_roles: dict[str, AgentRole] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self._setup_agents()

    def _setup_agents(self) -> None:
        """设置智能体"""

        # 系统协调员
        self.agents["system_coordinator"] = AssistantAgent(
            name="SystemCoordinator",
            model_client=create_model_client(temperature=0.2),
            tools=[
                FunctionTool(self._create_task, description="创建新任务"),
                FunctionTool(self._assign_task, description="分配任务"),
                FunctionTool(self._get_task_status, description="获取任务状态"),
                FunctionTool(self._update_task_status, description="更新任务状态"),
            ],
            system_message="""你是企业系统协调员。
            职责：
            - 接收和分析业务需求
            - 创建和分配任务
            - 协调各个专业团队
            - 监控项目进度
            - 确保交付质量

            当所有任务完成时说"系统协调完成"。""",
        )
        self.agent_roles["system_coordinator"] = AgentRole.COORDINATOR

        # 业务分析师
        self.agents["business_analyst"] = AssistantAgent(
            name="BusinessAnalyst",
            model_client=create_model_client(temperature=0.4),
            system_message="""你是业务分析师。
            专长：
            - 业务需求分析
            - 流程设计和优化
            - 用户故事编写
            - 业务规则定义
            - ROI分析

            只在被分配业务分析任务时发言。""",
        )
        self.agent_roles["business_analyst"] = AgentRole.SPECIALIST

        # 技术架构师
        self.agents["tech_architect"] = AssistantAgent(
            name="TechArchitect",
            model_client=create_model_client(temperature=0.3),
            system_message="""你是技术架构师。
            专长：
            - 系统架构设计
            - 技术选型
            - 性能优化
            - 安全架构
            - 可扩展性设计

            只在被分配技术架构任务时发言。""",
        )
        self.agent_roles["tech_architect"] = AgentRole.SPECIALIST

        # 项目经理
        self.agents["project_manager"] = AssistantAgent(
            name="ProjectManager",
            model_client=create_model_client(temperature=0.3),
            system_message="""你是项目经理。
            专长：
            - 项目计划制定
            - 资源协调
            - 风险管理
            - 进度跟踪
            - 团队协作

            只在被分配项目管理任务时发言。""",
        )
        self.agent_roles["project_manager"] = AgentRole.EXECUTOR

        # 质量保证
        self.agents["qa_specialist"] = AssistantAgent(
            name="QASpecialist",
            model_client=create_model_client(temperature=0.2),
            system_message="""你是质量保证专家。
            专长：
            - 质量标准制定
            - 测试策略设计
            - 代码审查
            - 质量控制
            - 持续改进

            只在被分配质量保证任务时发言。""",
        )
        self.agent_roles["qa_specialist"] = AgentRole.REVIEWER

        # 系统监控员
        self.agents["system_monitor"] = AssistantAgent(
            name="SystemMonitor",
            model_client=create_model_client(temperature=0.1),
            tools=[
                FunctionTool(self._get_system_metrics, description="获取系统指标"),
                FunctionTool(
                    self._check_agent_health,
                    description="检查智能体健康状态",
                ),
            ],
            system_message="""你是系统监控员。
            职责：
            - 监控系统性能
            - 跟踪智能体状态
            - 检测异常情况
            - 生成监控报告
            - 触发告警机制

            持续监控系统状态并及时报告。""",
        )
        self.agent_roles["system_monitor"] = AgentRole.MONITOR

    def _create_task(
        self,
        title: str,
        description: str,
        priority: str = "medium",
    ) -> str:
        """创建任务工具函数"""
        priority_enum = Priority(priority.lower())
        task = self.task_manager.create_task(title, description, priority_enum)
        return f"任务创建成功: {task.id} - {title}"

    def _assign_task(self, task_id: str, agent_names: str) -> str:
        """分配任务工具函数"""
        agents = [name.strip() for name in agent_names.split(",")]
        success = self.task_manager.assign_task(task_id, agents)
        if success:
            return f"任务 {task_id} 已分配给: {', '.join(agents)}"
        return f"任务分配失败: {task_id}"

    def _get_task_status(self, task_id: str) -> str:
        """获取任务状态工具函数"""
        task = self.task_manager.get_task(task_id)
        if task:
            return json.dumps(task.to_dict(), ensure_ascii=False, indent=2)
        return f"任务不存在: {task_id}"

    def _update_task_status(self, task_id: str, status: str) -> str:
        """更新任务状态工具函数"""
        try:
            status_enum = TaskStatus(status.lower())
            success = self.task_manager.update_task_status(task_id, status_enum)
            if success:
                return f"任务 {task_id} 状态更新为: {status}"
            return f"任务状态更新失败: {task_id}"
        except ValueError:
            return f"无效的状态值: {status}"

    def _get_system_metrics(self) -> str:
        """获取系统指标"""
        import random

        metrics = {
            "active_agents": len(self.agents),
            "pending_tasks": len(self.task_manager.get_pending_tasks()),
            "total_tasks": len(self.task_manager.tasks),
            "system_load": round(random.uniform(0.1, 0.8), 2),
            "memory_usage": round(random.uniform(30, 70), 1),
            "response_time": round(random.uniform(100, 300), 1),
            "timestamp": datetime.now().isoformat(),
        }
        return json.dumps(metrics, ensure_ascii=False, indent=2)

    def _check_agent_health(self) -> str:
        """检查智能体健康状态"""
        import random

        health_status = {}
        for agent_name in self.agents:
            health_status[agent_name] = {
                "status": "healthy" if random.random() > 0.1 else "warning",
                "last_active": datetime.now().isoformat(),
                "role": self.agent_roles[agent_name].value,
            }

        return json.dumps(health_status, ensure_ascii=False, indent=2)

    async def process_enterprise_request(self, request: str) -> None:
        """处理企业级请求"""
        print(f"\n🏢 处理企业请求: {request}")
        print("-" * 60)

        # 创建企业团队
        enterprise_team = SelectorGroupChat(
            participants=list(self.agents.values()),
            model_client=create_model_client(temperature=0.2),
            termination_condition=TextMentionTermination("系统协调完成"),
        )

        # 执行请求处理
        result = await enterprise_team.run(task=request)

        print("🏢 企业请求处理过程:")
        for i, message in enumerate(result.messages, 1):
            sender = message.source if hasattr(message, "source") else "Unknown"
            content = (
                message.content[:150] + "..."
                if len(message.content) > 150
                else message.content
            )
            print(f"   {i}. {sender}: {content}")

        return result


async def demo_enterprise_system_setup() -> None:
    """演示企业系统设置"""
    print("\n🏢 Enterprise System Setup Demo")
    print("-" * 50)

    system = EnterpriseAgentSystem()

    print("✅ 企业智能体系统初始化完成")
    print(f"   智能体数量: {len(system.agents)}")

    for name, agent in system.agents.items():
        role = system.agent_roles[name].value
        print(f"   - {agent.name} ({role})")

    # 显示系统指标
    metrics = system._get_system_metrics()
    print("\n📊 系统指标:")
    print(f"   {metrics}")


async def demo_task_management() -> None:
    """演示任务管理"""
    print("\n📋 Task Management Demo")
    print("-" * 50)

    system = EnterpriseAgentSystem()

    # 创建示例任务
    tasks_data = [
        ("客户关系系统升级", "升级现有CRM系统，增加AI智能推荐功能", Priority.HIGH),
        ("数据安全审计", "对企业数据安全进行全面审计和评估", Priority.CRITICAL),
        ("员工培训平台", "开发在线员工培训和认证平台", Priority.MEDIUM),
        ("移动应用开发", "开发企业移动办公应用", Priority.MEDIUM),
    ]

    created_tasks = []
    for title, desc, priority in tasks_data:
        task = system.task_manager.create_task(title, desc, priority)
        created_tasks.append(task)
        print(f"✅ 创建任务: {task.title} (优先级: {priority.value})")

    # 任务分配演示
    assignments = [
        (created_tasks[0].id, ["business_analyst", "tech_architect"]),
        (created_tasks[1].id, ["qa_specialist", "tech_architect"]),
        (created_tasks[2].id, ["business_analyst", "project_manager"]),
        (created_tasks[3].id, ["tech_architect", "project_manager"]),
    ]

    print("\n📋 任务分配:")
    for task_id, agents in assignments:
        system.task_manager.assign_task(task_id, agents)
        task = system.task_manager.get_task(task_id)
        print(f"   {task.title} -> {', '.join(agents)}")

    # 显示任务统计
    pending = len(system.task_manager.get_pending_tasks())
    high_priority = len(system.task_manager.get_tasks_by_priority(Priority.HIGH))
    critical = len(system.task_manager.get_tasks_by_priority(Priority.CRITICAL))

    print("\n📊 任务统计:")
    print(f"   总任务数: {len(system.task_manager.tasks)}")
    print(f"   待处理: {pending}")
    print(f"   高优先级: {high_priority}")
    print(f"   关键任务: {critical}")


async def demo_enterprise_workflow() -> None:
    """演示企业工作流"""
    print("\n🔄 Enterprise Workflow Demo")
    print("-" * 50)

    system = EnterpriseAgentSystem()

    # 企业级请求示例
    enterprise_requests = [
        "我们需要开发一个新的客户服务平台，集成AI聊天机器人、工单系统和知识库。请制定完整的项目计划。",
        "公司计划进行数字化转型，需要评估现有系统架构并提出改进建议。",
        "我们需要建立企业级数据分析平台，支持实时数据处理和可视化报表。",
    ]

    for i, request in enumerate(enterprise_requests, 1):
        print(f"\n🎯 企业请求 {i}:")
        await system.process_enterprise_request(request)


async def demo_system_monitoring() -> None:
    """演示系统监控"""
    print("\n📊 System Monitoring Demo")
    print("-" * 50)

    system = EnterpriseAgentSystem()

    # 创建监控团队
    monitor_team = RoundRobinGroupChat(
        [system.agents["system_monitor"]],
        termination_condition=MaxMessageTermination(3),
    )

    # 执行系统监控
    result = await monitor_team.run(
        task="执行系统健康检查，获取性能指标，并生成监控报告。",
    )

    print("📊 系统监控报告:")
    for message in result.messages:
        if hasattr(message, "source") and message.source == "SystemMonitor":
            print(f"   {message.content}")


async def demo_load_balancing() -> None:
    """演示负载均衡"""
    print("\n⚖️ Load Balancing Demo")
    print("-" * 50)

    system = EnterpriseAgentSystem()

    # 模拟多个并发请求
    concurrent_requests = [
        "分析市场竞争态势",
        "设计微服务架构",
        "制定项目时间表",
        "评估技术风险",
        "优化系统性能",
    ]

    print("🔄 处理并发请求:")

    # 创建多个专业团队
    teams = {
        "business_team": [system.agents["business_analyst"]],
        "tech_team": [system.agents["tech_architect"]],
        "project_team": [system.agents["project_manager"]],
        "qa_team": [system.agents["qa_specialist"]],
    }

    # 分配请求到不同团队
    team_assignments = [
        ("business_team", concurrent_requests[0]),
        ("tech_team", concurrent_requests[1]),
        ("project_team", concurrent_requests[2]),
        ("tech_team", concurrent_requests[3]),
        ("qa_team", concurrent_requests[4]),
    ]

    # 并发处理请求
    tasks = []
    for team_name, request in team_assignments:
        team = RoundRobinGroupChat(
            teams[team_name],
            termination_condition=MaxMessageTermination(2),
        )
        task = team.run(task=request)
        tasks.append((team_name, request, task))

    # 等待所有任务完成
    for team_name, request, task in tasks:
        result = await task
        print(f"   ✅ {team_name}: {request}")
        if result.messages:
            content = result.messages[-1].content[:100] + "..."
            print(f"      结果: {content}")


async def main() -> None:
    """主演示函数"""
    print("🏢 AutoGen 企业级多智能体系统演示")
    print("=" * 60)

    try:
        await demo_enterprise_system_setup()
        await demo_task_management()
        await demo_enterprise_workflow()
        await demo_system_monitoring()
        await demo_load_balancing()

        print("\n✨ 所有企业级系统演示完成!")
        print("\n📚 关键要点:")
        print("   • 分层智能体架构支持复杂企业需求")
        print("   • 任务管理系统确保工作流有序进行")
        print("   • 角色专业化提高处理效率")
        print("   • 系统监控保障服务质量")
        print("   • 负载均衡支持高并发处理")
        print("   • 企业级工作流满足业务需求")

    except Exception as e:
        print(f"❌ 演示失败: {e}")
        print("💡 检查API配置和网络连接")


if __name__ == "__main__":
    asyncio.run(main())
