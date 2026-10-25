"""Optional AI integration boundary.

The MVP is fully deterministic and never calls an external model. A future
provider may implement ``ReviewAssistant``, but its output must never create
approved facts or citations. Any future AI text should only rewrite or explain
findings that were already validated against the database.

No provider is registered in this repository. ``TRUELINE_AI_ENABLED`` is
accepted for configuration clarity but does not enable any network client.
"""

from __future__ import annotations

from typing import Protocol

from .config import Settings
from .rule_engine.models import FindingDraft


class ReviewAssistant(Protocol):
    provider_name: str

    def explain_finding(self, finding: FindingDraft, draft_text: str) -> str | None: ...

    def suggest_contextual_fix(
        self, finding: FindingDraft, draft_text: str
    ) -> str | None: ...


class DisabledReviewAssistant:
    provider_name = "disabled"

    def explain_finding(self, finding: FindingDraft, draft_text: str) -> str | None:
        return None

    def suggest_contextual_fix(
        self, finding: FindingDraft, draft_text: str
    ) -> str | None:
        return None


def get_review_assistant(settings: Settings) -> ReviewAssistant:
    """Return the configured assistant.

    No external provider is integrated, so this always returns the disabled
    implementation even if the flag is set. This prevents accidental paid API
    calls and accidental model-generated citations.
    """

    _ = settings.ai_enabled
    return DisabledReviewAssistant()
