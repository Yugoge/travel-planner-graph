---
description: "Multi-day iterative review command with incremental workflow"
name: review
allowed-tools: Task, Read, Write, TodoWrite, Bash, Skill
argument-hint: "<plan-id> [--day N] [--force-images]"
model: inherit
---

**⚠️ CRITICAL**: Use TodoWrite to track workflow phases. Mark in_progress before each phase, completed immediately after.

# Review Command

Iterative day-by-day review and refinement workflow for existing travel plans.

**IMPORTANT**: This command reads an **already existing plan** and performs manual day-by-day review. It does NOT create new plans - only refines existing ones.

## Usage

```
/review <plan-id> [--day N] [--force-images]
```

## Arguments

- `plan-id`: Plan identifier (e.g., `china-feb-15-mar-7-2026-20260202-195429`)
- `--day N`: Start from specific day (default: 1)
  - Can skip days by using `--day` multiple times: `--day 1 --day 3 --day 5`
- `--force-images`: Force refetch all POI images before review

## Key Differences from /plan Command

1. **No Phase 1-3**: Skip requirement collection, skeleton generation, validation
   - **Assumes plan already exists**: Works with existing `data/{destination-slug}/plan-skeleton.json`

2. **No Phase 4 (Validation & Optimization)**: Skip automated optimization loops
   - **Focus on manual refinement**: User provides day-specific feedback

3. **No Step 16-18 (Auto Deploy)**: Deployment is manual
   - **Only generates HTML locally**: User deploys manually when ready

4. **Iterative workflow**:
   - **Start from day 1**: Automatically advances day-by-day
   - **Manual progression**: User controls when to move to next day
   - **State tracking**: Remembers current day and iteration count per day


## Orchestrator Discipline

**NON-NEGOTIABLE RULES — Zero Exceptions:**

1. **You are an orchestrator. You do NOT execute.**
   - NEVER use WebSearch, WebFetch, gaode-maps, google-maps, rednote, or any research MCP tool directly
   - NEVER use Edit/Write tools on data files in `data/{destination-slug}/`
   - NEVER look up restaurants, attractions, shops, hotels, or transport options yourself

2. **ALL research goes through subagents.**
   - Need restaurant info? → Dispatch meals-agent via Task tool
   - Need attraction info? → Dispatch attractions-agent via Task tool
   - Need shopping/brand info? → Dispatch shopping-agent via Task tool
   - Need entertainment info? → Dispatch entertainment-agent via Task tool
   - Need transport info? → Dispatch transportation-agent via Task tool
   - Need accommodation info? → Dispatch accommodation-agent via Task tool
   - Need general research? → Dispatch deep-search or Explore agent via Task tool

3. **ALL file modifications go through owning subagents.**
   - meals.json → meals-agent only
   - attractions.json → attractions-agent only
   - entertainment.json → entertainment-agent only
   - shopping.json → shopping-agent only
   - accommodation.json → accommodation-agent only
   - transportation.json → transportation-agent only
   - timeline.json → timeline-agent only
   - budget.json → budget-agent only

4. **Your ONLY permitted actions:**
   - Read files (to coordinate and present to user)
   - Run validation/generation scripts via Bash
   - Dispatch subagents via Task tool
   - Present information to user
   - Parse user intent and delegate

5. **Self-check before every tool call:**
   - "Am I about to research something?" → If yes, delegate to subagent
   - "Am I about to modify a data file?" → If yes, delegate to owning subagent
   - "Am I using WebSearch/WebFetch/MCP tools?" → If yes, STOP and delegate

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

Load todos from: `scripts/todo/review.py`

```bash
source /root/.claude/venv/bin/activate && python /root/travel-planner/scripts/todo/review.py
```

Use output to create TodoWrite with all workflow steps.

**Rules**: Mark `in_progress` before each step, `completed` after. NEVER skip steps.

---

### Step 1: Parse Starting Day

**Extract from `$ARGUMENTS`**:
   - If `--day N` provided: start from day N
   - If no `--day`: start from day 1

**Example**:
```
# User: "/review china-trip --day 5"
# → Start reviewing from Day 5
# User: "/review china-trip"
# → Start reviewing from Day 1
```

---

### Step 2: Load Plan Data

Read existing plan:
```bash
# Read plan skeleton
test -f data/{destination-slug}/plan-skeleton.json && echo "verified" || echo "missing"

# Read all agent outputs
test -f data/{destination-slug}/meals.json && echo "meals.json verified" || echo "meals.json missing"
test -f data/{destination-slug}/attractions.json && echo "attractions.json verified" || echo "attractions.json missing"
test -f data/{destination-slug}/entertainment.json && echo "entertainment.json verified" || echo "entertainment.json missing"
test -f data/{destination-slug}/shopping.json && echo "shopping.json verified" || echo "shopping.json missing"
test -f data/{destination-slug}/accommodation.json && echo "accommodation.json verified" || echo "accommodation.json missing"
```

**Verification**:
   - All required files must exist before proceeding
   - If any file missing: Error and exit

---

### Phase 4: Validation and Conflict Review



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
    1. Extract current day data from all agent JSONs (see extraction method below)
    2. Validate extraction completeness (see validation below)
    3. Present COMPLETE day plan (MANDATORY format below)
    4. Offer user options (see below)
    5. Process user choice:
       - "This day is perfect" → Set day_confirmed_perfect = true, exit INNER loop
       - "Make changes to Day N" → Re-invoke agents (Step 15), stay in INNER loop
       - "Accept all remaining" → Exit both loops, proceed to Phase 5
    6. If changes made: Re-present Day N (loop continues)
```

**Step 1: Extract Current Day Data from Agent JSONs**

**Root Cause Reference**: Line 357 lacked extraction method specification, causing AI to default to Read with limit:100, truncating structured JSON day data beyond line 100. This caused critical omissions (drone show at lines 107-111) and complete data loss for Day 2-21.

**CRITICAL - Data Extraction Method**: You MUST use ONE of these two approaches to extract complete day data:

**Approach 1 - jq-based extraction (RECOMMENDED for large files)**:
```bash
# Extract Day N timeline data
jq --arg day "$current_day_index" '.timeline[$day | tonumber - 1]' /root/travel-planner/data/{destination-slug}/timeline.json > /tmp/day-${current_day_index}-timeline.json

# Extract Day N meals data
jq --arg day "$current_day_index" '.days[$day | tonumber - 1].meals' /root/travel-planner/data/{destination-slug}/meals.json > /tmp/day-${current_day_index}-meals.json

# Extract Day N attractions data
jq --arg day "$current_day_index" '.days[$day | tonumber - 1].attractions' /root/travel-planner/data/{destination-slug}/attractions.json > /tmp/day-${current_day_index}-attractions.json

# Extract Day N entertainment data
jq --arg day "$current_day_index" '.days[$day | tonumber - 1].entertainment' /root/travel-planner/data/{destination-slug}/entertainment.json > /tmp/day-${current_day_index}-entertainment.json

# Extract Day N shopping data
jq --arg day "$current_day_index" '.days[$day | tonumber - 1].shopping' /root/travel-planner/data/{destination-slug}/shopping.json > /tmp/day-${current_day_index}-shopping.json

# Extract Day N budget data
jq --arg day "$current_day_index" '.days[$day | tonumber - 1]' /root/travel-planner/data/{destination-slug}/budget.json > /tmp/day-${current_day_index}-budget.json
```

Then read the extracted day-specific JSON files:
```bash
Read /tmp/day-${current_day_index}-timeline.json  # Complete day data, no limit
Read /tmp/day-${current_day_index}-meals.json
Read /tmp/day-${current_day_index}-attractions.json
Read /tmp/day-${current_day_index}-entertainment.json
Read /tmp/day-${current_day_index}-shopping.json
Read /tmp/day-${current_day_index}-budget.json
```

**Approach 2 - Read complete file without limit**:
```bash
Read /root/travel-planner/data/{destination-slug}/timeline.json  # NO limit parameter
Read /root/travel-planner/data/{destination-slug}/meals.json     # NO limit parameter
Read /root/travel-planner/data/{destination-slug}/attractions.json
Read /root/travel-planner/data/{destination-slug}/entertainment.json
Read /root/travel-planner/data/{destination-slug}/shopping.json
Read /root/travel-planner/data/{destination-slug}/budget.json
```

Then manually extract Day N data from the complete JSON.

**PROHIBITED - Do NOT use these patterns**:
```bash
# ❌ WRONG - Truncates at line 100, causes data loss
Read /root/travel-planner/data/{destination-slug}/timeline.json offset:0 limit:100

# ❌ WRONG - Arbitrary limit truncates structured JSON
Read /root/travel-planner/data/{destination-slug}/timeline.json limit:200

# ❌ WRONG - Any Read with limit for day extraction
Read /root/travel-planner/data/{destination-slug}/timeline.json limit:N
```

**Why limit is prohibited for structured JSON day extraction**:
- Agent JSONs contain 21 days of data (1475+ lines for timeline.json)
- Day 1 data may span lines 10-122 (drone show at 107-111)
- Day 2 starts around line 150 (BEYOND limit:100)
- Using limit:100 completely omits Day 1 drone show and ALL of Day 2-21
- Structured JSON requires complete object extraction, not arbitrary line truncation

**Step 2: Validate Extraction Completeness**

**CRITICAL - Validation checkpoint before presentation**:

After extracting Day N data, verify ALL timeline entries for that day are present:

```bash
# Count timeline entries for Day N
timeline_entry_count=$(jq --arg day "$current_day_index" '.timeline[$day | tonumber - 1] | length' /root/travel-planner/data/{destination-slug}/timeline.json)

echo "Day ${current_day_index} has ${timeline_entry_count} timeline entries"
```

**Validation criteria**:
- Timeline entry count MUST be > 0
- If timeline_entry_count == 0: Extraction failed, debug and retry
- Typical day has 8-12 timeline entries (meals + attractions + entertainment + travel segments)
- If count seems low (< 5): Manually verify extraction captured all activities

**Example validation output**:
```
Day 1 has 11 timeline entries  ✓ PASS
Day 2 has 0 timeline entries   ✗ FAIL - Extraction error, re-extract
Day 3 has 9 timeline entries   ✓ PASS
```

**If validation fails**:
1. Check jq filter syntax
2. Verify day index (1-indexed in UI, 0-indexed in JSON arrays)
3. Read complete timeline.json without limit to inspect structure
4. Do NOT proceed to presentation until validation passes

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
source venv/bin/activate || source .venv/bin/activate && python3 /root/travel-planner/scripts/plan-validate.py /root/travel-planner/data/{destination-slug} --agent {agent_name}
```

**Exit code 0**: Changes valid → Proceed to next substep
**Exit code 1**: Validation errors → Review and fix before proceeding

---

**Substep: Re-sync Agent Data After Refinement**

After timeline/budget agents update, re-sync all agent times:
```bash
source /root/.claude/venv/bin/activate && python /root/travel-planner/scripts/sync-agent-data.py {destination-slug} --skip-html
```

This ensures agent JSONs stay synchronized with updated timeline after each refinement cycle.

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

#### Step 16: Final Data Sync Before HTML Generation

**MANDATORY**: Run final sync to ensure all agent data is synchronized with timeline before HTML generation. This sync also regenerates the HTML automatically.

```bash
source /root/.claude/venv/bin/activate && python /root/travel-planner/scripts/sync-agent-data.py {destination-slug}
```

Note: This run includes HTML regeneration (no `--skip-html` flag). Check sync-report.json for any remaining unmatched items.

#### Step 17: Plan Validation Gate (MANDATORY)

**CRITICAL**: After all agents complete and data is synced, run the plan validation script as a final quality gate before HTML generation. This ensures all agent outputs meet structural and content requirements.

```bash
source venv/bin/activate && python /root/travel-planner/scripts/plan-validate.py /root/travel-planner/data/{destination-slug}
```

**Exit code 0 (PASS)**: Validation passed. Proceed to Step 16 (HTML generation).

**Exit code 1 (FAIL)**: Validation failed. Critical issues found.
- Read the script output to identify which agents produced invalid data
- Re-dispatch the failing agent(s) via Task tool with specific fix instructions from the validation errors
- After agents fix their outputs, re-run the validation script
- Do NOT proceed to Step 16 until validation passes (exit code 0)

**Loop until exit code 0**: This step is a hard gate. HTML generation must not begin with invalid agent data.

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
bash /root/travel-planner/scripts/generate-html.sh {destination-slug} -v{version}
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
1. Update skeleton files via script (orchestrator NEVER edits data files directly):
   ```bash
   source /root/.claude/venv/bin/activate && python /root/travel-planner/scripts/update-skeleton.py \
     --destination-slug {destination-slug} \
     <operation-flags>
   ```
   Supported operations:
   - `--update-day N --location "City"` — change day location (auto re-detects location_change)
   - `--update-day N --add-plan "Activity"` — add user plan
   - `--update-day N --remove-plan "Activity"` — remove user plan (partial match)
   - `--update-day N --set-plans '["Plan A", "Plan B"]'` — replace all plans
   - `--update-budget "$2000"` / `--update-travelers "3 adults"` / `--update-preferences '{...}'` — update trip summary
   - `--add-day --day N --date "YYYY-MM-DD" --location "City" --plans '[...]'` — extend trip
   - `--remove-day N` — shorten trip (auto re-numbers)
2. Return to Step 6 (Verify Plan Skeleton) with updated requirements
3. Re-invoke ALL 8 agents (parallel 6, then serial timeline + budget)
4. Run all validation scripts
5. Generate HTML with version suffix
6. Present complete updated plan

**Example**:
```
User: "Change Day 3 location from Beijing to Shanghai"

Your action:
1. python scripts/update-skeleton.py --destination-slug {slug} --update-day 3 --location "Shanghai"
2. Re-run Step 6 (verify plan skeleton with updated location changes)
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

