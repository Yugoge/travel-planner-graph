"""
Replace Google Maps API photo URLs in bucket-list image datasets with Gaode search results.

Usage: python scripts/fix-google-photo-urls.py

Targets:
  1. beijing-exchange-bucket-list-20260202-232405/images.json - city_covers section
  2. china-exchange-bucket-list-2026/images.json - pois section (google_ prefixed keys)
"""

import json
import time
import urllib.parse
import urllib.request
import ssl
import os

GAODE_API_KEY = "99e97af6fd426ce3cfc45d22d26e78e3"
GAODE_BASE_URL = "https://restapi.amap.com/v3/place/text"
DELAY_SECONDS = 0.3

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def gaode_search(keywords):
    """Search Gaode for a place and return the first non-icon photo URL."""
    params = urllib.parse.urlencode({
        "key": GAODE_API_KEY,
        "keywords": keywords,
        "extensions": "all",
        "output": "json",
    })
    url = f"{GAODE_BASE_URL}?{params}"

    # Allow HTTPS without strict cert verification for API calls
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  ERROR: API request failed for '{keywords}': {e}")
        return None

    if data.get("status") != "1" or not data.get("pois"):
        print(f"  WARNING: No results for '{keywords}'")
        return None

    # Walk through POIs and their photos, skip .png icons
    for poi in data["pois"]:
        photos = poi.get("photos", [])
        for photo in photos:
            photo_url = photo.get("url", "")
            if photo_url and not photo_url.lower().endswith(".png"):
                # Force HTTPS
                if photo_url.startswith("http://"):
                    photo_url = "https://" + photo_url[7:]
                return photo_url

    print(f"  WARNING: No usable photo found for '{keywords}'")
    return None


def is_google_url(url):
    """Check if a URL is a Google Maps API URL."""
    return "googleapis" in url


def fix_city_covers(images_path):
    """Fix Google Maps URLs in city_covers of beijing-exchange dataset."""
    print(f"\n{'='*70}")
    print(f"Processing: {images_path}")
    print(f"Section: city_covers")
    print(f"{'='*70}")

    with open(images_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    city_covers = data.get("city_covers", {})
    replaced = 0
    failed = 0

    for city_name, url in list(city_covers.items()):
        if not is_google_url(url):
            continue

        search_term = f"{city_name} 景点"
        print(f"\n  [{city_name}] Searching Gaode for: {search_term}")

        new_url = gaode_search(search_term)
        time.sleep(DELAY_SECONDS)

        if new_url:
            city_covers[city_name] = new_url
            replaced += 1
            print(f"  [{city_name}] REPLACED -> {new_url[:80]}...")
        else:
            failed += 1
            print(f"  [{city_name}] FAILED - keeping original URL")

    data["city_covers"] = city_covers

    with open(images_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\nSummary: {replaced} replaced, {failed} failed")
    return replaced, failed


def fix_pois_google_prefix(images_path):
    """Fix Google Maps URLs in pois of china-exchange dataset (google_ prefixed keys)."""
    print(f"\n{'='*70}")
    print(f"Processing: {images_path}")
    print(f"Section: pois (google_ prefixed keys)")
    print(f"{'='*70}")

    with open(images_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    pois = data.get("pois", {})
    replaced = 0
    failed = 0

    for key, url in list(pois.items()):
        if not is_google_url(url):
            continue

        # Extract name: keys are like "google_Victoria Peak" or "google_Ovolo Hong Kong, Central"
        if key.startswith("google_"):
            name = key[len("google_"):]
        else:
            # Fallback: use key as-is
            name = key

        print(f"\n  [{name}] Searching Gaode for: {name}")

        new_url = gaode_search(name)
        time.sleep(DELAY_SECONDS)

        if new_url:
            # Replace the key prefix from google_ to gaode_
            new_key = f"gaode_{name}"
            del pois[key]
            pois[new_key] = new_url
            replaced += 1
            print(f"  [{name}] REPLACED -> {new_url[:80]}...")
            print(f"  [{name}] Key renamed: {key} -> {new_key}")
        else:
            failed += 1
            print(f"  [{name}] FAILED - keeping original URL and key")

    data["pois"] = pois

    with open(images_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\nSummary: {replaced} replaced, {failed} failed")
    return replaced, failed


def main():
    print("Fix Google Maps API photo URLs in bucket-list image datasets")
    print("=" * 70)

    total_replaced = 0
    total_failed = 0

    # Dataset 1: beijing-exchange city_covers
    path1 = os.path.join(DATA_DIR, "beijing-exchange-bucket-list-20260202-232405", "images.json")
    if os.path.exists(path1):
        r, f = fix_city_covers(path1)
        total_replaced += r
        total_failed += f
    else:
        print(f"WARNING: File not found: {path1}")

    # Dataset 2: china-exchange pois
    path2 = os.path.join(DATA_DIR, "china-exchange-bucket-list-2026", "images.json")
    if os.path.exists(path2):
        r, f = fix_pois_google_prefix(path2)
        total_replaced += r
        total_failed += f
    else:
        print(f"WARNING: File not found: {path2}")

    print(f"\n{'='*70}")
    print(f"TOTAL: {total_replaced} URLs replaced, {total_failed} failures")
    print(f"{'='*70}")

    # Final check: count remaining googleapis URLs
    remaining = 0
    for path in [path1, path2]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            count = content.count("googleapis")
            if count > 0:
                remaining += count
                print(f"WARNING: {count} googleapis URLs still remain in {path}")

    if remaining == 0:
        print("All googleapis URLs have been successfully replaced.")


if __name__ == "__main__":
    main()
