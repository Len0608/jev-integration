"""ActionOutput dataclass for the TypeSafe-Jev extension."""

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ActionOutput:
    """Output returned by action functions.

    Fields:
        prefix:       Effective variable prefix used for UAC global variable names.
        answers:      List of answer dicts from the Jev API, each with 'id', 'value',
                      and 'probability' (float rounded to 4 d.p.).
        low_confidence: Whether any answer probability fell below the threshold.
        answer_count: Number of answers received from the API.
    """

    prefix: Optional[str] = None
    answers: Optional[List[Dict[str, Any]]] = None
    low_confidence: Optional[bool] = None
    answer_count: Optional[int] = None

    def __post_init__(self):
        """Initialise list fields with safe defaults."""
        if self.answers is None:
            self.answers = []

    def print_output(self):
        """Print structured output to STDOUT.

        The full STDOUT format is handled directly inside the decide action
        (per-variable KEY=VALUE lines, audit block, completion marker).
        This method is a no-op for this extension because the action emits
        all required STDOUT content inline during execution.
        """

    def to_dict(self) -> Dict[str, Any]:
        """Convert to the Extension Output result dict.

        Returns a dict with the 'result' structure expected by UAC:
        {
            "result": {
                "prefix": "<PREFIX>",
                "answer_count": <N>,
                "low_confidence": <bool>,
                "answers": {
                    "<id>": {"value": "<val>", "probability": <float>},
                    ...
                }
            }
        }
        """
        answers_dict: Dict[str, Any] = {}
        for answer in (self.answers or []):
            q_id = answer.get("id", "")
            answers_dict[q_id] = {
                "value": answer.get("value", ""),
                "probability": round(float(answer.get("probability", 0.0)), 4),
            }

        return {
            "result": {
                "prefix": self.prefix,
                "answer_count": self.answer_count,
                "low_confidence": self.low_confidence,
                "answers": answers_dict,
            }
        }
