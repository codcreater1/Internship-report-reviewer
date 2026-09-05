import { useCallback, useEffect, useRef, useState } from "react";
import { Award, Download, Lock, PenLine, ShieldAlert } from "lucide-react";

import { certificateUrl, signCertificate } from "../services/reportsApi";
import { absoluteTime } from "../services/time";

// Remembered across submissions: a coordinator signing a queue should not
// retype their own name for every student. Local to this browser only — the
// backend records the name against each signature.
const NAME_KEY = "irr.coordinatorName";

export default function CertificatePanel({ selected, onSigned }) {
  const canvasRef = useRef(null);
  const drawing = useRef(false);
  const inked = useRef(false);

  const [coordinatorName, setCoordinatorName] = useState(
    () => localStorage.getItem(NAME_KEY) || "",
  );
  const [acknowledged, setAcknowledged] = useState(false);
  const [note, setNote] = useState("");
  const [signing, setSigning] = useState(false);
  const [error, setError] = useState("");

  // Match the backing store to the displayed size so strokes are crisp on
  // high-DPI screens and land where the cursor is.
  const fitCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;

    const dpr = window.devicePixelRatio || 1;
    const width = Math.round(rect.width * dpr);
    const height = Math.round(rect.height * dpr);
    if (canvas.width === width && canvas.height === height) return;

    // Resizing a canvas clears it, so anything drawn is gone either way. Say
    // so by resetting the flag rather than leaving a signature the coordinator
    // can no longer see but the button still believes in.
    canvas.width = width;
    canvas.height = height;
    inked.current = false;

    const ctx = canvas.getContext("2d");
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.scale(dpr, dpr);
    ctx.lineWidth = 2;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.strokeStyle = "#14161a";
  }, []);

  // Per-submission state is not reset here: App keys this component on the
  // submission id, so switching rows remounts it and every useState above
  // starts fresh.
  useEffect(() => {
    fitCanvas();

    // The pad is inside a column that changes width when the window does, and
    // on a narrow screen it is in a stacked layout that settles after mount.
    // Without this the drawing surface keeps its first measurement and strokes
    // land somewhere other than the cursor.
    const canvas = canvasRef.current;
    if (!canvas || typeof ResizeObserver === "undefined") return;

    const observer = new ResizeObserver(fitCanvas);
    observer.observe(canvas);
    return () => observer.disconnect();
  }, [fitCanvas]);

  if (!selected) {
    return (
      <aside className="col action">
        <div className="colHead">
          <p className="colTitle">Certificate</p>
        </div>
        <div className="empty">
          <p>Select a submission to issue its certificate.</p>
        </div>
      </aside>
    );
  }

  const signedUrl = certificateUrl(selected.signed_certificate_download_url);
  const warnings = (selected.findings || []).filter((f) => f.severity === "warning");
  const blocked =
    selected.status === "rejected" || selected.status === "request_clarification";
  const needsAcknowledgement = selected.status === "pending";

  function point(e) {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const t = e.touches ? e.touches[0] : e;
    return { x: t.clientX - rect.left, y: t.clientY - rect.top };
  }

  function startStroke(e) {
    drawing.current = true;
    const { x, y } = point(e);
    const ctx = canvasRef.current.getContext("2d");
    ctx.beginPath();
    ctx.moveTo(x, y);
  }

  function moveStroke(e) {
    if (!drawing.current) return;
    e.preventDefault();
    const { x, y } = point(e);
    const ctx = canvasRef.current.getContext("2d");
    ctx.lineTo(x, y);
    ctx.stroke();
    inked.current = true;
  }

  function endStroke() {
    drawing.current = false;
  }

  function clearPad() {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.restore();
    inked.current = false;
    setError("");
  }

  async function handleSign() {
    if (!coordinatorName.trim()) {
      setError("Enter your name — it is printed on the certificate.");
      return;
    }
    if (!inked.current) {
      setError("Draw your signature first.");
      return;
    }

    setError("");
    setSigning(true);
    try {
      localStorage.setItem(NAME_KEY, coordinatorName.trim());
      await signCertificate(selected.id, {
        coordinatorName: coordinatorName.trim(),
        signatureImageBase64: canvasRef.current.toDataURL("image/png"),
        acknowledgeWarnings: acknowledged,
        note,
      });
      // The certificate is not opened for them here. A window.open() after an
      // await is not a user gesture any more, so browsers block it silently:
      // the coordinator saw nothing happen and had no download either. The
      // panel now settles into its issued state with the link in it.
      await onSigned(selected.id);
    } catch (err) {
      // The backend's refusals are written to be read by a person.
      setError(err.message || "Signing failed.");
    } finally {
      setSigning(false);
    }
  }

  return (
    <aside className="col action">
      <div className="colHead">
        <p className="colTitle">Certificate</p>
      </div>

      {signedUrl ? (
        <div className="actionCard">
          <div className="issued">
            <div className="issuedMark">
              <Award size={20} />
            </div>
            <h3>Certificate issued</h3>
            <p>
              Signed by {selected.signed_by}
              {selected.signed_at && (
                <>
                  <br />
                  <span className="issuedStamp">{absoluteTime(selected.signed_at)}</span>
                </>
              )}
            </p>

            <a className="download" href={signedUrl} target="_blank" rel="noreferrer">
              <Download size={15} /> Download certificate
            </a>
          </div>

          {selected.coordinator_note && (
            <p className="footnote">Note: {selected.coordinator_note}</p>
          )}
          <p className="footnote">
            It carries the hash of the three submitted documents. Rehash them to
            check it at any time.
          </p>
        </div>
      ) : blocked ? (
        <div className="actionCard">
          <div className="locked">
            <div className="lockedMark">
              <Lock size={20} />
            </div>
            <strong>Cannot be signed yet</strong>
            <p>
              {selected.status === "rejected"
                ? "This submission cannot be approved automatically. Contact the student directly — signing is not available."
                : "The student has been asked to correct and resend. Signing now would certify an incomplete record."}
            </p>
          </div>
        </div>
      ) : (
        <div className="actionCard">
          <label className="field">
            <span className="fieldLabel">Your name</span>
            <input
              className="input"
              type="text"
              value={coordinatorName}
              onChange={(e) => setCoordinatorName(e.target.value)}
              placeholder="e.g. dr Anna Zielińska"
            />
          </label>

          {needsAcknowledgement && (
            <div className="ackCard">
              <ShieldAlert size={16} />
              <div>
                <strong>
                  {warnings.length} open point{warnings.length === 1 ? "" : "s"}
                </strong>
                <p>
                  Signing anyway records them on the certificate. Read them in
                  the panel to the left first.
                </p>
                <label className="ackCheck">
                  <input
                    type="checkbox"
                    checked={acknowledged}
                    onChange={(e) => setAcknowledged(e.target.checked)}
                  />
                  <span>I have reviewed these and accept them.</span>
                </label>
              </div>
            </div>
          )}

          <label className="field">
            <span className="fieldLabel">Note (optional)</span>
            <input
              className="input"
              type="text"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Recorded with the decision"
            />
          </label>

          <span className="fieldLabel">
            <PenLine size={12} style={{ verticalAlign: -1, marginRight: 5 }} />
            Signature
          </span>

          <div className="padWrap">
            <canvas
              ref={canvasRef}
              className="pad"
              onMouseDown={startStroke}
              onMouseMove={moveStroke}
              onMouseUp={endStroke}
              onMouseLeave={endStroke}
              onTouchStart={startStroke}
              onTouchMove={moveStroke}
              onTouchEnd={endStroke}
            />
            <div className="padLine" />
            <span className="padHint">Sign above the line</span>
          </div>

          <div className="actions">
            <button className="btn ghost" type="button" onClick={clearPad}>
              Clear
            </button>
            <button
              className="btn primary"
              type="button"
              onClick={handleSign}
              disabled={signing || (needsAcknowledgement && !acknowledged)}
            >
              <Award size={15} />
              {signing ? "Signing…" : "Sign certificate"}
            </button>
          </div>

          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
        </div>
      )}
    </aside>
  );
}
