import { useEffect, useRef, useState } from "react";
import { FileText, Loader2, UploadCloud, X } from "lucide-react";

import { submitReportPackage } from "../services/reportsApi";
import { REPORT_STATUS_SUMMARY, reportStatusLabel } from "../services/status";

/**
 * Submitting a package without going through a mailbox.
 *
 * The email route exists because that is how students actually send things.
 * It is not the only way a package arrives: a coordinator is handed three PDFs
 * on a memory stick, or a student's mail bounces, or somebody wants to see
 * what the checks say before telling a student to resend. All of that used to
 * mean emailing the documents to yourself and waiting a minute for the poll.
 *
 * The review is the same review — the same endpoint the workflow posts to —
 * so nothing decided here differs from what would have been decided by email.
 */
export default function UploadPanel({ onClose, onSubmitted }) {
  const [email, setEmail] = useState("");
  const [files, setFiles] = useState([]);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [outcome, setOutcome] = useState(null);

  const inputRef = useRef(null);

  useEffect(() => {
    function onKey(e) {
      if (e.key === "Escape" && !busy) onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose, busy]);

  function addFiles(incoming) {
    const pdfs = Array.from(incoming).filter(
      (f) => f.type === "application/pdf" || f.name.toLowerCase().endsWith(".pdf"),
    );
    setFiles((current) => {
      const seen = new Set(current.map((f) => `${f.name}:${f.size}`));
      return [...current, ...pdfs.filter((f) => !seen.has(`${f.name}:${f.size}`))];
    });
    setError("");
  }

  async function submit() {
    if (!email.trim()) {
      setError("Enter the student's address — the reply goes back to it.");
      return;
    }
    if (files.length === 0) {
      setError("Add the three PDFs first.");
      return;
    }

    setBusy(true);
    setError("");
    try {
      const result = await submitReportPackage({ internEmail: email.trim(), files });
      // The verdict is shown here rather than only in the queue: whoever just
      // uploaded is standing there waiting for an answer, and making them find
      // the row themselves would be a strange way to give them one.
      setOutcome(result);
      await onSubmitted(result.id);
    } catch (err) {
      setError(err.message || "The submission failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="sheetBackdrop" onClick={busy ? undefined : onClose} role="presentation">
      <div
        className="sheet upload"
        role="dialog"
        aria-modal="true"
        aria-label="Submit a package"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sheetHead">
          <h2>{outcome ? "Reviewed" : "Submit a package"}</h2>
          <button
            type="button"
            className="iconButton"
            onClick={onClose}
            aria-label="Close"
            disabled={busy}
          >
            <X size={15} />
          </button>
        </div>

        {outcome ? (
          <div className="uploadOutcome">
            <span className={`status ${outcome.status}`}>
              <span className="dot" />
              {reportStatusLabel(outcome.status)}
            </span>
            <p>{REPORT_STATUS_SUMMARY[outcome.status]}</p>

            {outcome.findings?.length > 0 && (
              <ul className="uploadFindings">
                {outcome.findings.map((f, i) => (
                  <li key={`${f.code}-${i}`}>
                    <code>{f.code}</code> {f.message}
                  </li>
                ))}
              </ul>
            )}

            <p className="sheetNote">
              It is open in the record beside this. The student was emailed
              nothing — this route reviews the package, and the wording it
              composed is on the record for you to send yourself.
            </p>

            <button type="button" className="btn primary" onClick={onClose}>
              Open the record
            </button>
          </div>
        ) : (
          <>
            <label className="field">
              <span className="fieldLabel">Student's email address</span>
              <input
                className="input"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="student@university.edu"
                disabled={busy}
              />
            </label>

            <div
              className={dragging ? "dropZone over" : "dropZone"}
              onDragOver={(e) => {
                e.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragging(false);
                addFiles(e.dataTransfer.files);
              }}
              onClick={() => inputRef.current?.click()}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
              }}
            >
              <UploadCloud size={20} />
              <strong>Drop the three PDFs here</strong>
              <span>the report, the employer evaluation and the attendance record</span>
              <input
                ref={inputRef}
                type="file"
                accept="application/pdf,.pdf"
                multiple
                hidden
                onChange={(e) => addFiles(e.target.files)}
              />
            </div>

            {files.length > 0 && (
              <ul className="fileList">
                {files.map((f) => (
                  <li key={`${f.name}:${f.size}`}>
                    <FileText size={14} />
                    <span className="fileName">{f.name}</span>
                    <span className="fileSize">{Math.round(f.size / 1024)} kB</span>
                    <button
                      type="button"
                      className="iconButton small"
                      aria-label={`Remove ${f.name}`}
                      disabled={busy}
                      onClick={() =>
                        setFiles((c) => c.filter((x) => !(x.name === f.name && x.size === f.size)))
                      }
                    >
                      <X size={13} />
                    </button>
                  </li>
                ))}
              </ul>
            )}

            {/* Said, not enforced. The service answers "you sent two files,
                not three" as a finding the student can act on, and refusing it
                here would hide that answer behind a form validation. */}
            {files.length > 0 && files.length !== 3 && (
              <p className="sheetNote warn">
                A package is three documents. {files.length} will be reviewed and
                come back asking for the rest.
              </p>
            )}

            <div className="actions">
              <button type="button" className="btn ghost" onClick={onClose} disabled={busy}>
                Cancel
              </button>
              <button type="button" className="btn primary" onClick={submit} disabled={busy}>
                {busy ? <Loader2 size={15} className="spinning" /> : <UploadCloud size={15} />}
                {busy ? "Reviewing…" : "Review the package"}
              </button>
            </div>

            {busy && (
              <p className="sheetNote">
                Reading three PDFs and running the checks. This takes a few
                seconds; the model that drafts the student's email can take a
                few more.
              </p>
            )}

            {error && (
              <p className="error" role="alert">
                {error}
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
