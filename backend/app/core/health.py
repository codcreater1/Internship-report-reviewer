"""Liveness probe payload.

Reports whether a model is configured, because the advisory reading and the
drafted student emails depend on it — but the *decision* does not, so
`ai_enabled: false` is a normal operating mode here, not a degraded one.
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
        "python": sys.version.split()[0],
    }
