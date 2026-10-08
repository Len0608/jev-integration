"""OutputFields dataclass for real-time UI updates."""

from dataclasses import dataclass, asdict
from typing import Optional
from universal_extension import ui
from fields.types import Text


@dataclass
class OutputFields:
    """Real-time output fields for UAC UI updates.

    Fields sync with the UAC UI in real-time during execution and are
    available in subsequent re-runs via InputFields.previous_output.

    Corresponds to the Output Only fields defined in template.json:
    - answers_written  (Text Field 3) — count and prefix of written answers
    - low_confidence   (Text Field 4) — mirrors the LOW_CONFIDENCE global variable
    """

    # Number of answers written and the variable prefix used
    answers_written: Optional[Text] = None

    # Whether any answer probability fell below the configured threshold
    low_confidence: Optional[Text] = None

    def update(self, **fields):
        """Update fields and sync with UAC UI in real-time.

        Args:
            **fields: Field names and string values to update. String values
                      are automatically wrapped in the Text type.
        """
        for field_name, field_value in fields.items():
            if hasattr(self, field_name):
                if isinstance(field_value, str):
                    field_value = Text(field_value)
                setattr(self, field_name, field_value)
        ui.update_output_fields(fields)

    def to_dict(self) -> dict:
        """Get current fields as a plain dictionary.

        Returns:
            Dict containing only non-None fields with Text wrappers unwrapped
            to their underlying string values.
        """
        result = {}
        for k, v in asdict(self).items():
            if v is not None:
                result[k] = v["value"] if isinstance(v, dict) and "value" in v else v
        return result

    def clear(self):
        """Reset all fields to None."""
        self.answers_written = None
        self.low_confidence = None
