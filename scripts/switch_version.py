#!/usr/bin/env python3
"""
CineFlow 版本切换工具

用于快速切换查看不同版本的代码，不覆盖当前工作。
支持分支切换和提交切换两种模式。

用法:
    python scripts/switch_version.py 2.0.0          # 切换到v2.0.0分支
    python scripts/switch_version.py 3.0-beta1      # 切换到v3.0-beta1分支
    python scripts/switch_version.py 3.0-beta2      # 切换到v3.0-beta2分支
    python scripts/switch_version.py 3.0-beta3      # 切换到v3.0-beta3分支
    python scripts/switch_version.py main           # 返回主分支
    python scripts/switch_version.py --list         # 列出所有版本
    python scripts/switch_version.py --create-tags  # 创建版本标签
"""

import sys
import subprocess
from typing import Dict, Optional

# 版本映射表 - 分支模式
VERSIONS: Dict[str, dict] = {
    "2.0.0": {
        "ref": "release/v2.0.0",
        "name": "v2.0.0 基础版本",
        "desc": "单Agent架构，基础视频处理，CLI界面",
        "date": "2024",
        "commit": "v2.0.0"
    },
    "3.0-beta1": {
        "ref": "release/v3.0-beta1",
        "name": "v3.0.0-beta1 多Agent架构",
        "desc": "6个专业Agent，核心服务层，多LLM支持",
        "date": "2025-01-20",
        "commit": "8a12093"
    },
    "3.0-beta2": {
        "ref": "release/v3.0-beta2",
        "name": "v3.0.0-beta2 PyQt6 UI",
        "desc": "图形界面，Agent监控，项目管理",
        "date": "2025-01-20",
        "commit": "b4192d4"
    },
    "3.0-beta3": {
        "ref": "release/v3.0-beta3",
        "name": "v3.0.0-beta3 代码优化",
        "desc": "性能优化，代码质量提升，异步初始化",
        "date": "2025-01-20",
        "commit": "a16f529"
    },
    "3.0-latest": {
        "ref": "main",
        "name": "v3.0.0-beta3-docs 文档完善",
        "desc": "完整文档，API参考，安装指南，版本工具",
        "date": "2025-01-20",
        "commit": "main"
    },
    "main": {
        "ref": "main",
        "name": "main 主分支",
        "desc": "最新开发版本",
        "date": "latest",
        "commit": "main"
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
    print(f"{'版本':<15} {'分支':<25} {'日期':<12} {'描述'}")
    print("-" * 85)
    
    for key, info in VERSIONS.items():
        print(f"{key:<15} {info['ref']:<25} {info['date']:<12} {info['desc']}")
    
    print("\n💡 提示:")
    print("  • 每个版本都有独立分支，代码完全保留")
    print("  • 切换版本不会丢失当前工作")
    print("  • 可以在不同版本间自由切换")
    print("\n用法: python scripts/switch_version.py <版本>")
    print("示例: python scripts/switch_version.py 3.0-beta1")


def create_version_tags():
    """创建版本标签"""
    print("\n🏷️  创建版本标签...\n")
    
    tags = [
        ("v3.0-beta1", "8a12093", "v3.0.0-beta1 多Agent架构"),
        ("v3.0-beta2", "b4192d4", "v3.0.0-beta2 PyQt6 UI"),
        ("v3.0-beta3", "a16f529", "v3.0.0-beta3 代码优化"),
        ("v3.0-latest", "main", "v3.0.0-beta3-docs 文档完善"),
    ]
    
    for tag, commit, msg in tags:
        success, output = run_git_command(["tag", "-a", tag, commit, "-m", msg])
        if success:
            print(f"  ✅ {tag} -> {commit}")
        else:
            print(f"  ⚠️  {tag} 已存在或失败: {output}")
    
    print("\n标签创建完成！")
    print("查看标签: git tag -l")
    print("推送标签: git push origin --tags")


def switch_version(version_key: str):
    """切换到指定版本"""
    if version_key not in VERSIONS:
        print(f"❌ 未知版本: {version_key}")
        print(f"可用版本: {', '.join(VERSIONS.keys())}")
        return False
    
    info = VERSIONS[version_key]
    ref = info["ref"]
    
    print(f"\n🔄 切换到: {info['name']}")
    print(f"   分支: {ref}")
    print(f"   提交: {info['commit']}")
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
    
    # 切换到指定分支
    success, output = run_git_command(["checkout", ref])
    if not success:
        print(f"❌ 切换失败: {output}")
        return False
    
    print(f"✅ 成功切换到: {info['name']}")
    print(f"   当前分支: {ref}")
    
    # 显示当前提交
    success, commit = run_git_command(["log", "-1", "--oneline"])
    if success:
        print(f"   当前提交: {commit}")
    
    print(f"\n💡 提示:")
    print(f"  • 当前在 '{ref}' 分支，可以自由查看和修改代码")
    print(f"  • 每个版本的代码都是独立的，不会互相影响")
    print(f"  • 修改后记得提交: git add -A && git commit -m 'xxx'")
    print(f"  • 返回主分支: python scripts/switch_version.py main")
    
    return True


def show_current():
    """显示当前版本"""
    success, branch = run_git_command(["branch", "--show-current"])
    if success:
        print(f"\n📍 当前分支: {branch}")
    
    success, commit = run_git_command(["log", "-1", "--oneline"])
    if success:
        print(f"   当前提交: {commit}")
    
    # 查找当前分支对应的版本
    for key, info in VERSIONS.items():
        if info["ref"] == branch:
            print(f"   版本标识: {key}")
            break


def show_branch_structure():
    """显示分支结构"""
    print("\n🌳 分支结构:\n")
    print("  main (主分支)")
    print("    │")
    print("    ├── release/v2.0.0 (v2.0.0 基础版本)")
    print("    │")
    print("    ├── release/v3.0-beta1 (v3.0-beta1 多Agent)")
    print("    │")
    print("    ├── release/v3.0-beta2 (v3.0-beta2 PyQt6 UI)")
    print("    │")
    print("    ├── release/v3.0-beta3 (v3.0-beta3 代码优化)")
    print("    │")
    print("    └── [继续开发...]")
    print("\n💡 每个分支都是独立的，可以自由切换")


def main():
    if len(sys.argv) < 2:
        show_current()
        list_versions()
        return
    
    arg = sys.argv[1]
    
    if arg in ("--list", "-l", "list"):
        list_versions()
    elif arg in ("--branches", "-b", "branches"):
        show_branch_structure()
    elif arg in ("--create-tags", "--tags"):
        create_version_tags()
    elif arg in ("--help", "-h", "help"):
        print(__doc__)
    else:
        switch_version(arg)


if __name__ == "__main__":
    main()
