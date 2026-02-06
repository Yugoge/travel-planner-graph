# 最终可用 MCP 技能清单

**更新日期**: 2026-01-30
**状态**: 生产就绪
**总计**: 5 个用户可用技能 + 1 个内部测试技能

---

## 📊 快速概览

| # | 技能名称 | 类型 | API Key | 状态 | 工具数 | 用途 |
|---|---------|------|---------|------|--------|------|
| 1 | **weather** | 天气 | ❌ 不需要 | ✅ 立即可用 | 12 | 天气预报、警报、空气质量 |
| 2 | **google-maps** | 地图 | ❌ 不需要 | ✅ 立即可用 | 7 | 国际地图、POI、路线 |
| 3 | **gaode-maps** | 地图 | ✅ 需要 | ✅ 已配置 | 14 | 中国地图、POI、路线 |
| 4 | **duffel-flights** | 航班 | ✅ 需要 | ⏳ 待配置 | 3 | 国际航班搜索（只读）|
| 5 | **airbnb** | 住宿 | ❌ 不需要 | ⚠️  需配置 | 2 | 度假租赁搜索 |
| 7 | test-mcp | 测试 | - | 内部使用 | - | MCP 协议测试 |

---

## ✅ 立即可用（无需配置）

### 1. Weather - 综合天气数据

**包名**: `@dangahagan/weather-mcp@1.6.1`
**API Key**: ❌ 不需要
**状态**: ✅ **生产就绪**
**数据源**: NOAA (美国) + Open-Meteo (全球)

#### 12 个可用工具

| 工具 | 功能 | 覆盖范围 |
|------|------|---------|
| `get_forecast` | 天气预报 | 全球 |
| `get_current_conditions` | 当前天气 | 美国 |
| `get_alerts` | 天气警报 | 美国 |
| `get_historical_weather` | 历史天气 | 全球 |
| `check_service_status` | 服务状态 | - |
| `search_location` | 位置搜索 | 全球 |
| `get_air_quality` | 空气质量 | 美国 |
| `get_marine_conditions` | 海洋状况 | 美国 |
| `get_weather_imagery` | 天气图像 | 美国 |
| `get_lightning_activity` | 闪电活动 | 美国 |
| `get_river_conditions` | 河流状况 | 美国 |
| `get_wildfire_info` | 野火信息 | 美国 |

#### 使用示例
```bash
cd /root/travel-planner/.claude/skills/weather

# 获取天气预报
python3 scripts/forecast.py 40.7128 -74.0060

# 搜索位置
python3 scripts/location.py "Paris, France"

# 空气质量
python3 scripts/air_quality.py 34.0522 -118.2437
```

#### 集成的 Agents
- ✅ transportation (天气影响交通选择)
- ✅ meals (室内/户外用餐)
- ✅ attractions (活动选择)
- ✅ shopping (天气装备建议)
- ✅ timeline (行程优化)
- ✅ budget (天气相关预算)

---

### 2. Google Maps - 国际地图服务

**包名**: Google Maps Grounding Lite MCP
**API Key**: ❌ 不需要
**状态**: ✅ **生产就绪**
**覆盖**: 全球

#### 7 个可用工具

| 工具 | 功能 |
|------|------|
| `search_places` | POI 搜索 |
| `get_place_details` | 地点详情 |
| `compute_routes` | 路线规划 |
| `geocode` | 地址转坐标 |
| `reverse_geocode` | 坐标转地址 |
| `get_distance_matrix` | 距离矩阵 |
| `lookup_weather` | 天气查询 |

#### 使用示例
```bash
cd /root/travel-planner/.claude/skills/google-maps

# POI 搜索
python3 scripts/places.py "restaurants in Paris" 10

# 路线规划
python3 scripts/routing.py "New York, NY" "Boston, MA" TRANSIT

# 天气查询
python3 scripts/weather.py "Tokyo, Japan"
```

#### 集成的 Agents
- ✅ transportation (路线规划)
- ✅ meals (餐厅搜索 - **替代 Yelp**)
- ✅ accommodation (住宿位置)
- ✅ attractions (景点搜索 - **替代 TripAdvisor**)
- ✅ entertainment (娱乐场所)
- ✅ shopping (商店搜索)

---

### 3. Gaode Maps - 中国地图服务

**包名**: `@amap/amap-maps-mcp-server`
**API Key**: ✅ 需要 `AMAP_MAPS_API_KEY`
**状态**: ✅ **已配置，生产就绪**
**覆盖**: 中国大陆
**坐标系**: GCJ-02

#### 14 个可用工具

**路线规划** (4):
- `driving_route` - 驾车路线
- `walking_route` - 步行路线
- `cycling_route` - 骑行路线
- `transit_route` - 公交路线

**POI 搜索** (3):
- `poi_search_keyword` - 关键词搜索
- `poi_search_nearby` - 附近搜索
- `poi_detail` - POI 详情

**地理编码** (3):
- `geocode` - 地址转坐标
- `reverse_geocode` - 坐标转地址
- `ip_location` - IP 定位

**工具类** (4):
- `weather_info` - 天气信息
- `distance_measure` - 距离测量
- 坐标转换工具
- 批量查询工具

#### 使用示例
```bash
cd /root/travel-planner/.claude/skills/gaode-maps

# 路线规划
python3 scripts/driving.py "北京" "上海"

# POI 搜索
python3 scripts/keyword.py "餐厅" "上海" 10

# 地理编码
python3 scripts/geocode.py "北京市朝阳区"
```

#### 集成的 Agents
- ✅ transportation (中国路线优先)
- ✅ meals (中国餐厅搜索)
- ✅ accommodation (中国住宿)
- ✅ attractions (中国景点)
- ✅ entertainment (中国娱乐)
- ✅ shopping (中国购物)

---

## ⏳ 需要配置 API Key

### 4. Duffel Flights - 国际航班搜索

**包名**: `flights-mcp` (Python)
**API Key**: ✅ 需要 `DUFFEL_API_KEY`
**状态**: ⏳ **待配置 API Key**
**模式**: 只读搜索（不能预订）
**费用**: 免费沙盒 + 按预订付费

#### 3 个可用工具

| 工具 | 功能 |
|------|------|
| `search_flights` | 单程/往返航班搜索 |
| `get_offer_details` | 航班详情 |
| `search_multi_city` | 多城市航班 |

#### 注册步骤
1. 访问 https://app.duffel.com/
2. 创建账号（1-5 分钟）
3. 从 Dashboard 创建 access token
4. 使用 "Developer test mode" (免费沙盒)

#### 设置环境变量
```bash
# Add to .env file
echo "DUFFEL_API_KEY=your_api_key_here" >> .env
```

#### 使用示例
```bash
cd /root/travel-planner/.claude/skills/duffel-flights

# 搜索航班
python3 scripts/search_flights.py "JFK" "LAX" "2026-02-15"

# 多城市
python3 scripts/search_multi_city.py "NYC" "PAR" "LON" "2026-03-01" "2026-03-08"
```

#### 集成的 Agents
- ✅ transportation (**替代 Amadeus 和 12306**)

---

## ⚠️  需要特殊配置

### 5. Airbnb - 度假租赁搜索

**包名**: `@openbnb/mcp-server-airbnb@0.1.3`
**API Key**: ❌ 不需要
**状态**: ⚠️  **需配置 robots.txt 绕过**
**方式**: 网页抓取
**费用**: 免费

#### 2 个可用工具

| 工具 | 功能 |
|------|------|
| `airbnb_search` | 搜索房源 |
| `airbnb_listing_details` | 房源详情 |

#### ⚠️  配置要求

Airbnb 默认被 robots.txt 阻止。需要在 `~/.config/Claude/claude_desktop_config.json` 添加：

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

#### ⚠️  法律声明
- 网页抓取可能违反 Airbnb 服务条款
- 仅用于个人研究/测试
- 商业使用需法律评估
- IP 可能被封禁

#### 使用示例
```bash
cd /root/travel-planner/.claude/skills/airbnb

# 搜索房源
python3 scripts/search.py "Paris, France" --checkin 2026-03-01 --checkout 2026-03-05

# 房源详情
python3 scripts/details.py 12345678 --checkin 2026-03-01 --checkout 2026-03-05
```

#### 集成的 Agents
- ✅ accommodation (度假租赁)

---

## 🔧 内部工具

### 7. test-mcp

**用途**: MCP 协议测试
**状态**: 仅内部使用
**说明**: 用于测试 MCP 工具调用，不面向用户

---

## 📈 技能统计

### 按类型分类

| 类型 | 技能 | 数量 |
|------|------|------|
| **地图导航** | google-maps, gaode-maps | 2 |
| **天气** | weather | 1 |
| **交通** | duffel-flights | 1 |
| **住宿** | airbnb | 1 |

### 按 API Key 需求分类

| 需求 | 技能 | 数量 |
|------|------|------|
| **无需 API Key** | weather, google-maps, airbnb | 3 |
| **需要 API Key** | gaode-maps, duffel-flights | 2 |

### 按状态分类

| 状态 | 技能 | 数量 |
|------|------|------|
| **立即可用** | weather, google-maps, gaode-maps | 3 |
| **待配置** | duffel-flights | 1 |
| **需特殊配置** | airbnb | 1 |

### 工具总数

| 技能 | 工具数 |
|------|--------|
| gaode-maps | 14 |
| weather | 12 |
| google-maps | 7 |
| duffel-flights | 3 |
| airbnb | 2 |
| **总计** | **38** |

---

## 🗺️ Agent 技能分配

### Transportation Agent
**技能**: google-maps, gaode-maps, duffel-flights, weather
**能力**:
- ✅ 国际路线规划 (Google Maps)
- ✅ 中国路线规划 (Gaode Maps)
- ✅ 国际航班搜索 (Duffel Flights) - **替代 Amadeus + 12306**
- ✅ 天气影响交通决策 (Weather)

### Meals Agent
**技能**: google-maps, gaode-maps, weather
**能力**:
- ✅ 国际餐厅搜索 (Google Maps POI) - **替代 Yelp**
- ✅ 中国餐厅搜索 (Gaode Maps)
- ✅ 天气影响室内/户外用餐 (Weather)

### Accommodation Agent
**技能**: google-maps, gaode-maps, weather, airbnb
**能力**:
- ✅ 度假租赁搜索 (Airbnb)
- ✅ 位置验证 (Google/Gaode Maps)
- ✅ 天气影响住宿选择 (Weather)

### Attractions Agent
**技能**: google-maps, gaode-maps, weather
**能力**:
- ✅ 国际景点搜索 (Google Maps POI) - **替代 TripAdvisor**
- ✅ 中国景点搜索 (Gaode Maps)
- ✅ 天气影响活动选择 (Weather)

### Entertainment Agent
**技能**: google-maps, gaode-maps, weather
**能力**:
- ✅ 娱乐场所搜索 (Google/Gaode Maps)
- ✅ 天气影响活动类型 (Weather)

### Shopping Agent
**技能**: google-maps, gaode-maps, weather
**能力**:
- ✅ 购物中心搜索 (Google/Gaode Maps)
- ✅ 天气装备建议 (Weather)

### Timeline Agent
**技能**: weather
**能力**:
- ✅ 天气优化行程安排

### Budget Agent
**技能**: weather
**能力**:
- ✅ 天气相关预算项目

---

## 🚀 快速开始指南

### 立即可用（0 配置）
```bash
# 测试 Weather
python3 /root/travel-planner/.claude/skills/weather/scripts/forecast.py 40.7128 -74.0060

# 测试 Google Maps
python3 /root/travel-planner/.claude/skills/google-maps/scripts/places.py "restaurants in Paris" 10
```

### 需要 API Key（10-15 分钟）

**优先级排序**:

1. **Duffel Flights** (5 分钟) - 航班搜索
   - 注册: https://app.duffel.com/
   - 免费沙盒

2. **Airbnb** (10 分钟) - 配置 robots.txt 绕过
   - 编辑 `~/.config/Claude/claude_desktop_config.json`
   - 添加 `--ignore-robots-txt` 参数

---

## 📋 已删除的技能

以下技能已从项目中完全移除：

### ❌ 12306 (中国铁路)
**原因**: 12306.cn API 返回 400 错误，无法使用
**替代方案**: Duffel Flights (国际航班) + Gaode/Google Maps (路线)
**删除日期**: 2026-01-30

### ❌ Yelp (餐厅搜索)
**原因**: 收费 API ($7.99+/1K calls)，30 天试用后需付费
**替代方案**: Google Maps POI search (免费)
**删除日期**: 2026-01-30

### ❌ Amadeus Flight
**原因**: Amadeus 目前无法注册
**替代方案**: Duffel Flights (国际航班搜索)
**删除日期**: 2026-01-30

### ❌ TripAdvisor
**原因**: npm 包不存在 (404 错误)
**替代方案**: Google Maps POI search
**删除日期**: 2026-01-30 (之前)

### ❌ Jinko Hotel
**原因**: npm 包不存在 (404 错误)
**替代方案**: Airbnb + Google Maps
**删除日期**: 2026-01-30 (之前)

### ❌ OpenWeatherMap
**原因**: 被 Weather 技能替代（更多功能）
**替代方案**: Weather (12 个工具 vs 有限功能)
**删除日期**: 2026-01-30 (之前)

### ❌ Eventbrite
**原因**: API 兼容性问题 - 所有 API 调用返回 400 错误
**替代方案**: Google Maps POI search (活动场馆)，Web search (活动日历)
**删除日期**: 2026-01-30

---

## 📞 支持和文档

### 技能文档位置
- 每个技能: `.claude/skills/{skill-name}/SKILL.md`
- 测试报告: `/root/travel-planner/FINAL-NO-API-KEY-TEST-SUMMARY.md`
- 完整报告: `/root/travel-planner/NO-API-KEY-MCP-TEST-REPORT.md`

### Agent 文档位置
- 所有 agents: `.claude/agents/{agent-name}.md`

### 配置文件
- 项目配置: `.claude/settings.json`
- Claude Desktop: `~/.config/Claude/claude_desktop_config.json`

---

**清单生成日期**: 2026-01-30
**最后更新**: 删除 Eventbrite (API 兼容性问题)
**状态**: 生产就绪
**总工具数**: 38
**可用技能**: 5 (+ 1 内部测试)
