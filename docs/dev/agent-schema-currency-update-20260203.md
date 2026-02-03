# Agent Output Schema Update: Currency Metadata Requirement

**Date**: 2026-02-03
**Related Commit**: 95a42d33ff3dc0cdf6326fe0fa2ac136db749db3 (hardcoded CNY→EUR conversion)
**Fix Implementation**: Dynamic currency conversion system with real-time exchange rates

---

## Summary

All budget-providing agents must now include currency metadata in their outputs to support the new dynamic currency conversion system. This replaces the hardcoded CNY→EUR conversion rate (7.8) with real-time exchange rates.

---

## Required Changes

### Affected Agents
- `accommodation` - Hotel/lodging costs
- `attractions` - Entrance fees and activity costs
- `transportation` - Travel costs
- `meals` - Restaurant costs
- `shopping` - Shopping budgets
- `entertainment` - Entertainment costs

### Schema Change

**OLD** (no currency field):
```json
{
  "name": "Restaurant Name",
  "cost": 25,
  "notes": "Famous for pasta"
}
```

**NEW** (with currency field):
```json
{
  "name": "Restaurant Name",
  "cost": 25,
  "currency": "CNY",
  "notes": "Famous for pasta"
}
```

---

## Implementation Details

### 1. Currency Field Specification

Add a `currency` field to all cost/price objects:

```json
{
  "cost": <numeric_value>,
  "currency": "<ISO_4217_code>"
}
```

**Requirements**:
- `currency` field is **REQUIRED** for all new trip data
- Must use ISO 4217 3-letter currency codes (e.g., "CNY", "EUR", "USD", "GBP")
- Uppercase only
- For backward compatibility, missing currency defaults to "CNY" in HTML generation

**Valid examples**:
```json
{ "cost": 120, "currency": "CNY" }
{ "cost": 45, "currency": "EUR" }
{ "cost": 30, "currency": "USD" }
{ "cost": 5000, "currency": "JPY" }
```

---

### 2. Agent-Specific Updates

#### Meals Agent (`meals.md`)

Update meal cost structure:

```json
{
  "breakfast": {
    "name": "Morning Glory Cafe",
    "location": "123 Main St, Chengdu",
    "cost": 25,
    "currency": "CNY",
    "cuisine": "Local",
    "notes": "Popular breakfast spot"
  },
  "lunch": {...},
  "dinner": {...}
}
```

#### Accommodation Agent (`accommodation.md`)

Update accommodation cost structure:

```json
{
  "accommodation": {
    "name": "Hilton Hotel",
    "location": "456 City Center",
    "cost": 500,
    "currency": "CNY",
    "notes": "Per night rate"
  }
}
```

#### Attractions Agent (`attractions.md`)

Update attraction cost structure:

```json
{
  "attractions": [
    {
      "name": "Giant Panda Base",
      "location": "Chengdu",
      "cost": 55,
      "currency": "CNY",
      "notes": "Entrance fee"
    }
  ]
}
```

#### Transportation Agent (`transportation.md`)

Update travel cost structure:

```json
{
  "location_change": {
    "from": "Chengdu",
    "to": "Chongqing",
    "method": "High-speed train",
    "cost": 154.5,
    "currency": "CNY",
    "duration": "2h"
  }
}
```

#### Shopping Agent (`shopping.md`)

Update shopping budget structure:

```json
{
  "shopping": [
    {
      "item": "Silk scarf",
      "location": "Jinli Ancient Street",
      "cost": 80,
      "currency": "CNY",
      "notes": "Handmade local craft"
    }
  ]
}
```

#### Entertainment Agent (`entertainment.md`)

Update entertainment cost structure:

```json
{
  "entertainment": [
    {
      "activity": "Sichuan Opera",
      "location": "Shufeng Yayun Theater",
      "cost": 280,
      "currency": "CNY",
      "notes": "Face-changing show"
    }
  ]
}
```

---

### 3. Budget Agent Impact

The budget agent (`budget.md`) **does NOT need changes** - it aggregates costs from other agents. The currency information from source agents flows through to the budget summaries.

---

## Backward Compatibility

### Existing Trip Data

Old trip data without `currency` fields will continue to work:
- HTML generation assumes "CNY" as default source currency if not specified
- Exchange rate fetching uses `config/currency-config.json` defaults
- No data migration required for archived trips

### Fallback Behavior

```javascript
// In generated HTML:
const CURRENCY_CONFIG = PLAN_DATA.currency_config || {
  source_currency: 'CNY',
  display_currency: 'EUR',
  exchange_rate: 7.8,  // Fallback only (won't be used if API works)
  currency_symbol: '€'
};
```

---

## Testing Checklist

When updating agent definitions, verify:

- [ ] All cost fields include `currency` property
- [ ] Currency codes are valid ISO 4217 (3 uppercase letters)
- [ ] Agent output validates against new schema
- [ ] Generated HTML displays correct currency symbol
- [ ] Exchange rate conversion applies correctly
- [ ] Old trip data (without currency) still renders correctly

---

## Configuration

Global currency preferences stored in `config/currency-config.json`:

```json
{
  "default_display_currency": "EUR",
  "default_source_currency": "CNY",
  "currency_symbol_map": {
    "EUR": "€",
    "USD": "$",
    "GBP": "£",
    "CNY": "¥",
    "JPY": "¥",
    "KRW": "₩"
  }
}
```

**To change display currency**:
1. Edit `config/currency-config.json`
2. Update `default_display_currency` to desired currency (e.g., "USD")
3. HTML generation will automatically use new currency

---

## Technical Implementation

### Exchange Rate Fetching

Script: `scripts/utils/fetch-exchange-rate.sh`

```bash
# Fetch real-time exchange rate
./scripts/utils/fetch-exchange-rate.sh CNY EUR
# Output: 0.122
```

- API: exchangerate-api.com (free tier, 1500 requests/month)
- No API key required
- 5-second timeout
- Supports all major currency pairs

### HTML Generation Integration

Modified: `scripts/generate-travel-html.sh`

```bash
# Automatically fetches exchange rate during generation
./scripts/generate-travel-html.sh <destination-slug>

# Output includes:
# Fetching exchange rate: CNY → EUR...
# Exchange rate: 1 CNY = 0.122 EUR
```

---

## Root Cause Analysis

### Problem
Hardcoded `CNY_TO_EUR = 7.8` in HTML generation script (line 505)
- Introduced in commit `95a42d33ff3dc0cdf6326fe0fa2ac136db749db3`
- Rate becomes stale over time
- No support for multiple currencies
- Inflexible for international users

### Solution
1. Remove hardcoded constant
2. Fetch real-time exchange rates via API
3. Support configurable display currency
4. Add currency metadata to data schema
5. Maintain backward compatibility

---

## Migration Path

### For New Trips
- Agents automatically include currency fields
- HTML generation fetches real-time rates
- Display currency configurable via config file

### For Existing Trips
- No changes required (backward compatible)
- Can regenerate HTML with current rates
- Currency field optional but recommended

---

## Questions & Support

**Q: What if the exchange rate API is unavailable?**
A: HTML generation will fail with clear error message. Future enhancement could add fallback rates.

**Q: Can I use multiple source currencies in one trip?**
A: Currently all costs assumed to be in `default_source_currency`. Mixed currency support is future work.

**Q: How often are rates updated?**
A: Fresh rate fetched every HTML generation (no caching).

**Q: Which currency pairs are supported?**
A: All currency pairs supported by exchangerate-api.com (covers all major currencies).

---

## Files Modified

- `scripts/generate-travel-html.sh` - Remove hardcoded conversion, add dynamic fetching
- `scripts/utils/fetch-exchange-rate.sh` - NEW: Exchange rate fetcher utility
- `config/currency-config.json` - NEW: Global currency configuration
- This documentation file - Agent schema update guide

---

## Related Documentation

- `config/currency-config.json` - Currency configuration
- `scripts/utils/fetch-exchange-rate.sh` - Rate fetching implementation
- Git commit `95a42d33ff3dc0cdf6326fe0fa2ac136db749db3` - Root cause commit
