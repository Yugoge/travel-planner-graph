# QA Report: Total Budget Display Error

**Status:** FAIL (2 critical issues)
**Date:** 2026-02-04
**Issue:** Total budget displays €157,065.57 instead of correct €2,337.76

---

## Executive Summary

The total budget is displaying **6,619% higher** than it should be due to an **exchange rate formula mismatch**. The API returns a CNY→EUR rate (0.122) but the code formula assumes an EUR→CNY rate (7.8) and uses division instead of multiplication.

### Quick Stats
- **Expected:** €2,337.76 (or €2,456.67 using budget.json rate of 7.8)
- **Displayed:** €157,065.57
- **Error:** 6,619% overstatement
- **Root Cause:** Division instead of multiplication when rate < 1

---

## Root Cause Analysis

### The Bug

**Location:** `/root/travel-planner/scripts/lib/html_generator.py:2470-2472` (embedded in HTML template)

```javascript
function convertCurrencyBash(amount) {
  if (!amount || isNaN(amount)) return '0.00';
  return (amount / CURRENCY_CONFIG_BASH.exchange_rate).toFixed(2);  // ← BUG HERE
}
```

**Problem:** This formula assumes `exchange_rate` means "1 EUR = X CNY" (e.g., 7.8), but the API returns "1 CNY = X EUR" (0.122).

### Exchange Rate Semantics Mismatch

| Source | Rate Format | Rate Value | Formula | Result |
|--------|-------------|------------|---------|---------|
| budget.json | 1 EUR = X CNY | 7.8 | 19,162 ÷ 7.8 | €2,456.67 ✓ |
| API (correct interpretation) | 1 CNY = X EUR | 0.122 | 19,162 × 0.122 | €2,337.76 ✓ |
| **Current code (BUG)** | **1 CNY = X EUR** | **0.122** | **19,162 ÷ 0.122** | **€157,065.57** ✗ |

### Why This Happened

1. **API returns:** `1 CNY = 0.122 EUR` (from exchangerate-api.com)
2. **Code expects:** `1 EUR = X CNY` (like budget.json's 7.8)
3. **Formula uses:** Division, which only works when rate > 1
4. **Result:** When rate < 1, division produces catastrophically wrong values

---

## Evidence

### 1. Correct Budget Calculation
```bash
# From budget.json
daily_budgets = [1000, 640, 1475, 1379, 914, 1757, 1470, 1793, 1176, 1822, 1712, 1321, 2703]
total_cny = 19,162

# Correct conversion
19,162 CNY × 0.122 EUR/CNY = €2,337.76 ✓
19,162 CNY ÷ 7.8 CNY/EUR = €2,456.67 ✓
```

### 2. What's Displayed in HTML
```javascript
// From travel-plan-beijing-exchange-bucket-list-20260202-232405.html
const PLAN_DATA = {
  "currency_config": {
    "source_currency": "CNY",
    "display_currency": "EUR",
    "exchange_rate": 0.122,  // ← From API
    "currency_symbol": "€"
  }
}

// Calculation (WRONG)
19,162 ÷ 0.122 = 157,065.57
```

### 3. Exchange Rate Source
```bash
$ /root/travel-planner/scripts/utils/fetch-exchange-rate.sh CNY EUR
0.122

$ cat ~/.cache/travel-planner/exchange-rates-CNY-EUR.json
{
  "rate": 0.122,
  "timestamp": "2026-02-04T19:46:24Z",
  "base": "CNY",
  "target": "EUR"
}
```

The API correctly returns `0.122`, meaning "1 CNY = 0.122 EUR". The bug is in how this rate is used.

---

## Critical Issues

### Issue 1: Exchange Rate Formula Mismatch (CRITICAL)

**Severity:** Critical (blocks release)
**Location:** `html_generator.py:2470-2472`

**Problem:**
- Formula uses division: `CNY ÷ rate`
- This only works when `rate` means "1 EUR = X CNY" (e.g., 7.8)
- API returns "1 CNY = X EUR" (0.122)
- Division with rate < 1 produces wildly incorrect results

**Impact:**
- 6,619% budget overstatement
- €157,065 displayed instead of €2,338
- Unusable for user decision-making

**Fix Required:**
Option 1 (RECOMMENDED): Invert API response to match formula
```python
# html_generator.py:177
api_rate = self._fetch_exchange_rate(source_currency, display_currency)
exchange_rate = 1.0 / api_rate if api_rate > 0 else 7.8  # Invert CNY→EUR to EUR→CNY
```

Option 2: Change formula to detect rate type
```javascript
// Use multiplication if rate < 1 (CNY→EUR), division if rate > 1 (EUR→CNY)
return rate < 1 ? (amount * rate).toFixed(2) : (amount / rate).toFixed(2);
```

### Issue 2: No Exchange Rate Validation (CRITICAL)

**Severity:** Critical (blocks release)
**Location:** `html_generator.py:149-151`

**Problem:**
No validation that `exchange_rate` value makes sense for the formula.
Rate of 0.122 should trigger error if formula expects > 1.

**Impact:**
Silent failures. Wrong data displayed without warnings.

**Fix Required:**
```python
# html_generator.py:150 (after fetching rate)
exchange_rate = float(result.stdout.strip())

# Add validation
if source_currency == 'CNY' and display_currency in ['EUR', 'USD', 'GBP']:
    if exchange_rate < 1:
        raise ValueError(
            f"Exchange rate {exchange_rate} appears to be CNY→EUR format. "
            f"Formula expects EUR→CNY format (rate > 1). "
            f"Use inverted rate: {1.0/exchange_rate:.2f}"
        )

print(f"Exchange rate: 1 {display_currency} = {exchange_rate} {source_currency}", file=sys.stderr)
```

---

## Major Issues

### Issue 3: Inconsistent Rate Semantics

**Severity:** Major
**Location:** `budget.json` vs HTML `currency_config`

**Problem:**
- `budget.json` uses `cny_to_eur: 7.8` (meaning 1 EUR = 7.8 CNY)
- HTML uses `exchange_rate: 0.122` (meaning 1 CNY = 0.122 EUR)
- Same currencies, opposite rate directions
- Naming is ambiguous ("cny_to_eur" could mean either direction)

**Recommendation:**
Standardize on explicit naming:
- Use `eur_per_cny: 0.122` (clear: EUR amount per 1 CNY)
- OR `cny_per_eur: 7.8` (clear: CNY amount per 1 EUR)
- NEVER use ambiguous "cny_to_eur"

### Issue 4: Missing Unit Tests

**Severity:** Major
**Location:** `html_generator.py` (no test file)

**Problem:**
No unit tests for `convertCurrencyBash()` with different rate formats.
Bug would have been caught by testing both rate > 1 and rate < 1.

**Recommendation:**
Add test cases:
```python
# test_html_generator.py
def test_convert_currency_eur_to_cny_rate():
    """Test with EUR→CNY rate (e.g., 7.8)"""
    assert convertCurrencyBash(19162, 7.8) == "2456.67"

def test_convert_currency_cny_to_eur_rate():
    """Test with CNY→EUR rate (e.g., 0.122) - should invert or throw error"""
    # After fix, this should either:
    # 1. Automatically invert: convertCurrencyBash(19162, 0.122) == "2337.76"
    # 2. Or raise ValueError for ambiguous rate
    pass
```

---

## Verification Results

### ✓ Passed Checks
1. Daily budget sum calculation: 19,162 CNY ✓
2. Exchange rate API call: Returns 0.122 ✓
3. Currency config injection: Correctly adds exchange_rate to HTML ✓
4. JavaScript budget sum: Correctly totals PLAN_DATA.days ✓

### ✗ Failed Checks
1. Total budget EUR amount: €157,065.57 instead of €2,337.76 ✗
2. Currency conversion formula: Uses division for rate < 1 ✗
3. Exchange rate validation: No validation of rate semantics ✗

---

## Recommended Fix (Immediate)

**File:** `/root/travel-planner/scripts/lib/html_generator.py`

```python
# Line 140-160: Update _fetch_exchange_rate method
def _fetch_exchange_rate(self, source_currency: str, display_currency: str) -> float:
    # ... existing validation code ...

    try:
        print(f"Fetching exchange rate: {source_currency} → {display_currency}...", file=sys.stderr)
        result = subprocess.run(
            [str(fetch_script), source_currency, display_currency],
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )
        api_rate = float(result.stdout.strip())

        # NEW: Invert rate to match formula expectations
        # API returns: 1 BASE = X TARGET (e.g., 1 CNY = 0.122 EUR)
        # Formula expects: 1 TARGET = X BASE (e.g., 1 EUR = 7.8 CNY)
        # So we invert: 1 / 0.122 = 8.2
        if api_rate <= 0:
            raise ValueError(f"Invalid exchange rate: {api_rate}")

        exchange_rate = 1.0 / api_rate

        # Validation: For CNY→EUR, rate should be > 1 after inversion
        if source_currency == 'CNY' and display_currency in ['EUR', 'USD', 'GBP']:
            if exchange_rate < 1:
                raise ValueError(
                    f"Exchange rate validation failed. Got {exchange_rate} but expected > 1 "
                    f"for {display_currency}→{source_currency} conversion"
                )

        print(f"Exchange rate: 1 {display_currency} = {exchange_rate:.4f} {source_currency}", file=sys.stderr)
        return exchange_rate

    except subprocess.CalledProcessError as e:
        # ... existing error handling ...
```

**Update HTML template comments (line 2470):**
```javascript
// Converts CNY to display currency using EUR→CNY rate
// exchange_rate format: 1 EUR = X CNY (e.g., 8.2)
// Formula: CNY_amount ÷ rate = EUR_amount
// Example: 19,162 CNY ÷ 8.2 = €2,337.56
function convertCurrencyBash(amount) {
  if (!amount || isNaN(amount)) return '0.00';
  return (amount / CURRENCY_CONFIG_BASH.exchange_rate).toFixed(2);
}
```

---

## Test Plan

After implementing fix:

1. **Manual verification:**
   ```bash
   # Generate new HTML
   ./scripts/generate-html.sh beijing-exchange-bucket-list-20260202-232405

   # Check displayed total
   # Should be €2,337 - €2,457 (depending on current exchange rate)
   # NOT €157,000+
   ```

2. **Automated test:**
   ```bash
   # Test exchange rate fetch and inversion
   python3 -c "
   from scripts.lib.html_generator import TravelPlanHTMLGenerator
   gen = TravelPlanHTMLGenerator('data/beijing-exchange-bucket-list-20260202-232405')
   rate = gen._fetch_exchange_rate('CNY', 'EUR')
   assert rate > 1, f'Expected EUR→CNY rate > 1, got {rate}'
   assert 7.0 < rate < 9.0, f'Rate {rate} outside expected range 7-9 for EUR→CNY'
   print(f'✓ Exchange rate validation passed: {rate}')
   "
   ```

3. **Regression test:**
   ```bash
   # Ensure budget.json calculations still work
   # v15 file uses hardcoded 7.8, should still show €2,456.67
   node -e "
   const fs = require('fs');
   const html = fs.readFileSync('travel-plan-beijing-exchange-bucket-list-20260202-232405-v15.html', 'utf8');
   const match = html.match(/const PLAN_DATA = ({[\\s\\S]*?});[\\s\\n]*const PROJECT_TYPE/);
   const data = JSON.parse(match[1]);
   const total = data.days.reduce((s, d) => s + (d.budget?.total || 0), 0);
   const rate = data.currency_config.exchange_rate;
   const eur = (total / rate).toFixed(2);
   console.log(\`Total: ${total} CNY ÷ ${rate} = €\${eur}\`);
   if (Math.abs(parseFloat(eur) - 2456.67) > 0.01) throw new Error('v15 regression!');
   console.log('✓ v15 still displays correctly');
   "
   ```

---

## Release Recommendation

**REJECT** - 2 critical issues block release:
1. Total budget displays 6,619% higher than actual (unusable)
2. No validation prevents silent failures with incorrect exchange rates

**Required before approval:**
- Implement exchange rate inversion in `html_generator.py`
- Add exchange rate validation (range check for rate > 1 when CNY→EUR)
- Add unit tests for currency conversion with both rate formats
- Regenerate HTML file with corrected exchange rate
- Verify displayed total is €2,300-€2,500 range

---

## Files Analyzed

- `/root/travel-planner/travel-plan-beijing-exchange-bucket-list-20260202-232405.html` (buggy)
- `/root/travel-planner/travel-plan-beijing-exchange-bucket-list-20260202-232405-v15.html` (working)
- `/root/travel-planner/data/beijing-exchange-bucket-list-20260202-232405/budget.json`
- `/root/travel-planner/scripts/lib/html_generator.py`
- `/root/travel-planner/scripts/utils/fetch-exchange-rate.sh`
- `~/.cache/travel-planner/exchange-rates-CNY-EUR.json`

---

## Additional Context

The v15 HTML file (created Feb 4, 14:14) displays correctly (€2,456.67) because it uses hardcoded `exchange_rate: 7.8`. The latest HTML file (created Feb 4, 18:32) uses live API rate (0.122) and displays incorrectly (€157,065.57).

This confirms the bug is in exchange rate handling when API integration is active, not in the budget calculation logic itself.
