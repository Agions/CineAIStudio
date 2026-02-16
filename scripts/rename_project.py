#!/usr/bin/env python3
"""
项目名称统一脚本：将 CineFlow 替换为 CineFlow
"""

import os
import re
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 需要处理的文件扩展名
FILE_EXTENSIONS = [
    '.py', '.md', '.txt', '.json', '.yaml', '.yml',
    '.html', '.css', '.js', '.ts', '.vue', '.jsx', '.tsx',
    '.xml', '.cfg', '.ini', '.toml'
]

# 需要跳过的目录
SKIP_DIRS = [
    '.git', '__pycache__', '.pytest_cache', '.mypy_cache',
    'node_modules', 'dist', 'build', '.idea', '.vscode',
    'venv', '.venv', 'env', '.env'
]

# 替换映射
REPLACEMENTS = [
    ('CineFlow', 'CineFlow'),
    ('cineflow', 'cineflow'),
    ('CINEFLOW', 'CINEFLOW'),
]


def should_process_file(filepath: Path) -> bool:
    """检查是否应该处理该文件"""
    # 跳过二进制文件
    if filepath.suffix.lower() not in FILE_EXTENSIONS:
        return False
    
    # 跳过特定目录
    for skip_dir in SKIP_DIRS:
        if skip_dir in filepath.parts:
            return False
    
    return True


def replace_in_file(filepath: Path) -> tuple[int, list[str]]:
    """
    在文件中替换文本
    返回: (替换次数, 修改的行列表)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # 跳过二进制文件
        return 0, []
    except Exception as e:
        print(f"❌ 无法读取文件 {filepath}: {e}")
        return 0, []
    
    original_content = content
    modified_lines = []
    total_replacements = 0
    
    # 执行替换
    for old, new in REPLACEMENTS:
        # 统计替换次数
        count = content.count(old)
        if count > 0:
            total_replacements += count
            
            # 记录修改的行
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if old in line:
                    modified_lines.append(f"  行 {i}: {line.strip()[:80]}...")
            
            # 执行替换
            content = content.replace(old, new)
    
    # 如果有修改，写回文件
    if content != original_content:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return total_replacements, modified_lines
        except Exception as e:
            print(f"❌ 无法写入文件 {filepath}: {e}")
            return 0, []
    
    return 0, []


def main():
    """主函数"""
    print("=" * 60)
    print("🎬 CineFlow 项目名称统一工具")
    print("=" * 60)
    print(f"\n项目目录: {PROJECT_ROOT}")
    print(f"处理扩展名: {', '.join(FILE_EXTENSIONS)}")
    print()
    
    # 统计
    processed_files = 0
    modified_files = 0
    total_replacements = 0
    
    # 遍历所有文件
    for filepath in PROJECT_ROOT.rglob('*'):
        if not filepath.is_file():
            continue
        
        if not should_process_file(filepath):
            continue
        
        processed_files += 1
        
        # 执行替换
        count, modified_lines = replace_in_file(filepath)
        
        if count > 0:
            modified_files += 1
            total_replacements += count
            
            # 显示相对路径
            rel_path = filepath.relative_to(PROJECT_ROOT)
            print(f"✅ {rel_path} ({count} 处替换)")
            
            # 显示修改的样本（最多3行）
            for line in modified_lines[:3]:
                print(line)
            if len(modified_lines) > 3:
                print(f"  ... 还有 {len(modified_lines) - 3} 处修改")
    
    # 输出统计
    print()
    print("=" * 60)
    print("📊 处理统计")
    print("=" * 60)
    print(f"处理文件数: {processed_files}")
    print(f"修改文件数: {modified_files}")
    print(f"总替换次数: {total_replacements}")
    print()
    
    if modified_files > 0:
        print("✨ 项目名称统一完成！")
        print()
        print("建议执行以下操作：")
        print("1. 检查修改是否正确")
        print("2. 运行测试确保功能正常")
        print("3. 提交更改到 Git")
    else:
        print("ℹ️ 没有找到需要替换的内容")
    
    print()


if __name__ == '__main__':
    main()
