---
name: create-skill
description: Guides creation of Agent Skills (SKILL.md files) following the agentskills.io specification. Use when the user wants to create, author, or set up a new skill for an AI agent, or when they mention SKILL.md, agent skills, or skill authoring.
compatibility: Requires filesystem access to create directories and files.
metadata:
  author: specscript
  version: "1.0"
  spec-url: https://agentskills.io/specification
---

## Overview

This skill walks you through creating an Agent Skill: a `SKILL.md` file with YAML frontmatter and Markdown instructions that agents can discover and load on demand.

The specification lives at https://agentskills.io/specification. This skill distills the spec and best practices into a step-by-step workflow.

## Workflow

Follow these steps in order. Do not skip the information-gathering phase.

### Step 1: Understand what the skill should do

Ask the user these questions before writing anything:

1. **What task does this skill help with?** Get a concrete description, not a vague category.
2. **What does the agent need to know that it does not already know?** Only add context the agent lacks. Do not explain things any competent LLM already knows (what a PDF is, how HTTP works, etc.).
3. **Are there specific tools, commands, or scripts involved?** If yes, get exact command syntax.
4. **Will this be used across sessions or by multiple agents?** This affects how self-contained the instructions need to be.
5. **Where should the skill live?** Common locations:
   - `.agents/skills/<name>/SKILL.md` (most universal, works with OpenCode, Claude Code, and other compatible agents)
   - `.opencode/skills/<name>/SKILL.md` (OpenCode-specific)
   - `.claude/skills/<name>/SKILL.md` (Claude Code-specific)
   - `~/.agents/skills/<name>/SKILL.md` (global, available to all projects)

### Step 2: Choose a name

The name must:
- Be 1-64 characters
- Use only lowercase letters, numbers, and hyphens
- Not start or end with a hyphen
- Not contain consecutive hyphens (`--`)
- Match the directory name containing `SKILL.md`

Prefer descriptive names. Good: `pdf-processing`, `goals-app`, `deploy-staging`. Bad: `helper`, `utils`, `my-skill`.

### Step 3: Write the description

The description field is critical -- agents use it to decide whether to activate the skill. It must:
- Be 1-1024 characters
- Describe what the skill does AND when to use it
- Include specific keywords that help agents match tasks to this skill
- Be written in third person ("Processes PDF files...", not "I help with PDFs" or "Use this to process PDFs")

Good example:
```yaml
description: Extracts text and tables from PDF files, fills forms, and merges documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
```

Bad example:
```yaml
description: Helps with PDFs.
```

### Step 4: Write the SKILL.md body

Structure the body with these principles:

**Be concise.** Every token competes with conversation history and other context. Challenge each paragraph: "Does the agent really need this? Can I assume it already knows this?"

**Match freedom to fragility:**
- High freedom (general guidelines) for tasks where multiple approaches work
- Low freedom (exact commands) for fragile operations where a specific sequence matters

**Recommended sections:**
1. Overview -- what the skill does, in 2-3 sentences
2. Commands/workflow -- concrete steps with exact syntax
3. When to use -- specific triggers and contexts
4. Important rules -- constraints, gotchas, things the agent must not do

**Rules for the body:**
- Keep under 500 lines total
- Use consistent terminology (pick one term and stick with it -- not "endpoint" in one place and "route" in another)
- No time-sensitive information (no "after August 2025, use the new API")
- Forward slashes only for file paths, even on Windows
- File references should be one level deep from SKILL.md (no chains of references)
- Include concrete examples with real-looking inputs and outputs, not abstract descriptions

### Step 5: Add optional frontmatter fields

Only add these if they apply:

```yaml
compatibility: Requires git, docker, and network access.
allowed-tools: Bash(git:*) Read Write
license: MIT
metadata:
  author: your-org
  version: "1.0"
```

- `compatibility` -- only if the skill has specific environment requirements
- `allowed-tools` -- space-delimited list of pre-approved tools (experimental)
- `license` -- if distributing the skill
- `metadata` -- arbitrary key-value pairs for additional info

### Step 6: Consider additional directories

Most skills need only `SKILL.md`. Add these only when justified:

- `scripts/` -- executable code the agent runs. Use when a command is complex enough that generating it on the fly is unreliable. Scripts must be self-contained, handle errors explicitly, avoid interactive prompts, support `--help`, and use structured output (JSON preferred).
- `references/` -- additional documentation loaded on demand. Use when SKILL.md approaches 500 lines and some content is only needed for specific sub-tasks.
- `assets/` -- templates, schemas, data files.

**Do not create these directories "just in case."** An empty `scripts/` folder adds nothing.

### Step 7: Validate the result

Check against this list:

- [ ] `name` in frontmatter matches the directory name
- [ ] `name` follows naming rules (lowercase, hyphens, no consecutive hyphens)
- [ ] `description` says what the skill does AND when to use it
- [ ] `description` is in third person
- [ ] Body is under 500 lines
- [ ] No unnecessary explanations of things agents already know
- [ ] Concrete examples with real-looking syntax
- [ ] Consistent terminology throughout
- [ ] No time-sensitive information
- [ ] File references are one level deep (no chains)
- [ ] Forward slashes in all paths

## Template

Use this as a starting point:

```markdown
---
name: skill-name
description: Does X and Y. Use when the user needs to Z or mentions A, B, or C.
---

## Overview

Brief description of what this skill does and why it exists.

## Commands

Exact commands or steps the agent should follow:

\`\`\`sh
example-command --flag value
\`\`\`

## When to use

- Specific trigger condition 1
- Specific trigger condition 2

## Rules

- Important constraint 1
- Important constraint 2
```

## Setting up a simple eval

After creating the skill, set up basic evaluation to verify it works. Create `evals/evals.json` in the skill directory.

### What to test

Write 3-4 test cases covering:
1. **Happy path** -- a straightforward prompt that should activate the skill and produce correct output
2. **Ambiguous prompt** -- a casually worded request to test whether the skill's description triggers correctly
3. **Edge case** -- a boundary condition (missing input, unusual request, conflicting instructions)
4. **Workflow compliance** -- does the agent follow the skill's prescribed steps in order?

### Eval file format

```json
{
  "skill_name": "your-skill-name",
  "evals": [
    {
      "id": 1,
      "prompt": "A realistic user message that should trigger this skill",
      "expected_output": "Human-readable description of what success looks like",
      "assertions": [
        "Specific, verifiable statement about the output",
        "Another verifiable statement"
      ]
    }
  ]
}
```

### Writing good assertions

Good assertions are specific and verifiable:
- "The output includes a valid JSON file with a `name` field"
- "The agent runs `spec goals list` before creating new goals"
- "The generated SKILL.md has both `name` and `description` in frontmatter"

Bad assertions are vague or subjective:
- "The output is good"
- "The skill works correctly"
- "The agent does the right thing"

### How to run evals

There is no automated eval runner. Run evals manually:

1. Start a fresh agent session (no leftover context)
2. Paste the eval prompt
3. Observe whether the agent's behavior matches expected output and passes assertions
4. Optionally, run the same prompt without the skill as a baseline comparison
5. Record results and iterate on the skill if assertions fail

Focus on whether the skill adds value over no-skill baseline. A skill that does not measurably improve agent behavior should be simplified or removed.
