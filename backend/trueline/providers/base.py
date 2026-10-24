"""AI Provider interface for the Trueline AI Review Engine."""

from abc import ABC, abstractmethod

from trueline.models import ApprovedFact, Finding, Guideline


class AIProviderError(Exception):
    """Raised when the AI provider fails."""
    def __init__(self, message: str, provider: str, original_error: Exception | None = None):
        self.message = message
        self.provider = provider
        self.original_error = original_error
        super().__init__(f"{provider}: {message}")


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier."""
        pass

    @abstractmethod
    async def analyze(
        self,
        draft_text: str,
        content_purpose: str,
        guidelines: list[Guideline],
        approved_facts: list[ApprovedFact],
        evaluation_date: str | None = None,
    ) -> list[Finding]:
        """
        Analyze draft text against guidelines using AI.

        Args:
            draft_text: The content to review
            content_purpose: Purpose/context of the content
            guidelines: Approved brand guidelines
            approved_facts: Approved brand facts
            evaluation_date: Optional ISO date for fact status evaluation

        Returns:
            List of AI-generated findings

        Raises:
            AIProviderError: If the provider fails
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is available."""
        pass
