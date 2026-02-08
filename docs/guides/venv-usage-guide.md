# Project Venv Usage Guide

**Project**: Travel Planner
**Date**: 2026-02-01
**Status**: ✅ Required for all operations

---

## 🎯 核心原则

**所有Python操作必须使用项目本地venv**

### 为什么需要本地venv？

1. **依赖隔离**: 项目依赖与系统Python隔离
2. **版本一致**: 确保所有环境使用相同的依赖版本
3. **Agent兼容**: Agents执行时需要访问正确的Python环境
4. **可重现性**: 其他开发者可以复现相同环境

---

## 📦 Venv位置

```
/root/travel-planner/venv/
```

### 已安装的依赖

**核心依赖（4个主要包）**:
```
openmeteo-requests==1.7.5
openmeteo-sdk==1.25.0
requests-cache==1.2.1
retry-requests==2.0.0
```

**传递依赖（自动安装）**: 16个包（attrs, cattrs, certifi, charset-normalizer, flatbuffers, h11, idna, jh2, niquests, platformdirs, qh3, requests, typing_extensions, url-normalize, urllib3, urllib3-future, wassima）

**总计**: 20个包（见`requirements.txt`）

**注意**: ❌ 不包含numpy和pandas（不需要）

---

## ✅ 正确使用方式

### 方式1: 激活venv后执行 (推荐)

```bash
# 1. 进入项目目录
cd /root/travel-planner

# 2. 激活venv
source venv/bin/activate

# 3. 现在可以直接使用python3
python3 .claude/skills/openmeteo-weather/scripts/forecast.py 39.9 116.4 --days 3

# 4. 完成后可以deactivate (可选)
deactivate
```

### 方式2: 直接使用venv Python

```bash
# 不激活venv，直接使用venv中的python3
/root/travel-planner/venv/bin/python3 \
  /root/travel-planner/.claude/skills/openmeteo-weather/scripts/forecast.py \
  39.9 116.4 --days 3
```

### 方式3: 一行命令

```bash
# 在subshell中激活venv并执行
(cd /root/travel-planner && source venv/bin/activate && \
  python3 .claude/skills/openmeteo-weather/scripts/forecast.py 39.9 116.4 --days 3)
```

---

## ❌ 错误使用方式

### 不要使用系统Python

```bash
# ❌ 错误 - 使用系统Python
python3 .claude/skills/openmeteo-weather/scripts/forecast.py ...
# 结果: ModuleNotFoundError: openmeteo_requests

# ❌ 错误 - 使用/usr/bin/python3
/usr/bin/python3 .claude/skills/openmeteo-weather/scripts/forecast.py ...
# 结果: ModuleNotFoundError: openmeteo_requests
```

### 不要使用全局venv

```bash
# ❌ 错误 - 使用Claude全局venv
~/.claude/venv/bin/python3 script.py
# 结果: 依赖不存在

# ❌ 错误 - 使用root venv
/root/venv/bin/python3 script.py
# 结果: 错误的环境
```

---

## 🧪 验证venv正确使用

### 快速验证脚本

```bash
#!/bin/bash
# verify-venv.sh - 验证当前是否使用项目venv

cd /root/travel-planner
source venv/bin/activate

echo "Python executable: $(which python3)"
echo "Expected: /root/travel-planner/venv/bin/python3"
echo

echo "Testing openmeteo_requests import:"
python3 -c "import openmeteo_requests; print('✅ Module found')"
echo

echo "Testing skill execution:"
python3 .claude/skills/openmeteo-weather/scripts/forecast.py 39.9 116.4 --days 1 --location-name "Test" | head -10
```

---

## 🤖 Agent Integration

### Agents应该如何使用Skills？

当Agents调用skills时，必须确保使用项目venv：

#### Option A: Skill调用前激活venv

```python
import subprocess

# Agent代码中
result = subprocess.run([
    'bash', '-c',
    'cd /root/travel-planner && source venv/bin/activate && '
    'python3 .claude/skills/openmeteo-weather/scripts/forecast.py 39.9 116.4 --days 3'
], capture_output=True, text=True)
```

#### Option B: 直接使用venv Python

```python
import subprocess

result = subprocess.run([
    '/root/travel-planner/venv/bin/python3',
    '/root/travel-planner/.claude/skills/openmeteo-weather/scripts/forecast.py',
    '39.9', '116.4', '--days', '3'
], capture_output=True, text=True)
```

#### Option C: 通过Skill tool (推荐)

```python
# 使用Skill tool，它应该自动处理venv
self.use_tool('Skill', {
    'skill': 'openmeteo-weather',
    'args': '39.9 116.4 --days 3 --location-name Beijing'
})
```

---

## 📋 所有Skills的venv要求

| Skill | 需要venv | 依赖 | 测试状态 |
|-------|---------|------|---------|
| **openmeteo-weather** | ✅ 是 | openmeteo_requests | ✅ PASS |
| **gaode-maps** | ❌ 否 | 只需.env (API key) | ✅ PASS |
| **google-maps** | ❌ 否 | 只需.env (API key) | ✅ PASS |
| **duffel-flights** | ❌ 否 | 只需.env (API key) | ✅ PASS |
| **airbnb** | ❌ 否 | 只需requests (系统已有) | ✅ PASS |
| **rednote** | ❌ 否 | MCP-based (不是Python) | ✅ 已初始化 |
| **weather** (旧) | ⚠️ 已废弃 | 不使用 | ⚠️ DEPRECATED |
| **test-mcp** | ❌ 否 | MCP测试工具 | ⚠️ TEST ONLY |

**总结**:
- 只有**openmeteo-weather**严格需要项目venv
- 其他skills也应使用venv以保持一致性
- 所有8个skills已完整测试（2026-02-01）

---

## 🔧 开发工作流

### 新建skill script

1. 创建script时默认使用标准shebang:
   ```python
   #!/usr/bin/env python3
   ```

2. 文档中明确说明需要venv:
   ```markdown
   ## Usage

   **Requirements**: Project venv must be activated

   \`\`\`bash
   source /root/travel-planner/venv/bin/activate
   python3 script.py
   \`\`\`
   ```

3. 在SKILL.md中添加venv说明

### 添加新依赖

```bash
# 1. 激活venv
source /root/travel-planner/venv/bin/activate

# 2. 安装依赖
pip install new-package

# 3. 更新requirements.txt (可选)
pip freeze > requirements.txt

# 4. 测试
python3 -c "import new_package"
```

---

## 🚀 CI/CD和自动化

### 测试脚本模板

```bash
#!/bin/bash
# test-skills.sh - 测试所有skills

PROJECT_ROOT="/root/travel-planner"
cd "$PROJECT_ROOT"

# 激活venv
source venv/bin/activate

# 测试每个skill
echo "Testing openmeteo-weather..."
python3 .claude/skills/openmeteo-weather/scripts/forecast.py 39.9 116.4 --days 1

echo "Testing gaode-maps..."
python3 .claude/skills/gaode-maps/scripts/poi_search.py keyword "test" "北京" "" 1

# ... 其他skills
```

### Agent测试模板

```python
#!/usr/bin/env python3
"""Test agent with skills using project venv."""

import subprocess
import os

def run_with_venv(command):
    """Run command with project venv activated."""
    venv_activate = 'source /root/travel-planner/venv/bin/activate'
    full_command = f'{venv_activate} && {command}'

    result = subprocess.run(
        ['bash', '-c', full_command],
        capture_output=True,
        text=True,
        cwd='/root/travel-planner'
    )
    return result

# 测试
result = run_with_venv(
    'python3 .claude/skills/openmeteo-weather/scripts/forecast.py 39.9 116.4 --days 1'
)
print(result.stdout)
```

---

## 🐛 故障排查

### 问题1: ModuleNotFoundError

```
ModuleNotFoundError: No module named 'openmeteo_requests'
```

**原因**: 没有使用项目venv

**解决**:
```bash
source /root/travel-planner/venv/bin/activate
# 现在重新运行
```

### 问题2: 错误的Python路径

```bash
# 检查当前Python
which python3
# 应该是: /root/travel-planner/venv/bin/python3
# 不应该是: /usr/bin/python3
```

**解决**:
```bash
source /root/travel-planner/venv/bin/activate
```

### 问题3: Agent无法访问venv

**症状**: Agents中skills失败，但直接测试成功

**诊断**:
```bash
# 运行诊断脚本
bash /root/travel-planner/scripts/debug-agent-skills.sh
```

**解决**: 确保agents使用以下方式之一调用skills:
1. 激活venv: `source venv/bin/activate && python3 script.py`
2. 直接使用venv Python: `/root/travel-planner/venv/bin/python3 script.py`

---

## 📚 相关文档

- `docs/AGENT-SKILLS-SOLUTION.md` - Agent-skills integration root cause analysis
- `docs/COMPLETE-TEST-REPORT.md` - 完整测试报告（8 skills + 8 agents）
- `scripts/debug-agent-skills.sh` - Environment diagnostic tool
- `requirements.txt` - 完整依赖清单（20个包）

---

## ✅ 检查清单

开始工作前确认:

- [ ] 已激活项目venv: `source venv/bin/activate`
- [ ] Python路径正确: `which python3` → `/root/travel-planner/venv/bin/python3`
- [ ] 依赖可用: `python3 -c "import openmeteo_requests"`
- [ ] 当前目录: `pwd` → `/root/travel-planner`

---

**记住**: 使用项目venv是**必需的**，不是可选的！

所有Python操作都应该从:
```bash
cd /root/travel-planner
source venv/bin/activate
```
开始。
