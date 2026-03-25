# Agents

This repository contains Agent Skills definitions following the [agentskills.io](https://agentskills.io) specification.

## Repository structure

```
.agents/
  skills/
    agility-rest-skill/  # Query and manage work items in Digital.ai Agility
      SKILL.md
    create-skill/        # Skill for authoring new SKILL.md files
      SKILL.md
      evals/evals.json
    goals-app/           # Persistent goal tracking with SpecScript
      SKILL.md
      evals/evals.json
    release-plugin/      # Build container-based plugins for Digital.ai Release
      SKILL.md
    specscript-tests/    # Write SpecScript test files for goals-app
      SKILL.md
```

## Conventions

- Each skill lives in its own directory under `.agents/skills/`
- The directory name must match the `name` field in the SKILL.md frontmatter
- Skill names use lowercase letters, numbers, and hyphens only
- Each skill should include an `evals/evals.json` for manual testing
- Keep SKILL.md files under 500 lines
- Follow the [Agent Skills specification](https://agentskills.io/specification) for all formatting and structure
