#!/usr/bin/env python3
"""Test HTML generation with actual data to verify formatters work correctly."""

import sys
from pathlib import Path

# Add scripts/lib to path
sys.path.insert(0, str(Path(__file__).parent / 'lib'))

from html_generator import TravelPlanHTMLGenerator

def main():
    if len(sys.argv) < 2:
        print("Usage: python test-html-generation.py <data-directory>")
        sys.exit(1)

    data_dir = Path(sys.argv[1])
    if not data_dir.exists():
        print(f"Error: Directory {data_dir} does not exist")
        sys.exit(1)

    output_file = data_dir / "travel-plan-test.html"

    print(f"Generating HTML from: {data_dir}")
    print(f"Output file: {output_file}")

    try:
        # Extract destination slug from directory name
        destination_slug = data_dir.name
        generator = TravelPlanHTMLGenerator(destination_slug, data_dir)
        generator.generate_html(output_file)
        print(f"✓ HTML generated successfully: {output_file}")
        return 0
    except Exception as e:
        print(f"✗ Error generating HTML: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
