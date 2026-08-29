import { GraduationCap, Moon, RefreshCw, Search, Sun } from "lucide-react";

/**
 * One bar instead of a navigation sidebar. This service has a single view, so
 * a nav rail would be an empty gesture — the width is better spent on the
 * findings text and document hashes in the columns below.
 */
export default function TopBar({
  query,
  setQuery,
  loading,
  refresh,
  theme,
  toggleTheme,
  toSignCount,
}) {
  return (
    <header className="topbar">
      <div className="brand">
        <div className="brandMark">
          <GraduationCap size={17} />
        </div>
        <div className="brandText">
          <strong>Report Reviewer</strong>
          <span>Internship completions</span>
        </div>
      </div>

      <label className="topSearch">
        <Search size={15} />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search student, company or ID"
          aria-label="Search submissions"
        />
      </label>

      <div className="topActions">
        {/* Only surfaced when something is genuinely waiting on a coordinator.
            A counter that is always lit stops being read. */}
        {toSignCount > 0 && (
          <span className="pill">
            <b className="tnum">{toSignCount}</b> awaiting signature
          </span>
        )}

        <button
          className="iconButton"
          onClick={toggleTheme}
          aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
          title={theme === "dark" ? "Light theme" : "Dark theme"}
        >
          {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
        </button>

        <button
          className="iconButton"
          onClick={refresh}
          aria-label="Refresh"
          title="Refresh"
        >
          <RefreshCw size={16} className={loading ? "spinning" : ""} />
        </button>
      </div>
    </header>
  );
}
