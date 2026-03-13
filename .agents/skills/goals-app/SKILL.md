---
name: goals-app
description: Manage persistent goals and sub-goals across agent sessions using the goals-app CLI. Use this when you need to track, plan, or update work items that span multiple conversations, or when the user mentions goals, tasks, planning, or tracking progress.
compatibility: Requires the spec CLI (SpecScript) to be installed and available on PATH.
allowed-tools: Bash(spec:*)
metadata:
  author: specscript
  version: "1.0"
---

## Overview

The goals app is a persistent goal tracker backed by a SQLite database. Goals survive across agent sessions -- you can create goals in one conversation and pick them up in another. This makes it ideal for project-level work that spans multiple agent contexts.

Goals support hierarchy: a goal can have sub-goals via `parent_id`, letting you break down large objectives into smaller, trackable pieces.

## Data model

| Field        | Type    | Required | Notes                                           |
|------------- |---------|----------|-------------------------------------------------|
| id           | integer | auto     | Auto-generated identifier                       |
| title        | string  | yes      | Short goal summary                              |
| description  | string  | yes      | Detailed description                            |
| state        | string  | no       | `todo` (default), `in_progress`, or `completed` |
| priority     | string  | no       | `low`, `medium` (default), or `high`            |
| assignee     | string  | no       | Person or agent responsible                     |
| parent_id    | integer | no       | ID of parent goal; null for top-level goals     |
| created_at   | string  | auto     | ISO 8601 timestamp                              |
| updated_at   | string  | auto     | ISO 8601 timestamp                              |

State transitions: `todo` -> `in_progress` -> `completed`

## Commands

You interact with goals by running `spec` commands from the `goals-app` directory. All commands below assume that working directory.

**Important:** Use `spec -j` (JSON output flag) when you need to parse command output programmatically.

### List goals

```sh
spec goals list                          # all goals
spec goals list --state in_progress      # filter by state
spec goals list --state todo             # filter by state
spec goals list --assignee alice         # filter by assignee
spec goals list --parent_id none         # top-level goals only
spec goals list --parent_id 5            # sub-goals of goal 5
```

### Get a goal

```sh
spec goals get --id 3
```

### Create a goal

```sh
spec goals create --title "Implement auth" --description "Add JWT-based authentication to the API" --priority high
```

### Create a sub-goal

```sh
spec goals create --title "Write auth tests" --description "Unit tests for JWT validation" --parent_id 3
```

### Update a goal

Only provide fields you want to change:

```sh
spec goals update --id 3 --state in_progress
spec goals update --id 3 --state completed
spec goals update --id 3 --title "New title" --priority low
```

### Delete a goal

Deleting a parent goal also deletes all its sub-goals.

```sh
spec goals delete --id 3
```

### Discover parameters

Use `--help` to see available subcommands and their parameters:

```sh
spec --help goals                  # list all subcommands
spec --help goals create           # show parameters for create
```

## SpecScript CLI basics

SpecScript is a YAML-based scripting tool. The `spec` command runs `.spec.yaml` files. Directories act as command groups with subcommands.

```
spec [global options] directory subcommand [--param value]
```

- The `.spec.yaml` extension can be omitted
- `spec -j` outputs JSON; `spec -o` outputs YAML
- `spec --help <path>` shows help without running anything
- Parameters are passed as `--name value`

## Session workflow

Follow this workflow when using goals across sessions:

1. **Start of session:** List pending work before doing anything else.
   ```sh
   spec goals list --state todo
   spec goals list --state in_progress
   ```

2. **Claim work:** Mark a goal as `in_progress` before you start on it.

3. **Complete work:** Mark a goal as `completed` when done.

4. **Create new goals** as you discover work that needs doing.

## Writing goals for cross-session handoff

Goals may be read by a different agent or model in a future session. Write them so they stand alone without prior conversation context.

1. **Self-contained titles.** Not "fix the bug" -- instead "Fix null pointer in UserService.getProfile when email is null".

2. **Full context in descriptions.** Include file paths, function names, error messages, acceptance criteria. Write as if for a colleague who has zero context.

3. **Use hierarchy.** Top-level goal for the objective; sub-goals for each concrete step:
   - Goal: "Add pagination to /api/users endpoint"
     - Sub-goal: "Add limit/offset params to UsersRepository.findAll (src/repos/users.ts)"
     - Sub-goal: "Update UsersController to accept page/size query params"
     - Sub-goal: "Add pagination integration tests"

4. **Keep state current.** A future agent relies on state fields to know what is done and what is not.

5. **Use assignee.** Set it when multiple agents or people are involved, so ownership is unambiguous.
