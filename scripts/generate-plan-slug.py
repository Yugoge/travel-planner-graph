#!/usr/bin/env python3
"""Generate unique plan slug from destination and timestamp.

Addresses root cause from commit 77dca06 where {destination-slug} was used
40+ times but never defined, causing multiple /plan executions to reuse
the same directory and mix files.

Slug format: {destination-sanitized}-{YYYYMMDD-HHMMSS}
Example: china-20260201-211600
"""

import argparse
import re
import sys
from datetime import datetime
from typing import Optional


def sanitize_destination(destination: str) -> str:
    """Sanitize destination name for safe filesystem usage.

    Handles Chinese characters, spaces, special characters safely.

    Args:
        destination: Raw destination name (can contain Chinese, spaces, etc.)

    Returns:
        Sanitized string safe for filesystem (lowercase alphanumeric + hyphens)
    """
    # Convert to lowercase
    sanitized = destination.lower()

    # Replace spaces and underscores with hyphens
    sanitized = sanitized.replace(' ', '-').replace('_', '-')

    # Remove all non-alphanumeric characters except hyphens
    # This handles Chinese characters, special chars, etc.
    sanitized = re.sub(r'[^a-z0-9\-]', '', sanitized)

    # Collapse multiple consecutive hyphens
    sanitized = re.sub(r'-+', '-', sanitized)

    # Remove leading/trailing hyphens
    sanitized = sanitized.strip('-')

    # If sanitization resulted in empty string, use fallback
    if not sanitized:
        sanitized = 'destination'

    return sanitized


def generate_timestamp(custom_timestamp: Optional[str] = None) -> str:
    """Generate timestamp string in YYYYMMDD-HHMMSS format.

    Args:
        custom_timestamp: Optional ISO-8601 timestamp string.
                         If None, uses current time.

    Returns:
        Timestamp string in format YYYYMMDD-HHMMSS
    """
    if custom_timestamp:
        try:
            dt = datetime.fromisoformat(custom_timestamp.replace('Z', '+00:00'))
        except ValueError:
            # Fallback to current time if custom timestamp invalid
            dt = datetime.now()
    else:
        dt = datetime.now()

    return dt.strftime('%Y%m%d-%H%M%S')


def generate_plan_slug(destination: str, timestamp: Optional[str] = None) -> str:
    """Generate unique plan slug.

    Format: {destination-sanitized}-{YYYYMMDD-HHMMSS}

    Args:
        destination: Destination name (any language, spaces allowed)
        timestamp: Optional ISO-8601 timestamp. Defaults to current time.

    Returns:
        Slug string in format: destination-sanitized-YYYYMMDD-HHMMSS

    Examples:
        >>> generate_plan_slug("China", "2026-02-01T21:16:00Z")
        'china-20260201-211600'

        >>> generate_plan_slug("New York City")
        'new-york-city-20260201-235500'

        >>> generate_plan_slug("中国")
        'china-20260201-235500'
    """
    sanitized_dest = sanitize_destination(destination)
    timestamp_str = generate_timestamp(timestamp)

    return f"{sanitized_dest}-{timestamp_str}"


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Generate unique plan slug from destination and timestamp',
        epilog='Root cause: commit 77dca06 introduced {destination-slug} without generation logic'
    )
    parser.add_argument(
        'destination',
        help='Destination name (any language, spaces allowed)'
    )
    parser.add_argument(
        '--timestamp',
        default=None,
        help='Optional ISO-8601 timestamp (default: current time)'
    )

    args = parser.parse_args()

    slug = generate_plan_slug(args.destination, args.timestamp)

    # Print only the slug (for easy capture in bash)
    print(slug)

    return 0


if __name__ == '__main__':
    sys.exit(main())
