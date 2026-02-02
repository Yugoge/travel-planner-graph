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
        Generate complete HTML template with premium Swiss Spa aesthetic.

        Returns:
            HTML string with Chart.js visualization and interactive features
        """
        # Convert merged data to JSON string for embedding
        merged_json = json.dumps(self.merged_data)

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Travel Plan - {self.destination_slug}</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    :root {{
      --color-primary: #F5F1E8;
      --color-secondary: #8B7355;
      --color-accent: #D4AF37;
      --color-dark: #4A3F35;
      --color-light: #FDFCFA;
      --color-neutral: #E8E3DA;
      --color-success: #8FAF7A;
      --color-warning: #D4A574;
      --color-danger: #B5695F;
      --space-xs: 8px;
      --space-sm: 16px;
      --space-md: 24px;
      --space-lg: 32px;
      --space-xl: 48px;
      --radius-sm: 4px;
      --radius-md: 8px;
      --radius-lg: 12px;
      --shadow-subtle: 0 1px 3px rgba(74, 63, 53, 0.08);
      --shadow-medium: 0 4px 6px rgba(74, 63, 53, 0.10);
      --shadow-large: 0 10px 20px rgba(74, 63, 53, 0.12);
    }}

    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      background: var(--color-primary);
      color: var(--color-dark);
      line-height: 1.6;
      min-height: 100vh;
    }}

    .container {{
      max-width: 1400px;
      margin: 0 auto;
      padding: var(--space-md);
    }}

    header {{
      text-align: center;
      padding: var(--space-xl) 0;
      margin-bottom: var(--space-lg);
    }}

    header h1 {{
      font-size: 2.5rem;
      font-weight: 300;
      color: var(--color-dark);
      margin-bottom: var(--space-sm);
      letter-spacing: -0.5px;
    }}

    header .subtitle {{
      font-size: 1rem;
      color: var(--color-secondary);
    }}

    .tabs {{
      display: flex;
      gap: var(--space-sm);
      margin-bottom: var(--space-lg);
      border-bottom: 2px solid var(--color-neutral);
      overflow-x: auto;
      padding-bottom: var(--space-xs);
    }}

    .tab {{
      background: transparent;
      border: none;
      padding: var(--space-sm) var(--space-md);
      font-size: 1rem;
      color: var(--color-secondary);
      cursor: pointer;
      transition: all 0.3s ease;
      white-space: nowrap;
      border-bottom: 3px solid transparent;
    }}

    .tab:hover {{
      color: var(--color-dark);
    }}

    .tab.active {{
      color: var(--color-accent);
      border-bottom-color: var(--color-accent);
      font-weight: 500;
    }}

    .tab-content {{
      display: none;
    }}

    .tab-content.active {{
      display: block;
    }}

    .stats-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: var(--space-md);
      margin-bottom: var(--space-xl);
    }}

    .stat-card {{
      background: var(--color-light);
      padding: var(--space-md);
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow-subtle);
      transition: transform 0.2s, box-shadow 0.2s;
    }}

    .stat-card:hover {{
      transform: translateY(-2px);
      box-shadow: var(--shadow-medium);
    }}

    .stat-icon {{
      font-size: 1.5rem;
      color: var(--color-accent);
      margin-bottom: var(--space-xs);
    }}

    .stat-value {{
      font-size: 1.8rem;
      font-weight: 600;
      color: var(--color-dark);
    }}

    .stat-label {{
      font-size: 0.85rem;
      color: var(--color-secondary);
      margin-top: var(--space-xs);
    }}

    .charts-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
      gap: var(--space-md);
      margin-bottom: var(--space-xl);
    }}

    .chart-card {{
      background: var(--color-light);
      border-radius: var(--radius-lg);
      padding: var(--space-md);
      box-shadow: var(--shadow-subtle);
    }}

    .chart-card.full-width {{
      grid-column: 1 / -1;
    }}

    .chart-title {{
      font-size: 1.1rem;
      font-weight: 500;
      color: var(--color-dark);
      margin-bottom: var(--space-md);
      display: flex;
      align-items: center;
      gap: var(--space-xs);
    }}

    .chart-container {{
      position: relative;
      height: 300px;
    }}

    .accordion {{
      margin-bottom: var(--space-lg);
    }}

    .accordion-item {{
      background: var(--color-light);
      border-radius: var(--radius-md);
      margin-bottom: var(--space-sm);
      overflow: hidden;
      box-shadow: var(--shadow-subtle);
    }}

    .accordion-header {{
      padding: var(--space-md);
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
      transition: background 0.3s;
    }}

    .accordion-header:hover {{
      background: var(--color-primary);
    }}

    .accordion-header h3 {{
      font-size: 1.1rem;
      font-weight: 500;
      color: var(--color-dark);
      display: flex;
      align-items: center;
      gap: var(--space-sm);
    }}

    .accordion-icon {{
      color: var(--color-accent);
      transition: transform 0.3s;
    }}

    .timeline-list {{
      display: flex;
      flex-direction: column;
      gap: var(--space-md);
    }}

    .timeline-city-card {{
      background: var(--color-light);
      padding: var(--space-md);
      border-radius: var(--radius-md);
      box-shadow: var(--shadow-subtle);
    }}

    .timeline-city-card h3 {{
      margin-bottom: var(--space-sm);
    }}

    .timeline-city-card p {{
      margin-bottom: var(--space-xs);
      color: var(--color-secondary);
    }}

    .accordion-item.active .accordion-icon {{
      transform: rotate(180deg);
    }}

    .accordion-content {{
      max-height: 0;
      overflow: hidden;
      transition: max-height 0.3s ease;
    }}

    .accordion-item.active .accordion-content {{
      max-height: 5000px;
    }}

    .accordion-body {{
      padding: var(--space-md);
      border-top: 1px solid var(--color-neutral);
    }}

    .activity-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: var(--space-md);
      margin-top: var(--space-md);
    }}

    .activity-card {{
      background: var(--color-primary);
      padding: var(--space-md);
      border-radius: var(--radius-md);
      border-left: 4px solid var(--color-accent);
    }}

    .activity-card h4 {{
      font-size: 1rem;
      font-weight: 500;
      color: var(--color-dark);
      margin-bottom: var(--space-xs);
    }}

    .activity-card p {{
      font-size: 0.9rem;
      color: var(--color-secondary);
      margin-bottom: var(--space-xs);
    }}

    .activity-card .cost {{
      font-weight: 600;
      color: var(--color-accent);
    }}

    .activity-card .type-badge {{
      display: inline-block;
      padding: 4px var(--space-xs);
      background: var(--color-accent);
      color: white;
      border-radius: var(--radius-sm);
      font-size: 0.75rem;
      margin-top: var(--space-xs);
    }}

    .booking-links {{
      font-size: 0.85rem;
      margin-top: var(--space-sm);
    }}

    .booking-link {{
      color: var(--color-accent);
      text-decoration: none;
      font-weight: 500;
    }}

    .booking-link:hover {{
      text-decoration: underline;
    }}

    .skill-icons {{
      display: inline-flex;
      gap: 6px;
      margin-left: 8px;
      align-items: center;
    }}

    .skill-icon-btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 24px;
      height: 24px;
      border-radius: 50%;
      background: white;
      border: 1px solid var(--color-neutral);
      color: white;
      text-decoration: none;
      transition: transform 0.2s, box-shadow 0.2s;
      font-size: 0.7rem;
    }}

    .skill-icon-btn:hover {{
      transform: translateY(-2px);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    }}

    .skill-icon-btn.google-maps {{
      background: #4285F4;
    }}

    .skill-icon-btn.gaode-maps {{
      background: #00A862;
    }}

    .skill-icon-btn.rednote {{
      background: #FF2442;
    }}

    .skill-icon-btn.airbnb {{
      background: #FF5A5F;
    }}

    footer {{
      text-align: center;
      padding: var(--space-xl) 0;
      color: var(--color-secondary);
      font-size: 0.85rem;
    }}

    @media (max-width: 768px) {{
      .container {{
        padding: var(--space-sm);
      }}

      header h1 {{
        font-size: 1.8rem;
      }}

      .charts-grid {{
        grid-template-columns: 1fr;
      }}

      .chart-container {{
        height: 250px;
      }}

      .activity-grid {{
        grid-template-columns: 1fr;
      }}

      .tabs {{
        gap: var(--space-xs);
      }}

      .tab {{
        padding: var(--space-xs) var(--space-sm);
        font-size: 0.9rem;
      }}
    }}

    @media (max-width: 320px) {{
      header h1 {{
        font-size: 1.5rem;
      }}

      .stat-value {{
        font-size: 1.5rem;
      }}
    }}

    .detail-overlay {{
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(74, 63, 53, 0.4);
      opacity: 0;
      visibility: hidden;
      transition: opacity 0.3s, visibility 0.3s;
      z-index: 999;
    }}

    .detail-overlay.open {{
      opacity: 1;
      visibility: visible;
    }}

    .detail-panel {{
      position: fixed;
      top: 0;
      right: -500px;
      width: 500px;
      height: 100vh;
      background: var(--color-light);
      box-shadow: -4px 0 20px rgba(74, 63, 53, 0.2);
      transition: right 0.3s ease;
      z-index: 1000;
      overflow-y: auto;
    }}

    .detail-panel.open {{
      right: 0;
    }}

    .detail-panel-header {{
      position: sticky;
      top: 0;
      background: linear-gradient(135deg, var(--color-accent) 0%, var(--color-secondary) 100%);
      color: white;
      padding: var(--space-md);
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: var(--shadow-medium);
    }}

    .detail-panel-title {{
      font-size: 1.2rem;
      font-weight: 500;
    }}

    .detail-panel-close {{
      background: rgba(255, 255, 255, 0.2);
      border: none;
      color: white;
      font-size: 1.5rem;
      cursor: pointer;
      padding: 0.25rem 0.5rem;
      border-radius: var(--radius-sm);
      transition: background 0.2s;
    }}

    .detail-panel-close:hover {{
      background: rgba(255, 255, 255, 0.3);
    }}

    .detail-panel-content {{
      padding: var(--space-md);
    }}

    @media (max-width: 768px) {{
      .detail-panel {{
        width: 100vw;
        right: -100vw;
      }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1 id="trip-title">Loading...</h1>
      <div class="subtitle" id="trip-meta"></div>
    </header>

    <div class="tabs" id="tabs-container"></div>

    <div id="overview-tab" class="tab-content active">
      <div class="stats-grid" id="stats-container"></div>
      <div class="charts-grid" id="charts-container"></div>
    </div>

    <div id="cities-tab" class="tab-content">
      <div class="accordion" id="cities-accordion"></div>
    </div>

    <div id="budget-tab" class="tab-content">
      <div class="charts-grid" id="budget-charts"></div>
    </div>

    <div id="timeline-tab" class="tab-content">
      <div id="timeline-container"></div>
    </div>

    <footer>
      <p>Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")} | Travel Planner Dashboard</p>
    </footer>
  </div>

  <div class="detail-overlay" id="detail-overlay" onclick="closeDetailPanel()"></div>

  <div class="detail-panel" id="detail-panel">
    <div class="detail-panel-header">
      <div class="detail-panel-title" id="detail-panel-title">Details</div>
      <button class="detail-panel-close" onclick="closeDetailPanel()">&times;</button>
    </div>
    <div class="detail-panel-content" id="detail-panel-content">
    </div>
  </div>

  <script>
    const PLAN_DATA = {merged_json};
    const PROJECT_TYPE = "{self.project_type}";

    const WARM_COLORS = [
      '#D4AF37', '#8B7355', '#D4A574', '#B5695F', '#8FAF7A',
      '#C9A86A', '#A67B5B', '#E8C5A5', '#9B7357', '#B8956A'
    ];

    const SKILL_ICON_MAPPING = {{
      'google-maps': {{ icon: 'fa-map-marked-alt', class: 'google-maps' }},
      'gaode-maps': {{ icon: 'fa-map-pin', class: 'gaode-maps' }},
      'rednote': {{ icon: 'fa-book-open', class: 'rednote' }},
      'airbnb': {{ icon: 'fa-home', class: 'airbnb' }}
    }};

    function renderSkillIcons(searchResults) {{
      if (!searchResults || !Array.isArray(searchResults) || searchResults.length === 0) {{
        return '';
      }}

      const uniqueUrls = new Map();
      searchResults.forEach(result => {{
        if (result.url && !uniqueUrls.has(result.url)) {{
          uniqueUrls.set(result.url, result);
        }}
      }});

      if (uniqueUrls.size === 0) return '';

      let html = '<span class="skill-icons">';
      uniqueUrls.forEach(result => {{
        const mapping = SKILL_ICON_MAPPING[result.skill];
        if (mapping) {{
          html += `<a href="${{result.url}}" target="_blank" class="skill-icon-btn ${{mapping.class}}" title="${{result.display_text || result.skill}}">`;
          html += `<i class="fas ${{mapping.icon}}"></i>`;
          html += '</a>';
        }}
      }});
      html += '</span>';

      return html;
    }}

    const CATEGORY_MAPPINGS = {{
      attraction_types: {{
        'historical_site': 'Historical Site',
        'museum': 'Museum',
        'temple': 'Temple',
        'natural_scenery': 'Natural Scenery',
        'park': 'Park',
        'cultural_experience': 'Cultural Experience',
        'ancient_architecture': 'Ancient Architecture',
        'modern_landmark': 'Modern Landmark',
        'unesco_heritage': 'UNESCO Heritage',
        'scenic_spot': 'Scenic Spot',
        'night_view': 'Night View',
        'street_food': 'Street Food Area',
        'shopping_district': 'Shopping District'
      }},
      hotel_categories: {{
        'budget': 'Budget Hotel',
        'mid-range': 'Mid-Range Hotel',
        'high-end': 'High-End Hotel',
        'luxury': 'Luxury Hotel',
        'boutique': 'Boutique Hotel',
        'hostel': 'Hostel',
        'guesthouse': 'Guesthouse'
      }},
      restaurant_categories: {{
        'local': 'Local Cuisine',
        'street_food': 'Street Food',
        'fine_dining': 'Fine Dining',
        'casual': 'Casual Dining',
        'fast_food': 'Fast Food',
        'vegetarian': 'Vegetarian',
        'halal': 'Halal',
        'international': 'International',
        'cafe': 'Café',
        'teahouse': 'Teahouse'
      }},
      entertainment_types: {{
        'show': 'Show',
        'nightlife': 'Nightlife',
        'bar': 'Bar',
        'club': 'Club',
        'karaoke': 'Karaoke',
        'theater': 'Theater',
        'cinema': 'Cinema',
        'live_music': 'Live Music'
      }}
    }};

    function formatCategoryLabel(code, type) {{
      if (!code) return '';

      let mapping;
      if (type === 'attraction') {{
        mapping = CATEGORY_MAPPINGS.attraction_types;
      }} else if (type === 'hotel') {{
        mapping = CATEGORY_MAPPINGS.hotel_categories;
      }} else if (type === 'restaurant') {{
        mapping = CATEGORY_MAPPINGS.restaurant_categories;
      }} else if (type === 'entertainment') {{
        mapping = CATEGORY_MAPPINGS.entertainment_types;
      }} else {{
        return code;
      }}

      return mapping[code] || code;
    }}

    function formatAddress(address) {{
      if (!address || address === null || address === 'null' || address.trim() === '') {{
        return 'Address not available';
      }}
      return address;
    }}

    function showDetailPanel(title, content) {{
      document.getElementById('detail-panel-title').textContent = title;
      document.getElementById('detail-panel-content').innerHTML = content;
      document.getElementById('detail-panel').classList.add('open');
      document.getElementById('detail-overlay').classList.add('open');
    }}

    function closeDetailPanel() {{
      document.getElementById('detail-panel').classList.remove('open');
      document.getElementById('detail-overlay').classList.remove('open');
    }}

    function showCityDetailPanel(cityIndex) {{
      if (PROJECT_TYPE === "bucket-list" && PLAN_DATA.cities) {{
        const city = PLAN_DATA.cities[cityIndex];
        if (city) {{
          const content = renderCityContent(city);
          showDetailPanel(city.city, content);
        }}
      }}
    }}

    function init() {{
      renderHeader();
      renderTabs();
      renderStats();
      renderCharts();
      renderCities();
      renderBudgetCharts();
      renderTimeline();
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

    function renderTabs() {{
      const tabsHtml = `
        <button class="tab active" onclick="switchTab('overview')">
          <i class="fas fa-chart-pie"></i> Overview
        </button>
        <button class="tab" onclick="switchTab('cities')">
          <i class="fas fa-city"></i> Cities
        </button>
        <button class="tab" onclick="switchTab('budget')">
          <i class="fas fa-money-bill-wave"></i> Budget
        </button>
        <button class="tab" onclick="switchTab('timeline')">
          <i class="fas fa-calendar-days"></i> Timeline
        </button>
      `;
      document.getElementById('tabs-container').innerHTML = tabsHtml;
    }}

    function switchTab(tabName) {{
      document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

      event.target.closest('.tab').classList.add('active');
      document.getElementById(`${{tabName}}-tab`).classList.add('active');
    }}

    function renderStats() {{
      let stats = [];
      if (PROJECT_TYPE === "itinerary" && PLAN_DATA.days) {{
        const totalBudget = PLAN_DATA.days.reduce((sum, day) => sum + (day.budget && day.budget.total || 0), 0);
        const totalAttractions = PLAN_DATA.days.reduce((sum, day) => sum + (day.attractions && day.attractions.length || 0), 0);
        const uniqueCities = new Set(PLAN_DATA.days.map(d => d.location)).size;
        stats = [
          {{ icon: 'fa-calendar-days', label: 'Days', value: PLAN_DATA.days.length }},
          {{ icon: 'fa-money-bill-wave', label: 'Total Budget', value: `€${{totalBudget.toFixed(2)}}` }},
          {{ icon: 'fa-landmark', label: 'Attractions', value: totalAttractions }},
          {{ icon: 'fa-city', label: 'Cities', value: uniqueCities }}
        ];
      }} else if (PROJECT_TYPE === "bucket-list" && PLAN_DATA.cities) {{
        const totalAttractions = PLAN_DATA.cities.reduce((sum, city) => sum + (city.attractions && city.attractions.length || 0), 0);
        stats = [
          {{ icon: 'fa-city', label: 'Cities', value: PLAN_DATA.cities.length }},
          {{ icon: 'fa-landmark', label: 'Attractions', value: totalAttractions }},
          {{ icon: 'fa-hotel', label: 'Hotels', value: PLAN_DATA.cities.reduce((sum, c) => sum + (c.hotels && c.hotels.length || 0), 0) }},
          {{ icon: 'fa-utensils', label: 'Restaurants', value: PLAN_DATA.cities.reduce((sum, c) => sum + (c.restaurants && c.restaurants.length || 0), 0) }}
        ];
      }}

      document.getElementById('stats-container').innerHTML = stats.map(s => `
        <div class="stat-card">
          <i class="fas ${{s.icon}} stat-icon"></i>
          <div class="stat-value">${{s.value}}</div>
          <div class="stat-label">${{s.label}}</div>
        </div>
      `).join('');
    }}

    function renderCharts() {{
      if (PROJECT_TYPE === "itinerary" && PLAN_DATA.days) {{
        renderItineraryCharts();
      }} else if (PROJECT_TYPE === "bucket-list" && PLAN_DATA.cities) {{
        renderBucketListCharts();
      }}
    }}

    function renderItineraryCharts() {{
      const budgetByCity = {{}};
      const attractionTypes = {{}};

      PLAN_DATA.days.forEach(day => {{
        const city = day.location;
        budgetByCity[city] = (budgetByCity[city] || 0) + (day.budget && day.budget.total || 0);

        if (day.attractions) {{
          day.attractions.forEach(attr => {{
            const type = attr.type || 'general';
            attractionTypes[type] = (attractionTypes[type] || 0) + 1;
          }});
        }}
      }});

      const chartsHtml = `
        <div class="chart-card">
          <div class="chart-title">
            <i class="fas fa-chart-bar"></i> Budget by City
          </div>
          <div class="chart-container">
            <canvas id="budgetByCityChart"></canvas>
          </div>
        </div>
        <div class="chart-card">
          <div class="chart-title">
            <i class="fas fa-chart-pie"></i> Attraction Types
          </div>
          <div class="chart-container">
            <canvas id="attractionTypesChart"></canvas>
          </div>
        </div>
      `;
      document.getElementById('charts-container').innerHTML = chartsHtml;

      new Chart(document.getElementById('budgetByCityChart'), {{
        type: 'bar',
        data: {{
          labels: Object.keys(budgetByCity),
          datasets: [{{
            label: 'Budget (EUR)',
            data: Object.values(budgetByCity),
            backgroundColor: WARM_COLORS[0],
            borderRadius: 4
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            legend: {{ display: false }}
          }},
          scales: {{
            y: {{ beginAtZero: true }}
          }}
        }}
      }});

      new Chart(document.getElementById('attractionTypesChart'), {{
        type: 'doughnut',
        data: {{
          labels: Object.keys(attractionTypes).map(type => formatCategoryLabel(type, 'attraction')),
          datasets: [{{
            data: Object.values(attractionTypes),
            backgroundColor: WARM_COLORS,
            borderWidth: 0
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            legend: {{
              position: 'right',
              labels: {{
                usePointStyle: true,
                padding: 15
              }}
            }}
          }}
        }}
      }});
    }}

    function renderBucketListCharts() {{
      const attractionsByCity = {{}};
      const attractionTypes = {{}};

      PLAN_DATA.cities.forEach(city => {{
        attractionsByCity[city.city] = city.attractions && city.attractions.length || 0;

        if (city.attractions) {{
          city.attractions.forEach(attr => {{
            const type = attr.type || 'general';
            attractionTypes[type] = (attractionTypes[type] || 0) + 1;
          }});
        }}
      }});

      const chartsHtml = `
        <div class="chart-card">
          <div class="chart-title">
            <i class="fas fa-chart-bar"></i> Attractions by City
          </div>
          <div class="chart-container">
            <canvas id="attractionsByCityChart"></canvas>
          </div>
        </div>
        <div class="chart-card">
          <div class="chart-title">
            <i class="fas fa-chart-pie"></i> Attraction Types
          </div>
          <div class="chart-container">
            <canvas id="attractionTypesChart"></canvas>
          </div>
        </div>
      `;
      document.getElementById('charts-container').innerHTML = chartsHtml;

      new Chart(document.getElementById('attractionsByCityChart'), {{
        type: 'bar',
        data: {{
          labels: Object.keys(attractionsByCity),
          datasets: [{{
            label: 'Attractions',
            data: Object.values(attractionsByCity),
            backgroundColor: WARM_COLORS[0],
            borderRadius: 4
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          indexAxis: 'y',
          onClick: (event, elements) => {{
            if (elements.length > 0) {{
              const index = elements[0].index;
              const cityName = Object.keys(attractionsByCity)[index];
              const city = PLAN_DATA.cities.find(c => c.city === cityName);
              if (city) {{
                const content = renderCityContent(city);
                showDetailPanel(cityName, content);
              }}
            }}
          }},
          plugins: {{
            legend: {{ display: false }}
          }},
          scales: {{
            x: {{ beginAtZero: true }}
          }}
        }}
      }});

      new Chart(document.getElementById('attractionTypesChart'), {{
        type: 'doughnut',
        data: {{
          labels: Object.keys(attractionTypes).map(type => formatCategoryLabel(type, 'attraction')),
          datasets: [{{
            data: Object.values(attractionTypes),
            backgroundColor: WARM_COLORS,
            borderWidth: 0
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          onClick: (event, elements) => {{
            if (elements.length > 0) {{
              const index = elements[0].index;
              const typeCode = Object.keys(attractionTypes)[index];
              const typeLabel = formatCategoryLabel(typeCode, 'attraction');
              let content = '<div class="activity-grid">';
              PLAN_DATA.cities.forEach(city => {{
                if (city.attractions) {{
                  city.attractions.forEach(attr => {{
                    if (attr.type === typeCode) {{
                      const formattedAddress = attr.location || attr.address || attr.how_to_get_there;
                      const skillIcons = renderSkillIcons(attr.search_results);
                      content += '<div class="activity-card"><h4>' + attr.name + skillIcons + '</h4>';
                      content += '<p style="color: var(--color-secondary);"><i class="fas fa-city"></i> ' + city.city + '</p>';
                      if (formattedAddress) content += '<p><i class="fas fa-map-marker-alt"></i> ' + formattedAddress + '</p>';
                      if (attr.description) content += '<p>' + attr.description + '</p>';
                      if (attr.ticket_price_eur) content += '<p class="cost"><i class="fas fa-ticket-alt"></i> €' + attr.ticket_price_eur + '</p>';
                      content += '</div>';
                    }}
                  }});
                }}
              }});
              content += '</div>';
              showDetailPanel(typeLabel + ' Attractions', content);
            }}
          }},
          plugins: {{
            legend: {{
              position: 'right',
              labels: {{
                usePointStyle: true,
                padding: 15
              }}
            }}
          }}
        }}
      }});
    }}

    function renderCities() {{
      let citiesHtml = '';

      if (PROJECT_TYPE === "itinerary" && PLAN_DATA.days) {{
        citiesHtml = PLAN_DATA.days.map((day, idx) => `
          <div class="accordion-item" id="city-${{idx}}">
            <div class="accordion-header" onclick="toggleAccordion(${{idx}})">
              <h3>
                <i class="fas fa-map-marker-alt"></i>
                Day ${{day.day}}: ${{day.location}} - ${{day.date}}
              </h3>
              <i class="fas fa-chevron-down accordion-icon"></i>
            </div>
            <div class="accordion-content">
              <div class="accordion-body">
                ${{renderDayContent(day)}}
              </div>
            </div>
          </div>
        `).join('');
      }} else if (PROJECT_TYPE === "bucket-list" && PLAN_DATA.cities) {{
        citiesHtml = PLAN_DATA.cities.map((city, idx) => `
          <div class="accordion-item" id="city-${{idx}}">
            <div class="accordion-header" onclick="toggleAccordion(${{idx}}); event.stopPropagation();">
              <h3 onclick="event.stopPropagation(); showCityDetailPanel(${{idx}});" style="cursor: pointer;">
                <i class="fas fa-city"></i>
                ${{city.city}}${{city.province ? ', ' + city.province : ''}}
              </h3>
              <i class="fas fa-chevron-down accordion-icon"></i>
            </div>
            <div class="accordion-content">
              <div class="accordion-body">
                ${{renderCityContent(city)}}
              </div>
            </div>
          </div>
        `).join('');
      }}

      document.getElementById('cities-accordion').innerHTML = citiesHtml;
    }}

    function toggleAccordion(idx) {{
      const item = document.getElementById(`city-${{idx}}`);
      item.classList.toggle('active');
    }}

    function renderDayContent(day) {{
      let html = '';

      if (day.attractions && day.attractions.length > 0) {{
        html += '<h4 style="color: var(--color-accent); margin-bottom: 1rem;"><i class="fas fa-landmark"></i> Attractions</h4>';
        html += '<div class="activity-grid">';
        day.attractions.forEach(attr => {{
          const formattedAddress = formatAddress(attr.location || attr.address);
          const formattedType = formatCategoryLabel(attr.type, 'attraction');
          const skillIcons = renderSkillIcons(attr.search_results);
          html += `<div class="activity-card">
            <h4>${{attr.name}}${{skillIcons}}</h4>
            <p><i class="fas fa-map-marker-alt"></i> ${{formattedAddress}}</p>
            <p class="cost"><i class="fas fa-euro-sign"></i> €${{attr.cost_eur || attr.cost || 0}}</p>
            ${{formattedType ? `<span class="type-badge">${{formattedType}}</span>` : ''}}
          </div>`;
        }});
        html += '</div>';
      }}

      if (day.hotels && day.hotels.length > 0 || day.accommodation && day.accommodation.name) {{
        html += '<h4 style="color: var(--color-accent); margin: 1.5rem 0 1rem;"><i class="fas fa-hotel"></i> Accommodation</h4>';
        html += '<div class="activity-grid">';
        if (day.accommodation && day.accommodation.name) {{
          const formattedAddress = formatAddress(day.accommodation.location || day.accommodation.address);
          const formattedCategory = formatCategoryLabel(day.accommodation.category, 'hotel');
          const skillIcons = renderSkillIcons(day.accommodation.search_results);
          html += `<div class="activity-card">
            <h4>${{day.accommodation.name}}${{skillIcons}}</h4>
            <p><i class="fas fa-map-marker-alt"></i> ${{formattedAddress}}</p>
            ${{formattedCategory ? `<p><i class="fas fa-star"></i> ${{formattedCategory}}</p>` : ''}}
            <p class="cost"><i class="fas fa-euro-sign"></i> €${{day.accommodation.cost_eur || 0}}</p>
          </div>`;
        }}
        html += '</div>';
      }}

      if (day.restaurants && day.restaurants.length > 0 || day.breakfast && day.breakfast.name || day.lunch && day.lunch.name || day.dinner && day.dinner.name) {{
        html += '<h4 style="color: var(--color-accent); margin: 1.5rem 0 1rem;"><i class="fas fa-utensils"></i> Dining</h4>';
        html += '<div class="activity-grid">';
        ['breakfast', 'lunch', 'dinner'].forEach(meal => {{
          if (day[meal] && day[meal].name) {{
            const formattedAddress = formatAddress(day[meal].location || day[meal].address);
            const formattedCategory = formatCategoryLabel(day[meal].category || day[meal].type, 'restaurant');
            const skillIcons = renderSkillIcons(day[meal].search_results);
            html += `<div class="activity-card">
              <h4>${{meal.charAt(0).toUpperCase() + meal.slice(1)}}: ${{day[meal].name}}${{skillIcons}}</h4>
              <p><i class="fas fa-map-marker-alt"></i> ${{formattedAddress}}</p>
              ${{formattedCategory ? `<p><i class="fas fa-tag"></i> ${{formattedCategory}}</p>` : ''}}
              <p class="cost"><i class="fas fa-euro-sign"></i> €${{day[meal].cost_eur || day[meal].cost || 0}}</p>
            </div>`;
          }}
        }});
        html += '</div>';
      }}

      if (day.entertainment && day.entertainment.length > 0) {{
        html += '<h4 style="color: var(--color-accent); margin: 1.5rem 0 1rem;"><i class="fas fa-masks-theater"></i> Entertainment</h4>';
        html += '<div class="activity-grid">';
        day.entertainment.forEach(ent => {{
          const formattedAddress = formatAddress(ent.location || ent.address);
          const formattedType = formatCategoryLabel(ent.type, 'entertainment');
          const skillIcons = renderSkillIcons(ent.search_results);
          html += `<div class="activity-card">
            <h4>${{ent.name}}${{skillIcons}}</h4>
            <p><i class="fas fa-map-marker-alt"></i> ${{formattedAddress}}</p>
            ${{ent.description ? `<p>${{ent.description}}</p>` : ''}}
            ${{formattedType ? `<span class="type-badge">${{formattedType}}</span>` : ''}}
          </div>`;
        }});
        html += '</div>';
      }}

      if (day.shopping && day.shopping.length > 0) {{
        html += '<h4 style="color: var(--color-accent); margin: 1.5rem 0 1rem;"><i class="fas fa-shopping-bag"></i> Shopping</h4>';
        html += '<div class="activity-grid">';
        day.shopping.forEach(shop => {{
          const formattedAddress = formatAddress(shop.location || shop.address);
          const skillIcons = renderSkillIcons(shop.search_results);
          html += `<div class="activity-card">
            <h4>${{shop.name}}${{skillIcons}}</h4>
            <p><i class="fas fa-map-marker-alt"></i> ${{formattedAddress}}</p>
            ${{shop.description ? `<p>${{shop.description}}</p>` : ''}}
            ${{shop.type ? `<span class="type-badge">${{shop.type}}</span>` : ''}}
          </div>`;
        }});
        html += '</div>';
      }}

      return html || '<p style="color: var(--color-secondary);">No details available</p>';
    }}

    function renderCityContent(city) {{
      let html = '';

      if (city.attractions && city.attractions.length > 0) {{
        html += '<h4 style="color: var(--color-accent); margin-bottom: 1rem;"><i class="fas fa-landmark"></i> Attractions</h4>';
        html += '<div class="activity-grid">';
        city.attractions.forEach(attr => {{
          const formattedAddress = attr.location || attr.address || attr.how_to_get_there;
          const formattedType = formatCategoryLabel(attr.type, 'attraction');
          const skillIcons = renderSkillIcons(attr.search_results);
          html += `<div class="activity-card">
            <h4>${{attr.name}}${{skillIcons}}</h4>
            ${{formattedAddress ? `<p><i class="fas fa-map-marker-alt"></i> ${{formattedAddress}}</p>` : ''}}
            ${{attr.description ? `<p>${{attr.description}}</p>` : ''}}
            ${{attr.ticket_price_eur ? `<p class="cost"><i class="fas fa-ticket-alt"></i> €${{attr.ticket_price_eur}}</p>` : ''}}
            ${{formattedType ? `<span class="type-badge">${{formattedType}}</span>` : ''}}
          </div>`;
        }});
        html += '</div>';
      }}

      if (city.hotels && city.hotels.length > 0) {{
        html += '<h4 style="color: var(--color-accent); margin: 1.5rem 0 1rem;"><i class="fas fa-hotel"></i> Hotels</h4>';
        html += '<div class="activity-grid">';
        city.hotels.forEach(hotel => {{
          const formattedAddress = hotel.location || hotel.address;
          const formattedCategory = formatCategoryLabel(hotel.category, 'hotel');
          const skillIcons = renderSkillIcons(hotel.search_results);
          html += '<div class="activity-card">';
          html += '<h4>' + hotel.name + skillIcons + '</h4>';
          if (formattedAddress) html += '<p><i class="fas fa-map-marker-alt"></i> ' + formattedAddress + '</p>';
          if (formattedCategory) html += '<p><i class="fas fa-star"></i> ' + formattedCategory + '</p>';
          if (hotel.price_per_night_eur) html += '<p class="cost"><i class="fas fa-euro-sign"></i> €' + hotel.price_per_night_eur + '/night</p>';
          if (hotel.booking_platforms && hotel.booking_platforms.length > 0) {{
            html += '<p class="booking-links"><i class="fas fa-external-link-alt"></i> ';
            hotel.booking_platforms.forEach((platform, idx) => {{
              if (idx > 0) html += ' • ';
              html += '<a href="https://www.google.com/search?q=' + encodeURIComponent(hotel.name + ' ' + platform) + '" target="_blank" class="booking-link">' + platform + '</a>';
            }});
            html += '</p>';
          }}
          html += '</div>';
        }});
        html += '</div>';
      }}

      if (city.restaurants && city.restaurants.length > 0) {{
        html += '<h4 style="color: var(--color-accent); margin: 1.5rem 0 1rem;"><i class="fas fa-utensils"></i> Restaurants</h4>';
        html += '<div class="activity-grid">';
        city.restaurants.forEach(rest => {{
          const formattedAddress = rest.location || rest.address;
          const formattedCategory = formatCategoryLabel(rest.category || rest.type, 'restaurant');
          const skillIcons = renderSkillIcons(rest.search_results);
          html += `<div class="activity-card">
            <h4>${{rest.name}}${{skillIcons}}</h4>
            ${{rest.cuisine ? `<p><i class="fas fa-bowl-food"></i> ${{rest.cuisine}}</p>` : ''}}
            ${{formattedCategory ? `<p><i class="fas fa-tag"></i> ${{formattedCategory}}</p>` : ''}}
            <p><i class="fas fa-map-marker-alt"></i> ${{formattedAddress}}</p>
          </div>`;
        }});
        html += '</div>';
      }}

      if (city.entertainment && city.entertainment.length > 0) {{
        html += '<h4 style="color: var(--color-accent); margin: 1.5rem 0 1rem;"><i class="fas fa-masks-theater"></i> Entertainment</h4>';
        html += '<div class="activity-grid">';
        city.entertainment.forEach(ent => {{
          const formattedAddress = formatAddress(ent.address || ent.location);
          const formattedType = formatCategoryLabel(ent.type, 'entertainment');
          const skillIcons = renderSkillIcons(ent.search_results);
          html += `<div class="activity-card">
            <h4>${{ent.name}}${{skillIcons}}</h4>
            <p><i class="fas fa-map-marker-alt"></i> ${{formattedAddress}}</p>
            ${{ent.description ? `<p>${{ent.description}}</p>` : ''}}
            ${{formattedType ? `<span class="type-badge">${{formattedType}}</span>` : ''}}
          </div>`;
        }});
        html += '</div>';
      }}

      if (city.shopping && city.shopping.length > 0) {{
        html += '<h4 style="color: var(--color-accent); margin: 1.5rem 0 1rem;"><i class="fas fa-shopping-bag"></i> Shopping</h4>';
        html += '<div class="activity-grid">';
        city.shopping.forEach(shop => {{
          const formattedAddress = formatAddress(shop.address || shop.location);
          const skillIcons = renderSkillIcons(shop.search_results);
          html += `<div class="activity-card">
            <h4>${{shop.name}}${{skillIcons}}</h4>
            <p><i class="fas fa-map-marker-alt"></i> ${{formattedAddress}}</p>
            ${{shop.description ? `<p>${{shop.description}}</p>` : ''}}
            ${{shop.type ? `<span class="type-badge">${{shop.type}}</span>` : ''}}
          </div>`;
        }});
        html += '</div>';
      }}

      return html || '<p style="color: var(--color-secondary);">No details available</p>';
    }}

    function renderBudgetCharts() {{
      if (PROJECT_TYPE === "itinerary" && PLAN_DATA.days) {{
        const categories = {{ meals: 0, accommodation: 0, activities: 0, shopping: 0, transportation: 0 }};
        const dailyBudget = [];

        PLAN_DATA.days.forEach(day => {{
          if (day.budget) {{
            Object.keys(categories).forEach(cat => {{
              categories[cat] += day.budget[cat] || 0;
            }});
            dailyBudget.push({{
              day: `Day ${{day.day}}`,
              total: day.budget.total || 0
            }});
          }}
        }});

        const budgetHtml = `
          <div class="chart-card">
            <div class="chart-title">
              <i class="fas fa-chart-pie"></i> Budget by Category
            </div>
            <div class="chart-container">
              <canvas id="budgetCategoryChart"></canvas>
            </div>
          </div>
          <div class="chart-card">
            <div class="chart-title">
              <i class="fas fa-chart-line"></i> Daily Budget Trend
            </div>
            <div class="chart-container">
              <canvas id="dailyBudgetChart"></canvas>
            </div>
          </div>
        `;
        document.getElementById('budget-charts').innerHTML = budgetHtml;

        new Chart(document.getElementById('budgetCategoryChart'), {{
          type: 'doughnut',
          data: {{
            labels: Object.keys(categories).map(k => k.charAt(0).toUpperCase() + k.slice(1)),
            datasets: [{{
              data: Object.values(categories),
              backgroundColor: WARM_COLORS,
              borderWidth: 0
            }}]
          }},
          options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
              legend: {{
                position: 'right',
                labels: {{
                  usePointStyle: true,
                  padding: 15
                }}
              }},
              tooltip: {{
                callbacks: {{
                  label: function(context) {{
                    return context.label + ': €' + context.raw.toFixed(2);
                  }}
                }}
              }}
            }}
          }}
        }});

        new Chart(document.getElementById('dailyBudgetChart'), {{
          type: 'line',
          data: {{
            labels: dailyBudget.map(d => d.day),
            datasets: [{{
              label: 'Budget (EUR)',
              data: dailyBudget.map(d => d.total),
              borderColor: WARM_COLORS[0],
              backgroundColor: 'rgba(212, 175, 55, 0.1)',
              fill: true,
              tension: 0.3,
              pointRadius: 4
            }}]
          }},
          options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
              legend: {{ display: false }}
            }},
            scales: {{
              y: {{ beginAtZero: true }}
            }}
          }}
        }});
      }} else if (PROJECT_TYPE === "bucket-list" && PLAN_DATA.cities) {{
        // Bucket list budget: aggregate estimated budget by city
        const budgetHtml = `
          <div class="chart-card">
            <div class="chart-title">
              <i class="fas fa-chart-bar"></i> Estimated Budget by City
            </div>
            <div class="chart-container">
              <canvas id="cityBudgetChart"></canvas>
            </div>
          </div>
          <div class="budget-summary">
            <h3 style="color: var(--color-accent); margin-bottom: 1rem;">Budget Overview</h3>
            <div class="activity-grid">
              ${{PLAN_DATA.cities.map(city => `
                <div class="activity-card">
                  <h4>${{city.city}}</h4>
                  <p><i class="fas fa-calendar"></i> ${{city.recommended_duration}}</p>
                  <p class="cost"><i class="fas fa-euro-sign"></i> €${{city.estimated_budget_eur}} estimated</p>
                </div>
              `).join('')}}
            </div>
          </div>
        `;

        document.getElementById('budget-charts').innerHTML = budgetHtml;

        // Create city budget chart
        new Chart(document.getElementById('cityBudgetChart'), {{
          type: 'bar',
          data: {{
            labels: PLAN_DATA.cities.map(c => c.city),
            datasets: [{{
              label: 'Budget (EUR)',
              data: PLAN_DATA.cities.map(c => c.estimated_budget_eur || 0),
              backgroundColor: WARM_COLORS[0],
              borderWidth: 0
            }}]
          }},
          options: {{
            responsive: true,
            maintainAspectRatio: false,
            onClick: (event, elements) => {{
              if (elements.length > 0) {{
                const index = elements[0].index;
                const city = PLAN_DATA.cities[index];
                if (city) {{
                  const content = renderCityContent(city);
                  showDetailPanel(city.city + ' - Budget Details', content);
                }}
              }}
            }},
            plugins: {{
              legend: {{ display: false }},
              tooltip: {{
                callbacks: {{
                  label: function(context) {{
                    return 'Budget: €' + context.raw;
                  }}
                }}
              }}
            }},
            scales: {{
              y: {{ beginAtZero: true }}
            }}
          }}
        }});
      }}
    }}

    function renderTimeline() {{
      let timelineHtml = '';

      if (PROJECT_TYPE === "itinerary" && PLAN_DATA.days) {{
        timelineHtml = '<div class="accordion">' + PLAN_DATA.days.map((day, idx) => {{
          let dayEvents = [];

          if (day.breakfast && day.breakfast.name) dayEvents.push({{ time: '08:00', icon: 'fa-coffee', label: `Breakfast: ${{day.breakfast.name}}` }});
          if (day.lunch && day.lunch.name) dayEvents.push({{ time: '12:00', icon: 'fa-utensils', label: `Lunch: ${{day.lunch.name}}` }});
          if (day.dinner && day.dinner.name) dayEvents.push({{ time: '19:00', icon: 'fa-utensils', label: `Dinner: ${{day.dinner.name}}` }});
          if (day.attractions && day.attractions.length > 0) {{
            day.attractions.forEach(attr => {{
              dayEvents.push({{ time: '10:00', icon: 'fa-landmark', label: attr.name }});
            }});
          }}

          const eventsHtml = dayEvents.length > 0 ? dayEvents.map(e => `
            <div style="padding: 0.5rem 0; border-left: 3px solid var(--color-accent); padding-left: 1rem; margin-left: 1rem; margin-bottom: 0.5rem;">
              <div style="color: var(--color-accent); font-weight: 600;">
                <i class="fas ${{e.icon}}"></i> ${{e.time}}
              </div>
              <div style="color: var(--color-dark);">${{e.label}}</div>
            </div>
          `).join('') : '<p style="color: var(--color-secondary); padding-left: 2rem;">No scheduled events</p>';

          return `
            <div class="accordion-item" id="timeline-${{idx}}">
              <div class="accordion-header" onclick="toggleTimelineAccordion(${{idx}})">
                <h3>
                  <i class="fas fa-calendar-day"></i>
                  Day ${{day.day}}: ${{day.location}} - ${{day.date}}
                </h3>
                <i class="fas fa-chevron-down accordion-icon"></i>
              </div>
              <div class="accordion-content">
                <div class="accordion-body">
                  ${{eventsHtml}}
                </div>
              </div>
            </div>
          `;
        }}).join('') + '</div>';
      }} else if (PROJECT_TYPE === "bucket-list" && PLAN_DATA.cities) {{
        timelineHtml = '<div class="timeline-list">' + PLAN_DATA.cities.map((city, idx) => `
          <div class="timeline-city-card">
            <h3 style="color: var(--color-accent);"><i class="fas fa-city"></i> ${{city.city}}</h3>
            <p><i class="fas fa-calendar"></i> <strong>Recommended Duration:</strong> ${{city.recommended_duration}}</p>
            <p><i class="fas fa-sun"></i> <strong>Best Months:</strong> ${{city.best_months.join(', ')}}</p>
            ${{city.estimated_budget_eur ? `<p><i class="fas fa-euro-sign"></i> <strong>Budget:</strong> €${{city.estimated_budget_eur}}</p>` : ''}}
          </div>
        `).join('') + '</div>';
      }} else {{
        timelineHtml = '<p style="text-align: center; color: var(--color-secondary); padding: 2rem;">Timeline not available</p>';
      }}

      document.getElementById('timeline-container').innerHTML = timelineHtml;
    }}

    function toggleTimelineAccordion(idx) {{
      const item = document.getElementById(`timeline-${{idx}}`);
      item.classList.toggle('active');
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
