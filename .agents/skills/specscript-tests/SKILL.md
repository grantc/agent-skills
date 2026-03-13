---
name: specscript-tests
description: Creates SpecScript test files (.spec.yaml) for the goals-app project. Use when the user asks to write tests, add test coverage, or create test cases for SpecScript commands or scripts.
compatibility: Requires the spec CLI (SpecScript) and the goals-app project structure.
metadata:
  author: specscript
  version: "1.0"
---

## Overview

Writes `.spec.yaml` test files for SpecScript projects. Tests are YAML files using SpecScript's built-in test
framework: `Tests`, `Before tests`, `After tests`, `Assert that`, and `Expected output`.

This skill contains the exact syntax patterns, constraints, and gotchas learned from building the goals-app test
suite (27 tests across 6 files). Follow these patterns precisely — SpecScript's YAML-based syntax has subtle rules
that differ from typical testing frameworks.

## Test file structure

Every test file follows this skeleton:

```yaml
# Description of what is tested
#
# Run with: spec --test tests/my-tests.spec.yaml

Script info: My tests

Before tests:
  # setup commands (runs once before all tests)

Tests:

  Test name here:
    # commands and assertions

  Another test:
    # commands and assertions

After tests:
  # cleanup commands (runs once after all tests)
```

### Rules

- `Before tests` and `After tests` run **once per file**, not per test.
- All three blocks (`Before tests`, `Tests`, `After tests`) share the same context — variables set in setup are
  visible in tests and teardown.
- Tests only execute with `spec --test`. Normal `spec` execution silently skips them.

## Running tests

```sh
# Single file
spec --test tests/create-tests.spec.yaml

# All test files in a directory
spec --test tests/
```

## Goals-app test setup pattern

The goals-app uses a SQLite test database. Every test file needs this setup/teardown:

```yaml
Before tests:
  Shell: rm -f db/test-goals.db
  Create test db: {}

After tests:
  Shell: rm -f db/test-goals.db
```

- `Shell:` runs from the **working directory** (where `spec` was invoked), not the script's directory.
- `Create test db: {}` is an imported command from `tests/create-test-db.spec.yaml` — it connects to the test DB
  and creates the schema.
- The `{}` is required because the command is an imported script with no parameters. Passing null content fails.

### Seeding test data in Before tests

Use `Do:` with a list to run multiple setup commands:

```yaml
Before tests:
  Shell: rm -f db/test-goals.db
  Create test db: {}
  Do:
    - Create:
        title: First goal
        description: A goal
    - Create:
        title: Second goal
        description: Another goal
```

Or for a single seed record, just use the command directly:

```yaml
Before tests:
  Shell: rm -f db/test-goals.db
  Create test db: {}
  Create:
    title: Seed goal
    description: Pre-existing goal for tests
    priority: high
```

## Assertions

### Assert that

```yaml
# Single assertion
Assert that:
  item: ${output[0].title}
  equals: Expected title

# Multiple assertions (list syntax)
Assert that:
  - item: ${output[0].title}
    equals: Expected title
  - item: ${output[0].state}
    equals: todo

# Negation
Assert that:
  not:
    item: ${output[0].parent_id}
    equals: ""

# Empty check
Assert that:
  empty: ${output}

# Not empty
Assert that:
  not:
    empty: ${output}
```

### Expected output

Shorthand for asserting `${output}` equals a value:

```yaml
Size: ${goals}
Expected output: 4

# Empty list
Get:
  id: 999
Expected output: []
```

### Inline eval with /Command: syntax

Use `/Command:` inside a data block to evaluate a command inline. The result replaces itself.

```yaml
Assert that:
  - item:
      /Size: ${goals}
    equals: 3
```

**Critical constraint:** The `/Command:` must be on its own YAML line as a map key. Never inline it like
`item: /Size: ${goals}` — that's parsed as a string, not an eval.

## Variable capture with As

`As:` stores the current `${output}` into a named variable:

```yaml
Create:
  title: My goal
  description: A goal
As: ${created}

# Now use ${created} in subsequent commands
Delete:
  id: ${created[0].id}
```

**Note:** `${varname}` in `As:` is a **write target**, not a dereference. This is the opposite of how `${...}`
works everywhere else.

## YAML constraints to remember

### No duplicate keys

YAML does not allow duplicate keys in the same mapping. These workarounds exist:

1. **`Do:` with a list** — preferred inside test cases:
   ```yaml
   Do:
     - Create:
         title: Goal one
         description: First
     - Create:
         title: Goal two
         description: Second
   ```

2. **`---` document separator** — only works at the **top level**, not inside `Tests:` or `Before tests:`.

3. **`As:` inside `Do:`** — works for capturing intermediate results:
   ```yaml
   Do:
     - Create:
         title: Parent
         description: Top level
     - As: ${parent}
     - Create:
         title: Child
         description: Sub-goal
         parent_id: ${parent[0].id}
   ```

### Do: returns a list of ALL outputs

`Do:` collects the output of every command into a list. So `Expected output:` after `Do:` compares against the
full list, not just the last command's output. If you need only the final result, use `As:` to capture it.

## Calling imported scripts as commands

Scripts imported via `.directory-info.yaml` become commands. The command name is derived from the filename:
`create.spec.yaml` becomes `Create:`, `create-batch.spec.yaml` becomes `Create batch:`.

```yaml
Create:
  title: A goal
  description: Something to do
  priority: high
  assignee: alice
```

When you need to call the same script with a variable in a parameter that was set earlier in the same block, use
`Run script:` with `resource:`:

```yaml
Create:
  title: Parent
  description: Top level
As: ${parent}
Run script:
  resource: ../goals/create.spec.yaml
  input:
    title: Child
    description: Sub-goal
    parent_id: ${parent[0].id}
```

- `resource:` resolves relative to the **calling script's** directory.
- `file:` resolves relative to the **working directory**.

## Complete example

```yaml
# Update goal tests
#
# Tests for the update goal command.
# Run with: spec --test tests/update-tests.spec.yaml

Script info: Update goal tests

Before tests:
  Shell: rm -f db/test-goals.db
  Create test db: {}
  Create:
    title: Original title
    description: Original description
    priority: low
    assignee: alice

Tests:

  Update title:
    Update:
      id: 1
      title: Updated title
    Assert that:
      - item: ${output[0].title}
        equals: Updated title
      - item: ${output[0].message}
        equals: Goal updated

  Update non-existent goal:
    Update:
      id: 999
      title: Ghost
    Expected output: []

  Unchanged fields are preserved:
    Update:
      id: 1
      title: Only title changes
    Assert that:
      - item: ${output[0].title}
        equals: Only title changes
      - item: ${output[0].description}
        equals: Original description

After tests:
  Shell: rm -f db/test-goals.db
```
