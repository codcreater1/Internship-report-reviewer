# Changelog

All notable changes to the Internship Report Reviewer.

---

## [Unreleased]

### Fixed — dashboard
- The layout broke below roughly 780px: the top bar laid brand, search and
  actions out in one unwrapping row, so a phone got a page that scrolled
  sideways with the search box off the edge. The bar wraps, the tab strip
  scrolls, and the queue takes a share of the viewport instead of a fixed slab.
- Search was scoped to the open tab while the tab counts ignored it, so a
  coordinator could search a student's name, see "no certificates yet", and
  read the strip above it claiming there was one. Search now runs across the
  queue, the counts follow it, and a match in another tab is offered as a
  button rather than left to be guessed at.
- A failed reload emptied the list and left the tab's ordinary empty state on
  screen — a service that is down and a queue that is clear looked identical.
  The queue now says it could not be reached, keeps the rows it already had,
  and offers a retry.
- Signing dropped the coordinator onto an unrelated student with no
  confirmation, and tried to open the certificate with a `window.open()` that
  browsers block because it happens after an await. Signing now follows the
  package into *Signed* and settles into the issued card, download link and
  all.
- The signature pad measured itself once. Resizing the window left strokes
  landing somewhere other than the cursor; it now re-fits and says so by
  clearing.

### Added — dashboard
- Arrival times on every row and in the record, relative in the list and exact
  on hover.
- The email the student was actually sent, with its subject, in the record.
  The backend has always returned it and the dashboard never showed it, which
  left a coordinator ringing a student unable to see what the service had
  already told them.
- Copy buttons on each document hash and on the package hash printed on the
  certificate, with a fallback for the plain-HTTP origins where
  `navigator.clipboard` does not exist.
- `/` focuses the search, `Esc` clears it from anywhere, and the student's
  address is a mailto link.

### Changed
- The advisory reading now runs after the response has been sent, on its own
  thread, and is attached to the stored submission when it finishes. Three
  model calls inside the request made a review as slow as the busiest minute
  at the provider; a package could take longer than the proxy would wait, and
  n8n received a gateway error page in place of a verdict that had already
  been decided and stored. A request now carries at most one model call.
- The model client retries a provider that says it is overloaded (429/503),
  which Gemini answers with under load. Only the advisory passes use it: they
  run after the response, so waiting out a busy minute costs nobody anything.
  The student's email is drafted on a single attempt - measured against the
  deployment, this provider's failures are mostly calls that hang until the
  deadline rather than fast 503s, so a second attempt rarely produced a draft
  and reliably pushed the request towards the proxy's 30s patience.

### Fixed
- One review froze the whole service. The intake routes were `async def` but
  called the pipeline synchronously, so PDF parsing and up to four model calls
  ran on the event loop; `/health` stopped answering for the duration, and a
  package that took longer than the proxy's read timeout came back to n8n as a
  Cloudflare 524. Both routes now hand the review to a worker thread.
- The model client was built with the SDK's defaults — a ten-minute timeout and
  two retries — so a single unresponsive call could hold a request open far
  past any gateway's patience. It now carries `REVIEW_LLM_TIMEOUT_SECONDS`
  (20s) and no retries: the advisory is optional by design, and a package must
  never wait on it.

### Added
- `Did the review answer?` in the n8n workflow. `neverError` lets a proxy's
  error page through as if it were a result — a 524 is JSON with no
  `intern_email`, and the Gmail node then fails on an address that resolved to
  nothing. Every real response carries a `status`; the gate tests for it and
  stops when it is absent.

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

### Fixed
- The advisory reading came back empty against Gemini. The provider rejected
  `response_format: json_object`, and the client swallowed that as a generic
  failure indistinguishable from a bad key. It now retries once without the
  parameter — the prompt already demands one JSON object and the response is
  parsed either way — and logs the exception type and message instead of a
  bare traceback line. Auth and network failures are not retried.

### Fixed
- Default model was `gemini-2.0-flash`, which the provider has retired. Every
  advisory reading came back empty. Updated to the successor its own 404 names.

### Fixed
- The advisory summary came back prefixed with a fragment of its own prompt
  ("captured within two to three sentences: The student optimised…"). The
  comprehend step now describes each field separately and says each must
  contain only its value.

### Added
- Keyboard navigation: ↑/↓ walk the queue, ignored while typing.
- Skeleton rows while the queue loads, sized like the rows that follow.
- Motion pass — staggered entrances, a replayed detail transition, a grain
  layer that stops large dark panels banding, and a certificate card that
  tilts into place and stamps its seal.

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
