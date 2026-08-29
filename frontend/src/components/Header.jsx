import { RefreshCw, Search } from "lucide-react";

export default function Header({ query, setQuery, loading, refresh }) {
  return (
    <header className="top">
      <div>
        <p className="eyebrow">Internship Coordination</p>
        <h1>Internship Completions</h1>
        <p className="sub">
          End-of-internship packages — report, employer evaluation and attendance
          record — checked automatically and waiting for your signature.
        </p>
      </div>

      <div className="topActions">
        <div className="search">
          <Search size={18} />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search student, company or ID..."
          />
        </div>

        <button className="refresh" onClick={refresh}>
          <RefreshCw size={18} className={loading ? "spinning" : ""} />
          Refresh
        </button>
      </div>
    </header>
  );
}
