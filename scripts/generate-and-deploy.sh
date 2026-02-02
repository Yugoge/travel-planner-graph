#!/usr/bin/env bash
# Unified atomic script: Generate HTML + Deploy to GitHub Pages
# Usage: generate-and-deploy.sh <destination-slug> [version-suffix]
# Exit codes: 0=success, 1=generation failed, 2=deployment failed, 3=missing files

set -euo pipefail

DESTINATION_SLUG="${1:?Missing required destination-slug}"
VERSION_SUFFIX="${2:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DATA_DIR="${PROJECT_ROOT}/data/${DESTINATION_SLUG}"

echo "=================================================="
echo "🚀 Unified Generate + Deploy"
echo "Destination: ${DESTINATION_SLUG}"
echo "Version: ${VERSION_SUFFIX:-default}"
echo "=================================================="

# Step 1: Auto-detect project type (itinerary vs bucket list)
echo ""
echo "📋 Step 1: Detecting project type..."

PROJECT_TYPE="unknown"

if [[ -f "${DATA_DIR}/plan-skeleton.json" ]]; then
  # Check if it's a bucket list (has "cities" array) or itinerary (has "days" array)
  if jq -e '.cities' "${DATA_DIR}/plan-skeleton.json" > /dev/null 2>&1; then
    PROJECT_TYPE="bucket-list"
  elif jq -e '.days' "${DATA_DIR}/plan-skeleton.json" > /dev/null 2>&1; then
    PROJECT_TYPE="itinerary"
  fi
fi

if [[ "$PROJECT_TYPE" == "unknown" ]]; then
  echo "❌ Error: Cannot detect project type"
  echo "   Plan skeleton must have 'days' array (itinerary) or 'cities' array (bucket list)"
  exit 3
fi

echo "✓ Detected project type: ${PROJECT_TYPE}"

# Step 2: Generate HTML using Python module
echo ""
echo "📋 Step 2: Generating HTML..."

OUTPUT_FILE="${PROJECT_ROOT}/travel-plan-${DESTINATION_SLUG}${VERSION_SUFFIX}.html"

# Activate virtual environment
if [[ -f "${PROJECT_ROOT}/venv/bin/activate" ]]; then
  source "${PROJECT_ROOT}/venv/bin/activate"
elif [[ -f /root/.claude/venv/bin/activate ]]; then
  source /root/.claude/venv/bin/activate
else
  echo "❌ Error: Virtual environment not found"
  exit 3
fi

# Use Python module to generate HTML
python - <<PYTHON_SCRIPT
import json
import sys
from pathlib import Path
from datetime import datetime

# Configuration
destination_slug = "${DESTINATION_SLUG}"
version_suffix = "${VERSION_SUFFIX}"
project_type = "${PROJECT_TYPE}"
data_dir = Path("${DATA_DIR}")
output_file = Path("${OUTPUT_FILE}")

# Load required files
try:
    plan_skeleton = json.loads((data_dir / "plan-skeleton.json").read_text())
except FileNotFoundError:
    print(f"❌ Error: plan-skeleton.json not found in {data_dir}", file=sys.stderr)
    sys.exit(3)

# Load agent outputs (graceful handling of missing files)
def load_json_safe(filename):
    try:
        return json.loads((data_dir / filename).read_text())
    except FileNotFoundError:
        return {}

meals = load_json_safe("meals.json")
accommodation = load_json_safe("accommodation.json")
attractions = load_json_safe("attractions.json")
entertainment = load_json_safe("entertainment.json")
shopping = load_json_safe("shopping.json")
transportation = load_json_safe("transportation.json")
timeline = load_json_safe("timeline.json")
budget = load_json_safe("budget.json")

# Generate HTML based on project type
if project_type == "itinerary":
    # Merge data for itinerary
    merged_data = plan_skeleton.copy()

    # Merge agent data into days
    if "days" in merged_data:
        for day in merged_data["days"]:
            day_num = day.get("day")

            # Find corresponding data in agent outputs
            if meals.get("data", {}).get("days"):
                meal_day = next((d for d in meals["data"]["days"] if d["day"] == day_num), {})
                day.update({
                    "breakfast": meal_day.get("breakfast", {}),
                    "lunch": meal_day.get("lunch", {}),
                    "dinner": meal_day.get("dinner", {})
                })

            if attractions.get("data", {}).get("days"):
                attr_day = next((d for d in attractions["data"]["days"] if d["day"] == day_num), {})
                day["attractions"] = attr_day.get("attractions", [])

            if entertainment.get("data", {}).get("days"):
                ent_day = next((d for d in entertainment["data"]["days"] if d["day"] == day_num), {})
                day["entertainment"] = ent_day.get("entertainment", [])

            if shopping.get("data", {}).get("days"):
                shop_day = next((d for d in shopping["data"]["days"] if d["day"] == day_num), {})
                day["shopping"] = shop_day.get("shopping", [])

            if accommodation.get("data", {}).get("days"):
                acc_day = next((d for d in accommodation["data"]["days"] if d["day"] == day_num), {})
                day["accommodation"] = acc_day.get("accommodation", {})

            if timeline.get("data", {}).get("days"):
                time_day = next((d for d in timeline["data"]["days"] if d["day"] == day_num), {})
                day["timeline"] = time_day.get("timeline", {})

            if budget.get("data", {}).get("days"):
                budg_day = next((d for d in budget["data"]["days"] if d["day"] == day_num), {})
                day["budget"] = budg_day.get("budget", {})

            if transportation.get("data", {}).get("days"):
                trans_day = next((d for d in transportation["data"]["days"] if d["day"] == day_num), {})
                if day.get("location_change"):
                    day["location_change"] = trans_day.get("location_change")

elif project_type == "bucket-list":
    # Merge data for bucket list
    merged_data = plan_skeleton.copy()

    if "cities" in merged_data:
        for city in merged_data["cities"]:
            city_name = city.get("city")

            # Find corresponding data in agent outputs
            if attractions.get("cities"):
                city_data = next((c for c in attractions["cities"] if c["city"] == city_name), {})
                city["attractions"] = city_data.get("attractions", [])

            if accommodation.get("cities"):
                city_data = next((c for c in accommodation["cities"] if c["city"] == city_name), {})
                city["hotels"] = city_data.get("hotels", [])

            if meals.get("cities"):
                city_data = next((c for c in meals["cities"] if c["city"] == city_name), {})
                city["restaurants"] = city_data.get("restaurants", [])

            if entertainment.get("cities"):
                city_data = next((c for c in entertainment["cities"] if c["city"] == city_name), {})
                city["entertainment"] = city_data.get("entertainment", [])

            if shopping.get("cities"):
                city_data = next((c for c in shopping["cities"] if c["city"] == city_name), {})
                city["shopping"] = city_data.get("shopping", [])

            if transportation.get("cities"):
                city_data = next((c for c in transportation["cities"] if c["city"] == city_name), {})
                city["transportation"] = city_data.get("transportation", {})

# Generate HTML template
html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Travel Plan - {destination_slug}</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      line-height: 1.6;
      color: #333;
      background: #f5f5f5;
    }}
    .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
    .header {{
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 40px 20px;
      border-radius: 12px;
      margin-bottom: 20px;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
    .header .meta {{ font-size: 1.1em; opacity: 0.9; }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 15px;
      margin-bottom: 20px;
    }}
    .stat-card {{
      background: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      transition: transform 0.3s;
    }}
    .stat-card:hover {{ transform: translateY(-5px); }}
    .stat-card .value {{ font-size: 2em; font-weight: bold; color: #667eea; }}
    .stat-card .label {{ color: #666; font-size: 0.9em; }}
    .day-card {{
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      margin-bottom: 20px;
      overflow: hidden;
    }}
    .day-header {{
      background: #667eea;
      color: white;
      padding: 15px 20px;
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .day-header:hover {{ background: #5568d3; }}
    .day-content {{
      padding: 20px;
      display: none;
    }}
    .day-content.active {{ display: block; }}
    .timeline-item {{
      border-left: 3px solid #667eea;
      padding-left: 20px;
      margin-bottom: 20px;
      position: relative;
    }}
    .timeline-item::before {{
      content: '';
      position: absolute;
      left: -7px;
      top: 0;
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background: #667eea;
    }}
    .timeline-time {{ font-weight: bold; color: #667eea; }}
    .activity-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 15px;
      margin-top: 20px;
    }}
    .activity-card {{
      background: #f9f9f9;
      padding: 15px;
      border-radius: 6px;
      border-left: 4px solid #667eea;
    }}
    .activity-card h4 {{ color: #667eea; margin-bottom: 8px; }}
    .activity-card .cost {{ color: #e74c3c; font-weight: bold; }}
    .section {{ margin-bottom: 30px; }}
    .section h3 {{ color: #667eea; margin-bottom: 15px; }}
    @media (max-width: 768px) {{
      .header h1 {{ font-size: 1.8em; }}
      .activity-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1 id="trip-title">Loading...</h1>
      <div class="meta" id="trip-meta"></div>
    </div>
    <div class="stats" id="stats-container"></div>
    <div id="content-container"></div>
  </div>
  <script>
    const PLAN_DATA = {json.dumps(merged_data)};
    const PROJECT_TYPE = "{project_type}";

    function init() {{
      renderHeader();
      renderStats();
      renderContent();
    }}

    function renderHeader() {{
      if (PROJECT_TYPE === "itinerary" && PLAN_DATA.days) {{
        const firstDay = PLAN_DATA.days[0];
        const lastDay = PLAN_DATA.days[PLAN_DATA.days.length - 1];
        document.getElementById('trip-title').textContent = `${{firstDay.location}} Travel Plan`;
        document.getElementById('trip-meta').textContent =
          `${{firstDay.date}} to ${{lastDay.date}} • ${{PLAN_DATA.days.length}} days`;
      }} else if (PROJECT_TYPE === "bucket-list" && PLAN_DATA.cities) {{
        document.getElementById('trip-title').textContent = PLAN_DATA.title || "Travel Bucket List";
        document.getElementById('trip-meta').textContent = `${{PLAN_DATA.cities.length}} cities to explore`;
      }}
    }}

    function renderStats() {{
      let stats = [];
      if (PROJECT_TYPE === "itinerary" && PLAN_DATA.days) {{
        const totalBudget = PLAN_DATA.days.reduce((sum, day) => sum + (day.budget?.total || 0), 0);
        const totalAttractions = PLAN_DATA.days.reduce((sum, day) => sum + (day.attractions?.length || 0), 0);
        stats = [
          {{ label: 'Days', value: PLAN_DATA.days.length }},
          {{ label: 'Total Budget', value: `$${{totalBudget}}` }},
          {{ label: 'Attractions', value: totalAttractions }},
          {{ label: 'Cities', value: new Set(PLAN_DATA.days.map(d => d.location)).size }}
        ];
      }} else if (PROJECT_TYPE === "bucket-list" && PLAN_DATA.cities) {{
        const totalAttractions = PLAN_DATA.cities.reduce((sum, city) => sum + (city.attractions?.length || 0), 0);
        stats = [
          {{ label: 'Cities', value: PLAN_DATA.cities.length }},
          {{ label: 'Attractions', value: totalAttractions }},
          {{ label: 'Hotels', value: PLAN_DATA.cities.reduce((sum, c) => sum + (c.hotels?.length || 0), 0) }},
          {{ label: 'Restaurants', value: PLAN_DATA.cities.reduce((sum, c) => sum + (c.restaurants?.length || 0), 0) }}
        ];
      }}

      document.getElementById('stats-container').innerHTML = stats.map(s => `
        <div class="stat-card">
          <div class="value">${{s.value}}</div>
          <div class="label">${{s.label}}</div>
        </div>
      `).join('');
    }}

    function renderContent() {{
      if (PROJECT_TYPE === "itinerary" && PLAN_DATA.days) {{
        renderItinerary();
      }} else if (PROJECT_TYPE === "bucket-list" && PLAN_DATA.cities) {{
        renderBucketList();
      }}
    }}

    function renderItinerary() {{
      const container = document.getElementById('content-container');
      container.innerHTML = PLAN_DATA.days.map(day => `
        <div class="day-card">
          <div class="day-header" onclick="toggleDay(${{day.day}})">
            <div>
              <strong>Day ${{day.day}}</strong> - ${{day.date}} - ${{day.location}}
            </div>
            <div>Budget: $${{day.budget?.total || 0}}</div>
          </div>
          <div class="day-content" id="day-${{day.day}}">
            ${{renderDayContent(day)}}
          </div>
        </div>
      `).join('');
    }}

    function renderBucketList() {{
      const container = document.getElementById('content-container');
      container.innerHTML = PLAN_DATA.cities.map((city, idx) => `
        <div class="day-card">
          <div class="day-header" onclick="toggleDay(${{idx}})">
            <div><strong>${{city.city}}</strong> - ${{city.province || city.region || ''}}</div>
          </div>
          <div class="day-content" id="day-${{idx}}">
            ${{renderCityContent(city)}}
          </div>
        </div>
      `).join('');
    }}

    function renderDayContent(day) {{
      let html = '';

      if (day.timeline && Object.keys(day.timeline).length > 0) {{
        html += '<div class="section"><h3>📅 Timeline</h3>';
        Object.entries(day.timeline).forEach(([activity, time]) => {{
          html += `<div class="timeline-item">
            <div class="timeline-time">${{time.start_time}} - ${{time.end_time}}</div>
            <div class="timeline-activity">${{activity}}</div>
          </div>`;
        }});
        html += '</div>';
      }}

      if (day.breakfast?.name || day.lunch?.name || day.dinner?.name) {{
        html += '<div class="section"><h3>🍽️ Meals</h3><div class="activity-grid">';
        ['breakfast', 'lunch', 'dinner'].forEach(meal => {{
          if (day[meal]?.name) {{
            html += `<div class="activity-card">
              <h4>${{meal.charAt(0).toUpperCase() + meal.slice(1)}}</h4>
              <p>${{day[meal].name}}</p>
              <p>${{day[meal].location}}</p>
              <p class="cost">$${{day[meal].cost}}</p>
            </div>`;
          }}
        }});
        html += '</div></div>';
      }}

      if (day.attractions?.length > 0) {{
        html += '<div class="section"><h3>🎯 Attractions</h3><div class="activity-grid">';
        day.attractions.forEach(attr => {{
          html += `<div class="activity-card">
            <h4>${{attr.name}}</h4>
            <p>${{attr.location}}</p>
            <p class="cost">$${{attr.cost}}</p>
          </div>`;
        }});
        html += '</div></div>';
      }}

      return html;
    }}

    function renderCityContent(city) {{
      let html = '';

      if (city.attractions?.length > 0) {{
        html += '<div class="section"><h3>🎯 Attractions</h3><div class="activity-grid">';
        city.attractions.forEach(attr => {{
          html += `<div class="activity-card">
            <h4>${{attr.name}}</h4>
            <p>${{attr.address || attr.location || ''}}</p>
            <p>${{attr.description || ''}}</p>
          </div>`;
        }});
        html += '</div></div>';
      }}

      if (city.hotels?.length > 0) {{
        html += '<div class="section"><h3>🏨 Hotels</h3><div class="activity-grid">';
        city.hotels.forEach(hotel => {{
          html += `<div class="activity-card">
            <h4>${{hotel.name}}</h4>
            <p>${{hotel.address || hotel.location || ''}}</p>
            <p class="cost">$${{hotel.price_range || ''}}</p>
          </div>`;
        }});
        html += '</div></div>';
      }}

      if (city.restaurants?.length > 0) {{
        html += '<div class="section"><h3>🍽️ Restaurants</h3><div class="activity-grid">';
        city.restaurants.forEach(rest => {{
          html += `<div class="activity-card">
            <h4>${{rest.name}}</h4>
            <p>${{rest.cuisine || ''}}</p>
            <p>${{rest.address || rest.location || ''}}</p>
          </div>`;
        }});
        html += '</div></div>';
      }}

      return html;
    }}

    function toggleDay(dayNum) {{
      const content = document.getElementById(`day-${{dayNum}}`);
      content.classList.toggle('active');
    }}

    init();
  </script>
</body>
</html>'''

# Write HTML file
output_file.write_text(html_content)
print(f"✓ Generated HTML: {output_file}")
sys.exit(0)
PYTHON_SCRIPT

if [[ $? -ne 0 ]]; then
  echo "❌ Error: HTML generation failed"
  exit 1
fi

echo "✓ HTML generated successfully"

# Step 3: Deploy to GitHub Pages (atomic - cannot be skipped)
echo ""
echo "📋 Step 3: Deploying to GitHub Pages..."

# Check if deployment is possible
if [[ -z "${GITHUB_TOKEN:-}" ]] && [[ ! -f ~/.ssh/id_ed25519 ]] && [[ ! -f ~/.ssh/id_rsa ]]; then
  echo "⚠️  Warning: No GitHub authentication found"
  echo "   Skipping deployment (local file only)"
  echo "   To enable deployment, set GITHUB_TOKEN or configure SSH keys"
  echo ""
  echo "✓ Generation complete (local only): ${OUTPUT_FILE}"
  exit 0
fi

# Deploy using existing script
bash "${SCRIPT_DIR}/deploy-travel-plans.sh" "${OUTPUT_FILE}"

if [[ $? -ne 0 ]]; then
  echo "❌ Error: Deployment failed"
  exit 2
fi

echo ""
echo "=================================================="
echo "✅ Complete: Generated + Deployed"
echo "=================================================="
echo ""
echo "📄 Local file: ${OUTPUT_FILE}"
echo "🌐 Live URL will be shown in deploy script output above"
echo ""

exit 0
