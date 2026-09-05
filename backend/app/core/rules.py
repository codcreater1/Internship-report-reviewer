"""The university's rules, loaded from a file rather than compiled in.

Every number in here is a decision a department made — twenty days, sixty out
of a hundred, five hundred words — and departments change them. Compiled in,
changing one meant editing Python, rebuilding an image and redeploying, which
is an absurd amount of ceremony for a line that says a placement is twenty
days rather than fifteen.

Two rules about the rules:

**A bad file stops the service.** Not a warning, not a fall back to the
defaults. A coordinator who edits a threshold, restarts, and sees the service
come up healthy would reasonably conclude their change took effect; silently
running the old value would be a lie told at exactly the moment somebody is
trying to be careful.

**Only the numbers are configurable.** Which findings reject and which ask for
a correction is not in the file. That distinction — nobody is refused for
something they can fix — is the argument this service exists to make, and a
service whose argument is a config value does not have one.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# Shipped alongside the code, one directory above the backend package, so the
# repository runs without configuration and a deployment can mount its own.
DEFAULT_RULES_PATH = Path(__file__).resolve().parents[3] / "rules" / "university-rules.json"


class RulesError(RuntimeError):
    """The rules file is unusable. Raised at import, so the service will not start."""


@dataclass(frozen=True)
class Rules:
    source: str

    min_working_days: int
    min_daily_hours: float
    max_daily_hours: float
    count_weekend_days: bool

    min_report_words: int
    required_report_sections: tuple[str, ...]

    min_evaluation_score: int

    similarity_reject_threshold: float
    similarity_warn_threshold: float

    required_attachment_count: int
    max_document_pages: int
    min_extractable_chars: int

    def as_dict(self) -> dict:
        """The effective rules, for the dashboard and for anyone asking why.

        The dashboard draws each figure against the line it is measured
        against; reading those lines from here rather than hardcoding them is
        what keeps the drawing honest when a department changes one.
        """
        return {
            # The file's name, not its path. Which rules are in force is worth
            # publishing; where the container keeps them is not.
            "source": Path(self.source).name,
            "attendance": {
                "min_working_days": self.min_working_days,
                "min_daily_hours": self.min_daily_hours,
                "max_daily_hours": self.max_daily_hours,
                "count_weekend_days": self.count_weekend_days,
            },
            "report": {
                "min_words": self.min_report_words,
                "required_sections": list(self.required_report_sections),
            },
            "evaluation": {"min_score": self.min_evaluation_score},
            "originality": {
                "reject_at": self.similarity_reject_threshold,
                "warn_at": self.similarity_warn_threshold,
            },
            "documents": {
                "required_attachment_count": self.required_attachment_count,
                "max_pages": self.max_document_pages,
                "min_extractable_chars": self.min_extractable_chars,
            },
        }


def _number(section: dict, group: str, key: str, kind, low, high):
    try:
        value = kind(section[key])
    except KeyError:
        raise RulesError(f"{group}.{key} is missing") from None
    except (TypeError, ValueError):
        raise RulesError(f"{group}.{key} is not a number: {section[key]!r}") from None

    if not low <= value <= high:
        raise RulesError(f"{group}.{key} is {value}; expected between {low} and {high}")
    return value


def load_rules(path: Path | None = None) -> Rules:
    """Read and check the rules file, or refuse to run."""
    path = path or Path(os.getenv("REVIEW_RULES_PATH") or DEFAULT_RULES_PATH)

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise RulesError(f"No rules file at {path}") from None
    except json.JSONDecodeError as exc:
        raise RulesError(f"{path} is not valid JSON: {exc}") from None

    try:
        attendance = raw["attendance"]
        report = raw["report"]
        evaluation = raw["evaluation"]
        originality = raw["originality"]
        documents = raw["documents"]
    except KeyError as exc:
        raise RulesError(f"{path} is missing the {exc.args[0]!r} section") from None

    sections = report.get("required_sections")
    if not isinstance(sections, list) or not all(isinstance(s, str) and s.strip() for s in sections):
        raise RulesError("report.required_sections must be a list of non-empty strings")

    weekends = attendance.get("count_weekend_days")
    if not isinstance(weekends, bool):
        raise RulesError("attendance.count_weekend_days must be true or false")

    min_hours = _number(attendance, "attendance", "min_daily_hours", float, 0.5, 24.0)
    max_hours = _number(attendance, "attendance", "max_daily_hours", float, 0.5, 24.0)
    if min_hours >= max_hours:
        raise RulesError(
            f"attendance.min_daily_hours ({min_hours}) must be below "
            f"attendance.max_daily_hours ({max_hours})"
        )

    warn_at = _number(originality, "originality", "warn_at", float, 0.0, 1.0)
    reject_at = _number(originality, "originality", "reject_at", float, 0.0, 1.0)
    if warn_at > reject_at:
        # A warning band above the rejection line would never be reached: the
        # package would already have been refused.
        raise RulesError(
            f"originality.warn_at ({warn_at}) must not be above "
            f"originality.reject_at ({reject_at})"
        )

    rules = Rules(
        source=str(path),
        min_working_days=_number(attendance, "attendance", "min_working_days", int, 1, 365),
        min_daily_hours=min_hours,
        max_daily_hours=max_hours,
        count_weekend_days=weekends,
        min_report_words=_number(report, "report", "min_words", int, 1, 100_000),
        required_report_sections=tuple(s.strip().lower() for s in sections),
        min_evaluation_score=_number(evaluation, "evaluation", "min_score", int, 0, 100),
        similarity_reject_threshold=reject_at,
        similarity_warn_threshold=warn_at,
        required_attachment_count=_number(
            documents, "documents", "required_attachment_count", int, 1, 20
        ),
        max_document_pages=_number(documents, "documents", "max_pages", int, 1, 10_000),
        min_extractable_chars=_number(
            documents, "documents", "min_extractable_chars", int, 0, 100_000
        ),
    )

    logger.info(
        "Rules loaded from %s: %d working days, %d/100 to pass, %d words, "
        "originality warns at %.2f and rejects at %.2f",
        path,
        rules.min_working_days,
        rules.min_evaluation_score,
        rules.min_report_words,
        rules.similarity_warn_threshold,
        rules.similarity_reject_threshold,
    )
    return rules


rules = load_rules()
