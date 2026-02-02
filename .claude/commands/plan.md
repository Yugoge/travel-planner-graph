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

Save to: `data/{destination-slug}/requirements-skeleton.json`

Format:
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

#### Step 6: Initialize Plan Skeleton

Read `requirements-skeleton.json`, detect location changes, create plan skeleton with all fields initialized, save to `data/{destination-slug}/plan-skeleton.json`.

Run location change detection:
```bash
/root/travel-planner/scripts/detect-location-changes.py /root/travel-planner/data/{destination-slug}/plan-skeleton.json
```

Plan skeleton structure:
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
  Save to: data/{destination-slug}/meals.json

  Return ONLY: complete
  "
```

**Each agent**:
- Reads requirements and plan skeleton
- Performs domain-specific research using available MCP skills (google-maps, gaode-maps, rednote, etc.)
- Saves structured data to `data/{destination-slug}/{agent-name}.json`
- Returns ONLY: `complete`

**Wait for all 6 agents to return "complete"**.

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

#### Step 10: Invoke Timeline Agent (Serial)

**IMPORTANT**: Timeline agent runs AFTER all parallel agents complete.

```
Use Task tool with:
- subagent_type: "timeline-agent"
- description: "Create timeline dictionary and detect conflicts"
- model: "sonnet"
- prompt: "
  Read ALL agent outputs:
  - data/{destination-slug}/plan-skeleton.json
  - data/{destination-slug}/meals.json
  - data/{destination-slug}/accommodation.json
  - data/{destination-slug}/attractions.json
  - data/{destination-slug}/entertainment.json
  - data/{destination-slug}/shopping.json
  - data/{destination-slug}/transportation.json

  Create timeline as DICTIONARY:
  - Keys: EXACT activity names from source JSONs
  - Values: {start_time: 'HH:MM', end_time: 'HH:MM', duration_minutes: N}

  Detect conflicts: overlapping times, unrealistic travel, tight schedules.

  Save to: data/{destination-slug}/timeline.json

  Return ONLY: complete
  "
```

Wait for "complete".

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

  Return ONLY: complete
  "
```

Wait for "complete".

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

**Note on Step 13**: Previously Step 11.5, renumbered to enforce integer-only step numbering (no decimal steps per dev agent standards).

---

### Phase 4: Validation and Conflict Review

#### Step 14: Day-by-Day Refinement Loop

Read warnings from:
- `data/{destination-slug}/timeline.json` → Check `warnings` array
- `data/{destination-slug}/budget.json` → Check `warnings` and `recommendations` arrays

**Check force_review flag** (set in Step 13 by budget gate)

**If no warnings AND force_review=false**: Proceed to Phase 5

**If warnings exist OR force_review=true**: Iterate through days with conflicts
- When `force_review=true`, user CANNOT skip review (budget gate enforcement)
- Present clear explanation: "Budget exceeds thresholds (see Step 13), day-by-day review is required"

**Day Iteration Pattern**:
1. Group warnings by day number
2. Initialize tracking: `days_reviewed = []`, `days_pending = [list of days with warnings]`
3. For each day in `days_pending` (sequential, NOT all at once):
   - Extract warnings for current day only
   - Present ONLY current day's warnings to user
   - Offer options: Auto-fix | Manual adjustment | Skip day | Accept all remaining
   - Process user choice (see Step 15)
   - If not "Accept all": mark day reviewed, continue to next day
   - If "Accept all": exit loop, proceed to Phase 5
4. When all days reviewed or accepted: proceed to Phase 5

**Example Day Presentation** (present ONE day at a time):
```
**Day {N} Review** ({X} conflicts found):

Timeline:
- {Activity A} ({start_time}-{end_time}) overlaps {Activity B} ({start_time}-{end_time})

Budget:
- {Item} exceeds daily budget by {currency}{amount}

Recommendation: {Specific recommendation based on conflicts}

Options:
1. Auto-fix based on recommendation
2. Tell me your preferred adjustment
3. Skip Day {N} (review later)
4. Accept all remaining days as-is
```

**After resolving Day {N}, present Day {N+1}** (if it has warnings):
```
**Day {N+1} Review** ({X} conflicts found):

Timeline:
- {Conflict description}

Recommendation: {Specific recommendation}

Options:
1. Auto-fix based on recommendation
2. Tell me your preferred adjustment
3. Skip Day {N+1} (review later)
4. Accept all remaining days as-is
```

**Continue until all days reviewed or user accepts remaining**.

#### Step 15: Handle Day-Scoped Refinement

**For each day being refined** (one at a time from Step 14):

Parse user choice:

**Option 1 - Auto-fix**:
- Extract day-specific recommendations from timeline.json and budget.json
- Re-invoke relevant agents with day filter and specific instructions
- Example prompt addition: "Focus ONLY on Day {N} (date {date}). Apply recommendation: {specific_recommendation}"

**Option 2 - Manual adjustment**:
- Parse user's specific adjustment request
- Re-invoke agents with user's instructions scoped to current day
- Example: "Change Day {N} {meal} to {dietary_preference} restaurant under {budget_limit}"

**Option 3 - Skip day**:
- Mark current day as skipped in tracking: `days_skipped.append(current_day)`
- Continue to next day in `days_pending`
- User can review skipped days later

**Option 4 - Accept all remaining**:
- Exit refinement loop immediately
- Proceed to Phase 5 with current state

**Re-invocation Pattern with Day Scope**:
```
Use Task tool with day filter:
- subagent_type: relevant agent (meals-agent, timeline-agent, etc.)
- prompt includes: "Focus ONLY on Day {N}, date {date}. {specific_instruction}"
- Agent modifies only that day's data in their JSON file
- Agent returns "complete"
- Re-run validation scripts for that day only
- Return to Step 14 day iteration loop
```

**Tracking State**:
- `days_reviewed`: Successfully processed days
- `days_pending`: Days with warnings not yet reviewed
- `days_skipped`: Days user chose to skip
- `iteration_count`: Limit to 3 major refinement iterations per day

**Exit Conditions**:
- All days in `days_pending` reviewed or skipped
- User selects "Accept all remaining"
- `iteration_count` exceeds 3 for current day (warn user, suggest accepting)

---

### Phase 5: HTML Generation

#### Step 16: Generate Interactive HTML

Run generation script:
```bash
bash /root/travel-planner/scripts/generate-travel-html.sh {destination-slug}
```

Script merges all agent JSONs and generates: `travel-plan-{destination-slug}.html`

**If warnings prompted refinement**: Use version suffix
```bash
bash /root/travel-planner/scripts/generate-travel-html.sh {destination-slug} -v2
```

Output: `travel-plan-{destination-slug}-v2.html`

#### Step 17: Verify HTML Generated

Check file exists:
```bash
test -f /root/travel-planner/travel-plan-{destination-slug}.html && echo "verified" || echo "missing"
```

**If missing**: Debug script, check agent JSON completeness

#### Step 18: Optional Deployment

Attempt GitHub Pages deployment:
```bash
if [ -n "$GITHUB_TOKEN" ] || [ -f ~/.ssh/id_ed25519 ]; then
  bash /root/travel-planner/scripts/deploy-travel-plans.sh /root/travel-planner/travel-plan-{destination-slug}.html
fi
```

**If succeeds**: Capture live URL
**If fails**: Silent graceful degradation (local file only)

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

**Step 20.1: Wait for User Response**

After presenting the final plan (Step 19), wait for explicit user feedback.

**User satisfied signals**:
- "Perfect", "Great", "Thank you", "Looks good"
- No response needed after these → End gracefully with: "Enjoy your trip to {destination}!"

**User refinement signals**:
- Questions about specifics ("spa呢？哪一家？", "What about nightlife?")
- Change requests ("Change Day 3 dinner", "Add museum")
- Major restructure ("Change destination from X to Y")

**Only proceed to Step 20.2 if user provides refinement request**.

---

**Step 20.2: Parse Refinement Request**

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

**Step 20.3: Classify Refinement Type**

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

**Step 20.4: Handle Type 3 (Informational Query)**

**If refinement_type == Type3**:
1. Read relevant data from existing JSONs in `data/{destination-slug}/`
2. Answer user's question directly using available information
3. Do NOT re-invoke any agents
4. Return to Step 20.1 (wait for next user response)

**Example**:
```
User: "Is this restaurant vegetarian-friendly?"
You: [Read meals.json] "Yes, {restaurant_name} on Day {N} offers vegetarian options including {dishes}."
```

**Then immediately return to Step 20.1**.

---

**Step 20.5: Build Refinement Context for Agent Delegation (Type 1)**

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

**Save this context** to memory for use in Step 20.6.

---

**Step 20.6: Re-invoke Specialist Agent(s) with Day-Scoped Context (Type 1)**

**⚠️ CRITICAL - MANDATORY AGENT DELEGATION**:
This is THE MOST IMPORTANT step. Orchestrator MUST delegate research to specialist agents.

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
  3. Return ONLY: complete

  **SPECIFIC INSTRUCTION**: {instruction from refinement_context}

  Budget constraint for Day {N}: {budget_limit}
  User preferences: {preferences from requirements-skeleton.json}
  "
```

**Wait for agent to return "complete"**.

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

**Step 20.7: Re-invoke Dependent Agents (timeline, budget)**

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
  Update data/{destination-slug}/timeline.json

  Return ONLY: complete
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

  Return ONLY: complete
  "
```

**Wait for both agents to return "complete"**.

---

**Step 20.8: Regenerate HTML with Version Suffix**

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

**Step 20.9: Present Updated Plan to User**

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

**After presenting**, return to Step 20.1 (wait for next user response).

**Iteration limit**: Max 3 major refinements. After 3rd refinement, suggest accepting current state.

---

**Step 20.10: Handle Type 2 (Major Restructure)**

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

**After completion**, return to Step 20.1.

---

**Step 20.11: Dialogue Length Protection**

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

