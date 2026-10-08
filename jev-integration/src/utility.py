"""
Utility module for the TypeSafe-Jev Universal Extension.

Provides three utility classes:

- JevAPIClient      — HTTP client for the TypeSafe Jev /v1/decide endpoint.
- QuestionValidator — Validates the questions_json field against the Jev schema rules.
- UACVariableWriter — Writes UAC global variables via the UAC Controller REST API.
"""

import json
import logging
import os
from typing import Any

import requests
import requests.exceptions

from exceptions import APIError
from exceptions import NetworkError
from exceptions import ResponseError
from exceptions import ValidationError

logger = logging.getLogger("UNV")


class JevAPIClient:
    """
    Encapsulates all HTTP communication with the TypeSafe Jev /v1/decide endpoint.

    Handles request construction, authentication header injection, timeout
    enforcement, HTTP error classification, and response parsing.

    Attrs:
        base_url:    Base URL of the Jev API (no trailing slash).
        token:       Bearer token for the Authorization header.
        timeout:     Maximum seconds to wait for a response.
        _endpoint:   Full POST endpoint URL ({base_url}/v1/decide).
    """

    def __init__(self, base_url: str, token: str, timeout: int) -> None:
        """
        Initialise the client.

        Args:
            base_url: Base URL of the Jev API (no trailing slash).
            token:    Bearer token string.
            timeout:  HTTP request timeout in seconds.
        """
        self.base_url: str = base_url
        self.token: str = token
        self.timeout: int = timeout
        self._endpoint: str = f"{base_url}/v1/decide"
        logger.debug(
            "JevAPIClient initialised: endpoint=%s, timeout=%d",
            self._endpoint,
            self.timeout,
        )

    def decide(self, context: str, questions: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Submit a decide request to the Jev API.

        Constructs the JSON request body, sets required HTTP headers, executes
        an HTTP POST, classifies any error response, parses the JSON body, and
        verifies the 'answers' key is present before returning.

        Args:
            context:   Unstructured situation text sent to the Jev model.
            questions: Validated list of typed question dicts.

        Returns:
            Parsed JSON response object containing the 'answers' key.

        Raises:
            NetworkError:  On request timeout or connection failure.
            APIError:      On HTTP 401, 429, 5xx, or any other non-2xx status.
            ResponseError: If the response body is unparseable or missing 'answers'.
        """
        headers: dict[str, str] = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload: dict[str, Any] = {
            "context": context,
            "questions": questions,
        }

        logger.info("Making POST request to %s", self._endpoint)
        logger.debug("Request payload question count: %d", len(questions))

        try:
            response = requests.post(
                self._endpoint,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
        except requests.exceptions.Timeout:
            logger.error(
                "Jev API request timed out after %ds", self.timeout
            )
            raise NetworkError(
                f"ERROR: Jev API request timed out after {self.timeout}s"
            )
        except requests.exceptions.ConnectionError as exc:
            logger.error("Jev API connection failed: %s", str(exc))
            raise NetworkError(
                f"ERROR: Jev API connection failed: {str(exc)}"
            )

        logger.debug("Response status code: %d", response.status_code)

        status = response.status_code

        if status == 401:
            logger.error("Jev API returned 401 — check API key credential")
            raise APIError(
                "ERROR: Jev API returned 401 — check API key credential"
            )

        if status == 429:
            logger.error("Jev API returned 429 — rate limit exceeded")
            raise APIError(
                "ERROR: Jev API returned 429 — rate limit exceeded"
            )

        if status >= 500 or (status >= 300 and status not in range(200, 300)):
            truncated_body: str = response.text[:500]
            logger.error(
                "Jev API returned %d: %s", status, truncated_body
            )
            raise APIError(
                f"ERROR: Jev API returned {status}: {truncated_body}"
            )

        # Parse response body
        try:
            data: dict[str, Any] = response.json()
        except ValueError as exc:
            logger.error("Failed to parse Jev API response as JSON: %s", str(exc))
            raise ResponseError(
                f"ERROR: Jev API response is not valid JSON: {str(exc)}"
            )

        logger.debug("Response body parsed successfully")

        if "answers" not in data:
            logger.error("Jev API response missing 'answers' key")
            raise ResponseError(
                "ERROR: Jev API response missing 'answers' key"
            )

        logger.info("API request successful — %d answers received", len(data["answers"]))
        return data


class QuestionValidator:
    """
    Validates a raw questions_json string against the Jev question schema rules.

    Raises ValidationError immediately on the first schema violation found.
    Returns the validated list of question dicts on success.
    """

    VALID_TYPES: frozenset[str] = frozenset({"choice", "noul", "score"})

    def validate(self, questions_json: str) -> list[dict[str, Any]]:
        """
        Parse and validate the questions_json field value.

        Checks performed in order:
        1. JSON parse succeeds.
        2. Parsed value is a list.
        3. Each element has non-empty 'id' and 'type' keys.
        4. 'type' is one of 'choice', 'noul', 'score'.
        5. 'choice' questions have a non-empty 'choices' list.
        6. 'score' questions have both 'min' and 'max' keys.

        Args:
            questions_json: Raw string value of the questions_json field.

        Returns:
            Validated list of question dicts.

        Raises:
            ValidationError: On any schema violation with a precise error message.
        """
        logger.debug("Validating questions_json (%d characters)", len(questions_json))

        # Step 1: JSON parse
        try:
            parsed: Any = json.loads(questions_json)
        except json.JSONDecodeError as exc:
            logger.error("questions_json is not valid JSON: %s", str(exc))
            raise ValidationError(
                f"ERROR: questions_json is not valid JSON: {str(exc)}"
            )

        # Step 2: Must be a list
        if not isinstance(parsed, list):
            logger.error(
                "questions_json must be a JSON array, got %s", type(parsed).__name__
            )
            raise ValidationError(
                "ERROR: questions_json must be a JSON array"
            )

        # Step 3–6: Per-element validation
        for i, question in enumerate(parsed):
            if not isinstance(question, dict):
                raise ValidationError(
                    f"ERROR: Question at index {i} must be a JSON object"
                )

            if "id" not in question:
                raise ValidationError(
                    f"ERROR: Question at index {i} is missing required key 'id'"
                )

            if "type" not in question:
                raise ValidationError(
                    f"ERROR: Question at index {i} is missing required key 'type'"
                )

            q_id: str = question["id"]
            q_type: str = question["type"]

            if q_type not in self.VALID_TYPES:
                raise ValidationError(
                    f"ERROR: Unknown question type '{q_type}' at index {i}"
                )

            if q_type == "choice":
                choices = question.get("choices")
                if not choices or not isinstance(choices, list):
                    raise ValidationError(
                        f"ERROR: Question '{q_id}' of type 'choice' must have"
                        " a non-empty choices list"
                    )

            if q_type == "score":
                if "min" not in question or "max" not in question:
                    raise ValidationError(
                        f"ERROR: Question '{q_id}' of type 'score' must include"
                        " 'min' and 'max'"
                    )

        logger.debug("questions_json validated: %d questions", len(parsed))
        return parsed


class UACVariableWriter:
    """
    Writes UAC global variables via the UAC Controller REST API.

    Reads UIP_URL, UIP_USERID, and UIP_PASSWORD from the operating system
    environment at construction time. If UIP_URL is absent or empty the writer
    is disabled — all write calls log a warning and return without making any
    network calls.

    All write failures are non-fatal: exceptions are caught, logged as
    warnings, and execution continues.
    """

    def __init__(self) -> None:
        """
        Initialise the writer from environment variables.

        Reads UIP_URL, UIP_USERID, and UIP_PASSWORD from os.environ.
        Marks the writer as disabled when UIP_URL is absent or empty.
        """
        self._url: str = os.environ.get("UIP_URL", "").strip()
        self._userid: str = os.environ.get("UIP_USERID", "")
        self._password: str = os.environ.get("UIP_PASSWORD", "")
        self._enabled: bool = bool(self._url)

        if self._enabled:
            logger.debug(
                "UACVariableWriter initialised: UIP_URL=%s", self._url
            )
        else:
            logger.debug(
                "UACVariableWriter initialised in disabled mode: UIP_URL not set"
            )

    def write(self, name: str, value: str) -> None:
        """
        Write a single UAC global variable via HTTP POST (upsert semantics).

        On any failure (disabled writer, network error, HTTP error), logs a
        WARNING and returns without propagating the exception.

        Args:
            name:  UAC global variable name.
            value: Variable value string.
        """
        if not self._enabled:
            logger.warning(
                "Could not write UAC variable '%s': UIP_URL not set", name
            )
            return

        endpoint: str = f"{self._url}/resources/globalvariable"
        body: dict[str, str] = {"name": name, "value": value}

        logger.debug("Writing UAC variable: %s", name)

        try:
            response = requests.post(
                endpoint,
                json=body,
                auth=(self._userid, self._password),
                timeout=10,
            )
            response.raise_for_status()
            logger.debug("UAC variable written: %s", name)
        except Exception as exc:
            logger.warning(
                "Could not write UAC variable '%s': %s", name, str(exc)
            )

    def write_batch(self, variables: list[tuple[str, str]]) -> None:
        """
        Write multiple UAC global variables in sequence.

        Each write is independent — a failure on one variable does not
        prevent writing subsequent variables.

        Args:
            variables: List of (name, value) string tuples.
        """
        logger.info("Writing %d UAC global variable(s)", len(variables))
        for name, value in variables:
            self.write(name, value)
        logger.debug("Batch write complete: %d variable(s) attempted", len(variables))
