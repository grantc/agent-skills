# agent-skills

A collection of reusable [Agent Skills](https://agentskills.io) -- `SKILL.md` files that AI coding agents can discover and load on demand.

## Skills

| Skill | Description |
|-------|-------------|
| [agility-rest-skill](.agents/skills/agility-rest-skill/SKILL.md) | Query and manage Portfolio Items, Stories, and Defects in Digital.ai Agility via the REST API. |
| [create-skill](.agents/skills/create-skill/SKILL.md) | Guides creation of Agent Skills (SKILL.md files) following the agentskills.io specification. |
| [goals-app](.agents/skills/goals-app/SKILL.md) | Manage persistent goals and sub-goals across agent sessions using the goals-app CLI. |
| [release-plugin](.agents/skills/release-plugin/SKILL.md) | Build, test, and maintain container-based integration plugins for Digital.ai Release. |
| [specscript-tests](.agents/skills/specscript-tests/SKILL.md) | Creates SpecScript test files (.spec.yaml) for the goals-app project. |

## Usage

Skills live in `.agents/skills/<name>/SKILL.md` and follow the [Agent Skills specification](https://agentskills.io/specification). Compatible agents (OpenCode, Claude Code, and others) automatically discover and activate skills based on their descriptions.

To use these skills in another project, copy the `.agents` directory (or individual skill directories) into your project root.

## Evals

Some skills include `evals/evals.json` files with test cases for manual evaluation. See the [create-skill](.agents/skills/create-skill/SKILL.md) skill for guidance on writing and running evals.
