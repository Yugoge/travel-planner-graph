#!/usr/bin/env bash
# Merge all agent JSONs and generate interactive HTML travel plan
# Usage: generate-travel-html.sh <destination-slug> [version-suffix]
# Exit codes: 0=success, 1=generation failed, 2=missing files

set -euo pipefail

DESTINATION_SLUG="${1:?Missing required destination-slug}"
VERSION_SUFFIX="${2:-}"

DATA_DIR="data/${DESTINATION_SLUG}"
PLAN_FILE="${DATA_DIR}/plan-skeleton.json"
OUTPUT_FILE="travel-plan-${DESTINATION_SLUG}${VERSION_SUFFIX}.html"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/../config/currency-config.json"

# Verify required files exist
if [[ ! -f "$PLAN_FILE" ]]; then
  echo "Error: Plan skeleton not found: $PLAN_FILE" >&2
  exit 2
fi

# Load currency configuration
if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "Warning: Currency config not found, using defaults (EUR display, CNY source)" >&2
  DEFAULT_DISPLAY_CURRENCY="EUR"
  DEFAULT_SOURCE_CURRENCY="CNY"
  CURRENCY_SYMBOL="€"
else
  DEFAULT_DISPLAY_CURRENCY=$(jq -r '.default_display_currency' "$CONFIG_FILE")
  DEFAULT_SOURCE_CURRENCY=$(jq -r '.default_source_currency // "CNY"' "$CONFIG_FILE")
  CURRENCY_SYMBOL=$(jq -r ".currency_symbol_map.${DEFAULT_DISPLAY_CURRENCY} // \"${DEFAULT_DISPLAY_CURRENCY}\"" "$CONFIG_FILE")
fi

# Fetch real-time exchange rate
echo "Fetching exchange rate: ${DEFAULT_SOURCE_CURRENCY} → ${DEFAULT_DISPLAY_CURRENCY}..."
EXCHANGE_RATE=$("${SCRIPT_DIR}/utils/fetch-exchange-rate.sh" "$DEFAULT_SOURCE_CURRENCY" "$DEFAULT_DISPLAY_CURRENCY") || {
  echo "Error: Failed to fetch exchange rate. Check network connection or API availability." >&2
  exit 1
}
echo "Exchange rate: 1 ${DEFAULT_SOURCE_CURRENCY} = ${EXCHANGE_RATE} ${DEFAULT_DISPLAY_CURRENCY}"

# Merge agent outputs into plan-skeleton
echo "Merging agent outputs..."

MERGED_DATA=$(jq -s '
  .[0] as $skeleton |

  # Load all agent outputs
  .[1] as $meals |
  .[2] as $accommodation |
  .[3] as $attractions |
  .[4] as $entertainment |
  .[5] as $shopping |
  .[6] as $transportation |
  .[7] as $timeline |
  .[8] as $budget |

  # Merge into skeleton
  $skeleton | .days |= [
    .[] | . as $day |
    . + {
      breakfast: ($meals.data.days[] | select(.day == $day.day) | .breakfast),
      lunch: ($meals.data.days[] | select(.day == $day.day) | .lunch),
      dinner: ($meals.data.days[] | select(.day == $day.day) | .dinner),
      accommodation: ($accommodation.data.days[] | select(.day == $day.day) | .accommodation),
      attractions: ($attractions.data.days[] | select(.day == $day.day) | .attractions),
      entertainment: ($entertainment.data.days[] | select(.day == $day.day) | .entertainment),
      shopping: ($shopping.data.days[] | select(.day == $day.day) | .shopping),
      location_change: (
        if $day.location_change then
          ($transportation.data.days[] | select(.day == $day.day) | .location_change)
        else
          null
        end
      ),
      timeline: ($timeline.data.days[] | select(.day == $day.day) | .timeline),
      budget: ($budget.data.days[] | select(.day == $day.day) | .budget)
    }
  ] |
  . + {
    emergency_info: $skeleton.emergency_info,
    currency_config: {
      source_currency: $source_currency,
      display_currency: $display_currency,
      exchange_rate: ($exchange_rate | tonumber),
      currency_symbol: $currency_symbol
    }
  }
' \
  --arg source_currency "$DEFAULT_SOURCE_CURRENCY" \
  --arg display_currency "$DEFAULT_DISPLAY_CURRENCY" \
  --arg exchange_rate "$EXCHANGE_RATE" \
  --arg currency_symbol "$CURRENCY_SYMBOL" \
  "$PLAN_FILE" \
  "${DATA_DIR}/meals.json" \
  "${DATA_DIR}/accommodation.json" \
  "${DATA_DIR}/attractions.json" \
  "${DATA_DIR}/entertainment.json" \
  "${DATA_DIR}/shopping.json" \
  "${DATA_DIR}/transportation.json" \
  "${DATA_DIR}/timeline.json" \
  "${DATA_DIR}/budget.json" 2>/dev/null || echo "{}")

if [[ "$MERGED_DATA" == "{}" ]]; then
  echo "Warning: Some agent outputs missing, generating partial HTML" >&2
fi

# Generate HTML using template
cat > "$OUTPUT_FILE" <<'HTML_TEMPLATE'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Travel Plan - DESTINATION_TITLE</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      line-height: 1.6;
      color: #333;
      background: #f5f5f5;
    }
    .container { max-width: 1400px; margin: 0 auto; padding: 20px; }

    /* Header */
    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 40px 20px;
      border-radius: 12px;
      margin-bottom: 20px;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .header h1 { font-size: 2.5em; margin-bottom: 10px; }
    .header .meta { font-size: 1.1em; opacity: 0.9; }

    /* Stats Dashboard - Expandable Cards */
    .stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 15px;
      margin-bottom: 20px;
    }
    .stat-card {
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      overflow: hidden;
      cursor: pointer;
      transition: transform 0.2s, box-shadow 0.2s;
    }
    .stat-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    .stat-header {
      padding: 20px;
      background: white;
    }
    .stat-card .value { font-size: 2em; font-weight: bold; color: #667eea; }
    .stat-card .label { color: #666; font-size: 0.9em; margin-top: 5px; }
    .stat-expand-icon {
      float: right;
      color: #999;
      transition: transform 0.2s;
    }
    .stat-card.expanded .stat-expand-icon { transform: rotate(180deg); }
    .stat-details {
      display: none;
      padding: 0 20px 20px 20px;
      background: #f9f9f9;
      border-top: 1px solid #eee;
      max-height: 400px;
      overflow-y: auto;
    }
    .stat-details.active { display: block; }
    .stat-detail-item {
      padding: 8px 0;
      border-bottom: 1px solid #eee;
      display: flex;
      justify-content: space-between;
      font-size: 0.9em;
    }
    .stat-detail-item:last-child { border-bottom: none; }

    /* Route Map - Kanban Style */
    .route-map {
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      padding: 20px;
      margin-bottom: 20px;
      overflow-x: auto;
    }
    .route-map h2 {
      color: #667eea;
      margin-bottom: 15px;
      font-size: 1.5em;
    }
    .route-kanban {
      display: flex;
      gap: 15px;
      min-width: min-content;
      padding-bottom: 10px;
    }
    .route-city {
      min-width: 180px;
      background: #f9f9f9;
      border-radius: 8px;
      border: 2px solid #667eea;
      cursor: pointer;
      transition: transform 0.2s, box-shadow 0.2s;
    }
    .route-city:hover {
      transform: translateY(-3px);
      box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
    }
    .route-city-header {
      background: #667eea;
      color: white;
      padding: 12px;
      border-radius: 6px 6px 0 0;
      font-weight: bold;
      text-align: center;
    }
    .route-city-days {
      padding: 10px;
    }
    .route-day-item {
      background: white;
      padding: 8px;
      margin: 5px 0;
      border-radius: 4px;
      font-size: 0.85em;
      border-left: 3px solid #667eea;
    }
    .route-day-date { font-weight: bold; color: #667eea; }
    .route-day-budget { color: #e74c3c; font-size: 0.9em; margin-top: 3px; }

    /* Budget by City Section */
    .budget-city-section {
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      padding: 20px;
      margin-bottom: 20px;
    }
    .budget-city-section h2 {
      color: #667eea;
      margin-bottom: 15px;
      font-size: 1.5em;
    }
    .budget-city-card {
      background: #f9f9f9;
      border-radius: 6px;
      margin-bottom: 10px;
      overflow: hidden;
      border: 1px solid #eee;
    }
    .budget-city-header {
      padding: 15px;
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: white;
      transition: background 0.2s;
    }
    .budget-city-header:hover { background: #f5f5f5; }
    .budget-city-name { font-weight: bold; color: #333; }
    .budget-city-total { color: #e74c3c; font-weight: bold; }
    .budget-city-expand { color: #999; transition: transform 0.2s; }
    .budget-city-card.expanded .budget-city-expand { transform: rotate(180deg); }
    .budget-city-details {
      display: none;
      padding: 15px;
      background: #fafafa;
    }
    .budget-city-details.active { display: block; }
    .budget-breakdown-item {
      display: flex;
      justify-content: space-between;
      padding: 6px 0;
      border-bottom: 1px solid #eee;
      font-size: 0.9em;
    }
    .budget-breakdown-item:last-child { border-bottom: none; }

    /* Attraction Types Section */
    .attraction-types-section {
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      padding: 20px;
      margin-bottom: 20px;
    }
    .attraction-types-section h2 {
      color: #667eea;
      margin-bottom: 15px;
      font-size: 1.5em;
    }
    .attraction-type-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 12px;
    }
    .attraction-type-card {
      background: #f9f9f9;
      padding: 15px;
      border-radius: 6px;
      border-left: 4px solid #667eea;
      cursor: pointer;
      transition: transform 0.2s;
    }
    .attraction-type-card:hover { transform: translateX(3px); }
    .attraction-type-name { font-weight: bold; color: #667eea; }
    .attraction-type-count { color: #666; font-size: 0.9em; margin-top: 5px; }

    /* Cities Panel - Geographic Clustering */
    .cities-panel {
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      padding: 20px;
      margin-bottom: 20px;
    }
    .cities-panel h2 {
      color: #667eea;
      margin-bottom: 15px;
      font-size: 1.5em;
    }
    .city-cluster {
      margin-bottom: 20px;
    }
    .city-cluster-header {
      font-weight: bold;
      color: #667eea;
      margin-bottom: 10px;
      padding-bottom: 5px;
      border-bottom: 2px solid #667eea;
    }
    .city-attractions {
      display: grid;
      gap: 10px;
    }
    .attraction-item {
      background: #f9f9f9;
      padding: 12px;
      border-radius: 6px;
      border-left: 3px solid #667eea;
    }
    .attraction-name {
      font-weight: bold;
      color: #333;
      margin-bottom: 5px;
    }
    .attraction-links {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 8px;
    }
    .attraction-link {
      display: inline-block;
      padding: 4px 10px;
      background: #667eea;
      color: white;
      text-decoration: none;
      border-radius: 4px;
      font-size: 0.85em;
      transition: background 0.2s;
    }
    .attraction-link:hover { background: #5568d3; }
    .attraction-link.gaode { background: #28a745; }
    .attraction-link.google { background: #4285f4; }
    .attraction-link.rednote { background: #ff2442; }

    /* Day Cards */
    .day-card {
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      margin-bottom: 20px;
      overflow: hidden;
    }
    .day-header {
      background: #667eea;
      color: white;
      padding: 15px 20px;
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .day-header:hover { background: #5568d3; }
    .day-content {
      padding: 20px;
      display: none;
    }
    .day-content.active { display: block; }

    /* Timeline */
    .timeline-item {
      border-left: 3px solid #667eea;
      padding-left: 20px;
      margin-bottom: 20px;
      position: relative;
    }
    .timeline-item::before {
      content: '';
      position: absolute;
      left: -7px;
      top: 0;
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background: #667eea;
    }
    .timeline-time { font-weight: bold; color: #667eea; }
    .timeline-activity { margin: 5px 0; }

    /* Activity Grid */
    .activity-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 15px;
      margin-top: 20px;
    }
    .activity-card {
      background: #f9f9f9;
      padding: 15px;
      border-radius: 6px;
      border-left: 4px solid #667eea;
    }
    .activity-card h4 { color: #667eea; margin-bottom: 8px; }
    .activity-card .cost { color: #e74c3c; font-weight: bold; }

    /* Side Panel */
    .side-panel {
      position: fixed;
      top: 0;
      right: -450px;
      width: 450px;
      height: 100vh;
      background: white;
      box-shadow: -2px 0 10px rgba(0,0,0,0.1);
      transition: right 0.3s;
      overflow-y: auto;
      z-index: 1000;
      padding: 20px;
    }
    .side-panel.active { right: 0; }
    .close-panel {
      cursor: pointer;
      font-size: 1.5em;
      float: right;
      color: #999;
    }

    /* Responsive */
    @media (max-width: 768px) {
      .header h1 { font-size: 1.8em; }
      .side-panel { width: 100%; right: -100%; }
      .activity-grid { grid-template-columns: 1fr; }
      .stats { grid-template-columns: 1fr; }
      .route-kanban { flex-direction: column; }
      .route-city { min-width: 100%; }
    }

    /* Utilities */
    .btn {
      background: #667eea;
      color: white;
      border: none;
      padding: 10px 20px;
      border-radius: 6px;
      cursor: pointer;
      transition: background 0.3s;
    }
    .btn:hover { background: #5568d3; }
    .section { margin-bottom: 30px; }
    .section h3 { color: #667eea; margin-bottom: 15px; }
  </style>
</head>
<body>
  <div class="container">
    <!-- Header -->
    <div class="header">
      <h1 id="trip-title">Loading...</h1>
      <div class="meta" id="trip-meta"></div>
    </div>

    <!-- Stats Dashboard -->
    <div class="stats" id="stats-container"></div>

    <!-- Route Map (Kanban) -->
    <div class="route-map">
      <h2>Route Overview</h2>
      <div class="route-kanban" id="route-kanban"></div>
    </div>

    <!-- Budget by City -->
    <div class="budget-city-section">
      <h2>Budget by City</h2>
      <div id="budget-by-city-container"></div>
    </div>

    <!-- Attraction Types -->
    <div class="attraction-types-section">
      <h2>Attraction Types</h2>
      <div class="attraction-type-grid" id="attraction-types-container"></div>
    </div>

    <!-- Cities Panel (Geographic) -->
    <div class="cities-panel">
      <h2>Cities & Attractions</h2>
      <div id="cities-container"></div>
    </div>

    <!-- Day by Day Timeline -->
    <h2 style="color: #667eea; margin: 30px 0 15px 0;">Day-by-Day Timeline</h2>
    <div id="days-container"></div>

    <!-- Emergency Info Side Panel -->
    <div class="side-panel" id="emergency-panel">
      <span class="close-panel" onclick="closePanel()">×</span>
      <h2>Emergency Information</h2>
      <div id="emergency-content"></div>
    </div>
  </div>

  <script>
    // Data will be injected here
    const PLAN_DATA = PLAN_DATA_INJECTION;

    // Currency configuration (dynamically fetched at HTML generation time)
    const CURRENCY_CONFIG = PLAN_DATA.currency_config || {
      source_currency: 'CNY',
      display_currency: 'EUR',
      exchange_rate: 7.8,
      currency_symbol: '€'
    };

    // Helper: Convert source currency to display currency
    function convertCurrency(amount) {
      return (amount * CURRENCY_CONFIG.exchange_rate).toFixed(2);
    }

    // Legacy helper for backward compatibility
    function toEUR(cny) {
      return convertCurrency(cny);
    }

    // Helper: Generate map links
    function generateMapLinks(name, location) {
      const encodedName = encodeURIComponent(name);
      const encodedLocation = encodeURIComponent(location);

      // Determine mainland vs HK/Macau
      const isMainland = !location.includes('Hong Kong') && !location.includes('Macau') &&
                         !location.includes('HK') && !location.includes('MO');

      const mapLink = isMainland
        ? `https://ditu.amap.com/search?query=${encodedName}`
        : `https://www.google.com/maps/search/?api=1&query=${encodedName}+${encodedLocation}`;

      const rednoteLink = `https://www.xiaohongshu.com/search_result?keyword=${encodedName}`;

      return { mapLink, rednote: rednoteLink, isMainland };
    }

    // Initialize page
    function init() {
      renderHeader();
      renderStats();
      renderRouteMap();
      renderBudgetByCity();
      renderAttractionTypes();
      renderCitiesPanel();
      renderDays();
      renderEmergencyInfo();
    }

    function renderHeader() {
      const firstDay = PLAN_DATA.days[0];
      const lastDay = PLAN_DATA.days[PLAN_DATA.days.length - 1];
      const cities = [...new Set(PLAN_DATA.days.map(d => d.location))];
      document.getElementById('trip-title').textContent = `${cities.join(' • ')} Travel Plan`;
      document.getElementById('trip-meta').textContent =
        `${firstDay.date} to ${lastDay.date} • ${PLAN_DATA.days.length} days • ${cities.length} cities`;
    }

    function renderStats() {
      // Calculate stats
      const totalBudgetCNY = PLAN_DATA.days.reduce((sum, day) => sum + (day.budget?.total || 0), 0);
      const totalAttractions = PLAN_DATA.days.reduce((sum, day) => sum + (day.attractions?.length || 0), 0);
      const cities = [...new Set(PLAN_DATA.days.map(d => d.location))];

      // Activities per city
      const activitiesByCity = {};
      PLAN_DATA.days.forEach(day => {
        if (!activitiesByCity[day.location]) activitiesByCity[day.location] = 0;
        activitiesByCity[day.location] += (day.attractions?.length || 0) +
                                          (day.entertainment?.length || 0) +
                                          (day.shopping?.length || 0);
      });

      // Days per city
      const daysByCity = {};
      PLAN_DATA.days.forEach(day => {
        daysByCity[day.location] = (daysByCity[day.location] || 0) + 1;
      });

      const stats = [
        {
          label: 'Total Budget',
          value: `${CURRENCY_CONFIG.currency_symbol}${toEUR(totalBudgetCNY)}`,
          details: PLAN_DATA.days.map(d => ({
            label: `Day ${d.day} - ${d.location}`,
            value: `${CURRENCY_CONFIG.currency_symbol}${toEUR(d.budget?.total || 0)}`
          }))
        },
        {
          label: 'Attractions',
          value: totalAttractions,
          details: Object.entries(activitiesByCity).map(([city, count]) => ({
            label: city,
            value: count
          }))
        },
        {
          label: 'Cities',
          value: cities.length,
          details: cities.map(city => ({
            label: city,
            value: `${daysByCity[city]} day${daysByCity[city] > 1 ? 's' : ''}`
          }))
        },
        {
          label: 'Travel Days',
          value: PLAN_DATA.days.length,
          details: PLAN_DATA.days.map(d => ({
            label: `Day ${d.day} - ${d.date}`,
            value: d.location
          }))
        }
      ];

      document.getElementById('stats-container').innerHTML = stats.map((s, idx) => `
        <div class="stat-card" onclick="toggleStat(${idx})">
          <div class="stat-header">
            <span class="stat-expand-icon">▼</span>
            <div class="value">${s.value}</div>
            <div class="label">${s.label}</div>
          </div>
          <div class="stat-details" id="stat-details-${idx}">
            ${s.details.map(d => `
              <div class="stat-detail-item">
                <span>${d.label}</span>
                <span>${d.value}</span>
              </div>
            `).join('')}
          </div>
        </div>
      `).join('');
    }

    function toggleStat(idx) {
      const details = document.getElementById(`stat-details-${idx}`);
      const card = details.closest('.stat-card');
      details.classList.toggle('active');
      card.classList.toggle('expanded');
    }

    function renderRouteMap() {
      // Group days by city
      const cityGroups = {};
      PLAN_DATA.days.forEach(day => {
        if (!cityGroups[day.location]) cityGroups[day.location] = [];
        cityGroups[day.location].push(day);
      });

      // Render Kanban columns
      const kanban = document.getElementById('route-kanban');
      kanban.innerHTML = Object.entries(cityGroups).map(([city, days]) => {
        const totalBudget = days.reduce((sum, d) => sum + (d.budget?.total || 0), 0);
        return `
          <div class="route-city" onclick="scrollToCity('${city}')">
            <div class="route-city-header">${city}</div>
            <div class="route-city-days">
              ${days.map(d => `
                <div class="route-day-item">
                  <div class="route-day-date">Day ${d.day} - ${d.date}</div>
                  <div class="route-day-budget">${CURRENCY_CONFIG.currency_symbol}${toEUR(d.budget?.total || 0)}</div>
                </div>
              `).join('')}
              <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #ddd; font-weight: bold; color: #e74c3c;">
                Total: ${CURRENCY_CONFIG.currency_symbol}${toEUR(totalBudget)}
              </div>
            </div>
          </div>
        `;
      }).join('');
    }

    function scrollToCity(city) {
      const element = document.getElementById(`city-${city.replace(/\s+/g, '-')}`);
      if (element) element.scrollIntoView({ behavior: 'smooth' });
    }

    function renderBudgetByCity() {
      const cityBudgets = {};
      PLAN_DATA.days.forEach(day => {
        if (!cityBudgets[day.location]) {
          cityBudgets[day.location] = {
            total: 0,
            breakdown: {}
          };
        }

        const budget = day.budget || {};
        cityBudgets[day.location].total += budget.total || 0;

        // Aggregate budget categories
        Object.entries(budget).forEach(([key, value]) => {
          if (key !== 'total' && typeof value === 'number') {
            cityBudgets[day.location].breakdown[key] =
              (cityBudgets[day.location].breakdown[key] || 0) + value;
          }
        });
      });

      const container = document.getElementById('budget-by-city-container');
      container.innerHTML = Object.entries(cityBudgets).map(([city, data], idx) => `
        <div class="budget-city-card">
          <div class="budget-city-header" onclick="toggleBudgetCity(${idx})">
            <div class="budget-city-name">${city}</div>
            <div>
              <span class="budget-city-total">${CURRENCY_CONFIG.currency_symbol}${toEUR(data.total)}</span>
              <span class="budget-city-expand">▼</span>
            </div>
          </div>
          <div class="budget-city-details" id="budget-city-${idx}">
            ${Object.entries(data.breakdown).map(([category, amount]) => `
              <div class="budget-breakdown-item">
                <span>${category.replace(/_/g, ' ')}</span>
                <span>${CURRENCY_CONFIG.currency_symbol}${toEUR(amount)}</span>
              </div>
            `).join('')}
          </div>
        </div>
      `).join('');
    }

    function toggleBudgetCity(idx) {
      const details = document.getElementById(`budget-city-${idx}`);
      const card = details.closest('.budget-city-card');
      details.classList.toggle('active');
      card.classList.toggle('expanded');
    }

    function renderAttractionTypes() {
      const types = {};
      PLAN_DATA.days.forEach(day => {
        (day.attractions || []).forEach(attr => {
          const type = attr.type || 'Other';
          types[type] = (types[type] || 0) + 1;
        });
      });

      const container = document.getElementById('attraction-types-container');
      container.innerHTML = Object.entries(types)
        .sort((a, b) => b[1] - a[1])
        .map(([type, count]) => `
          <div class="attraction-type-card">
            <div class="attraction-type-name">${type}</div>
            <div class="attraction-type-count">${count} attraction${count > 1 ? 's' : ''}</div>
          </div>
        `).join('');
    }

    function renderCitiesPanel() {
      // Geographic clustering: Group by city
      const cityClusters = {};
      PLAN_DATA.days.forEach(day => {
        (day.attractions || []).forEach(attr => {
          const city = day.location;
          if (!cityClusters[city]) cityClusters[city] = [];
          cityClusters[city].push({ ...attr, location: day.location });
        });
      });

      const container = document.getElementById('cities-container');
      container.innerHTML = Object.entries(cityClusters).map(([city, attractions]) => {
        // Remove duplicates
        const uniqueAttractions = attractions.filter((attr, idx, self) =>
          idx === self.findIndex(a => a.name === attr.name)
        );

        return `
          <div class="city-cluster" id="city-${city.replace(/\s+/g, '-')}">
            <div class="city-cluster-header">${city} (${uniqueAttractions.length} attractions)</div>
            <div class="city-attractions">
              ${uniqueAttractions.map(attr => {
                const links = generateMapLinks(attr.name, attr.location);
                return `
                  <div class="attraction-item">
                    <div class="attraction-name">${attr.name}</div>
                    <div class="attraction-links">
                      <a href="${links.mapLink}" target="_blank" class="attraction-link ${links.isMainland ? 'gaode' : 'google'}">
                        ${links.isMainland ? 'Gaode Maps' : 'Google Maps'}
                      </a>
                      <a href="${links.rednote}" target="_blank" class="attraction-link rednote">
                        RedNote
                      </a>
                    </div>
                  </div>
                `;
              }).join('')}
            </div>
          </div>
        `;
      }).join('');
    }

    function renderDays() {
      const container = document.getElementById('days-container');
      container.innerHTML = PLAN_DATA.days.map(day => `
        <div class="day-card">
          <div class="day-header" onclick="toggleDay(${day.day})">
            <div>
              <strong>Day ${day.day}</strong> - ${day.date} - ${day.location}
            </div>
            <div>${CURRENCY_CONFIG.currency_symbol}${toEUR(day.budget?.total || 0)}</div>
          </div>
          <div class="day-content" id="day-${day.day}">
            ${renderDayContent(day)}
          </div>
        </div>
      `).join('');
    }

    function renderDayContent(day) {
      let html = '';

      // Location change
      if (day.location_change) {
        html += `<div class="section">
          <h3>Transportation</h3>
          <p><strong>${day.location_change.from} → ${day.location_change.to}</strong></p>
          <p>${day.location_change.transportation} • ${day.location_change.departure_time} - ${day.location_change.arrival_time}</p>
          <p class="cost">${CURRENCY_CONFIG.currency_symbol}${toEUR(day.location_change.cost)}</p>
        </div>`;
      }

      // Timeline
      if (day.timeline && Object.keys(day.timeline).length > 0) {
        html += '<div class="section"><h3>Timeline</h3>';
        Object.entries(day.timeline).forEach(([activity, time]) => {
          html += `<div class="timeline-item">
            <div class="timeline-time">${time.start_time} - ${time.end_time}</div>
            <div class="timeline-activity">${activity}</div>
          </div>`;
        });
        html += '</div>';
      }

      // Meals
      html += '<div class="section"><h3>Meals</h3><div class="activity-grid">';
      ['breakfast', 'lunch', 'dinner'].forEach(meal => {
        if (day[meal]?.name) {
          html += `<div class="activity-card">
            <h4>${meal.charAt(0).toUpperCase() + meal.slice(1)}</h4>
            <p>${day[meal].name}</p>
            <p>${day[meal].location}</p>
            <p class="cost">${CURRENCY_CONFIG.currency_symbol}${toEUR(day[meal].cost)}</p>
          </div>`;
        }
      });
      html += '</div></div>';

      // Attractions
      if (day.attractions?.length > 0) {
        html += '<div class="section"><h3>Attractions</h3><div class="activity-grid">';
        day.attractions.forEach(attr => {
          const links = generateMapLinks(attr.name, attr.location);
          html += `<div class="activity-card">
            <h4>${attr.name}</h4>
            <p>${attr.location}</p>
            <p class="cost">${CURRENCY_CONFIG.currency_symbol}${toEUR(attr.cost)}</p>
            <div class="attraction-links" style="margin-top: 10px;">
              <a href="${links.mapLink}" target="_blank" class="attraction-link ${links.isMainland ? 'gaode' : 'google'}">
                ${links.isMainland ? 'Gaode' : 'Google'}
              </a>
              <a href="${links.rednote}" target="_blank" class="attraction-link rednote">
                RedNote
              </a>
            </div>
          </div>`;
        });
        html += '</div></div>';
      }

      // Entertainment & Shopping
      ['entertainment', 'shopping'].forEach(category => {
        if (day[category]?.length > 0) {
          html += `<div class="section"><h3>${category.charAt(0).toUpperCase() + category.slice(1)}</h3><div class="activity-grid">`;
          day[category].forEach(item => {
            html += `<div class="activity-card">
              <h4>${item.name}</h4>
              <p>${item.location}</p>
              <p class="cost">${CURRENCY_CONFIG.currency_symbol}${toEUR(item.cost)}</p>
            </div>`;
          });
          html += '</div></div>';
        }
      });

      return html;
    }

    function renderEmergencyInfo() {
      const emergency = PLAN_DATA.emergency_info;
      let html = '<div class="section"><h3>Hospitals</h3><ul>';
      (emergency?.hospitals || []).forEach(h => {
        html += `<li>${h.name} - ${h.phone}</li>`;
      });
      html += '</ul></div><button class="btn" onclick="closePanel()">Close</button>';
      document.getElementById('emergency-content').innerHTML = html;
    }

    function toggleDay(dayNum) {
      const content = document.getElementById(`day-${dayNum}`);
      content.classList.toggle('active');
    }

    function openEmergencyPanel() {
      document.getElementById('emergency-panel').classList.add('active');
    }

    function closePanel() {
      document.getElementById('emergency-panel').classList.remove('active');
    }

    // Initialize on load
    init();
  </script>
</body>
</html>
HTML_TEMPLATE

# Inject merged data into HTML using Python for safe JSON handling
TMP_DATA="/tmp/plan-data-$$.json"
echo "$MERGED_DATA" > "$TMP_DATA"

python3 <<PYTHON_INJECT
import json

# Load data
with open('$TMP_DATA', 'r') as f:
    merged_data = f.read()

# Read HTML template
with open('$OUTPUT_FILE', 'r', encoding='utf-8') as f:
    html_content = f.read()

# Replace placeholders
html_content = html_content.replace('PLAN_DATA_INJECTION', merged_data)
html_content = html_content.replace('DESTINATION_TITLE', '$DESTINATION_SLUG')

# Write back
with open('$OUTPUT_FILE', 'w', encoding='utf-8') as f:
    f.write(html_content)
PYTHON_INJECT

rm -f "$TMP_DATA"

echo "✓ Generated HTML: $OUTPUT_FILE"
exit 0
