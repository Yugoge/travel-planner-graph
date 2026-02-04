# Currency Explosion Bug - QA Analysis Report

**Date**: 2026-02-04
**Severity**: CRITICAL
**Status**: CONFIRMED - Bug causes 7.8x price inflation
**QA Result**: FAIL

---

## Executive Summary

User complaint "货币暴涨" (currency explosion) is CONFIRMED. All individual item prices throughout the HTML display are showing CNY values with € symbol WITHOUT conversion, making costs appear 7.8x higher than they should be.

**Example**: A 120 CNY meal displays as "€120" when it should show "€15.38"

---

## Root Cause

HTML template references non-existent `_eur` fields (`cost_eur`, `ticket_price_eur`, `price_per_night_eur`) that don't exist in the data files. When these fields are undefined, the template falls back to the `cost` field which contains raw CNY values, and displays them with a € symbol.

**File**: `/root/travel-planner/scripts/lib/html_generator.py`

---

## Critical Bug Locations

### Bug #1: Attraction Costs (Line 2771)

```javascript
<p class="cost"><i class="fas fa-euro-sign"></i> €${attr.cost_eur || attr.cost || 0}</p>
```

**Problem**: `attr.cost_eur` is undefined → falls back to `attr.cost` (CNY) → displays CNY with €

**Example**:
- Saint Sophia Cathedral: `cost = 3` CNY
- Displays: €3
- Should display: €0.38
- Error: 7.8x too high

**Fix**: Change to `€${toEURBash(attr.cost || 0)}`

---

### Bug #2: Accommodation Costs (Line 2789)

```javascript
<p class="cost"><i class="fas fa-euro-sign"></i> €${day.accommodation.cost_eur || 0}</p>
```

**Problem**: `cost_eur` undefined → displays €0 even when `cost` exists

**Example**:
- Day 1 hotel: `cost = 350` CNY
- Displays: €0
- Should display: €44.87
- Error: Value missing entirely

**Fix**: Change to `€${toEURBash(day.accommodation.cost || 0)}`

---

### Bug #3: Meal Costs (Line 2807)

```javascript
<p class="cost"><i class="fas fa-euro-sign"></i> €${day[meal].cost_eur || day[meal].cost || 0}</p>
```

**Problem**: `cost_eur` undefined → falls back to CNY `cost` → displays CNY with €

**Example**:
- Day 1 lunch (Sofiya Russian Restaurant): `cost = 120` CNY
- Displays: €120
- Should display: €15.38
- Error: 7.8x too high

**Fix**: Change to `€${toEURBash(day[meal].cost || 0)}`

---

### Bug #4: Wrong Conversion Formula (Line 3250)

```javascript
function convertCurrency(amount) {
  return (amount * CURRENCY_CONFIG.exchange_rate).toFixed(2);  // WRONG!
}
```

**Problem**: Formula MULTIPLIES by exchange rate instead of DIVIDING

**Example**:
- 120 CNY * 7.8 = €936 (WRONG!)
- Should be: 120 CNY / 7.8 = €15.38

**Impact**: If this function were used, would cause 60.8x explosion

**Status**: Currently unused (defined but not called), but dangerous if someone uses it

**Fix**: Change to `return (amount / CURRENCY_CONFIG.exchange_rate).toFixed(2);`

---

## Data Structure Analysis

### What EXISTS in data files:

```json
{
  "cost": 120,           // CNY value
  "cost_cny": 120,       // CNY value
  "ticket_price_cny": 50 // CNY value (attractions only)
}
```

### What DOESN'T exist but template expects:

```json
{
  "cost_eur": 15.38,           // MISSING
  "ticket_price_eur": 6.41,    // MISSING
  "price_per_night_eur": 44.87 // MISSING
}
```

---

## Examples of Incorrect Display

### Day 1 Examples:

| Item | Cost (CNY) | Displayed As | Should Be | Error |
|------|------------|--------------|-----------|-------|
| Breakfast (老鼎丰) | ¥35 | €35 | €4.49 | 7.8x |
| Lunch (Sofiya) | ¥120 | €120 | €15.38 | 7.8x |
| Saint Sophia Cathedral | ¥3 | €3 | €0.38 | 7.8x |
| Accommodation | ¥350 | €0 | €44.87 | Missing |

### Total Budget:

| Item | Value |
|------|-------|
| Total CNY | ¥18,096 |
| Correct EUR | €2,320.00 |
| If wrong conversion used | €141,148.80 (60.8x explosion) |

---

## What Works Correctly

### Dashboard Widgets (Lines 1507-1529)

```javascript
'Total Budget': `${CURRENCY_CONFIG_BASH.currency_symbol}${toEURBash(totalBudgetCNY)}`
```

✅ Uses `toEURBash()` function correctly
✅ Divides by 7.8
✅ Displays accurate EUR values

### Data Drawers

```javascript
formatValue: (v) => `${CURRENCY_CONFIG_BASH.currency_symbol}${toEURBash(v)}`
```

✅ All drawer displays use `toEURBash()`
✅ Show correct converted values

### Budget.json Pre-calculations

```json
{
  "total_cny": 1640,
  "total_eur": 210.26  // Correctly calculated: 1640 / 7.8 = 210.26
}
```

✅ Budget agent calculates EUR correctly

---

## Conversion Functions Comparison

### CORRECT Function (Line 746):

```javascript
function convertCurrencyBash(amount) {
  if (!amount || isNaN(amount)) return '0.00';
  return (amount / CURRENCY_CONFIG_BASH.exchange_rate).toFixed(2);  // DIVIDES
}

function toEURBash(cny) {
  return convertCurrencyBash(cny);
}
```

✅ Formula: `CNY / 7.8 = EUR`
✅ Example: `120 / 7.8 = 15.38`
✅ Used in dashboard widgets
✅ Used in data drawers

### WRONG Function (Line 3250):

```javascript
function convertCurrency(amount) {
  return (amount * CURRENCY_CONFIG.exchange_rate).toFixed(2);  // MULTIPLIES
}

function toEUR(cny) {
  return convertCurrency(cny);
}
```

❌ Formula: `CNY * 7.8 = EUR` (WRONG!)
❌ Example: `120 * 7.8 = 936`
⚠️ Currently unused but dangerous

---

## Recommended Fix

### Option 1: Template-side Conversion (RECOMMENDED)

Replace all `cost_eur` references with `toEURBash(cost)` calls:

**Line 2771**: `€${attr.cost_eur || attr.cost || 0}`
→ `€${toEURBash(attr.cost || 0)}`

**Line 2789**: `€${day.accommodation.cost_eur || 0}`
→ `€${toEURBash(day.accommodation.cost || 0)}`

**Line 2807**: `€${day[meal].cost_eur || day[meal].cost || 0}`
→ `€${toEURBash(day[meal].cost || 0)}`

**Line 2864**: `${attr.ticket_price_eur ? ...}`
→ `€${toEURBash(attr.ticket_price_cny || attr.cost || 0)}`

**Line 2882**: `if (hotel.price_per_night_eur)`
→ `€${toEURBash(hotel.price_per_night_cny || hotel.cost || 0)}`

**Line 3250**: `return (amount * CURRENCY_CONFIG.exchange_rate).toFixed(2);`
→ `return (amount / CURRENCY_CONFIG.exchange_rate).toFixed(2);`

### Option 2: Data-side Conversion

Add conversion step in `merge_itinerary_data()` to populate `_eur` fields for all items before passing to template.

**Recommendation**: Use Option 1 (simpler, reuses existing working function)

---

## Impact Assessment

### User Impact:

- ❌ All displayed prices are WRONG
- ❌ Trip appears 7.8x more expensive than it actually is
- ❌ Budget planning completely broken
- ❌ User cannot trust any price information

### Data Impact:

- ✅ Underlying data is CORRECT (CNY values accurate)
- ✅ Budget calculations are CORRECT
- ❌ Only display layer is broken

---

## QA Verdict

**Status**: FAIL
**Critical Issues**: 4
**Major Issues**: 2
**Release Recommendation**: REJECT

**Rationale**: Currency display bug makes all pricing information unreliable. Users cannot trust displayed values. This is a show-stopper bug that must be fixed before any release.

---

## Next Steps

1. Dev agent implements fix using Option 1 (template-side conversion)
2. Re-run QA to verify all prices display correctly
3. Test with multiple data files to ensure fix is universal
4. Verify dashboard and data drawers still work correctly after changes

---

## Files Affected

- `/root/travel-planner/scripts/lib/html_generator.py` (primary fix location)
- `/root/travel-planner/travel-plan-beijing-exchange-bucket-list-20260202-232405.html` (output file - will be regenerated)

---

**QA Report Generated**: 2026-02-04T15:45:00Z
**QA Agent**: QA #1
**Verified By**: Line-by-line code inspection + data structure analysis
