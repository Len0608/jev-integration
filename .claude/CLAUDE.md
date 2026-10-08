## Automation Mode (Pipeline Context)

This session runs inside the **Integration Self Service automated pipeline** (`UE_CA_SESSION=TRUE`).

**Critical constraints — do not violate these:**
- **NEVER call `AskUserQuestion`** — no human is available; the pipeline will hang and time out
- **NEVER call `Agent` or `Task` tools to spawn sub-agents** — only inline execution is permitted
- Make all decisions autonomously; prefer recommended defaults over asking
- Complete every step and write all output files without waiting for confirmation

---

## Workspace Layout

```
<workspace>/
├── .claude/
│   └── CLAUDE.md              ← this file
├── memory/
│   ├── requirements.md        ← user requirements — READ FIRST at every stage
│   ├── environment.md         ← UAC controller URL, agent name, workspace info
│   ├── analysis.md            ← implementation blueprint (output of analysis phase)
│   └── agents-memory/
│       ├── requirements-QnA.md
│       └── refined_requirements.md
├── extension-code/
│   ├── src/
│   │   ├── extension.yml      ← extension identity: name, version, api_level
│   │   ├── extension.py       ← main dispatcher — preserve its structure
│   │   ├── exceptions.py      ← custom exception hierarchy
│   │   ├── manager.py         ← ExtensionManager singleton
│   │   ├── fields/
│   │   │   ├── input.py       ← InputFields dataclass (one field per template field)
│   │   │   └── output.py      ← OutputFields dataclass (output/status fields)
│   │   ├── actions/
│   │   │   ├── __init__.py    ← ACTION_MAPPER dict
│   │   │   └── <action>.py    ← one file per action
│   │   └── templates/
│   │       └── template.json  ← UAC task template definition
│   └── requirements.txt       ← Python 3pp dependencies
├── acceptance_testing/        ← generated test task JSON files
└── ue-dev-env/                ← Python venv managed by uip — do not modify
```

**At the start of every stage:** read `memory/requirements.md` and `memory/environment.md` first.  
**After analysis completes:** read `memory/analysis.md` before implementing.

---

## UAC Extension Rules (violations cause import or runtime failures)

### template.json
- `showIfField` / `requireIfField` must reference the field's **`fieldMapping`** value (e.g. `"Choice Field 1"`), NOT the field's `name` (e.g. `"action"`) — UAC silently ignores name-based references
- `choiceFields` (for dynamic choices) is also a list of `fieldMapping` values
- `fieldType: "Large Text"` is **invalid** — UAC only accepts `"Plain"` for text fields
- Every field sysId must be **globally unique** across all templates in the UAC instance
- `variablePrefix` should be `"ops_var"` so scripts can reference fields as `${ops_var_<fieldname>}`

### Python code
- **Always use absolute imports** — relative imports (`from ..exceptions import`) break in UAC zip loading
- **All imports at the top** — never import inside functions
- **Type hints required** on all fields and method signatures
- The `InputFields` dataclass must have one entry for **every** field in `template.json` — missing fields cause runtime KeyError
- `extension.py` dispatches via `input_data.<choice_field>.value` — if the dispatch field is not named `action`, update the reference to match the actual field name in InputFields

### Dependencies (requirements.txt)
- All packages must have a **manylinux_2_17_x86_64 wheel** on PyPI — pure-Python packages are always fine; C-extension packages require a compatible wheel
- Prefer `requests` over `httpx` (broader wheel availability)
- Use `/ue-ca:checking-python-module-versions` skill before adding any new C-extension dependency

---

## Available Skills

| Skill | Purpose |
|---|---|
| `/ue-ca:retrieving-context` | Load architecture docs, field reference docs, template examples |
| `/ue-ca:managing-universal-controller` | Query UAC agents, credentials, tasks via REST API |
| `/ue-ca:checking-python-module-versions` | Verify PyPI wheel availability for target platform |

Use `/ue-ca:retrieving-context` when you need the full architecture guide, field type specs, or template.json structure reference.

---

## Output Style Override for Interactive Q&A Steps

When a command explicitly instructs you to present rich context before asking
a question (e.g., Question Type, Context, Rationale, Trade-offs, Resources),
the general brevity guidelines are suspended for that step.
Full context MUST be written as text output to the user before any
AskUserQuestion tool call is made.

---

## UAC REST API — Critical Rules for Extension Scripts

### Correct Base URL

The UAC API base is `{host}/resources/...` — NOT `/uc/resources/...`. The `/uc/` prefix returns 404.

Example: `https://ps1.stonebranchdev.cloud/resources/task/list`

### How Field Values Reach Scripts

UAC substitutes field values directly into the script text at launch time — scripts do NOT read field values from os.environ or argparse.

Access a field value in your script as:

```
${ops_var_<fieldname>}
```

Where `<fieldname>` is the field's `name` attribute in template.json, and the template's `variablePrefix` is `"ops_var"`.

Example: a field with `"name": "target_host"` → access in script as `${ops_var_target_host}`.

**Never use**: `os.environ.get("target_host")` or `parser.add_argument("--target-host")` — these do not work.

### Required Top-Level template.json Fields

Every template.json must include these keys at the top level (not nested in a field):

```json
{
  "minReleaseLevel": "7.0.0.0",
  "exportReleaseLevel": "8.0.0.0",
  "sendEnvironment": "Launch",
  "sendVariables": "None",
  "agentFieldsRestriction": "No Restriction",
  "credentialFieldsRestriction": "No Restriction"
}
```

### Field Reference Rules

- `showIfField` and `requireIfField` values in template.json MUST use the **`fieldMapping`** value (e.g., `"Choice Field 1"`), NOT the field's `name` attribute.
- Every field must have a **globally unique `sysId`** — a 32-character hex string with no dashes. Reusing a sysId that exists in another UAC template causes "Unexpected request failure" on import.
- `fieldType` must be `"Plain"` for multi-line text — `"Large Text"` is rejected by UAC.

### HTTP Method Quirk

Some UAC endpoints only accept POST. If a GET returns HTTP 405, retry as POST with body `{}`.

### Common API Endpoints

| Action | Method | Path |
|--------|--------|------|
| List tasks | GET | `/resources/task/list` |
| Launch task | POST | `/resources/task/launch` |
| List agents | GET | `/resources/agent/list` |
| Get task instance output | GET | `/resources/taskinstance/retrieveoutput` |
| Rerun instance | POST | `/resources/taskinstance/rerun` |
| Import template | POST | `/resources/universaltemplate/importtemplate` |

Authentication: HTTP Basic Auth (`user:password`).

## Project Type

**Type:** Unknown — manual classification required
