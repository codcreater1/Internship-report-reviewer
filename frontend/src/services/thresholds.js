// The lines each figure is measured against.
//
// Read from the service — `GET /reports/rules` publishes what it is actually
// enforcing, and a university changes those numbers in
// rules/university-rules.json. The values below are only what to draw before
// that answer arrives, and for a deployment old enough not to have the route:
// a dashboard that refused to render because it could not read a policy file
// would be a poor trade.
//
// The rule is written out beside every bar — "20 required", "60 to pass" — so
// a coordinator reads it rather than trusting a colour. The status and the
// findings remain the authority on what actually happened to a package; these
// bars only say how close a number came to its line.
export const DEFAULTS = {
  minWorkingDays: 20,
  minReportWords: 500,
  minEvaluationScore: 60,
  similarityWarn: 0.6,
  similarityReject: 0.8,
};

/** Reshape what GET /reports/rules returns; fall back to what shipped. */
export function rulesFrom(published) {
  if (!published) return DEFAULTS;
  return {
    minWorkingDays: published.attendance?.min_working_days ?? DEFAULTS.minWorkingDays,
    minReportWords: published.report?.min_words ?? DEFAULTS.minReportWords,
    minEvaluationScore: published.evaluation?.min_score ?? DEFAULTS.minEvaluationScore,
    similarityWarn: published.originality?.warn_at ?? DEFAULTS.similarityWarn,
    similarityReject: published.originality?.reject_at ?? DEFAULTS.similarityReject,
  };
}

const clamp = (n) => Math.max(0, Math.min(1, n));

/**
 * A bar for one figure: how full, what tone, and the rule in words.
 *
 * Returns null when there is nothing honest to draw — a missing employer score
 * is not a score of zero, and a bar at zero would read as one.
 */
export function meterFor(kind, value, rules = DEFAULTS) {
  if (value === null || value === undefined) return null;

  switch (kind) {
    case "days":
      return {
        ratio: clamp(value / rules.minWorkingDays),
        tone: value >= rules.minWorkingDays ? "ok" : "warn",
        caption: `${rules.minWorkingDays} required`,
      };

    case "score":
      return {
        ratio: clamp(value / 100),
        // Below the pass mark is the one finding that cannot be corrected by
        // resending, so it is the one that earns the danger colour.
        tone: value >= rules.minEvaluationScore ? "ok" : "danger",
        caption: `${rules.minEvaluationScore} to pass`,
        mark: rules.minEvaluationScore / 100,
      };

    case "words":
      return {
        ratio: clamp(value / rules.minReportWords),
        tone: value >= rules.minReportWords ? "ok" : "warn",
        caption: `${rules.minReportWords} required`,
      };

    // Similarity is the one figure where less is better, so the bar fills
    // towards the threshold rather than towards a target.
    case "similarity":
      return {
        ratio: clamp(value),
        tone:
          value >= rules.similarityReject
            ? "danger"
            : value >= rules.similarityWarn
              ? "warn"
              : "ok",
        caption: `${Math.round(rules.similarityReject * 100)}% rejects`,
        mark: rules.similarityReject,
      };

    default:
      return null;
  }
}
