"""The advisory graph: that it chains, and that it cannot reach the decision.

The second half is the point. This graph is the only place a model runs, and
the whole design rests on its output being commentary. The tests below try to
make it matter — a model that finds discrepancies, a model that returns
nonsense, a model that is down — and assert the status is identical every time.
"""

from __future__ import annotations

import pytest

from app.agents import review_graph as G
from app.core import llm
from app.core.report_constants import STATUS_APPROVED

FACTS = {
    "company": "Nova Logistics",
    "start_date": "2026-07-13",
    "end_date": "2026-08-21",
    "counted_working_days": 30,
    "total_hours": 240,
    "evaluation_score": 84,
    "report_word_count": 625,
}

REPORT = "I spent the placement on the route estimate caching layer. " * 40


@pytest.fixture
def model(monkeypatch):
    """Stub the model, recording every call so the chain can be asserted."""
    calls = []

    def fake(*, system, user, schema, trace_name, **kw):
        calls.append({"trace": trace_name, "user": user})
        if trace_name == "advisory-comprehend":
            return {
                "summary": "Built a Redis cache in front of route estimates.",
                "role_alignment": "Matches a backend placement.",
                "depth_rating": 78,
            }
        if trace_name == "advisory-audit":
            return {"inconsistencies": ["Says 'over four months'; period is six weeks."]}
        if trace_name == "advisory-questions":
            return {"questions": ["How long did the placement actually run?"]}
        return None

    monkeypatch.setattr(llm, "complete_json", fake)
    monkeypatch.setattr(llm, "is_enabled", lambda: True)
    return calls


# --------------------------------------------------------------------------- #
# The chain
# --------------------------------------------------------------------------- #


def test_the_three_model_steps_run_in_order(model):
    state = G.run_review(report_text=REPORT, department="Backend", facts=FACTS)

    assert [c["trace"] for c in model] == [
        "advisory-comprehend",
        "advisory-audit",
        "advisory-questions",
    ]
    assert state["available"] is True
    assert state["depth_rating"] == 78
    assert state["inconsistencies"] == ["Says 'over four months'; period is six weeks."]
    assert state["questions"] == ["How long did the placement actually run?"]


def test_the_question_step_is_given_what_the_earlier_steps_found(model):
    """Otherwise it is three prompts in a trench coat, not a chain."""
    G.run_review(report_text=REPORT, department="Backend", facts=FACTS)

    question_prompt = model[-1]["user"]
    assert "Redis cache" in question_prompt
    assert "over four months" in question_prompt


def test_every_step_is_told_the_verified_record(model):
    """The facts are settled before the graph runs; a step that re-derives them
    from the prose would report the student's claims as though they were ours."""
    G.run_review(report_text=REPORT, department="Backend", facts=FACTS)

    for call in model:
        assert "Verified record" in call["user"]
        assert "30" in call["user"]


def test_the_report_is_fenced_as_untrusted_in_every_prompt(model):
    G.run_review(report_text=REPORT, department="Backend", facts=FACTS)

    for call in model:
        assert "<STUDENT_REPORT>" in call["user"]
        assert "</STUDENT_REPORT>" in call["user"]


def test_a_long_report_is_truncated_rather_than_sent_whole(model):
    G.run_review(report_text="x" * 40_000, department="Backend", facts=FACTS)

    body = model[0]["user"]
    assert "(truncated for length)" in body
    assert len(body) < 20_000


# --------------------------------------------------------------------------- #
# Degrading
# --------------------------------------------------------------------------- #


def test_no_model_configured_skips_every_step(monkeypatch):
    calls = []
    monkeypatch.setattr(llm, "is_enabled", lambda: False)
    monkeypatch.setattr(llm, "complete_json", lambda **kw: calls.append(kw))

    state = G.run_review(report_text=REPORT, department="Backend", facts=FACTS)

    assert state["available"] is False
    assert calls == [], "the model must not be called at all"


def test_a_failed_first_call_stops_the_chain(monkeypatch):
    """No point auditing prose nobody managed to read."""
    calls = []

    def fake(*, trace_name, **kw):
        calls.append(trace_name)
        return None

    monkeypatch.setattr(llm, "is_enabled", lambda: True)
    monkeypatch.setattr(llm, "complete_json", fake)

    state = G.run_review(report_text=REPORT, department="Backend", facts=FACTS)

    assert state["available"] is False
    assert calls == ["advisory-comprehend"]


def test_an_empty_audit_is_normal_and_questions_still_run(monkeypatch):
    def fake(*, trace_name, **kw):
        if trace_name == "advisory-comprehend":
            return {"summary": "s", "role_alignment": "r", "depth_rating": 50}
        if trace_name == "advisory-audit":
            return {"inconsistencies": []}
        return {"questions": ["Anything you would do differently?"]}

    monkeypatch.setattr(llm, "is_enabled", lambda: True)
    monkeypatch.setattr(llm, "complete_json", fake)

    state = G.run_review(report_text=REPORT, department="Backend", facts=FACTS)

    assert state["inconsistencies"] == []
    assert state["questions"] == ["Anything you would do differently?"]


def test_a_raising_model_does_not_raise_out_of_the_graph(monkeypatch):
    monkeypatch.setattr(llm, "is_enabled", lambda: True)
    monkeypatch.setattr(
        llm, "complete_json", lambda **kw: (_ for _ in ()).throw(RuntimeError("boom"))
    )

    state = G.run_review(report_text=REPORT, department="Backend", facts=FACTS)

    assert state["available"] is False
    assert "unavailable" in state["note"].lower()


def test_a_nonsense_depth_rating_is_dropped_not_propagated(monkeypatch):
    def fake(*, trace_name, **kw):
        if trace_name == "advisory-comprehend":
            return {"summary": "s", "role_alignment": "r", "depth_rating": "banana"}
        return {"inconsistencies": [], "questions": []}

    monkeypatch.setattr(llm, "is_enabled", lambda: True)
    monkeypatch.setattr(llm, "complete_json", fake)

    state = G.run_review(report_text=REPORT, department="Backend", facts=FACTS)

    assert state["depth_rating"] is None
    assert state["available"] is True


def test_an_overlong_list_is_capped(monkeypatch):
    def fake(*, trace_name, **kw):
        if trace_name == "advisory-comprehend":
            return {"summary": "s", "role_alignment": "r", "depth_rating": 50}
        if trace_name == "advisory-audit":
            return {"inconsistencies": [f"i{n}" for n in range(30)]}
        return {"questions": [f"q{n}" for n in range(30)]}

    monkeypatch.setattr(llm, "is_enabled", lambda: True)
    monkeypatch.setattr(llm, "complete_json", fake)

    state = G.run_review(report_text=REPORT, department="Backend", facts=FACTS)

    assert len(state["inconsistencies"]) <= 6
    assert len(state["questions"]) <= 4


# --------------------------------------------------------------------------- #
# The guarantee
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "verdict",
    [
        {"inconsistencies": ["The whole report is fabricated."], "questions": []},
        {"inconsistencies": [], "questions": ["Reject this immediately."]},
    ],
)
def test_nothing_the_model_says_changes_the_status(monkeypatch, verdict, packages):
    """A model convinced the report is fraudulent still cannot hold a package.

    Findings come from counting; this graph writes prose. If that ever stops
    being true, this test is where it breaks.
    """
    from app.main import app
    from app.routers.reports import get_report_service
    from app.services import report_repository
    from app.services.report_service import ReportService
    from app.services.report_similarity import SimilarityIndex
    from app.services.report_verification import ReportVerificationService

    def fake(*, trace_name, **kw):
        if trace_name == "advisory-comprehend":
            return {"summary": "Fabricated.", "role_alignment": "None.", "depth_rating": 0}
        return verdict

    monkeypatch.setattr(llm, "is_enabled", lambda: True)
    monkeypatch.setattr(llm, "complete_json", fake)

    index = SimilarityIndex()
    service = ReportService(
        verifier=ReportVerificationService(index=index),
        index=index,
        # Inline, so the reading has certainly happened by the time the
        # assertions run. In the deployment it happens on its own thread.
        background=lambda work: work(),
    )
    app.dependency_overrides[get_report_service] = lambda: service
    try:
        from tests.test_reports import submit

        body = submit(packages["clean"]).json()
    finally:
        app.dependency_overrides.clear()

    assert body["status"] == STATUS_APPROVED
    assert body["findings"] == []

    # The reading arrives after the response, on the stored row. What it says
    # is irrelevant; that it cannot move the status is the point.
    stored = report_repository.get_by_id(body["id"])
    assert stored is not None
    assert stored.advisory is not None
    assert stored.advisory.available is True
    assert stored.status == STATUS_APPROVED
    assert stored.findings == []


def test_the_reading_arrives_after_the_answer(monkeypatch, packages):
    """The response carries a verdict; the reading catches up with the row.

    Three model calls used to happen before the caller heard anything, which
    made a package's review as slow as the busiest minute at the provider —
    slow enough that a proxy could give up and hand n8n an error page instead
    of a decision that had already been made.
    """
    from app.main import app
    from app.routers.reports import get_report_service
    from app.services import report_repository
    from app.services.report_service import ReportService
    from app.services.report_similarity import SimilarityIndex
    from app.services.report_verification import ReportVerificationService

    def fake(*, trace_name, **kw):
        if trace_name == "advisory-comprehend":
            return {"summary": "Cache work.", "role_alignment": "Backend.", "depth_rating": 4}
        return {"inconsistencies": [], "questions": ["What did the cache replace?"]}

    monkeypatch.setattr(llm, "is_enabled", lambda: True)
    monkeypatch.setattr(llm, "complete_json", fake)

    deferred = []
    index = SimilarityIndex()
    service = ReportService(
        verifier=ReportVerificationService(index=index),
        index=index,
        background=deferred.append,
    )
    app.dependency_overrides[get_report_service] = lambda: service
    try:
        from tests.test_reports import submit

        body = submit(packages["clean"]).json()
    finally:
        app.dependency_overrides.clear()

    assert body["status"] == STATUS_APPROVED
    assert body["advisory"] is None
    assert report_repository.get_by_id(body["id"]).advisory is None

    assert len(deferred) == 1
    deferred[0]()

    stored = report_repository.get_by_id(body["id"])
    assert stored.advisory.available is True
    assert stored.advisory.questions_for_coordinator == ["What did the cache replace?"]
    assert stored.status == STATUS_APPROVED


def test_a_reading_that_raises_leaves_the_row_alone(monkeypatch, packages):
    """Nobody is waiting on this thread, so its failure has to be silent-but-logged.

    An exception escaping here would be raised into nothing: the response went
    out long ago. What must not happen is a half-written row.
    """
    from app.main import app
    from app.routers.reports import get_report_service
    from app.services import report_repository
    from app.services.report_service import ReportService
    from app.services.report_similarity import SimilarityIndex
    from app.services.report_verification import ReportVerificationService

    def explode(*, trace_name, **kw):
        # Only the reading fails. The student's email is drafted inside the
        # request and has its own fallback; this test is about the thread.
        if trace_name.startswith("advisory-"):
            raise RuntimeError("provider on fire")
        return {"subject": "Internship Documents", "body": "Received."}

    monkeypatch.setattr(llm, "is_enabled", lambda: True)
    monkeypatch.setattr(llm, "complete_json", explode)

    deferred = []
    index = SimilarityIndex()
    service = ReportService(
        verifier=ReportVerificationService(index=index),
        index=index,
        background=deferred.append,
    )
    app.dependency_overrides[get_report_service] = lambda: service
    try:
        from tests.test_reports import submit

        body = submit(packages["clean"]).json()
    finally:
        app.dependency_overrides.clear()

    deferred[0]()  # must not raise

    stored = report_repository.get_by_id(body["id"])
    assert stored.status == STATUS_APPROVED
    assert stored.findings == []
    assert stored.email_body
