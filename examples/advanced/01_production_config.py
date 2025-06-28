#!/usr/bin/env python3
"""
AutoGen 学习项目 - 高级示例1: 生产级配置管理

展示企业级AutoGen系统的配置管理最佳实践。

学习要点:
- 环境配置管理
- 安全的API密钥管理
- 模型配置和切换
- 日志配置
- 性能监控配置
- 错误处理配置
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_core.models import ModelInfo
from autogen_core.tools import FunctionTool
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Environment(Enum):
    """环境类型枚举"""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(Enum):
    """日志级别枚举"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class ModelConfig:
    """模型配置类"""

    name: str
    provider: str
    api_key_env: str
    base_url: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4000
    timeout: int = 30
    retry_count: int = 3


class ConfigurationError(Exception):
    """配置错误异常"""


@dataclass
class ProductionConfig:
    """生产级配置管理类"""

    # 环境配置
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = True

    # API配置
    api_configs: dict[str, ModelConfig] = field(default_factory=dict)
    default_model: str = "deepseek"

    # 日志配置
    log_level: LogLevel = LogLevel.INFO
    log_file: str | None = None
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 性能配置
    max_concurrent_requests: int = 10
    request_timeout: int = 30
    cache_enabled: bool = True
    cache_ttl: int = 3600

    # 安全配置
    enable_rate_limiting: bool = True
    max_requests_per_minute: int = 60
    enable_audit_logging: bool = True

    # 监控配置
    enable_metrics: bool = True
    metrics_port: int = 8080
    health_check_interval: int = 30

    def __post_init__(self):
        """初始化后的配置验证和设置"""
        self._setup_logging()
        self._load_model_configs()
        self._validate_config()

    def _setup_logging(self) -> None:
        """设置日志配置"""
        logging.basicConfig(
            level=getattr(logging, self.log_level.value),
            format=self.log_format,
            filename=self.log_file,
        )

        # 为生产环境添加额外的日志处理器
        if self.environment == Environment.PRODUCTION:
            # 添加文件轮转处理器
            from logging.handlers import RotatingFileHandler

            handler = RotatingFileHandler(
                self.log_file or "autogen_production.log",
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
            )
            handler.setFormatter(logging.Formatter(self.log_format))
            logging.getLogger().addHandler(handler)

    def _load_model_configs(self) -> None:
        """加载模型配置"""
        # DeepSeek配置
        self.api_configs["deepseek"] = ModelConfig(
            name="deepseek-chat",
            provider="deepseek",
            api_key_env="OPENAI_API_KEY",
            base_url="https://api.deepseek.com/v1",
            temperature=0.7,
            max_tokens=4000,
        )

        # OpenAI配置（备用）
        self.api_configs["openai"] = ModelConfig(
            name="gpt-4",
            provider="openai",
            api_key_env="OPENAI_API_KEY_BACKUP",
            base_url="https://api.openai.com/v1",
            temperature=0.7,
            max_tokens=4000,
        )

        # 本地模型配置（开发环境）
        if self.environment == Environment.DEVELOPMENT:
            self.api_configs["local"] = ModelConfig(
                name="llama2",
                provider="local",
                api_key_env="LOCAL_API_KEY",
                base_url="http://localhost:8000/v1",
                temperature=0.8,
                max_tokens=2000,
            )

    def _validate_config(self) -> None:
        """验证配置的有效性"""
        # 验证默认模型是否存在
        if self.default_model not in self.api_configs:
            raise ConfigurationError(f"默认模型 '{self.default_model}' 未在配置中找到")

        # 验证API密钥
        default_config = self.api_configs[self.default_model]
        api_key = os.getenv(default_config.api_key_env)
        if not api_key:
            raise ConfigurationError(
                f"API密钥环境变量 '{default_config.api_key_env}' 未设置",
            )

        # 生产环境额外验证
        if self.environment == Environment.PRODUCTION:
            if self.debug:
                logging.warning("生产环境中启用了调试模式")
            # 为生产环境自动设置日志文件（如果未设置）
            if not self.log_file:
                self.log_file = "autogen_production.log"

    def get_model_client(
        self,
        model_name: str | None = None,
    ) -> OpenAIChatCompletionClient:
        """获取模型客户端"""
        model_name = model_name or self.default_model

        if model_name not in self.api_configs:
            raise ConfigurationError(f"模型 '{model_name}' 未配置")

        config = self.api_configs[model_name]
        api_key = os.getenv(config.api_key_env)

        if not api_key:
            raise ConfigurationError(f"API密钥环境变量 '{config.api_key_env}' 未设置")

        return OpenAIChatCompletionClient(
            model=config.name,
            api_key=api_key,
            base_url=config.base_url,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            model_info=ModelInfo(
                family="openai",
                vision=False,
                function_calling=True,
                json_output=True,
                structured_output=False,
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "environment": self.environment.value,
            "debug": self.debug,
            "default_model": self.default_model,
            "log_level": self.log_level.value,
            "max_concurrent_requests": self.max_concurrent_requests,
            "cache_enabled": self.cache_enabled,
            "enable_rate_limiting": self.enable_rate_limiting,
            "enable_metrics": self.enable_metrics,
        }

    @classmethod
    def from_file(cls, config_file: str) -> "ProductionConfig":
        """从配置文件加载"""
        if not Path(config_file).exists():
            raise ConfigurationError(f"配置文件 '{config_file}' 不存在")

        with open(config_file, encoding="utf-8") as f:
            config_data = json.load(f)

        return cls(**config_data)

    def save_to_file(self, config_file: str) -> None:
        """保存配置到文件"""
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)


class ProductionAgentFactory:
    """生产级智能体工厂"""

    def __init__(self, config: ProductionConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_agent(
        self,
        name: str,
        system_message: str,
        model_name: str | None = None,
        tools: list | None = None,
    ) -> AssistantAgent:
        """创建智能体"""
        try:
            model_client = self.config.get_model_client(model_name)

            agent = AssistantAgent(
                name=name,
                model_client=model_client,
                system_message=system_message,
                tools=tools or [],
            )

            self.logger.info(f"成功创建智能体: {name}")
            return agent

        except Exception as e:
            self.logger.exception(f"创建智能体失败: {name}, 错误: {e}")
            raise

    def create_monitoring_agent(self) -> AssistantAgent:
        """创建监控智能体"""
        return self.create_agent(
            name="MonitoringAgent",
            system_message="""你是系统监控智能体。
            职责：
            - 监控系统性能和健康状态
            - 检测异常和错误
            - 生成监控报告
            - 触发告警机制

            始终以JSON格式返回监控数据。""",
            tools=[
                FunctionTool(self._get_system_metrics, description="获取系统指标"),
                FunctionTool(self._check_health, description="检查系统健康状态"),
            ],
        )

    def _get_system_metrics(self) -> str:
        """获取系统指标（模拟）"""
        import random

        metrics = {
            "cpu_usage": round(random.uniform(10, 80), 2),
            "memory_usage": round(random.uniform(30, 90), 2),
            "request_count": random.randint(100, 1000),
            "error_rate": round(random.uniform(0, 5), 2),
            "response_time": round(random.uniform(100, 500), 2),
        }
        return json.dumps(metrics, ensure_ascii=False)

    def _check_health(self) -> str:
        """检查系统健康状态（模拟）"""
        import random

        health_status = {
            "status": "healthy" if random.random() > 0.1 else "warning",
            "services": {
                "api_gateway": "up",
                "database": "up",
                "cache": "up" if random.random() > 0.05 else "down",
                "message_queue": "up",
            },
            "timestamp": "2024-01-01T12:00:00Z",
        }
        return json.dumps(health_status, ensure_ascii=False)


async def demo_production_config() -> None:
    """演示生产级配置管理"""
    print("\n🏭 Production Configuration Demo")
    print("-" * 50)

    # 创建不同环境的配置
    configs = {
        "development": ProductionConfig(
            environment=Environment.DEVELOPMENT,
            debug=True,
            log_level=LogLevel.DEBUG,
            max_concurrent_requests=5,
        ),
        "staging": ProductionConfig(
            environment=Environment.STAGING,
            debug=False,
            log_level=LogLevel.INFO,
            max_concurrent_requests=20,
            log_file="staging.log",
        ),
        "production": ProductionConfig(
            environment=Environment.PRODUCTION,
            debug=False,
            log_level=LogLevel.WARNING,
            max_concurrent_requests=50,
            log_file="production.log",
            cache_enabled=True,
            enable_rate_limiting=True,
        ),
    }

    for env_name, config in configs.items():
        print(f"\n📋 {env_name.upper()} 环境配置:")
        print(f"   环境: {config.environment.value}")
        print(f"   调试模式: {config.debug}")
        print(f"   日志级别: {config.log_level.value}")
        print(f"   最大并发: {config.max_concurrent_requests}")
        print(f"   缓存启用: {config.cache_enabled}")
        print(f"   速率限制: {config.enable_rate_limiting}")

        # 保存配置到文件
        config_file = f"config_{env_name}.json"
        config.save_to_file(config_file)
        print(f"   配置已保存到: {config_file}")


async def demo_agent_factory() -> None:
    """演示智能体工厂"""
    print("\n🏭 Agent Factory Demo")
    print("-" * 50)

    # 使用开发环境配置
    config = ProductionConfig(environment=Environment.DEVELOPMENT, debug=True)

    factory = ProductionAgentFactory(config)

    # 创建不同类型的智能体
    agents = []

    # 业务智能体
    business_agent = factory.create_agent(
        name="BusinessAnalyst",
        system_message="你是业务分析师，专注于业务需求分析和解决方案设计。",
        model_name="deepseek",
    )
    agents.append(business_agent)

    # 技术智能体
    tech_agent = factory.create_agent(
        name="TechArchitect",
        system_message="你是技术架构师，专注于系统设计和技术方案。",
        model_name="deepseek",
    )
    agents.append(tech_agent)

    # 监控智能体
    monitor_agent = factory.create_monitoring_agent()
    agents.append(monitor_agent)

    print(f"✅ 成功创建 {len(agents)} 个智能体")
    for agent in agents:
        print(f"   - {agent.name}")

    # 测试监控智能体
    print("\n📊 测试监控智能体:")
    termination = MaxMessageTermination(3)
    monitor_team = RoundRobinGroupChat(
        [monitor_agent],
        termination_condition=termination,
    )

    result = await monitor_team.run(task="获取当前系统指标并检查健康状态")

    for message in result.messages:
        if hasattr(message, "source") and message.source == "MonitoringAgent":
            print(f"   监控报告: {message.content[:200]}...")


async def demo_config_validation() -> None:
    """演示配置验证"""
    print("\n✅ Configuration Validation Demo")
    print("-" * 50)

    # 测试有效配置
    try:
        valid_config = ProductionConfig(
            environment=Environment.DEVELOPMENT,
            default_model="deepseek",
        )
        print("✅ 有效配置验证通过")

        # 测试模型客户端创建
        valid_config.get_model_client()
        print("✅ 模型客户端创建成功")

    except Exception as e:
        print(f"❌ 配置验证失败: {e}")

    # 测试无效配置
    print("\n🔍 测试配置错误处理:")

    # 测试不存在的模型
    try:
        ProductionConfig(default_model="nonexistent")
        print("❌ 应该抛出配置错误")
    except ConfigurationError as e:
        print(f"✅ 正确捕获配置错误: {e}")

    # 测试缺失API密钥（模拟）
    original_key = os.environ.get("OPENAI_API_KEY")
    try:
        # 临时移除API密钥
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]

        config = ProductionConfig()
        config.get_model_client()
        print("❌ 应该抛出API密钥错误")

    except ConfigurationError as e:
        print(f"✅ 正确捕获API密钥错误: {e}")
    finally:
        # 恢复API密钥
        if original_key:
            os.environ["OPENAI_API_KEY"] = original_key


async def demo_environment_switching() -> None:
    """演示环境切换"""
    print("\n🔄 Environment Switching Demo")
    print("-" * 50)

    # 模拟不同环境的配置
    environments = [
        (Environment.DEVELOPMENT, "开发环境"),
        (Environment.STAGING, "测试环境"),
        (Environment.PRODUCTION, "生产环境"),
    ]

    for env, desc in environments:
        print(f"\n🏷️ 切换到{desc}:")

        config = ProductionConfig(environment=env)
        factory = ProductionAgentFactory(config)

        # 创建适合该环境的智能体
        agent = factory.create_agent(
            name=f"{env.value.title()}Agent",
            system_message=f"你是{desc}的智能体，请根据环境特点调整行为。",
            model_name="deepseek",
        )

        print(f"   ✅ 创建智能体: {agent.name}")
        print(
            f"   📊 配置摘要: 并发数={config.max_concurrent_requests}, "
            f"缓存={config.cache_enabled}, 限流={config.enable_rate_limiting}",
        )


async def main() -> None:
    """主演示函数"""
    print("🏭 AutoGen 生产级配置管理演示")
    print("=" * 60)

    try:
        await demo_production_config()
        await demo_agent_factory()
        await demo_config_validation()
        await demo_environment_switching()

        print("\n✨ 所有生产级配置演示完成!")
        print("\n📚 关键要点:")
        print("   • 分环境的配置管理确保部署安全")
        print("   • 智能体工厂模式提高代码复用性")
        print("   • 配置验证防止运行时错误")
        print("   • 日志和监控配置支持生产运维")
        print("   • 安全配置保护API密钥和系统")
        print("   • 性能配置优化系统响应")

        # 清理临时配置文件
        import glob

        for config_file in glob.glob("config_*.json"):
            try:
                os.remove(config_file)
                print(f"   🧹 已清理临时文件: {config_file}")
            except OSError:
                pass

    except Exception as e:
        print(f"❌ 演示失败: {e}")
        print("💡 检查API配置和环境变量")


if __name__ == "__main__":
    asyncio.run(main())
