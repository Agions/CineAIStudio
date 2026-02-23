"""
检查代码中的 dataclass mutable default 问题
用于验证 Issue #10 (Windows dataclass 错误) 是否已修复
"""

import ast
import sys
from typing import List, Dict, Tuple
from pathlib import Path


class DataclassChecker(ast.NodeVisitor):
    """检查 dataclass 中的 mutable default 问题"""

    def __init__(self):
        self.issues: List[Dict[str, any]] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """检查类定义"""
        # 检查是否有 @dataclass 装饰器
        has_dataclass = any(
            isinstance(decorator, ast.Name) and decorator.id == "dataclass"
            for decorator in node.decorator_list
        )

        if has_dataclass:
            self._check_dataclass_fields(node)

        self.generic_visit(node)

    def _check_dataclass_fields(self, node: ast.ClassDef) -> None:
        """检查 dataclass 字段"""
        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                field_name = stmt.target.id
                field_type = None

                # 提查类型注解
                if stmt.annotation:
                    if isinstance(stmt.annotation, ast.Name):
                        field_type = stmt.annotation.id
                    elif isinstance(stmt.annotation, ast.Subscript):
                        field_type = ast.unparse(stmt.annotation)

                # 检查默认值
                if stmt.value:
                    default_value = ast.unparse(stmt.value)

                    # 检查 mutable default
                    # 列表、字典、集合、QColor 等是 mutable 类型
                    mutable_patterns = [
                        "[]",        # 空列表
                        "{}",        # 空字典
                        "set()",     # 空集合
                        "QColor(",   # QColor 对象
                    ]

                    for pattern in mutable_patterns:
                        if pattern in default_value:
                            self.issues.append({
                                "file": self.current_file,
                                "line": node.lineno,
                                "class": node.name,
                                "field": field_name,
                                "type": field_type,
                                "default": default_value,
                                "issue": f"Mutable default: {default_value}"
                            })
                            break


def check_file(file_path: Path) -> List[Dict[str, any]]:
    """检查单个文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    try:
        tree = ast.parse(content, filename=str(file_path))
    except SyntaxError:
        return []

    checker = DataclassChecker()
    checker.current_file = str(file_path)
    checker.visit(tree)

    return checker.issues


def check_directory(directory: Path) -> List[Dict[str, any]]:
    """检查整个目录"""
    all_issues = []

    for py_file in directory.rglob("*.py"):
        # 跳过测试文件
        if "test_" in py_file.name:
            continue

        issues = check_file(py_file)
        all_issues.extend(issues)

    return all_issues


def main():
    """主函数"""
    import argparse
    from rich.console import Console

    parser = argparse.ArgumentParser(description="检查 dataclass mutable default 问题")
    parser.add_argument("path", nargs="?", default="app", help="要检查的文件或目录")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")

    args = parser.parse_args()
    console = Console()

    path = Path(args.path)

    if path.is_file():
        issues = check_file(path)
    elif path.is_dir():
        issues = check_directory(path)
    else:
        console.print(f"❌ 路径不存在: {path}")
        return 1

    if issues:
        console.print(f"\n❌ 发现 {len(issues)} 个问题:\n")

        for i, issue in enumerate(issues, 1):
            console.print(f"[{i}] {issue['file']}:{issue['line']}")
            console.print(f"    类: {issue.get('class', 'unknown')}")
            console.print(f"    字段: {issue['field']} : {issue.get('type', 'unknown')}")
            console.print(f"    默认值: {issue['default']}")
            console.print(f"    问题: {issue['issue']}\n")

            if args.verbose:
                console.print(f"    建议: 使用 default_factory 替代\n")

        console.print("\n💡 修复建议:\n")
        console.print("错误示例:\n")
        console.print("    @dataclass\n")
        console.print("    class MyClass:\n")
        console.print("        background_color: QColor = QColor(255, 255, 255)  # ❌ 错误\n")

        console.print("\n正确写法:\n")
        console.print("    from dataclasses import dataclass, field\n")
        console.print("    @dataclass\n")
        console.print("    class MyClass:\n")
        console.print("        background_color: QColor = field(default_factory=lambda: QColor(255, 255, 255))  # ✅\n")

        return 1
    else:
        console.print("✅ 未发现 dataclass mutable default 问题!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
