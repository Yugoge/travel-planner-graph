#!/usr/bin/env bash
# Description: Fetch real-time exchange rate between two currencies
# Usage: fetch-exchange-rate.sh <base_currency> <target_currency>
# Exit codes: 0=success, 1=failure, 2=invalid input
#
# API: exchangerate-api.com (free tier, 1500 requests/month, no key required)
# Endpoint: https://api.exchangerate-api.com/v4/latest/{BASE_CURRENCY}

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

# API endpoint
API_URL="https://api.exchangerate-api.com/v4/latest/${BASE_CURRENCY}"

# Fetch exchange rate with timeout
RESPONSE=$(curl -s -m 5 "$API_URL" 2>&1) || {
  echo "Error: Failed to fetch exchange rate from API (network issue or timeout)" >&2
  exit 1
}

# Validate response is valid JSON
if ! echo "$RESPONSE" | jq empty 2>/dev/null; then
  echo "Error: Invalid JSON response from API" >&2
  exit 1
fi

# Check if API returned error
if echo "$RESPONSE" | jq -e '.error' >/dev/null 2>&1; then
  ERROR_MSG=$(echo "$RESPONSE" | jq -r '.error')
  echo "Error: API returned error: $ERROR_MSG" >&2
  exit 1
fi

# Extract exchange rate for target currency
RATE=$(echo "$RESPONSE" | jq -r ".rates.${TARGET_CURRENCY}") || {
  echo "Error: Failed to extract exchange rate from response" >&2
  exit 1
}

# Validate rate is a number
if [[ "$RATE" == "null" ]] || ! [[ "$RATE" =~ ^[0-9]+\.?[0-9]*$ ]]; then
  echo "Error: Invalid exchange rate returned: $RATE" >&2
  exit 1
fi

# Output the exchange rate (clean output for piping)
echo "$RATE"
exit 0
