"""Configuration management for the Trueline AI Review Engine."""


from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Anthropic API Configuration
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    anthropic_max_tokens: int = 4096
    anthropic_temperature: float = 0.0

    # Review Engine Configuration
    review_degraded_mode: bool = True

    # Logging
    log_level: str = "INFO"

    @property
    def ai_enabled(self) -> bool:
        """Check if AI provider is configured and enabled."""
        return bool(self.anthropic_api_key and self.anthropic_api_key.strip())


settings = Settings()
