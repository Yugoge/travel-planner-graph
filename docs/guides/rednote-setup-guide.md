# RedNote MCP 初始化指南

**目标**: 配置RedNote (小红书) MCP服务器以访问旅游内容

---

## 前提条件

✅ **必需**:
- Node.js ≥ 16
- npm ≥ 7
- 小红书账号 (用于登录认证)
- 稳定的网络连接

✅ **可选**:
- VPN/代理 (如果在中国境外访问小红书)

---

## 步骤 1: 检查环境

```bash
# 检查 Node.js 版本
node --version
# 输出应该 >= v16.0.0

# 检查 npm 版本
npm --version
# 输出应该 >= 7.0.0
```

如果版本不符合要求，先更新 Node.js：
```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# 或使用 nvm
nvm install 20
nvm use 20
```

---

## 步骤 2: 安装 RedNote MCP

```bash
# 全局安装 rednote-mcp
npm install -g rednote-mcp

# 验证安装
which rednote-mcp
# 输出: /usr/local/bin/rednote-mcp 或类似路径

rednote-mcp --version
# 输出版本号
```

**如果安装失败**:
```bash
# 清理 npm 缓存重试
npm cache clean --force
npm install -g rednote-mcp

# 或使用 sudo (Linux/Mac)
sudo npm install -g rednote-mcp
```

---

## 步骤 3: 初始化认证 (关键步骤)

```bash
# 启动交互式登录流程
rednote-mcp init
```

**会发生什么**:

1. **浏览器自动打开** → Playwright会启动一个浏览器窗口
2. **跳转到小红书登录页** → https://www.xiaohongshu.com
3. **手动登录** → 使用你的小红书账号登录
   - 可以用手机号 + 验证码
   - 或者扫码登录
   - 完成任何必要的验证 (滑块、短信验证等)
4. **等待Cookie保存** → 登录成功后，脚本会自动保存cookies
5. **浏览器关闭** → Cookie保存完成后浏览器会关闭

**预期输出**:
```
Starting login process...
Opening browser for login...
Waiting for login completion...
Login successful!
Cookies saved to: /root/.mcp/rednote/cookies.json
```

**Cookie保存位置**: `~/.mcp/rednote/cookies.json`

---

## 步骤 4: 配置 MCP 服务器

### 选项 A: 使用 Claude Desktop (推荐)

编辑配置文件:
```bash
# Mac
nano ~/.config/Claude/claude_desktop_config.json

# Linux
nano ~/.config/Claude/claude_desktop_config.json

# Windows
notepad %APPDATA%\Claude\claude_desktop_config.json
```

添加 RedNote MCP 配置:
```json
{
  "mcpServers": {
    "rednote": {
      "command": "rednote-mcp",
      "args": ["--stdio"]
    }
  }
}
```

**如果已有其他MCP服务器**:
```json
{
  "mcpServers": {
    "rednote": {
      "command": "rednote-mcp",
      "args": ["--stdio"]
    },
    "gaode-maps": {
      "command": "npx",
      "args": ["-y", "@agentic/gaode-maps"]
    }
  }
}
```

保存文件后**重启 Claude Desktop**。

### 选项 B: 使用 Claude Code (当前环境)

Claude Code 会自动检测全局安装的 MCP 服务器。只需确保:

1. ✅ `rednote-mcp` 已全局安装
2. ✅ Cookie文件存在于 `~/.mcp/rednote/cookies.json`
3. ✅ 使用正确的MCP工具名称 (见下方)

---

## 步骤 5: 验证安装

### 测试 1: 检查 Cookie 文件

```bash
# 检查 cookie 文件是否存在
ls -lh ~/.mcp/rednote/cookies.json

# 查看 cookie 内容 (确认有数据)
cat ~/.mcp/rednote/cookies.json | jq . | head -20
```

**预期输出**: JSON格式的cookie数组

### 测试 2: 直接运行 MCP 服务器

```bash
# 测试 MCP 服务器是否能启动
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | rednote-mcp --stdio
```

**预期输出**: JSON-RPC响应，包含工具列表

### 测试 3: 在 Claude 中测试工具

使用以下MCP工具测试:

```javascript
// 测试搜索功能
mcp__rednote__search_notes({
  keywords: "成都美食",
  limit: 5
})
```

**预期结果**:
- 返回5条笔记
- 包含标题、作者、内容摘要、点赞数、URL

---

## 常见问题排查

### 问题 1: `rednote-mcp: command not found`

**原因**: npm全局bin目录不在PATH中

**解决**:
```bash
# 查找 npm 全局 bin 目录
npm config get prefix
# 输出: /usr/local (或其他路径)

# 添加到 PATH (bash)
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 或 (zsh)
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### 问题 2: 浏览器打不开或Playwright错误

**原因**: Playwright浏览器未安装

**解决**:
```bash
# 安装 Playwright 浏览器
npx playwright install chromium

# 或完整安装
npx playwright install
```

### 问题 3: Cookie保存失败

**症状**: 登录成功但提示"Cookies not saved"

**解决**:
```bash
# 手动创建目录
mkdir -p ~/.mcp/rednote

# 检查目录权限
ls -ld ~/.mcp/rednote
# 应该有写入权限

# 再次运行 init
rednote-mcp init
```

### 问题 4: 登录后立即被退出

**原因**: 小红书检测到自动化登录

**解决**:
1. 使用真实手机号登录 (不要用虚拟号)
2. 完成所有验证步骤 (滑块、短信)
3. 登录后等待10-15秒再关闭浏览器
4. 必要时使用VPN (如果在境外)

### 问题 5: Cookie过期

**症状**: 之前能用，现在返回"Not logged in"错误

**解决**:
```bash
# 重新认证
rednote-mcp init

# Cookie会被覆盖更新
```

**建议**: 每30天重新认证一次

### 问题 6: MCP工具调用失败

**症状**: 工具未找到或参数错误

**检查**:
```bash
# 1. 确认工具名称正确
# 正确: mcp__rednote__search_notes
# 错误: mcp__rednote__searchNotes

# 2. 确认参数名称正确
# 正确: keywords (复数), url
# 错误: keyword (单数), note_url

# 3. 查看详细文档
cat /root/travel-planner/.claude/skills/rednote/SKILL.md
```

---

## 快速测试脚本

保存为 `test-rednote.sh`:

```bash
#!/bin/bash
echo "=== RedNote MCP 测试 ==="

echo -e "\n1. 检查 rednote-mcp 安装"
which rednote-mcp && echo "✅ 已安装" || echo "❌ 未安装"

echo -e "\n2. 检查 Cookie 文件"
if [ -f ~/.mcp/rednote/cookies.json ]; then
    echo "✅ Cookie 文件存在"
    echo "大小: $(du -h ~/.mcp/rednote/cookies.json | cut -f1)"
else
    echo "❌ Cookie 文件不存在"
fi

echo -e "\n3. 测试 MCP 服务器启动"
timeout 5s bash -c 'echo "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\"}" | rednote-mcp --stdio' && echo "✅ MCP 服务器正常" || echo "❌ MCP 服务器异常"

echo -e "\n=== 测试完成 ==="
```

运行:
```bash
chmod +x test-rednote.sh
./test-rednote.sh
```

---

## MCP 工具使用指南

### 工具 1: 搜索笔记 (search_notes)

```javascript
// 基础搜索
mcp__rednote__search_notes({
  keywords: "北京旅游攻略",
  limit: 10
})

// 高级搜索 (更多结果)
mcp__rednote__search_notes({
  keywords: "上海网红餐厅推荐",
  limit: 50
})
```

**关键词建议**:
- 使用中文: "成都" 而不是 "Chengdu"
- 添加修饰词: "必去", "推荐", "攻略", "小众"
- 具体化: "成都火锅推荐" 比 "成都美食" 更精准

### 工具 2: 获取笔记内容 (get_note_content)

```javascript
// 从搜索结果中获取详细内容
mcp__rednote__get_note_content({
  url: "https://www.xiaohongshu.com/explore/65a1b2c3d4e5f6789"
})

// 支持短链接
mcp__rednote__get_note_content({
  url: "https://xhslink.com/abc123"
})
```

**返回数据**:
- 完整标题和内容
- 所有图片URL
- 标签列表
- 作者信息
- 点赞/评论/收藏数

### 工具 3: 获取评论 (get_note_comments)

```javascript
mcp__rednote__get_note_comments({
  url: "https://www.xiaohongshu.com/explore/65a1b2c3d4e5f6789"
})
```

**用途**:
- 验证餐厅/景点质量
- 查看最新用户反馈
- 获取实用建议和tips

### 工具 4: 手动登录 (login)

```javascript
// 触发交互式登录 (等同于 rednote-mcp init)
mcp__rednote__login()
```

**注意**: 优先使用CLI命令 `rednote-mcp init`

---

## 最佳实践

### 1. 搜索策略

```javascript
// ✅ 好的做法: 多关键词 + 高limit
mcp__rednote__search_notes({ keywords: "杭州西湖旅游攻略", limit: 30 })
mcp__rednote__search_notes({ keywords: "杭州西湖最佳拍照点", limit: 20 })
mcp__rednote__search_notes({ keywords: "杭州西湖周边美食", limit: 20 })

// ❌ 差的做法: 单关键词 + 低limit
mcp__rednote__search_notes({ keywords: "杭州", limit: 5 })
```

### 2. 内容筛选

```javascript
// 搜索后筛选高质量内容
// 1. 点赞数 > 5000
// 2. 评论数 > 100
// 3. 发布时间 < 6个月
// 4. 作者粉丝数 > 1000
```

### 3. 交叉验证

```javascript
// RedNote 搜索 → 获取详细内容
let notes = mcp__rednote__search_notes({ keywords: "成都宽窄巷子", limit: 20 })

// 提取地址 → Gaode Maps验证
let topNote = notes[0]
let content = mcp__rednote__get_note_content({ url: topNote.url })

// 使用高德地图确认位置和营业时间
mcp__plugin_amap_maps_amap_maps__maps_poi_search({
  keywords: "宽窄巷子",
  city: "成都"
})
```

---

## 安全提示

⚠️ **Cookie安全**:
- Cookie文件包含登录凭证，**不要提交到Git**
- 定期更换密码 (如果怀疑泄露)
- 不要在公共机器上保存Cookie

⚠️ **账号安全**:
- 避免频繁自动化登录 (可能被封号)
- 合理控制API调用频率
- 遵守小红书使用条款

⚠️ **隐私保护**:
- 不要用MCP工具访问私密内容
- 注意Cookie文件权限: `chmod 600 ~/.mcp/rednote/cookies.json`

---

## 下一步

初始化完成后:

1. ✅ 阅读完整文档: `.claude/skills/rednote/SKILL.md`
2. ✅ 查看使用示例: `.claude/skills/rednote/examples/`
3. ✅ 测试travel-planner集成 (见下方)

---

## Travel Planner 集成测试

RedNote已集成到4个agents，测试方法:

```bash
# 启动 /plan 命令测试完整工作流
# RedNote会在以下场景自动使用:

# 1. attractions agent - 景点推荐
# 搜索: "成都必去景点", "成都小众景点"

# 2. meals agent - 餐厅推荐
# 搜索: "上海本地人推荐美食", "上海网红餐厅"

# 3. shopping agent - 购物推荐
# 搜索: "北京购物攻略", "北京特产推荐"

# 4. entertainment agent - 娱乐推荐
# 搜索: "杭州夜生活", "杭州酒吧推荐"
```

---

## 总结

**初始化步骤**:
1. ✅ `npm install -g rednote-mcp`
2. ✅ `rednote-mcp init` (浏览器登录)
3. ✅ 配置 Claude Desktop (可选)
4. ✅ 测试工具调用

**关键文件**:
- Cookie: `~/.mcp/rednote/cookies.json`
- 配置: `~/.config/Claude/claude_desktop_config.json`
- 文档: `/root/travel-planner/.claude/skills/rednote/SKILL.md`

**支持**:
- GitHub: https://github.com/iFurySt/RedNote-MCP
- 问题反馈: 在项目issue中报告

---

✅ **准备就绪！开始使用RedNote MCP探索中国旅游内容吧！**
