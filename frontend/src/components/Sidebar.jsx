import { GraduationCap, ShieldCheck } from "lucide-react";

// This service has one job, so the sidebar is identity and status rather than
// navigation. It exists because the layout is a two-column shell and because a
// coordinator should be able to see at a glance whether anything is waiting.
export default function Sidebar({ toSignCount = 0 }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brandMark">
          <GraduationCap size={20} />
        </div>
        <div>
          <h2>Report Reviewer</h2>
          <p>Internship completions</p>
        </div>
      </div>

      <nav className="nav">
        <span className="navItem active">
          <GraduationCap size={18} /> Completions
          {toSignCount > 0 && <span className="navBadge">{toSignCount}</span>}
        </span>
        <span className="navItem">
          <ShieldCheck size={18} /> Verification
        </span>
      </nav>

      <div className="sideStatus">
        <div className="pulse" />
        <div>
          <strong>System online</strong>
          <p>n8n → FastAPI → Dashboard</p>
        </div>
      </div>
    </aside>
  );
}
