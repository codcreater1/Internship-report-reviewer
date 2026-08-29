import { useCallback, useEffect, useMemo, useState } from "react";
import "./App.css";

import { getReportSubmission, getReportSubmissions } from "./services/reportsApi";
import { countsByTab, tabFor } from "./services/completionTabs";
import TopBar from "./components/TopBar";
import CompletionList from "./components/CompletionList";
import CompletionDetails from "./components/CompletionDetails";
import CertificatePanel from "./components/CertificatePanel";

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

export default function App() {
  const [theme, setTheme] = useState(initialTheme);
  const [query, setQuery] = useState("");
  const [submissions, setSubmissions] = useState([]);
  const [tab, setTab] = useState("toSign");
  const [selectedId, setSelectedId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getReportSubmissions();
      setSubmissions(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, REFRESH_MS);
    return () => clearInterval(interval);
  }, [load]);

  const counts = useMemo(() => countsByTab(submissions), [submissions]);

  const filtered = useMemo(() => {
    const q = query.toLowerCase();
    const active = tabFor(tab);
    return submissions.filter(active.match).filter((s) => {
      const text =
        `${s.student_name ?? ""} ${s.student_id ?? ""} ${s.company ?? ""} ${s.status}`.toLowerCase();
      return text.includes(q);
    });
  }, [submissions, query, tab]);

  // Track the selection by id so an auto-refresh never yanks the coordinator
  // off the case they are working on. Falls back to the first row in view.
  const selectedRow =
    filtered.find((s) => s.id === selectedId) || filtered[0] || null;

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

  return (
    <div className="app">
      <TopBar
        query={query}
        setQuery={setQuery}
        loading={loading}
        refresh={load}
        theme={theme}
        toggleTheme={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
        toSignCount={counts.toSign ?? 0}
      />

      <div className="workspace">
        <CompletionList
          loading={loading}
          submissions={filtered}
          selectedId={selectedRow?.id ?? null}
          setSelectedId={setSelectedId}
          tab={tab}
          setTab={setTab}
          counts={counts}
        />

        <CompletionDetails selected={detail} loading={loadingDetail} />

        {/* Keyed on the submission: switching rows remounts the panel, so a
            half-drawn signature or a ticked acknowledgement can never carry
            over to the next student. */}
        <CertificatePanel
          key={detail?.id ?? "none"}
          selected={detail}
          refresh={load}
        />
      </div>
    </div>
  );
}
