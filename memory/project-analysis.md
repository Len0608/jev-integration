<!-- generated: 2026-10-08 00:00 -->

# Project Analysis — Universal Extension v1.0.0

## Purpose

Submits unstructured context and typed questions to the TypeSafe Jev AI decision API and writes typed decisions with calibrated probabilities to UAC global variables.

---

## Execution Modes / Actions

| Mode | Trigger | Description |
|------|---------|-------------|
| Decide | `action` = `"Decide"` | Validates inputs and questions schema, calls `POST /v1/decide` on the TypeSafe Jev API, writes one UAC global variable per answer (`{PREFIX}_{ID}` and `{PREFIX}_{ID}_PROB`), writes `{PREFIX}_LOW_CONFIDENCE`, and updates the real-time output fields `answers_written` and `low_confidence`. |

No dynamic choice commands or extension commands are implemented.

---

## Complete Field Table

| Seq | Name | Label | fieldMapping | Type | Required | Default | Restriction | Description |
|-----|------|-------|-------------|------|----------|---------|-------------|-------------|
| 0 | `action` | Action | Choice Field 1 | Choice | No | `Decide` | No Restriction | Operation to perform. Currently only `Decide` is supported. Single-choice; `choiceAllowMultiple=false`. |
| 1 | `jev_api_key` | Jev API Key | Credential Field 1 | Credential | Yes | — | No Restriction | UAC credential whose **password** attribute holds the TypeSafe Bearer API token. |
| 2 | `context` | Context | Large Text Field 1 | Text (Plain) | Yes | — | No Restriction | Unstructured text describing the situation the Jev model must evaluate. UAC variable substitution is supported. |
| 3 | `questions_json` | Questions JSON | Large Text Field 2 | Text (Plain) | Yes | — | No Restriction | JSON array of typed question definitions (`choice`, `noul`, `score`). UAC variable substitution is supported. |
| 4 | `api_base_url` | API Base URL | Text Field 1 | Text (Plain) | No | `https://api.typesafe.ai` | No Restriction | Base URL of the TypeSafe Jev API. The extension appends `/v1/decide` to form the full endpoint URL. Must not end with a trailing slash. |
| 5 | `timeout_seconds` | Timeout (Seconds) | Integer Field 1 | Integer | No | `30` | No Restriction | Maximum seconds to wait for a response from the Jev API. Must be ≥ 1. |
| 6 | `variable_prefix` | Variable Prefix | Text Field 2 | Text (Plain) | No | `JEV` | No Restriction | Prefix applied to all UAC global variable names written by this extension. Uppercased internally. Must not be empty when provided. |
| 7 | `confidence_threshold` | Confidence Threshold | Float Field 1 | Float | No | `0.0` | No Restriction | Confidence gate (0.0–1.0). If any answer probability is below this value, `LOW_CONFIDENCE` is set to `true`. `0.0` disables the check. |
| 8 | `answers_written` | Answers Written | Text Field 3 | Text (Plain) | No | — | Output Only | Number of answers written and the variable prefix used. Populated on successful execution. `extensionStatus=true`; shown in list view. |
| 9 | `low_confidence` | Low Confidence | Text Field 4 | Text (Plain) | No | — | Output Only | Mirrors the `{PREFIX}_LOW_CONFIDENCE` global variable. Indicates if any answer probability fell below the configured threshold. |

---

## Cross-References

**Always required (UAC-enforced):**
- `jev_api_key` — `required: true`
- `context` — `required: true`
- `questions_json` — `required: true`

**Conditionally required (runtime validation):**
- `jev_api_key.password` — must be non-empty after stripping whitespace
- `context` — must be non-empty and must not contain unresolved `${...}` patterns
- `questions_json` — must be non-empty and must not contain unresolved `${...}` patterns

**Visibility dependencies:**
- No `showIfField` references — all fields are always visible.

**Conditional requirements:**
- No `requireIfField` references — UAC-level conditional requirements are not used.

**Output-only fields (read-only from form perspective):**
- `answers_written` (seq 8) — `fieldRestriction: "Output Only"`, `preserveOutputOnRerun: true`
- `low_confidence` (seq 9) — `fieldRestriction: "Output Only"`, `preserveOutputOnRerun: true`

**Mutually exclusive / interdependent:**
- `variable_prefix` drives all UAC global variable names (`{PREFIX}_{ID}`, `{PREFIX}_{ID}_PROB`, `{PREFIX}_LOW_CONFIDENCE`); changing it after a run produces differently named variables.
- `confidence_threshold = 0.0` disables the low-confidence check; any value > 0 activates it.

---

## Error Handling

| Scope | Error | Handling |
|-------|-------|---------|
| Input — action | Invalid action value (not `Decide`) | `DataValidationError` — exit code 20 |
| Input — jev_api_key | Credential password empty or whitespace | `ValidationError` — exit code 20 |
| Input — context | Empty or whitespace | `ValidationError` — exit code 20 |
| Input — context | Contains unresolved `${...}` pattern | `ValidationError` — exit code 20 |
| Input — questions_json | Empty or whitespace | `ValidationError` — exit code 20 |
| Input — questions_json | Contains unresolved `${...}` pattern | `ValidationError` — exit code 20 |
| Input — api_base_url | Ends with trailing slash | `DataValidationError` — exit code 20 |
| Input — timeout_seconds | Value < 1 | `DataValidationError` — exit code 20 |
| Input — variable_prefix | Empty after stripping when provided | `DataValidationError` — exit code 20 |
| Input — confidence_threshold | Outside range 0.0–1.0 | `DataValidationError` — exit code 20 |
| Questions schema | Not valid JSON | `ValidationError` — exit code 20 |
| Questions schema | Parsed value is not a JSON array | `ValidationError` — exit code 20 |
| Questions schema | Question missing `id` or `type` key | `ValidationError` — exit code 20 |
| Questions schema | `type` not one of `choice`, `noul`, `score` | `ValidationError` — exit code 20 |
| Questions schema | `choice` question has absent or empty `choices` list | `ValidationError` — exit code 20 |
| Questions schema | `score` question missing `min` or `max` key | `ValidationError` — exit code 20 |
| Network | HTTP request timeout (`requests.Timeout`) | `NetworkError` — exit code 1; retry may succeed |
| Network | Host unreachable / connection refused | `NetworkError` — exit code 1; retry may succeed |
| API | HTTP 401 Unauthorized | `APIError` — exit code 1; requires credential fix |
| API | HTTP 429 Too Many Requests | `APIError` — exit code 1; retry after back-off |
| API | HTTP 5xx Server Error | `APIError` — exit code 1; retry may succeed |
| API | Any other non-2xx status | `APIError` — exit code 1 |
| API Response | Response body cannot be parsed as JSON | `ResponseError` — exit code 1; investigate API contract |
| API Response | Parsed response missing `answers` key | `ResponseError` — exit code 1; investigate API contract |
| System | Any uncaught exception | `UnexpectedSystemError` — exit code 1; full traceback logged |
