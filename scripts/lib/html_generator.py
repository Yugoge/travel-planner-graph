#!/usr/bin/env python3
"""
Reusable HTML generator module for travel plans.

Supports both itinerary and bucket list project types.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union
from datetime import datetime


class TravelPlanHTMLGenerator:
    """Generate interactive HTML for travel plans."""

    def __init__(self, destination_slug: str, data_dir: Path):
        """
        Initialize generator.

        Args:
            destination_slug: Unique identifier for the trip
            data_dir: Directory containing agent JSON outputs
        """
        self.destination_slug = destination_slug
        self.data_dir = Path(data_dir)
        self.project_type: Optional[str] = None
        self.merged_data: Dict = {}

    def detect_project_type(self) -> str:
        """
        Auto-detect project type from plan skeleton.

        Returns:
            "itinerary" or "bucket-list"

        Raises:
            FileNotFoundError: If plan skeleton not found
            ValueError: If project type cannot be detected
        """
        skeleton_path = self.data_dir / "plan-skeleton.json"

        if not skeleton_path.exists():
            raise FileNotFoundError(f"Plan skeleton not found: {skeleton_path}")

        skeleton = json.loads(skeleton_path.read_text())

        if "days" in skeleton:
            return "itinerary"
        elif "cities" in skeleton:
            return "bucket-list"
        else:
            raise ValueError("Cannot detect project type: skeleton has neither 'days' nor 'cities'")

    def load_json_safe(self, filename: str) -> Dict:
        """
        Load JSON file with graceful error handling.

        Args:
            filename: Name of JSON file in data_dir

        Returns:
            Parsed JSON dict, or empty dict if file not found
        """
        try:
            return json.loads((self.data_dir / filename).read_text())
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON in {filename}: {e}", file=sys.stderr)
            return {}

    def merge_itinerary_data(self) -> Dict:
        """
        Merge all agent outputs for itinerary project type.

        Returns:
            Merged data dictionary
        """
        plan_skeleton = json.loads((self.data_dir / "plan-skeleton.json").read_text())

        # Load agent outputs
        meals = self.load_json_safe("meals.json")
        accommodation = self.load_json_safe("accommodation.json")
        attractions = self.load_json_safe("attractions.json")
        entertainment = self.load_json_safe("entertainment.json")
        shopping = self.load_json_safe("shopping.json")
        transportation = self.load_json_safe("transportation.json")
        timeline = self.load_json_safe("timeline.json")
        budget = self.load_json_safe("budget.json")

        merged = plan_skeleton.copy()

        # Merge data into each day
        for day in merged.get("days", []):
            day_num = day.get("day")

            # Helper function to find day data
            def find_day_data(agent_output: Dict, day_number: int) -> Dict:
                days_list = agent_output.get("data", {}).get("days", [])
                return next((d for d in days_list if d.get("day") == day_number), {})

            # Merge meals
            meal_day = find_day_data(meals, day_num)
            day.update({
                "breakfast": meal_day.get("breakfast", {}),
                "lunch": meal_day.get("lunch", {}),
                "dinner": meal_day.get("dinner", {})
            })

            # Merge other categories
            day["attractions"] = find_day_data(attractions, day_num).get("attractions", [])
            day["entertainment"] = find_day_data(entertainment, day_num).get("entertainment", [])
            day["shopping"] = find_day_data(shopping, day_num).get("shopping", [])
            day["accommodation"] = find_day_data(accommodation, day_num).get("accommodation", {})
            day["timeline"] = find_day_data(timeline, day_num).get("timeline", {})
            day["budget"] = find_day_data(budget, day_num).get("budget", {})

            # Merge transportation for location changes
            if day.get("location_change"):
                trans_day = find_day_data(transportation, day_num)
                day["location_change"] = trans_day.get("location_change")

        return merged

    def merge_bucket_list_data(self) -> Dict:
        """
        Merge all agent outputs for bucket list project type.

        Returns:
            Merged data dictionary
        """
        plan_skeleton = json.loads((self.data_dir / "plan-skeleton.json").read_text())

        # Load agent outputs
        attractions = self.load_json_safe("attractions.json")
        accommodation = self.load_json_safe("accommodation.json")
        meals = self.load_json_safe("meals.json")
        entertainment = self.load_json_safe("entertainment.json")
        shopping = self.load_json_safe("shopping.json")
        transportation = self.load_json_safe("transportation.json")

        merged = plan_skeleton.copy()

        # Merge data into each city
        for city in merged.get("cities", []):
            city_name = city.get("city")

            # Helper function to find city data
            def find_city_data(agent_output: Dict, city: str) -> Dict:
                cities_list = agent_output.get("cities", [])
                return next((c for c in cities_list if c.get("city") == city), {})

            # Merge data
            city["attractions"] = find_city_data(attractions, city_name).get("attractions", [])
            city["hotels"] = find_city_data(accommodation, city_name).get("hotels", [])
            city["restaurants"] = find_city_data(meals, city_name).get("restaurants", [])
            city["entertainment"] = find_city_data(entertainment, city_name).get("entertainment", [])
            city["shopping"] = find_city_data(shopping, city_name).get("shopping", [])
            city["transportation"] = find_city_data(transportation, city_name).get("transportation", {})

        return merged

    def generate_html(self, output_path: Path) -> None:
        """
        Generate HTML file.

        Args:
            output_path: Path to save generated HTML

        Raises:
            ValueError: If project type not detected
        """
        # Detect project type if not already set
        if not self.project_type:
            self.project_type = self.detect_project_type()

        # Merge data based on project type
        if self.project_type == "itinerary":
            self.merged_data = self.merge_itinerary_data()
        elif self.project_type == "bucket-list":
            self.merged_data = self.merge_bucket_list_data()
        else:
            raise ValueError(f"Unknown project type: {self.project_type}")

        # Generate HTML content
        html_content = self._generate_html_template()

        # Write to file
        output_path.write_text(html_content)
        print(f"✓ Generated HTML: {output_path}")

    def _generate_html_template(self) -> str:
        """
        Generate complete HTML template.

        Returns:
            HTML string
        """
        # Convert merged data to JSON string for embedding
        merged_json = json.dumps(self.merged_data)

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Travel Plan - {self.destination_slug}</title>
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
    const PLAN_DATA = {merged_json};
    const PROJECT_TYPE = "{self.project_type}";

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


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate travel plan HTML")
    parser.add_argument("destination_slug", help="Destination slug")
    parser.add_argument("--data-dir", help="Data directory path", required=True)
    parser.add_argument("--output", help="Output HTML file path", required=True)

    args = parser.parse_args()

    generator = TravelPlanHTMLGenerator(
        destination_slug=args.destination_slug,
        data_dir=Path(args.data_dir)
    )

    generator.generate_html(Path(args.output))


if __name__ == "__main__":
    main()
