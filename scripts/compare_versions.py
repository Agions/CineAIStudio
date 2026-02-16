#!/usr/bin/env python3
"""
CineFlow 版本对比工具

对比不同版本的代码差异，生成统计报告。

用法:
    python scripts/compare_versions.py 2.0.0 3.0-beta1    # 对比v2.0和v3.0-beta1
    python scripts/compare_versions.py 3.0-beta1 3.0-beta3 # 对比两个beta版本
    python scripts/compare_versions.py --stats              # 显示所有版本统计
"""

import sys
import subprocess
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class VersionInfo:
    """版本信息"""
    key: str
    ref: str
    name: str
    files: int
    lines: int
    python_files: int
    python_lines: int


# 版本映射
VERSION_REFS = {
    "2.0.0": "v2.0.0",
    "3.0-beta1": "8a12093",
    "3.0-beta2": "b4192d4",
    "3.0-beta3": "a16f529",
    "3.0-latest": "e81edfa",
}


def run_git_command(args: list) -> Tuple[bool, str]:
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


def get_version_stats(ref: str) -> Dict:
    """获取版本统计信息"""
    stats = {
        "total_files": 0,
        "total_lines": 0,
        "python_files": 0,
        "python_lines": 0,
        "agents": 0,
        "services": 0,
        "ui_files": 0
    }
    
    # 获取文件列表
    success, output = run_git_command(["ls-tree", "-r", "--name-only", ref])
    if not success:
        return stats
    
    files = output.split('\n')
    stats["total_files"] = len(files)
    
    # 统计Python文件
    python_files = [f for f in files if f.endswith('.py')]
    stats["python_files"] = len(python_files)
    
    # 统计代码行数
    for file in python_files:
        success, content = run_git_command(["show", f"{ref}:{file}"])
        if success:
            lines = len(content.split('\n'))
            stats["python_lines"] += lines
    
    # 统计Agent数量
    agent_files = [f for f in python_files if 'agent' in f.lower() and f.endswith('_agent.py')]
    stats["agents"] = len(agent_files)
    
    # 统计服务数量
    service_files = [f for f in python_files if f.startswith('app/core/') and f.endswith('.py')]
    stats["services"] = len(service_files)
    
    # 统计UI文件
    ui_files = [f for f in python_files if f.startswith('app/ui/')]
    stats["ui_files"] = len(ui_files)
    
    return stats


def compare_versions(v1: str, v2: str):
    """对比两个版本"""
    ref1 = VERSION_REFS.get(v1, v1)
    ref2 = VERSION_REFS.get(v2, v2)
    
    print(f"\n📊 版本对比: {v1} → {v2}\n")
    
    # 获取统计
    print("正在统计...")
    stats1 = get_version_stats(ref1)
    stats2 = get_version_stats(ref2)
    
    # 显示对比
    print(f"{'指标':<20} {v1:<15} {v2:<15} {'变化'}")
    print("-" * 70)
    
    metrics = [
        ("Python文件", "python_files"),
        ("Python代码行", "python_lines"),
        ("Agent数量", "agents"),
        ("核心服务", "services"),
        ("UI文件", "ui_files"),
    ]
    
    for label, key in metrics:
        val1 = stats1[key]
        val2 = stats2[key]
        diff = val2 - val1
        
        if diff > 0:
            change = f"+{diff} ⬆️"
        elif diff < 0:
            change = f"{diff} ⬇️"
        else:
            change = "-"
        
        print(f"{label:<20} {val1:<15} {val2:<15} {change}")
    
    # 获取提交差异
    print("\n📋 提交记录:")
    success, output = run_git_command(["log", "--oneline", f"{ref1}..{ref2}"])
    if success and output:
        commits = output.split('\n')
        print(f"   共 {len(commits)} 个提交:")
        for commit in commits[:10]:  # 显示前10个
            print(f"   • {commit}")
        if len(commits) > 10:
            print(f"   ... 还有 {len(commits) - 10} 个提交")
    else:
        print("   无提交记录或版本顺序错误")
    
    # 获取文件变化
    print("\n📁 文件变化:")
    success, output = run_git_command(["diff", "--stat", ref1, ref2])
    if success and output:
        lines = output.split('\n')
        for line in lines[:15]:  # 显示前15行
            if line.strip():
                print(f"   {line}")
        if len(lines) > 15:
            print(f"   ... 还有 {len(lines) - 15} 行")


def show_all_stats():
    """显示所有版本统计"""
    print("\n📈 CineFlow 版本统计\n")
    print(f"{'版本':<15} {'Python文件':<12} {'代码行数':<12} {'Agents':<8} {'服务':<8} {'UI'}")
    print("-" * 75)
    
    for key, ref in VERSION_REFS.items():
        stats = get_version_stats(ref)
        print(f"{key:<15} {stats['python_files']:<12} {stats['python_lines']:<12} "
              f"{stats['agents']:<8} {stats['services']:<8} {stats['ui_files']}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        show_all_stats()
        return
    
    arg = sys.argv[1]
    
    if arg in ("--stats", "-s", "stats"):
        show_all_stats()
    elif arg in ("--help", "-h", "help"):
        print(__doc__)
    elif len(sys.argv) >= 3:
        compare_versions(sys.argv[1], sys.argv[2])
    else:
        print("❌ 参数错误")
        print(__doc__)


if __name__ == "__main__":
    main()
