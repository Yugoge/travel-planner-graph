#!/usr/bin/env bash
# Description: Fetch real-time exchange rate between two currencies with cache fallback
# Usage: fetch-exchange-rate.sh <base_currency> <target_currency>
# Exit codes: 0=success, 1=failure, 2=invalid input
#
# API: exchangerate-api.com (free tier, 1500 requests/month, no key required)
# Endpoint: https://api.exchangerate-api.com/v4/latest/{BASE_CURRENCY}
# Cache: ~/.cache/travel-planner/exchange-rates-{BASE}-{TARGET}.json (24h TTL)
# Root cause fix: commit 3d5971b added API without cache fallback strategy

set -euo pipefail

# Parameters
BASE_CURRENCY="${1:?Missing required base_currency (e.g., CNY, USD, GBP)}"
TARGET_CURRENCY="${2:?Missing required target_currency (e.g., EUR, USD, GBP)}"

# Validation: Currency codes should be 3 uppercase letters
if ! [[ "$BASE_CURRENCY" =~ ^[A-Z]{3}$ ]]; then
  echo "Error: Invalid base currency code: $BASE_CURRENCY (must be 3 uppercase letters, e.g., CNY)" >&2
  exit 2
fi

if ! [[ "$TARGET_CURRENCY" =~ ^[A-Z]{3}$ ]]; then
  echo "Error: Invalid target currency code: $TARGET_CURRENCY (must be 3 uppercase letters, e.g., EUR)" >&2
  exit 2
fi

# Cache configuration
CACHE_DIR="${HOME}/.cache/travel-planner"
CACHE_FILE="${CACHE_DIR}/exchange-rates-${BASE_CURRENCY}-${TARGET_CURRENCY}.json"
CACHE_TTL_SECONDS=$((24 * 60 * 60))  # 24 hours

# Create cache directory if not exists
mkdir -p "$CACHE_DIR"

# Function to check if cache is fresh (< 24h old)
is_cache_fresh() {
  if [[ ! -f "$CACHE_FILE" ]]; then
    return 1
  fi

  local cache_timestamp
  cache_timestamp=$(jq -r '.timestamp' "$CACHE_FILE" 2>/dev/null || echo "")

  if [[ -z "$cache_timestamp" ]]; then
    return 1
  fi

  local cache_epoch
  cache_epoch=$(date -d "$cache_timestamp" +%s 2>/dev/null || echo "0")
  local now_epoch
  now_epoch=$(date +%s)
  local age_seconds=$((now_epoch - cache_epoch))

  if [[ $age_seconds -lt $CACHE_TTL_SECONDS ]]; then
    return 0
  else
    return 1
  fi
}

# Function to read rate from cache
read_cache() {
  jq -r '.rate' "$CACHE_FILE" 2>/dev/null || echo ""
}

# Function to write rate to cache
write_cache() {
  local rate="$1"
  local timestamp
  timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

  cat > "$CACHE_FILE" <<EOF
{
  "rate": $rate,
  "timestamp": "$timestamp",
  "base": "$BASE_CURRENCY",
  "target": "$TARGET_CURRENCY"
}
EOF
}

# API endpoint
API_URL="https://api.exchangerate-api.com/v4/latest/${BASE_CURRENCY}"

# Step 1: Try API call
RESPONSE=$(curl -s -m 5 "$API_URL" 2>&1) && API_SUCCESS=true || API_SUCCESS=false

if [[ "$API_SUCCESS" == "true" ]]; then
  # Validate response is valid JSON
  if echo "$RESPONSE" | jq empty 2>/dev/null; then
    # Check if API returned error
    if ! echo "$RESPONSE" | jq -e '.error' >/dev/null 2>&1; then
      # Extract exchange rate for target currency
      RATE=$(echo "$RESPONSE" | jq -r ".rates.${TARGET_CURRENCY}" 2>/dev/null || echo "null")

      # Validate rate is a number
      if [[ "$RATE" != "null" ]] && [[ "$RATE" =~ ^[0-9]+\.?[0-9]*$ ]]; then
        # Success! Write to cache and output
        write_cache "$RATE"
        echo "$RATE"
        exit 0
      fi
    fi
  fi
fi

# Step 2: API failed, check cache
if is_cache_fresh; then
  CACHED_RATE=$(read_cache)
  if [[ -n "$CACHED_RATE" ]] && [[ "$CACHED_RATE" =~ ^[0-9]+\.?[0-9]*$ ]]; then
    echo "Warning: Using cached exchange rate (API unavailable)" >&2
    echo "$CACHED_RATE"
    exit 0
  fi
fi

# Step 3: No fresh cache, check if stale cache exists
if [[ -f "$CACHE_FILE" ]]; then
  CACHED_RATE=$(read_cache)
  if [[ -n "$CACHED_RATE" ]] && [[ "$CACHED_RATE" =~ ^[0-9]+\.?[0-9]*$ ]]; then
    echo "Warning: Using stale cached exchange rate (API unavailable, cache >24h old)" >&2
    echo "$CACHED_RATE"
    exit 0
  fi
fi

# Step 4: Fallback to hardcoded default only if no cache and no network
echo "Error: Failed to fetch exchange rate from API and no cache available, using fallback rate 7.8" >&2
echo "7.8"
exit 1
