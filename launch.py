#!/usr/bin/env python3
"""
CineFlow v3.0 启动脚本
"""

import sys
import os
from pathlib import Path

# 确保在项目根目录
os.chdir(Path(__file__).parent)

# 运行主程序
from app.main import main

if __name__ == "__main__":
    main()
