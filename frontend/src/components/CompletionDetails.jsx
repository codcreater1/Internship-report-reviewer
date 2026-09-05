import {
  AlertCircle,
  Brain,
  CheckCircle2,
  Clock3,
  FileText,
  GraduationCap,
  Info,
  Mail,
  ShieldAlert,
} from "lucide-react";

import { reportAttachmentUrl } from "../services/reportsApi";
import {
  DOCUMENT_LABELS,
  REPORT_STATUS_SUMMARY,
  reportStatusLabel,
  severityLabel,
} from "../services/status";
import { absoluteTime, relativeTime } from "../services/time";
import { meterFor } from "../services/thresholds";
import { tintFor } from "../services/tint";
import AuditTrail from "./AuditTrail";
import CopyButton from "./CopyButton";

/**
 * One figure, and how close it came to the line it is measured against.
 *
 * The four numbers were readable before and meant nothing on their own: 30
 * days is fine and 18 is not, and only somebody who has memorised the rules
 * could tell which they were looking at. The bar carries that, the caption
 * names the rule in words, and the colour follows the rule rather than
 * decorating it.
 */
function Stat({ label, value, unit, kind, raw, rules }) {
  const meter = meterFor(kind, raw, rules);

  return (
    <div className="stat">
      <div className="statLabel">{label}</div>
      <div className="statValue">
        {value}
        {unit && <small>{unit}</small>}
      </div>

      {meter && (
        <div className="statMeter">
          <div className={`meter ${meter.tone}`}>
            <span
              className="meterFill"
              style={{ width: `${Math.round(meter.ratio * 100)}%` }}
            />
            {meter.mark !== undefined && (
              <span
                className="meterMark"
                style={{ left: `${Math.round(meter.mark * 100)}%` }}
              />
            )}
          </div>
          <span className="meterCaption">{meter.caption}</span>
        </div>
      )}
    </div>
  );
}

function initials(name = "") {
  return name.split(" ").filter(Boolean).map((x) => x[0]).join("").slice(0, 2).toUpperCase();
}

// Findings are grouped by what they demand rather than listed flat. Working a
// queue, the question is never "what is wrong" — it is "whose move is it".
const GROUPS = [
  {
    severity: "reject",
    title: "Cannot be approved",
    icon: ShieldAlert,
    note: "Resending will not clear these. They need a conversation with the student.",
  },
  {
    severity: "clarify",
    title: "Waiting on the student",
    icon: AlertCircle,
    note: "The student was emailed exactly these points and can resend once fixed.",
  },
  {
    severity: "warning",
    title: "Open points for you",
    icon: Info,
    note: "None of these block a signature, but each wants a decision before you give one.",
  },
  { severity: "info", title: "Notes", icon: Info, note: null },
];

const BANNER_TONE = {
  approved: "ok",
  signed: "accent",
  pending: "warn",
  request_clarification: "warn",
  rejected: "danger",
};

const BANNER_ICON = {
  approved: CheckCircle2,
  signed: CheckCircle2,
  pending: Info,
  request_clarification: AlertCircle,
  rejected: ShieldAlert,
};

export default function CompletionDetails({ selected, loading, rules }) {
  if (loading && !selected) {
    return (
      <div className="col">
        <div className="empty">
          <p>Loading submission…</p>
        </div>
      </div>
    );
  }

  if (!selected) {
    return (
      <div className="col">
        <div className="empty">
          <div className="emptyIcon">
            <GraduationCap size={22} />
          </div>
          <h3>Select a submission</h3>
          <p>The internship record opens here.</p>
        </div>
      </div>
    );
  }

  const findings = selected.findings || [];
  const advisory = selected.advisory;
  const BannerIcon = BANNER_ICON[selected.status] || Info;
  const arrived = relativeTime(selected.created_at);
  const emailBody = selected.email_body || "";

  return (
    <div className="col">
      {/* Switching rows keeps the previous record on screen until the next one
          arrives, which is right — a blank panel between two clicks is worse
          than a stale one — but it has to say that it is fetching, or a slow
          connection looks like a click that did not register. */}
      {loading && <div className="colLoading" aria-hidden="true" />}

      {/* Keyed on the submission so the entrance replays on every selection:
          the panel reads as a new document rather than mutated text. */}
      <div className="colScroll detailEnter" key={selected.id}>
        <div className="detailHead" style={{ paddingLeft: 0, paddingRight: 0 }}>
          <div className="detailTop">
            <div
              className="avatar lg"
              style={{ "--tint": tintFor(selected.student_name || "?") }}
            >
              {initials(selected.student_name || "?")}
            </div>
            <div style={{ minWidth: 0 }}>
              <h2 className="detailName">{selected.student_name || "Unnamed student"}</h2>
              <div className="detailSub">
                <span className="idChip">{selected.student_id || "no id"}</span>
                {/* The address the package arrived from, and the one a reply
                    goes back to. Making it a mailto is the difference between
                    reading it and using it. */}
                <a className="mailLink" href={`mailto:${selected.intern_email}`}>
                  <Mail size={12} />
                  {selected.intern_email}
                </a>
                <span className={`status ${selected.status}`}>
                  <span className="dot" />
                  {reportStatusLabel(selected.status)}
                </span>
              </div>
              {arrived && (
                <div className="detailStamp" title={absoluteTime(selected.created_at)}>
                  <Clock3 size={12} />
                  Received {arrived}
                  {selected.signed_at && (
                    <>
                      <span className="stampSep">·</span>
                      Signed {relativeTime(selected.signed_at)}
                      {selected.signed_by ? ` by ${selected.signed_by}` : ""}
                    </>
                  )}
                </div>
              )}
            </div>
          </div>

          <div className={`banner ${BANNER_TONE[selected.status] || ""}`}>
            <BannerIcon size={16} />
            <p>{REPORT_STATUS_SUMMARY[selected.status] || selected.report}</p>
          </div>
        </div>

        {/* The figures the certificate would assert. */}
        <div className="stats">
          <Stat
            label="Working days"
            value={selected.counted_working_days}
            unit={`days · ${selected.total_hours}h`}
            kind="days"
            raw={selected.counted_working_days}
            rules={rules}
          />
          <Stat
            label="Employer score"
            value={selected.evaluation_score ?? "—"}
            unit={selected.evaluation_score !== null ? "/100" : ""}
            kind="score"
            raw={selected.evaluation_score}
            rules={rules}
          />
          <Stat
            label="Report length"
            value={selected.report_word_count}
            unit="words"
            kind="words"
            raw={selected.report_word_count}
            rules={rules}
          />
          <Stat
            label="Peak similarity"
            value={Math.round((selected.max_similarity || 0) * 100)}
            unit="%"
            kind="similarity"
            raw={selected.max_similarity || 0}
            rules={rules}
          />
        </div>

        <div className="metaGrid">
          <div className="meta">
            <div className="metaLabel">Host organisation</div>
            <div className="metaValue">{selected.company || "—"}</div>
          </div>
          <div className="meta">
            <div className="metaLabel">Internship period</div>
            <div className="metaValue tnum">
              {selected.start_date || "—"} → {selected.end_date || "—"}
            </div>
          </div>
        </div>

        {GROUPS.map((group) => {
          const items = findings.filter((f) => f.severity === group.severity);
          if (items.length === 0) return null;
          const Icon = group.icon;

          return (
            <section key={group.severity} className="section">
              <div className="sectionHead">
                <Icon size={14} />
                <h3>{group.title}</h3>
                <span className="sectionCount">{items.length}</span>
              </div>
              {group.note && <p className="sectionNote">{group.note}</p>}

              <div className="findings">
                {items.map((f, i) => (
                  <article
                    key={`${f.code}-${i}`}
                    className={`finding ${f.severity}`}
                    style={{ "--i": i }}
                  >
                    <div className="findingTop">
                      <span className="findingCode">{f.code}</span>
                      <span className={`sevChip ${f.severity}`}>
                        {severityLabel(f.severity)}
                      </span>
                    </div>
                    <p className="findingMsg">{f.message}</p>
                    {f.remedy && (
                      <p className="remedy">
                        <strong>Student was told:</strong> {f.remedy}
                      </p>
                    )}
                  </article>
                ))}
              </div>
            </section>
          );
        })}

        {findings.length === 0 && (
          <section className="section">
            <div className="sectionHead">
              <CheckCircle2 size={14} />
              <h3>Findings</h3>
            </div>
            <p className="sectionNote">
              Every check passed. Nothing was raised against this submission.
            </p>
          </section>
        )}

        {/* The message the student actually received. A coordinator ringing a
            student about their submission is at a disadvantage if they cannot
            see what the service already told them — and the wording is worth
            checking, since it is assembled from the findings above. */}
        {emailBody && (
          <section className="section">
            <div className="sectionHead">
              <Mail size={14} />
              <h3>Sent to the student</h3>
              <CopyButton value={emailBody} label="Copy the email text" />
            </div>

            <div className="emailCard">
              {selected.email_subject && (
                <p className="emailSubject">{selected.email_subject}</p>
              )}
              <pre className="emailBody">{emailBody}</pre>
            </div>
          </section>
        )}

        {advisory && (
          <section className="section">
            <div className="sectionHead">
              <Brain size={14} />
              <h3>Advisory reading</h3>
            </div>

            <div className="advisory">
              {advisory.available ? (
                <>
                  <p>{advisory.summary}</p>

                  {advisory.role_alignment && (
                    <p className="advisoryLine">
                      <strong>Role alignment</strong> — {advisory.role_alignment}
                    </p>
                  )}

                  {advisory.depth_rating !== null &&
                    advisory.depth_rating !== undefined && (
                      <p className="advisoryLine">
                        <strong>Technical depth</strong> —{" "}
                        <span className="tnum">{advisory.depth_rating}</span>/100
                      </p>
                    )}

                  {/* Things the prose claims that the verified record does not
                      support. Deliberately styled no louder than the rest: a
                      model noticing something is a reason to ask, not a
                      finding, and the layout should not suggest otherwise. */}
                  {advisory.inconsistencies?.length > 0 && (
                    <>
                      <p className="advisoryLine">
                        <strong>Does not match the record</strong>
                      </p>
                      <ul className="advisoryQuestions">
                        {advisory.inconsistencies.map((i) => (
                          <li key={i}>{i}</li>
                        ))}
                      </ul>
                    </>
                  )}

                  {advisory.questions_for_coordinator?.length > 0 && (
                    <>
                      <p className="advisoryLine">
                        <strong>Worth asking</strong>
                      </p>
                      <ul className="advisoryQuestions">
                        {advisory.questions_for_coordinator.map((q) => (
                          <li key={q}>{q}</li>
                        ))}
                      </ul>
                    </>
                  )}

                  <p className="advisoryNote">
                    Read by a model after the decision was already made — in
                    three passes: what the report describes, whether it matches
                    the verified record, and what is worth asking. None of it
                    affected the status above, and nothing here can.
                  </p>
                </>
              ) : (
                <p className="advisoryNote" style={{ marginTop: 0, borderTop: "none", paddingTop: 0 }}>
                  {advisory.summary}
                </p>
              )}
            </div>
          </section>
        )}

        {selected.documents?.length > 0 && (
          <section className="section">
            <div className="sectionHead">
              <FileText size={14} />
              <h3>Submitted documents</h3>
            </div>

            <div className="docs">
              {selected.documents.map((doc) => (
                <a
                  key={doc.sha256}
                  className="doc"
                  href={reportAttachmentUrl(selected.id, doc.role)}
                  target="_blank"
                  rel="noreferrer"
                >
                  <div className="docIcon">
                    <FileText size={15} />
                  </div>
                  <div className="docMain">
                    <div className="docRole">
                      {DOCUMENT_LABELS[doc.role] || doc.role}
                    </div>
                    <div className="docName">
                      {doc.filename} · {doc.page_count} pp
                    </div>
                  </div>
                  <code className="docHash" title={doc.sha256}>
                    {doc.sha256.slice(0, 10)}…
                  </code>
                  <CopyButton value={doc.sha256} label="Copy this document's hash" />
                </a>
              ))}
            </div>

            {/* The one hash that ends up printed on the certificate. Checking a
                certificate against its documents means rehashing all three and
                comparing this value, so it has to be here to copy. */}
            {selected.package_sha256 && (
              <div className="packageHash">
                <span className="packageHashLabel">Package hash</span>
                <code title={selected.package_sha256}>
                  {selected.package_sha256.slice(0, 24)}…
                </code>
                <CopyButton value={selected.package_sha256} label="Copy the package hash" />
              </div>
            )}

            <p className="sectionNote" style={{ marginTop: 10, marginBottom: 0 }}>
              The signed certificate carries the hash of these exact files, so it
              cannot be detached from what it attests to.
            </p>
          </section>
        )}

        <AuditTrail submissionId={selected.id} key={selected.id} />
      </div>
    </div>
  );
}
