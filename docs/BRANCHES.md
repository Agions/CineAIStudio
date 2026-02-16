# CineFlow 分支管理说明

> 每个版本独立分支，代码完全保留

---

## 分支结构

```
main (主分支 - 最新开发)
│
├── release/v2.0.0          # v2.0.0 基础版本
│   └── 单Agent架构，CLI界面
│
├── release/v3.0-beta1      # v3.0.0-beta1 多Agent架构
│   └── 6个Agent + 核心服务 + 多LLM
│
├── release/v3.0-beta2      # v3.0.0-beta2 PyQt6 UI
│   └── Agent监控 + 项目管理
│
├── release/v3.0-beta3      # v3.0.0-beta3 代码优化
│   └── 性能优化 + 异步初始化
│
└── [继续开发...]
```

---

## 分支列表

| 分支 | 版本 | 说明 | 提交 |
|------|------|------|------|
| `release/v2.0.0` | v2.0.0 | 基础版本 | v2.0.0 |
| `release/v3.0-beta1` | v3.0.0-beta1 | 多Agent架构 | 8a12093 |
| `release/v3.0-beta2` | v3.0.0-beta2 | PyQt6 UI | b4192d4 |
| `release/v3.0-beta3` | v3.0.0-beta3 | 代码优化 | a16f529 |
| `main` | v3.0.0-beta3-docs | 文档+工具 | latest |

---

## 快速切换

### 使用切换工具

```bash
# 查看所有版本
python scripts/switch_version.py --list

# 切换到v2.0.0
python scripts/switch_version.py 2.0.0

# 切换到v3.0-beta1
python scripts/switch_version.py 3.0-beta1

# 切换到v3.0-beta2
python scripts/switch_version.py 3.0-beta2

# 切换到v3.0-beta3
python scripts/switch_version.py 3.0-beta3

# 返回主分支
python scripts/switch_version.py main
```

### 使用Git命令

```bash
# 查看所有分支
git branch -a

# 切换到v2.0.0分支
git checkout release/v2.0.0

# 切换到v3.0-beta1分支
git checkout release/v3.0-beta1

# 切换到v3.0-beta2分支
git checkout release/v3.0-beta2

# 切换到v3.0-beta3分支
git checkout release/v3.0-beta3

# 返回主分支
git checkout main
```

---

## 版本对比

```bash
# 对比v2.0.0和v3.0-beta3
git diff release/v2.0.0..release/v3.0-beta3 --stat

# 对比v3.0-beta1和v3.0-beta2
git diff release/v3.0-beta1..release/v3.0-beta2 --stat

# 使用对比工具
python scripts/compare_versions.py 2.0.0 3.0-beta3
```

---

## 各分支代码特点

### release/v2.0.0

```
特点:
- 单Agent架构
- 基础视频处理
- CLI命令行界面
- 简单LLM调用

文件数: 131
代码行: 50,495
```

### release/v3.0-beta1

```
特点:
- 6个专业Agent
- 核心服务层
- 多LLM支持
- 无UI(命令行)

文件数: 170
代码行: 62,159
新增: Agent系统 + 核心服务
```

### release/v3.0-beta2

```
特点:
- PyQt6图形界面
- Agent监控中心
- 项目管理页面
- 暗色主题

文件数: 172
代码行: 62,584
新增: UI层
```

### release/v3.0-beta3

```
特点:
- 代码精益求精
- 性能优化
- 异步初始化
- 样式系统

文件数: 173
代码行: 63,465
优化: LLM/Video/UI
```

---

## 开发工作流

### 查看历史版本

```bash
# 切换到v2.0查看旧代码
python scripts/switch_version.py 2.0.0
# ...查看代码...

# 返回主分支继续开发
python scripts/switch_version.py main
```

### 对比学习

```bash
# 对比学习架构演进
python scripts/compare_versions.py 2.0.0 3.0-beta1
python scripts/compare_versions.py 3.0-beta1 3.0-beta2
```

### 修复旧版本

```bash
# 切换到旧版本分支
git checkout release/v3.0-beta1

# 创建修复分支
git checkout -b hotfix/v3.0-beta1-fix

# 修复代码...
git add -A
git commit -m "fix: xxx"

# 返回主分支
git checkout main
```

---

## 推送分支到远程

```bash
# 推送所有版本分支
git push origin release/v2.0.0
git push origin release/v3.0-beta1
git push origin release/v3.0-beta2
git push origin release/v3.0-beta3

# 或者一次性推送
git push origin --all
```

---

## 创建版本标签

```bash
# 创建标签
python scripts/switch_version.py --create-tags

# 或者手动创建
git tag -a v3.0-beta1 8a12093 -m "v3.0.0-beta1 多Agent架构"
git tag -a v3.0-beta2 b4192d4 -m "v3.0.0-beta2 PyQt6 UI"
git tag -a v3.0-beta3 a16f529 -m "v3.0.0-beta3 代码优化"

# 推送标签
git push origin --tags
```

---

## 注意事项

1. **每个分支独立** - 切换分支不会丢失其他分支的代码
2. **提交到正确分支** - 新功能提交到main，旧版本修复提交到对应分支
3. **定期同步** - 旧版本分支可以定期从main合并更新
4. **标签管理** - 重要版本打标签，方便回溯

---

## 常见问题

### Q: 切换分支后代码不见了？

A: 代码还在原来的分支，切换回去即可：
```bash
git checkout release/v3.0-beta1
```

### Q: 可以在旧版本分支上修改吗？

A: 可以，但建议创建新分支：
```bash
git checkout release/v3.0-beta1
git checkout -b feature/old-version-fix
# 修改...
git commit -m "fix: xxx"
```

### Q: 如何合并旧版本的修复到main？

A: 使用cherry-pick：
```bash
git checkout main
git cherry-pick <commit-hash>
```

---

*最后更新: 2025-01-20*
