import {
  AlertCircle,
  Brain,
  CheckCircle2,
  FileText,
  GraduationCap,
  Info,
  ShieldAlert,
} from "lucide-react";

import { reportAttachmentUrl } from "../services/reportsApi";
import {
  DOCUMENT_LABELS,
  REPORT_STATUS_SUMMARY,
  reportStatusLabel,
  severityLabel,
} from "../services/status";

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

export default function CompletionDetails({ selected, loading }) {
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

  return (
    <div className="col">
      {/* Keyed on the submission so the entrance replays on every selection:
          the panel reads as a new document rather than mutated text. */}
      <div className="colScroll detailEnter" key={selected.id}>
        <div className="detailHead" style={{ paddingLeft: 0, paddingRight: 0 }}>
          <div className="detailTop">
            <div className="avatar lg">{initials(selected.student_name || "?")}</div>
            <div style={{ minWidth: 0 }}>
              <h2 className="detailName">{selected.student_name || "Unnamed student"}</h2>
              <div className="detailSub">
                <span className="idChip">{selected.student_id || "no id"}</span>
                <span>{selected.intern_email}</span>
                <span className={`status ${selected.status}`}>
                  <span className="dot" />
                  {reportStatusLabel(selected.status)}
                </span>
              </div>
            </div>
          </div>

          <div className={`banner ${BANNER_TONE[selected.status] || ""}`}>
            <BannerIcon size={16} />
            <p>{REPORT_STATUS_SUMMARY[selected.status] || selected.report}</p>
          </div>
        </div>

        {/* The figures the certificate would assert. */}
        <div className="stats">
          <div className="stat">
            <div className="statLabel">Working days</div>
            <div className="statValue">
              {selected.counted_working_days}
              <small>days · {selected.total_hours}h</small>
            </div>
          </div>
          <div className="stat">
            <div className="statLabel">Employer score</div>
            <div className="statValue">
              {selected.evaluation_score ?? "—"}
              {selected.evaluation_score !== null && <small>/100</small>}
            </div>
          </div>
          <div className="stat">
            <div className="statLabel">Report length</div>
            <div className="statValue">
              {selected.report_word_count}
              <small>words</small>
            </div>
          </div>
          <div className="stat">
            <div className="statLabel">Peak similarity</div>
            <div className="statValue">
              {Math.round((selected.max_similarity || 0) * 100)}
              <small>%</small>
            </div>
          </div>
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
                    key={f.code}
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
                </a>
              ))}
            </div>

            <p className="sectionNote" style={{ marginTop: 10, marginBottom: 0 }}>
              The signed certificate carries the hash of these exact files, so it
              cannot be detached from what it attests to.
            </p>
          </section>
        )}
      </div>
    </div>
  );
}
