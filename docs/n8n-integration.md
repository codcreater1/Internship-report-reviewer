# n8n Integration Guide

Import [`../n8n/internship-report-review-workflow.json`](../n8n/internship-report-review-workflow.json).

```
Student email (subject "Internship Report", 3 PDFs attached)
        │
        ▼
Gmail Trigger            ← polls every minute
        │
        ▼
Get a message            ← downloads all three attachments
        │
        ▼
Review (FastAPI)         ← POST /reports/from-n8n  (multipart, 3 × files)
        │
        ├──────────────────────────────┐
        ▼                              ▼
Reply to Student          Waiting on a coordinator?   ← status approved/pending
                                       │
                                       ▼
                              Notify Coordinator
                                       │
                                     (stop)
```

## Setup

1. **Import** the workflow (Workflows → Import from File).

2. **Connect Gmail** on all four Gmail nodes — `Gmail Trigger`,
   `Get a message`, `Reply to Student`, `Notify Coordinator`. The imported
   credential is a placeholder and shows as a warning until you pick yours.

3. **Set the backend URL** in **Review (FastAPI)**: replace
   `https://REPLACE-WITH-YOUR-REVIEWER-URL` with wherever this service runs,
   keeping the `/reports/from-n8n` path.

4. **Set the coordinator address** in **Notify Coordinator**: replace
   `REPLACE_WITH_COORDINATOR_EMAIL`, and `REPLACE_WITH_DASHBOARD_URL` in the
   message body with the dashboard's address.

5. **(Optional) Secure the webhook.** If `REVIEW_API_SECRET_KEY` is set on the
   backend, add Authentication → Generic → Header Auth to the Review node, with
   name `Authorization` and value `Bearer <your key>`.

   The URL is baked into the workflow rather than read from `$env` because n8n
   blocks environment access in expressions by default — an expression-based
   URL silently resolves to nothing.

6. **Publish**, then send a test email with subject **`Internship Report`** and
   three PDFs attached. Generate them with:

   ```bash
   python testdocs/tool/completion_docs.py --scenario clean --out samples/clean
   ```

## How the attachments are sent

All three files go up under the **same field name**, `files`:

```
intern_email = {{ $json.from.value[0].address }}
files        = attachment_0
files        = attachment_1
files        = attachment_2
```

n8n names downloaded binaries `attachment_0`, `attachment_1`, … in whatever
order Gmail returns them. That order is not meaningful and the workflow does not
try to make it meaningful — the backend reads each document to decide which is
which.

**No text-extraction node.** The backend hashes the exact bytes it received onto
the certificate, and refuses scans that carry no extractable text. Extracting in
n8n would throw away both.

## Why there is one reply node

The backend returns `email_subject` and `email_body` already composed for
whatever the outcome was — a clarification request with a numbered list of
instructions, an acknowledgement, or a certificate delivery. The workflow sends
what it is given.

A Switch node with four branches would mean two places where the wording of a
request can drift out of sync with the reason for it. The text is generated from
the same `remedy` fields the checks produce, so it cannot say something the
checks did not find.

## Why `neverError` is set

A held or rejected package returns **HTTP 201 with the status in the body** — a
normal outcome, not a protocol error. `neverError` is set anyway so a genuine
4xx or 5xx also reaches the reply node instead of failing the execution
silently and leaving the student with no answer.

## Why it stops before signing

Signing is `POST /reports/by-id/{id}/sign`, it requires a named coordinator, and
it is deliberately not in this workflow. A node that called it automatically
whenever `status == "approved"` would remove the only human from the process,
and the institution would be issuing completion certificates on the strength of
a regex over a PDF.

The coordinator notification carries the verified figures, the open points and
the advisory reading — enough to decide, in the place where deciding happens.

## What to check on the first run

The one thing worth watching is the multipart body: n8n must send **three
separate parts all named `files`**. That is what the workflow is configured to
do and the endpoint has been verified against exactly that shape over the wire.
If the backend answers with an `ATTACHMENT_COUNT` finding saying it received one
file instead of three, open the Review node's output and confirm all three
`formBinaryData` rows are present and that `binaryMode` is `separate` in the
workflow settings.
