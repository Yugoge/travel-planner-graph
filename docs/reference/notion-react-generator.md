# Notion-Style React Travel Plan Generator

## Overview

全新的 Notion 风格 React 单页面应用生成器,将 skeleton 数据和 agent 输出转换为精美的交互式旅行计划 HTML。

## 特性

### 🎨 UI 设计
- **Notion 风格界面**: 极简、现代、专业
- **响应式设计**: 完美适配移动端、平板、桌面
- **双视图模式**:
  - **Kanban View**: 看板式布局,卡片展示每日行程
  - **Timeline View**: 时间轴视图,按时间顺序展示活动

### 📱 交互体验
- **侧边栏导航**:
  - 多城市/行程折叠式导航
  - 选中项左侧黑线高亮
  - 移动端抽屉式侧边栏
- **Cover 图片**: 每个城市/日期都有封面图
- **Icon + 标题**: Notion 风格的 emoji 图标
- **轻量卡片**: 无边框设计,微弱阴影,悬停效果
- **链接集成**: Google Maps, 高德地图, 小红书, Booking 等

### 📊 数据展示
- **Property Grid**: 行程概览属性表格
- **Donut 图表**: 预算分类环形图
- **时间轴**: 精确到分钟的活动安排
- **分类标签**: 餐饮、景点、娱乐、住宿

## 使用方法

### 1. 生成 Notion React HTML

```bash
python3 scripts/generate-notion-react.py <plan-id>
```

**示例**:
```bash
python3 scripts/generate-notion-react.py beijing-exchange-bucket-list-20260202-232405
```

**输出**:
- 文件: `travel-plan-notion-<plan-id>.html`
- 大小: ~40-50 KB (包含完整 React 应用)
- 格式: 单文件 HTML (嵌入 React + Babel)

### 2. 生成并部署到 GitHub Pages

```bash
bash scripts/generate-notion-and-deploy.sh <plan-id>
```

**示例**:
```bash
bash scripts/generate-notion-and-deploy.sh beijing-exchange-bucket-list-20260202-232405
```

**自动执行**:
1. ✅ 生成 Notion React HTML
2. ✅ 验证 HTML 结构
3. ✅ 部署到 GitHub Pages (gh-pages 分支)
4. ✅ 输出访问链接

**部署位置**:
```
https://<username>.github.io/<repo>/<plan-id>/<date>/
```

## 数据结构

### 输入数据 (从 skeleton + agents 合并)

生成器从以下文件读取数据:

```
data/<plan-id>/
├── plan-skeleton.json      # 基础行程结构
├── attractions.json         # 景点数据 (attractions-agent)
├── meals.json              # 餐饮数据 (meals-agent)
├── accommodation.json      # 住宿数据 (accommodation-agent)
├── entertainment.json      # 娱乐数据 (entertainment-agent)
├── transportation.json     # 交通数据 (transportation-agent)
├── timeline.json           # 时间轴数据 (timeline-agent)
└── budget.json            # 预算数据 (budget-agent)
```

### 输出数据结构 (PLAN_DATA)

嵌入 HTML 的 JavaScript 对象:

```javascript
const PLAN_DATA = {
  trip_summary: {
    trip_type: "itinerary" | "bucket_list",
    description: "Travel Plan",
    base_location: "Beijing",
    period: "2026-02-25 to 2026-06-30",
    travelers: "1 adult (solo travel)",
    budget_per_trip: "€500",
    preferences: "..."
  },
  trips: [
    {
      name: "Harbin",              // 城市名称
      days_label: "2 days",        // 天数标签
      cover: "https://...",        // 城市封面图
      days: [
        {
          day: 1,
          date: "2026-03-15",
          location: "Harbin",
          cover: "https://...",    // 日期封面图
          user_plans: ["...", "..."],  // 用户计划列表
          meals: {
            breakfast: { name, cost, image, time, links, ... },
            lunch: { ... },
            dinner: { ... }
          },
          attractions: [
            { name, type, cost, image, time, links, highlights, ... }
          ],
          entertainment: [
            { name, type, cost, duration, note, time, links, ... }
          ],
          accommodation: {
            name, type, cost, stars, location, time, links, ...
          },
          budget: {
            meals: 235,
            attractions: 20,
            entertainment: 300,
            accommodation: 450,
            total: 1005
          }
        }
      ]
    }
  ]
};
```

## 技术栈

- **React 18**: UI 框架 (通过 UMD 加载)
- **Babel Standalone**: JSX 转译
- **纯 CSS**: 内联样式 (无外部 CSS 框架)
- **单文件部署**: 完整应用打包在单个 HTML 文件

## 视觉设计规范

### 颜色系统
- **主色**: `#37352f` (深灰 - 文字)
- **次色**: `#9b9a97` (中灰 - 标签)
- **背景**: `#fbfbfa` (米白 - 侧边栏), `#ffffff` (纯白 - 主区域)
- **边框**: `#f0efed` (淡灰)
- **卡片阴影**: `rgba(0,0,0,0.04)` + 边框

### 分类配色
- 🍽️ **Meals**: `#f0b429` (金黄)
- 📍 **Attractions**: `#4a90d9` (蓝色)
- 🎭 **Entertainment**: `#9b6dd7` (紫色)
- 🏨 **Accommodation**: `#45b26b` (绿色)

### 字体系统
```css
font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont,
             'Segoe UI', Helvetica, 'Noto Sans SC', sans-serif
```

### 响应式断点
- **sm**: < 640px (手机)
- **md**: 640px - 960px (平板)
- **lg**: > 960px (桌面)

## 与原生成器对比

| 特性 | 原生成器 (html_generator.py) | Notion React 生成器 |
|------|------------------------------|---------------------|
| **UI 风格** | Chart.js + 传统 HTML | Notion + React |
| **文件大小** | 250+ KB | 40-50 KB |
| **交互性** | 中等 (tabs, modals) | 高 (React state) |
| **移动端** | 基本支持 | 完美适配 |
| **视图模式** | 单视图 (tabs) | 双视图 (Kanban + Timeline) |
| **性能** | 较重 (Chart.js) | 轻量 (纯 CSS) |
| **维护性** | Python 模板 | React 组件化 |

## 自定义封面图

生成器自动为不同城市匹配封面图:

```python
covers = {
    "harbin": "https://images.unsplash.com/photo-1548199973-03cce0bbc87b...",
    "beijing": "https://images.unsplash.com/photo-1508804185872-d7badad00f7d...",
    "shanghai": "https://images.unsplash.com/photo-1537887534808-c02b98e72156...",
    ...
}
```

如需自定义,修改 `scripts/generate-notion-react.py` 中的 `_get_cover_image()` 方法。

## 故障排除

### HTML 不显示内容
- 检查浏览器控制台是否有 JavaScript 错误
- 确认 PLAN_DATA 结构完整 (查看 HTML 源码)
- 验证 React/Babel CDN 链接可访问

### 数据缺失
- 确认 `data/<plan-id>/` 目录存在
- 检查各 agent JSON 文件是否生成
- 查看生成器输出的警告信息

### 部署失败
- 确认 git remote 已配置: `git remote -v`
- 检查 gh-pages 分支: `git branch -a`
- 手动推送: `cd _deploy && git push -f origin gh-pages`

## 文件结构

```
scripts/
├── generate-notion-react.py          # Notion React 生成器 (Python)
└── generate-notion-and-deploy.sh    # 生成 + 部署脚本 (Bash)

travel-plan-notion-<plan-id>.html    # 生成的 React 应用

_deploy/
└── <plan-id>/<date>/index.html      # GitHub Pages 部署文件
```

## 示例命令

### 完整工作流
```bash
# 1. 生成 skeleton (假设已有)
# 2. 运行所有 agents (假设已完成)

# 3. 生成 Notion React HTML
python3 scripts/generate-notion-react.py beijing-exchange-bucket-list-20260202-232405

# 4. 本地预览
open travel-plan-notion-beijing-exchange-bucket-list-20260202-232405.html

# 5. 部署到 GitHub Pages
bash scripts/generate-notion-and-deploy.sh beijing-exchange-bucket-list-20260202-232405

# 6. 访问在线版本
# https://Yugoge.github.io/travel-planner-graph/beijing-exchange-bucket-list-20260202-232405/2026-02-05/
```

## 未来改进

- [ ] 添加打印/PDF 导出优化
- [ ] 支持多语言切换 (中英文)
- [ ] 集成地图可视化 (Google Maps / 高德地图)
- [ ] 添加搜索和筛选功能
- [ ] 离线 PWA 支持
- [ ] 自定义主题配色
- [ ] 导出为 JSON/iCal 格式

## License

MIT License - 可自由使用和修改

---

**Generated with [Claude Code](https://claude.ai/code)**
