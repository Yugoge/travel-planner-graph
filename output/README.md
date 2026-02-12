# output

Final deployment directory for generated HTML travel plans.

---

## Purpose

This folder stores the final deployed HTML travel plans ready for viewing or publishing. Contains both root-level HTML files and a `travel-plan-data/` subdirectory for timestamped versions.

**Use case**: User-accessible HTML travel plans with interactive features.

## Allowed File Types

- `.html` files ONLY
- NO other formats (.md, .json, etc.)
- Exception: This README.md and INDEX.md for documentation

## Naming Convention

- **Root HTML files**: `travel-plan-{destination-slug}.html`
  - Example: `travel-plan-china-feb-15-mar-7-2026-20260202-195429.html`
  - Format: `travel-plan-{slug}-{timestamp}.html`
- **travel-plan-data/ subdirectory**: Timestamped HTML files
  - Same naming pattern as root
  - Purpose: Versioned backup of deployed plans

## Organization Rules

### Directory Structure

```
output/
├── travel-plan-{trip1}.html       # Latest version
├── travel-plan-{trip2}.html       # Latest version
├── travel-plan-data/              # Versioned backups
│   ├── beijing-exchange-bucket-list-YYYYMMDD-HHMMSS.html
│   └── china-feb-15-mar-7-2026-YYYYMMDD-HHMMSS.html
├── README.md                      # This file
└── INDEX.md                       # Auto-generated inventory
```

### File Responsibilities

**Root-level HTML files**:
- Primary user-accessible travel plans
- Features: Interactive timeline, bilingual toggle, POI cards, embedded maps
- Generated: By `scripts/generate-html-interactive.py`
- Updated: Overwritten on each deployment (latest version)
- Size: 300KB - 1MB depending on trip complexity

**travel-plan-data/ subdirectory**:
- Timestamped versions of deployed HTML
- Purpose: Version history and backup
- Created: By deployment scripts when copying from staging directories
- NOT overwritten: Each deployment creates new timestamped file

### Deployment Workflow

1. **Stage**: HTML generated in trip-specific folders (e.g., `china-feb-15-mar-7-2026/`)
2. **Deploy**: Scripts copy to `output/travel-plan-data/` with timestamp
3. **Update**: Latest version copied to root `output/` (overwrites existing)
4. **Commit**: Auto-commit with deployment message

## File Creation Patterns

Based on Git history:

**Created by**: Automated deployment scripts
**Timeframe**: Feb 8-11, 2026 (active)
**Automation**: 100% automated (script-generated)
**Update frequency**: High (multiple times daily during active planning)

**Pattern**:
1. Data updated in `data/` directory (JSON modifications)
2. HTML generated: `python scripts/generate-html-interactive.py`
3. Deployed to output: Timestamped copy to `travel-plan-data/`, latest to root
4. Commit message: "checkpoint: Auto-save at {timestamp}" or "Update China trip HTML"

**Recent commits**:
- 2026-02-11 08:23: "checkpoint: Auto-save at 2026-02-11 08:23:35"
- 2026-02-11 08:01: "checkpoint: Auto-save at 2026-02-11 08:01:36"
- 2026-02-11 01:22: "checkpoint: Auto-save at 2026-02-11 01:22:26"
- 2026-02-11 00:31: "Update China trip HTML with fixes"

## Standards

### HTML Format

1. **Self-contained**: All CSS/JS embedded (no external dependencies except images)
2. **UTF-8 encoding**: Full Chinese character support
3. **Single file**: All resources embedded except external images
4. **Responsive**: Mobile-first design, touch-friendly
5. **Performance**: Lazy loading, optimized images, minified CSS

### Interactive Features

**Bilingual toggle**:
- Switch between English and Chinese
- URL hash preservation: `#lang=en` or `#lang=zh`
- Persistent across page reloads

**Collapsible sections**:
- Day-by-day itinerary accordion
- Category-based POI groups
- Save/restore expansion state in localStorage

**POI cards**:
- Image thumbnails with fallback images
- Location coordinates with map links
- Opening hours, contact info
- Cost estimates (CNY/USD)

### Version Control

1. **Timestamps**: Files include creation timestamp in filename
2. **Latest always**: Root-level files are always latest version
3. **Backup preserved**: Old versions kept in `travel-plan-data/`
4. **Cleanup policy**: Remove versions >7 days old if >10 versions exist

## Integration with Workflow

**Deployment pipeline**:
```bash
# Generate HTML from data
python scripts/generate-html-interactive.py china-feb-15-mar-7-2026

# Deploy to output (auto-timestamps)
./scripts/deploy-travel-plans.sh china-feb-15-mar-7-2026

# Output locations:
# - output/travel-plan-china-feb-15-mar-7-2026-20260211-082335.html (latest)
# - output/travel-plan-data/china-feb-15-mar-7-2026-20260211-082335.html (backup)
```

**Data flow**:
```
data/china-*/timeline.json
  → scripts/generate-html-interactive.py
    → output/travel-plan-*.html (latest)
    → output/travel-plan-data/travel-plan-*.html (backup)
```

## Usage

**Viewing plans**:
- Open HTML file in any modern browser
- No server required (works offline)
- Recommended: Chrome, Firefox, Safari, Edge

**Sharing plans**:
- Send HTML file via email, messaging, or cloud storage
- Recipient doesn't need this project
- Everything embedded except external images

**Publishing**:
- Upload to GitHub Pages for web hosting
- Use `deploy-travel-plans.sh` for auto-publishing
- Generates public URL automatically

## Git Analysis

<!-- AUTO-GENERATED by rule-inspector - DO NOT EDIT -->
First created: 2026-02-08
Primary creator: Automated deployment scripts (generate-html-interactive.py, deploy-travel-plans.sh)
Last significant update: 2026-02-11 (active)
Total HTML files: 5 (root) + 2 (travel-plan-data/)
Total deployments: 50+ commits in 3 days
Update frequency: High (multiple daily during active planning)
Recent activity: Auto-save checkpoints, HTML fixes, image refresh, bilingual improvements
Automation level: 100% script-generated
<!-- END AUTO-GENERATED -->

---

*This README documents the organization rules for output/. Generated by rule-inspector from git history analysis.*
