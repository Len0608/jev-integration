> **Version:** 1.0.0 | **Date:** 2026-10-08

# Jev Integration — User Guide

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Task Actions](#task-actions)
4. [Task Configuration](#task-configuration)
5. [Example Walkthroughs](#example-walkthroughs)
6. [Troubleshooting](#troubleshooting)
7. [Field Reference](#field-reference)

---

## Overview

The **Jev Integration** extension connects Stonebranch UAC to the **TypeSafe Jev AI decision API**. It enables automation workflows to evaluate unstructured context against a set of typed questions and receive calibrated AI decisions — written directly as UAC global variables that downstream tasks can route on.

Typical use cases include:

- Routing incident response workflows based on AI-inferred severity or category.
- Gating approvals or escalations based on whether conditions warrant a hold.
- Enriching audit trails with scored assessments of run-time state.

---

## Prerequisites

- UAC Controller version **7.6.0.0** or later.
- A UAC Agent with outbound HTTPS access to `https://api.typesafe.ai` (or your custom Jev API endpoint) on port 443.
- A valid **TypeSafe Jev API token**.
- A **UAC Credential** with the API token stored in the credential's **password** field (the username field is ignored by the extension).
- Familiarity with the TypeSafe Jev question schema (`choice`, `noul`, and `score` question types).

---

## Task Actions

### Decide

The **Decide** action is the sole operation available in this extension.

**Execution flow:**

1. Validates all input fields and the `Questions JSON` schema.
2. Submits the `Context` text and the list of typed questions to the Jev `/v1/decide` endpoint.
3. Receives a response containing one answer object per question, each with a value and a probability score.
4. Writes the answers and their probabilities as UAC global variables.
5. Sets a `<PREFIX>_LOW_CONFIDENCE` global variable indicating whether any answer fell below the configured confidence threshold.
6. Updates the task's output fields in the UAC UI in real-time.

**When to use:** Any time you need AI-powered decision-making embedded in an automation workflow. The action always runs to completion or exits with a clear error code.

**Status and completion:**

| Exit Code | Meaning |
|---|---|
| `0` | Successful execution — all answers written to UAC global variables. |
| `1` | Transient runtime failure (network, API error, or unexpected error). Retry may succeed. |
| `20` | Validation failure. The task configuration must be corrected before retrying. |

**Post-execution:** Downstream UAC tasks can reference the written variables using `${<PREFIX>_<QUESTION_ID>}` and `${<PREFIX>_<QUESTION_ID>_PROB}` syntax.

---

## Task Configuration

### Authentication

| Field | Description | Required | Default |
|---|---|---|---|
| Jev API Key | UAC Credential whose **password** holds the TypeSafe Bearer token. | Yes | — |

### Request Content

| Field | Description | Required | Default |
|---|---|---|---|
| Context | Unstructured text describing the situation the Jev model must evaluate. UAC variable substitution is supported. | Yes | — |
| Questions JSON | JSON array of typed question definitions. UAC variable substitution is supported. | Yes | — |

### Connection Settings

| Field | Description | Required | Default |
|---|---|---|---|
| API Base URL | Base URL of the Jev API. The extension appends `/v1/decide` automatically. Must not end with a trailing `/`. | No | `https://api.typesafe.ai` |
| Timeout (Seconds) | Maximum seconds to wait for an API response. Must be ≥ 1. | No | `30` |

### Output Settings

| Field | Description | Required | Default |
|---|---|---|---|
| Variable Prefix | Prefix applied to all UAC global variable names written by this extension. Uppercased internally. | No | `JEV` |
| Confidence Threshold | Confidence gate (0.0–1.0). If any answer probability falls below this value, `<PREFIX>_LOW_CONFIDENCE` is set to `true`. Set to `0.0` to disable. | No | `0.0` |

### Questions JSON Schema

The `Questions JSON` field must contain a valid JSON array. Each element is an object with at minimum an `id` and a `type` property.

**Common fields (all question types):**

| Property | Type | Required | Description |
|---|---|---|---|
| `id` | string | Yes | Unique identifier for the question; used as the UAC variable name suffix. |
| `type` | string | Yes | One of `choice`, `noul`, or `score`. |

**Type-specific fields:**

| Type | Additional required properties | Description |
|---|---|---|
| `choice` | `choices` — non-empty array of strings | Model picks one value from the provided list. |
| `noul` | none | Free-form natural-language answer. |
| `score` | `min` and `max` — numbers | Numeric score within the specified range. |

**Example:**

```json
[
  {
    "id": "severity",
    "type": "choice",
    "choices": ["low", "medium", "high", "critical"]
  },
  {
    "id": "summary",
    "type": "noul"
  },
  {
    "id": "urgency_score",
    "type": "score",
    "min": 0,
    "max": 10
  }
]
```

### UAC Global Variables Written

After a successful run the extension writes the following variables (where `PREFIX` is the configured **Variable Prefix**, uppercased):

| Variable | Content |
|---|---|
| `<PREFIX>_<QUESTION_ID>` | The answer value returned by the Jev API. |
| `<PREFIX>_<QUESTION_ID>_PROB` | The probability/confidence score (4 decimal places). |
| `<PREFIX>_LOW_CONFIDENCE` | `true` if any probability fell below the threshold; `false` otherwise. |

---

## Example Walkthroughs

### Scenario 1 — Incident Severity Classification

Classify an incoming IT incident by severity and route the workflow accordingly.

**Prerequisites:**
- A UAC Credential named `jev-api-key` with the TypeSafe Bearer token in the password field.
- The Jev API is reachable from the UAC agent host.
- A downstream task or trigger that branches on the `JEV_SEVERITY` global variable.

**Configuration:**

| Field | Value | Notes |
|---|---|---|
| Action | `Decide` | |
| Jev API Key | `jev-api-key` | Select the UAC credential holding the Bearer token |
| Context | `Disk usage on host prod-db-01 reached 95%. Last backup completed 6 hours ago. On-call engineer is not available.` | Describes the incident state |
| Questions JSON | `[{"id":"severity","type":"choice","choices":["low","medium","high","critical"]},{"id":"requires_immediate_action","type":"choice","choices":["yes","no"]}]` | |
| API Base URL | *(leave blank)* | Uses default `https://api.typesafe.ai` |
| Timeout (Seconds) | `30` | |
| Variable Prefix | `JEV` | |
| Confidence Threshold | `0.8` | Flags low-confidence answers for human review |

**What happens:**
- The extension POSTs the incident description and questions to the Jev API.
- Variables written: `JEV_SEVERITY`, `JEV_SEVERITY_PROB`, `JEV_REQUIRES_IMMEDIATE_ACTION`, `JEV_REQUIRES_IMMEDIATE_ACTION_PROB`, and `JEV_LOW_CONFIDENCE`.
- If any answer probability is below `0.8`, `JEV_LOW_CONFIDENCE` is set to `true`.
- Downstream tasks can branch on `${JEV_SEVERITY}` to route to the appropriate incident queue.
- The **Answers Written** output field shows `2 answers → JEV_*` in the UAC UI.

---

### Scenario 2 — Change Request Risk Assessment

Score the risk of a proposed change request and generate a plain-language summary for stakeholders.

**Prerequisites:**
- A UAC Credential named `typesafe-jev-token` with the TypeSafe Bearer token in the password field.
- Change request metadata is available as UAC variables (e.g., `${OPS_CR_DESCRIPTION}`).
- The Jev API is reachable from the executing agent.

**Configuration:**

| Field | Value | Notes |
|---|---|---|
| Action | `Decide` | |
| Jev API Key | `typesafe-jev-token` | |
| Context | `Change request CR-4821: Upgrade PostgreSQL from 14.9 to 16.2 on prod-db cluster. Planned maintenance window: Saturday 02:00–04:00. Rollback plan documented. ${OPS_CR_DESCRIPTION}` | UAC substitutes `${OPS_CR_DESCRIPTION}` at runtime |
| Questions JSON | `[{"id":"risk_score","type":"score","min":0,"max":10},{"id":"risk_category","type":"choice","choices":["low","moderate","high","very_high"]},{"id":"risk_summary","type":"noul"}]` | |
| API Base URL | *(leave blank)* | |
| Timeout (Seconds) | `60` | Increase for longer context |
| Variable Prefix | `CR` | All variables use the `CR_` prefix |
| Confidence Threshold | `0.0` | No confidence gating required |

**What happens:**
- UAC substitutes `${OPS_CR_DESCRIPTION}` in the context before sending the request.
- The Jev API returns a numeric risk score, a risk category, and a free-text summary.
- Variables written: `CR_RISK_SCORE`, `CR_RISK_SCORE_PROB`, `CR_RISK_CATEGORY`, `CR_RISK_CATEGORY_PROB`, `CR_RISK_SUMMARY`, `CR_RISK_SUMMARY_PROB`, and `CR_LOW_CONFIDENCE`.
- Change approval workflows can gate on `${CR_RISK_CATEGORY}` being `low` or `moderate` before auto-approving.
- The natural-language summary in `${CR_RISK_SUMMARY}` can be posted to a Slack channel or attached to a JIRA ticket by a downstream task.

---

## Troubleshooting

### Authentication Failures

**Symptom:** Task fails with exit code 1 and message `API Error: Jev API returned 401`.  
**Possible cause:** The Bearer token stored in the UAC credential is invalid, expired, or missing.  
**Resolution:** Open the UAC credential and verify that the **password** field contains a valid, non-expired TypeSafe Jev API token. Regenerate the token in the TypeSafe portal if needed.

---

**Symptom:** Task fails with message `Field 'jev_api_key' is required but empty`.  
**Possible cause:** The **Jev API Key** field is blank or the referenced credential has an empty password.  
**Resolution:** Ensure the **Jev API Key** field references a valid UAC credential and that the credential's password is non-empty.

---

### Rate Limit Errors

**Symptom:** Task fails with exit code 1 and message `API Error: Jev API returned 429 — rate limit exceeded`.  
**Possible cause:** The API token has exceeded its request quota.  
**Resolution:** Reduce the request frequency or contact TypeSafe support to increase your rate limit. Consider adding a delay between workflow runs.

---

### Connection and Timeout Issues

**Symptom:** Task fails with message `Network Error: Jev API request timed out after Ns`.  
**Possible cause:** The Jev API did not respond within the configured timeout.  
**Resolution:** Increase the **Timeout (Seconds)** field. Verify that the UAC agent has outbound HTTPS access to the Jev API endpoint.

---

**Symptom:** Task fails with `Network Error: Jev API connection failed`.  
**Possible cause:** The agent host cannot reach the API endpoint (DNS failure, firewall block, or proxy misconfiguration).  
**Resolution:** Verify network connectivity from the agent host to `https://api.typesafe.ai`. Check firewall rules and proxy settings. If using a custom endpoint, confirm the **API Base URL** is correct and does not end with a trailing slash.

---

### Validation Failures (Exit Code 20)

**Symptom:** Task fails with exit code 20 and message `Validation Error: ERROR: questions_json is not valid JSON`.  
**Possible cause:** The **Questions JSON** field contains a syntax error.  
**Resolution:** Validate the JSON using a JSON linter before pasting into the field. Ensure the value is a JSON array (`[...]`).

---

**Symptom:** Task fails with exit code 20 and message `Validation Error: ERROR: Unknown question type 'X' at index N`.  
**Possible cause:** A question object uses a `type` value not in the accepted set.  
**Resolution:** Correct the `type` field. Only `choice`, `noul`, and `score` are accepted.

---

**Symptom:** Task fails with exit code 20 and message `ERROR: Field 'context' was not substituted`.  
**Possible cause:** The **Context** field contains an unresolved UAC variable reference (literal `${...}`).  
**Resolution:** Check that all UAC variables referenced in the context field are defined and in scope at runtime. Verify variable names for typos.

---

**Symptom:** Task fails with exit code 20 and message `Field 'api_base_url' must not end with a trailing slash`.  
**Possible cause:** The **API Base URL** field has a trailing `/`.  
**Resolution:** Remove the trailing slash (e.g., use `https://api.typesafe.ai` instead of `https://api.typesafe.ai/`).

---

### Configuration Mismatches

**Symptom:** Task fails with `Response Error: Jev API response missing 'answers' key`.  
**Possible cause:** The API returned a response that does not match the expected schema.  
**Resolution:** Verify the **API Base URL** points to the correct API endpoint version. Check whether the Jev API has updated its response format.

---

**Symptom:** Variables are not written to UAC after a successful run.  
**Possible cause:** The `UIP_URL` environment variable is not set on the agent, so the UAC variable writer is disabled.  
**Resolution:** Ensure the UAC agent is configured with the `UIP_URL`, `UIP_USERID`, and `UIP_PASSWORD` environment variables so the extension can reach the UAC Controller REST API.

---

**Symptom:** `LOW_CONFIDENCE` is always `false` even when answers appear uncertain.  
**Possible cause:** The **Confidence Threshold** field is `0.0` (the default), which disables confidence checking.  
**Resolution:** Set **Confidence Threshold** to a value between `0.0` and `1.0` (e.g., `0.7`) to activate confidence gating.

---

## Field Reference

| Field Name | Label | Type | Required | Description | Allowed Values / Default |
|---|---|---|---|---|---|
| `action` | Action | Choice | No | Operation to perform. Currently only `Decide` is supported. | `Decide` (default) |
| `jev_api_key` | Jev API Key | Credential | Yes | UAC Credential whose password holds the TypeSafe Bearer API token. | Any valid UAC Credential |
| `context` | Context | Text | Yes | Unstructured text describing the situation for the Jev model. UAC variable substitution supported. Must not contain unresolved `${...}` patterns. | Any non-empty string |
| `questions_json` | Questions JSON | Text | Yes | JSON array of typed question definitions (`choice`, `noul`, `score`). UAC variable substitution supported. | Valid JSON array |
| `api_base_url` | API Base URL | Text | No | Base URL of the Jev API. Extension appends `/v1/decide`. Must not end with `/`. | Default: `https://api.typesafe.ai` |
| `timeout_seconds` | Timeout (Seconds) | Integer | No | Maximum seconds to wait for an API response. Minimum: 1. | Default: `30` |
| `variable_prefix` | Variable Prefix | Text | No | Prefix for all UAC global variable names written by this extension. Uppercased internally. | Default: `JEV` |
| `confidence_threshold` | Confidence Threshold | Float | No | Confidence gate (0.0–1.0). Probabilities below this value set `<PREFIX>_LOW_CONFIDENCE=true`. Set to `0.0` to disable. | `0.0`–`1.0`; Default: `0.0` |
| `answers_written` | Answers Written | Text (Output Only) | — | Count and prefix of written answers. Populated on successful execution. | Read-only |
| `low_confidence` | Low Confidence | Text (Output Only) | — | Mirrors the `<PREFIX>_LOW_CONFIDENCE` global variable value. | `true` / `false` (read-only) |
