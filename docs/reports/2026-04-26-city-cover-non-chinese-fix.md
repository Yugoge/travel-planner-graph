# City Cover Fetching — Non-Chinese Destination Fix

**Date**: 2026-04-26
**Surfaced by**: `/review` on trip `gerardmer-20260419-135844` (France, no native-script city name)
**Affected files**: `scripts/fetch-images-batch.py`, `.claude/commands/review.md`

## Symptom

After running `/review` on the Gerardmer trip, the rendered HTML had no city hero image. `data/<slug>/images.json` showed `city_covers: {}` — empty — even though POI photos were fetched normally.

## Root cause #1: `fetch-images-batch.py` excluded any city without `location_local`

`fetch_cities()` built `city_local_map` only when BOTH the English name and the local-script name existed:

```python
if loc and loc_local:
    city_local_map[loc] = loc_local
```

For non-Chinese destinations (Gerardmer, Reykjavík, Innsbruck, …), agents leave `location_local: ""` because the city name doesn't have a separate native script. The condition skipped every city, so `cities = set()` and zero covers were ever fetched — silent failure, no error.

### Fix
`scripts/fetch-images-batch.py:523-530` — gate on `loc` only and fall back to English when local is missing:

```python
# Build city mapping: English name -> local name
# Fall back to English name when location_local is missing (e.g., non-Chinese destinations)
city_local_map = {}
for day in skeleton.get("days", []):
    loc = day.get("location")
    loc_local = day.get("location_local")
    if loc:
        city_local_map[loc] = loc_local or loc
```

## Root cause #2: `/review` never re-checked covers

`/review`'s per-day image fetch hard-coded `city_limit=0` (`fetch-images-batch.py {slug} 0 999 --day N`), assuming `/plan` had already populated `city_covers`. When `/plan` had been hit by Bug #1 (or `/review` was run standalone on a project without prior `/plan`), nothing in the `/review` flow ever fetched city covers — they stayed empty forever.

### Fix
`.claude/commands/review.md:301` — new **Step 3: Ensure City Covers Are Fetched** between Step 2 (Load Plan Data) and Phase 4 (Validation):

- Reads `data/<slug>/images.json`
- If `city_covers` is empty (or file is missing), runs `fetch-images-batch.py <slug> 5 0` once
- Non-blocking: a 0/N fetch (extremely rare) does not abort the review loop

## Impact

Together these fixes make `/plan` + `/review` robust for any destination:

- Chinese trips continue to work as before (the local name is preferred when present)
- European / non-Chinese trips now get city covers via the English-name fallback
- Standalone `/review` runs (no prior `/plan`) self-heal city covers on first invocation

## Verification

Re-ran on `gerardmer-20260419-135844` after both fixes:

```
🏙️  Fetching city covers (max 5)...
  Total fetched: 1/5
```

`images.json.city_covers` now contains the Gerardmer entry; HTML hero image renders correctly at <https://travel.life-ai.app/gerardmer/2026-04-19/>.
