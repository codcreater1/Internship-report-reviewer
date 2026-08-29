// The vocabulary the dashboard shows, and the one place raw API values are
// turned into words a coordinator reads.

// `approved` means every check passed and the package is waiting for a
// signature. It is deliberately not called "signed" until somebody signs it —
// passing the checks is necessary for a certificate, never sufficient.
export const REPORT_STATUS_LABELS = {
  approved: "ready to sign",
  pending: "needs review",
  request_clarification: "needs info",
  rejected: "rejected",
  signed: "signed",
};

export function reportStatusLabel(status = "") {
  return REPORT_STATUS_LABELS[status] || status.replace(/_/g, " ");
}

// One line per status, shown above the findings so a coordinator opening a
// case knows what is being asked of them before reading the detail.
export const REPORT_STATUS_SUMMARY = {
  approved:
    "Every automated check passed. This package is waiting for your signature.",
  pending:
    "Nothing is provably wrong, but there are open points worth a look before signing.",
  request_clarification:
    "The student has been asked to correct something and resend. Nothing can be signed until they do.",
  rejected:
    "This cannot be approved automatically and needs a conversation with the student.",
  signed: "The completion certificate has been issued.",
};

// Severity drives what happens to a package, so it is worth naming plainly
// rather than showing the raw enum.
export const SEVERITY_LABELS = {
  reject: "blocking",
  clarify: "student action",
  warning: "open point",
  info: "note",
};

export function severityLabel(severity = "") {
  return SEVERITY_LABELS[severity] || severity;
}

export const DOCUMENT_LABELS = {
  report: "Internship report",
  evaluation: "Employer evaluation",
  timesheet: "Attendance record",
  unknown: "Unrecognised document",
};
