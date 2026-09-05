# Conformance run

Fifty packages, generated and posted through the running service, each one
saying what it breaks and what the verdict should therefore be.

The unit suite builds field objects and asserts a finding. This does the other
half: real PDFs, real text extraction, real HTTP, and fifty verdicts compared
against what a coordinator would expect from the rule that was broken. It is
the layer that catches a check which never fires because the parser handed it a
value that looked filled in.

It found two of those on its first run — a blank field adopting the line below
it, and `Overall Score: None / 100` read as a perfect hundred — both of which
now have unit tests of their own in `backend/tests/test_reports.py`.

## Running it

Start the service against a **throwaway database**. The run submits fifty
packages and one of them is deliberately a copy of another, which only works
against a corpus that starts empty:

```bash
REVIEW_DB_PATH=/tmp/conformance.db REVIEW_STORAGE_ROOT=/tmp/conformance \
LLM_API_KEY= uvicorn app.main:app --port 8000
```

Then, from this directory:

```bash
python run.py
```

`CONFORMANCE_API` points it somewhere other than `http://127.0.0.1:8000`.
Every case prints `ok` or `FAIL`, the failures are summarised at the end, and
the full result of each submission lands in `results.json`.

## What is in the fifty

| Group | Cases | What they establish |
|---|---|---|
| Passing | 12 | Boundaries pass: exactly 20 days, exactly 60/100, 4h and 11h days, a report just over 500 words, and names that naive case folding breaks (`ELİF ŞAHİN`, `MICHAŁ ŁUKASIEWICZ`) |
| Open points | 3 | Weekend padding, an evaluation dated before the end, implausible hours — signable, but a person should look |
| Back to the student | 28 | Every fixable omission, each asserted with its own finding code, plus four combinations |
| Rejections | 3 | A failing score at the boundary and below, and a rejection outranking a clarification |
| Originality | 2 | A report lifted whole from an accepted one, and a half-lifted one |

## Why the prose is generated the way it is

Fifty reports that share their sentence frames are similar, and the service is
right to say so: the first version of this harness swapped only the nouns and
was scored at 0.76 against its own siblings, tripping the elevated-similarity
warning on packages that were supposed to be testing something else.

So each package gets its own domain vocabulary and one of four unrelated
phrasings per section, and `pick.py` chooses the combination for each package
by measuring it against the ones already chosen. The result sits at 0.33 worst
pairwise — comfortably below the 0.60 warning line, which is what lets the
originality cases mean what they say. `combos.json` holds the chosen
combinations so a run is reproducible; regenerate it with `python pick.py`.
