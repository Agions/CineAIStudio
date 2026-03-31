# VideoForge Makefile
# 使用方法: make <target>

.PHONY: help install install-dev test test-cov lint format clean build build:win build:mac build:linux docs

# 默认目标
help:
	@echo "VideoForge 构建工具"
	@echo ""
	@echo "可用命令："
	@echo "  install       - 安装项目依赖 (uv)"
	@echo "  install-dev   - 安装开发环境"
	@echo "  test          - 运行测试"
	@echo "  test-cov      - 运行测试并生成覆盖率报告"
	@echo "  lint          - 代码风格检查"
	@echo "  format        - 代码格式化"
	@echo "  clean         - 清理临时文件"
	@echo "  build         - 构建应用 (跨平台 PyInstaller)"
	@echo "  build:win     - 构建 Windows 版本"
	@echo "  build:mac     - 构建 macOS 版本"
	@echo "  build:linux   - 构建 Linux 版本"
	@echo "  docs          - 生成文档"
	@echo "  help          - 显示此帮助信息"

# 安装项目依赖
install:
	uv pip install -e .

# 安装开发环境
install-dev:
	uv pip install -e ".[dev]"
	pre-commit install

# 运行测试
test:
	pytest tests/ -v

# 运行测试并生成覆盖率报告
test-cov:
	pytest tests/ --cov=app --cov-report=html --cov-report=term

# 代码风格检查
lint:
	ruff check app tests
	black --check app tests
	isort --check-only app tests

# 代码格式化
format:
	black app tests
	isort app tests

# 清理临时文件
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

# 构建应用
build: clean
	pyinstaller main.spec --noconfirm

# Windows 构建
build:win:
	pyinstaller main.spec --noconfirm --win

# macOS 构建
build:mac:
	./build_dmg.sh

# Linux 构建
build:linux:
	pyinstaller main.spec --noconfirm --linux

# Nuitka 打包（性能更好，启动更快）
build:nuitka:
	./build_nuitka.sh

# 生成文档
docs:
	cd docs && npm run docs:build
