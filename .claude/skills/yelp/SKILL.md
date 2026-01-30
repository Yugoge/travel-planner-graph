---
name: yelp
description: Intelligent Yelp business agent for restaurant and business discovery with conversational AI
allowed-tools: [Bash]
model: inherit
user-invocable: true
---

# Yelp Skill

Conversational AI agent for discovering and interacting with local businesses via Yelp's comprehensive platform. Handles natural language queries with context-aware responses.

**MCP Server**: `yelp-mcp` (Official Yelp Python MCP)
**API Coverage**: 1/1 tools (100%)
**API Key**: Requires `YELP_API_KEY` environment variable
**Coverage**: Global businesses with focus on North America

## Available Tools

1. **yelp_agent** - Intelligent conversational agent for any business-related query

## How to Use

Execute script from skill directory:
```bash
cd /root/travel-planner/.claude/skills/yelp
python3 scripts/yelp_agent.py <query> [options]
```

**Requires**: `YELP_API_KEY` environment variable must be set.

## Script

### Yelp Agent (yelp_agent.py)

Conversational AI agent that handles any natural language query about local businesses.

```bash
# Basic restaurant search
python3 scripts/yelp_agent.py "Find Italian restaurants in San Francisco"

# With precise location
python3 scripts/yelp_agent.py "Best coffee shops nearby" --lat 37.7749 --lon -122.4194

# Follow-up question (use chat_id from previous response)
python3 scripts/yelp_agent.py "What are their hours?" --chat-id abc123def456

# Complex planning
python3 scripts/yelp_agent.py "Plan a progressive dinner in Mission District"

# Service search
python3 scripts/yelp_agent.py "Find emergency plumbers in Boston"

# Comparison request
python3 scripts/yelp_agent.py "Compare auto repair shops from budget to luxury in Sacramento"

# Restaurant booking
python3 scripts/yelp_agent.py "Book table for 2 at Mama Nachas tonight at 7pm"
```

**Parameters**:
- `query`: Natural language query about businesses (required)
- `--lat`, `--latitude`: Search latitude for precise location
- `--lon`, `--longitude`: Search longitude for precise location
- `--chat-id`: Previous chat ID for conversational follow-ups

**Returns**:
- Natural language response
- Structured business data:
  - Business names and Yelp URLs
  - Ratings and review counts
  - Addresses and phone numbers
  - Hours of operation
  - Price levels
  - Categories
  - Special features
- `chat_id` for follow-up questions

## Capabilities

The Yelp agent can handle diverse queries:

### Search & Discovery
- "Find vegan restaurants in downtown Seattle"
- "Best brunch spots near Golden Gate Park"
- "Late-night food options in Manhattan"
- "Pet-friendly cafes in Austin"

### Business Details
- "Tell me about The French Laundry"
- "What do reviews say about their service?"
- "Is parking available?"
- "Do they accept reservations?"

### Comparisons
- "Compare pizza places in Brooklyn"
- "Best value vs luxury sushi in LA"
- "Family-friendly vs romantic restaurants"

### Planning
- "Plan a food tour in Portland"
- "Create a date night itinerary in Miami"
- "Progressive dinner in San Francisco"

### Services
- "Emergency dentist near me"
- "Highly rated mechanics in Denver"
- "Wedding venues in Napa Valley"

### Reservations
- "Book table for 4 at Zuni Cafe tomorrow at 7pm"
- "Reserve dinner for tonight"

(Note: Bookings work only with Yelp Reservations partner restaurants)

## Conversational Context

Use `chat_id` for multi-turn conversations:

```bash
# Initial query
python3 scripts/yelp_agent.py "Find Thai restaurants in Chicago" > result1.json

# Extract chat_id from result1.json
CHAT_ID=$(jq -r '.chat_id' result1.json)

# Follow-up questions
python3 scripts/yelp_agent.py "Which one has the best pad thai?" --chat-id $CHAT_ID
python3 scripts/yelp_agent.py "What are their hours?" --chat-id $CHAT_ID
python3 scripts/yelp_agent.py "How much should I budget?" --chat-id $CHAT_ID
```

## Output Format

JSON structure:
```json
{
  "response": "Here are the top Italian restaurants in San Francisco...",
  "businesses": [
    {
      "name": "Tony's Pizza Napoletana",
      "url": "https://www.yelp.com/biz/...",
      "rating": 4.5,
      "review_count": 3421,
      "price": "$$",
      "categories": ["Italian", "Pizza"],
      "location": {
        "address": "1570 Stockton St",
        "city": "San Francisco",
        "zip_code": "94133"
      },
      "phone": "+1-415-835-9888",
      "is_closed": false
    }
  ],
  "chat_id": "abc123def456"
}
```

**CRITICAL**: Always include Yelp URLs from the response when recommending businesses. Users need direct links to view details on Yelp.

## API Key Setup

```bash
# Set environment variable
export YELP_API_KEY="your_api_key_here"

# Or add to .env file
echo "YELP_API_KEY=your_api_key_here" >> .env
```

Get API key from: https://www.yelp.com/developers

## Use Cases

### Restaurant Discovery
```bash
python3 scripts/yelp_agent.py "Romantic restaurants with outdoor seating in Napa"
```

### Trip Planning
```bash
python3 scripts/yelp_agent.py "Must-visit food spots in New Orleans for first-time visitors"
```

### Service Needs
```bash
python3 scripts/yelp_agent.py "Trusted car mechanics with good reviews in my area" --lat 34.0522 --lon -118.2437
```

### Event Planning
```bash
python3 scripts/yelp_agent.py "Catering options for 50 people in downtown Portland"
```

### Quick Decisions
```bash
python3 scripts/yelp_agent.py "Where should I eat dinner right now in Brooklyn?"
```

## Common Query Patterns

### Location-Based
- "Near [location]"
- "In [neighborhood]"
- "Close to [landmark]"

### Feature-Based
- "With outdoor seating"
- "Pet-friendly"
- "Good for groups"
- "Takes reservations"
- "Late-night"

### Quality Indicators
- "Best rated"
- "Top reviews"
- "Highly recommended"
- "Hidden gems"

### Price-Based
- "Budget-friendly"
- "Under $20 per person"
- "Fine dining"
- "Cheap eats"

### Cuisine/Category
- Specific cuisines (Italian, Thai, Japanese, etc.)
- Services (plumbers, mechanics, dentists)
- Businesses (hotels, gyms, salons)

## Error Handling

Scripts return:
- **Exit 0**: Success
- **Exit 1**: API error, missing key, or network failure

Common issues:
- **Missing API key**: Set `YELP_API_KEY`
- **No results**: Try broader location or different query
- **Invalid chat_id**: Use valid ID from previous response

## Technical Notes

- **MCP Type**: Python based (official Yelp MCP)
- **Server Command**: `mcp-yelp-agent`
- **Protocol**: JSON-RPC 2.0 over stdio
- **Data Source**: Yelp Fusion AI API
- **AI Agent**: Conversational context-aware responses
- **Language**: Natural language queries
- **Rate Limiting**: Subject to Yelp API limits

## Advantages Over Traditional Search

1. **Natural Language**: No need to learn query syntax
2. **Conversational**: Ask follow-up questions with context
3. **Intelligent**: Agent understands intent and nuance
4. **Comprehensive**: Combines search, details, and recommendations
5. **Planning**: Can create itineraries and compare options

## Tool Name Verification

Tool name verified against actual MCP server source code:
- Single tool `yelp_agent` matches source code
- Parameter names match API expectations
- No assumed tool names
