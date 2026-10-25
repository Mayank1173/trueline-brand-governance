"""Original AI labels that may accompany a finding.

The deterministic engine does not call a model and always leaves this field
``None``. A future AI adapter owned by Mayank may populate it, but it must not
change the deterministic category, severity, citation, or review decision.
"""

from __future__ import annotations

from enum import Enum


class AILabel(str, Enum):
    VIOLATION = "VIOLATION"
    NEEDS_HUMAN_JUDGEMENT = "NEEDS_HUMAN_JUDGEMENT"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    OUTDATED = "OUTDATED"


AI_LABEL_VALUES = frozenset(label.value for label in AILabel)
