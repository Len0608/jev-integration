"""Actions module — business logic implementations."""

from actions.output import ActionOutput
from actions.decide import decide
from manager import ExtensionManager

extension_manager = ExtensionManager()

# Map action choice values to their implementing functions.
# Keys must match the SingleChoice values defined in template.json.
ACTION_MAPPER = {
    "Decide": decide,
}
