# Requirements Completeness Assessment

The requirements document is classified as **High Detail**. The core intent is clearly established: a single-action UAC Universal Extension that calls the TypeSafe Jev Decision API, writes typed answers to UAC global variables, and provides structured output for workflow branching. The document specifies input fields with field types, defaults, and validation rules; a full STDOUT output format with exact line patterns; a comprehensive error table with precise status description strings; authentication requirements; environment variable usage; and all operational behaviors (cancel, re-run, dynamic commands). The questions below address four specific conflicts and gaps identified against UAC architecture best practices.

---

# Platform Compatibility

**Platform Compatibility from Requirements**: Linux  
**Platform Compatibility Agreement**: Linux *(confirmed — no question required)*

---

# Python Modules and Versions

## Researched Modules

**requests**
- **Module Purpose**: HTTP client for the TypeSafe Jev API call and UAC variable writeback REST calls
- **Version**: 2.34.2
- **Type**: Pure-Python

> All other dependencies (`json`, `logging`, `os`, `sys`) are Python standard library — no PyPI check required.

## Agreed Python Modules and Versions

| Module Name | Module Purpose | Version | Type |
|---|---|---|---|
| *(placeholder — to be filled once answers are confirmed)* | | | |

---

# Question Rationale

Four questions are raised. All reflect genuine conflicts or gaps between the requirements document and UAC architecture best practices sourced from the architect notes:

1. **Return code differentiation** — the requirements use exit code `1` for all failures, while architecture best practices reserve `20` for input validation errors and `1` for runtime failures. This distinction enables workflow branches to handle configuration mistakes differently from transient failures.
2. **Field types for numeric inputs** — the requirements specify `timeout_seconds` and `confidence_threshold` as Text fields with Python-level validation, while UAC provides native Integer and Float field types that enforce type constraints at the template level, simplifying the extension code and improving the task definition UI.
3. **Extension Output JSON** — the requirements thoroughly define STDOUT but do not specify a machine-processable Extension Output JSON structure, which is strongly recommended by the architecture for all extensions and enables downstream automation and audit trail use cases.
4. **Output Only fields** — no output-only fields are defined for display in the UAC task view or task list, which is an architectural recommendation for surfacing key operational values without requiring users to open the full STDOUT log.

---

# Clarifying Questions for Requirements Refinement

## Critical Decision Path Questions

**Question 1**: Should input validation failures use return code `20` (separate from runtime failures at `1`), or should all failures use `1` as currently specified?

- **Question Type**: Clarification on existing requirement
- **Context & Resources**: The current requirements assign exit code `1` to all failure scenarios — both input validation failures (empty required fields, malformed `questions_json`, invalid `confidence_threshold` format) and runtime failures (Jev API 4xx/5xx, network timeout, missing `answers` key in response). UAC architecture best practices differentiate these two categories:
  - **`1`** — runtime/execution failure: API unreachable, authentication rejected, rate limited, server error, response structure unexpected. These are failures that *might* succeed on retry.
  - **`20`** — validation failure: required field empty, field not substituted, `confidence_threshold` out of range, `timeout_seconds` non-integer, `questions_json` not valid JSON or invalid schema. These are configuration mistakes that *cannot* succeed on retry — the task definition itself must be corrected.
  
  Using distinct codes allows UAC workflow designers to route validation errors to a "fix configuration" branch and runtime errors to a "retry or escalate" branch, without needing to parse the status description string.

  **Validation failures that would use `20` under this option:**
  - Required field empty or not substituted
  - `confidence_threshold` not a float or out of `[0.0, 1.0]`
  - `timeout_seconds` not a positive integer
  - `questions_json` not valid JSON
  - `questions_json` not a list
  - Any question missing `id` or `type`
  - Unknown question type
  - `choice` question missing `choices`
  - `score` question missing `min`/`max`

  **Runtime failures that would remain at `1`:**
  - Network timeout
  - Jev API 401, 429, 5xx
  - Jev API response missing `answers` key
  - `requests` library not installed

- **Question Dependencies**: None
- **Recommended Answer**: **Option B — Use `20` for validation errors and `1` for runtime failures**, aligned with UAC architecture best practices. This enables cleaner workflow branching and is consistent with how well-designed extensions behave on ps1.
- **Rationale**: Validation errors are categorically different from runtime errors: they indicate that the task was configured incorrectly and no amount of retrying will fix them. Separating them at the exit code level makes this distinction actionable in the workflow without string-parsing the status description.
- **Trade-offs**: Option A (keep `1` for all) is simpler — one error branch in the workflow. Option B adds a second branch but gives workflows the information they need to respond appropriately. The validation/runtime split is idiomatic in UAC extension design.
- **Requirement Impact**: The error table in section 4.2 would be updated: all rows under "Input validation errors" and "Question schema errors" would show return code `20` instead of `1`. Runtime rows (Network timeout, Jev API errors, Response structure errors) remain `1`. No other changes.
- **User's Answer**: Use `20` for validation errors and `1` for runtime failures

---

## Essential Input/Output Questions

**Question 2**: Should `timeout_seconds` and `confidence_threshold` use native UAC Integer and Float field types instead of Text fields?

- **Question Type**: Clarification on existing requirement
- **Context & Resources**: The current requirements specify both `timeout_seconds` and `confidence_threshold` as Text (Plain) fields with Python-level validation code that parses and range-checks the string values. UAC provides native numeric field types that shift this validation to the template layer:

  | Field | Current Type | Alternative Type | Template-Level Constraint |
  |---|---|---|---|
  | `timeout_seconds` | Text | Integer Field | `intFieldMin: 1` (positive integer enforced at task definition time) |
  | `confidence_threshold` | Text | Float Field | `floatFieldMin: 0.0`, `floatFieldMax: 1.0` (range enforced at task definition time) |

  **Benefits of native types:**
  - The UAC UI renders a numeric input widget instead of a free-text box, reducing user input errors.
  - Type and range validation fires when the task definition is saved — before execution — rather than at runtime. This eliminates the need for the `confidence_threshold must be a float between 0.0 and 1.0` and `timeout_seconds must be a positive integer` error rows in the error table.
  - Extension code becomes simpler: `input_data.timeout_seconds` returns `int | None` and `input_data.confidence_threshold` returns `float | None` directly, with no parsing or format-error handling needed.

  **Consideration for Text:** Both fields are optional with defaults. Text fields make the "leave blank to use default" pattern slightly more explicit in the UI hint. Native fields show blank/empty to mean "use default" equally well when the field is not marked required.

- **Question Dependencies**: None
- **Recommended Answer**: **Option B — Use Integer Field for `timeout_seconds` and Float Field for `confidence_threshold`**, with template-level min/max constraints. This removes validation code for these two fields and provides better UX.
- **Rationale**: Native numeric field types are the simplest correct solution. They remove two validation error paths from the code, reduce the error table by two rows, and give users a numeric input widget rather than a text box. The functional behavior is identical.
- **Trade-offs**: Option A (keep Text) requires the extension to validate and parse these values, but keeps the field UI consistent (all optional configuration fields are text boxes). Option B (native types) is slightly more type-safe and reduces code complexity, at no behavioral cost.
- **Requirement Impact**: 
  - Section 3.3: `timeout_seconds` field type changes from "Text" to "Integer"; `confidence_threshold` field type changes from "Text" to "Float".
  - Section 4.2: Remove the "Invalid confidence threshold" and "Invalid timeout" rows from the error table — these are now enforced at template level.
- **User's Answer**: Use Integer Field for `timeout_seconds` and Float Field for `confidence_threshold`

---

## Extension Output & UI Display Questions

**Question 3**: What should the Extension Output JSON contain?

- **Question Type**: New Discussion topic
- **Context & Resources**: The requirements specify STDOUT output in detail but do not define an Extension Output JSON. Extension Output is distinct from STDOUT:

  | Channel | When available | Consumer | Format |
  |---|---|---|---|
  | STDOUT | During execution | Human (UAC task log viewer) | Human-readable lines |
  | Extension Output | At terminal state only | Automation, API queries, audit tools | Machine-processable JSON |

  Extension Output is queryable via the UAC REST API after the task completes and is recommended for all extensions as an audit and integration surface. It is separate from the `invocation` element (handled automatically by the framework) — only the `result` and `error` sections need to be defined.

  **Proposed `result` structure for success:**
  ```json
  {
    "result": {
      "prefix": "JEV",
      "answer_count": 3,
      "low_confidence": false,
      "answers": {
        "action":       { "value": "retry",  "probability": 0.9100 },
        "is_transient": { "value": "true",   "probability": 0.8200 },
        "severity":     { "value": "2.0",    "probability": 0.7500 }
      }
    }
  }
  ```

  **Proposed `error` structure for failure:**
  ```json
  {
    "error": {
      "type": "ValidationError",
      "message": "questions_json is not valid JSON: ..."
    }
  }
  ```

  `error.type` would be one of: `"ValidationError"`, `"NetworkError"`, `"APIError"`, `"ResponseError"`.

  **Options:**
  - **O1**: No Extension Output (omit; rely entirely on STDOUT and UAC global variables).
  - **O2**: Minimal Extension Output — only `low_confidence` flag and `answer_count` in `result`.
  - **O3**: Full structured Extension Output as shown above — answers dict keyed by question ID, each with `value` and `probability`, plus `prefix`, `low_confidence`, `answer_count`; and `error` object on failure.

- **Question Dependencies**: None
- **Recommended Answer**: **Option O3 — Full structured Extension Output** as shown above. The answers dict (keyed by question ID) is especially valuable because it provides a single queryable JSON payload that downstream automation can parse without reading STDOUT or UAC global variables individually.
- **Rationale**: The extension already writes all answer data to STDOUT and UAC global variables. Providing the same data in a structured Extension Output adds no behavioral complexity and creates an additional integration surface for automation and audit tools that consume the UAC REST API. The `error.type` field allows downstream code to differentiate error categories programmatically.
- **Trade-offs**: O1 is the simplest implementation. O3 adds a small amount of code to build and emit the JSON payload but significantly increases the extension's utility in downstream automation contexts.
- **Requirement Impact**: Section 4.1 (On Success) would add an "Extension Output" subsection describing the `result` structure. Section 4.2 (On Error) would add an "Extension Output" note describing the `error` structure.
- **User's Answer**: Full structured Extension Output (O3) — answers dict keyed by question ID, low_confidence, prefix, answer_count on success; error type and message on failure

---

**Question 4**: Should the extension populate any Output Only fields visible in the UAC task view and task list?

- **Question Type**: New Discussion topic
- **Context & Resources**: The current requirements do not define any Output Only fields. These are template fields with `fieldRestriction: "Output Only"` that the extension populates at runtime; they appear in the UAC task execution detail and optionally in the task list view. They let operators assess task outcomes at a glance without opening the full STDOUT log.

  UAC architecture best practices recommend 2–3 short output-only fields for most extensions. For this extension, the most operationally useful candidates are:

  | Candidate Field | Value Example | Why Useful |
  |---|---|---|
  | **Answers Written** (Text) | `"3 answers → JEV_*"` | Confirms variable writeback and prefix at a glance; immediately visible in the task list |
  | **Low Confidence** (Text) | `"true"` or `"false"` | Lets operators scan the task list for confidence failures without reading STDOUT; mirrors the `{PREFIX}_LOW_CONFIDENCE` global variable |

  A Boolean field could also be used for Low Confidence, but a Text field displaying `"true"`/`"false"` is consistent with the global variable value and avoids the checkbox rendering which can be less legible in task lists at scale.

  **Options:**
  - **O1**: No Output Only fields — results are visible only in STDOUT and UAC global variables.
  - **O2**: One field — **Low Confidence** (Text, e.g., `"false"`).
  - **O3**: Two fields — **Answers Written** (Text, e.g., `"3 answers → JEV_*"`) and **Low Confidence** (Text, e.g., `"false"`).

- **Question Dependencies**: None
- **Recommended Answer**: **Option O3 — Two output-only fields** (Answers Written + Low Confidence). Both are short, immediately readable, and directly represent the two most important operational outcomes of each execution.
- **Rationale**: The "Answers Written" field confirms that the Jev API returned the expected number of answers and that variable writeback succeeded (or shows `"0 answers"` if the API returned an unexpected response). The "Low Confidence" field mirrors the `{PREFIX}_LOW_CONFIDENCE` global variable and lets operators identify low-confidence executions without querying variables.
- **Trade-offs**: O1 keeps the template simpler. O3 adds two fields and minor output-populating code in the extension but significantly improves operational visibility in the UAC task list and detail views, especially in workflows where multiple Jev tasks run.
- **Requirement Impact**: A new section "3.5 Output Only Fields" would be added to the Input Requirements section describing the two fields. Section 4.1 would be updated to note that these fields are set on success. Section 4.2 would note that on fatal error both fields are left empty.
- **User's Answer**: Two output-only fields — "Answers Written" (Text) and "Low Confidence" (Text)
