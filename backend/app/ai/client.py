"""Thin OpenAI client wrapper for structured extraction (PRD §14, §35).

The LLM is used ONLY for document understanding/extraction and (later)
explanation. It never computes risk or makes verification decisions.
"""

from typing import TypeVar

from pydantic import BaseModel

from app.config import get_settings

T = TypeVar("T", bound=BaseModel)

settings = get_settings()


class AIUnavailableError(Exception):
    """Raised when the AI cannot be called (no key) or the call fails."""


class AIClient:
    def __init__(self) -> None:
        self._client = None
        if settings.openai_api_key:
            try:
                from openai import OpenAI

                self._client = OpenAI(api_key=settings.openai_api_key)
            except Exception:  # pragma: no cover - import/init failure guard
                self._client = None

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    def extract_structured(
        self,
        model: type[T],
        system_prompt: str,
        user_prompt: str,
        image_base64: str | None = None,
        image_media_type: str = "image/png",
    ) -> T:
        """Call the LLM with Structured Outputs and validate against `model`.

        If image_base64 is provided, the document is sent as a vision image
        (for PNG/JPG invoices); otherwise user_prompt is plain text.

        Raises AIUnavailableError if the AI is not configured or the call
        fails for any reason. Callers must degrade gracefully.
        """
        if self._client is None:
            raise AIUnavailableError(
                "AI extraction is not configured (OPENAI_API_KEY missing)."
            )

        if image_base64:
            user_content = [
                {"type": "text", "text": user_prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{image_media_type};base64,{image_base64}"
                    },
                },
            ]
        else:
            user_content = user_prompt

        try:
            response = self._client.beta.chat.completions.parse(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                response_format=model,
                temperature=0,
            )
        except Exception as exc:  # network, API, schema errors
            raise AIUnavailableError(f"AI request failed: {exc}") from exc

        parsed = response.choices[0].message.parsed
        if parsed is None:
            raise AIUnavailableError("AI returned no parseable structured output.")
        return parsed

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        """Plain chat completion used for explanation generation.

        Raises AIUnavailableError on any failure; callers degrade gracefully.
        """
        if self._client is None:
            raise AIUnavailableError("AI is not configured.")
        try:
            response = self._client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )
        except Exception as exc:
            raise AIUnavailableError(f"AI request failed: {exc}") from exc

        text = (response.choices[0].message.content or "").strip()
        if not text:
            raise AIUnavailableError("AI returned an empty explanation.")
        return text


ai_client = AIClient()
