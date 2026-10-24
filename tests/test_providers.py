"""Tests for AI providers."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from trueline.config import settings
from trueline.models import Category, Guideline
from trueline.providers.anthropic import AnthropicProvider
from trueline.providers.base import AIProvider, AIProviderError


@pytest.fixture
def provider():
    return AnthropicProvider()


class TestAIProviderBase:
    def test_abstract_methods(self):
        """Test that AIProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AIProvider()


class TestAnthropicProvider:
    def test_name_property(self, provider):
        assert provider.name == "anthropic"

    def test_ai_enabled_false(self, provider):
        """Test health_check returns False when AI not configured."""
        # Patch the underlying field since ai_enabled is a property
        with patch.object(settings, "anthropic_api_key", None):
            import asyncio
            result = asyncio.run(provider.health_check())
            assert result is False

    @pytest.mark.asyncio
    async def test_analyze_raises_without_api_key(self, provider):
        """Test analyze raises when API key not configured."""
        with patch.object(settings, "anthropic_api_key", None):
            with pytest.raises(AIProviderError) as exc_info:
                await provider.analyze(
                    draft_text="Test",
                    content_purpose="test",
                    guidelines=[],
                    approved_facts=[],
                )
            assert "ANTHROPIC_API_KEY not configured" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_analyze_success(self, provider):
        """Test successful analysis with mocked client."""
        mock_client = AsyncMock()
        # "test" appears at offset 10-14 in "This is a test draft."
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='[{"matched_text": "test", "start": 10, "end": 14, "category": "banned_term", "severity": "high", "explanation": "Test", "citation": null, "suggested_fix": null, "confidence": 0.9, "requires_human_review": false}]')]
        mock_client.messages.create.return_value = mock_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            with patch.object(settings, "anthropic_api_key", "test-key"):
                findings = await provider.analyze(
                    draft_text="This is a test draft.",
                    content_purpose="email",
                    guidelines=[
                        Guideline(id="RULE_001", text="Do not use test", category="banned_term", source="Guidelines")
                    ],
                    approved_facts=[],
                )

        assert len(findings) == 1
        assert findings[0].matched_text == "test"
        assert findings[0].category == Category.BANNED_TERM

    @pytest.mark.asyncio
    async def test_analyze_invalid_json(self, provider):
        """Test handling of invalid JSON from model."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Not valid JSON")]
        mock_client.messages.create.return_value = mock_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            with patch.object(settings, "anthropic_api_key", "test-key"):
                with pytest.raises(AIProviderError) as exc_info:
                    await provider.analyze(
                        draft_text="Test",
                        content_purpose="test",
                        guidelines=[],
                        approved_facts=[],
                    )
                assert "Invalid JSON response" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_analyze_non_array_response(self, provider):
        """Test handling of non-array JSON response."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"not": "an array"}')]
        mock_client.messages.create.return_value = mock_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            with patch.object(settings, "anthropic_api_key", "test-key"):
                with pytest.raises(AIProviderError) as exc_info:
                    await provider.analyze(
                        draft_text="Test",
                        content_purpose="test",
                        guidelines=[],
                        approved_facts=[],
                    )
                assert "must be a JSON array" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_analyze_api_error(self, provider):
        """Test handling of Anthropic API errors."""
        import anthropic
        mock_client = AsyncMock()
        # Create a proper APIError with required request argument
        mock_client.messages.create.side_effect = anthropic.APIError(
            "Rate limit", request=MagicMock(), body=None
        )

        with patch.object(provider, "_get_client", return_value=mock_client):
            with patch.object(settings, "anthropic_api_key", "test-key"):
                with pytest.raises(AIProviderError) as exc_info:
                    await provider.analyze(
                        draft_text="Test",
                        content_purpose="test",
                        guidelines=[],
                        approved_facts=[],
                    )
                assert "Anthropic API error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_analyze_citation_validation(self, provider):
        """Test that citations are validated against supplied guidelines."""
        mock_client = AsyncMock()
        # AI returns a finding citing a guideline that WAS provided
        # "guaranteed" in "Product guaranteed works." is at offset 8-18
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='[{"id": "ai-1", "matched_text": "guaranteed", "start": 8, "end": 18, "category": "unsupported_claim", "severity": "high", "explanation": "Violates rule", "citation": {"rule_id": "RULE_001", "source": "Guidelines", "excerpt": "Do not use guaranteed"}, "suggested_fix": "Remove", "confidence": 0.9, "requires_human_review": true}]')]
        mock_client.messages.create.return_value = mock_response

        guidelines = [
            Guideline(id="RULE_001", text="Do not use guaranteed", category="unsupported_claim", source="Guidelines")
        ]

        with patch.object(provider, "_get_client", return_value=mock_client):
            with patch.object(settings, "anthropic_api_key", "test-key"):
                findings = await provider.analyze(
                    draft_text="Product guaranteed works.",
                    content_purpose="email",
                    guidelines=guidelines,
                    approved_facts=[],
                )

        assert len(findings) == 1
        assert findings[0].citation is not None
        assert findings[0].citation.rule_id == "RULE_001"

    @pytest.mark.asyncio
    async def test_analyze_unknown_citation_rejected(self, provider):
        """Test that citations to unknown guidelines are rejected."""
        mock_client = AsyncMock()
        # "test" in "This is a test." is at offset 10-14
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='[{"id": "ai-1", "matched_text": "test", "start": 10, "end": 14, "category": "banned_term", "severity": "high", "explanation": "Test", "citation": {"rule_id": "UNKNOWN", "source": "Unknown", "excerpt": "text"}, "suggested_fix": null, "confidence": 0.9, "requires_human_review": false}]')]
        mock_client.messages.create.return_value = mock_response

        guidelines = [
            Guideline(id="RULE_001", text="Do not use test", category="banned_term", source="Guidelines")
        ]

        with patch.object(provider, "_get_client", return_value=mock_client):
            with patch.object(settings, "anthropic_api_key", "test-key"):
                findings = await provider.analyze(
                    draft_text="This is a test.",
                    content_purpose="email",
                    guidelines=guidelines,
                    approved_facts=[],
                )

        # Citation should be None since UNKNOWN not in guidelines
        assert len(findings) == 1
        assert findings[0].citation is None

    @pytest.mark.asyncio
    async def test_analyze_offset_mismatch_rejected(self, provider):
        """Test that findings with offset mismatch are rejected."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        # matched_text "wrong" but draft has "different" at those offsets
        mock_response.content = [MagicMock(text='[{"id": "ai-1", "matched_text": "wrong", "start": 0, "end": 5, "category": "banned_term", "severity": "high", "explanation": "Test", "citation": null, "suggested_fix": null, "confidence": 0.9, "requires_human_review": false}]')]
        mock_client.messages.create.return_value = mock_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            with patch.object(settings, "anthropic_api_key", "test-key"):
                findings = await provider.analyze(
                    draft_text="different text",
                    content_purpose="email",
                    guidelines=[],
                    approved_facts=[],
                )

        # Finding should be dropped due to offset mismatch
        assert len(findings) == 0

    @pytest.mark.asyncio
    async def test_analyze_excerpt_not_in_guideline(self, provider):
        """Test handling when AI provides excerpt not in guideline text."""
        mock_client = AsyncMock()
        # "test" in "This is a test." is at offset 10-14
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='[{"id": "ai-1", "matched_text": "test", "start": 10, "end": 14, "category": "banned_term", "severity": "high", "explanation": "Test", "citation": {"rule_id": "RULE_001", "source": "Guidelines", "excerpt": "This excerpt does not exist in guideline"}, "suggested_fix": null, "confidence": 0.9, "requires_human_review": false}]')]
        mock_client.messages.create.return_value = mock_response

        guidelines = [
            Guideline(id="RULE_001", text="Do not use test word", category="banned_term", source="Guidelines")
        ]

        with patch.object(provider, "_get_client", return_value=mock_client):
            with patch.object(settings, "anthropic_api_key", "test-key"):
                findings = await provider.analyze(
                    draft_text="This is a test.",
                    content_purpose="email",
                    guidelines=guidelines,
                    approved_facts=[],
                )

        # Should still return finding but with corrected excerpt
        assert len(findings) == 1
        assert findings[0].citation is not None
        # Excerpt should be from actual guideline text
        assert findings[0].citation.excerpt in guidelines[0].text


class TestAnthropicProviderSDKCompatibility:
    """Tests to verify AnthropicProvider builds requests compatible with the installed SDK."""

    @pytest.mark.asyncio
    async def test_analyze_request_parameters(self):
        """Test that analyze() calls the SDK with correct parameters (no temperature)."""
        provider = AnthropicProvider()
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='[]')]
        mock_client.messages.create.return_value = mock_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            with patch.object(settings, "anthropic_api_key", "test-key"):
                await provider.analyze(
                    draft_text="Test draft",
                    content_purpose="email",
                    guidelines=[
                        Guideline(id="RULE_001", text="Do not use test", category="banned_term", source="Guidelines")
                    ],
                    approved_facts=[],
                )

        # Verify the call was made with correct parameters
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args.kwargs

        # Required parameters should be present
        assert "model" in call_kwargs
        assert "max_tokens" in call_kwargs
        assert "system" in call_kwargs
        assert "messages" in call_kwargs

        # Temperature should NOT be passed (not supported in SDK 2.1.0)
        assert "temperature" not in call_kwargs

        # Verify types
        assert isinstance(call_kwargs["model"], str)
        assert isinstance(call_kwargs["max_tokens"], int)
        assert isinstance(call_kwargs["system"], str)
        assert isinstance(call_kwargs["messages"], list)

    @pytest.mark.asyncio
    async def test_analyze_uses_settings_for_model_config(self):
        """Test that analyze() uses settings for model configuration."""
        provider = AnthropicProvider()
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='[]')]
        mock_client.messages.create.return_value = mock_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            with patch.object(settings, "anthropic_api_key", "test-key"):
                with patch.object(settings, "anthropic_model", "claude-3-haiku-20240307"):
                    with patch.object(settings, "anthropic_max_tokens", 2048):
                        await provider.analyze(
                            draft_text="Test draft",
                            content_purpose="email",
                            guidelines=[],
                            approved_facts=[],
                        )

        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == "claude-3-haiku-20240307"
        assert call_kwargs["max_tokens"] == 2048


class TestAnthropicProviderErrorHandling:
    """Tests for error handling paths in AnthropicProvider."""

    @pytest.mark.asyncio
    async def test_analyze_anthropic_api_error(self, provider):
        """Test handling of Anthropic API errors (lines 224-229)."""
        import anthropic
        mock_client = AsyncMock()
        mock_client.messages.create.side_effect = anthropic.APIError(
            "Rate limit exceeded", request=MagicMock(), body=None
        )

        with patch.object(provider, "_get_client", return_value=mock_client):
            with patch.object(settings, "anthropic_api_key", "test-key"):
                with pytest.raises(AIProviderError) as exc_info:
                    await provider.analyze(
                        draft_text="Test",
                        content_purpose="test",
                        guidelines=[],
                        approved_facts=[],
                    )
                assert "Anthropic API error" in str(exc_info.value)
                assert exc_info.value.provider == "anthropic"

    @pytest.mark.asyncio
    async def test_analyze_unexpected_error(self, provider):
        """Test handling of unexpected errors (lines 230-235)."""
        mock_client = AsyncMock()
        mock_client.messages.create.side_effect = RuntimeError("Network failure")

        with patch.object(provider, "_get_client", return_value=mock_client):
            with patch.object(settings, "anthropic_api_key", "test-key"):
                with pytest.raises(AIProviderError) as exc_info:
                    await provider.analyze(
                        draft_text="Test",
                        content_purpose="test",
                        guidelines=[],
                        approved_facts=[],
                    )
                assert "Unexpected error calling Anthropic" in str(exc_info.value)
                assert exc_info.value.provider == "anthropic"

    @pytest.mark.asyncio
    async def test_analyze_empty_response(self, provider):
        """Test handling of empty/unexpected response (lines 238-242)."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = []
        mock_client.messages.create.return_value = mock_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            with patch.object(settings, "anthropic_api_key", "test-key"):
                with pytest.raises(AIProviderError) as exc_info:
                    await provider.analyze(
                        draft_text="Test",
                        content_purpose="test",
                        guidelines=[],
                        approved_facts=[],
                    )
                assert "Empty or unexpected response" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_analyze_response_missing_text(self, provider):
        """Test handling of response without text attribute (lines 238-242)."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        # Create a content item without text attribute
        class ContentItem:
            pass
        mock_response.content = [ContentItem()]
        mock_client.messages.create.return_value = mock_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            with patch.object(settings, "anthropic_api_key", "test-key"):
                with pytest.raises(AIProviderError) as exc_info:
                    await provider.analyze(
                        draft_text="Test",
                        content_purpose="test",
                        guidelines=[],
                        approved_facts=[],
                    )
                assert "Empty or unexpected response" in str(exc_info.value)


class TestAnthropicProviderCitationValidation:
    """Tests for citation validation edge cases (lines 127-133, 139-141)."""

    @pytest.mark.asyncio
    async def test_analyze_citation_excerpt_not_in_guideline_fallback(self, provider):
        """Test excerpt fallback when excerpt not in guideline (lines 127-133)."""
        mock_client = AsyncMock()
        # "test" in "This is a test." at offset 10-14
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='[{"id": "ai-1", "matched_text": "test", "start": 10, "end": 14, "category": "banned_term", "severity": "high", "explanation": "Test", "citation": {"rule_id": "RULE_001", "source": "Guidelines", "excerpt": "This excerpt does not exist in guideline"}, "suggested_fix": null, "confidence": 0.9, "requires_human_review": false}]')]
        mock_client.messages.create.return_value = mock_response

        guidelines = [
            Guideline(id="RULE_001", text="Do not use test word", category="banned_term", source="Guidelines")
        ]

        with patch.object(provider, "_get_client", return_value=mock_client):
            with patch.object(settings, "anthropic_api_key", "test-key"):
                findings = await provider.analyze(
                    draft_text="This is a test.",
                    content_purpose="email",
                    guidelines=guidelines,
                    approved_facts=[],
                )

        # Should still return finding but with corrected excerpt from guideline
        assert len(findings) == 1
        assert findings[0].citation is not None
        assert findings[0].citation.excerpt in guidelines[0].text

    @pytest.mark.asyncio
    async def test_analyze_citation_unknown_rule_ignored(self, provider):
        """Test citation with unknown rule_id is ignored (lines 139-141)."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='[{"id": "ai-1", "matched_text": "test", "start": 10, "end": 14, "category": "banned_term", "severity": "high", "explanation": "Test", "citation": {"rule_id": "UNKNOWN_RULE", "source": "Unknown", "excerpt": "text"}, "suggested_fix": null, "confidence": 0.9, "requires_human_review": false}]')]
        mock_client.messages.create.return_value = mock_response

        guidelines = [
            Guideline(id="RULE_001", text="Do not use test", category="banned_term", source="Guidelines")
        ]

        with patch.object(provider, "_get_client", return_value=mock_client):
            with patch.object(settings, "anthropic_api_key", "test-key"):
                findings = await provider.analyze(
                    draft_text="This is a test.",
                    content_purpose="email",
                    guidelines=guidelines,
                    approved_facts=[],
                )

        # Citation should be None since UNKNOWN_RULE not in guidelines
        assert len(findings) == 1
        assert findings[0].citation is None


class TestAnthropicProviderOffsetValidation:
    """Tests for offset validation edge cases (lines 147-157)."""

    @pytest.mark.asyncio
    async def test_analyze_invalid_offsets_negative(self, provider):
        """Test finding with negative start offset is skipped (line 148)."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='[{"id": "ai-1", "matched_text": "test", "start": -5, "end": 14, "category": "banned_term", "severity": "high", "explanation": "Test", "citation": null, "suggested_fix": null, "confidence": 0.9, "requires_human_review": false}]')]
        mock_client.messages.create.return_value = mock_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            with patch.object(settings, "anthropic_api_key", "test-key"):
                findings = await provider.analyze(
                    draft_text="This is a test draft.",
                    content_purpose="email",
                    guidelines=[],
                    approved_facts=[],
                )

        assert len(findings) == 0

    @pytest.mark.asyncio
    async def test_analyze_invalid_offsets_end_exceeds_length(self, provider):
        """Test finding with end exceeding draft length is skipped (line 148)."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='[{"id": "ai-1", "matched_text": "test", "start": 10, "end": 100, "category": "banned_term", "severity": "high", "explanation": "Test", "citation": null, "suggested_fix": null, "confidence": 0.9, "requires_human_review": false}]')]
        mock_client.messages.create.return_value = mock_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            with patch.object(settings, "anthropic_api_key", "test-key"):
                findings = await provider.analyze(
                    draft_text="Short text",
                    content_purpose="email",
                    guidelines=[],
                    approved_facts=[],
                )

        assert len(findings) == 0

    @pytest.mark.asyncio
    async def test_analyze_invalid_offsets_start_after_end(self, provider):
        """Test finding with start > end is skipped (line 148)."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='[{"id": "ai-1", "matched_text": "test", "start": 14, "end": 10, "category": "banned_term", "severity": "high", "explanation": "Test", "citation": null, "suggested_fix": null, "confidence": 0.9, "requires_human_review": false}]')]
        mock_client.messages.create.return_value = mock_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            with patch.object(settings, "anthropic_api_key", "test-key"):
                findings = await provider.analyze(
                    draft_text="This is a test draft.",
                    content_purpose="email",
                    guidelines=[],
                    approved_facts=[],
                )

        assert len(findings) == 0

    @pytest.mark.asyncio
    async def test_analyze_offset_mismatch_skipped(self, provider):
        """Test finding with offset mismatch is skipped (lines 152-157)."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        # matched_text "wrong" but draft has "This" at offsets 0-4
        mock_response.content = [MagicMock(text='[{"id": "ai-1", "matched_text": "wrong", "start": 0, "end": 4, "category": "banned_term", "severity": "high", "explanation": "Test", "citation": null, "suggested_fix": null, "confidence": 0.9, "requires_human_review": false}]')]
        mock_client.messages.create.return_value = mock_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            with patch.object(settings, "anthropic_api_key", "test-key"):
                findings = await provider.analyze(
                    draft_text="This is a test draft.",
                    content_purpose="email",
                    guidelines=[],
                    approved_facts=[],
                )

        assert len(findings) == 0


class TestAnthropicProviderHealthCheck:
    """Tests for health_check behavior (lines 249-263)."""

    @pytest.mark.asyncio
    async def test_health_check_returns_false_when_ai_disabled(self, provider):
        """Test health_check returns False when AI not enabled (line 252)."""
        with patch.object(settings, "anthropic_api_key", None):
            result = await provider.health_check()
            assert result is False

    @pytest.mark.asyncio
    async def test_health_check_success(self, provider):
        """Test health_check returns True on successful connection (lines 253-261)."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="pong")]
        mock_client.messages.create.return_value = mock_response

        with patch.object(provider, "_get_client", return_value=mock_client):
            with patch.object(settings, "anthropic_api_key", "test-key"):
                result = await provider.health_check()
                assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure_returns_false(self, provider):
        """Test health_check returns False on exception (lines 262-263)."""
        mock_client = AsyncMock()
        mock_client.messages.create.side_effect = Exception("Connection failed")

        with patch.object(provider, "_get_client", return_value=mock_client):
            with patch.object(settings, "anthropic_api_key", "test-key"):
                result = await provider.health_check()
                assert result is False
