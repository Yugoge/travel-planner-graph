#!/usr/bin/env python3
"""
Reusable HTML generator module for travel plans.

Supports both itinerary and bucket list project types.
"""

import json
import sys
import subprocess
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
        self.script_dir = Path(__file__).parent.parent
        self.config_dir = self.script_dir.parent / "config"

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

    def _load_currency_config(self) -> Dict:
        """
        Load currency configuration from config/currency-config.json.

        Returns:
            Currency config dict with defaults if file not found
        """
        config_file = self.config_dir / "currency-config.json"

        if not config_file.exists():
            print("Warning: Currency config not found, using defaults (EUR display, CNY source)", file=sys.stderr)
            return {
                "default_display_currency": "EUR",
                "default_source_currency": "CNY",
                "currency_symbol_map": {"EUR": "€", "USD": "$", "GBP": "£", "CNY": "¥"}
            }

        try:
            return json.loads(config_file.read_text())
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid currency config JSON: {e}, using defaults", file=sys.stderr)
            return {
                "default_display_currency": "EUR",
                "default_source_currency": "CNY",
                "currency_symbol_map": {"EUR": "€"}
            }

    def _fetch_exchange_rate(self, source_currency: str, display_currency: str) -> float:
        """
        Fetch real-time exchange rate using fetch-exchange-rate.sh script.

        Args:
            source_currency: Source currency code (e.g., CNY)
            display_currency: Target currency code (e.g., EUR)

        Returns:
            Exchange rate as float

        Raises:
            ValueError: If currency codes are invalid
            RuntimeError: If exchange rate fetch fails
        """
        # Security: Validate currency codes before subprocess call
        # Root cause fix: commit 3d5971b added subprocess without input validation
        import re
        ALLOWED_CURRENCIES = ['CNY', 'USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'HKD']
        CURRENCY_PATTERN = re.compile(r'^[A-Z]{3}$')

        if not CURRENCY_PATTERN.match(source_currency):
            raise ValueError(f"Invalid source currency code: {source_currency} (must be 3 uppercase letters)")
        if not CURRENCY_PATTERN.match(display_currency):
            raise ValueError(f"Invalid display currency code: {display_currency} (must be 3 uppercase letters)")
        if source_currency not in ALLOWED_CURRENCIES:
            raise ValueError(f"Source currency {source_currency} not in whitelist: {ALLOWED_CURRENCIES}")
        if display_currency not in ALLOWED_CURRENCIES:
            raise ValueError(f"Display currency {display_currency} not in whitelist: {ALLOWED_CURRENCIES}")

        fetch_script = self.script_dir / "utils" / "fetch-exchange-rate.sh"

        if not fetch_script.exists():
            print(f"Warning: Exchange rate script not found at {fetch_script}, using fallback rate 7.8", file=sys.stderr)
            return 7.8

        try:
            print(f"Fetching exchange rate: {source_currency} → {display_currency}...", file=sys.stderr)
            result = subprocess.run(
                [str(fetch_script), source_currency, display_currency],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            exchange_rate = float(result.stdout.strip())
            print(f"Exchange rate: 1 {source_currency} = {exchange_rate} {display_currency}", file=sys.stderr)
            return exchange_rate
        except subprocess.CalledProcessError as e:
            print(f"Error fetching exchange rate: {e.stderr}", file=sys.stderr)
            raise RuntimeError(f"Failed to fetch exchange rate: {e.stderr}")
        except subprocess.TimeoutExpired:
            print("Error: Exchange rate fetch timed out", file=sys.stderr)
            raise RuntimeError("Exchange rate fetch timed out after 10 seconds")
        except ValueError as e:
            print(f"Error: Invalid exchange rate format: {e}", file=sys.stderr)
            raise RuntimeError(f"Invalid exchange rate returned: {e}")

    def _inject_currency_config(self, merged_data: Dict) -> None:
        """
        Inject currency configuration into merged data.

        Modifies merged_data in-place to add currency_config section.

        Args:
            merged_data: Merged plan data dictionary
        """
        try:
            config = self._load_currency_config()
            source_currency = config.get("default_source_currency", "CNY")
            display_currency = config.get("default_display_currency", "EUR")
            currency_symbol = config.get("currency_symbol_map", {}).get(display_currency, display_currency)

            exchange_rate = self._fetch_exchange_rate(source_currency, display_currency)

            merged_data["currency_config"] = {
                "source_currency": source_currency,
                "display_currency": display_currency,
                "exchange_rate": exchange_rate,
                "currency_symbol": currency_symbol
            }
        except RuntimeError as e:
            print(f"Warning: Currency integration failed: {e}, using defaults", file=sys.stderr)
            merged_data["currency_config"] = {
                "source_currency": "CNY",
                "display_currency": "EUR",
                "exchange_rate": 7.8,
                "currency_symbol": "€"
            }

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

        # Inject currency configuration (Phase 1: Currency integration from commit 95a42d3)
        self._inject_currency_config(self.merged_data)

        # Generate HTML content
        html_content = self._generate_html_template()

        # Write to file
        output_path.write_text(html_content)
        print(f"✓ Generated HTML: {output_path}")

    def _generate_additional_styles(self) -> str:
        """
        Generate additional CSS for features migrated from bash script (commit 95a42d3).

        Includes expandable stats, Kanban route map, budget by city, attraction types,
        cities panel, map links with brand colors.

        Returns:
            CSS string with beige/coffee colors (replacing purple from bash)
        """
        return '''
    /* Stats Dashboard - Expandable Cards (Feature 1 from bash) */
    .stats-expandable {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 15px;
      margin-bottom: 20px;
    }
    .stat-card-expandable {
      background: var(--color-light);
      border-radius: var(--radius-md);
      box-shadow: var(--shadow-subtle);
      overflow: hidden;
      cursor: pointer;
      transition: transform 0.2s, box-shadow 0.2s;
    }
    .stat-card-expandable:hover {
      transform: translateY(-2px);
      box-shadow: var(--shadow-medium);
    }
    .stat-header-expandable {
      padding: 20px;
      background: var(--color-light);
    }
    .stat-card-expandable .value { font-size: 2em; font-weight: bold; color: var(--color-secondary); }
    .stat-card-expandable .label { color: #666; font-size: 0.9em; margin-top: 5px; }
    .stat-expand-icon {
      float: right;
      color: #999;
      transition: transform 0.2s;
    }
    .stat-card-expandable.expanded .stat-expand-icon { transform: rotate(180deg); }
    .stat-details {
      display: none;
      padding: 0 20px 20px 20px;
      background: var(--color-primary);
      border-top: 1px solid var(--color-neutral);
      max-height: 400px;
      overflow-y: auto;
    }
    .stat-details.active { display: block; }
    .stat-detail-item {
      padding: 8px 0;
      border-bottom: 1px solid var(--color-neutral);
      display: flex;
      justify-content: space-between;
      font-size: 0.9em;
    }
    .stat-detail-item:last-child { border-bottom: none; }

    /* Route Map - Kanban Style (Feature 2 from bash) */
    .route-map {
      background: var(--color-light);
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow-subtle);
      padding: var(--space-md);
      margin-bottom: var(--space-lg);
      overflow-x: auto;
    }
    .route-map h2 {
      color: var(--color-secondary);
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
      background: var(--color-primary);
      border-radius: var(--radius-md);
      border: 2px solid var(--color-secondary);
      cursor: pointer;
      transition: transform 0.2s, box-shadow 0.2s;
    }
    .route-city:hover {
      transform: translateY(-3px);
      box-shadow: 0 4px 8px rgba(139, 115, 85, 0.3);
    }
    .route-city-header {
      background: var(--color-secondary);
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
      background: var(--color-light);
      padding: 8px;
      margin: 5px 0;
      border-radius: 4px;
      font-size: 0.85em;
      border-left: 3px solid var(--color-secondary);
    }
    .route-day-date { font-weight: bold; color: var(--color-secondary); }
    .route-day-budget { color: var(--color-danger); font-size: 0.9em; margin-top: 3px; }

    /* Budget by City Section (Feature 3 from bash) */
    .budget-city-section {
      background: var(--color-light);
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow-subtle);
      padding: var(--space-md);
      margin-bottom: var(--space-lg);
    }
    .budget-city-section h2 {
      color: var(--color-secondary);
      margin-bottom: 15px;
      font-size: 1.5em;
    }
    .budget-city-card {
      background: var(--color-primary);
      border-radius: 6px;
      margin-bottom: 10px;
      overflow: hidden;
      border: 1px solid var(--color-neutral);
    }
    .budget-city-header {
      padding: 15px;
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--color-light);
      transition: background 0.2s;
    }
    .budget-city-header:hover { background: var(--color-primary); }
    .budget-city-name { font-weight: bold; color: var(--color-dark); }
    .budget-city-total { color: var(--color-danger); font-weight: bold; }
    .budget-city-expand { color: #999; transition: transform 0.2s; }
    .budget-city-card.expanded .budget-city-expand { transform: rotate(180deg); }
    .budget-city-details {
      display: none;
      padding: 15px;
      background: var(--color-primary);
    }
    .budget-city-details.active { display: block; }
    .budget-breakdown-item {
      display: flex;
      justify-content: space-between;
      padding: 6px 0;
      border-bottom: 1px solid var(--color-neutral);
      font-size: 0.9em;
    }
    .budget-breakdown-item:last-child { border-bottom: none; }

    /* Attraction Types Section (Feature 4 from bash) */
    .attraction-types-section {
      background: var(--color-light);
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow-subtle);
      padding: var(--space-md);
      margin-bottom: var(--space-lg);
    }
    .attraction-types-section h2 {
      color: var(--color-secondary);
      margin-bottom: 15px;
      font-size: 1.5em;
    }
    .attraction-type-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 12px;
    }
    .attraction-type-card {
      background: var(--color-primary);
      padding: 15px;
      border-radius: 6px;
      border-left: 4px solid var(--color-secondary);
      cursor: pointer;
      transition: transform 0.2s;
    }
    .attraction-type-card:hover { transform: translateX(3px); }
    .attraction-type-name { font-weight: bold; color: var(--color-secondary); }
    .attraction-type-count { color: #666; font-size: 0.9em; margin-top: 5px; }

    /* Cities Panel - Geographic Clustering (Feature 6 from bash) */
    .cities-panel-section {
      background: var(--color-light);
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow-subtle);
      padding: var(--space-md);
      margin-bottom: var(--space-lg);
    }
    .cities-panel-section h2 {
      color: var(--color-secondary);
      margin-bottom: 15px;
      font-size: 1.5em;
    }
    .city-cluster {
      margin-bottom: 20px;
    }
    .city-cluster-header {
      font-weight: bold;
      color: var(--color-secondary);
      margin-bottom: 10px;
      padding-bottom: 5px;
      border-bottom: 2px solid var(--color-secondary);
    }
    .city-attractions {
      display: grid;
      gap: 10px;
    }
    .attraction-item {
      background: var(--color-primary);
      padding: 12px;
      border-radius: 6px;
      border-left: 3px solid var(--color-secondary);
    }
    .attraction-name {
      font-weight: bold;
      color: var(--color-dark);
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
      background: var(--color-secondary);
      color: white;
      text-decoration: none;
      border-radius: 4px;
      font-size: 0.85em;
      transition: background 0.2s;
    }
    .attraction-link:hover { background: var(--color-dark); }
    /* Map Links - Brand Colors with Logo Icons (Root cause fix: colors only, no logos) */
    .attraction-link.gaode { background: #52C41A; } /* Gaode/Ant Design official green */
    .attraction-link.google { background: #4285f4; }
    .attraction-link.rednote { background: #ff2442; }
    /* Add spacing for icons in links */
    .attraction-link i { margin-right: 6px; }

    /* Day Cards with beige theme */
    .day-card-bash-style {
      background: var(--color-light);
      border-radius: var(--radius-md);
      box-shadow: var(--shadow-subtle);
      margin-bottom: var(--space-md);
      overflow: hidden;
    }
    .day-header-bash-style {
      background: var(--color-secondary);
      color: white;
      padding: 15px 20px;
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .day-header-bash-style:hover { background: var(--color-dark); }
    .day-content-bash-style {
      padding: 20px;
      display: none;
    }
    .day-content-bash-style.active { display: block; }

    /* Timeline with beige theme */
    .timeline-item-bash-style {
      border-left: 3px solid var(--color-secondary);
      padding-left: 20px;
      margin-bottom: 20px;
      position: relative;
    }
    .timeline-item-bash-style::before {
      content: '';
      position: absolute;
      left: -7px;
      top: 0;
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background: var(--color-secondary);
    }
    .timeline-time-bash-style { font-weight: bold; color: var(--color-secondary); }
    .timeline-activity-bash-style { margin: 5px 0; }

    /* Activity Grid with beige theme */
    .activity-grid-bash-style {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 15px;
      margin-top: 20px;
    }
    .activity-card-bash-style {
      background: var(--color-primary);
      padding: 15px;
      border-radius: 6px;
      border-left: 4px solid var(--color-secondary);
    }
    .activity-card-bash-style h4 { color: var(--color-secondary); margin-bottom: 8px; }
    .activity-card-bash-style .cost { color: var(--color-danger); font-weight: bold; }

    /* Side Panel */
    .side-panel-bash-style {
      position: fixed;
      top: 0;
      right: -450px;
      width: 450px;
      height: 100vh;
      background: var(--color-light);
      box-shadow: -2px 0 10px rgba(74, 63, 53, 0.1);
      transition: right 0.3s;
      overflow-y: auto;
      z-index: 1000;
      padding: 20px;
    }
    .side-panel-bash-style.active { right: 0; }
    .close-panel {
      cursor: pointer;
      font-size: 1.5em;
      float: right;
      color: #999;
    }

    /* Responsive for bash features */
    @media (max-width: 768px) {
      .side-panel-bash-style { width: 100%; right: -100%; }
      .stats-expandable { grid-template-columns: 1fr; }
      .route-kanban { flex-direction: column; }
      .route-city { min-width: 100%; }
    }

    /* Utilities with beige theme */
    .btn-bash-style {
      background: var(--color-secondary);
      color: white;
      border: none;
      padding: 10px 20px;
      border-radius: 6px;
      cursor: pointer;
      transition: background 0.3s;
    }
    .btn-bash-style:hover { background: var(--color-dark); }
    .section-bash-style { margin-bottom: 30px; }
    .section-bash-style h3 { color: var(--color-secondary); margin-bottom: 15px; }
'''

    def _generate_bash_features_html(self) -> str:
        """
        Generate HTML for 7 features migrated from bash script (commit 95a42d3).

        Features:
        1. Expandable stats dashboard
        2. Kanban route map
        3. Budget by city
        4. Attraction types
        5. Map links (integrated in city content)
        6. Cities panel (geographic clustering)
        7. Currency conversion (handled via JS, data injected in merged_data)

        Returns:
            HTML string with all bash feature sections
        """
        if self.project_type != "itinerary" or not self.merged_data.get("days"):
            # Bash features only apply to itinerary projects
            return ""

        # Root cause fix: ISSUE-5 - Duplicate content across tabs
        # Removed Feature 2 (Route Map) and Feature 6 (Cities Panel) as they're now in tabs
        return f'''
    <!-- Bash Features Migration (commit 95a42d3) - Deduplicated -->

    <!-- Feature 1: Expandable Stats Dashboard -->
    <div class="stats-expandable" id="stats-expandable-container"></div>

    <!-- Feature 3: Budget by City -->
    <div class="budget-city-section">
      <h2>Budget by City</h2>
      <div id="budget-by-city-container"></div>
    </div>

    <!-- Feature 4: Attraction Types -->
    <div class="attraction-types-section">
      <h2>Attraction Types</h2>
      <div class="attraction-type-grid" id="attraction-types-grid-container"></div>
    </div>
'''

    def _generate_bash_javascript(self) -> str:
        """
        Generate JavaScript functions for bash features (commit 95a42d3).

        Includes:
        - Currency conversion (Feature 7)
        - Map links generation (Feature 5)
        - Toggle functions for expandable sections
        - Rendering functions for all features

        Returns:
            JavaScript code as string
        """
        return '''
    // ============================================================
    // Bash Features JavaScript (migrated from commit 95a42d3)
    // ============================================================

    // Feature 7: Currency Configuration (dynamically fetched)
    const CURRENCY_CONFIG_BASH = PLAN_DATA.currency_config || {
      source_currency: 'CNY',
      display_currency: 'EUR',
      exchange_rate: 7.8,
      currency_symbol: '€'
    };

    function convertCurrencyBash(amount) {
      if (!amount || isNaN(amount)) return '0.00';
      return (amount / CURRENCY_CONFIG_BASH.exchange_rate).toFixed(2);
    }

    function toEURBash(cny) {
      return convertCurrencyBash(cny);
    }

    // Feature 5: Map Links Generation
    function generateMapLinksBash(name, location) {
      const encodedName = encodeURIComponent(name);
      const encodedLocation = encodeURIComponent(location);

      const isMainland = !location.includes('Hong Kong') && !location.includes('Macau') &&
                         !location.includes('HK') && !location.includes('MO');

      const mapLink = isMainland
        ? `https://ditu.amap.com/search?query=${encodedName}`
        : `https://www.google.com/maps/search/?api=1&query=${encodedName}+${encodedLocation}`;

      const rednoteLink = `https://www.xiaohongshu.com/search_result?keyword=${encodedName}`;

      return { mapLink, rednote: rednoteLink, isMainland };
    }

    // XSS Protection: HTML escaping function (root cause fix: commit 34e112a)
    function escapeHtml(str) {
      if (typeof str !== 'string') return str;
      return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }

    // Toggle functions for expandable sections
    function toggleStatBash(idx) {
      const details = document.getElementById(`stat-details-bash-${idx}`);
      const card = details.closest('.stat-card-expandable');
      if (details && card) {
        details.classList.toggle('active');
        card.classList.toggle('expanded');
      }
    }

    function toggleBudgetCityBash(idx) {
      const details = document.getElementById(`budget-city-bash-${idx}`);
      const card = details.closest('.budget-city-card');
      if (details && card) {
        details.classList.toggle('active');
        card.classList.toggle('expanded');
      }
    }

    function scrollToCityBash(city) {
      const element = document.getElementById(`city-geo-${city.replace(/\\s+/g, '-')}`);
      if (element) element.scrollIntoView({ behavior: 'smooth' });
    }

    // Feature 1: Render Expandable Stats Dashboard
    function renderStatsDashboardBash() {
      if (PROJECT_TYPE !== "itinerary" || !PLAN_DATA.days) return;

      const totalBudgetCNY = PLAN_DATA.days.reduce((sum, day) => sum + (day.budget?.total || 0), 0);
      const totalAttractions = PLAN_DATA.days.reduce((sum, day) => sum + (day.attractions?.length || 0), 0);
      const cities = [...new Set(PLAN_DATA.days.map(d => d.location))];

      const activitiesByCity = {};
      PLAN_DATA.days.forEach(day => {
        if (!activitiesByCity[day.location]) activitiesByCity[day.location] = 0;
        activitiesByCity[day.location] += (day.attractions?.length || 0) +
                                          (day.entertainment?.length || 0) +
                                          (day.shopping?.length || 0);
      });

      const daysByCity = {};
      PLAN_DATA.days.forEach(day => {
        daysByCity[day.location] = (daysByCity[day.location] || 0) + 1;
      });

      const stats = [
        {
          label: 'Total Budget',
          value: `${CURRENCY_CONFIG_BASH.currency_symbol}${toEURBash(totalBudgetCNY)}`,
          details: PLAN_DATA.days.map(d => ({
            label: `Day ${d.day} - ${d.location}`,
            value: `${CURRENCY_CONFIG_BASH.currency_symbol}${toEURBash(d.budget?.total || 0)}`
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

      const container = document.getElementById('stats-expandable-container');
      if (container) {
        container.innerHTML = stats.map((s, idx) => `
          <div class="stat-card-expandable" onclick="toggleStatBash(${idx})">
            <div class="stat-header-expandable">
              <span class="stat-expand-icon">▼</span>
              <div class="value">${escapeHtml(s.value)}</div>
              <div class="label">${escapeHtml(s.label)}</div>
            </div>
            <div class="stat-details" id="stat-details-bash-${idx}">
              ${s.details.map(d => `
                <div class="stat-detail-item">
                  <span>${escapeHtml(d.label)}</span>
                  <span>${escapeHtml(d.value)}</span>
                </div>
              `).join('')}
            </div>
          </div>
        `).join('');
      }
    }

    // Feature 2: Render Kanban Route Map
    function renderRouteKanbanBash() {
      if (PROJECT_TYPE !== "itinerary" || !PLAN_DATA.days) return;

      const cityGroups = {};
      PLAN_DATA.days.forEach(day => {
        if (!cityGroups[day.location]) cityGroups[day.location] = [];
        cityGroups[day.location].push(day);
      });

      const container = document.getElementById('route-kanban-container');
      if (container) {
        container.innerHTML = Object.entries(cityGroups).map(([city, days]) => {
          const totalBudget = days.reduce((sum, d) => sum + (d.budget?.total || 0), 0);
          return `
            <div class="route-city" onclick="scrollToCityBash('${escapeHtml(city)}')">
              <div class="route-city-header">${escapeHtml(city)}</div>
              <div class="route-city-days">
                ${days.map(d => `
                  <div class="route-day-item">
                    <div class="route-day-date">Day ${escapeHtml(d.day)} - ${escapeHtml(d.date)}</div>
                    <div class="route-day-budget">${escapeHtml(CURRENCY_CONFIG_BASH.currency_symbol)}${toEURBash(d.budget?.total || 0)}</div>
                  </div>
                `).join('')}
                <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid var(--color-neutral); font-weight: bold; color: var(--color-danger);">
                  Total: ${escapeHtml(CURRENCY_CONFIG_BASH.currency_symbol)}${toEURBash(totalBudget)}
                </div>
              </div>
            </div>
          `;
        }).join('');
      }
    }

    // Feature 3: Render Budget by City
    function renderBudgetByCityBash() {
      if (PROJECT_TYPE !== "itinerary" || !PLAN_DATA.days) return;

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

        Object.entries(budget).forEach(([key, value]) => {
          if (key !== 'total' && typeof value === 'number') {
            cityBudgets[day.location].breakdown[key] =
              (cityBudgets[day.location].breakdown[key] || 0) + value;
          }
        });
      });

      const container = document.getElementById('budget-by-city-container');
      if (container) {
        container.innerHTML = Object.entries(cityBudgets).map(([city, data], idx) => `
          <div class="budget-city-card">
            <div class="budget-city-header" onclick="toggleBudgetCityBash(${idx})">
              <div class="budget-city-name">${escapeHtml(city)}</div>
              <div>
                <span class="budget-city-total">${escapeHtml(CURRENCY_CONFIG_BASH.currency_symbol)}${toEURBash(data.total)}</span>
                <span class="budget-city-expand">▼</span>
              </div>
            </div>
            <div class="budget-city-details" id="budget-city-bash-${idx}">
              ${Object.entries(data.breakdown).map(([category, amount]) => `
                <div class="budget-breakdown-item">
                  <span>${escapeHtml(category.replace(/_/g, ' '))}</span>
                  <span>${escapeHtml(CURRENCY_CONFIG_BASH.currency_symbol)}${toEURBash(amount)}</span>
                </div>
              `).join('')}
            </div>
          </div>
        `).join('');
      }
    }

    // Feature 4: Render Attraction Types
    function renderAttractionTypesBash() {
      if (PROJECT_TYPE !== "itinerary" || !PLAN_DATA.days) return;

      const types = {};
      PLAN_DATA.days.forEach(day => {
        (day.attractions || []).forEach(attr => {
          const type = attr.type || 'Other';
          types[type] = (types[type] || 0) + 1;
        });
      });

      const container = document.getElementById('attraction-types-grid-container');
      if (container) {
        container.innerHTML = Object.entries(types)
          .sort((a, b) => b[1] - a[1])
          .map(([type, count]) => `
            <div class="attraction-type-card">
              <div class="attraction-type-name">${escapeHtml(formatCategoryLabel(type, 'attraction'))}</div>
              <div class="attraction-type-count">${count} attraction${count > 1 ? 's' : ''}</div>
            </div>
          `).join('');
      }
    }

    // Feature 6: Render Cities Panel (Geographic Clustering)
    function renderCitiesGeographicBash() {
      if (PROJECT_TYPE !== "itinerary" || !PLAN_DATA.days) return;

      const cityClusters = {};
      PLAN_DATA.days.forEach(day => {
        (day.attractions || []).forEach(attr => {
          const city = day.location;
          if (!cityClusters[city]) cityClusters[city] = [];
          cityClusters[city].push({ ...attr, location: day.location });
        });
      });

      const container = document.getElementById('cities-geographic-container');
      if (container) {
        container.innerHTML = Object.entries(cityClusters).map(([city, attractions]) => {
          const uniqueAttractions = attractions.filter((attr, idx, self) =>
            idx === self.findIndex(a => a.name === attr.name)
          );

          return `
            <div class="city-cluster" id="city-geo-${city.replace(/\\s+/g, '-')}">
              <div class="city-cluster-header">${city} (${uniqueAttractions.length} attractions)</div>
              <div class="city-attractions">
                ${uniqueAttractions.map(attr => {
                  const links = generateMapLinksBash(attr.name, attr.location);
                  return `
                    <div class="attraction-item">
                      <div class="attraction-name">${attr.name}</div>
                      <div class="attraction-links">
                        <a href="${links.mapLink}" target="_blank" class="attraction-link ${links.isMainland ? 'gaode' : 'google'}">
                          <i class="fas ${links.isMainland ? 'fa-map-marked-alt' : 'fa-map-marker-alt'}"></i>
                          ${links.isMainland ? 'Gaode Maps' : 'Google Maps'}
                        </a>
                        <a href="${links.rednote}" target="_blank" class="attraction-link rednote">
                          <i class="fas fa-book-open"></i>
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
    }

    // Initialize all bash features (deduplicated - removed route/cities functions)
    function initBashFeatures() {
      if (PROJECT_TYPE === "itinerary" && PLAN_DATA.days) {
        renderStatsDashboardBash();
        // renderRouteKanbanBash(); - Now in Timeline tab
        renderBudgetByCityBash();
        renderAttractionTypesBash();
        // renderCitiesGeographicBash(); - Now in Cities tab
      }
    }
'''

    def _generate_html_template(self) -> str:
        """
        Generate complete HTML template with premium Swiss Spa aesthetic.

        Returns:
            HTML string with Chart.js visualization and interactive features
        """
        # Convert merged data to JSON string for embedding
        merged_json = json.dumps(self.merged_data)

        # Get additional styles for bash features
        additional_styles = self._generate_additional_styles()

        # Get bash features HTML sections
        bash_features_html = self._generate_bash_features_html()

        # Get bash features JavaScript
        bash_features_js = self._generate_bash_javascript()

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

    /* Additional styles migrated from bash script (commit 95a42d3) with beige colors */
    {additional_styles}

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

    .detail-panel-controls {{
      display: flex;
      align-items: center;
      gap: 1rem;
    }}

    .sort-toggle {{
      display: flex;
      background: rgba(255, 255, 255, 0.2);
      border-radius: 6px;
      padding: 0.25rem;
      gap: 0.25rem;
    }}

    .sort-btn {{
      background: none;
      border: none;
      color: white;
      font-size: 0.75rem;
      cursor: pointer;
      padding: 0.4rem 0.8rem;
      border-radius: 4px;
      transition: background 0.2s;
      white-space: nowrap;
    }}

    .sort-btn.active {{
      background: rgba(255, 255, 255, 0.3);
      font-weight: 600;
    }}

    .sort-btn:hover {{
      background: rgba(255, 255, 255, 0.25);
    }}

    .detail-panel-summary {{
      padding: 1rem 1.5rem;
      background: var(--color-primary);
      border-bottom: 1px solid var(--color-neutral);
    }}

    .summary-row {{
      display: flex;
      justify-content: space-between;
      padding: 0.5rem 0;
    }}

    .summary-label {{
      color: var(--color-secondary);
      font-size: 0.9rem;
    }}

    .summary-value {{
      font-weight: 600;
      color: var(--color-dark);
      font-size: 0.9rem;
    }}

    .detail-panel-content {{
      padding: var(--space-md);
    }}

    .detail-item {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      padding: 0.75rem 0;
      border-bottom: 1px solid var(--color-neutral);
      font-size: 0.9rem;
    }}

    .detail-item:last-child {{
      border-bottom: none;
    }}

    .detail-item-info {{
      flex: 1;
      min-width: 0;
    }}

    .detail-item-name {{
      color: var(--color-dark);
      font-weight: 500;
      margin-bottom: 0.25rem;
    }}

    .detail-item-meta {{
      color: var(--color-secondary);
      font-size: 0.8rem;
    }}

    .detail-item-value {{
      font-weight: 600;
      color: var(--color-accent);
      margin-left: 1rem;
      white-space: nowrap;
    }}

    .chart-hint {{
      font-size: 0.75rem;
      color: #999;
      text-align: center;
      margin-top: 0.5rem;
      font-style: italic;
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

    {bash_features_html}

    <footer>
      <p>Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")} | Travel Planner Dashboard</p>
    </footer>
  </div>

  <div class="detail-overlay" id="detail-overlay" onclick="closeDetailPanel()"></div>

  <div class="detail-panel" id="detail-panel">
    <div class="detail-panel-header">
      <div class="detail-panel-title" id="detail-panel-title">Details</div>
      <div class="detail-panel-controls">
        <div class="sort-toggle" id="sort-toggle-container">
          <button class="sort-btn active" id="sortByDefault" onclick="setDrawerSort('default')">Default</button>
          <button class="sort-btn" id="sortByValue" onclick="setDrawerSort('value')">By Value</button>
          <button class="sort-btn" id="sortByName" onclick="setDrawerSort('name')">By Name</button>
        </div>
        <button class="detail-panel-close" onclick="closeDetailPanel()">&times;</button>
      </div>
    </div>
    <div class="detail-panel-summary" id="detail-panel-summary">
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
        // Root cause fix: commit 41f1017 incomplete localization mapping
        // Comprehensive Chinese translations for all attraction types
        'historical_site': '历史遗址',
        'museum': '博物馆',
        'temple': '寺庙',
        'natural_scenery': '自然景观',
        'park': '公园',
        'cultural_experience': '文化体验',
        'ancient_architecture': '古建筑',
        'modern_landmark': '现代地标',
        'unesco_heritage': '世界遗产',
        'scenic_spot': '风景名胜',
        'night_view': '夜景',
        'street_food': '美食街区',
        'shopping_district': '购物区',
        'mountain': '山岳',
        'observation deck': '观景台',
        'tourist attraction': '旅游景点',
        'observation_deck': '观景台',
        'tourist_attraction': '旅游景点',
        'palace': '宫殿',
        'garden': '园林',
        'lake': '湖泊',
        'river': '河流',
        'beach': '海滩',
        'forest': '森林',
        'cave': '洞穴',
        'waterfall': '瀑布',
        'bridge': '桥梁',
        'tower': '塔楼',
        'monument': '纪念碑',
        'square': '广场',
        'street': '街道',
        'market': '市场',
        'zoo': '动物园',
        'aquarium': '水族馆',
        'botanical_garden': '植物园',
        'theme_park': '主题公园',
        'general': '综合景点',
        'other': '其他'
      }},
      hotel_categories: {{
        'budget': '经济型酒店',
        'mid-range': '中档酒店',
        'high-end': '高端酒店',
        'luxury': '豪华酒店',
        'boutique': '精品酒店',
        'hostel': '青年旅舍',
        'guesthouse': '民宿'
      }},
      restaurant_categories: {{
        'local': '本地美食',
        'street_food': '街边小吃',
        'fine_dining': '高档餐厅',
        'casual': '休闲餐厅',
        'fast_food': '快餐',
        'vegetarian': '素食',
        'halal': '清真',
        'international': '国际美食',
        'cafe': '咖啡厅',
        'teahouse': '茶馆'
      }},
      entertainment_types: {{
        'show': '演出',
        'nightlife': '夜生活',
        'bar': '酒吧',
        'club': '夜店',
        'karaoke': 'KTV',
        'theater': '剧院',
        'cinema': '电影院',
        'live_music': '现场音乐'
      }}
    }};

    function formatCategoryLabel(code, type) {{
      if (!code) return '';

      // Normalize the code for mapping lookup
      const normalizedCode = code.toString().trim().toLowerCase().replace(/\\s+/g, '_');

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

      // Try normalized code first, then original code with space normalization
      return mapping[normalizedCode] || mapping[code.toString().trim().toLowerCase()] || mapping[code] || code;
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

    // Enhanced drawer functionality with sort/filter
    let currentDrawerData = [];
    let currentDrawerSort = 'default';

    function setDrawerSort(sortMode) {{
      currentDrawerSort = sortMode;
      document.querySelectorAll('.sort-btn').forEach(btn => btn.classList.remove('active'));
      document.getElementById(`sortBy${{sortMode.charAt(0).toUpperCase() + sortMode.slice(1)}}`).classList.add('active');
      renderDrawerItems(currentDrawerData);
    }}

    function openDataDrawer(title, summaryData, items, config) {{
      currentDrawerData = {{ items, config: config || {{}} }};
      currentDrawerSort = 'default';

      // Set title
      document.getElementById('detail-panel-title').textContent = title;

      // Render summary
      let summaryHtml = '';
      if (summaryData) {{
        summaryHtml = Object.keys(summaryData).map(key => `
          <div class="summary-row">
            <span class="summary-label">${{key}}</span>
            <span class="summary-value">${{summaryData[key]}}</span>
          </div>
        `).join('');
      }}
      document.getElementById('detail-panel-summary').innerHTML = summaryHtml;

      // Reset sort buttons
      document.querySelectorAll('.sort-btn').forEach(btn => btn.classList.remove('active'));
      document.getElementById('sortByDefault').classList.add('active');

      // Render items
      renderDrawerItems(currentDrawerData);

      // Open drawer
      document.getElementById('detail-panel').classList.add('open');
      document.getElementById('detail-overlay').classList.add('open');
    }}

    function renderDrawerItems(drawerData) {{
      if (!drawerData || !drawerData.items || drawerData.items.length === 0) {{
        document.getElementById('detail-panel-content').innerHTML = '<p style="text-align: center; color: #999; padding: 2rem;">No data available</p>';
        return;
      }}

      let items = [...drawerData.items];
      const config = drawerData.config || {{}};

      // Apply sorting
      if (currentDrawerSort === 'value' && config.valueKey) {{
        items.sort((a, b) => (b[config.valueKey] || 0) - (a[config.valueKey] || 0));
      }} else if (currentDrawerSort === 'name' && config.nameKey) {{
        items.sort((a, b) => (a[config.nameKey] || '').localeCompare(b[config.nameKey] || ''));
      }}

      // Render items
      const itemsHtml = items.map(item => {{
        const name = config.nameKey ? item[config.nameKey] : item.name || item.label || 'Unnamed';
        const value = config.valueKey ? item[config.valueKey] : item.value || '';
        const meta = config.metaKey ? item[config.metaKey] : item.meta || '';
        const formattedValue = config.formatValue ? config.formatValue(value) : value;

        return `
          <div class="detail-item">
            <div class="detail-item-info">
              <div class="detail-item-name">${{escapeHtml(name)}}</div>
              ${{meta ? `<div class="detail-item-meta">${{escapeHtml(meta)}}</div>` : ''}}
            </div>
            <div class="detail-item-value">${{escapeHtml(formattedValue.toString())}}</div>
          </div>
        `;
      }}).join('');

      document.getElementById('detail-panel-content').innerHTML = itemsHtml;
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

      // Root cause fix: Timeline and Cities tabs not rendering when switched
      // Previous dev (session 123500) claimed to add these functions but didn't
      // Call render functions when tabs are switched to populate content
      if (tabName === 'timeline') {{
        renderTimelineTab();
      }} else if (tabName === 'cities') {{
        renderCitiesTab();
      }}
    }}

    // Root cause fix: ISSUE-7 - Timeline/Cities tabs missing render functions
    // Previous dev session 123500 claimed to add these but didn't actually implement them
    // These wrapper functions call the existing renderTimeline() and renderCities() functions
    function renderTimelineTab() {{
      renderTimeline();
    }}

    function renderCitiesTab() {{
      renderCities();
    }}

    function renderStats() {{
      let stats = [];
      if (PROJECT_TYPE === "itinerary" && PLAN_DATA.days) {{
        const totalBudgetCNY = PLAN_DATA.days.reduce((sum, day) => sum + (day.budget && day.budget.total || 0), 0);
        const totalAttractions = PLAN_DATA.days.reduce((sum, day) => sum + (day.attractions && day.attractions.length || 0), 0);
        const uniqueCities = new Set(PLAN_DATA.days.map(d => d.location)).size;

        // Root cause fix: Stats cards were static display only, now making them interactive
        stats = [
          {{
            icon: 'fa-calendar-days',
            label: 'Days',
            value: PLAN_DATA.days.length,
            onClick: () => {{
              const items = PLAN_DATA.days.map(d => ({{
                name: `Day ${{d.day}} - ${{d.date}}`,
                value: d.location,
                meta: d.location
              }}));
              openDataDrawer('Day-by-Day Breakdown', {{ 'Total Days': PLAN_DATA.days.length }}, items,
                {{ nameKey: 'name', valueKey: 'value', metaKey: 'meta', formatValue: (v) => v }});
            }}
          }},
          {{
            icon: 'fa-money-bill-wave',
            label: 'Total Budget',
            value: `${{CURRENCY_CONFIG_BASH.currency_symbol}}${{toEURBash(totalBudgetCNY)}}`,
            onClick: () => {{
              const items = PLAN_DATA.days.map(d => ({{
                name: `Day ${{d.day}} - ${{d.location}}`,
                value: d.budget?.total || 0,
                meta: d.date
              }}));
              openDataDrawer('Daily Budget Breakdown',
                {{ 'Total Budget': `${{CURRENCY_CONFIG_BASH.currency_symbol}}${{toEURBash(totalBudgetCNY)}}`,
                   'Average per Day': `${{CURRENCY_CONFIG_BASH.currency_symbol}}${{toEURBash(totalBudgetCNY / PLAN_DATA.days.length)}}` }},
                items,
                {{ nameKey: 'name', valueKey: 'value', metaKey: 'meta', formatValue: (v) => `${{CURRENCY_CONFIG_BASH.currency_symbol}}${{toEURBash(v)}}` }});
            }}
          }},
          {{
            icon: 'fa-landmark',
            label: 'Attractions',
            value: totalAttractions,
            onClick: () => {{
              const items = [];
              PLAN_DATA.days.forEach(day => {{
                (day.attractions || []).forEach(attr => {{
                  items.push({{
                    name: attr.name,
                    value: attr.ticket_price_cny || 0,
                    meta: `${{day.location}} - Day ${{day.day}}`
                  }});
                }});
              }});
              openDataDrawer('All Attractions', {{ 'Total Attractions': totalAttractions }}, items,
                {{ nameKey: 'name', valueKey: 'value', metaKey: 'meta', formatValue: (v) => v > 0 ? `${{CURRENCY_CONFIG_BASH.currency_symbol}}${{toEURBash(v)}}` : 'Free' }});
            }}
          }},
          {{
            icon: 'fa-city',
            label: 'Cities',
            value: uniqueCities,
            onClick: () => {{
              const cityStats = {{}};
              PLAN_DATA.days.forEach(day => {{
                if (!cityStats[day.location]) {{
                  cityStats[day.location] = {{ days: 0, attractions: 0, budget: 0 }};
                }}
                cityStats[day.location].days += 1;
                cityStats[day.location].attractions += (day.attractions || []).length;
                cityStats[day.location].budget += day.budget?.total || 0;
              }});
              const items = Object.entries(cityStats).map(([city, data]) => ({{
                name: city,
                value: data.budget,
                meta: `${{data.days}} days, ${{data.attractions}} attractions`
              }}));
              openDataDrawer('City Breakdown', {{ 'Total Cities': uniqueCities }}, items,
                {{ nameKey: 'name', valueKey: 'value', metaKey: 'meta', formatValue: (v) => `${{CURRENCY_CONFIG_BASH.currency_symbol}}${{toEURBash(v)}}` }});
            }}
          }}
        ];
      }} else if (PROJECT_TYPE === "bucket-list" && PLAN_DATA.cities) {{
        const totalAttractions = PLAN_DATA.cities.reduce((sum, city) => sum + (city.attractions && city.attractions.length || 0), 0);
        stats = [
          {{
            icon: 'fa-city',
            label: 'Cities',
            value: PLAN_DATA.cities.length,
            onClick: () => {{
              const items = PLAN_DATA.cities.map(c => ({{
                name: c.city,
                value: (c.attractions || []).length,
                meta: c.province || ''
              }}));
              openDataDrawer('Cities Breakdown', {{ 'Total Cities': PLAN_DATA.cities.length }}, items,
                {{ nameKey: 'name', valueKey: 'value', metaKey: 'meta', formatValue: (v) => `${{v}} attractions` }});
            }}
          }},
          {{
            icon: 'fa-landmark',
            label: 'Attractions',
            value: totalAttractions,
            onClick: () => {{
              const items = [];
              PLAN_DATA.cities.forEach(city => {{
                (city.attractions || []).forEach(attr => {{
                  items.push({{ name: attr.name, value: attr.type || 'General', meta: city.city }});
                }});
              }});
              openDataDrawer('All Attractions', {{ 'Total Attractions': totalAttractions }}, items,
                {{ nameKey: 'name', valueKey: 'value', metaKey: 'meta' }});
            }}
          }},
          {{
            icon: 'fa-hotel',
            label: 'Hotels',
            value: PLAN_DATA.cities.reduce((sum, c) => sum + (c.hotels && c.hotels.length || 0), 0),
            onClick: () => {{
              const items = [];
              PLAN_DATA.cities.forEach(city => {{
                (city.hotels || []).forEach(hotel => {{
                  items.push({{ name: hotel.name, value: hotel.category || '', meta: city.city }});
                }});
              }});
              openDataDrawer('All Hotels', {{ 'Total Hotels': items.length }}, items,
                {{ nameKey: 'name', valueKey: 'value', metaKey: 'meta' }});
            }}
          }},
          {{
            icon: 'fa-utensils',
            label: 'Restaurants',
            value: PLAN_DATA.cities.reduce((sum, c) => sum + (c.restaurants && c.restaurants.length || 0), 0),
            onClick: () => {{
              const items = [];
              PLAN_DATA.cities.forEach(city => {{
                (city.restaurants || []).forEach(rest => {{
                  items.push({{ name: rest.name, value: rest.category || rest.type || '', meta: city.city }});
                }});
              }});
              openDataDrawer('All Restaurants', {{ 'Total Restaurants': items.length }}, items,
                {{ nameKey: 'name', valueKey: 'value', metaKey: 'meta' }});
            }}
          }}
        ];
      }}

      document.getElementById('stats-container').innerHTML = stats.map((s, idx) => `
        <div class="stat-card" onclick="statClickHandlers[${{idx}}]()" style="cursor: pointer;">
          <i class="fas ${{s.icon}} stat-icon"></i>
          <div class="stat-value">${{s.value}}</div>
          <div class="stat-label">${{s.label}}</div>
        </div>
      `).join('');

      // Store click handlers in global array for access from onclick attribute
      window.statClickHandlers = stats.map(s => s.onClick);
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
            // Root cause fix: commit 41f1017 aggregation incomplete
            // Strengthen normalization: handle null/undefined/whitespace/empty strings
            let type = attr.type;
            if (!type || type === null || type === undefined || type === 'null' || type === 'undefined') {{
              type = 'general';
            }} else {{
              type = type.toString().trim().toLowerCase();
              if (type === '') type = 'general';
            }}
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
          <div class="chart-hint">Click on any bar to see daily budget breakdown</div>
        </div>
        <div class="chart-card">
          <div class="chart-title">
            <i class="fas fa-chart-pie"></i> Attraction Types
          </div>
          <div class="chart-container">
            <canvas id="attractionTypesChart"></canvas>
          </div>
          <div class="chart-hint">Click on any slice to see all attractions of that type</div>
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
          onClick: (event, elements) => {{
            if (elements.length > 0) {{
              const index = elements[0].index;
              const cityName = Object.keys(budgetByCity)[index];
              const days = PLAN_DATA.days.filter(d => d.location === cityName);
              const items = days.map(d => ({{
                name: `Day ${{d.day}} - ${{d.date}}`,
                value: d.budget?.total || 0,
                meta: d.location
              }}));
              openDataDrawer(
                `Budget Breakdown: ${{cityName}}`,
                {{
                  'Total Days': days.length,
                  'Total Budget': `${{CURRENCY_CONFIG_BASH.currency_symbol}}${{toEURBash(budgetByCity[cityName])}}`,
                  'Average per Day': `${{CURRENCY_CONFIG_BASH.currency_symbol}}${{toEURBash(budgetByCity[cityName] / days.length)}}`
                }},
                items,
                {{ nameKey: 'name', valueKey: 'value', metaKey: 'meta', formatValue: (v) => `${{CURRENCY_CONFIG_BASH.currency_symbol}}${{toEURBash(v)}}` }}
              );
            }}
          }},
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
          onClick: (event, elements) => {{
            if (elements.length > 0) {{
              const index = elements[0].index;
              const typeKey = Object.keys(attractionTypes)[index];
              const typeLabel = formatCategoryLabel(typeKey, 'attraction');
              const items = [];
              PLAN_DATA.days.forEach(day => {{
                if (day.attractions) {{
                  day.attractions.forEach(attr => {{
                    const normalizedType = (attr.type || 'general').toString().trim().toLowerCase();
                    if (normalizedType === typeKey) {{
                      items.push({{
                        name: attr.name,
                        value: attr.ticket_price_cny || 0,
                        meta: `${{day.location}} - Day ${{day.day}}`
                      }});
                    }}
                  }});
                }}
              }});
              openDataDrawer(
                `${{typeLabel}} Attractions`,
                {{
                  'Total Attractions': items.length,
                  'Category': typeLabel
                }},
                items,
                {{ nameKey: 'name', valueKey: 'value', metaKey: 'meta', formatValue: (v) => v > 0 ? `${{CURRENCY_CONFIG_BASH.currency_symbol}}${{toEURBash(v)}}` : 'Free' }}
              );
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

    function renderBucketListCharts() {{
      const attractionsByCity = {{}};
      const attractionTypes = {{}};

      PLAN_DATA.cities.forEach(city => {{
        attractionsByCity[city.city] = city.attractions && city.attractions.length || 0;

        if (city.attractions) {{
          city.attractions.forEach(attr => {{
            // Root cause fix: commit 41f1017 aggregation incomplete
            // Strengthen normalization: handle null/undefined/whitespace/empty strings
            let type = attr.type;
            if (!type || type === null || type === undefined || type === 'null' || type === 'undefined') {{
              type = 'general';
            }} else {{
              type = type.toString().trim().toLowerCase();
              if (type === '') type = 'general';
            }}
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
          <div class="chart-hint">Click on any bar to see city attractions details</div>
        </div>
        <div class="chart-card">
          <div class="chart-title">
            <i class="fas fa-chart-pie"></i> Attraction Types
          </div>
          <div class="chart-container">
            <canvas id="attractionTypesChart"></canvas>
          </div>
          <div class="chart-hint">Click on any slice to see all attractions of that type</div>
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
            // Root cause fix: commit 41f1017 - should use openDataDrawer for consistent UX
            if (elements.length > 0) {{
              const index = elements[0].index;
              const cityName = Object.keys(attractionsByCity)[index];
              const city = PLAN_DATA.cities.find(c => c.city === cityName);
              if (city && city.attractions) {{
                const items = city.attractions.map(attr => ({{
                  name: attr.name,
                  value: attr.ticket_price_eur || 0,
                  meta: formatCategoryLabel(attr.type, 'attraction')
                }}));
                openDataDrawer(
                  `${{cityName}} - Attractions`,
                  {{
                    'Total Attractions': items.length,
                    'City': cityName
                  }},
                  items,
                  {{ nameKey: 'name', valueKey: 'value', metaKey: 'meta', formatValue: (v) => v > 0 ? `€${{v}}` : 'Free' }}
                );
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
            // Root cause fix: commit 41f1017 - should use openDataDrawer for consistent UX
            if (elements.length > 0) {{
              const index = elements[0].index;
              const typeCode = Object.keys(attractionTypes)[index];
              const typeLabel = formatCategoryLabel(typeCode, 'attraction');
              const items = [];

              // Normalize typeCode for comparison
              let normalizedTypeCode = typeCode;
              if (!typeCode || typeCode === null || typeCode === undefined || typeCode === 'null' || typeCode === 'undefined') {{
                normalizedTypeCode = 'general';
              }} else {{
                normalizedTypeCode = typeCode.toString().trim().toLowerCase();
                if (normalizedTypeCode === '') normalizedTypeCode = 'general';
              }}

              PLAN_DATA.cities.forEach(city => {{
                if (city.attractions) {{
                  city.attractions.forEach(attr => {{
                    // Normalize attr.type for comparison
                    let attrType = attr.type;
                    if (!attrType || attrType === null || attrType === undefined || attrType === 'null' || attrType === 'undefined') {{
                      attrType = 'general';
                    }} else {{
                      attrType = attrType.toString().trim().toLowerCase();
                      if (attrType === '') attrType = 'general';
                    }}

                    if (attrType === normalizedTypeCode) {{
                      items.push({{
                        name: attr.name,
                        value: attr.ticket_price_eur || 0,
                        meta: city.city
                      }});
                    }}
                  }});
                }}
              }});

              openDataDrawer(
                `${{typeLabel}} Attractions`,
                {{
                  'Total Attractions': items.length,
                  'Category': typeLabel
                }},
                items,
                {{ nameKey: 'name', valueKey: 'value', metaKey: 'meta', formatValue: (v) => v > 0 ? `€${{v}}` : 'Free' }}
              );
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

      // Root cause fix: Timeline and Cities tabs showed identical content
      // Cities tab should show geographic city clusters, not day-by-day breakdown
      if (PROJECT_TYPE === "itinerary" && PLAN_DATA.days) {{
        // Render cities geographic clustering for Cities tab
        const cityClusters = {{}};
        PLAN_DATA.days.forEach(day => {{
          (day.attractions || []).forEach(attr => {{
            const city = day.location;
            if (!cityClusters[city]) cityClusters[city] = [];
            cityClusters[city].push({{ ...attr, location: day.location }});
          }});
        }});

        citiesHtml = Object.entries(cityClusters).map(([city, attractions], idx) => {{
          const uniqueAttractions = attractions.filter((attr, idx, self) =>
            idx === self.findIndex(a => a.name === attr.name)
          );

          return `
            <div class="accordion-item" id="city-${{idx}}">
              <div class="accordion-header" onclick="toggleAccordion(${{idx}})">
                <h3>
                  <i class="fas fa-city"></i>
                  ${{city}} (${{uniqueAttractions.length}} attractions)
                </h3>
                <i class="fas fa-chevron-down accordion-icon"></i>
              </div>
              <div class="accordion-content">
                <div class="accordion-body">
                  <div class="activity-grid">
                    ${{uniqueAttractions.map(attr => {{
                      const links = generateMapLinksBash(attr.name, attr.location);
                      return `
                        <div class="activity-card">
                          <h4>${{attr.name}}</h4>
                          <p><i class="fas fa-map-marker-alt"></i> ${{formatAddress(attr.location || attr.address)}}</p>
                          ${{attr.type ? `<span class="type-badge">${{formatCategoryLabel(attr.type, 'attraction')}}</span>` : ''}}
                          <div class="attraction-links" style="margin-top: 10px;">
                            <a href="${{links.mapLink}}" target="_blank" class="attraction-link ${{links.isMainland ? 'gaode' : 'google'}}">
                              <i class="fas ${{links.isMainland ? 'fa-map-marked-alt' : 'fa-map-marker-alt'}}"></i>
                              ${{links.isMainland ? 'Gaode Maps' : 'Google Maps'}}
                            </a>
                            <a href="${{links.rednote}}" target="_blank" class="attraction-link rednote">
                              <i class="fas fa-book-open"></i>
                              RedNote
                            </a>
                          </div>
                        </div>
                      `;
                    }}).join('')}}
                  </div>
                </div>
              </div>
            </div>
          `;
        }}).join('');
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
            <div class="chart-hint">Click on any category to see daily breakdown</div>
          </div>
          <div class="chart-card">
            <div class="chart-title">
              <i class="fas fa-chart-line"></i> Daily Budget Trend
            </div>
            <div class="chart-container">
              <canvas id="dailyBudgetChart"></canvas>
            </div>
            <div class="chart-hint">Click on any point to see day details</div>
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
            onClick: (event, elements) => {{
              if (elements.length > 0) {{
                const index = elements[0].index;
                const categoryKey = Object.keys(categories)[index];
                const categoryLabel = categoryKey.charAt(0).toUpperCase() + categoryKey.slice(1);
                const items = PLAN_DATA.days.map(d => ({{
                  name: `Day ${{d.day}} - ${{d.location}}`,
                  value: d.budget?.[categoryKey] || 0,
                  meta: d.date
                }})).filter(item => item.value > 0);
                openDataDrawer(
                  `${{categoryLabel}} Budget Breakdown`,
                  {{
                    'Category': categoryLabel,
                    'Total': `${{CURRENCY_CONFIG_BASH.currency_symbol}}${{toEURBash(categories[categoryKey])}}`,
                    'Days with Expense': items.length
                  }},
                  items,
                  {{ nameKey: 'name', valueKey: 'value', metaKey: 'meta', formatValue: (v) => `${{CURRENCY_CONFIG_BASH.currency_symbol}}${{toEURBash(v)}}` }}
                );
              }}
            }},
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
                    return context.label + ': ' + CURRENCY_CONFIG_BASH.currency_symbol + toEURBash(context.raw);
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
            onClick: (event, elements) => {{
              if (elements.length > 0) {{
                const index = elements[0].index;
                const day = PLAN_DATA.days[index];
                if (day && day.budget) {{
                  const items = Object.keys(categories).map(key => ({{
                    name: key.charAt(0).toUpperCase() + key.slice(1),
                    value: day.budget[key] || 0,
                    meta: key
                  }})).filter(item => item.value > 0);
                  openDataDrawer(
                    `Day ${{day.day}} Budget - ${{day.location}}`,
                    {{
                      'Date': day.date,
                      'Location': day.location,
                      'Total Budget': `${{CURRENCY_CONFIG_BASH.currency_symbol}}${{toEURBash(day.budget.total || 0)}}`
                    }},
                    items,
                    {{ nameKey: 'name', valueKey: 'value', metaKey: 'meta', formatValue: (v) => `${{CURRENCY_CONFIG_BASH.currency_symbol}}${{toEURBash(v)}}` }}
                  );
                }}
              }}
            }},
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
              // Root cause fix: commit 41f1017 - some charts use showDetailPanel, should use openDataDrawer
              if (elements.length > 0) {{
                const index = elements[0].index;
                const city = PLAN_DATA.cities[index];
                if (city) {{
                  const items = [];
                  if (city.attractions) {{
                    city.attractions.forEach(attr => {{
                      items.push({{
                        name: attr.name,
                        value: attr.cost_eur || 0,
                        meta: formatCategoryLabel(attr.type, 'attraction')
                      }});
                    }});
                  }}
                  openDataDrawer(
                    `${{city.city}} - Budget Breakdown`,
                    {{
                      'Estimated Budget': `€${{city.estimated_budget_eur || 0}}`,
                      'Duration': city.recommended_duration,
                      'Attractions': (city.attractions || []).length
                    }},
                    items,
                    {{ nameKey: 'name', valueKey: 'value', metaKey: 'meta', formatValue: (v) => v > 0 ? `€${{v}}` : 'Free' }}
                  );
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

      // Root cause fix: Timeline and Cities tabs showed identical content
      // Timeline tab should show Kanban route map (day-by-day timeline by city)
      if (PROJECT_TYPE === "itinerary" && PLAN_DATA.days) {{
        const cityGroups = {{}};
        PLAN_DATA.days.forEach(day => {{
          if (!cityGroups[day.location]) cityGroups[day.location] = [];
          cityGroups[day.location].push(day);
        }});

        timelineHtml = `
          <div class="route-map">
            <h2 style="color: var(--color-secondary); margin-bottom: 20px;">
              <i class="fas fa-route"></i> Route Timeline
            </h2>
            <div class="route-kanban">
              ${{Object.entries(cityGroups).map(([city, days]) => {{
                const totalBudget = days.reduce((sum, d) => sum + (d.budget?.total || 0), 0);
                return `
                  <div class="route-city">
                    <div class="route-city-header">${{escapeHtml(city)}}</div>
                    <div class="route-city-days">
                      ${{days.map(d => `
                        <div class="route-day-item">
                          <div class="route-day-date">Day ${{escapeHtml(d.day)}} - ${{escapeHtml(d.date)}}</div>
                          <div class="route-day-budget">${{escapeHtml(CURRENCY_CONFIG_BASH.currency_symbol)}}${{toEURBash(d.budget?.total || 0)}}</div>
                        </div>
                      `).join('')}}
                      <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid var(--color-neutral); font-weight: bold; color: var(--color-danger);">
                        Total: ${{escapeHtml(CURRENCY_CONFIG_BASH.currency_symbol)}}${{toEURBash(totalBudget)}}
                      </div>
                    </div>
                  </div>
                `;
              }}).join('')}}
            </div>
          </div>
        `;
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

    // Additional JavaScript functions migrated from bash script (commit 95a42d3)
    // Currency conversion functions (Feature 7)
    const CURRENCY_CONFIG = PLAN_DATA.currency_config || {{
      source_currency: 'CNY',
      display_currency: 'EUR',
      exchange_rate: 7.8,
      currency_symbol: '€'
    }};

    function convertCurrency(amount) {{
      return (amount * CURRENCY_CONFIG.exchange_rate).toFixed(2);
    }}

    function toEUR(cny) {{
      return convertCurrency(cny);
    }}

    // Map links generation (Feature 5)
    function generateMapLinks(name, location) {{
      const encodedName = encodeURIComponent(name);
      const encodedLocation = encodeURIComponent(location);

      const isMainland = !location.includes('Hong Kong') && !location.includes('Macau') &&
                         !location.includes('HK') && !location.includes('MO');

      const mapLink = isMainland
        ? `https://ditu.amap.com/search?query=${{encodedName}}`
        : `https://www.google.com/maps/search/?api=1&query=${{encodedName}}+${{encodedLocation}}`;

      const rednoteLink = `https://www.xiaohongshu.com/search_result?keyword=${{encodedName}}`;

      return {{ mapLink, rednote: rednoteLink, isMainland }};
    }}

    // Toggle functions for expandable sections
    function toggleStat(idx) {{
      const details = document.getElementById(`stat-details-${{idx}}`);
      const card = details.closest('.stat-card-expandable');
      details.classList.toggle('active');
      card.classList.toggle('expanded');
    }}

    function toggleBudgetCity(idx) {{
      const details = document.getElementById(`budget-city-${{idx}}`);
      const card = details.closest('.budget-city-card');
      details.classList.toggle('active');
      card.classList.toggle('expanded');
    }}

    function toggleAttractionType(type) {{
      const element = document.getElementById(`attraction-type-${{type}}`);
      if (element) {{
        element.classList.toggle('expanded');
      }}
    }}

    function scrollToCity(city) {{
      const element = document.getElementById(`city-${{city.replace(/\\s+/g, '-')}}`);
      if (element) element.scrollIntoView({{ behavior: 'smooth' }});
    }}

    function scrollToDay(day) {{
      const element = document.getElementById(`day-${{day}}`);
      if (element) element.scrollIntoView({{ behavior: 'smooth' }});
    }}

    function toggleCitiesPanel() {{
      const panel = document.getElementById('cities-side-panel');
      if (panel) {{
        panel.classList.toggle('active');
      }}
    }}

    function closePanel() {{
      const panel = document.getElementById('emergency-panel');
      if (panel) {{
        panel.classList.remove('active');
      }}
      const citiesPanel = document.getElementById('cities-side-panel');
      if (citiesPanel) {{
        citiesPanel.classList.remove('active');
      }}
    }}

    function toggleDay(dayNum) {{
      const content = document.getElementById(`day-${{dayNum}}`);
      if (content) {{
        content.classList.toggle('active');
      }}
    }}

    {bash_features_js}

    // Initialize main features and bash features
    init();
    initBashFeatures();
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
