---
name: 12306
description: Chinese railway ticket search via 12306 official system
allowed-tools: [Bash]
model: inherit
user-invocable: true
---

# 12306 Skill

Search Chinese railway tickets, station information, and train routes via China's official 12306 system.

**MCP Server**: `12306-mcp` (Node.js based)
**API Coverage**: 8/8 tools (100%)
**API Key**: Not required
**Region**: China mainland railway network

## Available Tools

1. **get-current-date** - Get current date from 12306 system
2. **get-tickets** - Search for direct train tickets between stations
3. **get-interline-tickets** - Search for transfer tickets (multi-train routes)
4. **get-train-route-stations** - Get all stations along a train route
5. **get-station-by-telecode** - Get station information by telecode
6. **get-station-code-by-names** - Get station codes for multiple station names
7. **get-station-code-of-citys** - Get all stations in specified cities
8. **get-stations-code-in-city** - Get all stations within a single city

## How to Use

Execute scripts from skill directory:
```bash
cd /root/travel-planner/.claude/skills/12306
python3 scripts/<script_name>.py <arguments>
```

## Scripts

### 1. Current Date (get_current_date.py)

Get current date from 12306 system for ticket searches.

```bash
python3 scripts/get_current_date.py
```

**Returns**: Current date in YYYY-MM-DD format

### 2. Search Tickets (get_tickets.py)

Search for direct train tickets between two stations.

```bash
# Basic search
python3 scripts/get_tickets.py "北京" "上海" 2026-02-15

# With filters
python3 scripts/get_tickets.py "北京" "上海" 2026-02-15 \
  --train-filter G D \
  --earliest-time 8 \
  --latest-time 18 \
  --sort lishi \
  --limit 10

# CSV output
python3 scripts/get_tickets.py "北京" "上海" 2026-02-15 --format csv
```

**Parameters**:
- `from_station`: Departure station name or code
- `to_station`: Arrival station name or code
- `date`: Travel date (YYYY-MM-DD)
- `--train-filter`: Train types (G=高铁, D=动车, C=城际, Z=直达, T=特快, K=快速)
- `--earliest-time`: Earliest departure hour (0-24)
- `--latest-time`: Latest departure hour (0-24)
- `--sort`: Sort by `lishi` (duration) or `start-time`
- `--reverse`: Reverse sort order
- `--limit`: Maximum number of results
- `--format`: Output format (json or csv)

**Returns**: Train schedules, ticket availability, pricing, seat types

### 3. Transfer Tickets (get_interline_tickets.py)

Search for routes requiring train transfers.

```bash
# Basic transfer search
python3 scripts/get_interline_tickets.py "拉萨" "三亚" 2026-03-01

# With filters
python3 scripts/get_interline_tickets.py "拉萨" "三亚" 2026-03-01 \
  --train-filter G D \
  --earliest-time 6 \
  --sort lishi \
  --limit 5
```

**Parameters**: Same as get_tickets.py (except no --format option)

**Returns**: Multi-train routes with transfer stations and combined pricing

### 4. Train Route (get_train_route_stations.py)

Get all stations a train stops at along its route.

```bash
python3 scripts/get_train_route_stations.py G123 "北京" "上海" 2026-02-15
```

**Parameters**:
- `train_code`: Train number (e.g., G123, D456)
- `from_station`: Departure station
- `to_station`: Arrival station
- `date`: Travel date

**Returns**: Station list with arrival/departure times and distances

### 5. Station by Telecode (get_station_by_telecode.py)

Get station information using its telecode.

```bash
python3 scripts/get_station_by_telecode.py BJP  # Beijing
python3 scripts/get_station_by_telecode.py SHH  # Shanghai Hongqiao
```

**Returns**: Station name, pinyin, short code, city

### 6. Station Codes by Names (get_station_code_by_names.py)

Get telecodes for multiple stations at once.

```bash
python3 scripts/get_station_code_by_names.py "北京南" "上海虹桥" "广州南"
```

**Returns**: Map of station names to telecodes

### 7. Stations in Cities (get_station_code_of_citys.py)

Get all stations in multiple cities.

```bash
python3 scripts/get_station_code_of_citys.py "北京" "上海" "广州"
```

**Returns**: List of all stations in each specified city

### 8. Stations in City (get_stations_code_in_city.py)

Get all stations within a single city.

```bash
python3 scripts/get_stations_code_in_city.py "北京"
```

**Returns**: All stations in the specified city

## Train Type Codes

- **G (高铁)**: High-speed rail (300+ km/h)
- **D (动车)**: Electric multiple unit (200-250 km/h)
- **C (城际)**: Intercity trains
- **Z (直达)**: Direct express
- **T (特快)**: Express
- **K (快速)**: Fast train
- **L (临客)**: Temporary train

## Seat Type Codes

Common seat types in results:
- **商务座** (Business): First class on high-speed trains
- **一等座** (First class): Standard first class
- **二等座** (Second class): Standard second class
- **软卧** (Soft sleeper): Private sleeping berth
- **硬卧** (Hard sleeper): Standard sleeping berth
- **硬座** (Hard seat): Standard seating
- **无座** (No seat): Standing ticket

## Output Format

All scripts output:
- **stdout**: JSON formatted data (or CSV if specified)
- **stderr**: Error messages

## Example Workflows

### Book a Trip

```bash
# 1. Check current date
python3 scripts/get_current_date.py

# 2. Search for tickets
python3 scripts/get_tickets.py "北京" "上海" 2026-02-15 --train-filter G D --limit 5

# 3. Check specific train route
python3 scripts/get_train_route_stations.py G123 "北京" "上海" 2026-02-15
```

### Find Transfer Routes

```bash
# For destinations without direct service
python3 scripts/get_interline_tickets.py "敦煌" "三亚" 2026-04-01 --limit 3
```

### Station Lookup

```bash
# Find all stations in a city
python3 scripts/get_stations_code_in_city.py "上海"

# Get station telecode
python3 scripts/get_station_code_by_names.py "上海虹桥"
```

## Error Handling

Scripts return:
- **Exit 0**: Success
- **Exit 1**: API error, network failure, or invalid parameters

Common issues:
- **400 error**: 12306 service temporarily unavailable (peak hours)
- **No results**: Try broader date range or different station names
- **Station not found**: Use city name search to find correct station name

## Technical Notes

- **MCP Type**: Node.js based (launched via npx)
- **Server Path**: `/tmp/12306-mcp/build/index.js`
- **Protocol**: JSON-RPC 2.0 over stdio
- **Data Source**: Official 12306.cn API
- **Rate Limiting**: Requests throttled by 12306 backend
- **Language**: Station names support both Chinese and pinyin

## Tool Name Verification

Tool names verified against actual MCP server source code:
- All 8 tools match source code definitions
- Parameter names match API expectations
- No assumed tool names
