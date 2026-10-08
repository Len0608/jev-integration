"""InputFields dataclass for input parsing and validation."""

from dataclasses import dataclass, fields as dataclass_fields, asdict
from pathlib import Path
from typing import Optional, Any, Dict, List, Union, get_type_hints, get_origin, get_args
from fields.output import OutputFields
from fields.types import (
    Text,
    Integer,
    Float,
    Boolean,
    SingleChoice,
    MultiChoice,
    Credential,
    Script,
    Array,
)
from exceptions import DataValidationError
from manager import ExtensionManager

extension_manager = ExtensionManager()


@dataclass
class InputFields:
    """Input fields from UAC with validation.

    All user-defined fields are Optional — UAC Controller enforces required
    field validation at the template level. Fields can still be None when
    they reach the extension (e.g., hidden fields that UAC sends as empty
    strings are normalised to None by preprocess_fields).
    """

    # Dispatch selector — always visible, required
    action: Optional[SingleChoice] = None

    # Credential — holds the TypeSafe Bearer token in its password attribute
    jev_api_key: Optional[Credential] = None

    # Large text fields — UAC variable substitution supported
    context: Optional[Text] = None
    questions_json: Optional[Text] = None

    # Optional configuration fields
    api_base_url: Optional[Text] = None
    timeout_seconds: Optional[Integer] = None
    variable_prefix: Optional[Text] = None
    confidence_threshold: Optional[Float] = None

    # Output-only fields — populated by the extension, read-only from UAC perspective
    # These are included here so that preprocess_fields can detect them in re-run
    # scenarios where UAC injects previous output values into the incoming fields dict.
    answers_written: Optional[Text] = None
    low_confidence: Optional[Text] = None

    # Previous run output (auto-populated for re-runs)
    previous_output: Optional[OutputFields] = None

    # Skip validation flag (internal use only)
    _skip_validation: bool = False

    @staticmethod
    def preprocess_fields(fields: dict) -> dict:
        """Preprocess raw UAC fields before creating InputFields.

        Converts raw UAC values to wrapper type instances:
        1. Filters out flattened credential fields (containing dots)
        2. Wraps values in appropriate wrapper types based on field type hints
        3. Extracts previous OutputFields if present (from re-runs)
        """

        processed = {}
        previous_output_data = {}

        # Get all OutputFields field names for detection
        output_field_names = {f.name for f in dataclass_fields(OutputFields)}

        # Get type hints to detect wrapper types
        type_hints = get_type_hints(InputFields)

        # Map field names to their wrapper types
        field_wrapper_types = {}
        for field_name, field_type in type_hints.items():
            base_type = field_type
            if get_origin(field_type) is Union:
                args = get_args(field_type)
                non_none_args = [arg for arg in args if arg is not type(None)]
                if non_none_args:
                    base_type = non_none_args[0]
            field_wrapper_types[field_name] = base_type

        for key, value in fields.items():
            # Skip flattened credential fields (e.g., "jev_api_key.token")
            if "." in key:
                continue

            # Check if this field belongs to OutputFields (previous run data)
            if key in output_field_names:
                previous_output_data[key] = value
                continue

            # Preserve None values
            if value is None:
                processed[key] = value
                continue

            # Get the wrapper type for this field
            wrapper_type = field_wrapper_types.get(key)

            # Convert to appropriate wrapper type
            if wrapper_type == SingleChoice:
                if isinstance(value, list):
                    value = SingleChoice(_values=value)
                else:
                    value = SingleChoice(_values=[value])

            elif wrapper_type == MultiChoice:
                if isinstance(value, list):
                    value = MultiChoice(values=value)
                else:
                    value = MultiChoice(values=[value])

            elif wrapper_type == Script:
                if isinstance(value, str):
                    value = Script(path=Path(value))

            elif wrapper_type == Credential:
                if isinstance(value, dict):
                    value = Credential.from_dict(value)

            elif wrapper_type == Text:
                if isinstance(value, str):
                    value = Text(value=value)

            elif wrapper_type == Integer:
                if isinstance(value, (int, str)):
                    value = Integer(value=int(value))

            elif wrapper_type == Float:
                if isinstance(value, (int, float, str)):
                    value = Float(value=float(value))

            elif wrapper_type == Boolean:
                if isinstance(value, bool):
                    value = Boolean(value=value)

            elif wrapper_type == Array:
                if isinstance(value, list):
                    value = Array(pairs=value)

            processed[key] = value

        # If previous output fields were found, create an OutputFields instance
        if previous_output_data:
            for key, val in previous_output_data.items():
                if isinstance(val, str):
                    previous_output_data[key] = Text(value=val)
            processed["previous_output"] = OutputFields(**previous_output_data)

        return processed

    def to_dict(self) -> dict:
        """Convert to dict, unwrapping wrapper types and excluding internal fields.

        Returns:
            Dict with unwrapped field values, excluding _skip_validation and
            None previous_output.
        """

        data = asdict(self)

        result = {}
        for key, value in data.items():
            if key == "_skip_validation":
                continue

            if key == "previous_output" and value is None:
                continue

            if isinstance(value, dict):
                if "_values" in value:  # SingleChoice
                    result[key] = value["_values"]
                elif "values" in value and len(value) == 1:  # MultiChoice
                    result[key] = value["values"]
                elif "value" in value and len(value) == 1:  # Text, Integer, Float, Boolean
                    result[key] = value["value"]
                elif "path" in value:  # Script
                    result[key] = str(value["path"])
                elif "pairs" in value:  # Array
                    result[key] = value["pairs"]
                elif "user" in value:  # Credential
                    result[key] = value
                else:
                    result[key] = value
            else:
                result[key] = value

        return result

    def __post_init__(self):
        """Validate fields after initialization."""
        if self._skip_validation:
            return

        self._validate_action()
        self._validate_jev_api_key()
        self._validate_context()
        self._validate_questions_json()
        self._validate_api_base_url()
        self._validate_timeout_seconds()
        self._validate_variable_prefix()
        self._validate_confidence_threshold()

        if extension_manager.has_errors():
            raise DataValidationError(
                f"Validation failed with {extension_manager.error_count()} error(s)"
            )

    def _validate_action(self):
        """Validate action field — must be one of the accepted values."""
        if self.action is not None:
            valid_actions = ["Decide"]
            if self.action.value not in valid_actions:
                exc = DataValidationError(
                    f"Invalid action '{self.action.value}'. "
                    f"Valid actions: {', '.join(valid_actions)}"
                )
                extension_manager.add_error(exc, field="action", value=self.action.value)

    def _validate_jev_api_key(self):
        """Validate jev_api_key — the credential password must be non-empty."""
        if self.jev_api_key is not None:
            password = self.jev_api_key.password or ""
            if not password.strip():
                exc = DataValidationError(
                    "ERROR: Field 'jev_api_key' is required but empty"
                )
                extension_manager.add_error(exc, field="jev_api_key")

    def _validate_context(self):
        """Validate context field — must be non-empty and fully substituted."""
        if self.context is not None:
            value = self.context.value if self.context else ""
            if not value or not value.strip():
                exc = DataValidationError(
                    "ERROR: Field 'context' is required but empty"
                )
                extension_manager.add_error(exc, field="context")
            elif "${" in value:
                exc = DataValidationError(
                    "ERROR: Field 'context' was not substituted"
                )
                extension_manager.add_error(exc, field="context")

    def _validate_questions_json(self):
        """Validate questions_json field — must be non-empty and fully substituted."""
        if self.questions_json is not None:
            value = self.questions_json.value if self.questions_json else ""
            if not value or not value.strip():
                exc = DataValidationError(
                    "ERROR: Field 'questions_json' is required but empty"
                )
                extension_manager.add_error(exc, field="questions_json")
            elif "${" in value:
                exc = DataValidationError(
                    "ERROR: Field 'questions_json' was not substituted"
                )
                extension_manager.add_error(exc, field="questions_json")

    def _validate_api_base_url(self):
        """Validate api_base_url — when provided, must not end with a trailing slash."""
        if self.api_base_url is not None:
            value = self.api_base_url.value if self.api_base_url else ""
            if value and value.endswith("/"):
                exc = DataValidationError(
                    "Field 'api_base_url' must not end with a trailing slash"
                )
                extension_manager.add_error(exc, field="api_base_url", value=value)

    def _validate_timeout_seconds(self):
        """Validate timeout_seconds — must be >= 1 when provided."""
        if self.timeout_seconds is not None:
            value = self.timeout_seconds.value
            if value < 1:
                exc = DataValidationError(
                    "Field 'timeout_seconds' must be >= 1"
                )
                extension_manager.add_error(exc, field="timeout_seconds", value=value)

    def _validate_variable_prefix(self):
        """Validate variable_prefix — when provided, must be non-empty after stripping."""
        if self.variable_prefix is not None:
            value = self.variable_prefix.value if self.variable_prefix else ""
            if value is not None and not value.strip():
                exc = DataValidationError(
                    "Field 'variable_prefix' must not be empty when provided"
                )
                extension_manager.add_error(exc, field="variable_prefix")

    def _validate_confidence_threshold(self):
        """Validate confidence_threshold — must be between 0.0 and 1.0 inclusive."""
        if self.confidence_threshold is not None:
            value = self.confidence_threshold.value
            if value < 0.0 or value > 1.0:
                exc = DataValidationError(
                    f"Field 'confidence_threshold' must be between 0.0 and 1.0, got {value}"
                )
                extension_manager.add_error(
                    exc, field="confidence_threshold", value=value
                )
