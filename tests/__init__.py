#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI-EditX 测试框架
提供统一的测试基础设施和工具函数
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 测试配置
TEST_CONFIG = {
    "TEMP_DIR": project_root / "tests" / "temp",
    "TEST_DATA": project_root / "tests" / "data",
    "MOCK_DATA": project_root / "tests" / "mock_data",
    "COVERAGE_THRESHOLD": 80.0,
}

# 确保测试目录存在
for path in [TEST_CONFIG["TEMP_DIR"], TEST_CONFIG["TEST_DATA"], TEST_CONFIG["MOCK_DATA"]]:
    path.mkdir(parents=True, exist_ok=True)