#!/usr/bin/env python3
"""
AutoGen 学习项目 - 所有示例测试脚本
=====================================

这个脚本会运行所有10个示例，验证项目的完整性。

使用方法:
    nix develop --command python test_all_examples.py
"""

import os
import subprocess
import sys
import time
from pathlib import Path


def print_header(title: str):
    """打印格式化的标题"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")


def print_section(title: str):
    """打印章节标题"""
    print(f"\n{'🔸' * 20}")
    print(f"📋 {title}")
    print(f"{'🔸' * 20}")


def run_example(file_path: str, description: str) -> bool:
    """运行单个示例并返回是否成功"""
    print(f"\n🚀 运行: {description}")
    print(f"📄 文件: {file_path}")

    start_time = time.time()

    try:
        # 运行示例，限制最大运行时间为60秒
        result = subprocess.run(
            [sys.executable, file_path],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=Path(__file__).parent,
        )

        end_time = time.time()
        duration = end_time - start_time

        if result.returncode == 0:
            print(f"✅ 成功! 耗时: {duration:.2f}秒")
            return True
        print(f"❌ 失败! 错误代码: {result.returncode}")
        print(f"错误输出: {result.stderr}")
        return False

    except subprocess.TimeoutExpired:
        print("⏰ 超时! (>60秒)")
        return False
    except Exception as e:
        print(f"💥 异常: {e!s}")
        return False


def check_environment():
    """检查环境设置"""
    print_section("环境检查")

    # 检查Python版本
    python_version = sys.version_info
    print(
        f"🐍 Python版本: {python_version.major}."
        f"{python_version.minor}.{python_version.micro}",
    )

    # 检查AutoGen包
    import importlib.util

    packages = [
        ("autogen-agentchat", "autogen_agentchat"),
        ("autogen-core", "autogen_core"),
        ("autogen-ext", "autogen_ext"),
    ]

    for package_name, module_name in packages:
        if importlib.util.find_spec(module_name):
            print(f"✅ {package_name} 已安装")
        else:
            print(f"❌ {package_name} 未安装")
            return False

    # 检查.env文件
    if os.path.exists(".env"):
        print("✅ .env 文件存在")
    else:
        print("⚠️  .env 文件不存在，请复制 env.example 并配置API密钥")
        return False

    return True


def main():
    """主函数"""
    print_header("AutoGen 学习项目 - 完整测试")

    # 环境检查
    if not check_environment():
        print("\n❌ 环境检查失败，请先解决环境问题")
        sys.exit(1)

    # 定义所有示例
    examples = [
        # 基础阶段
        ("examples/basic/01_hello_world.py", "第一个 AutoGen 智能体"),
        ("examples/basic/02_assistant_agent.py", "助手智能体深入探索"),
        ("examples/basic/03_user_proxy.py", "用户代理智能体"),
        ("examples/basic/04_simple_conversation.py", "双智能体对话系统"),
        # 中级阶段
        ("examples/intermediate/01_tool_integration.py", "工具集成"),
        ("examples/intermediate/02_selector_group_chat.py", "智能选择器群组聊天"),
        ("examples/intermediate/03_workflow_orchestration.py", "工作流编排"),
        # 高级阶段
        ("examples/advanced/01_production_config.py", "生产级配置管理"),
        ("examples/advanced/02_enterprise_system.py", "企业级多智能体系统"),
        ("examples/advanced/03_monitoring_logging.py", "监控和日志系统"),
    ]

    # 运行测试
    total_examples = len(examples)
    successful_examples = 0
    failed_examples = []

    stages = [
        ("🌱 基础阶段", examples[0:4]),
        ("🌿 中级阶段", examples[4:7]),
        ("🌳 高级阶段", examples[7:10]),
    ]

    overall_start_time = time.time()

    for stage_name, stage_examples in stages:
        print_section(f"{stage_name} ({len(stage_examples)}个示例)")

        stage_success = 0
        for file_path, description in stage_examples:
            if run_example(file_path, description):
                successful_examples += 1
                stage_success += 1
            else:
                failed_examples.append((file_path, description))

        print(f"\n📊 {stage_name} 完成: {stage_success}/{len(stage_examples)} 成功")

    overall_end_time = time.time()
    total_duration = overall_end_time - overall_start_time

    # 生成测试报告
    print_header("测试报告")

    print("📊 总体统计:")
    print(f"   总示例数: {total_examples}")
    print(f"   成功示例: {successful_examples}")
    print(f"   失败示例: {len(failed_examples)}")
    print(f"   成功率: {(successful_examples/total_examples)*100:.1f}%")
    print(f"   总耗时: {total_duration:.2f}秒")

    if failed_examples:
        print("\n❌ 失败的示例:")
        for file_path, description in failed_examples:
            print(f"   - {description} ({file_path})")

    if successful_examples == total_examples:
        print(f"\n🎉 恭喜! 所有 {total_examples} 个示例都运行成功!")
        print("✨ 你已经完全掌握了 AutoGen 的所有功能!")
        sys.exit(0)
    else:
        print(f"\n⚠️  有 {len(failed_examples)} 个示例运行失败，请检查错误信息")
        sys.exit(1)


if __name__ == "__main__":
    main()
