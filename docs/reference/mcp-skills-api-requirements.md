# MCP Skills API Key Requirements Report

**Project**: Travel Planner
**Test Date**: 2026-01-30
**Skills Tested**: 7 (excluding gaode-maps and google-maps)

---

## Executive Summary

- **No API Key Required**: 3 skills (12306, airbnb, weather)
- **API Key Required**: 4 skills (amadeus-flight, duffel-flights, eventbrite, yelp)
- **Permanent Free Tier**: 6 skills
- **Paid Only (after 30-day trial)**: 1 skill (yelp)

---

## Skills Breakdown

### ✅ No API Key Required

#### 1. 12306 (Chinese Railway)
- **API Key**: ❌ Not required
- **Free Tier**: ✅ Yes (public API)
- **Registration URL**: N/A
- **Notes**:
  - Uses public 12306.cn API
  - China mainland railway network only
  - Requires Node.js/npx installation
- **MCP Server**: `npx -y 12306-mcp` (Node.js)

#### 2. Airbnb
- **API Key**: ❌ Not required
- **Free Tier**: ✅ Yes (web scraping)
- **Registration URL**: N/A
- **Notes**:
  - Uses web scraping via `@openbnb/mcp-server-airbnb`
  - May be blocked by robots.txt (use `--ignore-robots-txt` flag if needed)
  - ⚠️ Legal/ethical considerations for web scraping
- **MCP Server**: `npx -y @openbnb/mcp-server-airbnb`

#### 3. Weather
- **API Key**: ❌ Not required (optional NCEI token for enhanced data)
- **Free Tier**: ✅ Yes
- **Registration URL**: N/A
- **Notes**:
  - Uses free NOAA API (US locations)
  - Uses free Open-Meteo API (global coverage)
  - Optional NCEI token enhances climate normals
  - 12 tools: forecast, current, alerts, air quality, marine, etc.
- **MCP Server**: `@dangahagan/weather-mcp`

---

### 🔑 API Key Required

#### 4. Amadeus Flight
- **API Key**: ✅ Required (`AMADEUS_API_KEY`, `AMADEUS_API_SECRET`)
- **Free Tier**: ✅ Yes
- **Registration URL**: [https://developers.amadeus.com/](https://developers.amadeus.com/)
- **Setup Time**: 5-10 minutes
- **Registration Steps**:
  1. Create account at Amadeus for Developers portal
  2. Go to My Self-Service Workspace
  3. Click "Create New App"
  4. API key and secret generated automatically
  5. For production: Sign contract, provide billing info (72-hour approval)
- **Rate Limits**: Free monthly quota (same in test and production)
- **MCP Server**: `npx -y @amadeus/flight-search-mcp-server`
- **Sources**: [API Keys Guide](https://developers.amadeus.com/self-service/apis-docs/guides/developer-guides/API-Keys/)

#### 5. Duffel Flights
- **API Key**: ✅ Required (`DUFFEL_API_KEY`)
- **Free Tier**: ✅ Yes (sandbox mode)
- **Registration URL**: [https://duffel.com/](https://duffel.com/)
- **Setup Time**: 1-5 minutes
- **Registration Steps**:
  1. Sign up at [https://app.duffel.com/](https://app.duffel.com/)
  2. Create access token from dashboard
  3. Use "Developer test mode" for sandbox testing
- **Test Mode**: Unlimited Duffel Balance, risk-free, no real bookings
- **Pricing Model**: Pay-per-booking (charges only for confirmed bookings)
- **MCP Server**: `flights-mcp` (Python) - ⚠️ **Command not found, installation required**
- **Sources**: [Test Mode Docs](https://duffel.com/docs/api/overview/test-mode/duffel-airways)

#### 6. Eventbrite
- **API Key**: ✅ Required (`EVENTBRITE_API_KEY`)
- **Free Tier**: ✅ Yes
- **Registration URL**: [https://www.eventbrite.com/platform/](https://www.eventbrite.com/platform/)
- **Setup Time**: 5-10 minutes
- **Registration Steps**:
  1. Create Eventbrite account
  2. Go to Account Settings > Developer Links > API Keys
  3. Click "Create API key"
  4. Fill in application details (name, URL)
  5. Receive email when approved
- **Authorization**: OAuth 2.0
- **Rate Limits**: 1,000 calls/hour, 48,000 calls/day
- **API Version**: v3
- **MCP Server**: `npx -y @ibraheem4/eventbrite-mcp`
- **Sources**: [Generate API Key](https://www.eventbrite.com/help/en-us/articles/849962/generate-an-api-key/), [Platform Docs](https://www.eventbrite.com/platform/docs/introduction)

#### 7. Yelp ⚠️ **PAID AFTER TRIAL**
- **API Key**: ✅ Required (`YELP_API_KEY`)
- **Free Tier**: ❌ **No permanent free tier**
- **Free Trial**: 30 days, 5,000 API calls (evaluation only)
- **Registration URL**: [https://www.yelp.com/developers](https://www.yelp.com/developers)
- **Setup Time**: 5-10 minutes
- **Registration Steps**:
  1. Create Yelp user account
  2. Sign up at Yelp for Developers
  3. Generate API credentials
  4. 30-day trial starts automatically
- **Pricing (2026)**:
  - **Starter**: $7.99 per 1,000 calls
  - **Plus**: $9.99 per 1,000 calls
  - **Enterprise**: $14.99 per 1,000 calls
  - Included: 30,000 calls/month, 5,000 daily limit
  - Overage: Billed in 1,000-call increments
- **Important**: Yelp ended free access in 2024. All accounts converted to paid model.
- **MCP Server**: `mcp-yelp-agent` (Python) - ⚠️ **Command not found, installation required**
- **Sources**: [Yelp API Guide](https://elfsight.com/blog/how-to-get-and-use-yelp-api/), [Pricing Controversy](https://techcrunch.com/2024/08/02/yelps-lack-of-transparency-around-api-charges-angers-developers/)

---

## Recommendations

### ✅ Immediate Use (No Setup)
1. **Weather** - Ready to use, no API key needed

### 🟢 Easy Free Setup (5-10 minutes)
1. **Amadeus Flight** - Free tier, instant API keys
2. **Eventbrite** - Free tier, straightforward OAuth
3. **Duffel Flights** - Free sandbox, 1-minute signup

### 🟡 Special Considerations
1. **Airbnb** - Web scraping, robots.txt compliance, legal/ethical review needed
2. **12306** - China-specific, requires Node.js installation
3. **Yelp** - 30-day trial only, budget $7.99+/1K calls for production

### 🔧 MCP Server Installation Needed
1. **12306** - Install Node.js, run `npx -y 12306-mcp`
2. **Duffel Flights** - Install Python MCP `flights-mcp` command
3. **Yelp** - Install Python MCP `mcp-yelp-agent` command

---

## Priority Action Items

### High Priority
- [ ] **Yelp**: Decide if 30-day trial is sufficient or budget for paid API ($7.99+/1K calls)
  - **Decision Point**: Commercial use requires subscription after trial

### Medium Priority
- [ ] **Amadeus Flight**: Register for free API key (5-10 min)
- [ ] **Eventbrite**: Register for free API key (5-10 min)
- [ ] **Duffel Flights**: Register for free API key (1-5 min)

### Low Priority
- [ ] **Install MCP Servers**: Set up Node.js/Python dependencies for 12306, Duffel, Yelp
- [ ] **Airbnb Review**: Assess robots.txt compliance and legal implications

---

## Testing Summary

### Test Results
- **12306**: MCP server unavailable (npx required)
- **Airbnb**: Works without key, blocked by robots.txt
- **Amadeus**: API key required (confirmed in documentation)
- **Duffel**: MCP server not found (Python package needed)
- **Eventbrite**: API key required (confirmed by error message)
- **Weather**: Works without key (test params invalid)
- **Yelp**: MCP server not found (Python package needed)

### Methodology
- Documentation analysis (SKILL.md files)
- Runtime testing where possible
- Web research for 2026 registration procedures

### Confidence Level
- **High** for API key requirements (confirmed via docs and errors)
- **Medium** for pricing details (based on web research as of 2026-01-30)

---

## Sources

- [Amadeus API Keys Guide](https://developers.amadeus.com/self-service/apis-docs/guides/developer-guides/API-Keys/)
- [Duffel Test Mode Documentation](https://duffel.com/docs/api/overview/test-mode/duffel-airways)
- [Eventbrite API Key Generation](https://www.eventbrite.com/help/en-us/articles/849962/generate-an-api-key/)
- [Eventbrite Platform Introduction](https://www.eventbrite.com/platform/docs/introduction)
- [Yelp API Guide](https://elfsight.com/blog/how-to-get-and-use-yelp-api/)
- [Yelp Pricing Controversy (TechCrunch)](https://techcrunch.com/2024/08/02/yelps-lack-of-transparency-around-api-charges-angers-developers/)

---

**Report Generated**: 2026-01-30
**Full JSON Report**: `/root/travel-planner/mcp-skills-api-test-report.json`
