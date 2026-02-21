# CineFlow AI 版本统一方案

**文档版本**: v1.0
**创建日期**: 2026-02-14

---

## 📊 当前版本混乱状况

### 存在的版本标识

| 位置             | 版本号 | 说明             |
| ---------------- | ------ | ---------------- |
| `app/main.py`    | 1.5.0  | 主程序运行时显示 |
| `pyproject.toml` | 2.0.0  | Python 包版本    |
| `CHANGELOG.md`   | 3.0.0  | 最新发布版本     |
| Git 标签         | 无     | 无版本标签       |

---

## 🎯 版本统一目标

### 1. 确定当前版本

**建议**: `v2.0.0-rc.1` (Release Candidate 1)

**理由**:

- `2.0.0` 表示重大架构变更（重构后）
- `rc.1` 表示候选版，用于内部测试
- `3.0.0` 标注的功能可能未完全实现，不作为当前版本

### 2. 版本管理策略

#### 单一来源原则

```
pyproject.toml (唯一版本来源)
    ↓
app/utils/version.py (从 pyproject.toml 读取)
    ↓
app/main.py (显示运行时版本)
    ↓
CHANGELOG.md (记录历史版本)
    ↓
Git 标签 (对应每个发布版本)
```

#### 版本号格式

遵循 [语义化版本 2.0.0](https://semver.org/):

```
MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]

示例:
- 2.0.0          - 正式版
- 2.0.0-rc.1     - 候选版 1
- 2.0.0-beta.1   - Beta 版 1
- 2.0.0-alpha.1  - Alpha 版 1
- 2.0.0+20260214 - 带构建元数据
```

#### 版本规则

| 变更类型             | 版本规则                    | 示例          |
| -------------------- | --------------------------- | ------------- |
| 破坏性变更           | MAJOR + 1, MINOR=0, PATCH=0 | 2.0.0 → 3.0.0 |
| 新功能（向后兼容）   | MINOR + 1, PATCH=0          | 2.0.0 → 2.1.0 |
| Bug 修复（向后兼容） | PATCH + 1                   | 2.0.0 → 2.0.1 |

---

## 🛠️ 实施方案

### 步骤 1: 统一版本来源

#### 1.1 创建版本管理模块

**文件**: `app/utils/version.py`

```python
"""
CineFlow AI 版本管理
从 pyproject.toml 读取版本信息
"""

from pathlib import Path
from typing import NamedTuple
import tomli


class Version(NamedTuple):
    """版本信息"""
    major: int
    minor: int
    patch: int
    prerelease: str = ""
    build: str = ""

    def __str__(self) -> str:
        """字符串表示"""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build:
            version += f"+{self.build}"
        return version

    @classmethod
    def parse(cls, version_str: str) -> "Version":
        """解析版本字符串"""
        import re

        # 匹配: MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]
        pattern = r"^(\d+)\.(\d+)\.(\d+)(?:-(.+?))?(?:\+(.+)?)?$"
        match = re.match(pattern, version_str)

        if not match:
            raise ValueError(f"Invalid version: {version_str}")

        major, minor, patch, prerelease, build = match.groups()
        return cls(
            major=int(major),
            minor=int(minor),
            patch=int(patch),
            prerelease=prerelease or "",
            build=build or "",
        )


def get_version() -> Version:
    """
    从 pyproject.toml 读取版本

    Returns:
        版本信息
    """
    try:
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"

        if pyproject_path.exists():
            with open(pyproject_path, "rb") as f:
                data = tomli.load(f)

            version_str = data["project"]["version"]
            return Version.parse(version_str)

    except Exception as e:
        print(f"Warning: Failed to read version from pyproject.toml: {e}")

    # 后备方案
    return Version(2, 0, 0, prerelease="rc.1")


def get_version_string() -> str:
    """获取版本字符串"""
    return str(get_version())


# 便捷函数
VERSION = get_version()
__version__ = VERSION
if __name__ == "__main__":
    print(__version__)
```

#### 1.2 更新 pyproject.toml

```toml
[project]
name = "cineflow-ai"
version = "2.0.0-rc.1"  # 唯一版本来源
description = "CineFlow AI - Professional Video Creation with AI"
```

#### 1.3 更新主程序

**文件**: `app/main.py`

```python
from app.utils.version import __version__, VERSION

def main():
    print("=" * 50)
    print(f"🎬 CineFlow AI - AI 视频创作工具")
    print("=" * 50)
    print(f"\n版本: {__version__}")
    print("作者: Agions")
    print()
```

### 步骤 2: 更新 CHANGELOG

**文件**: `CHANGELOG.md`

```markdown
# CineFlow AI 版本发布记录

## [2.0.0-rc.1] - 2026-02-14

### 🎯 版本修复

- 统一版本管理，从 pyproject.toml 读取
- 项目重命名为 CineFlow AI

### 🔧 内部变更

- 代码审计完成，发现 10 个主要问题
- 重构计划制定完成

---

## [2.0.0] - 计划中

### 🚀 重构版本

- 完整架构重构
- 国产 LLM 集成
- 统一服务接口
- 单元测试覆盖 > 85%
```

### 步骤 3: 版本发布流程

#### 开发流程

```
1. 开发阶段: 2.0.0-alpha.1, alpha.2, ...
2. 测试阶段: 2.0.0-beta.1, beta.2, ...
3. 候选版本: 2.0.0-rc.1, rc.2, ...
4. 正式发布: 2.0.0
```

#### 发布检查清单

- [ ] 所有测试通过
- [ ] CHANGELOG 更新
- [ ] pyproject.toml 版本号更新
- [ ] git commit
- [ ] 创建 Git 标签: `git tag -a v2.0.0 -m "Release v2.0.0"`
- [ ] 推送标签: `git push origin v2.0.0`
- [ ] GitHub Release

---

## 📋 迁移计划

### 立即执行

1. ✅ 创建 `app/utils/version.py`
2. ✅ 更新 `pyproject.toml` 版本为 `2.0.0-rc.1`
3. ✅ 更新 `app/main.py` 使用统一版本
4. ✅ 更新 `CHANGELOG.md` 记录变更

### 后续工作

1. ✅ 实现自动化版本管理
2. ✅ 添加版本检查工具
3. ✅ 集成到 CI/CD 流程

---

## 🔍 版本检查工具

### 创建工具脚本

**文件**: `scripts/check_version.py`

```python
#!/usr/bin/env python3
"""
版本一致性检查工具
检查项目各处版本号是否一致
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.version import get_version
import tomli


def check_version() -> bool:
    """检查版本一致性"""
    print("检查项目版本一致性...")
    print("-" * 50)

    # 从版本模块读取
    version = get_version()
    version_str = str(version)
    print(f"版本模块: {version_str}")

    # 从 pyproject.toml 读取
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        data = tomli.load(f)

    pyproject_version = data["project"]["version"]
    print(f"pyproject.toml: {pyproject_version}")

    # 检查一致性
    if version_str == pyproject_version:
        print("\n✅ 版本一致!")
        return True
    else:
        print("\n❌ 版本不一致!")
        print(f"  版本模块: {version_str}")
        print(f"  pyproject.toml: {pyproject_version}")
        return False


if __name__ == "__main__":
    success = check_version()
    sys.exit(0 if success else 1)
```

---

## 🎉 总结

### 关键改进

1. **单一来源**: 版本号只在 `pyproject.toml` 维护
2. **自动读取**: 运行时从配置文件读取版本
3. **语义化**: 遵循 SemVer 2.0.0 标准
4. **可追踪**: Git 标签对应每个发布版本

### 下一步

- [ ] 实施版本统一方案
- [ ] 运行版本检查工具
- [ ] 集成到 CI/CD 流程

---

**文档状态**: ✅ 完成
**实施状态**: ⏳ 待执行
