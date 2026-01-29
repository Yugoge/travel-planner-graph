---
description: "Interactive travel planning with research and HTML itinerary generation"
allowed-tools: Task, Read, Write, TodoWrite, WebSearch, Skill
argument-hint: "[destination]"
model: inherit
---

**⚠️ CRITICAL**: Use TodoWrite to track workflow phases. Mark in_progress before each phase, completed immediately after.

# Plan Command

Interactive travel planning with automatic web research and comprehensive HTML itinerary generation using Three-Party Architecture.

## Step 0: Initialize Workflow Checklist

**Load todos from**: `scripts/todo/plan.py`

Execute via venv:
```bash
source /root/.claude/venv/bin/activate && python /root/travel-planner/scripts/todo/plan.py
```

Use output to create TodoWrite with all workflow steps.

**Rules**: Mark `in_progress` before each step, `completed` after. NEVER skip steps.

---

## Usage

```
/plan [destination]
```

## Examples

```
/plan Paris
/plan Japan in spring
/plan
```

## What This Command Does

1. **Parses destination hint** from arguments (optional)
2. **Conducts BA-style interview** to gather comprehensive travel requirements
3. **Consults research subagent** (backend JSON consultant - web research for destinations)
4. **Consults HTML subagent** (backend HTML generator - creates professional itinerary)
5. **Delivers complete travel plan** as interactive HTML file
6. **Multi-turn refinement** if user wants to adjust the plan

## Implementation

### Step 1: Parse Destination Hint

Extract the destination hint from `$ARGUMENTS`:

```
Destination hint: "$ARGUMENTS" (or empty)
```

**Handle edge cases**:
- If `$ARGUMENTS` is empty → Start interview with destination question first
- If `$ARGUMENTS` contains destination → Start interview acknowledging the destination
- Otherwise → Proceed to Step 2

**Initial Response Pattern**:

If destination provided:
```
I'll help you plan an amazing trip to {destination}! Let me gather some details to create a personalized travel plan for you.
```

If no destination:
```
I'll help you plan an amazing trip! Let me gather some details to create a personalized travel plan for you.
```

Proceed immediately to Step 2.

### Step 2: Conduct BA-Style Requirement Interview

**Your Role**: You are a professional travel consultant conducting a requirements interview. Ask questions naturally and collect comprehensive information.

**Architecture**: This command uses the Three-Party Architecture pattern:
- You (main agent) orchestrate the conversation and are THE TRAVEL CONSULTANT visible to user
- Research subagent provides JSON consultation via Task tool (backend responses only)
- HTML subagent generates travel plan HTML via Task tool (backend responses only)
- User sees natural dialogue only (no "I'm consulting..." meta-commentary)

**Interview Questions** (ask naturally, not as a form):

1. **Destination(s)** (if not already provided):
   - "Where would you like to go?"
   - "Any specific cities or regions in mind?"
   - "Open to suggestions or have a specific place?"

2. **Travel Dates**:
   - "When are you planning to travel?"
   - "How long is the trip? (number of days)"
   - "Any specific dates or flexible?"

3. **Travelers**:
   - "Who will be traveling?"
   - "Solo trip, couple, family, or group?"
   - "Any children? (ages if relevant)"

4. **Budget**:
   - "What's your budget range?"
   - "Total or per person?"
   - "Which currency?"

5. **Accommodation Preferences**:
   - "What type of accommodation do you prefer?"
   - "Budget hotels, mid-range, luxury, or boutique?"
   - "Any specific location preferences (city center, beach, quiet area)?"

6. **Activity Interests**:
   - "What are you most interested in?"
   - "Culture/history, adventure, relaxation, food, nightlife, nature?"
   - "Any must-see attractions or experiences?"

7. **Special Requirements**:
   - "Any dietary restrictions or allergies?"
   - "Accessibility needs?"
   - "Other special requirements?"

8. **Transportation**:
   - "How will you get there?"
   - "Flying, train, car rental once there?"
   - "Need airport transfer suggestions?"

**Dialogue Style**:
- Ask 2-3 questions at a time (don't overwhelm)
- Be conversational and friendly
- Adapt based on user responses
- If user provides comprehensive info upfront, acknowledge and fill gaps
- Confirm understanding before proceeding to research

**Completion Criteria**:
- Destination(s) confirmed
- Dates and duration confirmed
- Number of travelers confirmed
- Budget range confirmed
- At least 2-3 preference areas clarified

When you have enough information, confirm with user:
```
Perfect! Let me confirm what I've gathered:

- **Destination**: {destination}
- **Dates**: {dates} ({duration} days)
- **Travelers**: {number and type}
- **Budget**: {budget}
- **Interests**: {interests}
- **Accommodation**: {preferences}

Is this correct? Any adjustments before I start researching?
```

Wait for user confirmation. If confirmed, proceed to Step 3. If adjustments needed, collect them and re-confirm.

### Step 3: Initial Research Consultation (JSON)

**Consult research subagent for comprehensive travel information**.

After user confirms requirements, transition naturally:
```
Excellent! Give me a few moments to research the best options for your trip.
```

Then execute research consultation (user doesn't see this process):

```
Use Task tool with:
- subagent_type: "research-travel"
- description: "Research travel information and create comprehensive destination data"
- model: "sonnet"  # Use capable model for quality research
- prompt: "
  ⚠️ CRITICAL OUTPUT INSTRUCTIONS:

  1. Save your research JSON to: /root/travel-planner/data/{destination-slug}/research.json
  2. After saving the file, return ONLY the word: complete
  3. Do NOT return the JSON content in your response

  Where {destination-slug} is the destination in lowercase with hyphens (e.g., 'paris', 'new-york', 'chongqing-bazhong-chengdu-shanghai-beijing')

  You are a CONSULTANT to the main /plan agent, NOT the user's travel planner.
  The user will NEVER see your response - only the main agent will read your JSON file.

  Your task: Research comprehensive travel information for this trip and save structured data as JSON file.

  **User Requirements**:
  - Destination(s): {destination}
  - Dates: {dates} ({duration} days)
  - Travelers: {travelers}
  - Budget: {budget}
  - Interests: {interests}
  - Accommodation preferences: {accommodation}
  - Special requirements: {special_requirements}

  ---

  **RESEARCH INSTRUCTIONS**:

  ⚠️ **CRITICAL - WebFetch is DISABLED**: Never use WebFetch (disabled to prevent timeouts).

  **ADVANCED SEARCH CAPABILITIES**:

  1. **SlashCommand Tool** (for comprehensive research):
     - Use /research-deep when: user requests \"comprehensive/thorough\" research OR initial search yields < 10 quality sources
     - Command: `/research-deep {destination} travel guide 2026`
     - This triggers 15-20 iterative searches across multiple sources
     - Available commands: /research-deep, /deep-search, /search-tree
     - Integrate results into your research data

  2. **Standard WebSearch** (always required):
     Execute multiple searches NOW:
     - \"best time to visit {destination} {year}\"
     - \"top attractions in {destination} 2026\"
     - \"best hotels in {destination} {budget_tier}\"
     - \"best restaurants in {destination}\"
     - \"things to do in {destination} {interests}\"
     - \"{destination} travel costs {year}\"
     - \"{destination} transportation guide\"
     - Additional searches based on specific interests

  3. **Bilibili Search** (supplementary - Chinese video platform):
     Search queries (use WebSearch with site:bilibili.com or general search):
     - \"{destination} 旅游攻略\" (travel guide)
     - \"{destination} vlog\"
     - \"{destination} 美食探店\" (food exploration)
     - \"{destination} 景点推荐\" (attractions recommendation)

     Extract: video title, UP主 (creator), views, URL, brief summary
     Add to video_content array in JSON

     **IMPORTANT**: This is supplementary. Do NOT fail if no Bilibili results found.

  4. **Xiaohongshu (小红书) Search** (supplementary - Chinese social platform):
     Search queries (use WebSearch with site:xiaohongshu.com or general search):
     - \"{destination} 旅游\" (travel)
     - \"{destination} 攻略\" (guide)
     - \"{destination} 美食\" (food)
     - \"{destination} 酒店\" (hotels)
     - \"{destination} 打卡\" (check-in spots)

     Extract: note title, author, likes, URL, content snippet
     Add to social_content array in JSON

     **IMPORTANT**: This is supplementary. Do NOT fail if no Xiaohongshu results found.

  **VALIDATION CHECK**: Your JSON must contain:
  - At least 10 unique URLs in sources (from any combination of searches)
  - At least 5 attractions with real data
  - At least 3 accommodation options
  - At least 5 restaurant/dining options
  - Budget estimates based on research
  - video_content array (can be empty if no results)
  - social_content array (can be empty if no results)

  Empty core fields = you did NOT execute research = CRITICAL FAILURE
  Missing video_content/social_content arrays = acceptable (Chinese platforms are optional)

  After completing actual web research, return ONLY:

  {
    \"destination_info\": {
      \"name\": \"Destination name\",
      \"best_time_to_visit\": \"Season/months and why\",
      \"weather\": \"Weather during user's travel dates\",
      \"time_zone\": \"Time zone\",
      \"currency\": \"Local currency\",
      \"language\": \"Primary language(s)\",
      \"overview\": \"Brief destination overview highlighting what makes it special\"
    },
    \"attractions\": [
      {
        \"name\": \"Attraction name\",
        \"category\": \"culture|adventure|nature|food|nightlife|relaxation\",
        \"description\": \"What it is and why visit\",
        \"location\": \"Specific location/address\",
        \"estimated_time\": \"How long to spend there\",
        \"estimated_cost\": \"Entrance fee or free\",
        \"best_time\": \"Best time of day to visit\",
        \"url\": \"Official website or info URL\"
      }
    ],
    \"accommodations\": [
      {
        \"name\": \"Hotel/accommodation name\",
        \"type\": \"hotel|hostel|resort|apartment|boutique\",
        \"location\": \"Neighborhood/area\",
        \"description\": \"Brief description\",
        \"estimated_price_per_night\": \"Price range in local currency\",
        \"amenities\": [\"amenity1\", \"amenity2\"],
        \"url\": \"Booking URL or official website\"
      }
    ],
    \"restaurants\": [
      {
        \"name\": \"Restaurant name\",
        \"cuisine\": \"Cuisine type\",
        \"description\": \"What they're known for\",
        \"location\": \"Neighborhood/address\",
        \"estimated_cost\": \"budget|moderate|expensive\",
        \"specialties\": [\"dish1\", \"dish2\"],
        \"url\": \"Website or review URL\"
      }
    ],
    \"video_content\": [
      {
        \"platform\": \"bilibili\",
        \"title\": \"Video title\",
        \"creator\": \"UP主 name\",
        \"views\": \"View count\",
        \"url\": \"https://www.bilibili.com/video/...\",
        \"summary\": \"Brief description of content\"
      }
    ],
    \"social_content\": [
      {
        \"platform\": \"xiaohongshu\",
        \"title\": \"Note title\",
        \"author\": \"Author name\",
        \"likes\": \"Like count\",
        \"url\": \"https://www.xiaohongshu.com/...\",
        \"snippet\": \"Content preview or key highlights\"
      }
    ],
    \"transportation\": {
      \"getting_there\": \"How to reach destination (flights, trains, etc.)\",
      \"airport\": \"Main airport code and name\",
      \"local_transport\": [\"metro\", \"bus\", \"taxi\", \"rental car\"],
      \"transport_tips\": \"Tips for getting around\",
      \"estimated_transport_cost\": \"Daily transport budget estimate\"
    },
    \"daily_itinerary_suggestions\": [
      {
        \"day\": 1,
        \"theme\": \"Day theme (e.g., Historic Center, Nature Day)\",
        \"activities\": [
          {
            \"time\": \"morning|afternoon|evening\",
            \"activity\": \"What to do\",
            \"location\": \"Where\"
          }
        ]
      }
    ],
    \"estimated_costs\": {
      \"accommodation_total\": \"Total for duration\",
      \"food_daily\": \"Estimated daily food budget\",
      \"activities_total\": \"Total for attractions/activities\",
      \"transportation_total\": \"Flights + local transport\",
      \"total_estimate\": \"Overall trip cost estimate\",
      \"currency\": \"Currency used\",
      \"notes\": \"Budget breakdown notes\"
    },
    \"practical_info\": {
      \"visa_requirements\": \"Visa info for common nationalities\",
      \"health_safety\": \"Health and safety tips\",
      \"local_customs\": \"Important customs/etiquette\",
      \"emergency_numbers\": \"Police, ambulance, etc.\"
    },
    \"useful_links\": [\"URL 1\", \"URL 2\", \"URL 3\"],
    \"sources\": [\"All research source URLs\"],
    \"confidence\": 85,
    \"research_quality\": \"comprehensive|good|limited\"
  }

  Save the complete JSON object to /root/travel-planner/data/{destination-slug}/research.json using the Write tool.

  After saving, return ONLY: complete

  DO NOT return the JSON in your response.
  "
```

Critical:
- Research subagent saves JSON to file and returns ONLY "complete"
- Main agent reads JSON from file after receiving "complete"
- User NEVER sees research subagent's response

### Step 4: Validate Research Quality

**After receiving "complete", read and validate the research JSON file**.

Step 1 - Verify file exists:
```bash
test -f /root/travel-planner/data/{destination-slug}/research.json && echo "verified" || echo "missing"
```

If output is "missing", STOP and debug (research subagent failed to save file).

Step 2 - Read JSON file:
```
Use Read tool on: /root/travel-planner/data/{destination-slug}/research.json
```

Step 3 - Parse and validate the JSON:

1. **Check if response is valid JSON**:
   - Try to parse the file content as JSON
   - Check for required fields: `destination_info`, `attractions`, `accommodations`, `restaurants`, `sources`

2. **Check research quality**:
   - Minimum 10 sources
   - Minimum 5 attractions
   - Minimum 3 accommodations
   - Minimum 5 restaurants
   - confidence >= 70

3. **If quality insufficient** → Re-invoke research subagent with escalated requirements:
   - Force more comprehensive web searches
   - Require minimum thresholds
   - Maximum 2 escalation attempts
   - Subagent overwrites same file path

4. **If still insufficient after 2 attempts** → Inform user:
   ```
   I was able to gather some information about {destination}, but comprehensive travel data is limited. I'll create a plan with the best information available. Would you like to proceed or choose a different destination?
   ```

5. **If validation passes** → Proceed to Step 5

**Result**: You now have validated research data loaded in memory to pass to HTML generation.

### Step 5: Generate HTML Travel Plan

**Consult HTML subagent to create professional travel plan**.

Transition naturally (user doesn't see consultation):
```
Great! I've gathered comprehensive information. Now I'm putting together your personalized travel plan.
```

Then execute HTML generation (user doesn't see this process):

```
Use Task tool with:
- subagent_type: "html-travel"
- description: "Generate professional HTML travel plan"
- model: "sonnet"  # Use capable model for quality HTML
- prompt: "
  ⚠️ CRITICAL OUTPUT INSTRUCTIONS:

  1. Save your HTML to: /root/travel-planner/travel-plan-{destination-slug}-{YYYY-MM-DD}.html
  2. After saving the file, return ONLY the word: complete
  3. Do NOT return the HTML content in your response

  Where:
  - {destination-slug} is the destination in lowercase with hyphens (e.g., 'paris', 'new-york')
  - {YYYY-MM-DD} is today's date in ISO format

  You are a CONSULTANT to the main /plan agent, NOT the user's travel planner.
  The user will NEVER see your response - only the main agent will read your HTML file.

  Your task: Generate a professional, beautiful HTML travel plan and save it to the specified file path.

  **User Requirements**:
  {stringify user requirements}

  **Research Data**:
  {stringify research JSON}

  ---

  **HTML REQUIREMENTS**:

  1. **Structure**:
     - Header with trip title, destination, dates
     - Table of contents / quick navigation
     - Day-by-day itinerary section
     - Attractions detail section
     - Accommodation recommendations section
     - Dining recommendations section
     - Transportation guide section
     - Budget breakdown section
     - Practical information section
     - Useful links section
     - Footer with generation timestamp

  2. **Styling**:
     - Modern, clean design
     - Professional color scheme (avoid garish colors)
     - Mobile-responsive (media queries for small screens)
     - Print-friendly (hide navigation, optimize for paper)
     - Good typography (readable fonts, proper hierarchy)
     - Icons for sections (use Unicode emoji or CSS symbols)
     - Cards or panels for organized information
     - Hover effects for interactive elements

  3. **Content**:
     - Day-by-day itinerary with timeline
     - Each attraction: name, description, location, hours, cost, tips
     - Each hotel: name, location, description, price, amenities, booking link
     - Each restaurant: name, cuisine, specialties, location, price range
     - Budget breakdown table with totals
     - Google Maps embeds or links for locations
     - Clickable external links (open in new tab)

  4. **Interactive Features**:
     - Collapsible sections for long content
     - Smooth scroll navigation
     - Print button
     - Back-to-top button

  5. **Technical**:
     - Valid HTML5
     - Semantic tags (article, section, nav, etc.)
     - Accessibility (alt text, ARIA labels, semantic structure)
     - Meta tags (charset, viewport, description)

  **Example Structure**:
  ```html
  <!DOCTYPE html>
  <html lang=\"en\">
  <head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>Travel Plan: {Destination}</title>
    <style>
      /* Embedded CSS here */
      * { margin: 0; padding: 0; box-sizing: border-box; }
      body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }
      /* ... more styles ... */
      @media print { /* print styles */ }
      @media (max-width: 768px) { /* mobile styles */ }
    </style>
  </head>
  <body>
    <header>
      <h1>Your {Destination} Adventure</h1>
      <p class=\"trip-dates\">{dates} • {duration} days</p>
    </header>

    <nav><!-- quick navigation --></nav>

    <main>
      <section id=\"overview\"><!-- destination overview --></section>
      <section id=\"itinerary\"><!-- day by day --></section>
      <section id=\"attractions\"><!-- detailed attractions --></section>
      <section id=\"accommodations\"><!-- hotel options --></section>
      <section id=\"dining\"><!-- restaurants --></section>
      <section id=\"transportation\"><!-- getting around --></section>
      <section id=\"budget\"><!-- cost breakdown --></section>
      <section id=\"practical\"><!-- practical info --></section>
      <section id=\"links\"><!-- useful links --></section>
    </main>

    <footer>
      <p>Generated on {timestamp} by Claude Travel Planner</p>
    </footer>

    <script>
      // Minimal JavaScript for interactivity (collapsible sections, smooth scroll, print button)
    </script>
  </body>
  </html>
  ```

  Save the complete HTML document to the specified file path using the Write tool.

  After saving, return ONLY: complete

  DO NOT return the HTML in your response.
  "
```

Critical:
- HTML subagent saves HTML to file and returns ONLY "complete"
- Main agent reads HTML from file after receiving "complete"
- User NEVER sees HTML subagent's response

### Step 6: Present Plan and Save to File

**After receiving "complete", read HTML file and present to user**.

Step 1 - Verify file exists:
```bash
test -f /root/travel-planner/travel-plan-{destination-slug}-{YYYY-MM-DD}.html && echo "verified" || echo "missing"
```

If output is "missing", STOP and debug (HTML subagent failed to save file).

Step 2 - Read HTML file to validate:
```
Use Read tool on: /root/travel-planner/travel-plan-{destination-slug}-{YYYY-MM-DD}.html
```

Validate it's actual HTML (starts with <!DOCTYPE or <html>).

If HTML validation fails:
- Re-invoke HTML subagent with simplified requirements (max 1 retry)
- If still fails: Create basic HTML manually using Write tool with research data

Step 3 - Attempt GitHub Pages deployment (optional):

Check for credentials silently:
```bash
if [ -n "$GITHUB_TOKEN" ] || [ -f ~/.ssh/id_ed25519 ] || [ -f ~/.ssh/id_rsa ]; then
  bash /root/travel-planner/scripts/deploy-travel-plans.sh /root/travel-planner/travel-plan-{destination-slug}-{YYYY-MM-DD}.html
fi
```

If deployment succeeds:
- Capture the live URL from script output
- Include URL in presentation

If deployment fails or credentials not found:
- Continue without deployment (silent graceful degradation)
- Only show local file path

Step 4 - Present to user:

If deployed successfully:
```
Your personalized travel plan is ready!

📄 Saved to: `travel-plan-{destination-slug}-{YYYY-MM-DD}.html`
🌐 Live URL: https://{username}.github.io/travel-planner-graph/{destination-slug}/{YYYY-MM-DD}/

**Plan Summary**:
- 🌍 Destination: {destination}
- 📅 Duration: {duration} days
- 💰 Estimated Budget: {total_cost}
- 🏨 {number} accommodation options
- 🍽️ {number} dining recommendations
- 🎯 {number} attractions and activities

**What's Included**:
✓ Day-by-day itinerary
✓ Detailed attraction information
✓ Hotel recommendations with prices
✓ Restaurant suggestions
✓ Transportation guide
✓ Budget breakdown
✓ Practical travel tips
✓ Interactive map links

You can open the HTML file locally or view it online at the URL above. It's mobile-friendly and printable!

Would you like to make any adjustments to the plan?
```

If NOT deployed:
```
Your personalized travel plan is ready!

📄 Saved to: `travel-plan-{destination-slug}-{YYYY-MM-DD}.html`

**Plan Summary**:
- 🌍 Destination: {destination}
- 📅 Duration: {duration} days
- 💰 Estimated Budget: {total_cost}
- 🏨 {number} accommodation options
- 🍽️ {number} dining recommendations
- 🎯 {number} attractions and activities

**What's Included**:
✓ Day-by-day itinerary
✓ Detailed attraction information
✓ Hotel recommendations with prices
✓ Restaurant suggestions
✓ Transportation guide
✓ Budget breakdown
✓ Practical travel tips
✓ Interactive map links

You can open the HTML file in any browser to view your complete travel plan. It's mobile-friendly and printable!

Would you like to make any adjustments to the plan?
```

Proceed to Step 7.

### Step 7: Offer Iterations and Refinements

**Multi-turn refinement loop with subagent re-invocation support**.

Wait for user response:

**User says satisfied** ("thanks", "perfect", "looks good"):
- Acknowledge and end gracefully
- Remind them they can run `/plan` again for future trips
- End workflow

**User requests changes** - Determine change type and take appropriate action:

**Type 1: Research-level changes** (require new/updated research):
- Examples: "add more restaurants", "find budget hotels instead", "focus more on nightlife"
- Action:
  1. Re-invoke research subagent (Step 3) with refined requirements:
     - Include conversation context and user refinement request
     - Specify what changed (e.g., "User wants more budget hotels, fewer luxury options")
     - Subagent overwrites `/root/travel-planner/data/{destination-slug}/research.json`
     - Subagent returns "complete"
  2. Verify updated research.json exists (test -f)
  3. Read updated research.json
  4. Re-invoke HTML subagent (Step 5) with updated research data
     - Save to: `/root/travel-planner/travel-plan-{destination-slug}-{YYYY-MM-DD}-v2.html`
     - Subagent returns "complete"
  5. Verify HTML exists, read it, validate, deploy (optional)
  6. Present updated plan to user
  7. Loop back to refinement offer

**Type 2: HTML-only changes** (no new research needed):
- Examples: "change color scheme", "reorder sections", "make it more compact"
- Action:
  1. Re-invoke HTML subagent (Step 5) with same research data but new styling requirements
     - Read existing research.json
     - Include conversation context and user refinement request
     - Save to: `/root/travel-planner/travel-plan-{destination-slug}-{YYYY-MM-DD}-v2.html`
     - Subagent returns "complete"
  2. Verify HTML exists, read it, validate, deploy (optional)
  3. Present updated plan to user
  4. Loop back to refinement offer

**Type 3: Questions** ("tell me more about X", "is Y good for families?"):
- Answer naturally using research data you have in memory
- If you don't have the info: Offer to re-research and update plan (becomes Type 1)
- Continue dialogue
- Loop back to refinement offer

**Versioning Pattern**:
- Original: `travel-plan-{destination-slug}-{YYYY-MM-DD}.html`
- Version 2: `travel-plan-{destination-slug}-{YYYY-MM-DD}-v2.html`
- Version 3: `travel-plan-{destination-slug}-{YYYY-MM-DD}-v3.html`
- Track version number throughout refinement loop

**Re-consultation Pattern**:
```
Use same Task tool patterns from Steps 3-5:
- Research subagent: Include refinement context in prompt, overwrite research.json, return "complete"
- HTML subagent: Include refinement context in prompt, save versioned HTML, return "complete"
- Always verify files exist before reading
- Always read files to validate content
```

**Maximum iterations**: 3 major revisions
- After 3 revisions (v3), gently close: "We've created a comprehensive plan! You can always run `/plan` again if you want to start fresh with different requirements."

**Dialogue Length Protection**:
- After 15 total turns in workflow → Suggest finalizing
- After 20 turns → Politely close and save final version

### Step 8: Workflow Completion

Mark final step as completed in TodoWrite.

Natural ending:
```
Enjoy planning your trip to {destination}! Your travel plan is saved and ready to use.

💡 Tip: You can run `/plan` anytime to create plans for other destinations.
```

## Architecture Notes

This command uses **Three-Party Architecture**:

1. **You (Main Agent)**: The travel consultant the user interacts with
   - Conduct requirement interviews
   - Present information naturally
   - Orchestrate subagent consultations invisibly
   - Handle user dialogue and refinements

2. **Research Subagent**: Backend JSON consultant (via Task tool)
   - Executes web searches for travel information
   - Returns structured JSON data
   - User never sees this interaction

3. **HTML Subagent**: Backend HTML generator (via Task tool)
   - Generates professional travel plan HTML
   - Returns complete standalone HTML document
   - User never sees this interaction

**Golden Rules**:
- User sees: Natural conversation with a single travel consultant (you)
- User never sees: "Let me consult the researcher...", "Generating HTML...", or any meta-commentary
- You internalize subagent outputs and present results naturally
- Subagents are your invisible assistants, not visible participants

## Notes

- Always use absolute file paths when saving HTML
- HTML files are standalone (no external dependencies except optional CDN fonts)
- Research quality gate ensures minimum viable plan data
- Support iterative refinement but cap at 3 major revisions
- Follow Three-Party Architecture strictly for clean user experience
