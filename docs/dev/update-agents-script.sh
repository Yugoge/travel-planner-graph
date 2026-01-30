#!/bin/bash
# Script to remove WebSearch fallback and add script execution instructions to all agents

AGENTS_DIR="/root/travel-planner/.claude/agents"

# Update meals.md
sed -i 's|Fallback: If MCP unavailable, use WebSearch|No WebSearch fallback - report errors if scripts fail|g' "$AGENTS_DIR/meals.md"
sed -i 's|If Yelp unavailable, fall back to WebSearch|If Yelp unavailable, report error to user|g' "$AGENTS_DIR/meals.md"
sed -i 's|fall back to Yelp or WebSearch|report error to user|g' "$AGENTS_DIR/meals.md"
sed -i 's|fall back to Google Maps or WebSearch|report error to user|g' "$AGENTS_DIR/meals.md"

# Update accommodation.md
sed -i 's|\*\*Fallback\*\*: Use WebSearch if MCP unavailable or API errors occur.|**No WebSearch fallback** - report errors if scripts fail.|g' "$AGENTS_DIR/accommodation.md"
sed -i 's|\*\*Fallback\*\*: Use WebSearch "airbnb \[location\] \[dates\]" if MCP unavailable.|**No WebSearch fallback** - report errors if scripts fail.|g' "$AGENTS_DIR/accommodation.md"
sed -i 's|\*\*Fallback\*\*: Use Google Maps or WebSearch if Gaode unavailable|**No WebSearch fallback** - report errors if scripts fail|g' "$AGENTS_DIR/accommodation.md"

# Update attractions.md
sed -i 's|\*\*Fallback Method: WebSearch\*\* (if TripAdvisor unavailable)|**No WebSearch fallback** - report errors if TripAdvisor scripts fail|g' "$AGENTS_DIR/attractions.md"
sed -i 's|indicate if from TripAdvisor or WebSearch|indicate data source: tripadvisor|g' "$AGENTS_DIR/attractions.md"
sed -i 's|fall back to WebSearch|report error to user|g' "$AGENTS_DIR/attractions.md"
sed -i 's|fall back to TripAdvisor or WebSearch|report error to user|g' "$AGENTS_DIR/attractions.md"
sed -i 's|Fallback: Use Google Maps or WebSearch if Gaode unavailable|No WebSearch fallback - report errors if scripts fail|g' "$AGENTS_DIR/attractions.md"

# Update entertainment.md
sed -i 's|\*\*Fallback Method: WebSearch\*\* (if TripAdvisor unavailable)|**No WebSearch fallback** - report errors if TripAdvisor scripts fail|g' "$AGENTS_DIR/entertainment.md"
sed -i 's|indicate if from TripAdvisor or WebSearch|indicate data source: tripadvisor|g' "$AGENTS_DIR/entertainment.md"
sed -i 's|fall back to WebSearch|report error to user|g' "$AGENTS_DIR/entertainment.md"
sed -i 's|fall back to TripAdvisor or WebSearch|report error to user|g' "$AGENTS_DIR/entertainment.md"
sed -i 's|Fallback: Use Google Maps or WebSearch|No WebSearch fallback - report errors if scripts fail|g' "$AGENTS_DIR/entertainment.md"

# Update shopping.md
sed -i 's|\*\*Fallback\*\*: Use WebSearch for detailed information|**No WebSearch fallback** - report errors if scripts fail|g' "$AGENTS_DIR/shopping.md"
sed -i 's|fall back to WebSearch|report error to user|g' "$AGENTS_DIR/shopping.md"
sed -i 's|Fallback: Use Google Maps or WebSearch|No WebSearch fallback - report errors if scripts fail|g' "$AGENTS_DIR/shopping.md"

echo "All agents updated - WebSearch fallback removed"
