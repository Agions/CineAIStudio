"""
CineFlow v3.0 主入口
多Agent智能视频剪辑系统
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入主窗口
from app.ui.main_window import main

if __name__ == "__main__":
    main()
