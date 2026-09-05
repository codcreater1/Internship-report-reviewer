import { Inbox, RefreshCw, SearchX, ServerCrash } from "lucide-react";

import { COMPLETION_TABS, tabFor } from "../services/completionTabs";
import { reportStatusLabel } from "../services/status";
import { absoluteTime, relativeTime } from "../services/time";
import { tintFor } from "../services/tint";

function initials(name = "") {
  return name.split(" ").filter(Boolean).map((x) => x[0]).join("").slice(0, 2).toUpperCase();
}

export default function CompletionList({
  loading,
  error,
  retry,
  submissions,
  selectedId,
  setSelectedId,
  tab,
  setTab,
  counts,
  query,
  elsewhere,
  openShortcuts,
}) {
  const active = tabFor(tab);
  const searching = Boolean(query.trim());

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
          <span>to move</span>
          <kbd>/</kbd>
          <span>to search</span>
          {/* The hint that says there are more hints. A shortcut nobody can
              discover is a shortcut nobody has. */}
          <button type="button" className="kbdMore" onClick={openShortcuts}>
            <kbd>?</kbd>
          </button>
        </p>
      </div>

      <div className="colScroll">
        {/* A failed reload is reported where the rows would have been. Showing
            the tab's usual empty state here would tell a coordinator their
            queue is clear when it is only unreachable. */}
        {error && (
          <div className="empty error" role="alert">
            <div className="emptyIcon danger">
              <ServerCrash size={22} />
            </div>
            <h3>Queue unavailable</h3>
            <p>{error}</p>
            <button type="button" className="btn ghost" onClick={retry}>
              <RefreshCw size={14} /> Try again
            </button>
          </div>
        )}

        {/* Shapes the size of the rows that are coming, so the list does not
            reflow when the data lands. */}
        {!error &&
          loading &&
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

        {!error && !loading && submissions.length === 0 && (
          <div className="empty">
            <div className="emptyIcon">
              {searching ? <SearchX size={22} /> : <Inbox size={22} />}
            </div>
            <h3>{searching ? "No match here" : active.empty.title}</h3>
            <p>
              {searching
                ? `Nothing in ${active.label.toLowerCase()} matches “${query.trim()}”.`
                : active.empty.body}
            </p>

            {/* The match exists, just not in the tab that happens to be open.
                Saying where — and going there in one click — is the whole
                reason a search that ignores tabs is worth having. */}
            {elsewhere && (
              <button
                type="button"
                className="btn ghost"
                onClick={() => setTab(elsewhere.key)}
              >
                {elsewhere.count} in {elsewhere.label}
              </button>
            )}
          </div>
        )}

        {submissions.map((s, i) => {
          // What a coordinator acts on: how many things the student must fix,
          // or how many points need a decision before signing.
          const badge = s.clarification_count || s.warning_count;
          const arrived = relativeTime(s.created_at);

          return (
            <button
              key={s.id}
              type="button"
              className={s.id === selectedId ? "row selected" : "row"}
              style={{ "--i": i }}
              onClick={() => setSelectedId(s.id)}
              aria-label={`${s.student_name || "Unnamed student"}, ${reportStatusLabel(
                s.status,
              )}${arrived ? `, received ${arrived}` : ""}`}
            >
              <div
                className="avatar"
                style={{ "--tint": tintFor(s.student_name || "?") }}
              >
                {initials(s.student_name || "?")}
              </div>

              <div className="rowMain">
                <div className="rowName">{s.student_name || "Unnamed student"}</div>
                <div className="rowSub">{s.company || "No host organisation stated"}</div>
                {arrived && (
                  <div className="rowTime" title={absoluteTime(s.created_at)}>
                    {arrived}
                  </div>
                )}
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
