# Voxplore Makefile
# 多系统版本打包工具
#
# 使用方法:
#   make help          显示帮助
#   make build:win     Windows x64 (.zip)
#   make build:mac     macOS x64 (.dmg)
#   make build:mac-arm macOS ARM64 (.dmg)
#   make build:linux   Linux x86_64 (.AppImage)
#   make test          运行测试
#   make clean         清理临时文件

.SUFFIXES:
.PHONY: help build build:win build:mac build:mac-arm build:linux clean test test-cov lint format docs

# ── 版本号（单一真相来源：pyproject.toml）───────────────────────────
VERSION := $(shell grep '^version = ' pyproject.toml 2>/dev/null | sed 's/version = "//;s/"//' | tr -d '[:space:]')
PLATFORM := $(shell python3 -c "import sys; s='darwin' if sys.platform=='darwin' else 'win32' if sys.platform=='win32' else 'linux'; print(s)")

# ── 颜色输出 ───────────────────────────────────────────────────────
GREEN  := \033[0;32m
CYAN   := \033[0;36m
YELLOW := \033[1;33m
RED    := \033[0;31m
NC     := \033[0m

info    = @echo "$(GREEN)[INFO]$(NC)  $*"
step    = @echo "$(CYAN)[STEP]$(NC)  $*"
warn    = @echo "$(YELLOW)[WARN]$(NC)  $*"

# ── 默认目标：显示帮助 ─────────────────────────────────────────────
help:
	@echo "Voxplore Build System  v$(VERSION)"
	@echo ""
	@echo "使用方式: make <target>"
	@echo ""
	@echo "构建目标:"
	@echo "  build:win     构建 Windows x64 版本（.zip）"
	@echo "  build:mac     构建 macOS x64 版本（.dmg）"
	@echo "  build:mac-arm 构建 macOS ARM64 版本（.dmg）"
	@echo "  build:linux   构建 Linux x86_64 版本（.AppImage）"
	@echo ""
	@echo "开发目标:"
	@echo "  test          运行测试"
	@echo "  test-cov      运行测试并生成覆盖率报告"
	@echo "  lint          代码风格检查"
	@echo "  format        代码格式化"
	@echo "  clean         清理临时文件"
	@echo ""
	@echo "版本: $(VERSION)"

# ── 跨平台构建 ─────────────────────────────────────────────────────
build: build:$(PLATFORM)

build:win:
	$(step) Windows x64 构建（PyInstaller）...
	@if [ "$(shell uname)" = "Darwin" ]; then \
		echo "$(RED)[ERROR]$(NC) Windows 构建只能在 Windows/macOS/Linux 执行"; \
		exit 1; \
	fi
	@powershell -ExecutionPolicy Bypass -File scripts/build_windows.ps1 -Version $(VERSION)
	@echo "$(GREEN)✅ Windows 构建完成: dist/Voxplore-$(VERSION)-windows-x64.zip$(NC)"

build:mac:
	$(step) macOS x64 构建（PyInstaller）...
	@bash scripts/build_macos.sh x64
	@echo "$(GREEN)✅ macOS x64 构建完成: dist/Voxplore-$(VERSION)-macos-x64.dmg$(NC)"

build:mac-arm:
	$(step) macOS ARM64 构建（PyInstaller）...
	@bash scripts/build_macos.sh arm64
	@echo "$(GREEN)✅ macOS ARM64 构建完成: dist/Voxplore-$(VERSION)-macos-arm64.dmg$(NC)"

build:linux:
	$(step) Linux x86_64 构建（Nuitka + AppImage）...
	@bash scripts/build_linux.sh
	@echo "$(GREEN)✅ Linux 构建完成: Voxplore-$(VERSION)-linux-x86_64.AppImage$(NC)"

# ── 开发目标 ───────────────────────────────────────────────────────
test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=app --cov-report=html --cov-report=term

lint:
	ruff check app tests
	black --check app tests
	isort --check-only app tests

format:
	black app tests
	isort app tests

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf build/ dist/ dist-nuitka/ *.egg-info/
	rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/
	rm -rf htmlcov/ .coverage

docs:
	cd docs && npm run docs:build
