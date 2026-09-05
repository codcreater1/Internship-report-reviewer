import { GraduationCap, Moon, Plus, RefreshCw, Search, Sun, WifiOff } from "lucide-react";

import { relativeTime } from "../services/time";

/**
 * One bar instead of a navigation sidebar. This service has a single view, so
 * a nav rail would be an empty gesture — the width is better spent on the
 * findings text and document hashes in the columns below.
 */
export default function TopBar({
  query,
  setQuery,
  searchRef,
  loading,
  refresh,
  theme,
  toggleTheme,
  toSignCount,
  lastLoadedAt,
  error,
  openUpload,
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
          ref={searchRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search student, company or ID"
          aria-label="Search submissions"
        />
        {/* Shown until it is used, then it stops taking up room. */}
        {!query && <kbd className="searchKey">/</kbd>}
      </label>

      <div className="topActions">
        {/* A queue that cannot be reloaded is worse than an empty one, because
            it looks the same. This says which of the two you are looking at. */}
        {error && (
          <span className="pill danger" role="status">
            <WifiOff size={13} />
            Offline
          </span>
        )}

        {/* Only surfaced when something is genuinely waiting on a coordinator.
            A counter that is always lit stops being read. */}
        {!error && toSignCount > 0 && (
          <span className="pill">
            <b className="tnum">{toSignCount}</b> awaiting signature
          </span>
        )}

        {!error && lastLoadedAt && (
          <span className="topStamp" title="The queue reloads every minute">
            updated {relativeTime(lastLoadedAt)}
          </span>
        )}

        {/* The email route is how packages usually arrive; it is not the only
            way one can. Three PDFs handed over on a memory stick used to mean
            emailing them to yourself and waiting for the next poll. */}
        <button className="btn small primary" type="button" onClick={openUpload}>
          <Plus size={15} />
          Submit
        </button>

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
