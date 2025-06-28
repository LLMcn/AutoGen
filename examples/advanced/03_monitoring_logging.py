#!/usr/bin/env python3
"""
AutoGen 学习项目 - 高级示例3: 监控和日志系统

展示生产级AutoGen系统的监控和日志最佳实践。

学习要点:
- 结构化日志记录
- 性能监控
- 错误追踪
- 指标收集
- 告警机制
- 日志分析
"""

import asyncio
import json
import logging
import os
import time
import traceback
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from autogen_agentchat.agents import AssistantAgent
from autogen_core.models import ModelInfo
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

load_dotenv()


class LogLevel(Enum):
    """日志级别"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class MetricType(Enum):
    """指标类型"""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class LogEntry:
    """日志条目"""

    timestamp: datetime
    level: LogLevel
    logger_name: str
    message: str
    agent_name: str | None = None
    task_id: str | None = None
    user_id: str | None = None
    session_id: str | None = None
    extra_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "logger_name": self.logger_name,
            "message": self.message,
            "agent_name": self.agent_name,
            "task_id": self.task_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "extra_data": self.extra_data,
        }


@dataclass
class Metric:
    """指标数据"""

    name: str
    type: MetricType
    value: float
    timestamp: datetime
    tags: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "type": self.type.value,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
        }


class StructuredLogger:
    """结构化日志记录器"""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(name)
        self.log_entries: list[LogEntry] = []
        self._setup_logger()

    def _setup_logger(self) -> None:
        """设置日志记录器"""
        # 创建自定义格式化器
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # 文件处理器
        file_handler = logging.FileHandler("autogen_system.log")
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        self.logger.setLevel(logging.INFO)

    def log(
        self,
        level: LogLevel,
        message: str,
        agent_name: str | None = None,
        task_id: str | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
        **extra_data,
    ) -> None:
        """记录结构化日志"""

        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            logger_name=self.name,
            message=message,
            agent_name=agent_name,
            task_id=task_id,
            user_id=user_id,
            session_id=session_id,
            extra_data=extra_data,
        )

        self.log_entries.append(entry)

        # 记录到标准日志系统
        log_method = getattr(self.logger, level.value.lower())
        log_method(f"[{agent_name or 'SYSTEM'}] {message}")

    def info(self, message: str, **kwargs) -> None:
        """记录信息日志"""
        self.log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """记录警告日志"""
        self.log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """记录错误日志"""
        self.log(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """记录严重错误日志"""
        self.log(LogLevel.CRITICAL, message, **kwargs)

    def get_logs(
        self,
        level: LogLevel | None = None,
        agent_name: str | None = None,
        since: datetime | None = None,
    ) -> list[LogEntry]:
        """获取过滤后的日志"""
        logs = self.log_entries

        if level:
            logs = [log for log in logs if log.level == level]

        if agent_name:
            logs = [log for log in logs if log.agent_name == agent_name]

        if since:
            logs = [log for log in logs if log.timestamp >= since]

        return logs


class MetricsCollector:
    """指标收集器"""

    def __init__(self):
        self.metrics: list[Metric] = []
        self.counters: dict[str, float] = {}
        self.gauges: dict[str, float] = {}
        self.timers: dict[str, list[float]] = {}

    def counter(self, name: str, value: float = 1.0, **tags) -> None:
        """计数器指标"""
        self.counters[name] = self.counters.get(name, 0) + value

        metric = Metric(
            name=name,
            type=MetricType.COUNTER,
            value=self.counters[name],
            timestamp=datetime.now(),
            tags=tags,
        )
        self.metrics.append(metric)

    def gauge(self, name: str, value: float, **tags) -> None:
        """仪表盘指标"""
        self.gauges[name] = value

        metric = Metric(
            name=name,
            type=MetricType.GAUGE,
            value=value,
            timestamp=datetime.now(),
            tags=tags,
        )
        self.metrics.append(metric)

    def timer(self, name: str, value: float, **tags) -> None:
        """计时器指标"""
        if name not in self.timers:
            self.timers[name] = []
        self.timers[name].append(value)

        metric = Metric(
            name=name,
            type=MetricType.TIMER,
            value=value,
            timestamp=datetime.now(),
            tags=tags,
        )
        self.metrics.append(metric)

    @asynccontextmanager
    async def time_operation(self, name: str, **tags):
        """计时上下文管理器"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.timer(name, duration, **tags)

    def get_metrics(
        self,
        metric_type: MetricType | None = None,
        since: datetime | None = None,
    ) -> list[Metric]:
        """获取指标"""
        metrics = self.metrics

        if metric_type:
            metrics = [m for m in metrics if m.type == metric_type]

        if since:
            metrics = [m for m in metrics if m.timestamp >= since]

        return metrics

    def get_summary(self) -> dict[str, Any]:
        """获取指标摘要"""
        return {
            "total_metrics": len(self.metrics),
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "timer_stats": {
                name: {
                    "count": len(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                }
                for name, values in self.timers.items()
            },
        }


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self, logger: StructuredLogger, metrics: MetricsCollector):
        self.logger = logger
        self.metrics = metrics
        self.agent_stats: dict[str, dict[str, Any]] = {}

    def track_agent_performance(
        self,
        agent_name: str,
        operation: str,
        duration: float,
        success: bool = True,
    ) -> None:
        """跟踪智能体性能"""

        # 更新统计信息
        if agent_name not in self.agent_stats:
            self.agent_stats[agent_name] = {
                "total_operations": 0,
                "successful_operations": 0,
                "failed_operations": 0,
                "total_duration": 0.0,
                "avg_duration": 0.0,
                "operations": {},
            }

        stats = self.agent_stats[agent_name]
        stats["total_operations"] += 1
        stats["total_duration"] += duration
        stats["avg_duration"] = stats["total_duration"] / stats["total_operations"]

        if success:
            stats["successful_operations"] += 1
        else:
            stats["failed_operations"] += 1

        # 记录操作统计
        if operation not in stats["operations"]:
            stats["operations"][operation] = {"count": 0, "total_time": 0.0}

        stats["operations"][operation]["count"] += 1
        stats["operations"][operation]["total_time"] += duration

        # 记录指标
        self.metrics.timer(f"agent.{operation}.duration", duration, agent=agent_name)
        self.metrics.counter(
            f"agent.{operation}.count",
            1.0,
            agent=agent_name,
            success=str(success),
        )

        # 记录日志
        self.logger.info(
            f"智能体操作完成: {operation}",
            agent_name=agent_name,
            duration=duration,
            success=success,
        )

    def get_agent_stats(self, agent_name: str | None = None) -> dict[str, Any]:
        """获取智能体统计信息"""
        if agent_name:
            return self.agent_stats.get(agent_name, {})
        return self.agent_stats


class AlertManager:
    """告警管理器"""

    def __init__(self, logger: StructuredLogger, metrics: MetricsCollector):
        self.logger = logger
        self.metrics = metrics
        self.alert_rules: list[dict[str, Any]] = []
        self.active_alerts: list[dict[str, Any]] = []

    def add_rule(
        self,
        name: str,
        condition: Callable[[dict[str, Any]], bool],
        message: str,
        severity: str = "warning",
    ) -> None:
        """添加告警规则"""
        rule = {
            "name": name,
            "condition": condition,
            "message": message,
            "severity": severity,
            "enabled": True,
        }
        self.alert_rules.append(rule)
        self.logger.info(f"添加告警规则: {name}")

    def check_alerts(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        """检查告警条件"""
        triggered_alerts = []

        for rule in self.alert_rules:
            if not rule["enabled"]:
                continue

            try:
                if rule["condition"](context):
                    alert = {
                        "rule_name": rule["name"],
                        "message": rule["message"],
                        "severity": rule["severity"],
                        "timestamp": datetime.now(),
                        "context": context,
                    }
                    triggered_alerts.append(alert)
                    self.active_alerts.append(alert)

                    # 记录告警日志
                    self.logger.warning(
                        f"触发告警: {rule['name']} - {rule['message']}",
                        alert_rule=rule["name"],
                        severity=rule["severity"],
                    )

                    # 记录告警指标
                    self.metrics.counter(
                        "alerts.triggered",
                        1.0,
                        rule=rule["name"],
                        severity=rule["severity"],
                    )

            except Exception as e:
                self.logger.exception(f"告警规则检查失败: {rule['name']} - {e}")

        return triggered_alerts


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


class MonitoredAgent:
    """带监控的智能体包装器"""

    def __init__(
        self,
        agent: AssistantAgent,
        logger: StructuredLogger,
        metrics: MetricsCollector,
        monitor: PerformanceMonitor,
    ):
        self.agent = agent
        self.logger = logger
        self.metrics = metrics
        self.monitor = monitor

    async def run_with_monitoring(self, task: str, **kwargs) -> Any:
        """带监控的运行方法"""
        start_time = time.time()
        success = True
        error_message = None

        try:
            self.logger.info(
                f"开始执行任务: {task[:100]}...",
                agent_name=self.agent.name,
                task_id=kwargs.get("task_id"),
            )

            # 记录任务开始指标
            self.metrics.counter("agent.tasks.started", 1.0, agent=self.agent.name)

            # 执行任务（这里是模拟，实际应该调用agent的方法）
            await asyncio.sleep(0.1)  # 模拟处理时间
            result = f"任务完成: {task}"

            self.logger.info(
                "任务执行成功",
                agent_name=self.agent.name,
                task_id=kwargs.get("task_id"),
            )

            return result

        except Exception as e:
            success = False
            error_message = str(e)

            self.logger.exception(
                f"任务执行失败: {error_message}",
                agent_name=self.agent.name,
                task_id=kwargs.get("task_id"),
                error=error_message,
                traceback=traceback.format_exc(),
            )

            # 记录错误指标
            self.metrics.counter(
                "agent.errors",
                1.0,
                agent=self.agent.name,
                error_type=type(e).__name__,
            )

            raise

        finally:
            duration = time.time() - start_time

            # 记录性能数据
            self.monitor.track_agent_performance(
                self.agent.name,
                "task_execution",
                duration,
                success,
            )

            # 记录完成指标
            self.metrics.counter(
                "agent.tasks.completed",
                1.0,
                agent=self.agent.name,
                success=str(success),
            )


async def demo_structured_logging() -> None:
    """演示结构化日志"""
    print("\n📝 Structured Logging Demo")
    print("-" * 50)

    logger = StructuredLogger("AutoGenSystem")

    # 记录不同类型的日志
    logger.info("系统启动", agent_name="SystemManager", user_id="admin")
    logger.warning("高CPU使用率", agent_name="MonitorAgent", cpu_usage=85.5)
    logger.error(
        "API调用失败",
        agent_name="DataAgent",
        api_endpoint="/api/data",
        status_code=500,
    )

    # 获取日志统计
    all_logs = logger.get_logs()
    error_logs = logger.get_logs(level=LogLevel.ERROR)
    recent_logs = logger.get_logs(since=datetime.now() - timedelta(minutes=1))

    print("📊 日志统计:")
    print(f"   总日志数: {len(all_logs)}")
    print(f"   错误日志数: {len(error_logs)}")
    print(f"   最近1分钟日志: {len(recent_logs)}")

    # 显示最近的日志
    print("\n📋 最近日志:")
    for log in recent_logs[-3:]:
        print(f"   [{log.level.value}] {log.agent_name}: {log.message}")


async def demo_metrics_collection() -> None:
    """演示指标收集"""
    print("\n📊 Metrics Collection Demo")
    print("-" * 50)

    metrics = MetricsCollector()

    # 模拟各种指标
    for i in range(10):
        metrics.counter("requests.total", 1.0, endpoint="/api/chat")
        metrics.gauge("memory.usage", 60.5 + i, unit="percent")

        # 模拟API响应时间
        import random

        response_time = random.uniform(0.1, 0.5)
        metrics.timer("api.response_time", response_time, endpoint="/api/chat")

    # 模拟错误
    metrics.counter("errors.total", 1.0, type="timeout")
    metrics.counter("errors.total", 2.0, type="validation")

    # 获取指标摘要
    summary = metrics.get_summary()

    print("📊 指标摘要:")
    print(f"   总指标数: {summary['total_metrics']}")
    print(f"   计数器: {json.dumps(summary['counters'], indent=2)}")
    print(f"   仪表盘: {json.dumps(summary['gauges'], indent=2)}")
    print(f"   计时器统计: {json.dumps(summary['timer_stats'], indent=2)}")


async def demo_performance_monitoring() -> None:
    """演示性能监控"""
    print("\n⚡ Performance Monitoring Demo")
    print("-" * 50)

    logger = StructuredLogger("PerformanceTest")
    metrics = MetricsCollector()
    monitor = PerformanceMonitor(logger, metrics)

    # 创建监控的智能体
    base_agent = AssistantAgent(
        name="TestAgent",
        model_client=create_model_client(),
        system_message="你是测试智能体。",
    )

    monitored_agent = MonitoredAgent(base_agent, logger, metrics, monitor)

    # 模拟多个任务执行
    tasks = [
        "分析用户行为数据",
        "生成报告摘要",
        "处理客户请求",
        "优化系统配置",
        "执行数据备份",
    ]

    print("🔄 执行监控任务:")
    for i, task in enumerate(tasks):
        try:
            async with metrics.time_operation("task_execution", task_type="analysis"):
                await monitored_agent.run_with_monitoring(
                    task,
                    task_id=f"task_{i+1}",
                )
            print(f"   ✅ 任务 {i+1}: {task}")
        except Exception as e:
            print(f"   ❌ 任务 {i+1} 失败: {e}")

    # 显示性能统计
    stats = monitor.get_agent_stats("TestAgent")
    print("\n📊 智能体性能统计:")
    print(f"   总操作数: {stats.get('total_operations', 0)}")
    print(f"   成功操作: {stats.get('successful_operations', 0)}")
    print(f"   失败操作: {stats.get('failed_operations', 0)}")
    print(f"   平均耗时: {stats.get('avg_duration', 0):.3f}秒")


async def demo_alerting_system() -> None:
    """演示告警系统"""
    print("\n🚨 Alerting System Demo")
    print("-" * 50)

    logger = StructuredLogger("AlertSystem")
    metrics = MetricsCollector()
    alert_manager = AlertManager(logger, metrics)

    # 定义告警规则
    def high_error_rate(context: dict[str, Any]) -> bool:
        return context.get("error_rate", 0) > 5.0

    def high_response_time(context: dict[str, Any]) -> bool:
        return context.get("avg_response_time", 0) > 1.0

    def low_success_rate(context: dict[str, Any]) -> bool:
        return context.get("success_rate", 100) < 95.0

    # 添加告警规则
    alert_manager.add_rule(
        "high_error_rate",
        high_error_rate,
        "错误率过高，需要立即检查",
        "critical",
    )

    alert_manager.add_rule(
        "high_response_time",
        high_response_time,
        "响应时间过长，可能影响用户体验",
        "warning",
    )

    alert_manager.add_rule(
        "low_success_rate",
        low_success_rate,
        "成功率偏低，系统可能存在问题",
        "warning",
    )

    # 模拟不同的系统状态
    test_contexts = [
        {"error_rate": 2.0, "avg_response_time": 0.3, "success_rate": 98.5},
        {
            "error_rate": 8.0,  # 触发高错误率告警
            "avg_response_time": 0.5,
            "success_rate": 92.0,  # 触发低成功率告警
        },
        {
            "error_rate": 1.0,
            "avg_response_time": 1.5,  # 触发高响应时间告警
            "success_rate": 99.0,
        },
    ]

    print("🔍 检查告警条件:")
    for i, context in enumerate(test_contexts, 1):
        print(f"\n   测试场景 {i}: {context}")
        alerts = alert_manager.check_alerts(context)

        if alerts:
            for alert in alerts:
                print(f"   🚨 告警: {alert['message']} (严重性: {alert['severity']})")
        else:
            print("   ✅ 无告警触发")

    print("\n📊 告警统计:")
    print(f"   活跃告警数: {len(alert_manager.active_alerts)}")
    print(f"   告警规则数: {len(alert_manager.alert_rules)}")


async def demo_log_analysis() -> None:
    """演示日志分析"""
    print("\n🔍 Log Analysis Demo")
    print("-" * 50)

    logger = StructuredLogger("LogAnalysis")

    # 生成模拟日志数据
    agents = ["DataProcessor", "APIGateway", "UserManager", "ReportGenerator"]
    operations = ["process_data", "handle_request", "authenticate", "generate_report"]

    import random

    for _ in range(50):
        agent = random.choice(agents)
        operation = random.choice(operations)
        success = random.random() > 0.1  # 90% 成功率

        if success:
            logger.info(
                f"操作成功: {operation}",
                agent_name=agent,
                operation=operation,
                duration=random.uniform(0.1, 2.0),
            )
        else:
            logger.error(
                f"操作失败: {operation}",
                agent_name=agent,
                operation=operation,
                error_code=random.choice(
                    ["TIMEOUT", "VALIDATION_ERROR", "NETWORK_ERROR"],
                ),
            )

    # 分析日志
    all_logs = logger.get_logs()
    error_logs = logger.get_logs(level=LogLevel.ERROR)

    # 按智能体统计
    agent_stats = {}
    for log in all_logs:
        if log.agent_name:
            if log.agent_name not in agent_stats:
                agent_stats[log.agent_name] = {"total": 0, "errors": 0}
            agent_stats[log.agent_name]["total"] += 1
            if log.level == LogLevel.ERROR:
                agent_stats[log.agent_name]["errors"] += 1

    # 按错误类型统计
    error_types = {}
    for log in error_logs:
        error_code = log.extra_data.get("error_code", "UNKNOWN")
        error_types[error_code] = error_types.get(error_code, 0) + 1

    print("📊 日志分析结果:")
    print(f"   总日志数: {len(all_logs)}")
    print(f"   错误日志数: {len(error_logs)}")
    print(f"   错误率: {len(error_logs)/len(all_logs)*100:.1f}%")

    print("\n📋 智能体统计:")
    for agent, stats in agent_stats.items():
        error_rate = stats["errors"] / stats["total"] * 100
        print(
            f"   {agent}: {stats['total']} 操作, "
            f"{stats['errors']} 错误 ({error_rate:.1f}%)",
        )

    print("\n🚨 错误类型分布:")
    for error_type, count in error_types.items():
        print(f"   {error_type}: {count} 次")


async def main() -> None:
    """主演示函数"""
    print("📊 AutoGen 监控和日志系统演示")
    print("=" * 60)

    try:
        await demo_structured_logging()
        await demo_metrics_collection()
        await demo_performance_monitoring()
        await demo_alerting_system()
        await demo_log_analysis()

        print("\n✨ 所有监控和日志演示完成!")
        print("\n📚 关键要点:")
        print("   • 结构化日志提供丰富的上下文信息")
        print("   • 指标收集支持性能监控和分析")
        print("   • 性能监控帮助识别瓶颈和优化点")
        print("   • 告警系统确保及时响应问题")
        print("   • 日志分析提供系统健康洞察")
        print("   • 监控数据支持运维决策")

        # 清理日志文件
        try:
            if os.path.exists("autogen_system.log"):
                os.remove("autogen_system.log")
                print("   🧹 已清理日志文件")
        except OSError:
            pass

    except Exception as e:
        print(f"❌ 演示失败: {e}")
        print("💡 检查API配置和网络连接")


if __name__ == "__main__":
    asyncio.run(main())
