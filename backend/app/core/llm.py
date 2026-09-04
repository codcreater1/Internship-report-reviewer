"""Thin wrapper around an OpenAI-compatible LLM API for structured CV evaluation.

Provider-agnostic: talks to any OpenAI-compatible endpoint via the ``openai``
SDK. Defaults to Groq (free, fast). Switch providers via env vars — see
``.env.example``.

When ``LANGFUSE_PUBLIC_KEY`` and ``LANGFUSE_SECRET_KEY`` are set, every LLM
call is automatically traced in LangFuse (latency, tokens, input/output).
Set ``LANGFUSE_HOST`` to self-host; defaults to cloud.langfuse.com.
"""

from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


def _create(kwargs: dict[str, Any]) -> str:
    """One completion call, returning the message text."""
    response = _client().chat.completions.create(**kwargs)
    return (response.choices[0].message.content or "").strip()


def _is_bad_request(exc: Exception) -> bool:
    """Whether the provider rejected the request itself, rather than us.

    Matched by status code and class name rather than by importing the SDK's
    exception types, because the client is chosen at call time — it may be the
    LangFuse-wrapped OpenAI class instead of the plain one.
    """
    if getattr(exc, "status_code", None) == 400:
        return True
    return type(exc).__name__ in {"BadRequestError", "UnprocessableEntityError"}


def _api_key() -> str:
    return os.getenv("LLM_API_KEY", "")


def is_enabled() -> bool:
    return bool(_api_key())


def _langfuse_enabled() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))


@lru_cache(maxsize=1)
def _client():
    if _langfuse_enabled():
        from langfuse.openai import OpenAI
        logger.info("LLM client initialised with LangFuse observability")
    else:
        from openai import OpenAI

    # No retries, and a deadline the proxy in front of this service can outlive.
    # The SDK defaults to ten minutes and two retries, so one unresponsive call
    # could hold a request open for half an hour; a package would then reach the
    # caller as a gateway timeout rather than as the verdict it already has,
    # because the deterministic checks finished long before the model was asked
    # anything. Failing fast costs an advisory reading. Failing slow costs the
    # answer.
    return OpenAI(
        api_key=_api_key(),
        base_url=settings.llm_base_url,
        timeout=settings.llm_timeout_seconds,
        max_retries=0,
    )


def complete_json(
    *,
    system: str,
    user: str,
    schema: dict[str, Any],
    max_tokens: int = 1500,
    trace_name: str = "llm-call",
) -> dict[str, Any] | None:
    """Call the LLM and return a JSON dict matching *schema*, or ``None`` on failure.

    ``trace_name`` labels the call in LangFuse (e.g. "cv-evaluation",
    "email-generation"). Ignored when LangFuse is not configured.
    """
    if not is_enabled():
        return None

    system_prompt = (
        f"{system}\n\n"
        "Respond with ONE valid JSON object and nothing else (no markdown, no "
        "code fences). It must match this JSON schema:\n"
        f"{json.dumps(schema)}"
    )

    kwargs: dict[str, Any] = dict(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=max_tokens,
    )
    if _langfuse_enabled():
        kwargs["name"] = trace_name

    try:
        text = _create(kwargs)
    except Exception as exc:  # noqa: BLE001 — provider errors vary by SDK
        # Not every OpenAI-compatible endpoint accepts response_format. Gemini's
        # compatibility layer in particular rejects some shapes of it outright,
        # and a 400 there looks identical to a real failure from the outside.
        #
        # Dropping it costs nothing: the system prompt already demands one JSON
        # object and the response is parsed below either way. So retry once
        # without it before giving up — but only for a bad-request, since
        # retrying a bad key or a dead network just doubles the wait.
        if _is_bad_request(exc) and "response_format" in kwargs:
            logger.info(
                "LLM rejected response_format (%s); retrying without it. "
                "Set a provider that supports it to restore strict JSON mode.",
                type(exc).__name__,
            )
            kwargs.pop("response_format")
            try:
                text = _create(kwargs)
            except Exception as retry_exc:  # noqa: BLE001
                logger.error(
                    "LLM request failed after retry: %s: %s",
                    type(retry_exc).__name__,
                    retry_exc,
                )
                return None
        else:
            # Type and message, not a bare traceback: this line is the only
            # thing visible to whoever is looking at container logs wondering
            # why the advisory reading is empty.
            logger.error(
                "LLM request failed (%s: %s); falling back to deterministic logic",
                type(exc).__name__,
                exc,
            )
            return None

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.error("LLM returned non-JSON content: %s", text[:200])
        return None
