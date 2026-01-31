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

#### Step 4: Validate Day Completion

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

#### Step 5: Initialize Plan Skeleton

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

#### Step 6: Validate Location Continuity

Run validation script:
```bash
bash /root/travel-planner/scripts/check-location-continuity.sh {destination-slug}
```

**Exit code 0**: All location changes have objects → Proceed
**Exit code 1**: Missing location_change objects → Fix and retry

---

### Phase 3: Specialist Agent Execution

#### Step 7: Invoke Parallel Agents (6 agents simultaneously)

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

#### Step 8: Verify Agent Outputs

Check all files exist:
```bash
cd /root/travel-planner/data/{destination-slug} && ls -1 *.json | grep -E '(meals|accommodation|attractions|entertainment|shopping|transportation)\.json'
```

Expected: 6 files (or 5 if no location changes → transportation.json may be empty)

If any missing: Debug and re-invoke failed agent.

#### Step 9: Invoke Timeline Agent (Serial)

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

#### Step 10: Validate Timeline Consistency

Run validation script:
```bash
bash /root/travel-planner/scripts/validate-timeline-consistency.sh {destination-slug}
```

**Exit code 0**: Timeline valid → Proceed
**Exit code 1**: Validation errors (mismatched keys, conflicts) → Review timeline.json warnings

#### Step 11: Invoke Budget Agent (Serial)

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

---

### Phase 4: Validation and Conflict Review

#### Step 12: Day-by-Day Refinement Loop

Read warnings from:
- `data/{destination-slug}/timeline.json` → Check `warnings` array
- `data/{destination-slug}/budget.json` → Check `warnings` and `recommendations` arrays

**If no warnings**: Proceed to Phase 5

**If warnings exist**: Iterate through days with conflicts

**Day Iteration Pattern**:
1. Group warnings by day number
2. Initialize tracking: `days_reviewed = []`, `days_pending = [list of days with warnings]`
3. For each day in `days_pending` (sequential, NOT all at once):
   - Extract warnings for current day only
   - Present ONLY current day's warnings to user
   - Offer options: Auto-fix | Manual adjustment | Skip day | Accept all remaining
   - Process user choice (see Step 13)
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

#### Step 13: Handle Day-Scoped Refinement

**For each day being refined** (one at a time from Step 12):

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
- Return to Step 12 day iteration loop
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

#### Step 14: Generate Interactive HTML

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

#### Step 15: Verify HTML Generated

Check file exists:
```bash
test -f /root/travel-planner/travel-plan-{destination-slug}.html && echo "verified" || echo "missing"
```

**If missing**: Debug script, check agent JSON completeness

#### Step 16: Optional Deployment

Attempt GitHub Pages deployment:
```bash
if [ -n "$GITHUB_TOKEN" ] || [ -f ~/.ssh/id_ed25519 ]; then
  bash /root/travel-planner/scripts/deploy-travel-plans.sh /root/travel-planner/travel-plan-{destination-slug}.html
fi
```

**If succeeds**: Capture live URL
**If fails**: Silent graceful degradation (local file only)

#### Step 17: Present Final Plan

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

Open the HTML file locally or view online. Would you like any adjustments?
```

**Without deployment**:
```
Your personalized travel plan is ready!

📄 Saved to: `travel-plan-{destination-slug}.html`

[Same summary and features as above]

Open the HTML file in any browser to view your complete travel plan.
```

---

### Phase 6: Refinement Loop

#### Step 18: Handle User Refinements

**User satisfied**: End gracefully

**User requests changes**: Determine scope

**Type 1 - Specific agent changes (including new research)**:
```
Supports:
- Adjusting existing recommendations ("Change Day {N} dinner to cheaper option")
- Adding NEW requirements that need research ("Add museum for Day {N}", "Research nightlife for Day {N}")
- Any change within a single domain (meals, attractions, entertainment, shopping, accommodation, transportation)

Example: "Add more {category} {items} for Day {N}"
Action:
1. Re-invoke relevant specialist agent with refinement context
   - Agent can perform NEW research for added requirements
   - All 8 specialist agents available: meals, accommodation, attractions, entertainment, shopping, transportation, timeline, budget
2. Re-invoke timeline-agent (depends on modified agent)
3. Re-invoke budget-agent (depends on timeline)
4. Re-run validations
5. Regenerate HTML with -v2 suffix
6. Present updated plan

Note: Specialist agents research using MCP skills (google-maps, gaode-maps, rednote, etc.), not orchestrator
```

**Type 2 - Major restructure**:
```
Example: "Change Day {N} location from {City A} to {City B}"
Action:
1. Update requirements-skeleton.json
2. Re-init plan-skeleton.json (Step 5)
3. Re-invoke ALL 8 agents
4. Run all validations
5. Generate new HTML with -v2 suffix
6. Present updated plan
```

**Type 3 - Questions only**:
```
Example: "Is this restaurant good for vegetarians?"
Action:
- Answer from existing data
- No agent re-invocation needed
```

**Versioning**: `-v2`, `-v3`, etc.
**Max iterations**: 3 major revisions

