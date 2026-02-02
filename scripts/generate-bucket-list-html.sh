#!/bin/bash
# Generate Bucket List HTML for China Exchange Semester Guide
# Usage: ./generate-bucket-list-html.sh <destination-slug>

set -e

DESTINATION_SLUG="$1"
DATA_DIR="/root/travel-planner/data/${DESTINATION_SLUG}"
OUTPUT_FILE="/root/travel-planner/china-exchange-bucket-list-2026.html"

if [ -z "$DESTINATION_SLUG" ]; then
    echo "Error: Please provide destination slug"
    echo "Usage: $0 <destination-slug>"
    exit 1
fi

if [ ! -d "$DATA_DIR" ]; then
    echo "Error: Data directory not found: $DATA_DIR"
    exit 1
fi

# Verify all required JSON files exist
REQUIRED_FILES=(
    "requirements-skeleton.json"
    "plan-skeleton.json"
    "attractions.json"
    "accommodation.json"
    "meals.json"
    "transportation.json"
    "entertainment.json"
    "shopping.json"
    "timeline.json"
    "budget.json"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$DATA_DIR/$file" ]; then
        echo "Error: Required file not found: $file"
        exit 1
    fi
done

echo "Generating Bucket List HTML..."
echo "Data directory: $DATA_DIR"
echo "Output file: $OUTPUT_FILE"

# Generate HTML using Python script
python3 - <<'PYTHON_SCRIPT'
import json
import sys
from pathlib import Path
from datetime import datetime

# Read destination slug from environment
destination_slug = sys.argv[1] if len(sys.argv) > 1 else "china-exchange-bucket-list-2026"
data_dir = Path(f"/root/travel-planner/data/{destination_slug}")

# Load all JSON files
requirements = json.loads((data_dir / "requirements-skeleton.json").read_text())
plan = json.loads((data_dir / "plan-skeleton.json").read_text())
attractions_data = json.loads((data_dir / "attractions.json").read_text())
accommodation_data = json.loads((data_dir / "accommodation.json").read_text())
meals_data = json.loads((data_dir / "meals.json").read_text())
transportation_data = json.loads((data_dir / "transportation.json").read_text())
entertainment_data = json.loads((data_dir / "entertainment.json").read_text())
shopping_data = json.loads((data_dir / "shopping.json").read_text())
timeline_data = json.loads((data_dir / "timeline.json").read_text())
budget_data = json.loads((data_dir / "budget.json").read_text())

# Build city data dictionary
cities_data = {}
for city_obj in plan["cities"]:
    city_name = city_obj["city"]
    cities_data[city_name] = {
        "basics": city_obj,
        "attractions": None,
        "accommodation": None,
        "meals": None,
        "transportation": None,
        "entertainment": None,
        "shopping": None,
        "timeline": None,
        "budget": None
    }

# Merge attractions
for city_obj in attractions_data.get("cities", []):
    city_name = city_obj["city"]
    if city_name in cities_data:
        cities_data[city_name]["attractions"] = city_obj.get("attractions", [])

# Merge accommodation
for city_obj in accommodation_data.get("cities", []):
    city_name = city_obj["city"]
    if city_name in cities_data:
        cities_data[city_name]["accommodation"] = city_obj.get("hotels", [])

# Merge meals
for city_obj in meals_data.get("cities", []):
    city_name = city_obj["city"]
    if city_name in cities_data:
        cities_data[city_name]["meals"] = city_obj

# Merge transportation
for city_obj in transportation_data.get("cities", []):
    city_name = city_obj["city"]
    if city_name in cities_data:
        cities_data[city_name]["transportation"] = city_obj

# Merge entertainment
for city_obj in entertainment_data.get("cities", []):
    city_name = city_obj["city"]
    if city_name in cities_data:
        cities_data[city_name]["entertainment"] = city_obj

# Merge shopping
for city_obj in shopping_data.get("cities", []):
    city_name = city_obj["city"]
    if city_name in cities_data:
        cities_data[city_name]["shopping"] = city_obj

# Merge timeline
for city_obj in timeline_data.get("cities", []):
    city_name = city_obj["city"]
    if city_name in cities_data:
        cities_data[city_name]["timeline"] = city_obj.get("sample_itinerary", {})

# Merge budget
for city_obj in budget_data.get("cities", []):
    city_name = city_obj["city"]
    if city_name in cities_data:
        cities_data[city_name]["budget"] = city_obj

# Generate HTML
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>China Exchange Semester Bucket List 2026</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            line-height: 1.6;
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        header {{
            text-align: center;
            color: white;
            padding: 40px 20px;
            margin-bottom: 40px;
        }}

        header h1 {{
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}

        header p {{
            font-size: 1.2em;
            opacity: 0.95;
        }}

        .exchange-info {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}

        .exchange-info h2 {{
            color: #667eea;
            margin-bottom: 20px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}

        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}

        .info-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }}

        .info-card h3 {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
        }}

        .info-card p {{
            font-size: 1.1em;
            font-weight: 600;
            color: #333;
        }}

        .cities-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 30px;
            margin-top: 30px;
        }}

        .city-card {{
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}

        .city-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.3);
        }}

        .city-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            cursor: pointer;
            position: relative;
        }}

        .city-header h2 {{
            font-size: 2em;
            margin-bottom: 5px;
        }}

        .city-header .chinese {{
            font-size: 1.2em;
            opacity: 0.9;
            margin-bottom: 10px;
        }}

        .city-meta {{
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 15px;
            font-size: 0.9em;
        }}

        .meta-item {{
            background: rgba(255,255,255,0.2);
            padding: 5px 12px;
            border-radius: 20px;
        }}

        .budget-badge {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(255,255,255,0.95);
            color: #667eea;
            padding: 8px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 1.1em;
        }}

        .budget-badge.over {{
            background: #ff6b6b;
            color: white;
        }}

        .budget-badge.under {{
            background: #51cf66;
            color: white;
        }}

        .city-content {{
            padding: 25px;
            display: none;
        }}

        .city-content.active {{
            display: block;
        }}

        .section {{
            margin-bottom: 25px;
        }}

        .section h3 {{
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.3em;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 8px;
        }}

        .attraction-item, .hotel-item, .restaurant-item, .activity-item {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 12px;
            border-left: 4px solid #667eea;
        }}

        .item-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 8px;
        }}

        .item-name {{
            font-weight: 600;
            font-size: 1.1em;
            color: #333;
        }}

        .item-chinese {{
            color: #666;
            font-size: 0.9em;
            margin-top: 2px;
        }}

        .item-price {{
            background: #667eea;
            color: white;
            padding: 4px 10px;
            border-radius: 15px;
            font-size: 0.9em;
            font-weight: 600;
        }}

        .item-description {{
            color: #666;
            margin: 8px 0;
            font-size: 0.95em;
        }}

        .item-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
        }}

        .tag {{
            background: #e9ecef;
            color: #495057;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.85em;
        }}

        .timeline-day {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
        }}

        .timeline-day h4 {{
            color: #667eea;
            margin-bottom: 12px;
            font-size: 1.1em;
        }}

        .timeline-item {{
            display: flex;
            align-items: start;
            padding: 8px 0;
            border-bottom: 1px solid #dee2e6;
        }}

        .timeline-item:last-child {{
            border-bottom: none;
        }}

        .timeline-time {{
            font-weight: 600;
            color: #667eea;
            min-width: 100px;
            font-size: 0.9em;
        }}

        .timeline-activity {{
            flex: 1;
            color: #495057;
            font-size: 0.95em;
        }}

        .budget-breakdown {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
        }}

        .budget-item {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #dee2e6;
        }}

        .budget-item:last-child {{
            border-bottom: none;
            font-weight: 700;
            font-size: 1.1em;
            margin-top: 10px;
            padding-top: 15px;
            border-top: 2px solid #667eea;
        }}

        .recommendations {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
        }}

        .recommendations h4 {{
            color: #856404;
            margin-bottom: 10px;
        }}

        .recommendations ul {{
            margin-left: 20px;
            color: #856404;
        }}

        .tips {{
            background: #d1ecf1;
            border-left: 4px solid #17a2b8;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
        }}

        .tips h4 {{
            color: #0c5460;
            margin-bottom: 10px;
        }}

        .tips ul {{
            margin-left: 20px;
            color: #0c5460;
        }}

        .toggle-all {{
            text-align: center;
            margin: 30px 0;
        }}

        .toggle-btn {{
            background: white;
            color: #667eea;
            border: 2px solid white;
            padding: 12px 30px;
            border-radius: 25px;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }}

        .toggle-btn:hover {{
            background: #667eea;
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 7px 20px rgba(0,0,0,0.3);
        }}

        footer {{
            text-align: center;
            color: white;
            padding: 40px 20px;
            margin-top: 50px;
            font-size: 0.95em;
        }}

        footer a {{
            color: white;
            text-decoration: underline;
        }}

        @media (max-width: 768px) {{
            header h1 {{
                font-size: 2em;
            }}

            .cities-grid {{
                grid-template-columns: 1fr;
            }}

            .city-header h2 {{
                font-size: 1.5em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎓 China Exchange Semester Bucket List</h1>
            <p>Tsinghua University · Spring 2026 · 10 Amazing Cities to Explore</p>
        </header>
"""

# Add exchange program info
exchange_info = requirements["trip_summary"]["exchange_program"]
bucket_list_period = requirements["trip_summary"]["bucket_list_period"]

html += f"""
        <div class="exchange-info">
            <h2>📚 Exchange Program Information</h2>
            <div class="info-grid">
                <div class="info-card">
                    <h3>University</h3>
                    <p>{exchange_info["university"]}</p>
                </div>
                <div class="info-card">
                    <h3>Location</h3>
                    <p>{exchange_info["location"]}</p>
                </div>
                <div class="info-card">
                    <h3>Duration</h3>
                    <p>{exchange_info["start_date"]} to {exchange_info["end_date"]}</p>
                </div>
                <div class="info-card">
                    <h3>Class Schedule</h3>
                    <p>{exchange_info["class_schedule"]}</p>
                </div>
                <div class="info-card">
                    <h3>Travel Time</h3>
                    <p>{exchange_info["available_travel_days"]}</p>
                </div>
                <div class="info-card">
                    <h3>Budget per Trip</h3>
                    <p>€500</p>
                </div>
            </div>
        </div>

        <div class="toggle-all">
            <button class="toggle-btn" onclick="toggleAll()">Expand All Cities</button>
        </div>

        <div class="cities-grid">
"""

# Generate city cards
for city_name, city_data in cities_data.items():
    basics = city_data["basics"]
    budget = city_data["budget"]

    # Determine budget status
    budget_status = ""
    budget_class = ""
    if budget:
        status = budget.get("budget_status", "")
        total_cost = budget["budget_breakdown"]["total_trip_cost"]
        if "OVER" in status:
            budget_class = "over"
            budget_status = f"€{total_cost:.0f}"
        elif "UNDER" in status:
            budget_class = "under"
            budget_status = f"€{total_cost:.0f}"
        else:
            budget_status = f"€{total_cost:.0f}"

    html += f"""
            <div class="city-card">
                <div class="city-header" onclick="toggleCity('{city_name}')">
                    <div class="budget-badge {budget_class}">{budget_status}</div>
                    <h2>{city_name}</h2>
                    <div class="chinese">{basics.get('city_chinese', '')}</div>
                    <div class="city-meta">
                        <span class="meta-item">📅 {basics.get('recommended_duration', 'N/A')}</span>
                        <span class="meta-item">🌸 Best: {', '.join(basics.get('best_months', []))}</span>
                    </div>
                </div>
                <div class="city-content" id="content-{city_name}">
"""

    # Attractions section
    if city_data["attractions"]:
        html += """
                    <div class="section">
                        <h3>🏛️ Top Attractions</h3>
"""
        for attraction in city_data["attractions"][:5]:  # Top 5
            price = attraction.get("ticket_price_eur", 0)
            price_str = "Free" if price == 0 else f"€{price}"
            duration = attraction.get("recommended_duration_hours", "N/A")

            html += f"""
                        <div class="attraction-item">
                            <div class="item-header">
                                <div>
                                    <div class="item-name">{attraction.get('name', 'N/A')}</div>
                                    <div class="item-chinese">{attraction.get('name_chinese', '')}</div>
                                </div>
                                <div class="item-price">{price_str}</div>
                            </div>
                            <div class="item-description">{attraction.get('why_visit', attraction.get('description', ''))[:150]}...</div>
                            <div class="item-tags">
                                <span class="tag">⏱️ {duration}h</span>
                                <span class="tag">📍 {attraction.get('type', '').replace('_', ' ').title()}</span>
                            </div>
                        </div>
"""
        html += """
                    </div>
"""

    # Accommodation section
    if city_data["accommodation"]:
        html += """
                    <div class="section">
                        <h3>🏨 Recommended Hotels</h3>
"""
        for hotel in city_data["accommodation"][:3]:  # Top 3
            price = hotel.get("price_per_night_eur", 0)

            html += f"""
                        <div class="hotel-item">
                            <div class="item-header">
                                <div>
                                    <div class="item-name">{hotel.get('name', 'N/A')}</div>
                                    <div class="item-chinese">{hotel.get('name_chinese', '')}</div>
                                </div>
                                <div class="item-price">€{price}/night</div>
                            </div>
                            <div class="item-description">{hotel.get('why_recommended', '')[:150]}</div>
                            <div class="item-tags">
                                <span class="tag">📍 {hotel.get('location', '')}</span>
                                <span class="tag">{hotel.get('category', '').replace('_', ' ').title()}</span>
                            </div>
                        </div>
"""
        html += """
                    </div>
"""

    # Sample itinerary
    if city_data["timeline"]:
        html += """
                    <div class="section">
                        <h3>📅 Sample Itinerary</h3>
"""
        for day_key, day_data in list(city_data["timeline"].items())[:3]:  # First 3 days
            if not isinstance(day_data, dict):
                continue

            day_num = day_key.replace("day_", "Day ")
            theme = day_data.get("theme", "")
            timeline = day_data.get("timeline", {})

            html += f"""
                        <div class="timeline-day">
                            <h4>{day_num}: {theme}</h4>
"""
            for time_slot, activity in list(timeline.items())[:6]:  # First 6 activities
                if isinstance(activity, dict):
                    activity_name = activity.get("activity", "")
                    html += f"""
                            <div class="timeline-item">
                                <div class="timeline-time">{time_slot}</div>
                                <div class="timeline-activity">{activity_name}</div>
                            </div>
"""
            html += """
                        </div>
"""
        html += """
                    </div>
"""

    # Budget breakdown
    if budget:
        html += """
                    <div class="section">
                        <h3>💰 Budget Breakdown</h3>
                        <div class="budget-breakdown">
"""
        breakdown = budget["budget_breakdown"]
        html += f"""
                            <div class="budget-item">
                                <span>Transportation</span>
                                <span>€{breakdown.get('transportation', {}).get('total', 0)}</span>
                            </div>
                            <div class="budget-item">
                                <span>Accommodation</span>
                                <span>€{breakdown.get('accommodation', {}).get('total', 0)}</span>
                            </div>
                            <div class="budget-item">
                                <span>Meals</span>
                                <span>€{breakdown.get('meals', {}).get('total', 0)}</span>
                            </div>
                            <div class="budget-item">
                                <span>Attractions</span>
                                <span>€{breakdown.get('attractions', {}).get('total', 0)}</span>
                            </div>
                            <div class="budget-item">
                                <span>Entertainment</span>
                                <span>€{breakdown.get('entertainment', {}).get('total', 0)}</span>
                            </div>
                            <div class="budget-item">
                                <span>Shopping</span>
                                <span>€{breakdown.get('shopping', 0)}</span>
                            </div>
                            <div class="budget-item">
                                <span>Total Trip Cost</span>
                                <span>€{breakdown.get('total_trip_cost', 0)}</span>
                            </div>
"""
        html += """
                        </div>
"""

        # Recommendations if over budget
        if budget.get("recommendations"):
            html += """
                        <div class="recommendations">
                            <h4>💡 Budget Recommendations</h4>
                            <ul>
"""
            for rec in budget["recommendations"][:3]:  # Top 3 recommendations
                html += f"                                <li>{rec}</li>\n"
            html += """
                            </ul>
                        </div>
"""

        # Money saving tips
        if budget.get("money_saving_tips"):
            html += """
                        <div class="tips">
                            <h4>💵 Money-Saving Tips</h4>
                            <ul>
"""
            for tip in budget["money_saving_tips"][:5]:  # Top 5 tips
                html += f"                                <li>{tip}</li>\n"
            html += """
                            </ul>
                        </div>
"""

        html += """
                    </div>
"""

    html += """
                </div>
            </div>
"""

# Close cities grid and add footer
html += """
        </div>

        <footer>
            <p>🌏 Generated for China Exchange Semester 2026</p>
            <p>Generated with <a href="https://claude.ai/code">Claude Code</a> via <a href="https://happy.engineering">Happy</a></p>
        </footer>
    </div>

    <script>
        function toggleCity(cityName) {
            const content = document.getElementById('content-' + cityName);
            content.classList.toggle('active');
        }

        let allExpanded = false;
        function toggleAll() {
            const contents = document.querySelectorAll('.city-content');
            const btn = document.querySelector('.toggle-btn');

            if (allExpanded) {
                contents.forEach(c => c.classList.remove('active'));
                btn.textContent = 'Expand All Cities';
                allExpanded = false;
            } else {
                contents.forEach(c => c.classList.add('active'));
                btn.textContent = 'Collapse All Cities';
                allExpanded = true;
            }
        }
    </script>
</body>
</html>
"""

# Write HTML file
output_path = Path("/root/travel-planner/china-exchange-bucket-list-2026.html")
output_path.write_text(html, encoding='utf-8')

print(f"✅ HTML generated successfully: {output_path}")
print(f"📊 Cities included: {len(cities_data)}")
print(f"📄 File size: {output_path.stat().st_size / 1024:.1f} KB")

PYTHON_SCRIPT

echo ""
echo "✅ Bucket List HTML generation complete!"
echo "📄 Output: $OUTPUT_FILE"
