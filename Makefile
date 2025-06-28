# AutoGen Learning Project - Code Quality Makefile
# ================================================
# 
# 使用方法:
#   make fmt      - 格式化所有代码
#   make lint     - 运行代码检查
#   make security - 运行安全审查
#   make check    - 运行所有检查
#   make clean    - 清理缓存文件

.PHONY: fmt lint security check clean help

# 默认目标
help:
	@echo "🛠️  AutoGen 项目代码质量工具"
	@echo "================================"
	@echo ""
	@echo "📋 可用命令:"
	@echo "  make fmt          - 格式化所有代码"
	@echo "  make lint         - 运行代码检查"
	@echo "  make security     - 运行安全审查 (快速模式)"
	@echo "  make security-full - 运行完整安全审查"
	@echo "  make check        - 运行所有检查"
	@echo "  make quick        - 快速检查 (格式+基本检查)"
	@echo "  make clean        - 清理缓存文件"
	@echo ""
	@echo "💡 提示: 请先运行 'nix develop' 进入开发环境"

# 代码格式化
fmt:
	@echo "🎨 格式化 Python 代码..."
	@black --line-length 88 --target-version py311 .
	@echo "📦 整理 Python 导入..."
	@isort --profile black --line-length 88 .
	@echo "🔧 格式化 Nix 代码..."
	@nixpkgs-fmt flake.nix
	@echo "✅ 代码格式化完成!"

# 代码检查
lint:
	@echo "🔍 运行代码检查..."
	@echo "📋 Ruff 检查 (快速 linter)..."
	@ruff check . --select E,W,F,B,C,N,UP,S,A,COM,DTZ,ISC,ICN,PIE,PT,Q,RET,SIM,ARG,PTH,ERA,PGH,PL,TRY,FLY,PERF,RUF
	@echo "🔬 MyPy 类型检查..."
	@mypy --ignore-missing-imports --no-strict-optional examples/ test_all_examples.py || true
	@echo "🔧 Nix 代码检查..."
	@statix check flake.nix || true
	@deadnix flake.nix || true
	@echo "✅ 代码检查完成!"

# 安全审查
security:
	@echo "🔒 运行安全审查..."
	@echo "🛡️  Bandit 安全扫描 (仅项目代码)..."
	@bandit -c .bandit -r examples/ test_all_examples.py -f json -o bandit-report.json || true
	@bandit -c .bandit -r examples/ test_all_examples.py || true
	@echo "📦 Safety 依赖漏洞扫描 (快速模式)..."
	@timeout 30 safety scan --output text > safety-report.txt 2>&1 || echo "   ⚠️  Safety 扫描超时或失败，跳过依赖漏洞检查"
	@echo "✅ 安全审查完成!"

# 完整安全审查 (包括网络依赖的扫描)
security-full:
	@echo "🔒 运行完整安全审查..."
	@echo "🛡️  Bandit 安全扫描..."
	@bandit -c .bandit -r examples/ test_all_examples.py || true
	@echo "📦 Safety 依赖漏洞扫描 (完整模式)..."
	@safety scan || true
	@echo "✅ 完整安全审查完成!"

# 运行所有检查
check: fmt lint security
	@echo ""
	@echo "🎉 所有代码质量检查完成!"
	@echo ""
	@echo "📊 检查报告:"
	@echo "  • 格式化: 已完成"
	@echo "  • 代码检查: 已完成"
	@echo "  • 安全审查: 已完成"
	@echo ""
	@if [ -f bandit-report.json ]; then \
		echo "📄 安全报告: bandit-report.json"; \
	fi
	@if [ -f safety-report.txt ]; then \
		echo "📄 依赖报告: safety-report.txt"; \
	fi

# 清理缓存文件
clean:
	@echo "🧹 清理缓存文件..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@find . -name "*.pyo" -delete 2>/dev/null || true
	@rm -f bandit-report.json safety-report.txt 2>/dev/null || true
	@echo "✅ 清理完成!"

# 快速检查（仅格式化和基本检查）
quick:
	@echo "⚡ 快速检查..."
	@black --check --line-length 88 .
	@isort --check-only --profile black --line-length 88 .
	@ruff check . --select E,W,F
	@echo "✅ 快速检查通过!" 