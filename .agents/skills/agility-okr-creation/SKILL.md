---
name: agility-okr-creation
description: Create and update OKR objectives and key results in Digital.ai Agility via the REST API
---

## What I do

Create and update OKR objectives and key results in Digital.ai Agility using the REST API. I handle session lookup, objective creation, key result creation with proper types and targets, and linking/cascading between objectives.

## When to use me

Use this skill when asked to create, update, or modify OKRs in Digital.ai Agility.

## Prerequisites

The environment variable `AGILITY_TOKEN` must be set with a valid Bearer token.

## Configuration

- **Agility instance base URL**: `https://www7.v1host.com/V1Production/`
- **REST API endpoint**: `rest-1.v1/Data/{AssetType}`
- **Authentication**: `Authorization: Bearer $AGILITY_TOKEN`
- **Headers**: `Content-Type: application/json` and `Accept: application/json`

## API Data Model

### Asset Types

| Asset Type | Description |
|------------|-------------|
| `OkrObjective` | An OKR objective |
| `KeyResult` | A key result belonging to an objective |
| `OkrSession` | A time-bound OKR session (quarter, year, etc.) |

### OkrObjective Fields (for creation)

| Field | Required | Writable | Notes |
|-------|----------|----------|-------|
| `Name` | Yes | Yes | Objective title |
| `Description` | No | Yes | Objective description |
| `OkrSession` | Yes | Yes | Reference to session, e.g. `OkrSession:3442518` |
| `Owner` | - | **No (read-only)** | Auto-assigned to authenticated user |
| `CascadedFrom` | No | Yes | Parent objective reference for cascading |

### KeyResult Fields (for creation)

| Field | Required | Writable | Notes |
|-------|----------|----------|-------|
| `Name` | Yes | Yes | Key result title |
| `Description` | No | Yes | Key result description |
| `OkrObjective` | Yes | Yes | Parent objective reference |
| `Type` | No | Yes | Measurement type (see below) |
| `InitialValue` | No | Yes | Starting value (default 0) |
| `TargetValue` | No | Yes | Target value |
| `CriticalValue` | No | Yes | Threshold for Maintain types |
| `Unit` | No | Yes | Reference to `KeyResultUnit` |
| `Commitment` | No | Yes | Reference to `KeyResultCommitment` |

### Key Result Types

| Type | Description | How progress is calculated |
|------|-------------|---------------------------|
| `AchievedOrNot` | Binary yes/no | Set CurrentValue to 100 when done |
| `IncreaseTo` | Increase metric to target | Progress = (Current - Initial) / (Target - Initial) |
| `DecreaseTo` | Decrease metric to target | Progress = (Initial - Current) / (Initial - Target) |
| `MaintainAbove` | Keep metric above critical value | Based on CurrentValue vs CriticalValue |
| `MaintainBelow` | Keep metric below critical value | Based on CurrentValue vs CriticalValue |

### OkrSession Fields

| Field | Description |
|-------|-------------|
| `Name` | Session name |
| `BeginDate` | Start date (NOT `StartDate`) |
| `EndDate` | End date |

## Workflow

### Step 1: Find the target session

```bash
curl -s \
  -H "Authorization: Bearer $AGILITY_TOKEN" \
  -H "Accept: application/json" \
  "https://www7.v1host.com/V1Production/rest-1.v1/Data/OkrSession?sel=Name,BeginDate,EndDate&where=BeginDate>='2026-01-01'"
```

### Step 2: Create the objective

```bash
curl -s -X POST \
  -H "Authorization: Bearer $AGILITY_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  "https://www7.v1host.com/V1Production/rest-1.v1/Data/OkrObjective" \
  -d '{
    "Attributes": {
      "Name": { "value": "Objective title", "act": "set" },
      "OkrSession": { "value": "OkrSession:{session_id}", "act": "set" }
    }
  }'
```

The response returns the new objective's ID (e.g. `OkrObjective:3473579`).

### Step 3: Create key results

```bash
curl -s -X POST \
  -H "Authorization: Bearer $AGILITY_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  "https://www7.v1host.com/V1Production/rest-1.v1/Data/KeyResult" \
  -d '{
    "Attributes": {
      "Name": { "value": "Key result title", "act": "set" },
      "OkrObjective": { "value": "OkrObjective:{objective_id}", "act": "set" },
      "Type": { "value": "IncreaseTo", "act": "set" },
      "InitialValue": { "value": 0, "act": "set" },
      "TargetValue": { "value": 10, "act": "set" }
    }
  }'
```

Multiple key results can be created in parallel since they are independent.

### Step 4: Verify

Query the created objective with inline key results to confirm:

```bash
curl -s \
  -H "Authorization: Bearer $AGILITY_TOKEN" \
  -H "Accept: application/json" \
  "https://www7.v1host.com/V1Production/rest-1.v1/Data/OkrObjective/{id}?sel=Name,Number,Owner.Name,OkrSession.Name,KeyResults.Name,KeyResults.Number,KeyResults.Type,KeyResults.TargetValue,KeyResults.CurrentValue,KeyResults.Progress"
```

## Updating Existing Assets

POST to the asset's specific URL:

```bash
curl -s -X POST \
  -H "Authorization: Bearer $AGILITY_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  "https://www7.v1host.com/V1Production/rest-1.v1/Data/OkrObjective/{id}" \
  -d '{
    "Attributes": {
      "Name": { "value": "Updated title", "act": "set" }
    }
  }'
```

### Updating Key Result Progress

To update the current value of a key result:

```bash
curl -s -X POST \
  -H "Authorization: Bearer $AGILITY_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  "https://www7.v1host.com/V1Production/rest-1.v1/Data/KeyResult/{id}" \
  -d '{
    "Attributes": {
      "CurrentValue": { "value": 5, "act": "set" }
    }
  }'
```

## Linking and Cascading

### Link two objectives

Use the `LinkedTo` multi-relation with `act: add`:

```bash
curl -s -X POST \
  -H "Authorization: Bearer $AGILITY_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  "https://www7.v1host.com/V1Production/rest-1.v1/Data/OkrObjective/{id}" \
  -d '{
    "Attributes": {
      "LinkedTo": { "value": "OkrObjective:{other_id}", "act": "add" }
    }
  }'
```

### Cascade from a parent objective

Set `CascadedFrom` on creation:

```bash
curl -s -X POST \
  -H "Authorization: Bearer $AGILITY_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  "https://www7.v1host.com/V1Production/rest-1.v1/Data/OkrObjective" \
  -d '{
    "Attributes": {
      "Name": { "value": "Child objective", "act": "set" },
      "OkrSession": { "value": "OkrSession:{session_id}", "act": "set" },
      "CascadedFrom": { "value": "OkrObjective:{parent_id}", "act": "set" }
    }
  }'
```

## UI URL Pattern

Link to an OKR objective in the Agility UI:

```
https://www7.v1host.com/V1Production/Rooms2.mvc/okr/objectives/asset/OkrObjective:{id}
```

Example: `https://www7.v1host.com/V1Production/Rooms2.mvc/okr/objectives/asset/OkrObjective:3473579`

## Known Pitfalls

1. **`Owner` is read-only** - Do NOT set `Owner` when creating an objective. It is auto-assigned to the authenticated user.
2. **`StartDate` does not exist on `OkrSession`** - Use `BeginDate`.
3. **Use `act: "set"` for single-value fields** and `act: "add"` for adding to multi-value relations (e.g. `LinkedTo`).
4. **Session is required** - Every objective must have an `OkrSession` set.
5. **`OkrObjective` is required on `KeyResult`** - Every key result must reference its parent objective.
6. **Create objective before key results** - You need the objective ID before you can attach key results to it.
7. **Key results can be created in parallel** - Once you have the objective ID, all key results are independent.
