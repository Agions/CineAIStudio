.PHONY: help install install-dev test test-cov lint format clean build run docs

# 默认目标
help:
	@echo "AI-EditX 开发工具"
	@echo ""
	@echo "可用命令："
	@echo "  install      - 安装项目依赖"
	@echo "  install-dev  - 安装开发环境"
	@echo "  test         - 运行测试"
	@echo "  test-cov     - 运行测试并生成覆盖率报告"
	@echo "  lint         - 代码风格检查"
	@echo "  format       - 代码格式化"
	@echo "  clean        - 清理临时文件"
	@echo "  build        - 构建应用"
	@echo "  run          - 运行应用"
	@echo "  docs         - 生成文档"
	@echo "  help         - 显示此帮助信息"

# 安装项目依赖
install:
	pip install -r requirements.txt

# 安装开发环境
install-dev:
	pip install -r requirements.txt[dev]
	pre-commit install

# 运行测试
test:
	pytest tests/ -v

# 运行测试并生成覆盖率报告
test-cov:
	pytest tests/ --cov=app --cov-report=html --cov-report=term

# 代码风格检查
lint:
	flake8 app tests examples
	mypy app --ignore-missing-imports
	black --check app tests examples
	isort --check-only app tests examples

# 代码格式化
format:
	black app tests examples
	isort app tests examples

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
build:
	python -m PyInstaller \
		--name="AI-EditX" \
		--windowed \
		--onefile \
		--add-data="resources:resources" \
		--hidden-import="PyQt6.sip" \
		--hidden-import="PyQt6.QtCore" \
		--hidden-import="PyQt6.QtGui" \
		--hidden-import="PyQt6.QtWidgets" \
		main.py

# 运行应用
run:
	python main.py

# 运行开发模式
run-dev:
	python main.py --dev

# 生成文档
docs:
	cd docs && make html

# 安装 Git hooks
install-hooks:
	pre-commit install

# 检查依赖更新
check-deps:
	pip list --outdated

# 更新依赖
update-deps:
	pip install --upgrade -r requirements.txt

# 运行安全扫描
security:
	bandit -r app/ -f json -o security-report.json
	safety check

# 性能测试
perf:
	python -m pytest tests/performance/ -v

# 集成测试
integration:
	python -m pytest tests/integration/ -v

# 代码质量检查
quality:
	@echo "运行代码质量检查..."
	$(MAKE) lint
	$(MAKE) test-cov
	$(MAKE) security
	@echo "代码质量检查完成！"

# 发布准备
release-prep:
	$(MAKE) clean
	$(MAKE) test
	$(MAKE) lint
	$(MAKE) docs
	@echo "发布准备完成！"

# Docker 构建
docker-build:
	docker build -t aieditx:latest .

# Docker 运行
docker-run:
	docker run -it --rm \
		--device /dev/dri \
		--env DISPLAY=$$DISPLAY \
		-v /tmp/.X11-unix:/tmp/.X11-unix \
		aieditx:latest

# 插件开发环境
plugin-dev:
	@echo "设置插件开发环境..."
	cp examples/plugins/sample_plugin_template/ my_plugin/
	@echo "插件模板已创建在 my_plugin/ 目录"
	@echo "请参考 app/plugins/README.md 开始开发"

# 性能分析
profile:
	python -m cProfile -o profile.stats main.py
	python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"

# 内存分析
memory:
	python -m memory_profiler main.py

# 安装 GPU 支持
install-gpu:
	@if command -v nvidia-smi &> /dev/null; then \
		echo "检测到 NVIDIA GPU，安装 PyTorch CUDA 版本..."; \
		pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118; \
	elif command -v rocm-smi &> /dev/null; then \
		echo "检测到 AMD GPU，安装 PyTorch ROCm 版本..."; \
		pip install torch torchvision --index-url https://download.pytorch.org/whl/rocm5.4.2; \
	else \
		echo "未检测到支持的 GPU，安装 CPU 版本..."; \
		pip install torch torchvision; \
	fi

# 检查系统兼容性
check-system:
	@echo "检查系统兼容性..."
	@python -c "import sys; print(f'Python 版本: {sys.version}')"
	@python -c "import PyQt6; print(f'PyQt6 版本: {PyQt6.QtCore.PYQT_VERSION_STR}')"
	@python -c "import sys; print(f'平台: {sys.platform}')"

# 快速测试
quick-test:
	python -m pytest tests/test_core/test_application.py -v

# 演示模式
demo:
	python main.py --demo

# 调试模式
debug:
	python -m pdb main.py

# 日志级别设置
verbose:
	python main.py --log-level DEBUG

# 版本信息
version:
	@python -c "import app; print(f'AI-EditX 版本: {app.__version__}')"

# 统计信息
stats:
	@echo "项目统计信息："
	@echo "Python 文件数量: $(shell find app -name '*.py' | wc -l)"
	@echo "代码行数: $(shell find app -name '*.py' -exec wc -l {} + | tail -1)"
	@echo "测试文件数量: $(shell find tests -name '*.py' | wc -l)"

# 完整的质量检查
full-check:
	@echo "执行完整质量检查..."
	$(MAKE) check-system
	$(MAKE) install-dev
	$(MAKE) lint
	$(MAKE) test-cov
	$(MAKE) security
	@echo "完整质量检查完成！"

# 设置开发环境
setup-dev:
	$(MAKE) install-dev
	$(MAKE) install-hooks
	@echo "开发环境设置完成！"
	@echo ""
	@echo "下一步："
	@echo "1. 运行 'make test' 验证环境"
	@echo "2. 运行 'make run' 启动应用"
	@echo "3. 运行 'make docs' 查看文档"

# 更新版本
bump-version:
	@echo "更新版本号..."
	@read -p "请输入新版本号: " version; \
	sed -i "s/__version__ = \".*\"/__version__ = \"$$version\"/" app/__init__.py
	@echo "版本已更新为 $$version"

# 构建文档站点
docs-site:
	cd docs && make html && open _build/html/index.html

# 清理所有生成的文件
clean-all:
	$(MAKE) clean
	rm -rf docs/_build/
	rm -rf site/
	rm -f *.log
	rm -f *.stats
	rm -f security-report.json
	rm -f .coverage
	rm -f coverage.xml

# 检查许可证兼容性
license-check:
	@echo "检查许可证兼容性..."
	pip-licenses
	@echo "许可证检查完成"

# 导出依赖列表
export-deps:
	pip freeze > requirements-freeze.txt
	pip list --format=freeze > requirements-list.txt

# 安装本地开发版本
install-local:
	pip install -e .

# 发布到 PyPI
publish:
	$(MAKE) clean
	$(MAKE) test
	python setup.py sdist bdist_wheel
	twine upload dist/*