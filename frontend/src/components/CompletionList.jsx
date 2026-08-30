import { Inbox } from "lucide-react";

import { COMPLETION_TABS, tabFor } from "../services/completionTabs";
import { reportStatusLabel } from "../services/status";

function initials(name = "") {
  return name.split(" ").filter(Boolean).map((x) => x[0]).join("").slice(0, 2).toUpperCase();
}

export default function CompletionList({
  loading,
  submissions,
  selectedId,
  setSelectedId,
  tab,
  setTab,
  counts,
}) {
  const active = tabFor(tab);

  return (
    <div className="col queue">
      <div className="colHead">
        <p className="colTitle">Queue</p>

        <div className="segmented" role="tablist">
          {COMPLETION_TABS.map((t) => (
            <button
              key={t.key}
              type="button"
              role="tab"
              aria-selected={tab === t.key}
              className={tab === t.key ? "segment on" : "segment"}
              onClick={() => setTab(t.key)}
            >
              {t.label}
              <span className="segmentCount">{counts[t.key] ?? 0}</span>
            </button>
          ))}
        </div>

        {/* A list is worked with the hands on the keyboard; saying so costs
            one line and is the difference between a tool and a page. */}
        <p className="kbdHint">
          <kbd>↑</kbd>
          <kbd>↓</kbd>
          <span>to move through the queue</span>
        </p>
      </div>

      <div className="colScroll">
        {/* Shapes the size of the rows that are coming, so the list does not
            reflow when the data lands. */}
        {loading &&
          submissions.length === 0 &&
          [0, 1, 2, 3].map((i) => (
            <div className="skeleton" key={i} style={{ "--i": i }}>
              <div className="shimmer avatar" />
              <div className="skeletonLines">
                <div className="shimmer" />
                <div className="shimmer" />
              </div>
            </div>
          ))}

        {!loading && submissions.length === 0 && (
          <div className="empty">
            <div className="emptyIcon">
              <Inbox size={22} />
            </div>
            <h3>{active.empty.title}</h3>
            <p>{active.empty.body}</p>
          </div>
        )}

        {submissions.map((s, i) => {
          // What a coordinator acts on: how many things the student must fix,
          // or how many points need a decision before signing.
          const badge = s.clarification_count || s.warning_count;

          return (
            <button
              key={s.id}
              type="button"
              className={s.id === selectedId ? "row selected" : "row"}
              style={{ "--i": i }}
              onClick={() => setSelectedId(s.id)}
            >
              <div className="avatar">{initials(s.student_name || "?")}</div>

              <div className="rowMain">
                <div className="rowName">{s.student_name || "Unnamed student"}</div>
                <div className="rowSub">{s.company || "No host organisation stated"}</div>
              </div>

              <div className="rowSide">
                <span className={`status ${s.status}`}>
                  <span className="dot" />
                  {reportStatusLabel(s.status)}
                </span>
                <span className="rowFigure">
                  {badge > 0 && <span className="countChip">{badge}</span>}
                  {badge === 0 && `${s.counted_working_days} days`}
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
