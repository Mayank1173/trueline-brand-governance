"""
Trueline AI Review Engine

An explainable AI brand-governance application for reviewing content
against approved brand guidelines.

PROVISIONAL - Schema and APIs subject to team review.
"""

from trueline.config import settings
from trueline.models import (
    ApprovedFact,
    Category,
    Citation,
    Finding,
    Guideline,
    ReviewRequest,
    ReviewResponse,
    ReviewStatus,
    Severity,
)
from trueline.providers import AIProvider, AIProviderError, AnthropicProvider
from trueline.review import ReviewEngine, create_review_engine

__version__ = "0.1.0"

__all__ = [
    "settings",
    "Finding",
    "Guideline",
    "ApprovedFact",
    "ReviewRequest",
    "ReviewResponse",
    "ReviewStatus",
    "Category",
    "Severity",
    "Citation",
    "ReviewEngine",
    "create_review_engine",
    "AIProvider",
    "AIProviderError",
    "AnthropicProvider",
]
