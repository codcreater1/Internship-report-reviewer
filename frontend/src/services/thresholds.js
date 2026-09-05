// The lines each figure is measured against.
//
// These mirror backend/app/core/report_constants.py. They are duplicated here
// on purpose and shown as text next to every bar — "20 required", "60 to pass"
// — so a coordinator reads the rule rather than trusting a colour, and a
// divergence between the two shows up as a visibly wrong caption instead of a
// silently wrong tint. The status and the findings remain the authority on
// what actually happened to a package; these bars only say how close a number
// came to its line.
export const MIN_WORKING_DAYS = 20;
export const MIN_REPORT_WORDS = 500;
export const MIN_EVALUATION_SCORE = 60;
export const SIMILARITY_WARN = 0.6;
export const SIMILARITY_REJECT = 0.8;

const clamp = (n) => Math.max(0, Math.min(1, n));

/**
 * A bar for one figure: how full, what tone, and the rule in words.
 *
 * Returns null when there is nothing honest to draw — a missing employer score
 * is not a score of zero, and a bar at zero would read as one.
 */
export function meterFor(kind, value) {
  if (value === null || value === undefined) return null;

  switch (kind) {
    case "days":
      return {
        ratio: clamp(value / MIN_WORKING_DAYS),
        tone: value >= MIN_WORKING_DAYS ? "ok" : "warn",
        caption: `${MIN_WORKING_DAYS} required`,
      };

    case "score":
      return {
        ratio: clamp(value / 100),
        // Below the pass mark is the one finding that cannot be corrected by
        // resending, so it is the one that earns the danger colour.
        tone: value >= MIN_EVALUATION_SCORE ? "ok" : "danger",
        caption: `${MIN_EVALUATION_SCORE} to pass`,
        mark: MIN_EVALUATION_SCORE / 100,
      };

    case "words":
      return {
        ratio: clamp(value / MIN_REPORT_WORDS),
        tone: value >= MIN_REPORT_WORDS ? "ok" : "warn",
        caption: `${MIN_REPORT_WORDS} required`,
      };

    // Similarity is the one figure where less is better, so the bar fills
    // towards the threshold rather than towards a target.
    case "similarity":
      return {
        ratio: clamp(value),
        tone:
          value >= SIMILARITY_REJECT
            ? "danger"
            : value >= SIMILARITY_WARN
              ? "warn"
              : "ok",
        caption: `${Math.round(SIMILARITY_REJECT * 100)}% rejects`,
        mark: SIMILARITY_REJECT,
      };

    default:
      return null;
  }
}
