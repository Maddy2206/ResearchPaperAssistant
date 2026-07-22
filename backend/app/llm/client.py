import json
from collections.abc import AsyncIterator
from typing import TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.config import Settings, get_settings

T = TypeVar("T", bound=BaseModel)

# provider -> (base_url, default_model). base_url=None means OpenAI's default endpoint.
_PROVIDERS: dict[str, tuple[str | None, str]] = {
    "openai": (None, "gpt-4o-mini"),
    "groq": ("https://api.groq.com/openai/v1", "llama-3.3-70b-versatile"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai/", "gemini-2.0-flash"),
    "openrouter": ("https://openrouter.ai/api/v1", "openrouter/auto"),
    "ollama": (None, "llama3.1"),  # base_url resolved from settings.ollama_base_url
}

_KEY_ATTR = {
    "openai": "openai_api_key",
    "groq": "groq_api_key",
    "gemini": "gemini_api_key",
    "openrouter": "openrouter_api_key",
    "ollama": None,  # ollama needs no key
}

_MODEL_ATTR = {
    "openai": "openai_model",
    "groq": "groq_model",
    "gemini": "gemini_model",
    "openrouter": "openrouter_model",
    "ollama": "ollama_model",
}

_FALLBACK_ORDER = ["groq", "openai", "gemini", "openrouter", "ollama"]


def _has_key(settings: Settings, provider: str) -> bool:
    if provider == "ollama":
        return True
    attr = _KEY_ATTR[provider]
    return bool(getattr(settings, attr))


def _resolve_provider(settings: Settings) -> str:
    explicit = settings.llm_provider
    if explicit and explicit in _PROVIDERS and _has_key(settings, explicit):
        return explicit

    for provider in _FALLBACK_ORDER:
        if _has_key(settings, provider):
            return provider

    raise RuntimeError(
        "No LLM provider configured. Set LLM_PROVIDER and the matching "
        "*_API_KEY env var (or run Ollama locally)."
    )


class LLMClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.provider = _resolve_provider(self.settings)

        base_url, _default_model = _PROVIDERS[self.provider]
        if self.provider == "ollama":
            base_url = self.settings.ollama_base_url

        api_key = "not-needed" if self.provider == "ollama" else getattr(
            self.settings, _KEY_ATTR[self.provider]
        )

        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = getattr(self.settings, _MODEL_ATTR[self.provider]) or _PROVIDERS[self.provider][1]

    async def chat(
        self,
        system: str,
        user: str,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    async def stream_chat(
        self,
        system: str,
        user: str,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield delta

    async def structured(
        self,
        system: str,
        user: str,
        schema: type[T],
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> T:
        schema_json = json.dumps(schema.model_json_schema())
        structured_system = (
            f"{system}\n\n"
            "Respond with ONLY a single JSON object matching this JSON schema, "
            f"no prose, no markdown fences:\n{schema_json}"
        )

        last_error: Exception | None = None
        for attempt in range(2):
            raw = await self.chat(
                structured_system,
                user,
                temperature=temperature,
                max_tokens=max_tokens if attempt == 0 else max_tokens * 2,
            )
            cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            try:
                data = json.loads(cleaned)
                return schema.model_validate(data)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                continue

        raise ValueError(f"Failed to parse structured output after retries: {last_error}")


_client_singleton: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _client_singleton
    if _client_singleton is None:
        _client_singleton = LLMClient()
    return _client_singleton
