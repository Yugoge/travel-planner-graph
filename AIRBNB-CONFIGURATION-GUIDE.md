# Airbnb MCP 配置指南

## 问题：robots.txt 阻止

Airbnb 默认会被 robots.txt 阻止。你会看到这个错误：

```json
{
  "error": "This path is disallowed by Airbnb's robots.txt"
}
```

## 解决方案：配置 MCP 服务器

### 步骤 1: 找到 Claude Desktop 配置文件

```bash
~/.config/Claude/claude_desktop_config.json
```

### 步骤 2: 添加 Airbnb MCP 配置

打开配置文件，添加以下内容：

```json
{
  "mcpServers": {
    "airbnb": {
      "command": "npx",
      "args": ["-y", "@openbnb/mcp-server-airbnb", "--ignore-robots-txt"],
      "env": {}
    }
  }
}
```

**关键参数**: `--ignore-robots-txt`

### 步骤 3: 重启 Claude Desktop

关闭并重新打开 Claude Desktop，让配置生效。

### 步骤 4: 测试

在 Claude Code 中运行：

```bash
python3 /root/travel-planner/.claude/skills/airbnb/scripts/search.py \
  "Paris, France" \
  --checkin "2026-03-01" \
  --checkout "2026-03-05"
```

应该返回房源列表，而不是 robots.txt 错误。

---

## ⚠️  法律声明

### 使用风险

- ⚠️  绕过 robots.txt 可能违反 Airbnb 服务条款
- ⚠️  网页抓取可能导致 IP 被封禁
- ⚠️  仅建议用于个人研究和测试
- ⚠️  商业使用需要法律评估

### 推荐使用场景

✅ **可以使用**:
- 个人旅行规划
- 学习和研究
- 测试和开发

❌ **不建议使用**:
- 商业数据采集
- 大规模爬取
- 自动化预订系统

---

## 完整配置文件示例

如果你有多个 MCP 服务器，完整配置可能如下：

```json
{
  "mcpServers": {
    "airbnb": {
      "command": "npx",
      "args": ["-y", "@openbnb/mcp-server-airbnb", "--ignore-robots-txt"],
      "env": {}
    },
    "gaode-maps": {
      "url": "https://mcp.amap.com/mcp?key=YOUR_AMAP_API_KEY"
    },
    "weather": {
      "command": "npx",
      "args": ["-y", "@dangahagan/weather-mcp"],
      "env": {}
    },
    "eventbrite": {
      "command": "npx",
      "args": ["-y", "@mseep/eventbrite-mcp"],
      "env": {
        "EVENTBRITE_API_KEY": "YOUR_KEY_HERE"
      }
    }
  }
}
```

---

## 故障排除

### 问题 1: 仍然看到 robots.txt 错误

**解决**:
1. 确认配置文件中有 `--ignore-robots-txt` 参数
2. 确认重启了 Claude Desktop
3. 检查配置文件的 JSON 格式是否正确

### 问题 2: MCP 服务器无法启动

**解决**:
1. 确认已安装 Node.js 和 npx
2. 运行 `npx -y @openbnb/mcp-server-airbnb --version` 测试
3. 检查 Claude Desktop 日志

### 问题 3: 搜索结果为空

**可能原因**:
- 搜索参数不正确
- 日期格式错误 (应为 YYYY-MM-DD)
- Airbnb 在该地区没有房源

---

**配置完成后，Airbnb 技能将完全可用！**
