"""
Exceptions module for the TypeSafe-Jev Universal Extension.

This module provides:
- Base ExecutionError class
- ValidationError  — input field and schema validation failures (exit code 20)
- NetworkError     — HTTP connection timeouts and unreachable host errors (exit code 1)
- APIError         — HTTP error status responses from the Jev API (exit code 1)
- ResponseError    — structurally invalid API responses (exit code 1)
- DataValidationError — generic input field validation (exit code 20, kept for compatibility)
- UnexpectedSystemError — unexpected system-level errors (exit code 1)

Exit code conventions:
    0  — successful execution
    1  — runtime failure (network, API, or response error); retry may succeed
    20 — validation failure; task definition must be corrected before retry
"""
from typing import Optional


class ExecutionError(Exception):
    """
    The default error raised by an extension.

    All extension errors must inherit from it.

    Attrs:
        exit_code: The exit code of the extension (for UAC)
        message: The error message for status description
    """

    exit_code: int = 1
    message: str = "Execution Failed"

    def __init__(self, message: Optional[str] = None):
        """
        Initialize exception.

        Args:
            message: Optional message that will be appended to the default message.

        Note:
            To return result data with errors, use error_manager.set_result()
            before raising the exception.
        """
        if message:
            self.message = f"{self.message}: {message}"

        super().__init__(self.message)


class ValidationError(ExecutionError):
    """
    Raised when an input field value or the questions_json schema is invalid.

    Use when:
    - A required field is empty or contains only whitespace.
    - A field value contains an unresolved UAC variable substitution pattern (literal '${').
    - The questions_json string is not valid JSON.
    - The parsed questions_json value is not a JSON array.
    - A question object is missing required keys ('id' or 'type').
    - A question 'type' is not one of the accepted values ('choice', 'noul', 'score').
    - A 'choice' question has an absent or empty 'choices' list.
    - A 'score' question is missing 'min' or 'max' keys.

    Exit code 20 signals that the task definition must be corrected before retry.
    """

    exit_code: int = 20
    message: str = "Validation Error"


class NetworkError(ExecutionError):
    """
    Raised when a network-level failure prevents the Jev API from being reached.

    Use when:
    - The HTTP request to the Jev API times out (requests.exceptions.Timeout).
    - The host is unreachable or the connection is refused
      (requests.exceptions.ConnectionError).

    Exit code 1 signals a transient failure; a retry may succeed.
    """

    exit_code: int = 1
    message: str = "Network Error"


class APIError(ExecutionError):
    """
    Raised when the Jev API returns an HTTP error status code.

    Use when:
    - HTTP 401 Unauthorized is received (invalid or expired Bearer token).
    - HTTP 429 Too Many Requests is received (rate limit exceeded).
    - Any HTTP 5xx Server Error is received (transient server-side issue).
    - Any other non-2xx HTTP status is received.

    Include the status code and truncated response body (max 500 characters)
    in the message to aid diagnosis.

    Exit code 1 signals a runtime failure; retry may or may not succeed
    depending on the status (e.g., 401 requires a credential fix, 429/5xx may
    succeed on retry).
    """

    exit_code: int = 1
    message: str = "API Error"


class ResponseError(ExecutionError):
    """
    Raised when the Jev API returns a structurally invalid response body.

    Use when:
    - The HTTP response body cannot be parsed as JSON.
    - The parsed response JSON object does not contain the expected 'answers' key.

    This indicates an unexpected change in the API contract rather than a
    transient network issue. Exit code 1 is used; investigation of the API
    response shape is required.
    """

    exit_code: int = 1
    message: str = "Response Error"


class DataValidationError(ExecutionError):
    """Raised when an input field is invalid."""

    exit_code: int = 20
    message: str = "Data Validation Error"


class UnexpectedSystemError(ExecutionError):
    """Raised for unexpected system errors."""

    exit_code: int = 1
    message: str = "System Error"
