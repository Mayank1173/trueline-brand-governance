"""Anthropic Claude provider for the Trueline AI Review Engine."""

import json
import logging

import anthropic

from trueline.config import settings
from trueline.models import (
    ApprovedFact,
    Category,
    Citation,
    Finding,
    FindingLabel,
    Guideline,
    ReviewRequest,
    Severity,
)
from trueline.providers.base import AIProvider, AIProviderError

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = (
    "You are a brand compliance reviewer. Your task is to analyze draft "
    "content against approved brand guidelines and identify potential "
    "violations.\n\n"
    "You will receive:\n"
    "1. Draft text to review\n"
    "2. Content purpose/context\n"
    "3. Approved brand guidelines (each with id, text, category, source)\n"
    "4. Approved brand facts (each with id, claim, evidence, category)\n\n"
    "Your output MUST be a JSON array of findings. Each finding must have:\n"
    "- matched_text: Exact substring from the draft that violates a guideline\n"
    "- start: Zero-based start index (inclusive) of matched_text in draft\n"
    "- end: Zero-based end index (exclusive) of matched_text in draft\n"
    "- category: One of: banned_term, tone, missing_disclaimer, "
    "unsupported_claim, preferred_terminology, required_phrase, "
    "product_name_inconsistency, formatting, missing_content, length_limit\n"
    "- severity: One of: low, medium, high\n"
    "- explanation: Why this violates the guideline\n"
    "- citation: Object with rule_id, source, and an excerpt copied from the "
    "supporting guideline or approved fact (or null if no source applies). "
    "For a fact citation, rule_id is the fact id and excerpt is copied from "
    "that fact's claim.\n"
    "- suggested_fix: Proposed correction (or null if not applicable)\n"
    "- confidence: Float 0.0 to 1.0\n"
    "- requires_human_review: Boolean\n\n"
    "CRITICAL RULES:\n"
    "1. You MUST only cite guidelines that were provided in the input. "
    "Never invent rule IDs, sources, or excerpts.\n"
    "2. The matched_text MUST exactly match draft_text[start:end]. "
    "Verify this before output.\n"
    "3. If no guideline supports a finding, set citation to null.\n"
    "4. If you cannot determine a suggested fix, set suggested_fix to null.\n"
    "5. Flag uncertain or consequential findings with "
    "requires_human_review = true.\n"
    "6. Return an empty array [] if no issues are found. Do not invent issues.\n"
    "7. Only return the JSON array, no additional text."
)


def _build_user_prompt(request: ReviewRequest) -> str:
    """Build the user prompt with draft and guidelines."""
    guidelines_json = [
        {
            "id": g.id,
            "title": g.title,
            "text": g.text,
            "category": g.category,
            "source": g.source,
        }
        for g in request.guidelines
    ]

    facts_json = [
        {
            "id": f.id,
            "claim": f.claim,
            "evidence": f.evidence,
            "category": f.category,
        }
        for f in request.approved_facts
    ]

    return f"""Draft text to review:
---
{request.draft_text}
---

Content purpose: {request.content_purpose}

Approved brand guidelines:
{json.dumps(guidelines_json, indent=2)}

Approved brand facts:
{json.dumps(facts_json, indent=2)}

Return findings as a JSON array."""


def _parse_findings(
    response_text: str,
    draft_text: str,
    guidelines: list[Guideline],
    approved_facts: list[ApprovedFact] | None = None,
) -> list[Finding]:
    """Parse and validate AI response into Finding objects."""
    try:
        raw_findings = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise AIProviderError(
            f"Invalid JSON response from model: {e}",
            provider="anthropic",
        )

    if not isinstance(raw_findings, list):
        raise AIProviderError(
            "Model response must be a JSON array",
            provider="anthropic",
        )

    # Build lookups for citation validation. A finding may cite either a
    # guideline or an approved fact; both use the source row's id as rule_id.
    guideline_map = {g.id: g for g in guidelines}
    fact_map = {f.id: f for f in approved_facts or []}

    findings = []
    for idx, raw in enumerate(raw_findings):
        if not isinstance(raw, dict):
            logger.warning(f"Skipping non-dict finding at index {idx}")
            continue

        # Validate citation against supplied guidelines or approved facts.
        citation = None
        if raw.get("citation"):
            cit_data = raw["citation"]
            rule_id = cit_data.get("rule_id")
            if rule_id and rule_id in guideline_map:
                guideline = guideline_map[rule_id]
                # Verify excerpt exists in guideline text
                excerpt = cit_data.get("excerpt", "")
                if excerpt and excerpt not in guideline.text:
                    logger.warning(
                        f"Citation excerpt not found in guideline {rule_id}; "
                        f"using guideline text instead"
                    )
                    excerpt = guideline.text[:200]
                citation = Citation(
                    rule_id=rule_id,
                    source=guideline.source,
                    excerpt=excerpt or guideline.text[:200],
                    document_id=guideline.document_id,
                    section=guideline.section,
                )
            elif rule_id and rule_id in fact_map:
                fact = fact_map[rule_id]
                excerpt = cit_data.get("excerpt", "")
                if excerpt and excerpt not in fact.claim:
                    logger.warning(
                        f"Citation excerpt not found in approved fact {rule_id}; "
                        f"using the approved claim instead"
                    )
                    excerpt = fact.claim[:200]
                citation = Citation(
                    rule_id=rule_id,
                    source=fact.evidence,
                    excerpt=excerpt or fact.claim[:200],
                    document_id=None,
                    section=None,
                )
            else:
                logger.warning(f"Citation references unknown rule_id: {rule_id}; ignoring")

        # Validate offsets
        start = raw.get("start", 0)
        end = raw.get("end", 0)
        matched_text = raw.get("matched_text", "")

        if start < 0 or end > len(draft_text) or start > end:
            logger.warning(
                f"Invalid offsets start={start}, end={end} for draft length "
                f"{len(draft_text)}"
            )
            continue

        actual_text = draft_text[start:end]
        if actual_text != matched_text:
            logger.warning(
                f"Offset mismatch: draft[{start}:{end}] = '{actual_text}' "
                f"!= matched_text = '{matched_text}'"
            )
            # Do NOT silently correct - skip this finding
            continue

        # Parse label from AI response if provided
        label_str = raw.get("label")
        label = FindingLabel(label_str) if label_str else None

        # Parse rule_id from AI response if provided
        rule_id = raw.get("rule_id")

        finding = Finding(
            id=raw.get("id", f"finding-{idx}"),
            matched_text=matched_text,
            start=start,
            end=end,
            category=Category(raw.get("category", "unsupported_claim")),
            severity=Severity(raw.get("severity", "medium")),
            explanation=raw.get("explanation", ""),
            citation=citation,
            suggested_fix=raw.get("suggested_fix"),
            confidence=float(raw.get("confidence", 0.5)),
            requires_human_review=bool(raw.get("requires_human_review", False)),
            label=label,
            rule_id=rule_id,
        )
        findings.append(finding)

    return findings


class AnthropicProvider(AIProvider):
    """Anthropic Claude API provider."""

    def __init__(self) -> None:
        self._client: anthropic.AsyncAnthropic | None = None

    @property
    def name(self) -> str:
        return "anthropic"

    def _get_client(self) -> anthropic.AsyncAnthropic:
        if self._client is None:
            if not settings.trueline_ai_enabled:
                raise AIProviderError(
                    "AI review is disabled (set TRUELINE_AI_ENABLED=true)",
                    provider="anthropic",
                )
            if not settings.anthropic_api_key:
                raise AIProviderError(
                    "ANTHROPIC_API_KEY not configured",
                    provider="anthropic",
                )
            self._client = anthropic.AsyncAnthropic(
                api_key=settings.anthropic_api_key,
                timeout=settings.anthropic_timeout_seconds,
            )
        return self._client

    async def analyze(
        self,
        draft_text: str,
        content_purpose: str,
        guidelines: list[Guideline],
        approved_facts: list[ApprovedFact],
        evaluation_date: str | None = None,
    ) -> list[Finding]:
        """Analyze draft using Anthropic Claude."""
        client = self._get_client()

        request = ReviewRequest(
            draft_text=draft_text,
            brand_id="",  # Not used in prompt
            content_purpose=content_purpose,
            guidelines=guidelines,
            approved_facts=approved_facts,
            evaluation_date=evaluation_date,
        )

        user_prompt = _build_user_prompt(request)

        try:
            response = await client.messages.create(
                model=settings.anthropic_model,
                max_tokens=settings.anthropic_max_tokens,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
        except anthropic.APIError as e:
            raise AIProviderError(
                f"Anthropic API error: {e}",
                provider="anthropic",
                original_error=e,
            )
        except Exception as e:
            raise AIProviderError(
                f"Unexpected error calling Anthropic: {e}",
                provider="anthropic",
                original_error=e,
            )

        # Extract text from response
        if not response.content or not hasattr(response.content[0], "text"):
            raise AIProviderError(
                "Empty or unexpected response from Anthropic",
                provider="anthropic",
            )

        response_text = response.content[0].text
        logger.debug(f"Anthropic response: {response_text[:500]}...")

        return _parse_findings(response_text, draft_text, guidelines, approved_facts)

    async def health_check(self) -> bool:
        """Check if Anthropic API is accessible."""
        if not settings.ai_enabled:
            return False
        try:
            client = self._get_client()
            # Minimal request to verify connectivity
            await client.messages.create(
                model=settings.anthropic_model,
                max_tokens=10,
                messages=[{"role": "user", "content": "ping"}],
            )
            return True
        except Exception:
            return False
