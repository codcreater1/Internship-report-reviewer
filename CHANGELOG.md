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

### Notes
- Extracted from the Agentic Internship Coordinator, where this was first built
  as a second phase. Kept as its own service so it can be deployed and reasoned
  about on its own; the API surface is stable enough to merge back if that ever
  makes sense.
