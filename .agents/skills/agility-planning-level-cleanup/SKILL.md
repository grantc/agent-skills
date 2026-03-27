# Skill: agility-planning-level-cleanup

## When To Use
- User wants to clean up, close, or audit a planning level (Scope) in Digital.ai Agility
- User wants to find Sub-Features, Features, or Epics that are ready to close
- User wants to bulk-update statuses or close portfolio items on a planning level
- User asks about work item completion status across a planning level
- User wants to generate reports of open/completable work on a planning level

## Overview

This skill provides workflows and Python scripts for auditing and cleaning up
a planning level (Scope) in Digital.ai Agility. The typical workflow is:

1. **Fetch** all portfolio items (Sub-Features/Features/Epics) on a planning level
2. **Fetch** all children (Stories + Defects) for those portfolio items — **across all scopes**
3. **Analyze** which portfolio items are "effectively done" and ready for completion
4. **Update** statuses (e.g. mark as "Completed")
5. **Close** portfolio items via the Inactivate operation
6. **Report** on remaining open items for owner decision-making

## Prerequisites

- `AGILITY_TOKEN` environment variable must be set with a valid bearer token
- Python 3.8+ with no external dependencies (uses only stdlib: json, urllib, os, sys)
- Network access to `https://www7.v1host.com/V1Production`

## API Reference

### Base URL
```
https://www7.v1host.com/V1Production
```

### Authentication
```
Authorization: Bearer {AGILITY_TOKEN}
```

### Key Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `rest-1.v1/Data/{AssetType}?sel=...&where=...&page=...` | GET | Query assets |
| `rest-1.v1/Data/{AssetType}/{id}` | POST | Update an asset |
| `rest-1.v1/Data/{AssetType}/{id}?op=Inactivate` | POST | Close (inactivate) an asset |

### Asset Types

| Type | Description |
|---|---|
| `Epic` | Portfolio items (Epic, Feature, Sub-Feature -- distinguished by `Category.Name`) |
| `Story` | User stories / backlog items |
| `Defect` | Bugs / defects |
| `Scope` | Projects / planning levels |
| `EpicStatus` | Status values for Epics |
| `EpicCategory` | Category values (Epic, Feature, Sub-Feature, etc.) |

### Asset States

| Code | State |
|---|---|
| 0 | Future |
| 64 | Active |
| 128 | Closed |
| 208 | Broken Down |
| 255 | Deleted |

### Known Status OIDs (DevOps)

| OID | Name |
|---|---|
| `EpicStatus:1905281` | Completed |
| `EpicStatus:670492` | In Progress |
| `EpicStatus:670502` | Review |
| `EpicStatus:559703` | Discovery |
| `EpicStatus:1905275` | Breakdown |
| `EpicStatus:2200973` | Not Doing |

### Known Scope OIDs (DevOps)

| Scope | OID | Parent |
|---|---|---|
| DevOps (root) | `Scope:1731677` | -- |
| 26.1 DevOps | `Scope:3234178` | DevOps |

### Where Clause Syntax
- Equality: `Field='Value'`
- Not equal: `Field!='Value'`
- AND: `;` separator
- OR: `|` separator
- Nested: `Super.Category.Name='Sub-Feature'`
- Always exclude deleted: `AssetState!='255'`

### Efficient Bulk Querying

**Do NOT query children one-by-one per portfolio item.** Instead, use scope-level
filters with nested attributes.

#### Cross-Scope Querying (Critical)

Children (Stories/Defects) often live in a **different scope** than their parent
portfolio item. For example, a Sub-Feature in "26.1 DevOps" may have children in
"DevOps" (parent scope), "UXD", "DevOps Delivery", etc.

**Always use `Super.Scope` instead of `Scope` when fetching children** to get
all children regardless of which scope they live in:

```
# WRONG — misses children in other scopes (607 results in 26.1):
GET rest-1.v1/Data/Story?sel=...
    &where=Scope='Scope:3234178';Super.Category.Name='Sub-Feature';AssetState!='255'

# CORRECT — gets ALL children whose parent is in the scope (1100 results in 26.1):
GET rest-1.v1/Data/Story?sel=...
    &where=Super.Scope='Scope:3234178';Super.Category.Name='Sub-Feature';AssetState!='255'
```

This is a critical difference — in 26.1 DevOps, scope-only queries returned 607
children while `Super.Scope` queries returned 1,100 (nearly double). Children were
spread across 15 different scopes including DevOps, UXD, DevOps Delivery, 25.3-DevOps,
AppMgt/AppSec, DevOps Docs, and others.

Paginate with `page=500,0`, `page=500,500`, etc. until you get fewer than pageSize results.

### Updating Status

```bash
curl -s -X POST \
  -H "Authorization: Bearer $AGILITY_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  "https://www7.v1host.com/V1Production/rest-1.v1/Data/Epic/{oid_num}" \
  -d '{"Attributes": {"Status": {"value": "EpicStatus:1905281", "act": "set"}}}'
```

### Closing (Inactivating) an Asset

```bash
curl -s -X POST \
  -H "Authorization: Bearer $AGILITY_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  "https://www7.v1host.com/V1Production/rest-1.v1/Data/Epic/{oid_num}?op=Inactivate" \
  -d '{}'
```

## Python Scripts

All scripts are in `scripts/` relative to this skill. They use only Python stdlib
and read `AGILITY_TOKEN` from the environment.

**Note:** `fetch_children.py` currently filters by `Scope` (child's scope), which
misses cross-scope children. For accurate analysis, use `Super.Scope` queries
directly (see "Cross-Scope Querying" above) or update the script accordingly.

### scripts/fetch_subfeatures.py

Fetches all portfolio items of a given category on a planning level and saves to JSON.

```bash
python3 scripts/fetch_subfeatures.py --scope "26.1 DevOps" --category Sub-Feature --output subfeatures.json
```

### scripts/fetch_children.py

Fetches all Stories and Defects under portfolio items of a given category on a
planning level. Uses bulk scope-level queries (not per-item).

```bash
python3 scripts/fetch_children.py --scope "26.1 DevOps" --parent-category Sub-Feature --output children.json
```

### scripts/analyze_readiness.py

Reads the subfeatures and children JSON files, computes which portfolio items
are ready to close (all children closed), and outputs a report.

```bash
python3 scripts/analyze_readiness.py --subfeatures subfeatures.json --children children.json --output report.json
```

### scripts/update_status.py

Updates the status of portfolio items. Supports dry-run mode.

```bash
# Dry run (preview only)
python3 scripts/update_status.py --input report.json --status Completed --dry-run

# Execute
python3 scripts/update_status.py --input report.json --status Completed
```

### scripts/close_items.py

Closes (Inactivates) portfolio items. Supports dry-run mode and pre-checks.

```bash
# Dry run
python3 scripts/close_items.py --input report.json --dry-run

# Execute
python3 scripts/close_items.py --input report.json
```

## Typical Workflow

```bash
# 1. Fetch Sub-Features
python3 scripts/fetch_subfeatures.py --scope "26.1 DevOps" --category Sub-Feature -o sf.json

# 2. Fetch all children (Stories + Defects) in bulk
python3 scripts/fetch_children.py --scope "26.1 DevOps" --parent-category Sub-Feature -o children.json

# 3. Analyze readiness
python3 scripts/analyze_readiness.py --subfeatures sf.json --children children.json -o report.json

# 4. Mark ready items as Completed (dry-run first)
python3 scripts/update_status.py --input report.json --status Completed --filter ready_to_close --dry-run
python3 scripts/update_status.py --input report.json --status Completed --filter ready_to_close

# 5. Close items (dry-run first)
python3 scripts/close_items.py --input report.json --filter ready_to_close --dry-run
python3 scripts/close_items.py --input report.json --filter ready_to_close
```

## Agent Guidance

- Always start with a dry-run before making changes
- Always verify results after updates by re-querying
- The `--filter` flag on update/close scripts supports: `ready_to_close`, `all_completed`, `no_children`, or a comma-separated list of Epic numbers (e.g., `E-19816,E-19822`)
- Include Defects in analysis -- they also block closing
- Use `page=500,0` for bulk queries, paginate until results < pageSize
- Remember: changing Status to "Completed" and Closing (Inactivate) are separate operations
- UI links use: `https://www7.v1host.com/V1Production/assetdetail.v1?number={Number}`

## Effectively Done Criteria

A child (Story/Defect) is **effectively done** if any of these are true:
- Asset State is **Closed** (128) — formally closed
- Status is **Done** or **DONE** (case-insensitive) — work completed but not formally closed
- Status is **Not Doing** — work deliberately skipped, also terminal

A portfolio item (Sub-Feature/Feature/Epic) is **ready for completion** when ALL
its children are effectively done. This is broader than just checking Asset State
and catches the common case where teams mark Stories as "Done" without formally
closing them.

### Readiness Categories

When analyzing a planning level, portfolio items fall into these categories:

| Category | Criteria | Action |
|---|---|---|
| Already Closed | Asset State = Closed (128) | None needed |
| All children formally Closed | All children have state=128 | Can be Closed (Inactivated) |
| All children effectively Done | All children Closed or Done/Not Doing | Should be marked "Completed" first |
| Has genuinely open children | Some children not Done | Needs owner decision |
| No children | Zero Stories/Defects | May be empty placeholder — review |

### Status vs Asset State

These are **independent** in Agility:
- **Status** = workflow field set by users (e.g. "Done", "In Progress")
- **Asset State** = lifecycle state (Active/Closed/Deleted)

A Story with Status="Done" but AssetState=Active is finished work that hasn't been
formally closed. This is extremely common — in 26.1 DevOps, 451 of 559 active
children had Done/Not Doing status.

## Report Patterns

### Completable Sub-Features Report
For showing which portfolio items can be marked Completed:
- Group by **Team** (from the portfolio item level)
- Include: Sub-Feature number (hyperlinked), Name, Owner, SF Status, children counts
- Separate sections for "effectively done" vs "formally closed"
- Exclude items that already have Completed status (to show only actionable items)
- Save as markdown with hyperlinks using `assetdetail.v1?number=` pattern

### Open Stories Report
For owner decision-making on remaining open work:
- Group by **Team** (from the Sub-Feature level)
- Each Sub-Feature section shows: Owner, Status, count of open items
- List each open child with: number (hyperlinked), name, status, iteration, team, scope
- Include iteration/sprint info — items with no iteration likely were never picked up
- Items already in future sprints (e.g. 26.3) may need to be reparented to a new Sub-Feature
- Sub-Features should only apply to a single planning level in DevOps

## Data Files

When running this workflow, the following data files are typically generated
in the project root:

| File | Contents |
|---|---|
| `subfeatures_26_1_devops.json` | All Sub-Features with metadata |
| `children_cross_scope_26_1.json` | All children across all scopes (use this, not scope-filtered) |
| `readiness_cross_scope_26_1.json` | Readiness analysis with effectively-done criteria |
| `completable_subfeatures_26_1.md` | Markdown report of completable Sub-Features by team |
| `open_stories_26_1.md` | Markdown report of open items needing owner decisions |
