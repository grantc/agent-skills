---
name: agility-rest-skill
description: Use when you need to query or manage Portfolio Items (Epics/Features), Stories, and Defects in Digital.ai Agility via the rest-1.v1 Data API.
---

# agility-rest

## When To Use
- User asks to query, create, or update work items in Digital.ai Agility.
- You need data from `rest-1.v1/Data/{AssetType}` for Epics, Stories, Defects, or related assets.
- Asset types include: `Epic`, `Story`, `Defect`, `Scope`, `Team`, `Timebox`, `Theme`, `Member`, `EpicCategory`, `StoryCategory`, `Request`.
- Bearer token auth is required (`Authorization: Bearer ...`).

## Concepts

### Asset Types
| Asset Type | Description | Common Aliases |
|---|---|---|
| `Epic` | Portfolio Items (Epics, Features, Initiatives, Sub-Features) | Portfolio Item, PI |
| `Story` | User stories / backlog items | Backlog Item |
| `Defect` | Bugs / defects | Bug |
| `Scope` | Projects / planning levels | Project |
| `Team` | Teams within a scope | - |
| `Timebox` | Sprints / iterations | Sprint, Iteration |
| `Theme` | Themes / tags | Tag |
| `EpicCategory` | Category values for Epics | - |

### Epic Categories
Epics are distinguished by `Category.Name`. Known values:
Area, Capability, Enhancement, **Epic**, **Feature**, Feature Outcome, Goal, Impact Epic, **Initiative**, Marketing Commitment, Marketing Program, Milestone, New Feature, Non-Functional, Release Themes, Request, **Sub-Feature**, Sub-Initiative, Team Commitment

When the user says "Epics" they typically mean `Category.Name='Epic'`. When they say "Features" they mean `Category.Name='Feature'`.

### Asset States
| Value | Meaning |
|---|---|
| 0 | Future (not yet started) |
| 64 | Active |
| 128 | Closed |
| 200 | Template |
| 208 | Broken Down |
| 255 | Deleted |

To exclude deleted items, add `AssetState!='255'` to `where` clauses.

### Key Relationships
- `Epic.Super` -> parent Epic (for Epic-to-Epic hierarchy)
- `Story.Super` / `Defect.Super` -> parent Epic
- `Epic.Scope` / `Story.Scope` -> owning Scope (planning level)
- `Story.Team` / `Defect.Team` -> assigned Team
- `Story.Timebox` / `Defect.Timebox` -> Sprint/Iteration
- `Epic.Subs` -> child Epics (multi-value)
- `Epic.ChildrenMeAndDown` -> all descendant stories/defects

### Scope (Planning Level) — DevOps Example
The DevOps planning level has **two Scopes** both named "DevOps". The correct one for Epics is:
- **Scope OID**: `Scope:1731677`
- Filter with: `Scope='Scope:1731677'`
- Or by name: `Scope.Name='DevOps'` (may match both — prefer OID for precision)

Sub-scopes (sprints/releases) like "26.1 DevOps", "26.2 DevOps" are children of `Scope:1731677`.

## API Base URL
`https://www7.v1host.com/V1Production`

## REST API Patterns

### Query (GET)
```
GET {baseUrl}/rest-1.v1/Data/{AssetType}?sel={fields}&where={filter}&sort={sort}&page={limit},{offset}
```

Headers:
```
Authorization: Bearer {token}
Accept: application/json
```

### Query by OID (GET single asset)
```
GET {baseUrl}/rest-1.v1/Data/{AssetType}/{id}?sel={fields}
```

### Create (POST)
```
POST {baseUrl}/rest-1.v1/Data/{AssetType}
Content-Type: application/json
Authorization: Bearer {token}

{
  "Attributes": {
    "Name": { "value": "...", "act": "set" },
    "Scope": { "value": "Scope:1731677", "act": "set" },
    ...
  }
}
```

### Update (POST to existing asset)
```
POST {baseUrl}/rest-1.v1/Data/{AssetType}/{id}
Content-Type: application/json
Authorization: Bearer {token}

{
  "Attributes": {
    "FieldName": { "value": "...", "act": "set" }
  }
}
```

## Where Clause Syntax
- Equality: `Field='Value'`
- Not equal: `Field!='Value'`
- AND: use `;` separator — `Field1='A';Field2='B'`
- OR: use `|` separator — `Field1='A'|Field1='B'`
- Empty/null: `Field=''`
- Not empty: `Field!=''`
- Relation by OID: `Scope='Scope:1731677'`
- Nested attribute: `Scope.Name='DevOps'`, `Category.Name='Epic'`, `Status.Name='Done'`
- Combine: `Scope='Scope:1731677';Category.Name='Epic';AssetState!='255'`

## Sort Syntax
- Ascending: `Name`
- Descending: `-Name`

## Paging
- `page={pageSize},{offset}` — e.g., `page=50,0` returns first 50

## Inputs
- `baseUrl` (required): e.g. `https://www7.v1host.com/V1Production`
- `bearerToken` (required): API token for `Authorization: Bearer ...`
- `assetType` (required): One of `Epic`, `Story`, `Defect`, `Scope`, `Team`, `Timebox`, etc.
- `action` (optional, default `query`): `query`, `get`, `create`, `update`
- `id` (optional): Asset numeric ID for `get` or `update` actions
- `sel` (optional): Comma-delimited field selection
- `where` (optional): Filter clause
- `sort` (optional): Sort expression
- `limit` (optional, default `50`): Page size
- `offset` (optional, default `0`): Paging offset
- `find` (optional): Free text search
- `findin` (optional): Fields to search in
- `body` (optional): JSON body for `create`/`update` actions
- `noPrompt` (optional, default `false`): Non-interactive mode

## Execution

### Using curl
Agents and users can use curl directly. This is often simpler for one-off queries than writing a script.

**Query Epics in DevOps scope:**
```bash
curl -s -H "Authorization: Bearer <token>" \
  -H "Accept: application/json" \
  "https://www7.v1host.com/V1Production/rest-1.v1/Data/Epic?sel=Name,Number,Status.Name,Category.Name,Scope.Name&where=Scope%3D%27Scope%3A1731677%27%3BCategory.Name%3D%27Epic%27%3BAssetState!%3D%27255%27&sort=-ChangeDate&page=20,0"
```

**Query Stories under a specific Epic:**
```bash
curl -s -H "Authorization: Bearer <token>" \
  -H "Accept: application/json" \
  "https://www7.v1host.com/V1Production/rest-1.v1/Data/Story?sel=Name,Number,Status.Name,Team.Name,Timebox.Name,Estimate&where=Super%3D%27Epic%3A12345%27%3BAssetState!%3D%27255%27&sort=-ChangeDate&page=100,0"
```

**Query orphaned Stories (no parent Epic) in a sub-scope:**
```bash
curl -s -H "Authorization: Bearer <token>" \
  -H "Accept: application/json" \
  "https://www7.v1host.com/V1Production/rest-1.v1/Data/Story?sel=Name,Number,Status.Name,Team.Name,Timebox.Name&where=Scope.Name%3D%2726.1+DevOps%27%3BSuper%3D%27%27%3BAssetState!%3D%27255%27&sort=-ChangeDate&page=200,0"
```

**Create a Feature under a parent Epic:**
```bash
curl -s -X POST \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  "https://www7.v1host.com/V1Production/rest-1.v1/Data/Epic" \
  -d '{
    "Attributes": {
      "Name": { "value": "My New Feature - 26.3", "act": "set" },
      "Scope": { "value": "Scope:1731677", "act": "set" },
      "Super": { "value": "Epic:17160", "act": "set" },
      "Category": { "value": "EpicCategory:148", "act": "set" }
    }
  }'
```

**Query all EpicCategory values:**
```bash
curl -s -H "Authorization: Bearer <token>" \
  -H "Accept: application/json" \
  "https://www7.v1host.com/V1Production/rest-1.v1/Data/EpicCategory?sel=Name&page=100,0"
```

**Query Teams in a scope:**
```bash
curl -s -H "Authorization: Bearer <token>" \
  -H "Accept: application/json" \
  "https://www7.v1host.com/V1Production/rest-1.v1/Data/Team?sel=Name&where=Scope.Name%3D%27DevOps%27&page=100,0"
```

## UI URL Pattern
To link to an asset in the Agility web UI:
```
https://www7.v1host.com/V1Production/{AssetType}.mvc/Summary?oidToken={AssetType}:{id}
```
Examples:
- Epic E-19550: `https://www7.v1host.com/V1Production/Epic.mvc/Summary?oidToken=Epic:3370498`
- Story S-125773: `https://www7.v1host.com/V1Production/Story.mvc/Summary?oidToken=Story:3459190`

Note: The `{id}` in the URL is the **OID number** (e.g., `3370498`), NOT the display number (e.g., `19550`). Use the `ID` or `id` field from API responses to construct these URLs.

## Configuration File
Default config file path: `./agility-rest.config.json` (next to `SKILL.md`)

Use this file to define:
- default selected fields per asset type
- default sort per asset type
- default page size
- default scope filter (DevOps)
- known fields per asset type
- guardrails (read-only mode, strict field validation)

Guardrail defaults:
- `guardrails.readOnlyByDefault: true` -> blocks POST/PUT unless `--action create` or `--action update` is explicit
- `guardrails.allowedEndpointPattern` -> only allows `/rest-1.v1/Data/<AssetType>` patterns
- `guardrails.strictFields: false` -> off by default (Agility has many fields; use config lists as guidance, not enforcement)

Override precedence (highest to lowest):
1. CLI args
2. Environment variables
3. Config file defaults
4. Built-in fallback defaults

## Environment Variables
- `AGILITY_BASE_URL`
- `AGILITY_BEARER_TOKEN`
- `AGILITY_DEFAULT_SCOPE`

## Agent Guidance
When an agent uses this skill, it should:
- **Always exclude deleted assets** by including `AssetState!='255'` in `where` clauses
- **Use OID references** for Scope, Super, Category relations (e.g., `Scope='Scope:1731677'`) for precision
- **Use `Category.Name`** to distinguish Epic subtypes: `Category.Name='Epic'`, `Category.Name='Feature'`, etc.
- **Check `Super=''`** to find orphaned Stories/Defects with no parent Epic
- **Use `Number`** field for display-friendly IDs (e.g., E-19550, S-125773, D-45678)
- **Use `id`** field from response for OID-based references and URL construction
- **Keep `limit` conservative** (20-50) unless bulk retrieval is needed
- **URL-encode `where` clauses** in curl — single quotes become `%27`, semicolons become `%3B`, equals becomes `%3D`, spaces become `+`
- **For creation**, always set `Scope` explicitly — it is NOT inherited from parent
- **For Epics/Features**, set `Category` to the correct `EpicCategory` OID (e.g., `EpicCategory:148` for Feature)
- Present results in **concise tabular format** when possible
- Include **UI links** for key assets using the URL pattern above

### Common EpicCategory OIDs (DevOps)
These are reference values; verify with a query if unsure:
- Epic: query `EpicCategory?where=Name='Epic'`
- Feature: `EpicCategory:148`
- Initiative: query `EpicCategory?where=Name='Initiative'`
- Sub-Feature: query `EpicCategory?where=Name='Sub-Feature'`

### DevOps Teams (26.1 scope)
Alphas, Apollo, Dry Bones, FI Deploy, Integrations, Judo, Lambdas, Mario, PM DevOps, Sonic

## Output
Success prints JSON:
- `requestUrl`: final URL used
- `status`: HTTP status
- `contentType`: response content type
- `total`: total matching assets (from API `total` field)
- `assets`: flattened display-ready asset rows
- `data`: parsed JSON response (raw API shape)

Errors print JSON to stderr:
- `code`: `INPUT | NETWORK | AUTH | INTERNAL`
- `message`
- `details`
