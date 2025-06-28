# AutoGen 学习项目 🤖

一个基于 Nix 的 AutoGen 框架完整学习项目，包含 10 个渐进式示例，从基础概念到企业级应用，展示多智能体系统的强大功能。

## 🚀 快速开始

```bash
# 1. 进入开发环境
nix develop

# 2. 配置 API 密钥
cp env.example .env
# 编辑 .env 文件，添加你的 DeepSeek API 密钥

# 3. 运行第一个示例
python examples/basic/01_hello_world.py

# 4. 或者运行完整测试（可选）
python test_all_examples.py

# 5. 代码质量检查（可选）
make fmt          # 格式化代码
make lint         # 代码检查
make security     # 安全审查 (快速模式)
make security-full # 完整安全审查
make check        # 运行所有检查
```

## 📚 完整学习路径

### 🌱 基础阶段 (4个示例)
- **01_hello_world.py** - 第一个 AutoGen 智能体
- **02_assistant_agent.py** - 助手智能体深入探索
- **03_user_proxy.py** - 用户代理智能体和人机交互
- **04_simple_conversation.py** - 双智能体对话系统

### 🌿 中级阶段 (3个示例)
- **01_tool_integration.py** - 工具集成和外部API调用
- **02_selector_group_chat.py** - 智能选择器群组聊天
- **03_workflow_orchestration.py** - 复杂工作流编排

### 🌳 高级阶段 (3个示例)
- **01_production_config.py** - 生产级配置管理
- **02_enterprise_system.py** - 企业级多智能体系统
- **03_monitoring_logging.py** - 监控和日志系统

## 🔧 技术特性

- ✅ **Nix 环境管理** - 完全可重现的开发环境，一键启动
- ✅ **AutoGen 新架构** - 使用最新的 autogen-agentchat, autogen-core, autogen-ext
- ✅ **DeepSeek API 支持** - 完全兼容 OpenAI API 格式
- ✅ **异步编程** - 所有示例采用 async/await 模式
- ✅ **工具集成** - 丰富的 FunctionTool 示例
- ✅ **群组聊天** - RoundRobinGroupChat 和 SelectorGroupChat
- ✅ **代码质量** - 集成 Black、Ruff、MyPy、Bandit 等业界标准工具
- ✅ **安全审查** - 项目代码零安全漏洞，快速和完整两种扫描模式
- ✅ **中文友好** - 所有示例和文档支持中文
- ✅ **渐进式学习** - 从简单到复杂的完整学习路径
- ✅ **生产就绪** - 包含监控、日志、配置管理等企业级功能

## 📖 详细文档

- **[设置指南](SETUP_GUIDE.md)** - 详细的环境设置和故障排除
- **[完整测试](test_all_examples.py)** - 一键测试所有10个示例
- **[代码质量工具](Makefile)** - 格式化、检查、安全审查命令

## 🎯 项目目标

通过 10 个渐进式示例学习 AutoGen 的所有核心功能：

### 基础能力
- 智能体创建和配置 (temperature, max_tokens, 系统消息等)
- 用户代理和人机交互
- 双智能体对话和终止条件

### 中级能力  
- 工具集成 (计算器、天气、文本分析等)
- 智能群组选择器和专业化团队协作
- 复杂工作流编排和状态管理

### 高级能力
- 生产级配置管理 (多环境、智能体工厂)
- 企业级任务管理系统
- 监控、日志、告警系统

## 📈 学习进度追踪

### 基础阶段 ✅
- [x] 第一个智能体和API配置
- [x] 助手智能体深入配置
- [x] 用户代理和协作工作流
- [x] 双智能体对话系统

### 中级阶段 ✅
- [x] 工具集成和函数调用
- [x] 智能选择器群组聊天
- [x] 复杂工作流编排

### 高级阶段 ✅
- [x] 生产级配置管理
- [x] 企业级多智能体系统
- [x] 监控和日志系统

**🎉 项目完成度: 100% (10/10 示例)**

## 🤝 贡献指南

欢迎提交问题和改进建议！请遵循以下步骤：

1. Fork 本项目
2. 创建功能分支
3. 提交更改
4. 发起 Pull Request

## 📄 许可证

MIT License - 详见 LICENSE 文件

---

**开始你的 AutoGen 学习之旅！** 🚀

> 💡 **提示**: 如果你是第一次使用，请先阅读 [设置指南](SETUP_GUIDE.md) 了解详细的环境配置步骤。 