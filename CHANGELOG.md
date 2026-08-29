# Changelog

All notable changes to the Internship Report Reviewer.

---

## [Unreleased]

### Added — initial release
- `POST /reports/` reviews an end-of-internship package: three PDFs and the
  address they arrived from. Attachments are classified by reading them, so
  filenames and order do not matter.
- Deterministic checks decide the outcome; the model reads the report and
  drafts the student email but runs after the status is fixed. The service
  decides identically with no API key, so an outage never holds a package.
- Only a failing employer score or a copied report reject. Everything else
  lands at `request_clarification` with a specific instruction, and the
  student's email is assembled from those instructions.
- Cross-submission originality check (TF-IDF, stdlib only) catches reports
  circulated between students, which no per-document check can see. The corpus
  is rebuilt from SQLite at startup.
- Certificates carry the SHA-256 of the three documents they attest to, so a
  certificate cannot be detached from what it certifies. Signing requires a
  named coordinator and is refused for rejected or clarification-held packages.
- React dashboard: queue grouped by who acts next, findings grouped by what
  they demand, and a signature panel that mirrors the API's refusals.
- n8n workflow: Gmail trigger → review → reply to the student → notify the
  coordinator. Stops before signing, deliberately.
- `testdocs/tool/completion_docs.py` generates the three documents across nine
  scenarios, failures included.
- 55 tests, hermetic and offline.

### Fixed
- `REVIEW_CORS_ORIGINS` crashed the service at import time unless it was valid
  JSON: pydantic-settings decodes list fields straight from the environment,
  before any validator runs, so a plain `https://dash.example.com` raised a
  SettingsError and the container crash-looped. Annotated with `NoDecode` so a
  JSON array, a comma-separated list and a single origin all work.

### Added
- Advisory reading is now a LangGraph workflow in three passes — comprehend,
  audit, question — instead of one call. The audit pass compares the report's
  prose against the verified record, which no deterministic check can do; its
  output reaches the coordinator as questions, never as findings.
- LangFuse tracing wired through, one trace per pass. Dormant without keys.

### Changed
- Dashboard redesigned: top bar instead of a navigation sidebar, three working
  columns, a bronze accent taken from the certificate itself, tabular figures,
  dark/light themes, and Inter bundled into the build rather than fetched from
  a CDN.
- Backend image no longer installs `libgl1`/`libglib2.0-0`. Reading the ELF
  headers of the PyMuPDF and Pillow wheels shows neither links against them —
  PyMuPDF needs only libc, libstdc++ and its own bundled libmupdf, and Pillow
  vendors all of its dependencies. `libgl1` was pulling in llvm19, mesa, libdrm
  and libvulkan for nothing.
- `pytest` and `httpx` moved to `requirements-dev.txt`; the production image
  installed a test runner it never runs.

### Notes
- Extracted from the Agentic Internship Coordinator, where this was first built
  as a second phase. Kept as its own service so it can be deployed and reasoned
  about on its own; the API surface is stable enough to merge back if that ever
  makes sense.
