"""Runtime configuration — every tunable lives here, sourced from environment.

Override any value with the ``REVIEW_`` prefix::

    REVIEW_MIN_WORKING_DAYS=30 uvicorn app.main:app

or from a ``.env`` file (gitignored) for local development.

Thresholds that decide whether a package passes live in
:mod:`app.core.report_constants` instead. The split is deliberate: this file
holds deployment settings — where things are stored, which model to call, who
may call us — while that file holds the institution's rules, which are read by
people arguing about whether twenty days is the right number.
"""

from __future__ import annotations

import secrets
from pathlib import Path

from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# Per-process fallback secret, used to sign certificate download tokens when no
# explicit api_secret_key is configured. Regenerated each restart — acceptable
# because tokens are short-lived, but it means links break on restart and do
# not work across multiple workers. Set REVIEW_API_SECRET_KEY in a real
# deployment; an HMAC keyed on "" is not a signature.
_FALLBACK_SECRET = secrets.token_hex(32)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="REVIEW_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ------------------------------------------------------------------ #
    # Service identity
    # ------------------------------------------------------------------ #
    app_title: str = "Internship Report Reviewer"
    app_version: str = "1.0.0"

    # NoDecode is load-bearing. Without it pydantic-settings JSON-decodes a
    # list field straight out of the environment, before any validator runs —
    # so REVIEW_CORS_ORIGINS=https://dash.example.com raises a SettingsError at
    # import time and the container crash-loops on a value a person would
    # reasonably type. With it, the raw string reaches _parse_origins below and
    # both forms work.
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:80",
        ],
        description=(
            "Allowed browser origins. Accepts a JSON array or a plain "
            "comma-separated list."
        ),
    )

    # ------------------------------------------------------------------ #
    # Storage
    # ------------------------------------------------------------------ #
    storage_root: Path = Field(
        default=Path(__file__).resolve().parent.parent.parent / "tmp",
        description="Root directory for per-submission working directories.",
    )

    db_path: Path = Field(
        default=Path(__file__).resolve().parent.parent.parent / "submissions.db",
        description="SQLite file storing reviewed submissions.",
    )

    # ------------------------------------------------------------------ #
    # Upload limits
    # ------------------------------------------------------------------ #
    max_pdf_bytes: int = Field(
        default=15 * 1024 * 1024,
        gt=0,
        description="Maximum accepted size for one attachment.",
    )
    max_image_bytes: int = Field(
        default=5 * 1024 * 1024,
        gt=0,
        description="Maximum accepted signature image size.",
    )
    read_chunk_bytes: int = Field(default=256 * 1024, gt=0)

    # ------------------------------------------------------------------ #
    # AI (OpenAI-compatible — advisory reading and email drafting only)
    # ------------------------------------------------------------------ #
    llm_base_url: str = Field(
        default="https://generativelanguage.googleapis.com/v1beta/openai/",
        description="OpenAI-compatible API base URL (Google Gemini by default).",
    )
    llm_model: str = Field(
        default="gemini-3.6-flash",
        description=(
            "Model used for the advisory reading and email drafting. Providers "
            "retire model ids, and a retired one fails as a 404 that looks like a "
            "configuration error — the log line from app.core.llm names it "
            "explicitly, and the provider's own error usually names the successor."
        ),
    )
    report_language: str = Field(
        default="English",
        description="Language the model writes student emails and readings in.",
    )
    llm_timeout_seconds: float = Field(
        default=20.0,
        gt=0,
        description=(
            "Per-call deadline for the model. One package costs four calls - three "
            "advisory passes and the student's email - so four times this is the "
            "review's worst case, and it has to stay under whatever read timeout "
            "the proxy in front of this service enforces. The SDK's own default is "
            "ten minutes, which turns a single hanging call into a gateway timeout "
            "and hands the caller an error page instead of a verdict."
        ),
    )

    # ------------------------------------------------------------------ #
    # Security
    # ------------------------------------------------------------------ #
    api_secret_key: str = Field(
        default="",
        description=(
            "If non-empty, /reports/from-n8n requires 'Authorization: Bearer <key>'. "
            "Also signs certificate download tokens."
        ),
    )

    @property
    def signing_secret(self) -> str:
        """Secret used to sign download tokens — the configured key, or a
        per-process random fallback so tokens are never signed with ''."""
        return self.api_secret_key or _FALLBACK_SECRET

    # ------------------------------------------------------------------ #
    # Validators
    # ------------------------------------------------------------------ #
    @field_validator("storage_root", "db_path", mode="before")
    @classmethod
    def _resolve_path(cls, v: str | Path) -> Path:
        return Path(v).resolve()

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_origins(cls, v):
        """Accept a JSON array, a comma-separated list, or a single origin."""
        if not isinstance(v, str):
            return v

        text = v.strip()
        if text.startswith("["):
            import json

            return json.loads(text)
        return [part.strip() for part in text.split(",") if part.strip()]


# Module-level singleton — import this everywhere.
settings = Settings()
