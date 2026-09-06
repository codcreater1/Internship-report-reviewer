"""Liveness probe payload.

Reports whether a model is configured, because the advisory reading and the
drafted student emails depend on it — but the *decision* does not, so
`ai_enabled: false` is a normal operating mode here, not a degraded one.

It names the model too. `ai_enabled` only says a key is present, and a key
plus a retired model id is a service that reports itself healthy while every
call comes back 404 — which is exactly what a deployment did after a model
was changed to one the project could not reach. Which id is in force is the
first thing anyone asks then, and it took a container log to answer.
"""

import sys

from app.core import llm
from app.core.config import settings


def get_health() -> dict:
    return {
        "status": "healthy",
        "service": settings.app_title,
        "version": settings.app_version,
        "ai_enabled": llm.is_enabled(),
        "llm_model": settings.llm_model if llm.is_enabled() else None,
        "python": sys.version.split()[0],
    }
