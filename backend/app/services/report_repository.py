"""Persistent storage for reviewed report packages (SQLite, stdlib only).

Mirrors :mod:`app.services.application_repository` exactly — same connection
helper, same lock, same "store the response model whole as JSON" approach — so
there is one storage idiom in this codebase rather than two.

A completion package is an event with its own lifecycle: a student can submit,
be asked for a correction, and submit again. Each attempt is its own row rather
than an overwrite, so the history stays readable. ``application_id`` is an
optional caller-supplied reference to whatever record approved the placement;
this service never resolves it, it only groups by it.

The originality corpus is rebuilt from this table at startup
(:func:`accepted_report_bodies`) so a restart does not amnesty a report that was
copied from a submission accepted last week.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone

from app.core.config import settings
from app.core.report_constants import STATUS_APPROVED, STATUS_PENDING, STATUS_SIGNED
from app.models.report import ReportSubmissionResponse

_lock = threading.Lock()


def _connect() -> sqlite3.Connection:
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _lock, _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS report_submissions (
                id             TEXT PRIMARY KEY,
                created_at     TEXT NOT NULL,
                application_id TEXT,
                status         TEXT NOT NULL,
                report_body    TEXT NOT NULL,
                data           TEXT NOT NULL
            )
            """
        )
        # Queue views filter by status and by candidate; both are read on every
        # dashboard refresh.
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_report_status ON report_submissions (status)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_report_application "
            "ON report_submissions (application_id)"
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS report_events (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                submission_id TEXT NOT NULL,
                at            TEXT NOT NULL,
                kind          TEXT NOT NULL,
                detail        TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_report_events_submission "
            "ON report_events (submission_id)"
        )


def add(submission: ReportSubmissionResponse, report_body: str = "") -> ReportSubmissionResponse:
    """Store a submission.

    ``report_body`` is the extracted prose, kept in its own column rather than
    dug out of the JSON blob: the originality index reloads every accepted body
    at startup, and that should be one indexed scan, not a parse of every row.
    """
    with _lock, _connect() as conn:
        conn.execute(
            "INSERT INTO report_submissions "
            "(id, created_at, application_id, status, report_body, data) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                submission.id,
                submission.created_at,
                submission.application_id,
                submission.status,
                report_body,
                submission.model_dump_json(),
            ),
        )
    return submission


def update(submission: ReportSubmissionResponse) -> ReportSubmissionResponse:
    with _lock, _connect() as conn:
        conn.execute(
            "UPDATE report_submissions SET status = ?, data = ? WHERE id = ?",
            (submission.status, submission.model_dump_json(), submission.id),
        )
    return submission


def delete(submission_id: str) -> bool:
    """Remove one submission by id. Returns True if a row was deleted."""
    with _lock, _connect() as conn:
        cur = conn.execute("DELETE FROM report_submissions WHERE id = ?", (submission_id,))
        return cur.rowcount > 0


def get_by_id(submission_id: str) -> ReportSubmissionResponse | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT data FROM report_submissions WHERE id = ?", (submission_id,)
        ).fetchone()
    return ReportSubmissionResponse.model_validate_json(row["data"]) if row else None


def list_all(status: str | None = None) -> list[ReportSubmissionResponse]:
    """Newest first, optionally filtered to one status."""
    query = "SELECT data FROM report_submissions"
    params: tuple = ()
    if status:
        query += " WHERE status = ?"
        params = (status,)
    query += " ORDER BY created_at DESC"

    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return [ReportSubmissionResponse.model_validate_json(row["data"]) for row in rows]


def list_for_application(application_id: str) -> list[ReportSubmissionResponse]:
    """Every completion attempt made against one application, newest first."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT data FROM report_submissions WHERE application_id = ? "
            "ORDER BY created_at DESC",
            (application_id,),
        ).fetchall()
    return [ReportSubmissionResponse.model_validate_json(row["data"]) for row in rows]


# Statuses whose reports join the corpus future submissions are compared
# against. Rejected and clarification-held packages are excluded: indexing a
# copied report would let it poison the index against the original it was
# taken from, and indexing a draft that is about to be resubmitted would make
# the student's own corrected version look plagiarised.
_ACCEPTED_STATUSES = (STATUS_APPROVED, STATUS_PENDING, STATUS_SIGNED)


def accepted_report_bodies() -> list[tuple[str, str]]:
    """Return ``(submission_id, report_body)`` for every accepted report."""
    placeholders = ", ".join("?" for _ in _ACCEPTED_STATUSES)
    with _connect() as conn:
        rows = conn.execute(
            f"SELECT id, report_body FROM report_submissions "
            f"WHERE status IN ({placeholders}) AND report_body != '' "
            f"ORDER BY created_at",
            _ACCEPTED_STATUSES,
        ).fetchall()
    return [(row["id"], row["report_body"]) for row in rows]


# --------------------------------------------------------------------------- #
# Audit trail
#
# A certificate is an institutional claim about a real person, and somebody
# will eventually ask how it came to be issued: what the checks found on the
# day, whether the reading arrived, who signed, what they acknowledged when
# they did. The submission row answers the first question and overwrites the
# rest — signing rewrites the same row, so the state before the signature is
# gone the moment it lands.
#
# These rows are append-only and never rewritten. They are the difference
# between "this package is signed" and "this package was signed by this person
# at this time, having acknowledged these two open points".
# --------------------------------------------------------------------------- #


def add_event(submission_id: str, kind: str, detail: dict | None = None) -> None:
    """Record one thing that happened to a submission."""
    with _lock, _connect() as conn:
        conn.execute(
            "INSERT INTO report_events (submission_id, at, kind, detail) VALUES (?, ?, ?, ?)",
            (
                submission_id,
                datetime.now(timezone.utc).isoformat(),
                kind,
                json.dumps(detail or {}),
            ),
        )


def events_for(submission_id: str) -> list[dict]:
    """Everything recorded against one submission, oldest first."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT at, kind, detail FROM report_events "
            "WHERE submission_id = ? ORDER BY id ASC",
            (submission_id,),
        ).fetchall()

    return [
        {"at": row["at"], "kind": row["kind"], "detail": json.loads(row["detail"] or "{}")}
        for row in rows
    ]
