---
name: agility-okr-report
description: Generate OKR reports from Digital.ai Agility by querying the REST API for objectives, key results, sessions, and linked team objectives
---

## What I do

Build markdown OKR reports from the Digital.ai Agility REST API. I fetch objectives, key results, linked/cascaded team objectives, and progress data, then produce a structured markdown report.

## When to use me

Use this skill when asked to generate, update, or query OKR data from Digital.ai Agility.

## Prerequisites

The environment variable `AGILITY_TOKEN` must be set with a valid Bearer token. The Agility instance URL must be known (see Configuration below).

## Configuration

- **Agility instance base URL**: `https://www7.v1host.com/V1Production/`
- **REST API endpoint**: `rest-1.v1/Data/{AssetType}`
- **Metadata endpoint**: `meta.v1/{AssetType}`
- **Authentication**: `Authorization: Bearer $AGILITY_TOKEN`
- **Accept header**: `application/json`

## API Data Model

### Asset Types

| Asset Type | Description |
|------------|-------------|
| `OkrObjective` | An OKR objective |
| `KeyResult` | A key result belonging to an objective |
| `OkrSession` | A time-bound OKR session (quarter, year, etc.) |
| `OkrComment` | A comment on an OKR |
| `Okr` | Base type for objectives and key results |

### Key Relationships

- `OkrObjective.KeyResults` -> multi-relation to `KeyResult`
- `OkrObjective.OkrSession` -> relation to `OkrSession`
- `OkrObjective.Owner` -> relation to `Member`
- `OkrObjective.CascadedFrom` -> parent objective (single relation via `Okr` base type)
- `OkrObjective.CascadedTo` -> child objectives (multi-relation via `Okr` base type)
- `OkrObjective.LinkedFrom` / `LinkedTo` -> peer-linked objectives (multi-relation via `Okr` base type)
- `KeyResult.OkrObjective` -> parent objective
- `KeyResult.Progress` -> decimal 0-1+ representing completion fraction
- `KeyResult.CurrentValue`, `KeyResult.TargetValue`, `KeyResult.InitialValue` -> quantitative tracking
- `KeyResult.Type` -> one of: `AchievedOrNot`, `IncreaseTo`, `DecreaseTo`, `MaintainAbove`, `MaintainBelow`
- `KeyResult.Commitment` -> relation to `KeyResultCommitment` (Committed, Aspirational, Learning)
- `KeyResult.Unit` -> relation to `KeyResultUnit` (Count, Percentage, Currency, etc.)

### OkrObjective Fields

| Field | Description |
|-------|-------------|
| `Name` | Objective title |
| `Description` | Objective description |
| `Number` | Display number (e.g., O-03833) |
| `IsCompleted` | All key results are done |
| `IsInProgress` | At least one key result has progress |
| `IsNotStarted` | No key results have progress |
| `IsClosed` | Broader than IsCompleted; includes closed-but-not-completed |
| `OkrSession` | The session this objective belongs to |
| `Owner` | The member who owns this objective |
| `KeyResults` | Multi-relation to key results |
| `CascadedFrom` | Parent objective (if cascaded) |
| `CascadedTo` | Child objectives (if any cascade from this) |
| `LinkedFrom` / `LinkedTo` | Peer-linked objectives |
| `AssociatedAssets` | Related Agility work items |

### KeyResult Fields

| Field | Description |
|-------|-------------|
| `Name` | Key result title |
| `Description` | Key result description |
| `Number` | Display number (e.g., KR-04968) |
| `Progress` | Decimal 0 to 1+ (can exceed 1 if target exceeded) |
| `CurrentValue` | Current numeric value |
| `TargetValue` | Target numeric value |
| `InitialValue` | Starting numeric value |
| `CriticalValue` | Threshold value (for Maintain types) |
| `Type` | Measurement type |
| `Unit` | Unit of measurement |
| `Commitment` | Commitment level |
| `OkrObjective` | Parent objective |

### OkrSession Fields

| Field | Description |
|-------|-------------|
| `Name` | Session name |
| `BeginDate` | Start date (NOT `StartDate`) |
| `EndDate` | End date |

## API Query Patterns

### Basic query structure

```
curl -s \
  -H "Authorization: Bearer $AGILITY_TOKEN" \
  -H "Accept: application/json" \
  "https://www7.v1host.com/V1Production/rest-1.v1/Data/{AssetType}?sel={fields}&where={filters}"
```

### Field selection (`sel`)

- Comma-separated field names: `sel=Name,Description,Number`
- Inline related fields with dot notation: `sel=KeyResults.Name,KeyResults.Progress,Owner.Name`
- Multi-level nesting works for owned attributes but NOT for attributes of base-type relations (e.g., `CascadedTo.Owner.Name` fails because `CascadedTo` references `Okr` base type which lacks `Owner`)

### Filtering (`where`)

- Use `;` for AND: `where=Owner='Member:1576424';IsCompleted='true'`
- Use `,` for OR within a value: `where=OkrSession='OkrSession:3442519','OkrSession:3442520'`
- Exact match only: `=` operator. There is NO `~` (contains/like) operator for string matching.
- Boolean filters: `IsCompleted='true'`, `IsInProgress='true'`
- Reference filters: `Owner='Member:1576424'`, `OkrSession='OkrSession:3442519'`

### Metadata discovery

To discover available fields on an asset type:

```
curl -s \
  -H "Authorization: Bearer $AGILITY_TOKEN" \
  -H "Accept: application/json" \
  "https://www7.v1host.com/V1Production/meta.v1/{AssetType}"
```

## Recommended Workflow for Building an OKR Report

### Step 1: Identify the target sessions

Query `OkrSession` filtered by `BeginDate` and `EndDate` to find sessions in the target year or period.

```
rest-1.v1/Data/OkrSession?sel=Name,BeginDate,EndDate&where=BeginDate>='2025-01-01';EndDate<='2025-12-31'
```

### Step 2: Fetch objectives with inline key results

Query `OkrObjective` with the session IDs, filtered by owner if needed, selecting inline key result fields. This gets everything in one call.

```
rest-1.v1/Data/OkrObjective?sel=Name,Description,Number,IsCompleted,IsInProgress,IsNotStarted,IsClosed,OkrSession.Name,Owner.Name,KeyResults.Name,KeyResults.Description,KeyResults.Progress,KeyResults.CurrentValue,KeyResults.TargetValue,KeyResults.InitialValue,KeyResults.Type,KeyResults.Unit,KeyResults.Commitment,CascadedTo.Name,CascadedTo.Number,LinkedTo.Name,LinkedTo.Number,CascadedFrom.Name,CascadedFrom.Number&where=Owner='Member:{id}';OkrSession='OkrSession:{id1}','OkrSession:{id2}'
```

**Key filter tips:**
- Use `IsCompleted='true'` for completed objectives (all KRs done)
- Omit status filters to get all objectives (completed + in-progress + not started)
- Do NOT use `IsClosed='true'` if you only want completed; it returns a much broader set

### Step 3: Fetch linked/cascaded team objectives

To find team members' objectives that link to or cascade from the user's objectives:

**Objectives linked TO the user's objectives (reverse links):**
```
rest-1.v1/Data/OkrObjective?sel=Name,Number,Owner.Name,IsCompleted,IsInProgress,IsClosed,OkrSession.Name,KeyResults.Name,KeyResults.Progress,KeyResults.CurrentValue,KeyResults.TargetValue,KeyResults.Type,LinkedTo.Name,LinkedTo.Number&where=LinkedTo='OkrObjective:{id1}','OkrObjective:{id2}'
```

**Objectives cascaded FROM the user's objectives (children):**
```
rest-1.v1/Data/OkrObjective?sel=Name,Number,Owner.Name,IsCompleted,IsInProgress,IsClosed,OkrSession.Name,KeyResults.Name,KeyResults.Progress,KeyResults.CurrentValue,KeyResults.TargetValue,KeyResults.Type,CascadedFrom.Name,CascadedFrom.Number&where=CascadedFrom='OkrObjective:{id1}','OkrObjective:{id2}'
```

**Important:** You cannot select `CascadedTo.Owner.Name` or `LinkedTo.Owner.Name` because these relations use the `Okr` base type which does not have an `Owner` attribute. Query the linked/cascaded objectives separately to get their owner.

### Step 4: Generate the report

Structure the markdown report as follows:

```markdown
# OKR Report {Period} - {Person Name}

## Summary
Table with status counts, total objectives, total KRs, linked team objectives.

## {Session Name}

### {Number}: {Objective Name}
- Status, commitment, description
- Key results table with: Name, Type, Progress (current/target), Status
- Expandable details section for KR descriptions
- Linked/cascaded team objectives shown as blockquotes under the parent

## Linked Team Objectives Summary
Summary table at the bottom showing all team objectives, their owners, link targets, status, and progress.
```

## Known Pitfalls

1. **`Progress` does not exist on `OkrObjective`** - Only `KeyResult` has `Progress`. Objectives have `IsCompleted`, `IsInProgress`, `IsNotStarted`.
2. **`PercentComplete` does not exist** on any OKR type.
3. **`StartDate` does not exist on `OkrSession`** - Use `BeginDate`.
4. **`IsCompleted` does not exist on `KeyResult`** - Use `Progress` (1.0 = complete).
5. **No `~` operator** - The `where` clause does not support contains/like matching.
6. **`IsClosed` != `IsCompleted`** - `IsClosed` is a superset that includes objectives closed without completion.
7. **Base type relations** - `CascadedFrom`, `CascadedTo`, `LinkedFrom`, `LinkedTo` reference the `Okr` base type. You can select `Name` and `Number` on them, but NOT `Owner` or other `OkrObjective`-specific fields. Query those objectives separately.
8. **KeyResult.Progress can exceed 1.0** - When `CurrentValue` exceeds `TargetValue`, progress > 1.0.
## UI URL Pattern

Link to an OKR objective in the Agility UI:

```
https://www7.v1host.com/V1Production/Rooms2.mvc/okr/objectives/asset/OkrObjective:{id}
```

Example: `https://www7.v1host.com/V1Production/Rooms2.mvc/okr/objectives/asset/OkrObjective:3473579`

Use the numeric ID from the API response (e.g., `3473579` from `OkrObjective:3473579`).
