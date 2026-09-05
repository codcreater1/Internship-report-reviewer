import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import "./App.css";

import { getReportSubmission, getReportSubmissions } from "./services/reportsApi";
import { COMPLETION_TABS, countsByTab, tabFor } from "./services/completionTabs";
import TopBar from "./components/TopBar";
import CompletionList from "./components/CompletionList";
import CompletionDetails from "./components/CompletionDetails";
import CertificatePanel from "./components/CertificatePanel";
import ShortcutsSheet from "./components/ShortcutsSheet";

// Matches the n8n Gmail poll interval — refreshing faster only adds load.
const REFRESH_MS = 60000;

const THEME_KEY = "irr.theme";

function initialTheme() {
  const stored = localStorage.getItem(THEME_KEY);
  if (stored === "dark" || stored === "light") return stored;
  return window.matchMedia?.("(prefers-color-scheme: light)").matches
    ? "light"
    : "dark";
}

function matchesQuery(submission, q) {
  if (!q) return true;
  const text = `${submission.student_name ?? ""} ${submission.student_id ?? ""} ${
    submission.company ?? ""
  } ${submission.intern_email ?? ""} ${submission.status}`.toLowerCase();
  return text.includes(q);
}

export default function App() {
  const [theme, setTheme] = useState(initialTheme);
  const [query, setQuery] = useState("");
  const [submissions, setSubmissions] = useState([]);
  const [tab, setTab] = useState("toSign");
  const [selectedId, setSelectedId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [loadError, setLoadError] = useState("");
  const [lastLoadedAt, setLastLoadedAt] = useState(null);
  const [showShortcuts, setShowShortcuts] = useState(false);

  const searchRef = useRef(null);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getReportSubmissions();
      setSubmissions(Array.isArray(data) ? data : []);
      setLoadError("");
      setLastLoadedAt(Date.now());
    } catch (err) {
      console.error(err);
      // Without this the queue empties and the page says "nothing waiting on
      // you" — a service that is down and a queue that is clear must never
      // look the same to somebody whose job is to work through it.
      setLoadError(
        "Could not reach the reviewer service. The queue below may be out of date.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, REFRESH_MS);
    return () => clearInterval(interval);
  }, [load]);

  // Search runs across the whole queue, not just the open tab. A coordinator
  // typing a student's name is asking "where is this person", and answering
  // "not in the tab you happen to have open" is not an answer.
  const matching = useMemo(() => {
    const q = query.trim().toLowerCase();
    return submissions.filter((s) => matchesQuery(s, q));
  }, [submissions, query]);

  // Counts follow the search too, so the tab strip never claims a number the
  // list underneath it does not show.
  const counts = useMemo(() => countsByTab(matching), [matching]);
  const totalCounts = useMemo(() => countsByTab(submissions), [submissions]);

  const filtered = useMemo(
    () => matching.filter(tabFor(tab).match),
    [matching, tab],
  );

  // When a search matches nothing here but something elsewhere, say where.
  const elsewhere = useMemo(() => {
    if (!query.trim() || filtered.length > 0) return null;
    const hit = COMPLETION_TABS.find(
      (t) => t.key !== tab && (counts[t.key] ?? 0) > 0,
    );
    return hit ? { key: hit.key, label: hit.label, count: counts[hit.key] } : null;
  }, [query, filtered.length, counts, tab]);

  // Track the selection by id so an auto-refresh never yanks the coordinator
  // off the case they are working on. Falls back to the first row in view.
  const selectedRow =
    filtered.find((s) => s.id === selectedId) || filtered[0] || null;

  // Arrow keys walk the queue, "/" jumps to the search box, Escape clears it.
  // A coordinator working thirty packages should not have to reach for the
  // mouse between each one; this is the difference between a tool and a page.
  useEffect(() => {
    function onKey(e) {
      if (e.metaKey || e.ctrlKey || e.altKey) return;

      const tag = e.target.tagName;
      const typing =
        tag === "INPUT" || tag === "TEXTAREA" || e.target.isContentEditable;

      // Escape clears the search from anywhere, not only from inside the box.
      // By the time a coordinator wants the full queue back they have usually
      // clicked a row, and a key that works only while the cursor is still in
      // the field they typed in ten seconds ago is a key nobody finds.
      if (e.key === "Escape" && query) {
        setQuery("");
        if (e.target === searchRef.current) e.target.blur();
        return;
      }

      if (typing) return;

      if (e.key === "/") {
        e.preventDefault();
        searchRef.current?.focus();
        return;
      }

      if (e.key === "?") {
        e.preventDefault();
        setShowShortcuts(true);
        return;
      }

      const step = e.key === "ArrowDown" ? 1 : e.key === "ArrowUp" ? -1 : 0;
      if (step === 0 || filtered.length === 0) return;

      e.preventDefault();
      const at = filtered.findIndex((s) => s.id === selectedRow?.id);
      // Clamped, not wrapped: falling off the end of a queue and silently
      // landing back at the top is how you review the same case twice.
      const next = Math.min(
        Math.max(at === -1 ? 0 : at + step, 0),
        filtered.length - 1,
      );
      setSelectedId(filtered[next].id);
    }

    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [filtered, selectedRow?.id, query]);

  // Queue rows are compact; the detail payload — findings, documents, advisory
  // reading — is fetched only for the row actually open.
  useEffect(() => {
    const id = selectedRow?.id;
    if (!id) {
      setDetail(null);
      return;
    }

    let cancelled = false;
    setLoadingDetail(true);
    getReportSubmission(id)
      .then((data) => {
        if (!cancelled) setDetail(data);
      })
      .catch((err) => {
        console.error(err);
        if (!cancelled) setDetail(null);
      })
      .finally(() => {
        if (!cancelled) setLoadingDetail(false);
      });

    return () => {
      cancelled = true;
    };
  }, [selectedRow?.id, selectedRow?.status]);

  // Signing moves a package out of "To sign" and into "Signed". Following it
  // there keeps the coordinator looking at what they just did — the previous
  // behaviour dropped them onto an unrelated student with no confirmation
  // that anything had happened at all.
  const onSigned = useCallback(
    async (signedId) => {
      setSelectedId(signedId);
      setTab("signed");
      await load();
    },
    [load],
  );

  return (
    <div className="app">
      <TopBar
        query={query}
        setQuery={setQuery}
        searchRef={searchRef}
        loading={loading}
        refresh={load}
        theme={theme}
        toggleTheme={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
        toSignCount={totalCounts.toSign ?? 0}
        lastLoadedAt={lastLoadedAt}
        error={loadError}
      />

      <div className="workspace">
        <CompletionList
          loading={loading}
          error={loadError}
          retry={load}
          submissions={filtered}
          selectedId={selectedRow?.id ?? null}
          setSelectedId={setSelectedId}
          tab={tab}
          setTab={setTab}
          counts={counts}
          query={query}
          elsewhere={elsewhere}
          openShortcuts={() => setShowShortcuts(true)}
        />

        <CompletionDetails selected={detail} loading={loadingDetail} />

        {/* Keyed on the submission: switching rows remounts the panel, so a
            half-drawn signature or a ticked acknowledgement can never carry
            over to the next student. */}
        <CertificatePanel
          key={detail?.id ?? "none"}
          selected={detail}
          onSigned={onSigned}
        />
      </div>

      {showShortcuts && <ShortcutsSheet onClose={() => setShowShortcuts(false)} />}
    </div>
  );
}
