from __future__ import annotations

import os
from dataclasses import dataclass


TRUE_VALUES = {"1", "true", "yes", "on"}


@dataclass(frozen=True, repr=False)
class LLMConfig:
    api_key: str
    base_url: str
    model: str
    provider: str
    enabled: bool

    @property
    def is_ready(self) -> bool:
        return self.enabled and bool(self.api_key)


def load_llm_config() -> LLMConfig:
    return LLMConfig(
        api_key=os.getenv("LLM_API_KEY", ""),
        base_url=os.getenv("LLM_BASE_URL", ""),
        model=os.getenv("LLM_MODEL", ""),
        provider=os.getenv("LLM_PROVIDER", "openai_compatible"),
        enabled=_env_enabled(os.getenv("LLM_ENABLED", "false")),
    )


def get_llm_status() -> dict[str, str | bool]:
    config = load_llm_config()
    if not config.enabled:
        return {"enabled": False, "reason": "disabled"}
    if not config.api_key:
        return {"enabled": False, "reason": "missing_api_key"}
    return {"enabled": True, "provider": config.provider}


def call_llm_for_intent(message: str) -> str | dict | None:
    config = load_llm_config()
    if not config.is_ready:
        return None

    # Real model calls are intentionally not wired yet. Keep route generation
    # controlled by deterministic backend rules until the LLM contract is ready.
    return None


def _env_enabled(value: str | None) -> bool:
    return (value or "").strip().lower() in TRUE_VALUES
