"""Decide action — submits context and questions to the TypeSafe Jev API."""

import json
import logging
from typing import Any, Dict, List

from actions.output import ActionOutput
from exceptions import ValidationError
from fields.input import InputFields
from fields.output import OutputFields
from manager import ExtensionManager
from utility import JevAPIClient, QuestionValidator, UACVariableWriter

logger = logging.getLogger("UNV")
extension_manager = ExtensionManager()

_DEFAULT_API_BASE_URL = "https://api.typesafe.ai"
_DEFAULT_TIMEOUT_SECONDS = 30
_DEFAULT_VARIABLE_PREFIX = "JEV"
_DEFAULT_CONFIDENCE_THRESHOLD = 0.0


def decide(input_data: InputFields) -> ActionOutput:
    """Submit context and questions to the TypeSafe Jev API and write decisions.

    Execution flow:
        1. Resolve effective configuration values (prefix, timeout, base URL,
           confidence threshold).
        2. Validate required fields (jev_api_key, context, questions_json).
        3. Validate the questions_json schema via QuestionValidator.
        4. Emit startup line to STDOUT.
        5. Call the Jev /v1/decide endpoint via JevAPIClient.
        6. Emit raw API response audit block to STDOUT.
        7. Process answers: write UAC global variables, emit KEY=VALUE lines.
        8. Update OutputFields for real-time UAC UI.
        9. Return ActionOutput.

    Args:
        input_data: Validated input fields from the UAC task form.

    Returns:
        ActionOutput carrying the prefix, answers, low_confidence flag, and
        answer count for Extension Output serialisation.

    Raises:
        ValidationError: On missing or structurally invalid input field values.
        NetworkError:    On HTTP timeout or connection failure to the Jev API.
        APIError:        On non-2xx HTTP responses from the Jev API.
        ResponseError:   On a Jev API response that is missing the 'answers' key.
    """
    logger.info("Starting decide action")

    # ------------------------------------------------------------------
    # Step 1 — Resolve effective configuration values
    # ------------------------------------------------------------------
    raw_prefix = (
        input_data.variable_prefix.value.strip()
        if input_data.variable_prefix and input_data.variable_prefix.value
        else ""
    )
    prefix: str = raw_prefix.upper() if raw_prefix else _DEFAULT_VARIABLE_PREFIX

    api_base_url: str = (
        input_data.api_base_url.value.strip()
        if input_data.api_base_url and input_data.api_base_url.value
        else _DEFAULT_API_BASE_URL
    )

    timeout_seconds: int = (
        int(input_data.timeout_seconds.value)
        if input_data.timeout_seconds and input_data.timeout_seconds.value is not None
        else _DEFAULT_TIMEOUT_SECONDS
    )

    confidence_threshold: float = (
        float(input_data.confidence_threshold.value)
        if input_data.confidence_threshold and input_data.confidence_threshold.value is not None
        else _DEFAULT_CONFIDENCE_THRESHOLD
    )

    logger.debug(
        "Effective config: prefix=%s, api_base_url=%s, timeout=%ds, "
        "confidence_threshold=%s",
        prefix,
        api_base_url,
        timeout_seconds,
        confidence_threshold,
    )

    # ------------------------------------------------------------------
    # Step 2 — Validate required fields
    # ------------------------------------------------------------------
    api_token: str = ""
    if input_data.jev_api_key and input_data.jev_api_key.password:
        api_token = input_data.jev_api_key.password.strip()
    if not api_token:
        logger.error("Field 'jev_api_key' is required but empty")
        raise ValidationError("ERROR: Field 'jev_api_key' is required but empty")

    context_value: str = (
        input_data.context.value
        if input_data.context and input_data.context.value is not None
        else ""
    )
    if not context_value.strip():
        logger.error("Field 'context' is required but empty")
        raise ValidationError("ERROR: Field 'context' is required but empty")
    if "${" in context_value:
        logger.error("Field 'context' contains unresolved UAC variable pattern")
        raise ValidationError("ERROR: Field 'context' was not substituted")

    questions_json_str: str = (
        input_data.questions_json.value
        if input_data.questions_json and input_data.questions_json.value is not None
        else ""
    )
    if not questions_json_str.strip():
        logger.error("Field 'questions_json' is required but empty")
        raise ValidationError("ERROR: Field 'questions_json' is required but empty")
    if "${" in questions_json_str:
        logger.error("Field 'questions_json' contains unresolved UAC variable pattern")
        raise ValidationError("ERROR: Field 'questions_json' was not substituted")

    logger.debug("Required field validation passed")

    # ------------------------------------------------------------------
    # Step 3 — Validate questions schema
    # ------------------------------------------------------------------
    logger.info("Validating questions_json schema")
    validator = QuestionValidator()
    questions: List[Dict[str, Any]] = validator.validate(questions_json_str)
    n_questions: int = len(questions)
    logger.info("questions_json validation passed: %d question(s)", n_questions)

    # ------------------------------------------------------------------
    # Step 4 — Startup line (emitted after N is known)
    # ------------------------------------------------------------------
    # Read extension version from extension.yml via the manager (best-effort)
    version: str = "1.0.0"
    try:
        import yaml  # type: ignore[import]
        import pathlib

        yml_path = pathlib.Path(__file__).parent.parent / "extension.yml"
        with open(yml_path, "r") as fh:
            yml_data = yaml.safe_load(fh)
        version = yml_data.get("extension", {}).get("version", "1.0.0")
    except Exception:
        pass  # Non-fatal; fall back to default version string

    print(
        f"TypeSafe Jev v{version} | prefix={prefix} | questions={n_questions}"
    )

    # ------------------------------------------------------------------
    # Step 5 — API call
    # ------------------------------------------------------------------
    logger.info(
        "Calling TypeSafe Jev API: %s/v1/decide (timeout=%ds)",
        api_base_url,
        timeout_seconds,
    )
    print(f"Calling TypeSafe Jev API at {api_base_url}/v1/decide ...")

    client = JevAPIClient(
        base_url=api_base_url,
        token=api_token,
        timeout=timeout_seconds,
    )
    response_data: Dict[str, Any] = client.decide(
        context=context_value,
        questions=questions,
    )

    answers: List[Dict[str, Any]] = response_data["answers"]
    m_answers: int = len(answers)
    logger.info("Response received — %d answer(s)", m_answers)
    print(f"Response received — {m_answers} answers")

    # ------------------------------------------------------------------
    # Step 6 — Audit block
    # ------------------------------------------------------------------
    print("=== TypeSafe Jev Response ===")
    print(json.dumps(response_data, indent=2))
    print("=============================")

    # ------------------------------------------------------------------
    # Step 7 — Answer processing and variable writeback
    # ------------------------------------------------------------------
    low_confidence_flag: bool = False
    uac_variables: List[tuple] = []

    for answer in answers:
        a_id: str = answer.get("id", "")
        a_value: str = str(answer.get("value", ""))
        a_prob: float = float(answer.get("probability", 0.0))
        prob_str: str = f"{a_prob:.4f}"

        id_upper: str = a_id.upper()
        var_name: str = f"{prefix}_{id_upper}"
        prob_var_name: str = f"{prefix}_{id_upper}_PROB"

        uac_variables.append((var_name, a_value))
        uac_variables.append((prob_var_name, prob_str))

        print(f"{var_name}={a_value}")
        print(f"{prob_var_name}={prob_str}")

        if confidence_threshold > 0.0 and a_prob < confidence_threshold:
            low_confidence_flag = True

    low_confidence_str: str = "true" if low_confidence_flag else "false"
    low_confidence_var: str = f"{prefix}_LOW_CONFIDENCE"
    uac_variables.append((low_confidence_var, low_confidence_str))
    print(f"{low_confidence_var}={low_confidence_str}")

    # Write all variables to UAC
    writer = UACVariableWriter()
    writer.write_batch(uac_variables)

    # ------------------------------------------------------------------
    # Step 8 — Update OutputFields for real-time UAC UI
    # ------------------------------------------------------------------
    output_fields = OutputFields()
    output_fields.update(
        answers_written=f"{m_answers} answers → {prefix}_*",
        low_confidence=low_confidence_str,
    )
    logger.debug(
        "OutputFields updated: answers_written=%d, low_confidence=%s",
        m_answers,
        low_confidence_str,
    )

    # ------------------------------------------------------------------
    # Step 9 — Completion
    # ------------------------------------------------------------------
    print("Done.")
    logger.info("decide action completed successfully")

    return ActionOutput(
        prefix=prefix,
        answers=answers,
        low_confidence=low_confidence_flag,
        answer_count=m_answers,
    )
