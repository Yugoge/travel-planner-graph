#!/usr/bin/env python3
"""
Generate GitHub Pages index.html by scanning deployed plans
"""

import os
import json
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
from typing import List, Dict

def extract_plan_metadata(html_path: Path) -> Dict:
    """Extract metadata from a plan HTML file"""
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')

            # Try to find PLAN_DATA script
            script = soup.find('script', string=lambda t: t and 'const PLAN_DATA' in t)
            if script:
                # Extract JSON data
                json_start = script.string.find('{')
                json_end = script.string.rfind('}') + 1
                if json_start > 0 and json_end > json_start:
                    data = json.loads(script.string[json_start:json_end])
                    summary = data.get('tripSummary', {})

                    return {
                        'title': summary.get('description', 'Travel Plan'),
                        'period': summary.get('period', ''),
                        'base_location': summary.get('base_location', ''),
                        'budget': summary.get('budget_per_trip', ''),
                        'city_count': len(data.get('trips', [])),
                    }

            # Fallback: try to extract from HTML
            title_tag = soup.find('title')
            if title_tag:
                return {'title': title_tag.string or 'Travel Plan'}

    except Exception as e:
        print(f"Warning: Could not extract metadata from {html_path}: {e}")

    return {'title': 'Travel Plan'}

def scan_deployments(gh_pages_dir: Path) -> List[Dict]:
    """Scan gh-pages directory for all deployed plans"""
    plans = []

    # Scan for plan directories (format: plan-name-timestamp)
    for plan_dir in gh_pages_dir.iterdir():
        if not plan_dir.is_dir() or plan_dir.name.startswith('.'):
            continue

        # Scan for version directories (format: YYYY-MM-DD)
        for version_dir in plan_dir.iterdir():
            if not version_dir.is_dir():
                continue

            index_path = version_dir / 'index.html'
            if not index_path.exists():
                continue

            # Extract metadata
            metadata = extract_plan_metadata(index_path)

            # Parse date from directory name
            try:
                version_date = datetime.strptime(version_dir.name, '%Y-%m-%d')
            except ValueError:
                continue

            # Create plan entry
            plan_slug = plan_dir.name
            plan_title = metadata.get('title', plan_slug.replace('-', ' ').title())

            # Determine emoji based on location or plan name
            emoji = '🌏'
            if 'beijing' in plan_slug.lower() or 'china' in plan_slug.lower():
                emoji = '🇨🇳'
            elif 'japan' in plan_slug.lower():
                emoji = '🇯🇵'
            elif 'europe' in plan_slug.lower():
                emoji = '🇪🇺'

            plans.append({
                'emoji': emoji,
                'title': plan_title,
                'slug': plan_slug,
                'version': version_dir.name,
                'url': f"{plan_slug}/{version_dir.name}/",
                'date': version_date,
                'period': metadata.get('period', ''),
                'city_count': metadata.get('city_count', 0),
            })

    # Sort by date (newest first)
    plans.sort(key=lambda x: x['date'], reverse=True)

    return plans

def generate_index_html(plans: List[Dict]) -> str:
    """Generate index.html from plans list"""

    # Group plans by slug (to show versions together)
    plans_by_slug = {}
    for plan in plans:
        slug = plan['slug']
        if slug not in plans_by_slug:
            plans_by_slug[slug] = []
        plans_by_slug[slug].append(plan)

    # Generate plan cards HTML
    cards_html = []
    for slug, versions in plans_by_slug.items():
        # Use latest version for display
        latest = versions[0]

        # Build metadata line
        meta_parts = []
        if latest['city_count']:
            meta_parts.append(f"{latest['city_count']} cities")
        if latest['period']:
            meta_parts.append(latest['period'])

        # Add version count if multiple versions exist
        if len(versions) > 1:
            meta_parts.append(f"{len(versions)} versions")

        meta_parts.append(f"Updated {latest['version']}")
        meta_text = ' • '.join(meta_parts)

        # Build versions dropdown if multiple versions
        versions_html = ""
        if len(versions) > 1:
            versions_items = [
                f'<a href="{v["url"]}" class="version-link">{v["version"]}</a>'
                for v in versions
            ]
            versions_html = f'''
            <div class="versions-dropdown">
              <button class="versions-button">Versions ▾</button>
              <div class="versions-menu">
                {"".join(versions_items)}
              </div>
            </div>
            '''

        card_html = f'''
        <a href="{latest['url']}" class="plan-card">
          <div class="plan-icon">{latest['emoji']}</div>
          <div class="plan-content">
            <div class="plan-title">{latest['title']}</div>
            <div class="plan-meta">{meta_text}</div>
          </div>
          {versions_html}
          <div class="arrow">→</div>
        </a>
        '''
        cards_html.append(card_html)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Travel Plans</title>
  <style>
    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}

    body {{
      font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, "Apple Color Emoji", Arial, sans-serif;
      background: #fbfbfa;
      color: #37352f;
      padding: 40px 20px;
      min-height: 100vh;
    }}

    .container {{
      max-width: 900px;
      margin: 0 auto;
    }}

    .header {{
      margin-bottom: 40px;
    }}

    .title {{
      font-size: 40px;
      font-weight: 700;
      margin-bottom: 12px;
      color: #37352f;
    }}

    .subtitle {{
      font-size: 16px;
      color: #9b9a97;
    }}

    .plans-grid {{
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}

    .plan-card {{
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 16px;
      background: white;
      border: 1px solid #e3e2e0;
      border-radius: 8px;
      text-decoration: none;
      color: inherit;
      transition: all 0.15s ease;
      position: relative;
    }}

    .plan-card:hover {{
      background: #f7f6f3;
      border-color: #d3d1cb;
      box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }}

    .plan-icon {{
      font-size: 40px;
      flex-shrink: 0;
    }}

    .plan-content {{
      flex: 1;
      min-width: 0;
    }}

    .plan-title {{
      font-size: 16px;
      font-weight: 600;
      color: #37352f;
      margin-bottom: 4px;
      line-height: 1.4;
    }}

    .plan-meta {{
      font-size: 13px;
      color: #9b9a97;
      line-height: 1.4;
    }}

    .arrow {{
      font-size: 20px;
      color: #9b9a97;
      flex-shrink: 0;
      transition: transform 0.15s ease;
    }}

    .plan-card:hover .arrow {{
      transform: translateX(4px);
      color: #37352f;
    }}

    .versions-dropdown {{
      position: relative;
      flex-shrink: 0;
      margin-left: 8px;
    }}

    .versions-button {{
      padding: 4px 12px;
      background: #f7f6f3;
      border: 1px solid #e3e2e0;
      border-radius: 4px;
      font-size: 13px;
      color: #37352f;
      cursor: pointer;
      transition: all 0.15s ease;
    }}

    .versions-button:hover {{
      background: #e3e2e0;
    }}

    .versions-menu {{
      display: none;
      position: absolute;
      top: 100%;
      right: 0;
      margin-top: 4px;
      background: white;
      border: 1px solid #e3e2e0;
      border-radius: 6px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.12);
      min-width: 140px;
      z-index: 10;
    }}

    .versions-dropdown:hover .versions-menu {{
      display: block;
    }}

    .version-link {{
      display: block;
      padding: 8px 12px;
      font-size: 13px;
      color: #37352f;
      text-decoration: none;
      transition: background 0.15s ease;
    }}

    .version-link:hover {{
      background: #f7f6f3;
    }}

    .version-link:first-child {{
      border-radius: 6px 6px 0 0;
    }}

    .version-link:last-child {{
      border-radius: 0 0 6px 6px;
    }}

    .empty-state {{
      text-align: center;
      padding: 60px 20px;
      color: #9b9a97;
    }}

    .empty-icon {{
      font-size: 60px;
      margin-bottom: 16px;
    }}

    .footer {{
      margin-top: 60px;
      padding-top: 20px;
      border-top: 1px solid #e3e2e0;
      text-align: center;
      font-size: 13px;
      color: #9b9a97;
    }}

    @media (max-width: 640px) {{
      .title {{
        font-size: 32px;
      }}

      .plan-card {{
        padding: 12px;
        gap: 12px;
      }}

      .plan-icon {{
        font-size: 32px;
      }}

      .plan-title {{
        font-size: 15px;
      }}

      .versions-dropdown {{
        position: static;
      }}

      .versions-menu {{
        position: fixed;
        left: 20px;
        right: 20px;
        top: auto;
        bottom: 20px;
      }}
    }}
  </style>
  <script>
    // Prevent version dropdown from triggering card navigation
    document.addEventListener('DOMContentLoaded', () => {{
      document.querySelectorAll('.versions-dropdown').forEach(dropdown => {{
        dropdown.addEventListener('click', (e) => {{
          e.preventDefault();
          e.stopPropagation();
        }});
      }});
    }});
  </script>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="title">✈️ Travel Plans</div>
      <div class="subtitle">Your travel planning hub</div>
    </div>

    <div class="plans-grid">
      {chr(10).join(cards_html) if cards_html else '<div class="empty-state"><div class="empty-icon">🗺️</div><div>No travel plans yet</div></div>'}
    </div>

    <div class="footer">
      Generated automatically • {datetime.now().strftime('%Y-%m-%d %H:%M')}
    </div>
  </div>
</body>
</html>
'''

    return html

def main():
    """Main function"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: generate-gh-pages-index.py <gh-pages-directory>")
        sys.exit(1)

    gh_pages_dir = Path(sys.argv[1])
    if not gh_pages_dir.exists():
        print(f"Error: Directory {gh_pages_dir} does not exist")
        sys.exit(1)

    print(f"Scanning {gh_pages_dir}...")
    plans = scan_deployments(gh_pages_dir)
    print(f"Found {len(plans)} plan versions")

    print("Generating index.html...")
    html = generate_index_html(plans)

    output_path = gh_pages_dir / 'index.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✓ Generated {output_path}")

    # Print summary
    print("\nDeployed plans:")
    for plan in plans:
        print(f"  {plan['emoji']} {plan['title']} ({plan['version']})")

if __name__ == '__main__':
    main()
