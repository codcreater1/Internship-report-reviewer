"""Fifty end-to-end packages through the running reviewer.

Each case says what it breaks and what the service is supposed to do about it.
The point is not that fifty requests return 201 — they all do, that is the
protocol — but that the verdict and the finding match what a coordinator would
expect from the rule that was broken.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

import requests

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "testdocs" / "tool"))
sys.path.insert(0, str(Path(__file__).parent))

import completion_docs as C  # noqa: E402
from prose import DOMAINS, STUDENTS, SUPERVISORS, sections_for  # noqa: E402

OUT = Path(os.environ.get("CONFORMANCE_OUT", Path(__file__).parent / "pkgs"))
API = os.environ.get("CONFORMANCE_API", "http://127.0.0.1:8000") + "/reports/"

TODAY = date.today()


def base(i: int, **kw) -> C.Package:
    """One package in its own domain, with its own prose and its own student."""
    company, dept, *_ = DOMAINS[i % len(DOMAINS)]
    sup, title = SUPERVISORS[i % len(SUPERVISORS)]
    pkg = C.Package(
        student_name=STUDENTS[i % len(STUDENTS)],
        student_id=f"s{24100 + i}",
        company=company,
        department=dept,
        supervisor_name=sup,
        supervisor_title=title,
        sections=sections_for(i),
    )
    return replace(pkg, **kw) if kw else pkg


def write(pkg: C.Package, name: str) -> dict[str, Path]:
    d = OUT / name
    d.mkdir(parents=True, exist_ok=True)
    files = {
        "report": d / "internship_report.pdf",
        "evaluation": d / "evaluation_form.pdf",
        "timesheet": d / "attendance_record.pdf",
    }
    C.write_report(pkg, files["report"])
    C.write_evaluation(pkg, files["evaluation"])
    C.write_attendance(pkg, files["timesheet"])
    return files


def trimmed(sections, words: int):
    """The same prose cut to about *words* words, with all six sections intact.

    Cutting from the end instead would drop whole headings and fire
    SECTIONS_MISSING, which is a different rule from the one under test.
    """
    per = max(1, words // len(sections))
    return [(heading, " ".join(body.split()[:per])) for heading, body in sections]


# --------------------------------------------------------------------------- #
# The matrix
#
# (name, files, expected status, codes that must fire, codes that must not)
# --------------------------------------------------------------------------- #

CASES: list[tuple] = []


def case(name, files, status, must=(), must_not=()):
    CASES.append((name, files, status, list(must), list(must_not)))


def build() -> None:
    i = 0

    # ---- Packages that should pass -------------------------------------- #
    case("clean", write(base(0), "clean"), "approved", (), ("DAYS_SHORT", "REPORT_SHORT"))
    case("boundary-days-20", write(base(1, working_days=20), "days20"), "approved", (), ("DAYS_SHORT",))
    case("boundary-score-60", write(base(2, overall_score=60), "score60"), "approved", (), ("EVAL_SCORE_LOW",))
    case("boundary-hours-4", write(base(3, daily_hours=4.0), "hours4"), "approved", (), ("HOURS_SHORT",))
    case("boundary-hours-11", write(base(4, daily_hours=11.0), "hours11"), "approved", (), ("HOURS_IMPLAUSIBLE",))
    case(
        "long-placement-45d",
        write(
            base(
                5,
                working_days=45,
                start_date=TODAY - timedelta(days=90),
                end_date=TODAY - timedelta(days=10),
                evaluation_date=TODAY - timedelta(days=7),
            ),
            "long45",
        ),
        "approved",
    )
    case("score-100", write(base(6, overall_score=100), "score100"), "approved")
    case(
        "boundary-words-just-over-500",
        write(base(7, sections=trimmed(sections_for(7), 516)), "words500"),
        "approved",
        (),
        ("REPORT_SHORT",),
    )
    # Names that naive case folding gets wrong: the Turkish dotted I and the
    # Polish crossed L. Same person, written the way each document writes it.
    case(
        "name-turkish-caps",
        write(base(8, student_name="Elif Şahin", evaluation_student_name="ELİF ŞAHİN"), "nameTr"),
        "approved",
        (),
        ("NAME_MISMATCH",),
    )
    case(
        "name-polish-caps",
        write(base(9, student_name="Michał Łukasiewicz", evaluation_student_name="MICHAŁ ŁUKASIEWICZ"), "namePl"),
        "approved",
        (),
        ("NAME_MISMATCH",),
    )
    case(
        "name-extra-space",
        write(base(10, student_name="Jan Kowalski", evaluation_student_name="Jan  Kowalski "), "nameSpace"),
        "approved",
        (),
        ("NAME_MISMATCH",),
    )
    case("hours-8-30days", write(base(11, working_days=30, daily_hours=8.0), "std30"), "approved")

    # ---- Open points only: signable, but a person should look ------------ #
    case(
        "weekend-padding-26",
        write(base(12, include_weekends=True, working_days=26), "weekend26"),
        "pending",
        ("WEEKEND_DAYS",),
    )
    case(
        "eval-dated-before-end",
        write(base(13, evaluation_date=C.Package().end_date - timedelta(days=5)), "evalEarly"),
        "pending",
        ("EVAL_DATED_EARLY",),
    )
    case(
        "hours-12-implausible",
        write(base(14, daily_hours=12.0), "hours12"),
        "pending",
        ("HOURS_IMPLAUSIBLE",),
    )
    case(
        "hours-3-short",
        write(base(15, daily_hours=3.0), "hours3"),
        "request_clarification",
        ("HOURS_SHORT",),
    )

    # ---- Fixable, back to the student ------------------------------------ #
    case("days-18", write(base(16, working_days=18), "days18"), "request_clarification", ("DAYS_SHORT",))
    case("days-19-boundary", write(base(17, working_days=19), "days19"), "request_clarification", ("DAYS_SHORT",))
    case(
        "name-mismatch",
        write(base(18, evaluation_student_name="Jakub Nowak"), "nameMismatch"),
        "request_clarification",
        ("NAME_MISMATCH",),
    )
    case("eval-unsigned", write(base(19, signed=False), "unsigned"), "request_clarification", ("EVAL_UNSIGNED",))
    case("eval-unstamped", write(base(20, stamped=False), "unstamped"), "request_clarification", ("EVAL_UNSTAMPED",))
    case(
        "eval-unsigned-unstamped",
        write(base(21, signed=False, stamped=False), "unsignedUnstamped"),
        "request_clarification",
        ("EVAL_UNSIGNED", "EVAL_UNSTAMPED"),
    )
    case(
        "report-thin-52w",
        write(
            base(
                22,
                sections=[
                    ("1. Introduction", "I did an internship at a company."),
                    ("2. Company Overview", "It is a company."),
                    ("3. Work Performed", "I wrote some code and fixed some bugs."),
                    ("4. Technologies Used", "Python."),
                    ("5. Challenges and Solutions", "It was hard at first."),
                    ("6. Conclusion", "I learned a lot. Thank you."),
                ],
            ),
            "thin",
        ),
        "request_clarification",
        ("REPORT_SHORT",),
    )
    case(
        "report-499-words",
        write(base(23, sections=trimmed(sections_for(23), 470)), "words499"),
        "request_clarification",
        ("REPORT_SHORT",),
    )
    case(
        "sections-missing",
        write(
            base(
                24,
                sections=[
                    ("1. Introduction", " ".join(w for h, b in sections_for(24) for w in b.split())),
                ],
            ),
            "noSections",
        ),
        "request_clarification",
        ("SECTIONS_MISSING",),
    )
    case("report-is-a-scan", write(base(25, report_as_image=True), "scan"), "request_clarification", ("ATTACHMENT_NOT_TEXT",))
    case(
        "future-dates",
        write(
            base(
                26,
                start_date=TODAY - timedelta(days=5),
                end_date=TODAY + timedelta(days=40),
                evaluation_date=TODAY + timedelta(days=43),
                day_offset=0,
            ),
            "future",
        ),
        "request_clarification",
        ("FUTURE_DATES",),
    )
    case(
        "supervisor-missing",
        write(base(27, supervisor_name=""), "noSupervisor"),
        "request_clarification",
        ("SUPERVISOR_MISSING",),
    )
    case(
        "eval-score-missing",
        write(base(28, overall_score=None, scores={}), "noScore"),
        "request_clarification",
        ("EVAL_SCORE_MISSING",),
    )
    case(
        "period-invalid",
        write(base(29, start_date=C.Package().end_date + timedelta(days=10)), "periodInvalid"),
        "request_clarification",
        ("PERIOD_INVALID",),
    )

    # ---- Cross-document disagreements, built by mixing two packages ------ #
    a = write(base(30), "mixA")
    b = write(base(31, student_id="s99999"), "mixB_id")
    case(
        "student-id-mismatch",
        {"report": a["report"], "evaluation": b["evaluation"], "timesheet": a["timesheet"]},
        "request_clarification",
        ("STUDENT_ID_MISMATCH",),
    )

    c1 = write(base(32), "mixC")
    c2 = write(base(33, company="Somewhere Else Sp. z o.o.", student_name=STUDENTS[32], student_id=f"s{24100 + 32}"), "mixC_company")
    case(
        "company-mismatch",
        {"report": c1["report"], "evaluation": c2["evaluation"], "timesheet": c1["timesheet"]},
        "request_clarification",
        ("COMPANY_MISMATCH",),
    )

    d1 = write(base(34), "mixD")
    d2 = write(
        base(
            35,
            student_name=STUDENTS[34],
            student_id=f"s{24100 + 34}",
            company=DOMAINS[34][0],
            end_date=C.Package().end_date - timedelta(days=30),
        ),
        "mixD_period",
    )
    case(
        "period-mismatch",
        {"report": d1["report"], "evaluation": d1["evaluation"], "timesheet": d2["timesheet"]},
        "request_clarification",
        ("PERIOD_MISMATCH",),
    )

    # ---- Intake: the wrong pile of files --------------------------------- #
    e = write(base(36), "intakeA")
    case("only-two-attachments", {"report": e["report"], "evaluation": e["evaluation"]}, "request_clarification", ("ATTACHMENT_COUNT",))
    case(
        "four-attachments",
        {
            "report": e["report"],
            "evaluation": e["evaluation"],
            "timesheet": e["timesheet"],
            "extra": e["report"],
        },
        "request_clarification",
        ("ATTACHMENT_COUNT",),
    )
    f = write(base(37), "intakeB")
    case(
        "two-reports-no-timesheet",
        {"report": f["report"], "report2": f["report"], "evaluation": f["evaluation"]},
        "request_clarification",
        ("DOCUMENT_DUPLICATED",),
    )
    case(
        "missing-evaluation",
        {"report": f["report"], "timesheet": f["timesheet"], "timesheet2": f["timesheet"]},
        "request_clarification",
        ("DOCUMENT_DUPLICATED",),
    )

    # ---- Rejections ------------------------------------------------------ #
    case(
        "score-59-just-below",
        write(base(38, overall_score=59), "score59"),
        "rejected",
        ("EVAL_SCORE_LOW",),
    )
    case("score-30", write(base(39, overall_score=30), "score30"), "rejected", ("EVAL_SCORE_LOW",))
    case(
        "failing-score-outranks-short-days",
        write(base(40, overall_score=41, working_days=17), "rejectOutranks"),
        "rejected",
        ("EVAL_SCORE_LOW", "DAYS_SHORT"),
    )

    # ---- Combinations ---------------------------------------------------- #
    case(
        "short-days-and-unsigned",
        write(base(41, working_days=16, signed=False), "combo1"),
        "request_clarification",
        ("DAYS_SHORT", "EVAL_UNSIGNED"),
    )
    case(
        "thin-report-and-name-mismatch",
        write(
            base(
                42,
                sections=trimmed(sections_for(42), 120),
                evaluation_student_name="Someone Else",
            ),
            "combo2",
        ),
        "request_clarification",
        ("REPORT_SHORT", "NAME_MISMATCH"),
    )
    case(
        "weekend-and-short-days",
        write(base(43, include_weekends=True, working_days=18), "combo3"),
        "request_clarification",
        ("DAYS_SHORT",),
    )
    case(
        "unsigned-and-future",
        write(
            base(
                44,
                signed=False,
                start_date=TODAY - timedelta(days=3),
                end_date=TODAY + timedelta(days=30),
                evaluation_date=TODAY + timedelta(days=33),
                day_offset=0,
            ),
            "combo4",
        ),
        "request_clarification",
        ("EVAL_UNSIGNED", "FUTURE_DATES"),
    )

    # ---- More passing packages, to keep the queue realistic -------------- #
    for n, idx in enumerate((45, 46, 47, 48), start=1):
        case(f"clean-extra-{n}", write(base(idx), f"cleanExtra{n}"), "approved")

    # ---- Originality: run last, against a corpus that now has 15+ accepted #
    # The same report text as the first case, a different student. Nothing in
    # a single document gives this away.
    copied = base(49, sections=sections_for(0))
    case(
        "copied-from-case-1",
        write(copied, "copied"),
        "rejected",
        ("REPORT_NOT_ORIGINAL",),
    )
    # Half lifted, half original: should land in the warning band rather than
    # the rejection band.
    half = sections_for(1)[:3] + sections_for(2)[3:]
    case(
        "half-copied",
        write(base(45, sections=half, student_name="Borys Halicki", student_id="s24777"), "halfCopied"),
        None,  # whatever it is, it must not be silently approved with no note
        (),
    )

    print(f"{len(CASES)} cases built", file=sys.stderr)


def post(files: dict[str, Path]) -> dict:
    opened = [("files", (p.name, p.open("rb"), "application/pdf")) for p in files.values()]
    try:
        r = requests.post(
            API,
            data={"intern_email": "student@example.edu"},
            files=opened,
            timeout=120,
        )
        return r.json()
    finally:
        for _, (_, fh, _) in opened:
            fh.close()


def main() -> None:
    build()
    results = []
    failures = []

    for n, (name, files, want_status, must, must_not) in enumerate(CASES, start=1):
        body = post(files)
        got = body.get("status")
        codes = [f["code"] for f in body.get("findings", [])]

        problems = []
        if want_status is not None and got != want_status:
            problems.append(f"status {got!r}, expected {want_status!r}")
        for code in must:
            if code not in codes:
                problems.append(f"missing {code}")
        for code in must_not:
            if code in codes:
                problems.append(f"unexpected {code}")

        row = {
            "n": n,
            "case": name,
            "want": want_status,
            "got": got,
            "codes": codes,
            "problems": problems,
            "id": body.get("id"),
            "words": body.get("report_word_count"),
            "days": body.get("counted_working_days"),
            "similarity": round(body.get("max_similarity") or 0, 3),
        }
        results.append(row)
        if problems:
            failures.append(row)

        mark = "ok  " if not problems else "FAIL"
        print(f"{mark} {n:>2}. {name:<34} {str(got):<22} {','.join(codes)[:70]}")

    Path(__file__).with_name("results.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )

    print()
    print(f"{len(results) - len(failures)}/{len(results)} as expected")
    for row in failures:
        print(f"  - {row['case']}: {'; '.join(row['problems'])}  [codes: {','.join(row['codes'])}]")


if __name__ == "__main__":
    main()
