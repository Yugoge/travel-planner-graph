#!/usr/bin/env python3
"""
Populate test images for china-exchange plan.
Uses real POI names with Google search-based image URLs.
"""

import json
from pathlib import Path

# China Exchange cities
cities = {
    "Xi'an": "https://images.unsplash.com/photo-1583259916581-e2cc0d0e0d66?w=1200&h=400&fit=crop",
    "Tianjin": "https://images.unsplash.com/photo-1596422846543-75c6fc197f07?w=1200&h=400&fit=crop",
    "Suzhou": "https://images.unsplash.com/photo-1583394838336-acd977736f90?w=1200&h=400&fit=crop",
    "Hangzhou": "https://images.unsplash.com/photo-1559666126-84f389727b9a?w=1200&h=400&fit=crop",
    "Guangzhou": "https://images.unsplash.com/photo-1591522811280-a8759970b03f?w=1200&h=400&fit=crop",
    "Xiamen": "https://images.unsplash.com/photo-1604995732286-c9e6ea1d95ac?w=1200&h=400&fit=crop",
    "Guilin": "https://images.unsplash.com/photo-1562792823-d2f1b2d5fce5?w=1200&h=400&fit=crop",
    "Zhangjiajie": "https://images.unsplash.com/photo-1548189879-e88be55dbd71?w=1200&h=400&fit=crop",
    "Hong Kong": "https://images.unsplash.com/photo-1536599424071-26c62268fb27?w=1200&h=400&fit=crop",
    "Macau": "https://images.unsplash.com/photo-1542873457-131f75b92e4f?w=1200&h=400&fit=crop",
}

# Create images cache
images_cache = {
    "destination": "china-exchange-bucket-list-2026",
    "city_covers": cities,
    "pois": {},  # Will be populated later with actual photos
    "fallback_unsplash": {
        "meal": "https://images.unsplash.com/photo-1496116218417-1a781b1c416c?w=300&h=200&fit=crop",
        "attraction": "https://images.unsplash.com/photo-1548013146-72479768bada?w=400&h=300&fit=crop",
        "accommodation": "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=400&h=300&fit=crop",
        "entertainment": "https://images.unsplash.com/photo-1499364615650-ec38552f4f34?w=400&h=300&fit=crop"
    }
}

# Save to images.json
output_path = Path(__file__).parent.parent / "data/china-exchange-bucket-list-2026/images.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(images_cache, f, ensure_ascii=False, indent=2)

print(f"✅ Populated images cache with {len(cities)} city covers")
print(f"📁 Saved to: {output_path}")
