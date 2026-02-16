#!/usr/bin/env python3
"""
CineFlow 版本切换工具

用于快速切换查看不同版本的代码，不覆盖当前工作。

用法:
    python scripts/switch_version.py 2.0.0     # 切换到v2.0.0
    python scripts/switch_version.py 3.0-beta1 # 切换到v3.0-beta1
    python scripts/switch_version.py 3.0-beta2 # 切换到v3.0-beta2
    python scripts/switch_version.py 3.0-beta3 # 切换到v3.0-beta3
    python scripts/switch_version.py main      # 返回主分支
    python scripts/switch_version.py --list    # 列出所有版本
"""

import sys
import subprocess
from typing import Dict, Optional

# 版本映射表
VERSIONS: Dict[str, str] = {
    "2.0.0": {
        "ref": "v2.0.0",
        "name": "v2.0.0 基础版本",
        "desc": "单Agent架构，基础视频处理，CLI界面",
        "date": "2024"
    },
    "3.0-beta1": {
        "ref": "8a12093",
        "name": "v3.0.0-beta1 多Agent架构",
        "desc": "6个专业Agent，核心服务层，多LLM支持",
        "date": "2025-01-20"
    },
    "3.0-beta2": {
        "ref": "b4192d4",
        "name": "v3.0.0-beta2 PyQt6 UI",
        "desc": "图形界面，Agent监控，项目管理",
        "date": "2025-01-20"
    },
    "3.0-beta3": {
        "ref": "a16f529",
        "name": "v3.0.0-beta3 代码优化",
        "desc": "性能优化，代码质量提升，异步初始化",
        "date": "2025-01-20"
    },
    "3.0-latest": {
        "ref": "e81edfa",
        "name": "v3.0.0-beta3-docs 文档完善",
        "desc": "完整文档，API参考，安装指南",
        "date": "2025-01-20"
    },
    "main": {
        "ref": "main",
        "name": "main 主分支",
        "desc": "最新开发版本",
        "date": "latest"
    }
}


def run_git_command(args: list) -> tuple[bool, str]:
    """运行git命令"""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()


def list_versions():
    """列出所有版本"""
    print("\n📦 CineFlow 可用版本:\n")
    print(f"{'版本':<15} {'日期':<12} {'描述'}")
    print("-" * 70)
    
    for key, info in VERSIONS.items():
        print(f"{key:<15} {info['date']:<12} {info['desc']}")
    
    print("\n用法: python scripts/switch_version.py <版本>")
    print("示例: python scripts/switch_version.py 3.0-beta1")


def switch_version(version_key: str):
    """切换到指定版本"""
    if version_key not in VERSIONS:
        print(f"❌ 未知版本: {version_key}")
        print(f"可用版本: {', '.join(VERSIONS.keys())}")
        return False
    
    info = VERSIONS[version_key]
    ref = info["ref"]
    
    print(f"\n🔄 切换到: {info['name']}")
    print(f"   提交: {ref}")
    print(f"   描述: {info['desc']}")
    print()
    
    # 检查是否有未提交的更改
    success, output = run_git_command(["status", "--porcelain"])
    if not success:
        print(f"❌ Git错误: {output}")
        return False
    
    if output:
        print("⚠️  警告: 当前有未提交的更改")
        print("   建议先提交或暂存更改:")
        print("   git add -A && git commit -m '保存更改'")
        print("   或: git stash")
        
        response = input("\n是否继续? (y/N): ")
        if response.lower() != 'y':
            print("❌ 已取消")
            return False
    
    # 切换到指定版本
    success, output = run_git_command(["checkout", ref])
    if not success:
        print(f"❌ 切换失败: {output}")
        return False
    
    print(f"✅ 成功切换到: {info['name']}")
    print(f"\n提示:")
    print(f"  - 当前处于 '分离HEAD' 状态，可以自由查看代码")
    print(f"  - 修改不会被保存，如需修改请创建分支:")
    print(f"    git checkout -b my-branch-{version_key}")
    print(f"  - 返回主分支: python scripts/switch_version.py main")
    
    return True


def show_current():
    """显示当前版本"""
    success, output = run_git_command(["log", "-1", "--oneline"])
    if success:
        print(f"\n📍 当前版本: {output}")
    
    success, branch = run_git_command(["branch", "--show-current"])
    if success and branch:
        print(f"   分支: {branch}")


def main():
    if len(sys.argv) < 2:
        show_current()
        list_versions()
        return
    
    arg = sys.argv[1]
    
    if arg in ("--list", "-l", "list"):
        list_versions()
    elif arg in ("--help", "-h", "help"):
        print(__doc__)
    else:
        switch_version(arg)


if __name__ == "__main__":
    main()
