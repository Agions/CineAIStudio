# ClipFlowCut AI 故障排查手册

> 常见问题解决指南

---

## 🚨 Windows 用户必读

### Issue #10: dataclass mutable default 错误 ✅ 已修复

**错误信息**:

```
ValueError: mutable default <class 'PyQt6.QtGui.QColor'> for field background_color is not allowed: use default_factory
```

**问题原因**:
旧版本的代码在 dataclass 中使用了 mutable 对象作为默认值，这是 Python 不允许的。

**解决方法**:

**方法 1: 更新到最新版本** (推荐)

```bash
# 拉取最新代码
cd ClipFlowCut
git pull origin main

# 删除旧环境
rm -rf .venv  # macOS/Linux
rmdir /s .venv  # Windows

# 创建新环境
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# 重新安装依赖
pip install --upgrade pip
pip install -r requirements.txt
```

**方法 2: 升级 Python**

确保使用 Python 3.12+:

```bash
# Windows
py --version

# macOS/Linux
python3 --version

# 如果版本低于 3.12，请下载并安装:
# https://www.python.org/downloads/
```

**方法 3: 清理缓存后重装**

```bash
# 清理 pip 缓存
pip cache purge

# 强制重新安装 PyQt6
pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip
pip install --upgrade PyQt6 PyQt6-Qt6 PyQt6-sip

# 重新安装所有依赖
pip install -r requirements.txt --upgrade --force-reinstall
```

---

## 🔧 常见问题

### 1. 所有功能都不可用

**问题**: 安装完成后，所有按钮点击都没有反应。

**原因**: 未配置 LLM API 密钥。

**解决**:

1. 获取 API 密钥:
   - 通义千问: https://bailian.console.aliyun.com/ （推荐）
   - Kimi: https://platform.moonshot.cn/
   - GLM-5: https://open.bigmodel.cn/

2. 配置密钥:

```bash
# 方法 1: 环境变量 (推荐)
export QWEN_API_KEY="your-api-key"  # macOS/Linux
set QWEN_API_KEY=your-api-key        # Windows CMD
$env:QWEN_API_KEY="your-api-key"     # Windows PowerShell

# 方法 2: 编辑配置文件
cp config/llm.yaml.example config/llm.yaml
# 然后编辑 config/llm.yaml
```

3. 重启应用。

---

### 2. API 调用失败

**错误信息**:

```
ConnectionError: Failed to connect to API server
AuthenticationError: Invalid API key
```

**解决方法**:

**检查 API 密钥**:

```bash
# 验证密钥是否设置
echo $QWEN_API_KEY  # macOS/Linux
echo %QWEN_API_KEY%  # Windows CMD
echo $env:QWEN_API_KEY  # Windows PowerShell
```

**检查网络连接**:

```bash
ping dashscope.aliyuncs.com
curl -v https://dashscope.aliyuncs.com
```

**检查余额**:

- 登录阿里云控制台查看 API 余额
- 确保有足够的额度

---

### 3. 视频处理失败

**错误信息**:

```
RuntimeError: FFmpeg not found
FileNotFoundError: FFmpeg executable not found
```

**解决方法**:

**安装 FFmpeg**:

**macOS**:

```bash
brew install ffmpeg
```

**Windows**:

1. 下载 FFmpeg: https://ffmpeg.org/download.html
2. 解压到 `C:\ffmpeg`
3. 添加到环境变量:
   - 右键"我的电脑" → 属性 → 高级 → 环境变量
   - 在"系统变量"中找到 "Path"
   - 添加 `C:\ffmpeg\bin`

**验证安装**:

```bash
ffmpeg -version
```

---

### 4. 依赖安装失败

**错误信息**:

```
ERROR: Could not find a version that satisfies the requirement PyQt6
ERROR: No matching distribution found
```

**解决方法**:

**升级 pip**:

```bash
python -m pip install --upgrade pip
```

**使用国内镜像源**:

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**检查 Python 版本**:

```bash
python --version
# 确保 Python >= 3.12
```

---

### 5. 虚拟环境激活失败

**Windows**:

```cmd
# 命令行
.venv\Scripts\activate.bat

# PowerShell
.venv\Scripts\Activate.ps1
```

如果激活失败，可能是策略限制，运行:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**macOS/Linux**:

```bash
source .venv/bin/activate
```

---

## 🧪 调试技巧

### 启用详细日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

或者在环境变量中设置:

```bash
export LOG_LEVEL=DEBUG
```

### 检查版本

```bash
python scripts/check_version.py
```

### 运行测试

```bash
# 单元测试
pytest tests/ -v

# 集成测试 (需要 API 密钥)
pytest tests/ -v -m "integration"

# 覆盖率
pytest --cov=app tests/
```

### 检查 dataclass 问题

```bash
python scripts/check_dataclass.py
```

---

## 📦 重新安装指南

### 完全清理并重新安装

```bash
# 1. 删除现有环境
rm -rf .venv

# 2. 创建新环境
python3 -m venv .venv
source .venv/bin/activate

# 3. 升级 pip
pip install --upgrade pip

# 4. 从源码安装
pip install -e .

# 5. 运行检查
python scripts/check_version.py
pytest tests/ -v
```

---

## 📞 获取帮助

### 搜索问题

在解决之前，先搜索是否有相同问题:

- [GitHub Issues](https://github.com/Agions/ClipFlowCut/issues)
- [INSTALL.md](INSTALL.md) - 安装指南
- [DEVELOPER.md](DEVELOPER.md) - 开发指南

### 报告新问题

如果以上方法都无法解决，请提交 Issue:

1. 记录完整的错误信息
2. 提供系统信息:
   ```bash
   python --version
   pip list | grep PyQt6
   ffmpeg -version
   ```
3. 提供复现步骤
4. 提供日志文件 (如适用)

---

## ✅ 已知问题及修复版本

| 问题                    | 版本        | 状态        |
| ----------------------- | ----------- | ----------- |
| Windows dataclass 错误  | v2.0.0-rc.1 | ✅ 已修复   |
| 克隆地址错误 (Issue #9) | v2.0.0-rc.1 | ✅ 已修复   |
| 功能不可用 (未配置 API) | v2.0.0-rc.1 | ✅ 已有文档 |
| 安装验证问题            | v2.0.0-rc.1 | ✅ 已有文档 |

---

## 💡 最佳实践

1. **始终使用虚拟环境**
2. **定期更新依赖**:
   ```bash
   pip install --upgrade -r requirements.txt
   ```
3. **使用最新的代码**:
   ```bash
   git pull origin main
   ```
4. **定期运行测试**:
   ```bash
   pytest tests/ -v
   ```

---

**最后更新**: 2026-02-14
**版本**: v2.0.0-rc.1
