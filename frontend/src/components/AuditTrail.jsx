import { useEffect, useState } from "react";
import { Brain, FileCheck2, History, PenLine } from "lucide-react";

import { getReportAudit } from "../services/reportsApi";
import { absoluteTime, relativeTime } from "../services/time";

const SHAPE = {
  received: {
    icon: FileCheck2,
    title: (d) => `Package received — ${String(d.status || "").replace(/_/g, " ")}`,
    line: (d) =>
      d.findings?.length
        ? `${d.documents} documents, ${d.findings.length} finding${
            d.findings.length === 1 ? "" : "s"
          }: ${d.findings.join(", ")}`
        : `${d.documents} documents, every check passed`,
  },
  advisory: {
    icon: Brain,
    title: () => "Advisory reading attached",
    line: (d) =>
      d.available
        ? `${d.questions} question${d.questions === 1 ? "" : "s"} for the coordinator`
        : "The model was unavailable; the verdict was unaffected",
  },
  signed: {
    icon: PenLine,
    title: (d) => `Signed by ${d.coordinator}`,
    line: (d) => {
      const parts = [];
      if (d.acknowledged?.length) {
        parts.push(`accepted ${d.acknowledged.join(", ")}`);
      }
      if (d.note) parts.push(`note: ${d.note}`);
      return parts.join(" · ") || "No open points to acknowledge";
    },
  },
};

/**
 * What happened to this package, in order.
 *
 * The submission row only carries its current state — signing rewrites it, so
 * the shape it was signed in is gone the moment the signature lands. A
 * certificate is an institutional claim about a real person, and the question
 * that eventually gets asked is not "is this signed" but "who signed it, when,
 * and what did they know at the time".
 */
export default function AuditTrail({ submissionId }) {
  const [events, setEvents] = useState([]);

  useEffect(() => {
    // No reset here: the parent keys this on the submission, so a different
    // package gets a fresh component rather than one holding another
    // student's history for a moment.
    let cancelled = false;
    getReportAudit(submissionId)
      .then((rows) => {
        if (!cancelled) setEvents(Array.isArray(rows) ? rows : []);
      })
      // An older deployment has no such route. The record is worth reading
      // without its history; the history is not worth an error banner.
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [submissionId]);

  if (events.length === 0) return null;

  return (
    <section className="section">
      <div className="sectionHead">
        <History size={14} />
        <h3>History</h3>
        <span className="sectionCount">{events.length}</span>
      </div>

      <ol className="timeline">
        {events.map((event, i) => {
          const shape = SHAPE[event.kind];
          const Icon = shape?.icon || FileCheck2;

          return (
            <li key={`${event.at}-${i}`} className="timelineItem">
              <span className="timelineMark">
                <Icon size={12} />
              </span>
              <div className="timelineBody">
                <div className="timelineTop">
                  <strong>{shape ? shape.title(event.detail || {}) : event.kind}</strong>
                  <span className="timelineWhen" title={absoluteTime(event.at)}>
                    {relativeTime(event.at)}
                  </span>
                </div>
                {shape && <p>{shape.line(event.detail || {})}</p>}
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
