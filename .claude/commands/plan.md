---
description: "Multi-agent travel planning with specialized subagents and interactive HTML generation"
allowed-tools: Task, Read, Write, TodoWrite, Skill, Bash
argument-hint: "[destination]"
model: inherit
---

**⚠️ CRITICAL**: Use TodoWrite to track workflow phases. Mark in_progress before each phase, completed immediately after.

# Plan Command

Multi-agent travel planning system using specialized domain agents for comprehensive itinerary creation with validation and HTML generation.

## Usage

```
/plan [destination]
```

## Subagent Communication Protocol

**CRITICAL ARCHITECTURE PRINCIPLE**: This workflow uses a file-based pipeline pattern where orchestrator coordinates and subagents execute. All data passes through working files, NOT agent responses.

### Response Modes

Subagents operate in two response modes:

**Mode 1: Normal Operations** (default)
- Subagent returns ONLY the string: `"complete"`
- NO data, NO summaries, NO explanations in response
- All output written to designated working file
- Orchestrator verifies file exists with `test -f` before proceeding
- Orchestrator reads working file for data presentation

**Mode 2: Refine Operations** (optimization loops)
- Subagent returns JSON with changes diff
- Used in Day optimization loops (Step 14-15) and refinement iterations (Step 20)
- Format:
```json
{
  "status": "complete",
  "modified_data": "Complete data matching working file structure",
  "changes": [
    {
      "location": "JSONPath to changed field (e.g., days[2].entertainment[0].name)",
      "action": "added|modified|deleted",
      "before": "Previous value (if modified/deleted)",
      "after": "New value (if added/modified)",
      "reason": "Explanation of why this change was made"
    }
  ],
  "summary": {
    "total_changes": 5,
    "items_added": 2,
    "items_modified": 2,
    "items_deleted": 1
  }
}
```

### File-Based Pipeline Rules

1. **Orchestrator reads, subagents write**: Orchestrator uses Read tool for coordination, NEVER modifies working files directly
2. **Pass file paths, not content**: Agent prompts specify file paths to read, not data content
3. **Verify before proceeding**: Always use `test -f <file_path>` after agent returns to confirm output exists
4. **No response parsing**: Orchestrator does NOT parse agent response text for data - only reads working files
5. **Single source of truth**: Working files in `data/{destination-slug}/*.json` are authoritative

### Working File Ownership

Each specialist agent owns specific working files:
- `meals.json` - meals-agent
- `attractions.json` - attractions-agent
- `entertainment.json` - entertainment-agent
- `shopping.json` - shopping-agent
- `accommodation.json` - accommodation-agent
- `transportation.json` - transportation-agent
- `timeline.json` - timeline-agent
- `budget.json` - budget-agent

**Architecture Enforcement**: Orchestrator MUST delegate modifications to owning agent via Task tool. Direct file modification by orchestrator violates separation of concerns.

### Example: File-Based Pattern in Action

**Scenario**: User requests "Add spa for Day 3"

**❌ INCORRECT (Direct Data Return Pattern)**:
```
Orchestrator invokes entertainment-agent
Agent response: "I've added three spas: Spa A, Spa B, Spa C. Here are the details... [returns full spa data in response text]"
Orchestrator parses response text
Orchestrator displays to user
```
**Problem**: Data in response text, not verifiable file, coupling between orchestrator and agent response format.

**✅ CORRECT (File-Based Pipeline Pattern)**:
```
Step 1: Orchestrator invokes entertainment-agent
  - Passes file paths: requirements-skeleton.json, entertainment.json
  - Instruction: "Add spa options for Day 3, save to entertainment.json"
  - Agent researches using gaode-maps/rednote
  - Agent updates entertainment.json
  - Agent returns: "complete"

Step 2: Orchestrator verifies file exists
  bash: test -f data/{destination-slug}/entertainment.json && echo "verified"

Step 3: Orchestrator re-invokes timeline-agent
  - Agent reads updated entertainment.json
  - Agent recalculates timeline
  - Agent returns: "complete"

Step 4: Orchestrator verifies timeline.json exists
  bash: test -f data/{destination-slug}/timeline.json && echo "verified"

Step 5: Orchestrator reads both files to present results
  - Reads entertainment.json for spa details
  - Reads timeline.json for updated schedule
  - Presents to user: "Added 3 spa options, timeline updated"
```

**Key Principles Demonstrated**:
1. Agent returns ONLY "complete" (no data in response)
2. All data flows through files (entertainment.json, timeline.json)
3. Orchestrator verifies with test -f before proceeding
4. Orchestrator reads files for presentation (not agent responses)
5. Dependent agents re-invoked automatically (timeline after entertainment change)

## Bilingual Annotation Requirement

**CRITICAL ARCHITECTURE PRINCIPLE**: All location-based subagents (meals, attractions, entertainment, shopping) MUST output proper nouns with bilingual annotations to prevent information loss.

### Why This Is Required

**Root Cause**: Chinese restaurant names get corrupted when subagents translate them to romanized English for JSON output. For example, '夜景' (Night View) was incorrectly written as '野青' (Wild Youth) because romanization loses tonal and character information.

**Data Flow Path Where Loss Occurs**:
```
User requirement (中文)
  → Orchestrator prompt (English)
  → Subagent searches Gaode Maps (中文输入/输出)
  → Subagent outputs JSON with romanized name ONLY
  → Information loss occurs here (homophones indistinguishable)
```

**Problem**: Chinese proper nouns lose semantic information when romanized. Homophones (同音字) cannot be distinguished without character annotations:
- '夜景' (yèjǐng) = "night view"
- '野青' (yěqīng) = "wild youth"
Both romanize to similar "Yeqing" but mean completely different things.

**Solution**: Require format: `"Romanized Name (原文字)"` or `"English Translation (Foreign Language)"`

This preserves original information alongside romanization, preventing homophone confusion and character loss during orchestrator-subagent communication.

### Annotation Format Specification

**Format**: `"Romanized/Translated Name (Original Script)"`

**Examples by Language**:
- Chinese: `"Qu Nanshan Yeqing Huoguo Gongyuan (去南山夜景火锅公园)"`
- Japanese: `"Fushimi Inari Shrine (伏見稲荷大社)"`
- Korean: `"Gyeongbokgung Palace (경복궁)"`
- Arabic: `"Khan el-Khalili (خان الخليلي)"`
- Thai: `"Som Tam Nua (ส้มตำนัว)"`
- Russian: `"Red Square (Красная площадь)"`

**When to Apply**:
- Restaurant names
- Attraction names
- Entertainment venue names
- Shopping location names
- Street/area names (if not standard romanization)

**What NOT to annotate**:
- Common nouns (e.g., "hotpot", "museum", "market")
- Already-standardized place names (e.g., "Beijing", "Tokyo")
- English brand names (e.g., "Starbucks", "McDonald's")

### Enforcement in Orchestrator Prompts

All subagent invocation prompts in this file explicitly require bilingual annotation format. If a subagent returns JSON without proper annotations, the orchestrator MUST flag this as a validation error and re-invoke the agent with specific feedback.

### Orchestrator Prompt Enforcement

**RULE**: ALL location-based subagent prompts MUST include bilingual annotation template from lines 156-177. Copy exactly, no abbreviations.

**VALIDATION**: After subagent completion, verify all proper nouns have bilingual annotations (format: "Name (原文)"). Missing annotations → re-invoke agent with validation error.

**REFERENCE**: See lines 159-165 for format examples.

---

## Implementation

### Step 0: Initialize Workflow

Load todos from: `scripts/todo/plan.py`

```bash
source /root/.claude/venv/bin/activate && python /root/travel-planner/scripts/todo/plan.py
```

Use output to create TodoWrite with all workflow steps.

**Rules**: Mark `in_progress` before each step, `completed` after. NEVER skip steps.

---

### Phase 1: BA Requirement Collection

#### Step 1: Parse Destination Hint

Extract from `$ARGUMENTS`:
- If provided: "I'll help you plan an amazing trip to {destination}!"
- If empty: "I'll help you plan an amazing trip! Where would you like to go?"

#### Step 2: Conduct Requirements Interview

Collect: destination(s), dates, duration, travelers, budget, daily plans (user's raw input in any language), preferences (accommodation type, dietary restrictions, activity pace, special needs).

For multi-city: confirm location per day.

**IMPORTANT - Orchestrator Role Boundaries**:
- You collect RAW user requirements only (dates, preferences, rough ideas)
- Do NOT research domain-specific details yourself - delegate to specialist agents
- Specialist agents handle all research in Phase 3
- Example: User says "need train from Chongqing to Bazhong" → Record requirement, delegate research to transportation-agent
- Example: User says "want to eat hot pot" → Record preference, delegate research to meals-agent
- Your job: Extract and structure user intent. Specialist agents research concrete options.

#### Step 3: Generate Requirements Skeleton

**CRITICAL**: Use script via Bash tool. Orchestrator architectural constraint prohibits Write tool.

Run skeleton generation script:
```bash
source /root/.claude/venv/bin/activate && python /root/travel-planner/scripts/generate-skeletons.py \
  --destination-slug "{destination-slug}" \
  --dates "{start_date}" "{end_date}" \
  --duration {days_count} \
  --travelers "{travelers_description}" \
  --budget "{budget_description}" \
  --preferences '{preferences_json}' \
  --days '{days_array_json}'
```

**Parameter Format**:
- `--destination-slug`: From Step 4 output (e.g., "beijing-20260204-145508")
- `--dates`: Two arguments, start and end dates in YYYY-MM-DD format
- `--duration`: Integer number of days
- `--travelers`: String description (e.g., "2 adults", "family of 4")
- `--budget`: String description (e.g., "$3000 per person", "5000 CNY total")
- `--preferences`: JSON string with dict (must escape quotes properly)
- `--days`: JSON string with array of day objects (must escape quotes properly)

**Example**:
```bash
source /root/.claude/venv/bin/activate && python /root/travel-planner/scripts/generate-skeletons.py \
  --destination-slug "beijing-20260204-145508" \
  --dates "2026-03-15" "2026-03-24" \
  --duration 10 \
  --travelers "2 adults" \
  --budget "\$3000 per person" \
  --preferences '{"accommodation": "mid-range", "dietary": "vegetarian", "pace": "moderate"}' \
  --days '[{"day": 1, "date": "2026-03-15", "location": "Beijing", "user_plans": ["Great Wall", "Peking Duck"]}, {"day": 2, "date": "2026-03-16", "location": "Beijing", "user_plans": ["Forbidden City", "Temple of Heaven"]}]'
```

**Script Output**:
- Creates: `data/{destination-slug}/requirements-skeleton.json`
- Creates: `data/{destination-slug}/plan-skeleton.json` (with location change detection)
- Prints: Confirmation messages with file paths and location change count

**Exit Codes**:
- 0: Success (both files created)
- 1: Validation error (invalid parameters)
- 2: Unexpected error (file system, permissions)

**Requirements Skeleton Structure**:
```json
{
  "trip_summary": {
    "dates": "2026-03-15 to 2026-03-24",
    "duration_days": 10,
    "travelers": "2 adults",
    "budget": "$3000 per person",
    "preferences": {
      "accommodation": "mid-range",
      "dietary": "vegetarian",
      "pace": "moderate"
    }
  },
  "days": [
    {
      "day": 1,
      "date": "2026-03-15",
      "location": "Chongqing",
      "user_plans": [
        "想去洪崖洞看夜景",
        "吃火锅",
        "看长江索道"
      ]
    },
    {
      "day": 2,
      "date": "2026-03-16",
      "location": "Chongqing",
      "user_plans": [
        "磁器口古镇",
        "解放碑购物"
      ]
    }
  ]
}
```

#### Step 4: Generate Plan Slug

**CRITICAL: This step addresses root cause from commit 77dca06.**

Generate unique directory slug to prevent multiple /plan executions from mixing files.

Run slug generation script:
```bash
source /root/.claude/venv/bin/activate && python /root/travel-planner/scripts/generate-plan-slug.py "{destination}"
```

Capture output and set `{destination-slug}` variable for ALL subsequent steps.

**Slug Format Specification**:
- Pattern: `{destination-sanitized}-{YYYYMMDD-HHMMSS}`
- Sanitization rules:
  - Lowercase conversion
  - Spaces/underscores → hyphens
  - Remove non-alphanumeric (handles Chinese characters safely)
  - Collapse multiple hyphens
  - Fallback to "destination" if empty after sanitization
- Timestamp: Current execution time in format YYYYMMDD-HHMMSS
- Examples:
  - "China" → `china-20260201-211600`
  - "New York City" → `new-york-city-20260201-235500`
  - "中国" → `destination-20260201-235500` (Chinese chars removed)

**Verification**:
```bash
echo "{destination-slug}" | grep -E '^[a-z0-9\-]+-[0-9]{8}-[0-9]{6}$' && echo "valid" || echo "invalid"
```

**Why This Fixes the Issue**:
Commit 77dca06 introduced {destination-slug} placeholder used 40+ times throughout plan.md, but never defined generation logic. Without explicit timestamp-based slugs, multiple /plan executions with same destination/dates reused identical directories, causing file conflicts and data混淆.

#### Step 5: Validate Day Completion

Run validation script:
```bash
bash /root/travel-planner/scripts/check-day-completion.sh {destination-slug}
```

**Exit code 0**: All days complete → Proceed to Phase 2
**Exit code 1**: Missing user_plans → Loop back, ask for missing days
**Exit code 2**: File not found → Debug and retry

**Loop until all days have user_plans populated**.

---

### Phase 2: Orchestrator Skeleton Initialization

#### Step 6: Verify Plan Skeleton

**NOTE**: Plan skeleton is already created by Step 3 script with location change detection.

Verify plan skeleton exists and contains location changes:
```bash
test -f /root/travel-planner/data/{destination-slug}/plan-skeleton.json && echo "verified" || echo "missing"
```

**If missing**: Debug Step 3 script execution and retry.

Plan skeleton structure (already created):
```json
{
  "days": [
    {
      "day": 1,
      "date": "2026-03-15",
      "location": "Chongqing",
      "location_change": null,
      "user_requirements": ["想去洪崖洞看夜景", "吃火锅"],
      "breakfast": {"name": "", "location": "", "cost": 0},
      "lunch": {"name": "", "location": "", "cost": 0},
      "dinner": {"name": "", "location": "", "cost": 0},
      "accommodation": {"name": "", "location": "", "cost": 0},
      "attractions": [],
      "entertainment": [],
      "shopping": [],
      "free_time": [],
      "timeline": {},
      "budget": {
        "meals": 0,
        "accommodation": 0,
        "activities": 0,
        "shopping": 0,
        "transportation": 0,
        "total": 0
      }
    }
  ],
  "emergency_info": {
    "hospitals": [],
    "police_stations": [],
    "embassy": null
  }
}
```

#### Step 7: Validate Location Continuity

Run validation script:
```bash
bash /root/travel-planner/scripts/check-location-continuity.sh {destination-slug}
```

**Exit code 0**: All location changes have objects → Proceed
**Exit code 1**: Missing location_change objects → Fix and retry

---

### Phase 3: Specialist Agent Execution

#### Step 8: Invoke Parallel Agents (6 agents simultaneously)

**Invoke these agents in parallel using Task tool**:

1. **meals-agent**
2. **accommodation-agent**
3. **attractions-agent**
4. **entertainment-agent**
5. **shopping-agent**
6. **transportation-agent** (only processes days with location_change)

**Invocation Pattern**:
```
Use Task tool with:
- subagent_type: "meals-agent"
- description: "Research meals for {destination} trip"
- model: "sonnet"
- prompt: "
  Read from:
  - data/{destination-slug}/requirements-skeleton.json
  - data/{destination-slug}/plan-skeleton.json

  Research and recommend breakfast, lunch, dinner for each day.

  **IMPORTANT - Bilingual Annotation Required**:
  To prevent information loss through romanization (e.g., homophone confusion where 夜景 yèjǐng becomes 野青 yěqīng), ALL proper nouns MUST include original script annotations.

  Format: "Romanized Name (原文)" or "English Translation (Foreign Language)"
  Examples:
  - "Qu Nanshan Yeqing Huoguo Gongyuan (去南山夜景火锅公园)"
  - "Night View Hotpot Park (夜景火锅公园)"

  **IMPORTANT - GPS Coordinates Required**:
  For each meal location, use gaode-maps (China) or google-maps (international) to obtain GPS coordinates.
  Output format for each meal:
  {
    name: string (with bilingual annotation),
    location: string (address),
    cost: number,
    cuisine: string,
    notes: string,
    coordinates: {latitude: float, longitude: float}
  }

  Save to: data/{destination-slug}/meals.json

  After completing all tasks, return ONLY the word 'complete'.
  "
```

**Each agent**:
- Reads requirements and plan skeleton
- Performs domain-specific research using available MCP skills (google-maps, gaode-maps, rednote, etc.)
- **Bilingual Annotation Requirements** (meals, attractions, entertainment, shopping agents):
  - ALL proper nouns MUST include original script annotations
  - Format: "Romanized Name (原文)" or "English Translation (Foreign Language)"
  - This prevents information loss through homophone confusion (see Bilingual Annotation Requirement section)
- **GPS Coordinate Requirements** (meals, attractions, entertainment, shopping agents):
  - Use gaode-maps (for China locations) or google-maps (international) to obtain GPS coordinates
  - Add `coordinates: {latitude: float, longitude: float}` field to each location entry
  - Format: latitude/longitude as decimal degrees (e.g., 29.5583, 106.5528 for Chongqing)
- Saves structured data to `data/{destination-slug}/{agent-name}.json`
- Returns ONLY: `complete`

**Wait for all 6 agents to return "complete"**.

**Verify files exist before proceeding**:
```bash
test -f /root/travel-planner/data/{destination-slug}/meals.json && echo "meals.json verified" || echo "meals.json missing"
test -f /root/travel-planner/data/{destination-slug}/accommodation.json && echo "accommodation.json verified" || echo "accommodation.json missing"
test -f /root/travel-planner/data/{destination-slug}/attractions.json && echo "attractions.json verified" || echo "attractions.json missing"
test -f /root/travel-planner/data/{destination-slug}/entertainment.json && echo "entertainment.json verified" || echo "entertainment.json missing"
test -f /root/travel-planner/data/{destination-slug}/shopping.json && echo "shopping.json verified" || echo "shopping.json missing"
test -f /root/travel-planner/data/{destination-slug}/transportation.json && echo "transportation.json verified" || echo "transportation.json missing"
```

If any file missing: Debug and re-invoke failed agent.

#### Step 9: Verify Agent Outputs

Check all files exist:
```bash
cd /root/travel-planner/data/{destination-slug} && ls -1 *.json | grep -E '(meals|accommodation|attractions|entertainment|shopping|transportation)\.json'
```

Expected: 6 files (or 5 if no location changes → transportation.json may be empty)

If any missing: Debug and re-invoke failed agent.

**Deep Content Validation**:

Run validation script:
```bash
source /root/.claude/venv/bin/activate && python /root/travel-planner/scripts/validate-agent-outputs.py /root/travel-planner/data/{destination-slug}
```

**Exit code 0**: All valid → Proceed
**Exit code 1**: Critical issues → Re-invoke failed agents with specific feedback from validation errors
**Exit code 2**: Warnings only → Log warnings and continue

If critical issues found, extract specific errors and re-invoke relevant agents with fix instructions.

#### Step 10: Invoke Timeline Agent with Route Optimization (Serial)

**Architecture Note - Root Cause Reference (commit 795bea0)**: This step delegates route optimization and timeline creation to timeline-agent as a unified workflow. Orchestrator must NOT execute scripts directly - all implementation details are handled by the subagent.

```
Use Task tool with:
- subagent_type: "timeline-agent"
- description: "Optimize route and create timeline with conflict detection"
- model: "sonnet"
- prompt: "
  **UNIFIED WORKFLOW: Route Optimization + Timeline Creation**

  Your task has two phases:

  **Phase 1 - Route Optimization**:
  1. Read GPS coordinates from all location-based agent outputs:
     - data/{destination-slug}/meals.json (breakfast/lunch/dinner coordinates)
     - data/{destination-slug}/attractions.json (attraction coordinates)
     - data/{destination-slug}/entertainment.json (entertainment coordinates)
     - data/{destination-slug}/shopping.json (shopping coordinates)

  2. For each day, analyze activity locations:
     - Calculate haversine distances between all locations
     - Detect inefficient routing patterns (A→B→A patterns)
     - Optimize activity order using nearest-neighbor approach to minimize travel
     - Generate optimized activity sequence per day

  3. Save optimization results to: data/{destination-slug}/route-optimization.json
     Format:
     {
       days: [
         {
           day: N,
           date: 'YYYY-MM-DD',
           location: 'City',
           optimized_order: ['Activity 1', 'Activity 2', ...],
           distance_comparison: {
             original_km: float,
             optimized_km: float,
             savings_km: float,
             savings_percent: float
           },
           warnings: ['efficiency notes']
         }
       ]
     }

  **Phase 2 - Timeline Creation**:
  1. Read ALL agent outputs:
     - data/{destination-slug}/plan-skeleton.json
     - data/{destination-slug}/meals.json
     - data/{destination-slug}/accommodation.json
     - data/{destination-slug}/attractions.json
     - data/{destination-slug}/entertainment.json
     - data/{destination-slug}/shopping.json
     - data/{destination-slug}/transportation.json
     - data/{destination-slug}/route-optimization.json (from Phase 1)

  2. Create timeline as DICTIONARY using optimized activity order:
     - Keys: EXACT activity names from source JSONs
     - Values: {start_time: 'HH:MM', end_time: 'HH:MM', duration_minutes: N}
     - Schedule activities following route-optimization.json order for efficiency

  3. Detect conflicts: overlapping times, unrealistic travel, tight schedules

  4. **CRITICAL - Save JSON to: data/{destination-slug}/timeline.json**
     Use Write tool explicitly (see timeline.md Step 3 for details).
     Root Cause Reference (commit ef0ed28): Explicit Write instruction prevents timeline data loss.

  **IMPORTANT**:
  - If any locations lack GPS coordinates, optimize only locations with valid coordinates
  - Log warnings for missing coordinates but continue with optimization
  - Both route-optimization.json AND timeline.json must be created

  After completing all tasks, return ONLY the word 'complete'.
  "
```

Wait for agent to return "complete".

**Verification - Root Cause Reference (commit ef0ed28)**: File-based pipeline requires explicit verification after subagent completion.

**Step 1**: Confirm both files exist:
```bash
test -f /root/travel-planner/data/{destination-slug}/route-optimization.json && echo "route-optimization.json verified" || echo "missing"
test -f /root/travel-planner/data/{destination-slug}/timeline.json && echo "timeline.json verified" || echo "missing"
```

If either file missing: Debug timeline-agent execution and retry.

**Step 2**: Read and verify timeline.json content (equity-analyst pattern):
```bash
Read data/{destination-slug}/timeline.json
```

**Step 3**: Validate timeline data completeness:
- Verify JSON contains "data.days" array
- Verify at least one day has non-empty "timeline" dictionary (not {})
- Count days with populated timeline data

**Step 4**: If timeline.json has empty timeline dictionaries for all days:
- Flag as data loss error
- Re-invoke timeline-agent with explicit Write instruction reminder
- Do NOT proceed to Step 11 until timeline data is verified

#### Step 11: Validate Timeline Consistency

Run validation script:
```bash
bash /root/travel-planner/scripts/validate-timeline-consistency.sh {destination-slug}
```

**Exit code 0**: Timeline valid → Proceed
**Exit code 1**: Validation errors (mismatched keys, conflicts) → Review timeline.json warnings

#### Step 12: Invoke Budget Agent (Serial)

**IMPORTANT**: Budget agent runs AFTER timeline agent completes.

```
Use Task tool with:
- subagent_type: "budget-agent"
- description: "Calculate budget and detect overages"
- model: "sonnet"
- prompt: "
  Read ALL agent outputs including timeline:
  - data/{destination-slug}/requirements-skeleton.json
  - data/{destination-slug}/plan-skeleton.json
  - data/{destination-slug}/meals.json
  - data/{destination-slug}/accommodation.json
  - data/{destination-slug}/attractions.json
  - data/{destination-slug}/entertainment.json
  - data/{destination-slug}/shopping.json
  - data/{destination-slug}/transportation.json
  - data/{destination-slug}/timeline.json

  Calculate daily budget breakdown.
  Compare to user's budget.
  Generate warnings for overages.
  Provide specific optimization recommendations.

  Save to: data/{destination-slug}/budget.json

  After completing all tasks, return ONLY the word 'complete'.
  "
```

Wait for agent to return "complete".

**Verification**: Confirm file exists before proceeding:
```bash
test -f /root/travel-planner/data/{destination-slug}/budget.json && echo "budget.json verified" || echo "missing"
```

If file missing: Debug budget-agent execution and retry.

#### Step 13: Budget Gate Check

**CRITICAL**: Check if budget overage exceeds thresholds requiring mandatory review.

Run budget gate script:
```bash
source /root/.claude/venv/bin/activate && python /root/travel-planner/scripts/check-budget-overage.py /root/travel-planner/data/{destination-slug}/budget.json 200 20
```

**Exit code 0**: Budget acceptable → Set `force_review=false`, proceed to Step 14
**Exit code 1**: Review required → Set `force_review=true`, proceed to Step 14 (user CANNOT skip)
**Exit code 2**: Error → Debug budget.json and retry

**Root Cause Reference**: Budget gate added to address commit 77dca06 issue where €963 overage (96%) was not caught, requiring mandatory day-by-day review when overage exceeds thresholds.

---

### Phase 4: Validation and Conflict Review

#### Step 14: Day-by-Day Refinement Loop (Nested Loop Pattern)

**Root Cause Reference**: Commit 77dca06 inherited linear day iteration without per-day cycling support. This step implements nested loop: OUTER loop for sequential day progression (1→2→3...→N), INNER loop for current day refinement until user confirms perfect.

**CRITICAL ORCHESTRATOR CONSTRAINT**: You CANNOT modify working files directly. All changes MUST be delegated to specialist subagents via Task tool. Working files in `data/{destination-slug}/*.json` represent specialist agent outputs and require domain expertise to modify correctly.

Read warnings from:
- `data/{destination-slug}/timeline.json` → Check `warnings` array
- `data/{destination-slug}/budget.json` → Check `warnings` and `recommendations` arrays

**Check force_review flag** (set in Step 13 by budget gate)

**If no warnings AND force_review=false**: Proceed to Phase 5

**If warnings exist OR force_review=true**: Execute nested loop refinement
- When `force_review=true`, user CANNOT skip review (budget gate enforcement)
- Present clear explanation: "Budget exceeds thresholds (see Step 13), day-by-day review is required"

---

**NESTED LOOP PATTERN**:

**OUTER LOOP - Sequential Day Progression**:
```
current_day_index = 1
total_days = count of days with warnings (or all days if force_review=true)

while current_day_index <= total_days:
    Execute INNER LOOP for current_day_index
    If user confirms "Day is perfect": current_day_index += 1
    If user chooses "Accept all remaining": break, proceed to Phase 5
```

**INNER LOOP - Current Day Refinement Cycle**:
```
day_confirmed_perfect = false

while not day_confirmed_perfect:
    1. Extract current day data from all agent JSONs
    2. Present COMPLETE day plan (MANDATORY format below)
    3. Offer user options (see below)
    4. Process user choice:
       - "This day is perfect" → Set day_confirmed_perfect = true, exit INNER loop
       - "Make changes to Day N" → Re-invoke agents (Step 15), stay in INNER loop
       - "Accept all remaining" → Exit both loops, proceed to Phase 5
    5. If changes made: Re-present Day N (loop continues)
```

---

**MANDATORY COMPLETE DAY PRESENTATION FORMAT**:

**CRITICAL**: ALWAYS present complete day details regardless of budget status. Never omit content due to budget overage.

```
═══════════════════════════════════════════════
**DAY {N} - {date}** ({location})
═══════════════════════════════════════════════

**📅 TIMELINE**:
{hour_by_hour_timeline_dict}
Example:
- 08:00-09:00: Breakfast at {restaurant_name}, {address}
- 09:30-11:30: Visit {attraction_name}, {location}
- 12:00-13:00: Lunch at {restaurant_name}, {address}
[... complete timeline with start/end times for all activities]

**🍽️ MEALS**:
- Breakfast: {name}, {address}, {cost} CNY
- Lunch: {name}, {address}, {cost} CNY
- Dinner: {name}, {address}, {cost} CNY

**🎯 ATTRACTIONS**:
- {attraction_name}: {location}, {duration} hours, {admission_fee} CNY
- {attraction_name}: {location}, {duration} hours, {admission_fee} CNY
[... all attractions with specific details]

**🎭 ENTERTAINMENT**:
- {activity_name}: {location}, {time}, {cost} CNY
[... all entertainment activities with specifics]

**💰 BUDGET BREAKDOWN**:
- Meals: {amount} CNY
- Accommodation: {amount} CNY
- Activities: {amount} CNY
- Transportation: {amount} CNY
- Shopping: {amount} CNY
- **Daily Total**: {total} CNY

⚠️ **WARNINGS** (if any):
- Timeline conflict: {specific_conflict_description}
- Budget overage: {specific_overage_description}

💡 **RECOMMENDATIONS** (if any):
- {specific_recommendation_based_on_warnings}

═══════════════════════════════════════════════
**YOUR OPTIONS FOR DAY {N}**:

1. ✅ This day is perfect, continue to Day {N+1}
2. ✏️ Make changes to Day {N} (describe your adjustments)
3. 🚀 Accept all remaining days as-is

Please choose an option or describe specific changes you'd like.
```

---

**STATE TRACKING**:
- `current_day_index`: Which day in sequence (1 to total_days)
- `day_confirmed_perfect`: Boolean flag for INNER loop exit
- `iteration_count_per_day`: Limit 5 iterations per day before suggesting acceptance
- `days_with_warnings`: Initial list of days requiring review

**USER CHOICE PROCESSING**:

**Option 1 - "This day is perfect"**:
- Set `day_confirmed_perfect = true`
- Exit INNER loop
- OUTER loop increments `current_day_index += 1`
- Present next day (if exists)

**Option 2 - "Make changes to Day N"**:
- Parse user's change request (identify affected domain and instruction)
- Stay in INNER loop (do NOT increment day index)
- **CRITICAL**: Use Task tool to delegate changes to specialist subagent (Step 15)
- **NEVER modify working files directly** - orchestrator reads, subagents write
- After agent completion, re-present Day N with INNER loop

**Option 3 - "Accept all remaining"**:
- Exit both OUTER and INNER loops
- Proceed to Phase 5 immediately

**REMOVED OPTION**: "Skip day" (user confirmed sequential-until-perfect pattern only)

---

**ITERATION SAFETY**:

After 5 iterations on same day:
```
I notice we've refined Day {N} multiple times ({iteration_count} iterations).

Current Day {N} state: [Show brief summary]

Options:
1. Accept Day {N} as-is and continue to Day {N+1}
2. Make one final adjustment to Day {N}
3. Accept all remaining days

Recommend: Review current state before additional changes.
```

---

**EXAMPLE EXECUTION FLOW**:

```
OUTER LOOP starts: current_day_index = 1

  INNER LOOP starts for Day 1:
    → Present complete Day 1 plan
    → User: "Make changes - add spa"
    → Re-invoke entertainment-agent (Step 15)
    → Re-present Day 1 with spa included
    → User: "Make changes - change lunch to vegetarian"
    → Re-invoke meals-agent (Step 15)
    → Re-present Day 1 with new lunch
    → User: "This day is perfect"
    → day_confirmed_perfect = true
  INNER LOOP exits

  current_day_index += 1 (now = 2)

  INNER LOOP starts for Day 2:
    → Present complete Day 2 plan
    → User: "This day is perfect"
    → day_confirmed_perfect = true
  INNER LOOP exits

  current_day_index += 1 (now = 3)

[Continue until all days confirmed or user accepts all remaining]
```

---

**EXIT CONDITIONS**:
- All days confirmed perfect (current_day_index > total_days)
- User selects "Accept all remaining"
- Then proceed to Phase 5

#### Step 15: Handle Day-Scoped Refinement (Re-invoke Agents)

**CRITICAL**: This step handles "Make changes to Day N" option from Step 14 INNER loop. After agent re-invocation and validation, **RETURN TO STEP 14 INNER LOOP** to re-present the current day. Do NOT auto-advance to next day.

**Root Cause Reference**: Commit 77dca06's linear design advanced to next day after changes. Nested loop requires returning to INNER loop for same day until user confirms perfect.

**ORCHESTRATOR ARCHITECTURAL PRINCIPLE**: You are COORDINATING changes, not EXECUTING them. All file modifications MUST be delegated to specialist subagents via Task tool. Working files in `data/{destination-slug}/*.json` are specialist domains - orchestrator reads to coordinate, subagents write to implement.

---

**When user selects "Make changes to Day N"** from Step 14:

Parse user's change request to extract:
- **Domain affected**: Which agent? (meals, attractions, entertainment, shopping, transportation)
- **Specific instruction**: What exactly to change/add/remove?
- **Constraints**: Budget limits, time constraints, preferences

**NEVER attempt to research or modify data yourself** - delegate to specialist subagent who will use MCP tools (gaode-maps, google-maps, rednote) and update working files.

---

**RE-INVOCATION PATTERN (Day-Scoped)**:

**Substep: Identify Affected Agent(s)**

Map user request to domain agent(s):
- "add spa", "nightlife", "娱乐" → entertainment-agent
- "restaurant", "meal", "breakfast", "lunch", "dinner" → meals-agent
- "attraction", "景点", "museum", "temple" → attractions-agent
- "shopping", "mall", "购物" → shopping-agent
- "hotel", "accommodation" → accommodation-agent
- "train", "flight", "transportation" → transportation-agent

**Substep: Re-invoke Specialist Agent with Day Filter**

**CRITICAL DELEGATION PATTERN**: Orchestrator delegates research and file modification to specialist subagent. Orchestrator provides context, subagent executes and updates working files.

```
Use Task tool with:
- subagent_type: "{domain}-agent"
- description: "Day {N} refinement: {user_request}"
- model: "sonnet"
- prompt: "
  **DAY-SCOPED REFINEMENT REQUEST**

  Focus ONLY on: Day {N}, Date {date}, Location {location}

  User's change request: {user's original text}

  Read existing data from:
  - data/{destination-slug}/requirements-skeleton.json
  - data/{destination-slug}/plan-skeleton.json
  - data/{destination-slug}/{domain}.json (your previous output)
  - data/{destination-slug}/budget.json (for Day {N} budget constraints)
  - data/{destination-slug}/timeline.json (for Day {N} schedule)

  YOUR TASK:
  1. Research NEW options OR adjust existing items for Day {N} only
     - Use MCP tools: google-maps, gaode-maps, rednote, etc.
     - DO NOT use placeholder data
  2. Update data/{destination-slug}/{domain}.json for Day {N} ONLY
     - MODIFY/ADD/REMOVE items for Day {N} as requested
     - PRESERVE data for all other days unchanged
  3. After completing all tasks, return ONLY the word 'complete'

  SPECIFIC INSTRUCTION: {parsed_user_instruction}

  Budget constraint for Day {N}: {remaining_budget} CNY
  Timeline constraint: {available_time_slots}
  User preferences: {preferences_from_requirements}
  "
```

Wait for agent to return "complete".

**Verification**: Confirm file updated before proceeding:
```bash
test -f /root/travel-planner/data/{destination-slug}/{domain}.json && echo "{domain}.json verified" || echo "{domain}.json missing"
```

If file missing: Debug specialist agent execution and retry.

**What orchestrator does**: Reads current state, identifies domain, delegates via Task tool, waits for completion
**What subagent does**: Researches using MCP tools, updates working file, returns completion signal

**Substep: Re-invoke Dependent Agents (Timeline + Budget)**

After specialist agent completes, **ALWAYS** re-invoke timeline and budget agents:

**Timeline Agent**:
```
Use Task tool with:
- subagent_type: "timeline-agent"
- description: "Recalculate timeline for Day {N}"
- model: "sonnet"
- prompt: "
  Re-read ALL agent outputs for Day {N}:
  - data/{destination-slug}/meals.json (Day {N})
  - data/{destination-slug}/attractions.json (Day {N})
  - data/{destination-slug}/entertainment.json (Day {N}) [UPDATED]
  - data/{destination-slug}/shopping.json (Day {N})
  - data/{destination-slug}/transportation.json (Day {N})

  Recalculate timeline ONLY for Day {N}.

  **CRITICAL - Save JSON to: data/{destination-slug}/timeline.json** (Day {N} section only).
  Use Write tool explicitly (see timeline.md Step 3).
  Root Cause Reference (commit ef0ed28): Explicit Write prevents timeline data loss.

  Detect any new conflicts.

  After completing all tasks, return ONLY the word 'complete'.
  "
```

**Budget Agent**:
```
Use Task tool with:
- subagent_type: "budget-agent"
- description: "Recalculate budget for Day {N}"
- model: "sonnet"
- prompt: "
  Re-read ALL agent outputs for Day {N} including updated timeline.
  Recalculate budget ONLY for Day {N}.
  Update data/{destination-slug}/budget.json (Day {N} section only).
  Check for new overages or warnings.

  After completing all tasks, return ONLY the word 'complete'.
  "
```

Wait for both agents to return "complete".

**Verification - Root Cause Reference (commit ef0ed28)**: File-based pipeline requires verification.

**Step 1**: Confirm files exist:
```bash
test -f /root/travel-planner/data/{destination-slug}/timeline.json && echo "timeline.json verified" || echo "timeline.json missing"
test -f /root/travel-planner/data/{destination-slug}/budget.json && echo "budget.json verified" || echo "budget.json missing"
```

**Step 2**: Read and verify timeline.json content (equity-analyst pattern):
```bash
Read data/{destination-slug}/timeline.json
```

Verify Day {N} timeline is populated (not empty dictionary).

---

**Substep: Validation (Day-Scoped)

Run day-scoped validation:
```bash
source /root/.claude/venv/bin/activate && python /root/travel-planner/scripts/validate-day-changes.py /root/travel-planner/data/{destination-slug} {day_number}
```

**Exit code 0**: Changes valid → Proceed to next substep
**Exit code 1**: Validation errors → Review and fix before proceeding

---

**Substep: Return to Step 14 INNER LOOP**

**CRITICAL**: Do NOT advance to next day. Return to Step 14 INNER loop to re-present the SAME day (Day N) with updated data.

```
Increment iteration_count_per_day
Return to Step 14 INNER LOOP:
  → Extract updated Day {N} data from all JSONs
  → Present complete Day {N} plan (with changes applied)
  → Offer same options:
    1. This day is perfect, continue to Day {N+1}
    2. Make changes to Day {N} (stays in INNER loop)
    3. Accept all remaining days
```

**User must explicitly choose "This day is perfect" to exit INNER loop and advance to Day N+1.**

---

**TRACKING STATE**:
- `iteration_count_per_day`: Increments after each re-invocation for same day
- `current_day_index`: Does NOT change during INNER loop iterations
- `agents_invoked_for_day`: Track which agents modified this day

**ITERATION LIMIT**:
After 5 iterations on same day, present safety warning (see Step 14).

---

**EXAMPLE EXECUTION FLOW**:

```
Step 14 INNER LOOP - Day 3:
  → Present complete Day 3 plan
  → User: "Make changes - add spa"

Step 15 (this step):
  → Parse: domain=entertainment, instruction="add spa"
  → Re-invoke entertainment-agent for Day 3
  → Re-invoke timeline-agent for Day 3
  → Re-invoke budget-agent for Day 3
  → Validate Day 3 changes
  → Return to Step 14 INNER LOOP

Step 14 INNER LOOP - Day 3 (re-presentation):
  → Present complete Day 3 plan WITH spa included
  → User: "Make changes - change lunch to vegetarian"

Step 15 (this step again):
  → Parse: domain=meals, instruction="change lunch to vegetarian"
  → Re-invoke meals-agent for Day 3
  → Re-invoke timeline-agent for Day 3
  → Re-invoke budget-agent for Day 3
  → Validate Day 3 changes
  → Return to Step 14 INNER LOOP

Step 14 INNER LOOP - Day 3 (re-presentation):
  → Present complete Day 3 plan WITH spa AND vegetarian lunch
  → User: "This day is perfect"
  → day_confirmed_perfect = true
  → Exit INNER loop, increment current_day_index to 4

Step 14 OUTER LOOP:
  → Move to Day 4, start new INNER loop
```

---

**KEY PRINCIPLE**: Step 15 is a subroutine of Step 14 INNER loop. After completing agent re-invocations and validations, **ALWAYS return to Step 14 INNER loop for same day**, never auto-advance.

---

### Phase 5: HTML Generation and Deployment

**⚠️ CRITICAL: Steps 16-18 are MANDATORY and ATOMIC. NEVER skip these steps.**

Root cause reference: Script separation caused workflow interruption where AI subjectively skipped deployment steps, violating the principle that generated plans must be immediately published.

#### Step 16: Generate and Deploy (Atomic Operation)

**IMPORTANT**: Generation and deployment are now a SINGLE atomic operation. Once HTML is generated, it MUST be deployed. There is NO option to skip deployment.

Run unified script:
```bash
bash /root/travel-planner/scripts/generate-and-deploy.sh {destination-slug}
```

**If warnings prompted refinement**: Use version suffix
```bash
bash /root/travel-planner/scripts/generate-and-deploy.sh {destination-slug} -v2
```

Script performs:
1. Auto-detects project type (itinerary vs bucket list)
2. Generates HTML using Python module
3. Immediately deploys to GitHub Pages
4. Returns live URL

**Exit codes**:
- 0: Success (HTML generated + deployed)
- 1: Generation failed
- 2: Deployment failed
- 3: Missing required files

**If authentication unavailable** (no GITHUB_TOKEN or SSH keys):
- Script will generate HTML locally only
- Warn user about missing authentication
- Provide instructions to enable deployment

#### Step 17: Verify Generation and Deployment

Check file exists locally:
```bash
test -f /root/travel-planner/travel-plan-{destination-slug}.html && echo "verified" || echo "missing"
```

**If missing**: Debug unified script, check agent JSON completeness

Verify deployment URL from script output (script will display live URL)

#### Step 18: Capture Live URL

Extract and save the live URL from deploy script output:
```
https://{username}.github.io/travel-planner-graph/{destination-slug}/{date}/
```

**This URL will be presented to user in Step 19.**

#### Step 19: Present Final Plan

**Generate Booking Checklist**:

Run checklist generator:
```bash
source /root/.claude/venv/bin/activate && python /root/travel-planner/scripts/generate-booking-checklist.py /root/travel-planner/data/{destination-slug}/timeline.json /root/travel-planner/data/{destination-slug}/budget.json
```

Capture output and include in presentation below.

**With deployment**:
```
Your personalized travel plan is ready!

📄 Saved to: `travel-plan-{destination-slug}.html`
🌐 Live URL: https://{username}.github.io/travel-planner-graph/{destination-slug}/

**Plan Summary**:
- 🌍 Destination: {destinations}
- 📅 Duration: {duration} days
- 💰 Total Budget: ${total}
- 🏨 {count} accommodation options
- 🍽️ Daily meal recommendations
- 🎯 {count} attractions and activities
- 📅 Hour-by-hour timeline
- 💵 Detailed budget breakdown

**Interactive Features**:
✓ Day-by-day collapsible sections
✓ Timeline with start/end times
✓ Side panel for emergency info
✓ Mobile-responsive design
✓ Budget tracking per day

---

**Booking Checklist** (from timeline/budget warnings):

{Insert booking checklist output here}

---

Open the HTML file locally or view online. Would you like any adjustments?
```

**Without deployment**:
```
Your personalized travel plan is ready!

📄 Saved to: `travel-plan-{destination-slug}.html`

[Same summary and features as above]

---

**Booking Checklist** (from timeline/budget warnings):

{Insert booking checklist output here}

---

Open the HTML file in any browser to view your complete travel plan.
```

---

### Phase 6: Refinement Loop

#### Step 20: Handle User Refinements

**CRITICAL**: This multi-turn refinement phase follows the same pattern as /ask command's Step 6 dialogue loop. Each refinement request must be parsed, classified, and delegated to specialist agents.

**Root Cause Reference**: Step 20 was too brief (11 lines), causing AI to skip proper agent delegation and manually research via WebSearch/Gaode Maps. This violates orchestration architecture where specialist agents handle all domain research.

---

**Substep: Wait for User Response**

After presenting the final plan (Step 20), wait for explicit user feedback.

**User satisfied signals**:
- "Perfect", "Great", "Thank you", "Looks good"
- No response needed after these → End gracefully with: "Enjoy your trip to {destination}!"

**User refinement signals**:
- Questions about specifics ("spa呢？哪一家？", "What about nightlife?")
- Change requests ("Change Day 3 dinner", "Add museum")
- Major restructure ("Change destination from X to Y")

**Only proceed to next substep if user provides refinement request**.

---

**Substep: Parse Refinement Request**

Extract structured information from user's refinement:

**Parse these elements**:
1. **Day scope**: Which day(s) are affected?
   - Example: "Day 3" → `day_scope = [3]`
   - Example: "All days" → `day_scope = [1, 2, 3, ..., N]`
   - Example: No day specified → Ask user: "Which day would you like to adjust?"

2. **Domain affected**: Which specialist agent's domain?
   - Keywords mapping:
     - "restaurant", "meal", "breakfast", "lunch", "dinner", "food" → meals-agent
     - "hotel", "accommodation", "lodging", "stay" → accommodation-agent
     - "attraction", "景点", "museum", "temple", "park" → attractions-agent
     - "nightlife", "spa", "entertainment", "娱乐", "bar", "club" → entertainment-agent
     - "shopping", "mall", "store", "购物" → shopping-agent
     - "train", "flight", "transportation", "transfer" → transportation-agent
   - Multiple domains possible (re-invoke multiple agents)

3. **Refinement nature**: New research needed or adjustment only?
   - **New research keywords**: "add", "include", "find", "research", "recommend", "呢", "哪一家"
   - **Adjustment keywords**: "change", "replace", "cheaper", "expensive", "remove"

**Output of this step**: `refinement_context` object
```json
{
  "user_request": "spa呢？哪一家？",
  "day_scope": [3],
  "domains": ["entertainment"],
  "nature": "new_research",
  "requires_agent_delegation": true
}
```

**If parsing is ambiguous, ask clarifying question before proceeding**.

---

**Substep: Classify Refinement Type**

Based on parsed `refinement_context`, classify into one of three types:

**Type 1 - Single Domain Refinement** (most common):
- **Criteria**: Affects 1-2 domains, day scope <= 3 days, requires research OR adjustment
- **Examples**:
  - "spa呢？哪一家？" → entertainment-agent for Day 3
  - "Change Day 2 lunch to vegetarian" → meals-agent for Day 2
  - "Add museum for Day 5" → attractions-agent for Day 5

**Type 2 - Major Restructure**:
- **Criteria**: Changes fundamental structure (location change, date change, traveler count change)
- **Examples**:
  - "Change Day 3 location from Beijing to Shanghai"
  - "Add 2 more days to the trip"
  - "Budget reduced from $3000 to $2000"

**Type 3 - Informational Query**:
- **Criteria**: No changes needed, user asking about existing data
- **Examples**:
  - "Is this restaurant vegetarian-friendly?"
  - "What time does the museum close?"
  - "How far is the hotel from the attraction?"

**Set refinement_type variable**: `Type1`, `Type2`, or `Type3`

---

**Substep: Handle Type 3 (Informational Query)**

**If refinement_type == Type3**:
1. Read relevant data from existing JSONs in `data/{destination-slug}/`
2. Answer user's question directly using available information
3. Do NOT re-invoke any agents
4. Return to Step 20 first substep (wait for next user response)

**Example**:
```
User: "Is this restaurant vegetarian-friendly?"
You: [Read meals.json] "Yes, {restaurant_name} on Day {N} offers vegetarian options including {dishes}."
```

**Then immediately return to first substep**.

---

**Substep: Build Refinement Context for Agent Delegation (Type 1)**

**⚠️ CRITICAL - DO NOT MANUALLY RESEARCH**:
- **NEVER** use WebSearch, WebFetch, or gaode-maps MCP tools yourself
- **NEVER** attempt to research specific venues, restaurants, or attractions
- **YOUR ROLE**: Parse user intent and delegate to specialist agents
- **SPECIALIST AGENT ROLE**: Perform all domain research using MCP tools

**If refinement_type == Type1**, build detailed context JSON for agent re-invocation:

**Context JSON structure**:
```json
{
  "refinement_request": {
    "original_user_text": "spa呢？哪一家？",
    "day_scope": [3],
    "date": "2026-03-17",
    "location": "Chongqing",
    "instruction": "Research spa options for Day 3 in Chongqing. User specifically asking for spa recommendations."
  },
  "existing_data": {
    "current_entertainment": [
      "Extract current entertainment items for Day 3 from entertainment.json"
    ],
    "budget_remaining": "Extract from budget.json Day 3 entertainment budget"
  },
  "constraints": {
    "budget_limit": 500,
    "user_preferences": "Extract from requirements-skeleton.json"
  }
}
```

**Save this context** to memory for next substep.

---

**Substep: Re-invoke Specialist Agent(s) with Day-Scoped Context (Type 1)**

**⚠️ CRITICAL - MANDATORY AGENT DELEGATION**:
This is THE MOST IMPORTANT step. Orchestrator MUST delegate research to specialist agents.

**ARCHITECTURAL PRINCIPLE**: Orchestrator coordinates, does NOT execute. All domain research and file modifications MUST be performed by specialist subagents via Task tool. Working files in `data/{destination-slug}/*.json` are specialist domains.

**For each domain in refinement_context.domains**:

**Re-invocation pattern**:
```
Use Task tool with:
- subagent_type: "{domain}-agent"  # e.g., "entertainment-agent"
- description: "Refinement: {user_request} for Day {N}"
- model: "sonnet"
- prompt: "
  **REFINEMENT REQUEST** (Day-scoped):

  User refinement: {user's original text, e.g., 'spa呢？哪一家？'}

  Focus ONLY on: Day {N}, Date {date}, Location {location}

  Read existing data from:
  - data/{destination-slug}/requirements-skeleton.json
  - data/{destination-slug}/plan-skeleton.json
  - data/{destination-slug}/{domain}.json (your previous output)
  - data/{destination-slug}/budget.json (for budget constraints)

  **YOUR TASK**:
  1. Research NEW options to address user's refinement
     - Use MCP tools: google-maps, gaode-maps, rednote, etc.
     - DO NOT use placeholder data
  2. Update {domain}.json for Day {N} only
     - APPEND new items OR REPLACE existing items as appropriate
     - Preserve data for other days
  3. After completing all tasks, return ONLY the word 'complete'

  **SPECIFIC INSTRUCTION**: {instruction from refinement_context}

  Budget constraint for Day {N}: {budget_limit}
  User preferences: {preferences from requirements-skeleton.json}
  "
```

**Wait for agent to return "complete"**.

**Verification**: Confirm file updated before proceeding:
```bash
test -f /root/travel-planner/data/{destination-slug}/{domain}.json && echo "{domain}.json verified" || echo "{domain}.json missing"
```

**Example agent delegation**:
```
User: "spa呢？哪一家？"
Your action:
→ Task tool (entertainment-agent)
   - "Research spa options for Day 3 in Chongqing"
   - Agent uses gaode-maps, rednote to find spas
   - Agent updates entertainment.json with spa recommendations
   - Agent returns "complete"
```

**⚠️ VERIFICATION CHECKPOINT**:
- [ ] Did you invoke Task tool with appropriate specialist agent?
- [ ] Did you include day-scoped context (Day N, date, location)?
- [ ] Did you specify the domain-specific instruction?
- [ ] Did you wait for agent to return "complete"?

**If ANY checkbox unchecked → You violated orchestration architecture. Stop and re-invoke agent correctly.**

---

**Substep: Re-invoke Dependent Agents (timeline, budget)**

After specialist agent(s) complete refinement, **ALWAYS re-invoke dependent agents**:

**Re-invoke timeline-agent**:
```
Use Task tool with:
- subagent_type: "timeline-agent"
- description: "Recalculate timeline after refinement"
- model: "sonnet"
- prompt: "
  Re-read ALL agent outputs:
  - data/{destination-slug}/meals.json
  - data/{destination-slug}/entertainment.json (UPDATED)
  - [all other domain JSONs]

  Recalculate timeline for Day {N} only (or all days if multiple domains affected).

  **CRITICAL - Save JSON to: data/{destination-slug}/timeline.json**
  Use Write tool explicitly (see timeline.md Step 3).
  Root Cause Reference (commit ef0ed28): Explicit Write prevents timeline data loss.

  After completing all tasks, return ONLY the word 'complete'.
  "
```

**Re-invoke budget-agent**:
```
Use Task tool with:
- subagent_type: "budget-agent"
- description: "Recalculate budget after refinement"
- model: "sonnet"
- prompt: "
  Re-read ALL agent outputs including updated timeline.
  Recalculate budget for Day {N}.
  Update data/{destination-slug}/budget.json

  After completing all tasks, return ONLY the word 'complete'.
  "
```

**Wait for both agents to return "complete"**.

**Verification - Root Cause Reference (commit ef0ed28)**: File-based pipeline requires verification.

**Step 1**: Confirm files exist:
```bash
test -f /root/travel-planner/data/{destination-slug}/timeline.json && echo "timeline.json verified" || echo "timeline.json missing"
test -f /root/travel-planner/data/{destination-slug}/budget.json && echo "budget.json verified" || echo "budget.json missing"
```

**Step 2**: Read and verify timeline.json content (equity-analyst pattern):
```bash
Read data/{destination-slug}/timeline.json
```

Verify affected day timelines are populated (not empty dictionaries).

---

**Substep: Regenerate HTML with Version Suffix**

Increment version counter (track internally: v2, v3, etc.)

Run generation script:
```bash
bash /root/travel-planner/scripts/generate-travel-html.sh {destination-slug} -v{version}
```

**Example**: Second refinement → `travel-plan-{destination-slug}-v2.html`

Verify file exists:
```bash
test -f /root/travel-planner/travel-plan-{destination-slug}-v{version}.html && echo "verified" || echo "missing"
```

**If missing**: Debug and retry.

---

**Substep: Present Updated Plan to User**

Show what changed:
```
Updated your travel plan based on your refinement!

**Changes Made** (Day {N}):
- {Domain}: {Specific changes, e.g., "Added 3 spa options"}
- Timeline: {Updated timeline for affected activities}
- Budget: {Updated budget impact, e.g., "+$50 for spa activities"}

📄 New version saved: `travel-plan-{destination-slug}-v{version}.html`

**Updated Day {N} Summary**:
{Show relevant excerpts from updated JSONs for this day}

---

Would you like any further adjustments?
```

**After presenting**, return to first substep (wait for next user response).

**Iteration limit**: Max 3 major refinements. After 3rd refinement, suggest accepting current state.

---

**Substep: Handle Type 2 (Major Restructure)**

**If refinement_type == Type2**:

Major restructures require re-running entire Phase 2-5 workflow.

**Action sequence**:
1. Update `data/{destination-slug}/requirements-skeleton.json` with new constraints
2. Return to Step 6 (Initialize Plan Skeleton) with updated requirements
3. Re-invoke ALL 8 agents (parallel 6, then serial timeline + budget)
4. Run all validation scripts
5. Generate HTML with version suffix
6. Present complete updated plan

**Example**:
```
User: "Change Day 3 location from Beijing to Shanghai"

Your action:
1. Edit requirements-skeleton.json → Day 3 location = "Shanghai"
2. Re-run Step 6 (plan skeleton initialization with location detection)
3. Re-run Step 8 (invoke all 6 parallel agents + timeline + budget)
4. Re-run Steps 9-13 (validations)
5. Generate HTML v2
6. Present full updated plan
```

**After completion**, return to first substep.

---

**Substep: Dialogue Length Protection**

Track refinement iterations internally (no user-facing counter).

**Turn 3 refinement**: Gentle reminder
```
We've made several refinements. Current version: v3.

I recommend reviewing the updated plan before additional changes to ensure everything aligns with your vision. Would you like to:
1. Review the current plan as final
2. Make one more refinement
3. Start over with new requirements
```

**Hard limit**: After 3 refinements, strongly suggest accepting current state or starting fresh.

