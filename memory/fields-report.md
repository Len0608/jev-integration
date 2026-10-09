<!-- generated: 2026-10-09 -->
# Fields Analysis — Universal Extension v1.0.0

> Source: `/tmp/jev-integration/jev-integration/src/templates/template.json`
> Note: `fields.yml` was present but empty. All field definitions are authoritative from `template.json` (`templateType: "Extension"`).

## Complete Field Table

| # | name | label | fieldType | fieldMapping | required | requireIfVisible | default | showIfField | showIfFieldValue | requireIfField | requireIfFieldValue | fieldRestriction | extensionStatus | hint |
|---|------|-------|-----------|--------------|----------|-----------------|---------|-------------|-----------------|----------------|--------------------|--------------------|-----------------|------|
| 0 | `action` | Action | Choice | Choice Field 1 | false | false | `Decide` | — | — | — | — | No Restriction | false | Operation to perform. Currently only 'Decide' is supported. |
| 1 | `jev_api_key` | Jev API Key | Credential | Credential Field 1 | **true** | false | — | — | — | — | — | No Restriction | false | UAC credential whose password attribute holds the TypeSafe Bearer API token. |
| 2 | `context` | Context | Text | Large Text Field 1 | **true** | false | — | — | — | — | — | No Restriction | false | Unstructured text describing the situation the Jev model must evaluate. UAC variable substitution is supported. |
| 3 | `questions_json` | Questions JSON | Text | Large Text Field 2 | **true** | false | — | — | — | — | — | No Restriction | false | JSON array of typed question definitions (choice, noul, score). UAC variable substitution is supported. |
| 4 | `api_base_url` | API Base URL | Text | Text Field 1 | false | false | `https://api.typesafe.ai` | — | — | — | — | No Restriction | false | Base URL of the TypeSafe Jev API. The extension appends /v1/decide to form the full endpoint URL. |
| 5 | `timeout_seconds` | Timeout (Seconds) | Integer | Integer Field 1 | false | false | `30` | — | — | — | — | No Restriction | false | Maximum seconds to wait for a response from the Jev API. |
| 6 | `variable_prefix` | Variable Prefix | Text | Text Field 2 | false | false | `JEV` | — | — | — | — | No Restriction | false | Prefix applied to all UAC global variable names written by this extension. Uppercased internally. |
| 7 | `confidence_threshold` | Confidence Threshold | Float | Float Field 1 | false | false | `0.0` | — | — | — | — | No Restriction | false | Confidence gate (0.0–1.0). If any answer probability is below this value, LOW_CONFIDENCE is set to true. 0.0 disables the check. |
| 8 | `answers_written` | Answers Written | Text | Text Field 3 | false | false | — | — | — | — | — | **Output Only** | **true** | Number of answers written and the variable prefix used. Populated on successful execution. |
| 9 | `low_confidence` | Low Confidence | Text | Text Field 4 | false | false | — | — | — | — | — | **Output Only** | false | Mirrors the LOW_CONFIDENCE global variable. Indicates if any answer probability fell below the configured threshold. |

## Cross-References

### Always-Required Fields
- `jev_api_key` — UAC Credential holding the TypeSafe Bearer token
- `context` — Unstructured situation text (Text / Large Text Field 1)
- `questions_json` — JSON array of typed question definitions (Text / Large Text Field 2)

### Conditionally-Required Fields
- None — no `requireIfField` / `requireIfFieldValue` relationships are defined on any field.

### Field Visibility Dependencies (showIfField)
- None — all fields are always visible; no `showIfField` relationships are defined.

### Output-Only Fields (written by extension, not editable by user)
- `answers_written` (`Text Field 3`) — `extensionStatus: true`, `preserveOutputOnRerun: true`, shown in default list view
- `low_confidence` (`Text Field 4`) — `extensionStatus: false`, `preserveOutputOnRerun: true`

### Mutually Exclusive Options
- None identified. The `action` field has a single choice (`Decide`) with no branching visibility or requirement logic.

### Additional Notes
- `action` field: only one choice value (`Decide`) is currently defined — the field is decorative/forward-looking.
- `timeout_seconds`: has `intFieldMin: 1`; no maximum bound set.
- `confidence_threshold`: `0.0` default effectively disables the confidence gate.
- `variable_prefix` is uppercased internally; default is `JEV`, producing global variables such as `${JEV_<question_name>}`.
- `variablePrefix` at template level is `ops_var` — UAC uses this to expose fields to the script as `${ops_var_<name>}`.
