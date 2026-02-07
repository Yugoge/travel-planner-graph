# 紧急问题分析报告

**时间**: 2026-02-07
**状态**: 🔴 5个严重问题需要立即修复

---

## 问题1: 图片未更新到HTML ❌

### 症状
HTML显示的图片不是images.json中新抓取的图片

### 根本原因
**双重缓存问题**:
1. `fetch-images-batch.py` 抓取图片存到 `images.json`:
   - Key格式: `"gaode_Raffles City Chongqing Observation Deck (来福士观景台)"`

2. `generate-html-interactive.py` 查找图片使用 `_get_placeholder_image()`:
   - Line 177-180: 查找 `f"gaode_{poi_name}"`
   - poi_name来自agent JSON: `attr.get("name", "")`

3. **但是agent JSON中的POI已经有image字段**:
   - Agent输出时已经预填了Unsplash fallback URL
   - Line 371: `attr.get("image", self._get_placeholder_image(...))`
   - 因为`attr.get("image")`不为空，永远不会调用`_get_placeholder_image()`！

### 证据
```python
# attractions.json中已有image字段
{
  "name": "Raffles City...",
  "image": "https://images.unsplash.com/photo-xxx"  # ← 这个阻止了查找images.json
}
```

### 修复方案
**方案A**: 删除agent JSON中的image字段，强制从images.json查找
**方案B**: 修改`_get_placeholder_image()`检查逻辑，优先使用images.json

---

## 问题2: 图片风马牛不相及 ❌

### 症状
Chongqing Day 1图片仍然不准确

### 根本原因
**Issue 3的修复未生效** - 因为问题1，image字段永远来自agent JSON的Unsplash fallback，不会查找images.json

### 验证
```bash
# 检查cache key
gaode_Raffles City Chongqing Observation Deck (来福士观景台)  # ✅ 存在
# 但HTML用的是agent JSON的Unsplash URL，不是这个cache
```

### 修复方案
同问题1 - 解决image字段问题后自动修复

---

## 问题3: Entertainment没有照片 ❌

### 症状
Entertainment项目没有图片显示

### 根本原因
**Agent JSON中entertainment完全没有image字段**:
```python
# entertainment.json
{
  "name": "静·serene SPA 泰式按摩足疗 (Serene Thai SPA)",
  # NO image field at all!
}
```

**同时images.json中的cache key是full name**:
```
gaode_静·serene SPA 泰式按摩足疗 (Serene Thai SPA)
```

**HTML generator查找**:
- Line 442-444: `ent.get("image", self._get_placeholder_image("entertainment", poi_name=ent.get("name", "")))`
- 会调用`_get_placeholder_image()`
- Line 177-180: 查找 `f"gaode_{poi_name}"` ✅ 应该能找到

### 问题根源
需要实际测试 - 可能是查找成功但图片URL失效

### 修复方案
1. 验证images.json中entertainment cache是否有效
2. 如需重新抓取，运行fetch专门针对entertainment

---

## 问题4: Timeline有冲突 ⚠️

### 症状
用户看到timeline显示冲突

### 可能原因
1. **Issue 6的修复引入bug**: `_find_timeline_item()` fuzzy match错误匹配
2. **timeline.json本身有重叠**: 生成时计算错误
3. **HTML渲染重叠**: TimelineView的top计算错误

### 需要验证
```bash
# 检查Day 1的timeline重叠
python3 -c "检查timeline.json中是否有时间重叠"
```

### 修复方案
- 如果timeline.json有重叠 → 修复timeline-agent (Issue 7未完全解决)
- 如果fuzzy match错误 → 修复`_find_timeline_item()`
- 如果渲染错误 → 修复TimelineView CSS

---

## 问题5: 很多交通完全没有显示 ❌

### 症状
只看到寥寥几处交通，不是全部4个location_change

### 根本原因分析

**Transportation数据存在**:
```
Day 2: Chongqing → Bazhong
Day 3: Bazhong → Chengdu
Day 4: Chengdu → Shanghai
Day 8: Shanghai → Beijing
```

**HTML中找到21个transportation**:
```bash
grep -c '"transportation":' HTML  # 输出21
```

**问题**: 21个出现但用户说"寥寥几处"

### 可能原因
1. **Transportation在HTML中但未显示**: CSS隐藏或条件渲染失败
2. **只在某个View显示**: KanbanView有但TimelineView没有(或反之)
3. **Day 5 intra_city_routes未显示**: 只有location_change显示，intra_city被忽略

### 需要验证
```bash
# 检查KanbanView中transportation section
grep -A5 "Transportation" HTML

# 检查TimelineView中transportation entries
grep -A5 "transportation.*timeline" HTML
```

### 修复方案
- 检查Issue 8的implementation - transportation display可能不完整
- 验证条件渲染逻辑
- 确认intra_city_routes是否应该显示

---

## 立即行动计划

### 优先级修复顺序

**P0 - 立即修复 (阻塞用户)**:
1. 问题1 - 图片未更新 (核心display bug)
2. 问题5 - 交通缺失 (核心功能缺失)

**P1 - 高优先级**:
3. 问题3 - Entertainment图片 (功能不完整)
4. 问题4 - Timeline冲突 (用户体验问题)

**P2 - 已自动修复**:
5. 问题2 - 图片相关性 (解决问题1后自动修复)

---

## 修复方案建议

### 方案A: 快速hotfix (15分钟)
1. 删除所有agent JSON中的image字段 → 强制查找images.json
2. 重新生成HTML → 图片问题解决
3. 检查transportation display逻辑 → 修复缺失
4. 调查timeline冲突原因

### 方案B: 系统性修复 (1小时)
1. 修改agents输出格式 - 不预填image字段
2. 修改HTML generator - 优先使用images.json
3. 完善transportation display - 支持intra_city
4. 修复timeline冲突根源
5. 重新部署

---

## 根本问题总结

**架构问题**: Agent输出JSON和images.json之间没有集成

```
Agent JSON (attractions.json)     images.json (fetch-images-batch)
├─ name: "POI Name"               ├─ "gaode_POI Name": "url"
├─ image: "unsplash fallback" ❌  └─ [never used!]
└─ [blocks lookup of images.json]

HTML Generator
├─ attr.get("image")  ← 返回 Unsplash
└─ _get_placeholder_image()  ← 永远不会被调用
```

**解决方案**:
- Agent输出不应该包含image字段
- 或HTML generator应该忽略agent的image，强制查找images.json

---

要我立即执行方案A快速hotfix吗？
