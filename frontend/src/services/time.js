// Arrival times. The queue is worked in order of what has been waiting
// longest, and until now the dashboard showed no time at all — a coordinator
// could not tell a package that landed this morning from one sitting there
// since last term.
//
// Relative in the list because that is the question ("how long has this been
// waiting"), absolute on hover and in the record because that is what gets
// quoted in an email to a student.

const MINUTE = 60_000;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

export function parseInstant(value) {
  if (!value) return null;
  const at = new Date(value);
  return Number.isNaN(at.getTime()) ? null : at;
}

/** "just now", "12 min ago", "3 h ago", "yesterday", "6 Sep". */
export function relativeTime(value, now = Date.now()) {
  const at = parseInstant(value);
  if (!at) return "";

  const delta = now - at.getTime();
  // A clock skew between this browser and the server should read as "just
  // now", never as a package that arrives from the future.
  if (delta < MINUTE) return "just now";
  if (delta < HOUR) return `${Math.floor(delta / MINUTE)} min ago`;
  if (delta < DAY) return `${Math.floor(delta / HOUR)} h ago`;
  if (delta < 2 * DAY) return "yesterday";
  if (delta < 7 * DAY) return `${Math.floor(delta / DAY)} days ago`;

  return at.toLocaleDateString(undefined, { day: "numeric", month: "short" });
}

/** The full stamp, for tooltips and the record itself. */
export function absoluteTime(value) {
  const at = parseInstant(value);
  if (!at) return "";
  return at.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}
