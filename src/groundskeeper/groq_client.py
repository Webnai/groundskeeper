"""GroqClient: a free-tier AIClient backend, added without touching training_data_bot.

This exists because of a real constraint hit while building this project:
no funded Anthropic or OpenAI account was available for the evaluation run
(see CHANGELOG.md). Groq's API is OpenAI-compatible and offers a genuinely
free, no-credit-card developer tier, so this backend reuses the exact same
`openai` SDK `training_data_bot` already depends on — just pointed at a
different `base_url`. Implementing `training_data_bot.ai.base.AIClient`
means every other component in this project (the auditor, the pipeline,
the baseline) works completely unchanged with this backend. This is the
provider-agnostic `AIClient` abstraction paying off against a real
constraint, not a hypothetical one — see CHANGELOG.md for how this came up
during the actual build.
"""

from __future__ import annotations

import os

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from training_data_bot.ai.base import AIClient, RetryableAIError
from training_data_bot.core.exceptions import AIClientError, ConfigurationError
from training_data_bot.core.logging import get_logger

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"


class GroqClient(AIClient):
    """Calls Groq-hosted open models via their OpenAI-compatible endpoint."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        key = api_key or os.environ.get("GROQ_API_KEY")
        if not key:
            raise ConfigurationError(
                "GROQ_API_KEY is not set. Get a free key (no card required) at "
                "console.groq.com and add it to .env."
            )
        self.model = model or os.environ.get("GROQ_MODEL", DEFAULT_GROQ_MODEL)

        try:
            import openai
        except ImportError as exc:
            raise ConfigurationError(
                "openai package required. Install with: pip install openai"
            ) from exc

        self._openai = openai
        self._client = openai.AsyncOpenAI(api_key=key, base_url=GROQ_BASE_URL)
        self.logger = get_logger("groundskeeper.ai.GroqClient")

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(RetryableAIError),
    )
    async def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore[arg-type]
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except self._openai.RateLimitError as exc:
            raise RetryableAIError(f"Groq rate limited: {exc}", model=self.model) from exc
        except self._openai.APIConnectionError as exc:
            raise RetryableAIError(f"Groq connection error: {exc}", model=self.model) from exc
        except self._openai.APIStatusError as exc:
            if exc.status_code >= 500:
                raise RetryableAIError(
                    f"Groq server error: {exc}", model=self.model, status_code=exc.status_code
                ) from exc
            raise AIClientError(
                f"Groq API error: {exc}", model=self.model, status_code=exc.status_code
            ) from exc
        except Exception as exc:
            raise AIClientError(f"Groq API call failed: {exc}", model=self.model) from exc

        choice = response.choices[0] if response.choices else None
        content = choice.message.content if choice and choice.message else None
        if not content:
            raise AIClientError("Groq response contained no text content", model=self.model)
        return content

    async def close(self) -> None:
        await self._client.close()
