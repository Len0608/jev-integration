# Universal Extension Requirements (Refined)

**Extension Name:** TypeSafe-Jev
**Original Generated:** 2026-10-08 08:30 UTC
**Refined:** 2026-10-08 08:30 UTC
**Requirements Completeness:** High Detail
**Target Platform:** Linux

---

# Table of Contents

1. [Overview](#overview)
2. [Actions](#actions)
   - 2.1 [Decide — Call TypeSafe Jev Decision API](#21-decide--call-typesafe-jev-decision-api)
3. [Input Requirements](#input-requirements)
   - 3.1 [Authentication](#31-authentication-fields)
   - 3.2 [Decision Context](#32-decision-context-fields)
   - 3.3 [API Configuration](#33-api-configuration-fields)
   - 3.4 [Output Control](#34-output-control-fields)
4. [Output Requirements](#output-requirements)
   - 4.1 [On Success](#41-on-success)
   - 4.2 [On Error](#42-on-error)
5. [Authentication Requirements](#authentication-requirements)
6. [Environment Variables](#environment-variables)
7. [Operational Behavior](#operational-behavior)
8. [Implementation Notes](#implementation-notes)
   - 8.1 [Python Compatibility](#81-python-compatibility)
   - 8.2 [Target Platform](#82-target-platform)
   - 8.3 [Third-Party Services and Tools](#83-third-party-services-and-tools)
   - 8.4 [Error Handling](#84-error-handling)
   - 8.5 [Resource Cleanup](#85-resource-cleanup)
9. [Requirements Summary](#requirements-summary)
10. [Document Change History](#document-change-history)
11. [References](#references)

---

# Overview

This document specifies the functional and operational requirements for the TypeSafe-Jev Universal Extension for Stonebranch UAC.

**Integration Purpose:** The extension provides UAC workflows with a reusable, typed decision primitive by wrapping the TypeSafe Jev System One AI API. It accepts unstructured context text and a set of typed questions, calls the Jev API, and writes the resulting typed decisions (categorical choices, yes/no probabilities, numeric scores) and their calibrated probabilities back to UAC global variables. This enables UAC workflow gateways to branch on structured, AI-derived decisions rather than relying on brittle hardcoded conditions or slow LLM text generation.

---

# Actions

## 2.1 Decide — Call TypeSafe Jev Decision API

**Functional Requirements:**

1. The extension must accept an unstructured context string describing the system state, event, or situation to be evaluated.
2. The extension must accept a JSON array of typed question definitions that instruct the Jev API on what decisions to make.
3. The extension must support three question types: `choice` (categorical selection from a provided list), `noul` (yes/no boolean with calibrated probability), and `score` (numeric value within a specified min/max range).
4. The extension must authenticate to the TypeSafe Jev API using a Bearer token.
5. The extension must construct and submit a single API call to the Jev `/v1/decide` endpoint containing the context and all questions.
6. The extension must receive the typed answers from the API response, each containing a `value` and a `probability`.
7. The extension must write each answer to a UAC global variable named `{PREFIX}_{ID}`, where `PREFIX` is the user-configured output variable prefix and `ID` is the question's `id` uppercased.
8. The extension must write each answer's probability to a UAC global variable named `{PREFIX}_{ID}_PROB`.
9. The extension must write a `{PREFIX}_LOW_CONFIDENCE` variable set to `true` if any answer's probability falls below the configured confidence threshold, or `false` otherwise. If no threshold is configured (value `0.0`), this variable must always be set to `false`.
10. The extension must print all answers and probabilities to stdout in `KEY=VALUE` format, one per line, to support downstream output capture.
11. The extension must print the complete raw JSON response from the Jev API to stdout as an audit trail block, delimited by header and footer lines.
12. The extension must exit with return code `0` on successful API call and variable writeback.
13. The extension must exit with return code `1` on any validation failure or Jev API error, printing a descriptive error message.

---

# Input Requirements

## 3.1 Authentication Fields

- **`jev_api_key`** (Credential, required): UAC Credential whose **password field** holds the TypeSafe Bearer token. The username field is not used.
  - Example: UAC Credential named `TypeSafe-Jev-API-Key` with username `jev` and password `sk-ts-...`
  - Applicability: All executions
  - Default Value: None

## 3.2 Decision Context Fields

- **`context`** (Large Text, required): Unstructured text that describes the situation the model must evaluate. UAC variable substitution is supported — the field value may contain `${variable_name}` references that UAC resolves before execution.
  - Example: `"Task 'ETL-Load-Redshift' failed after 3 retries. Exit code 1. Output: JDBC connection timeout. Agent: UA-STONEBRANCH-K8S. Business Service: Finance."`
  - Applicability: All executions
  - Default Value: None

- **`questions_json`** (Large Text, required): A JSON array of typed question objects. Each question must have at minimum an `id` (string) and a `type` (one of `choice`, `noul`, `score`). Additional required properties depend on the type:
  - `choice` questions must include a `choices` array of non-empty strings.
  - `score` questions must include a numeric `min` and `max`.
  - `noul` questions require no additional properties.
  - UAC variable substitution is supported in this field.
  - Example:
    ```json
    [
      {"id": "action", "type": "choice", "choices": ["retry", "escalate", "skip"]},
      {"id": "is_transient", "type": "noul"},
      {"id": "severity", "type": "score", "min": 1, "max": 5}
    ]
    ```
  - Applicability: All executions
  - Default Value: None

## 3.3 API Configuration Fields

- **`api_base_url`** (Text, optional): Base URL of the TypeSafe Jev API. Must not include a trailing slash.
  - Example: `https://api.typesafe.ai`
  - Applicability: All executions
  - Default Value: `https://api.typesafe.ai`

- **`timeout_seconds`** (Text, optional): HTTP request timeout in seconds. Must be a positive integer.
  - Example: `30`
  - Applicability: All executions
  - Default Value: `30`

## 3.4 Output Control Fields

- **`variable_prefix`** (Text, optional): Prefix applied to all UAC global variable names written by this extension. Must be non-empty when provided. The value is uppercased internally. Using distinct prefixes allows multiple Jev tasks within the same workflow to write without collision.
  - Example: `JEV` produces `JEV_ACTION`, `JEV_ACTION_PROB`, `JEV_LOW_CONFIDENCE`
  - Example (second call in same workflow): `TRIAGE` produces `TRIAGE_ACTION`, `TRIAGE_SEVERITY`
  - Applicability: All executions
  - Default Value: `JEV`

- **`confidence_threshold`** (Text, optional): A float value between `0.0` and `1.0` (inclusive). If any answer from the Jev API has a probability strictly below this value, the extension sets `{PREFIX}_LOW_CONFIDENCE=true`. Setting this to `0.0` disables the check.
  - Example: `0.75` — any answer with probability below 75% triggers the low-confidence flag
  - Applicability: All executions
  - Default Value: `0.0` (disabled)

---

# Output Requirements

## 4.1 On Success

**Return code:** `0`

**Status description:** `Successful Execution`

**STDOUT output:** The following is emitted in order:

1. An INFO log line: `TypeSafe Jev v<version> | prefix=<PREFIX> | questions=<N>`
2. An INFO log line: `Calling TypeSafe Jev API at <api_base_url>/v1/decide ...`
3. An INFO log line: `Response received — <N> answers`
4. A delimited JSON audit block:
   ```
   === TypeSafe Jev Response ===
   {
     "answers": [ ... ]
   }
   =============================
   ```
5. For each answer, two `KEY=VALUE` lines:
   ```
   {PREFIX}_{ID}={value}
   {PREFIX}_{ID}_PROB={probability_4dp}
   ```
   Where `probability_4dp` is the probability rounded to 4 decimal places (e.g. `0.9100`).
6. A low-confidence flag line:
   ```
   {PREFIX}_LOW_CONFIDENCE=true|false
   ```
7. An INFO log line: `Done.`

**UAC global variables written (per answer):**

| Variable Name | Type | Description |
|---|---|---|
| `{PREFIX}_{ID}` | String | The decided value. Choice: string from the choices list. Noul: `true` or `false`. Score: decimal string. |
| `{PREFIX}_{ID}_PROB` | String | Probability as a 4-decimal-place string, e.g. `"0.9100"` |
| `{PREFIX}_LOW_CONFIDENCE` | String | `"true"` or `"false"` |

**Success Criteria:**

1. Jev API returns HTTP 200 or 201 with a valid JSON body containing an `answers` array.
2. All UAC global variables are written (or a warning is logged if UAC REST is unavailable — this does not fail the task).
3. All `KEY=VALUE` lines appear in task stdout.
4. Extension exits with code `0`.

## 4.2 On Error

**Failure Scenarios:**

| Scenario | Root Causes | Return Code | Status Description Pattern |
|---|---|---|---|
| Required field empty | `jev_api_key`, `context`, or `questions_json` field is blank or not substituted by UAC | 1 | `ERROR: Field '<name>' is required but empty` |
| Field substitution failure | UAC variable not defined — field contains literal `${ops_var_...}` string | 1 | `ERROR: Field '<name>' was not substituted` |
| Invalid confidence threshold | `confidence_threshold` is not a float, or is outside `[0.0, 1.0]` | 1 | `ERROR: confidence_threshold must be a float between 0.0 and 1.0` |
| Invalid timeout | `timeout_seconds` is not a positive integer | 1 | `ERROR: timeout_seconds must be a positive integer` |
| Questions JSON parse failure | `questions_json` is not valid JSON | 1 | `ERROR: questions_json is not valid JSON: <parse error>` |
| Questions not a list | `questions_json` parses to a non-list JSON value | 1 | `ERROR: questions_json must be a JSON array` |
| Question missing `id` or `type` | A question object lacks the required keys | 1 | `ERROR: Question at index <N> is missing required key '<key>'` |
| Unknown question type | A question's `type` is not one of `choice`, `noul`, `score` | 1 | `ERROR: Unknown question type '<type>' at index <N>` |
| Choice question missing choices | A `choice` question has an empty or absent `choices` array | 1 | `ERROR: Question '<id>' of type 'choice' must have a non-empty choices list` |
| Score question missing min/max | A `score` question lacks `min` or `max` | 1 | `ERROR: Question '<id>' of type 'score' must include 'min' and 'max'` |
| Network timeout | HTTP request to Jev API exceeds `timeout_seconds` | 1 | `ERROR: Jev API request timed out after <N>s` |
| Jev API authentication failure | HTTP 401 — invalid or expired Bearer token | 1 | `ERROR: Jev API returned 401 — check API key credential` |
| Jev API rate limit | HTTP 429 | 1 | `ERROR: Jev API returned 429 — rate limit exceeded` |
| Jev API server error | HTTP 5xx | 1 | `ERROR: Jev API returned <status>: <body[:500]>` |
| Jev response missing `answers` | API response is 200 but JSON lacks `answers` key | 1 | `ERROR: Jev API response missing 'answers' key` |
| `requests` library not available | Library not installed on agent | 1 | `ERROR: requests library not available — install via pip` |

**UAC variable write failure (non-fatal):**
- If `UIP_URL` is not set or the variable write REST call fails for any reason, the extension logs a WARNING and continues. The extension does not fail due to variable writeback errors.
- Warning format: `WARNING: Could not write UAC variable '<name>': <reason>`

**Input Validation Rules:**
- `jev_api_key` password must be non-empty after stripping whitespace.
- `context` must be non-empty after stripping whitespace.
- `questions_json` must be non-empty after stripping whitespace.
- `confidence_threshold` must parse as float and satisfy `0.0 <= value <= 1.0`.
- `timeout_seconds` must parse as int and satisfy `value > 0`.
- All question objects must pass type-specific schema validation before the API call is made. The API is never called if any question is invalid.

---

# Authentication Requirements

The extension authenticates to the TypeSafe Jev API using **HTTP Bearer token** authentication. The token must be stored in the **password field** of a UAC Credential of type Username/Password. The username field of the credential is not used.

Header sent: `Authorization: Bearer <token>`

The UAC Credential is referenced in the `jev_api_key` field. UAC resolves the credential at execution time using the `${_credentialPwd(...)}` substitution function.

---

# Environment Variables

The following environment variables are injected automatically by the UAC agent when `sendEnvironment: Launch` is configured in the template. They are used for UAC global variable writeback and are not exposed as user-facing fields.

| Variable | Description |
|---|---|
| `UIP_URL` | Base URL of the UAC Controller REST API (e.g. `https://ps1.stonebranchdev.cloud`). If absent, variable writeback is skipped with a warning. |
| `UIP_USERID` | UAC username for REST API authentication during variable writeback. |
| `UIP_PASSWORD` | UAC password for REST API authentication during variable writeback. |

No user-facing environment variable configuration is required. All user configuration is provided through input fields.

---

# Operational Behavior

**Dynamic Choice Fields:**
Not applicable. This extension has no fields whose options change based on other field values. All 7 fields are always visible.

**Cancel Action:**
If the UAC task is cancelled while the HTTP request to the Jev API is in flight, the `requests` library will receive a signal and the network call will terminate. No partial results will be written. No cleanup of UAC global variables is required — they either exist (from a prior successful run) or do not exist (first run).

**Re-run Capability:**
The extension is fully re-runnable. On re-run, UAC global variables from the prior run are overwritten with the new values via the upsert mechanism. Each re-run is independent.

**Progress Reporting:**
The extension logs progress via standard Python `logging` at INFO level. Log lines are visible in the UAC task output stream. No structured progress bar or percentage reporting is implemented.

**Dynamic Commands:**
Not applicable.

---

# Implementation Notes

## 8.1 Python Compatibility

Python 3.11 target. The script must run with the Python interpreter available on the UAC agent without any installation step — only the `requests` library is required as a dependency, and it is expected to be available on the agent or installable via standard pip.

## 8.2 Target Platform

**Linux only.** The extension targets Linux UAC agents (e.g. the Kubernetes-based UA pods on ps1). Windows is not a priority for this extension.

The `scriptWindows` field in `template.json` must be populated with the same script content for template completeness, but Linux execution is the tested path.

C extension modules with a confirmed `manylinux_2_17_x86_64` wheel are viable for the `requests` library (it is pure-Python, so this is not a concern).

## 8.3 Third-Party Services and Tools

**TypeSafe Jev API**
- Description: System One AI model that returns typed decisions with calibrated probabilities for structured questions. Does not generate text.
- Endpoint: `POST /v1/decide` at the configured base URL (default: `https://api.typesafe.ai`)
- Version constraints: No specific version pinning required — the API is versioned via the `/v1/` path prefix.
- Integration approach: Single synchronous HTTP POST per execution. No polling or streaming. Response is expected within the configured timeout.

**requests (Python library)**
- Description: HTTP client library for Python.
- Version constraints: Any version supporting `requests.post()` with `json=`, `headers=`, and `timeout=` parameters (>= 2.20.0).
- Integration approach: Used for both the Jev API call and the UAC variable writeback REST calls.

## 8.4 Error Handling

**Error categories:**

1. **Input validation errors** — Detected before any network call. Field value is missing, non-substituted, or fails type/format validation. Always fatal (exit 1).
2. **Question schema errors** — Detected during JSON parsing and validation of `questions_json`. Always fatal (exit 1).
3. **Network errors** — Timeout or connection failure to the Jev API. Always fatal (exit 1).
4. **Jev API errors** — Non-2xx HTTP response from the Jev API (auth, rate limit, server error). Always fatal (exit 1), log includes status code and truncated response body.
5. **Response structure errors** — Jev response does not contain expected `answers` key. Always fatal (exit 1).
6. **UAC variable writeback errors** — REST call to UAC Controller fails. Non-fatal — log warning and continue. Extension still exits 0 if the Jev call succeeded.

**Error handling strategy:**
- Validate all inputs before any network calls.
- On fatal error: log to stderr at ERROR level with a descriptive message, exit with code 1.
- On non-fatal error (variable writeback): log to stderr at WARNING level, continue execution.

**Recovery mechanisms:**
- No automatic retry on Jev API failures. The UAC workflow is responsible for retry logic (e.g. configuring the task's retry count in UAC).
- On UAC variable write failure, stdout still contains all `KEY=VALUE` lines that can be captured by UAC output scanning as a fallback.

## 8.5 Resource Cleanup

- No temporary files are created.
- No database connections are opened.
- HTTP connections made via `requests` are closed automatically at end of each call.
- No explicit cleanup is required on cancel or error.

---

# Requirements Summary

The TypeSafe-Jev Universal Extension is a single-action extension that:
- Accepts unstructured context and a JSON question schema from UAC task fields.
- Authenticates to the TypeSafe Jev API using a Bearer token stored in a UAC Credential.
- Submits a single API call and receives typed decisions with probabilities.
- Writes decisions and probabilities to UAC global variables using a configurable prefix, enabling zero-parse downstream variable references in workflow gateways.
- Optionally flags low-confidence answers via a threshold parameter.
- Fails fast (exit 1) on any input validation or API error.
- Treats UAC variable writeback as non-fatal — always prints results to stdout as a fallback capture path.
- Is stateless, idempotent, and fully re-runnable.

---

# Document Change History

- **2026-10-08 08:30 UTC:** Initial requirements document — High Detail. Based on analysis of ps1 UAC workflows (Root Cause Analysis With AI, Stonebranch Demo - AI Decision Making, Batchman Insurance Claims Processing, SAP Commission Process - DSAG), existing extension patterns (Nagios, LangSmith, Workday), and TypeSafe Jev API documentation.
