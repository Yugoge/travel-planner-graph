# HTML File Naming Convention

## Principle

Use **descriptive, human-readable directory names** instead of timestamps.

## URL Format

```
https://yugoge.github.io/travel-planner-graph/{trip-slug}/{date}/
```

## Trip Slugs

| Directory Name | Display Title | Type |
|----------------|---------------|------|
| `china-trip-2026` | China Feb-Mar 2026 | Itinerary (21 days) |
| `china-weekend-destinations` | China Weekend Destinations | Bucket List |
| `beijing-weekend-trips` | Beijing Weekend Trips | Bucket List |

## Date Format

Use `YYYY-MM-DD` format representing when the HTML was generated.

## Example Full URLs

- China Trip: `https://yugoge.github.io/travel-planner-graph/china-trip-2026/2026-02-11/`
- China Bucket List: `https://yugoge.github.io/travel-planner-graph/china-weekend-destinations/2026-02-10/`
- Beijing Bucket List: `https://yugoge.github.io/travel-planner-graph/beijing-weekend-trips/2026-02-02/`

## Migration Plan

The old timestamp-based URLs (like `china-feb-15-mar-7-2026-20260202-195429`) should redirect to the new names.

For now, keep both old and new URLs working by creating symbolic directories or redirects.
