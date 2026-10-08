# TypeSafe-Jev - Implementation Analysis

**Extension Name:** *TypeSafe-Jev (jev-integration)*
**Universal Template Name:** *Jev Integration*
**Target Platform:** Linux

---

## Extension Overview

The TypeSafe-Jev Universal Extension integrates Stonebranch UAC workflows with the TypeSafe Jev System One AI decision API. It accepts unstructured context text and a JSON-defined set of typed questions, submits a single synchronous POST to the Jev `/v1/decide` endpoint, and writes the resulting typed decisions (categorical, boolean, numeric) and their calibrated probabilities back to UAC global variables using a configurable prefix. This enables downstream workflow gateways to branch on structured, AI-derived decisions via zero-parse variable references, eliminating brittle hardcoded conditions or slow text-generation LLM calls.

---

# Template Fields

## 1. Input Fields

**(action)**
- **Type**: Choice Field (Single-select)
- **Visible When**: always
- **Required When**: always
- **Options**:
  - `Decide` — Submit context and questions to the TypeSafe Jev API and write typed decisions to UAC global variables
- **Default Value**: `Decide`
- **Validation**:
  - Must be one of the options
- **Purpose**: Selects the operation to perform. Currently a single action; field present for extensibility and dispatcher conformance.

---

**(jev_api_key)**
- **Type**: Credential Field
- **Visible When**: always
- **Required When**: always
- **Validation**:
  - The `password` attribute of the credential must be non-empty after stripping whitespace. The `user` attribute is required by UAC credential definition but is not used by the extension.
- **Purpose**: Holds the TypeSafe Bearer API token. The token is read from the credential's `password` attribute and placed in the `Authorization: Bearer <token>` HTTP header for all Jev API calls.

---

**(context)**
- **Type**: Text Field (Large)
- **Visible When**: always
- **Required When**: always
- **Validation**:
  - Must be non-empty after stripping whitespace.
  - Must not contain unresolved UAC variable patterns (i.e., the literal string `${` must not appear in the received value, as this indicates a failed UAC substitution).
- **Purpose**: Unstructured text describing the situation, system state, or event that the Jev model must evaluate. UAC variable substitution is supported — operators may embed `${variable_name}` references that UAC resolves before the extension runs.
- **Example**: `"Task 'ETL-Load-Redshift' failed after 3 retries. Exit code 1. Output: JDBC connection timeout. Agent: UA-STONEBRANCH-K8S. Business Service: Finance."`

---

**(questions_json)**
- **Type**: Text Field (Large)
- **Visible When**: always
- **Required When**: always
- **Validation**:
  - Must be non-empty after stripping whitespace.
  - Must not contain unresolved UAC variable patterns (literal `${` must not be present after UAC substitution).
  - Must parse as valid JSON.
  - The parsed value must be a JSON array (list).
  - Each element of the array must be a JSON object containing both `id` (non-empty string) and `type` (one of `choice`, `noul`, `score`).
  - For objects with `type` = `choice`: a `choices` key must exist and must be a non-empty array of strings.
  - For objects with `type` = `score`: both `min` and `max` keys must exist as numeric values.
  - For objects with `type` = `noul`: no additional keys are required.
  - All validation must complete before the Jev API is called.
- **Purpose**: Defines the typed questions submitted to the Jev API. Supports three question types: `choice` (categorical selection), `noul` (yes/no with probability), `score` (numeric within a range). UAC variable substitution is supported.
- **Example**:
  ```json
  [
    {"id": "action", "type": "choice", "choices": ["retry", "escalate", "skip"]},
    {"id": "is_transient", "type": "noul"},
    {"id": "severity", "type": "score", "min": 1, "max": 5}
  ]
  ```

---

**(api_base_url)**
- **Type**: Text Field
- **Visible When**: always
- **Required When**: not required
- **Default Value**: `https://api.typesafe.ai`
- **Validation**:
  - When provided, must not end with a trailing slash.
- **Purpose**: Base URL of the TypeSafe Jev API. The extension appends `/v1/decide` to this value to form the full endpoint URL. Allows overriding the target environment (e.g., staging, on-premise deployment).
- **Example**: `https://api.typesafe.ai`

---

**(timeout_seconds)**
- **Type**: Int Field
- **Visible When**: always
- **Required When**: not required
- **Default Value**: `30`
- **Validation**:
  - Minimum value: `1` (enforced at template level)
- **Purpose**: Maximum seconds to wait for a response from the Jev API. Passed directly as the HTTP request timeout. Transient network delays beyond this value result in exit code `1`.

---

**(variable_prefix)**
- **Type**: Text Field
- **Visible When**: always
- **Required When**: not required
- **Default Value**: `JEV`
- **Validation**:
  - When provided, must be non-empty after stripping whitespace.
- **Purpose**: Prefix applied to all UAC global variable names written by this extension. Uppercased internally. Distinct prefixes allow multiple Jev task instances within the same workflow to write without variable name collisions. Example: prefix `JEV` produces variables `JEV_ACTION`, `JEV_ACTION_PROB`, `JEV_LOW_CONFIDENCE`.

---

**(confidence_threshold)**
- **Type**: Float Field
- **Visible When**: always
- **Required When**: not required
- **Default Value**: `0.0`
- **Validation**:
  - Minimum value: `0.0`, maximum value: `1.0` (enforced at template level)
- **Purpose**: Confidence gate. If any answer returned by the Jev API has a probability strictly below this value, the extension sets `{PREFIX}_LOW_CONFIDENCE=true`. Setting to `0.0` (default) disables the check — `{PREFIX}_LOW_CONFIDENCE` is always `false` when threshold is `0.0`.

---

## 2. Output Fields

**(answers_written)**
- **Type**: Text Output
- **Purpose**: Confirms the number of answers written and the variable prefix used. Provides at-a-glance visibility in the UAC task list and detail view. Set only on successful execution; left empty on any fatal error.
- **Examples**: `"3 answers → JEV_*"`, `"1 answers → TRIAGE_*"`

---

**(low_confidence)**
- **Type**: Text Output
- **Purpose**: Mirrors the `{PREFIX}_LOW_CONFIDENCE` global variable. Indicates whether any answer's probability fell below the configured threshold. Set only on successful execution; left empty on any fatal error.
- **Examples**: `"false"`, `"true"`

---

## 3. Field Ordering

The task form uses a **2-column grid layout**. Fields can be displayed in two ways:

- **Full-width fields**: Span both columns (typically for dropdowns, credentials, or primary selections)
- **Half-width fields**: Occupy one column, allowing two fields side-by-side (typically for related pairs)

**Layout Rules:**
- Credential fields ALWAYS span full-width (both columns)
- Group related fields side-by-side when logical (e.g., API base URL / timeout)
- Primary selection and large text input fields span full-width for prominence

**Field Order (Visual Layout):**

```
┌─────────────────────────────────────────┐
│                  action                 │  ← Full-width
├─────────────────────────────────────────┤
│               jev_api_key               │  ← Full-width (credential)
├─────────────────────────────────────────┤
│                 context                 │  ← Full-width (large text)
├─────────────────────────────────────────┤
│              questions_json             │  ← Full-width (large text)
├─────────────────────────────────────────┤
│    api_base_url    │  timeout_seconds   │  ← Half-width pair (API config)
├────────────────────┼────────────────────┤
│  variable_prefix   │ confidence_thresh. │  ← Half-width pair (output control)
├────────────────────┼────────────────────┤
│  answers_written   │  low_confidence    │  ← Half-width pair (output only)
└────────────────────┴────────────────────┘
```

---

# Actions

## Action: Decide

**Description**: Submits unstructured context text and a set of typed questions to the TypeSafe Jev `/v1/decide` API endpoint. Receives typed answers with calibrated probabilities and writes each answer and its probability to a UAC global variable using the configured prefix. Sets a low-confidence flag variable if any answer probability falls below the configured threshold. Populates output-only fields and emits a structured Extension Output JSON payload.

### Input Requirements

- **action** — dispatch selector (value: `Decide`)
- **jev_api_key** — Credential; `password` attribute holds the Bearer token
- **context** — the situation text submitted to the Jev API
- **questions_json** — JSON array of typed question definitions
- **api_base_url** — base URL for the Jev API (default: `https://api.typesafe.ai`)
- **timeout_seconds** — HTTP request timeout in seconds (default: `30`)
- **variable_prefix** — prefix for UAC global variable names (default: `JEV`)
- **confidence_threshold** — minimum acceptable answer probability (default: `0.0`)

### Execution Flow

**Step 1 — Startup Logging**
- Read the extension version from `extension.yml`.
- Determine the effective prefix: if `variable_prefix` is provided and non-empty after strip, uppercase it; otherwise use `JEV`.
- Parse `questions_json` length is unknown at this point; count will be logged after parse.
- Emit to STDOUT: `TypeSafe Jev v<version> | prefix=<PREFIX> | questions=<N>` (where N is filled in after Step 3).

**Step 2 — Input Validation (all checks before any network call)**

2a. Check `jev_api_key.password`: if empty or whitespace-only → raise `ValidationError` with message `ERROR: Field 'jev_api_key' is required but empty`, exit code `20`.

2b. Check `context`: if empty or whitespace-only → raise `ValidationError` with message `ERROR: Field 'context' is required but empty`, exit code `20`.
   - Check for unresolved UAC substitution: if the value contains the literal substring `${` → raise `ValidationError` with message `ERROR: Field 'context' was not substituted`, exit code `20`.

2c. Check `questions_json`: if empty or whitespace-only → raise `ValidationError` with message `ERROR: Field 'questions_json' is required but empty`, exit code `20`.
   - Check for unresolved UAC substitution: if the value contains the literal substring `${` → raise `ValidationError` with message `ERROR: Field 'questions_json' was not substituted`, exit code `20`.

**Step 3 — Questions Schema Validation**

3a. Attempt to parse `questions_json` as JSON. On parse failure → raise `ValidationError` with message `ERROR: questions_json is not valid JSON: <parse error message>`, exit code `20`.

3b. Verify the parsed value is a Python list. If not → raise `ValidationError` with message `ERROR: questions_json must be a JSON array`, exit code `20`.

3c. For each question object at index `i`:
   - Verify `id` key exists → on failure raise `ValidationError`: `ERROR: Question at index <i> is missing required key 'id'`, exit code `20`.
   - Verify `type` key exists → on failure raise `ValidationError`: `ERROR: Question at index <i> is missing required key 'type'`, exit code `20`.
   - Verify `type` value is one of `choice`, `noul`, `score` → on failure raise `ValidationError`: `ERROR: Unknown question type '<type>' at index <i>`, exit code `20`.
   - If `type` = `choice`: verify `choices` key exists and is a non-empty list → on failure raise `ValidationError`: `ERROR: Question '<id>' of type 'choice' must have a non-empty choices list`, exit code `20`.
   - If `type` = `score`: verify both `min` and `max` keys exist → on failure raise `ValidationError`: `ERROR: Question '<id>' of type 'score' must include 'min' and 'max'`, exit code `20`.

3d. Store the validated question list. N = count of questions.

3e. Emit to STDOUT (now that N is known): `TypeSafe Jev v<version> | prefix=<PREFIX> | questions=<N>` (this replaces the placeholder from Step 1 — the actual implementation emits this single line here after validation).

**Step 4 — API Call**

4a. Construct the request URL: `<api_base_url>/v1/decide`.

4b. Build the JSON request body:
```json
{
  "context": "<context field value>",
  "questions": [<validated question array>]
}
```

4c. Set request headers: `Authorization: Bearer <jev_api_key.password>`, `Content-Type: application/json`, `Accept: application/json`.

4d. Emit to STDOUT: `Calling TypeSafe Jev API at <api_base_url>/v1/decide ...`

4e. Send HTTP POST to the endpoint with the body and headers using a timeout of `timeout_seconds` seconds.

4f. Handle network-level errors:
   - Connection timeout → raise `NetworkError` with message `ERROR: Jev API request timed out after <timeout_seconds>s`, exit code `1`.
   - Any other connection error → raise `NetworkError` with message `ERROR: Jev API connection failed: <error detail>`, exit code `1`.

4g. Handle HTTP response errors:
   - Status `401` → raise `APIError` with message `ERROR: Jev API returned 401 — check API key credential`, exit code `1`.
   - Status `429` → raise `APIError` with message `ERROR: Jev API returned 429 — rate limit exceeded`, exit code `1`.
   - Status `5xx` → raise `APIError` with message `ERROR: Jev API returned <status>: <response body truncated to 500 characters>`, exit code `1`.
   - Any other non-2xx status → raise `APIError` with message `ERROR: Jev API returned <status>: <response body truncated to 500 characters>`, exit code `1`.

4h. Parse the response body as JSON. Verify the parsed object contains an `answers` key. If `answers` key is absent → raise `ResponseError` with message `ERROR: Jev API response missing 'answers' key`, exit code `1`.

4i. Extract the `answers` list from the response. Count = M (number of answers received).

4j. Emit to STDOUT: `Response received — <M> answers`

**Step 5 — Audit Output**

5a. Emit the raw JSON audit block to STDOUT:
```
=== TypeSafe Jev Response ===
<pretty-printed full JSON response body>
=============================
```

**Step 6 — Answer Processing and Variable Writeback**

6a. Determine effective prefix: uppercase value of `variable_prefix` field (or `JEV` if empty).

6b. Determine effective threshold: use `confidence_threshold` field value (default `0.0`).

6c. Initialize `low_confidence_flag = False`.

6d. For each answer object in the `answers` list (process in order received):
   - Extract `id` (string) and uppercase it → `ID_UPPER`.
   - Extract `value` (string as-is from API response).
   - Extract `probability` (float) and format to 4 decimal places → `PROB_STR` (e.g., `0.9100`).
   - Construct variable names: `VAR_NAME = <PREFIX>_<ID_UPPER>`, `PROB_VAR_NAME = <PREFIX>_<ID_UPPER>_PROB`.
   - Write `VAR_NAME` → `value` to UAC global variables (see writeback rules below).
   - Write `PROB_VAR_NAME` → `PROB_STR` to UAC global variables.
   - Emit to STDOUT: `<VAR_NAME>=<value>`
   - Emit to STDOUT: `<PROB_VAR_NAME>=<PROB_STR>`
   - If `probability` is strictly less than `confidence_threshold` AND `confidence_threshold` > `0.0`: set `low_confidence_flag = True`.

6e. Write `<PREFIX>_LOW_CONFIDENCE` → `"true"` if `low_confidence_flag` else `"false"` to UAC global variables.

6f. Emit to STDOUT: `<PREFIX>_LOW_CONFIDENCE=<true|false>`

**UAC Global Variable Writeback Rules:**
- Read environment variables `UIP_URL`, `UIP_USERID`, `UIP_PASSWORD`.
- If `UIP_URL` is absent or empty: log `WARNING: Could not write UAC variable '<name>': UIP_URL not set` for each variable and skip all writeback. Continue execution.
- For each variable, send HTTP POST to `{UIP_URL}/resources/globalvariable` with HTTP Basic Auth (`UIP_USERID:UIP_PASSWORD`) and body `{"name": "<VAR_NAME>", "value": "<VAR_VALUE>"}` (upsert semantics).
- If any individual POST fails for any reason (network error, HTTP error, timeout): log `WARNING: Could not write UAC variable '<VAR_NAME>': <reason>` and continue to the next variable. Do not abort execution.
- Writeback errors are always non-fatal.

**Step 7 — Output-Only Fields**

7a. Set `answers_written` output field to: `"<M> answers → <PREFIX>_*"` where M is the count of answers received from the API.

7b. Set `low_confidence` output field to: `"true"` if `low_confidence_flag` else `"false"`.

**Step 8 — Completion**

8a. Emit to STDOUT: `Done.`

8b. Emit Extension Output JSON `result` structure (see Output Examples below).

8c. Exit with code `0`.

**Fatal Error Handling (any step):**
- On any fatal error (ValidationError, NetworkError, APIError, ResponseError):
  - Log the error message to STDERR at ERROR level.
  - Do NOT populate `answers_written` or `low_confidence` output fields.
  - Emit Extension Output JSON `error` structure.
  - Exit with the error's associated exit code (`20` for ValidationError, `1` for all others).

### Output Examples

**STDOUT (success)**:
```
TypeSafe Jev v1.0.0 | prefix=JEV | questions=3
Calling TypeSafe Jev API at https://api.typesafe.ai/v1/decide ...
Response received — 3 answers
=== TypeSafe Jev Response ===
{
  "answers": [
    {"id": "action", "value": "retry", "probability": 0.91},
    {"id": "is_transient", "value": "true", "probability": 0.82},
    {"id": "severity", "value": "2.0", "probability": 0.75}
  ]
}
=============================
JEV_ACTION=retry
JEV_ACTION_PROB=0.9100
JEV_IS_TRANSIENT=true
JEV_IS_TRANSIENT_PROB=0.8200
JEV_SEVERITY=2.0
JEV_SEVERITY_PROB=0.7500
JEV_LOW_CONFIDENCE=false
Done.
```

**Extension Output result object (JSON)**:

The Extension Output also includes `exit_code`, `status_description`, and `invocation` elements added automatically during implementation.

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

The `answers` dict is keyed by the original question `id` (lowercase, as provided in `questions_json`). Each entry contains:
- `value`: the decided value as a string, matching the corresponding UAC global variable.
- `probability`: the calibrated probability as a float rounded to 4 decimal places.

**Extension Output error object (JSON — on failure)**:
```json
{
  "error": {
    "type": "ValidationError",
    "message": "questions_json is not valid JSON: ..."
  }
}
```

`error.type` is one of: `"ValidationError"` (exit code `20`), `"NetworkError"` (exit code `1`), `"APIError"` (exit code `1`), `"ResponseError"` (exit code `1`).

### Success Criteria

1. Jev API returns HTTP `200` or `201` with a valid JSON body containing an `answers` array.
2. All UAC global variables are written (or a non-fatal warning logged if UAC REST is unavailable).
3. All `KEY=VALUE` lines appear in task STDOUT for every answer and its probability, plus the `LOW_CONFIDENCE` flag.
4. Output-only fields `answers_written` and `low_confidence` are populated.
5. Extension Output JSON contains a `result` object with `prefix`, `answer_count`, `low_confidence`, and `answers` dict.
6. Extension exits with return code `0`.

---

# Progress Reporting

Progress reporting as a percentage of completion is not required. The extension reports progress solely through INFO-level log lines emitted to STDOUT at key milestones (startup, API call initiation, response received, completion). No progress bar or structured percentage output is implemented.

---

# Dynamic Choice Field Population

No Dynamic choice fields should be implemented. All field options are statically defined and no field values are populated programmatically at runtime.

---

# Cancellation Behavior

Default cancellation logic is used (TERM signal). If the UAC task is cancelled while an HTTP request to the Jev API is in flight, the `requests` library terminates the network call when it receives SIGTERM. No partial answers are written. No UAC global variable cleanup is required — variables either exist from a prior successful run or do not exist (first run). No custom cancellation code is required.

---

# Re-Run Behavior

Re-runs are treated as initial executions. On re-run, the extension follows the full execution flow from Step 1 through Step 8. UAC global variables from the prior run are overwritten with new values via the upsert mechanism. Output-only fields from the prior run are not consulted and do not affect execution. Each re-run is stateless and idempotent.

---

# Dynamic Commands

No Dynamic commands should be implemented.

---

# Utility Modules

## Required Utility Modules

### 1. JevAPIClient

**Purpose:** Encapsulates all HTTP communication with the TypeSafe Jev API, including request construction, authentication header injection, timeout enforcement, HTTP error classification, and response parsing.

**Required Capabilities:**

- Accept base URL, Bearer token, and timeout value at construction time.
- Build the complete `/v1/decide` endpoint URL by appending `/v1/decide` to the base URL.
- Construct the JSON request body from a context string and a validated questions list.
- Set required HTTP headers: `Authorization: Bearer <token>`, `Content-Type: application/json`, `Accept: application/json`.
- Execute HTTP POST with the configured timeout.
- Detect and classify connection timeout → `NetworkError`.
- Detect and classify any other connection failure → `NetworkError`.
- Detect HTTP status `401` → `APIError`.
- Detect HTTP status `429` → `APIError`.
- Detect HTTP status `5xx` or any other non-2xx → `APIError` with status code and truncated response body (max 500 characters) in the message.
- Parse the response body as JSON.
- Verify the parsed response contains the `answers` key → `ResponseError` if absent.
- Return the parsed response object to the caller.

**Used By:** Decide action

---

### 2. QuestionValidator

**Purpose:** Validates a raw `questions_json` string against the Jev question schema rules, producing a structured validated list or raising `ValidationError` with a precise error message.

**Required Capabilities:**

- Accept the raw `questions_json` string value.
- Attempt JSON parsing; on failure raise `ValidationError` with parse error message.
- Verify the parsed value is a list; on failure raise `ValidationError`.
- For each element at index `i`:
  - Verify presence of `id` key; on failure raise `ValidationError` with index.
  - Verify presence of `type` key; on failure raise `ValidationError` with index.
  - Verify `type` is one of `choice`, `noul`, `score`; on failure raise `ValidationError` with type value and index.
  - For `choice`: verify `choices` key exists and is a non-empty list; on failure raise `ValidationError` with question `id`.
  - For `score`: verify both `min` and `max` keys are present; on failure raise `ValidationError` with question `id`.
  - For `noul`: no additional key verification required.
- Return the validated list of question dicts on success.

**Used By:** Decide action (Step 3)

---

### 3. UACVariableWriter

**Purpose:** Writes UAC global variables via the UAC Controller REST API using injected environment credentials. All write failures are non-fatal — errors are logged as warnings and execution continues.

**Required Capabilities:**

**Environment Resolution:**
- Read `UIP_URL`, `UIP_USERID`, `UIP_PASSWORD` from the operating system environment at construction time.
- If `UIP_URL` is absent or empty, mark the writer as disabled; all subsequent write calls immediately log a warning and return without making network calls.

**Variable Writing:**
- For each write request, send HTTP POST to `{UIP_URL}/resources/globalvariable` with:
  - HTTP Basic Auth using `UIP_USERID` and `UIP_PASSWORD`.
  - JSON body: `{"name": "<VAR_NAME>", "value": "<VAR_VALUE>"}` (upsert semantics — creates or updates).
- If the POST raises any exception (timeout, connection error, HTTP error): log `WARNING: Could not write UAC variable '<VAR_NAME>': <reason>` and return. Do not propagate the exception.
- Log a warning and return gracefully for any failure condition.

**Batch Write Interface:**
- Accept a list of `(name, value)` string tuples and write each in sequence.
- Each write is independent — failure of one does not prevent writing subsequent variables.

**Used By:** Decide action (Step 6)

---

## Exception Mapping Strategy

**Input Validation Errors (exit code 20 — non-transient, must fix task definition):**
- Required field empty after strip → `ValidationError` (exit code 20, user input)
- Required field contains unresolved UAC substitution pattern → `ValidationError` (exit code 20, user configuration)
- `questions_json` is not valid JSON → `ValidationError` (exit code 20, user input)
- `questions_json` parses to a non-list → `ValidationError` (exit code 20, user input)
- Question missing `id` or `type` key → `ValidationError` (exit code 20, user input)
- Unknown question `type` value → `ValidationError` (exit code 20, user input)
- `choice` question has empty or absent `choices` array → `ValidationError` (exit code 20, user input)
- `score` question missing `min` or `max` → `ValidationError` (exit code 20, user input)

**Network Errors (exit code 1 — transient, retry may succeed):**
- HTTP request timeout → `NetworkError` (exit code 1, transient)
- Connection refused or unreachable host → `NetworkError` (exit code 1, transient)

**API Response Errors (exit code 1):**
- HTTP 401 Unauthorized → `APIError` (exit code 1, user configuration — invalid or expired token)
- HTTP 429 Too Many Requests → `APIError` (exit code 1, transient — rate limit)
- HTTP 5xx Server Error → `APIError` (exit code 1, transient — server-side issue)
- Any other non-2xx status → `APIError` (exit code 1)

**Response Structure Errors (exit code 1):**
- Response JSON missing `answers` key → `ResponseError` (exit code 1, system — unexpected API response shape)

**Exit Code Guide:**
- Exit code `0`: Successful execution
- Exit code `1`: Runtime failure (network, API, or response error) — retry may succeed
- Exit code `20`: Validation failure — task definition must be corrected before retry

---

# Dependencies

## 1. External API Dependencies

**1. TypeSafe Jev Decision API**
- **Endpoint**: `https://api.typesafe.ai/v1/decide` (default; configurable via `api_base_url` field)
- **Purpose**: Receives unstructured context and typed questions; returns typed decisions with calibrated probabilities
- **Protocol**: HTTPS
- **Method**: POST
- **Authentication**: HTTP Bearer token (`Authorization: Bearer <token>`) from UAC Credential `password` attribute
- **Response Format**: JSON — object containing `answers` array; each answer has `id`, `value`, and `probability` attributes
- **Data Sent**: `{"context": "<string>", "questions": [<array of typed question objects>]}`
- **Data Retrieved**: `{"answers": [{"id": "<string>", "value": "<string>", "probability": <float>}, ...]}`

**General API Requirements:**
- A TypeSafe API account and active Bearer token are required.
- The Bearer token must be stored in the `password` attribute of a UAC Credential referenced by the `jev_api_key` field.
- The API is versioned via the `/v1/` path prefix; no version pinning in the URL beyond this prefix is required.
- The API is synchronous — a single POST call produces the complete response; no polling or streaming is involved.

---

## 2. Python version dependency

Python `>= 3.11` is required.

---

## 3. Target Platform

**Linux only.** The extension targets Linux UAC agents. C extension modules with a confirmed `manylinux_2_17_x86_64` wheel are viable in addition to pure-Python modules. The sole 3pp dependency (`requests`) is pure-Python, so wheel compatibility constraints do not apply.

---

## 4. Python Library Dependencies

**1. requests**
- **Purpose**: HTTP client for both the TypeSafe Jev API call and the UAC Controller variable writeback REST calls
- **Version**: `2.34.2`
- **Installation**: `pip install requests==2.34.2`
- **Usage**: Used in `JevAPIClient` for the `POST /v1/decide` call and in `UACVariableWriter` for UAC global variable upsert calls
- **Features Used**: `requests.post()`, `requests.exceptions.Timeout`, `requests.exceptions.ConnectionError`, `Response.status_code`, `Response.json()`, `Response.text`, HTTP Basic Auth via `auth=` parameter

---

## 5. Python Standard Library Dependencies

**1. json**
- **Purpose**: Parsing the `questions_json` field value and formatting API response for the STDOUT audit block
- **Version**: Built-in (Python 3.11+)
- **Installation**: No installation required
- **Usage**: `json.loads()` in `QuestionValidator`, `json.dumps()` for pretty-printing the audit block in the Decide action
- **Features Used**: `json.loads`, `json.dumps` with `indent=2`

**2. os**
- **Purpose**: Reading UAC-injected environment variables (`UIP_URL`, `UIP_USERID`, `UIP_PASSWORD`) for variable writeback
- **Version**: Built-in (Python 3.11+)
- **Installation**: No installation required
- **Usage**: `os.environ.get()` in `UACVariableWriter`
- **Features Used**: `os.environ.get`

**3. logging**
- **Purpose**: Structured log output to STDERR at configurable log levels (INFO, DEBUG, WARNING, ERROR)
- **Version**: Built-in (Python 3.11+)
- **Installation**: No installation required
- **Usage**: Throughout all modules for INFO progress messages, WARNING for non-fatal writeback failures, ERROR for fatal exceptions
- **Features Used**: `logging.getLogger`, `logger.info`, `logger.warning`, `logger.error`

---

## 6. CLI Tool Dependencies

No Dependencies.

---

## 7. Environment Variables

**UIP_URL** (*string*, *optional — injected by UAC agent*):
- **Purpose**: Base URL of the UAC Controller REST API, used by `UACVariableWriter` to construct variable upsert endpoints
- **Default**: Not set — if absent, UAC variable writeback is skipped with a warning per variable
- **Usage**: Prepended to `/resources/globalvariable` to form the full writeback endpoint URL
- **Examples**: `https://ps1.stonebranchdev.cloud`

**UIP_USERID** (*string*, *optional — injected by UAC agent*):
- **Purpose**: UAC username for HTTP Basic Auth during variable writeback REST calls
- **Default**: Not set
- **Usage**: Passed as the `auth` username in `UACVariableWriter` POST requests
- **Examples**: `len`

**UIP_PASSWORD** (*string*, *optional — injected by UAC agent*):
- **Purpose**: UAC password for HTTP Basic Auth during variable writeback REST calls
- **Default**: Not set
- **Usage**: Passed as the `auth` password in `UACVariableWriter` POST requests
- **Examples**: *(configured in UAC agent environment)*
