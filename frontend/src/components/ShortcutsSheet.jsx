import { useEffect } from "react";
import { X } from "lucide-react";

const KEYS = [
  { keys: ["↑", "↓"], what: "Move through the queue" },
  { keys: ["/"], what: "Jump to the search box" },
  { keys: ["Esc"], what: "Clear the search, or close this" },
  { keys: ["?"], what: "Open this list" },
];

/**
 * The keys, written down.
 *
 * A tool that rewards the keyboard has to say so somewhere other than a hint
 * under the tab strip, and the place people look is the sheet that "?" opens.
 */
export default function ShortcutsSheet({ onClose }) {
  useEffect(() => {
    function onKey(e) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="sheetBackdrop" onClick={onClose} role="presentation">
      <div
        className="sheet"
        role="dialog"
        aria-modal="true"
        aria-label="Keyboard shortcuts"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sheetHead">
          <h2>Keyboard</h2>
          <button
            type="button"
            className="iconButton"
            onClick={onClose}
            aria-label="Close"
          >
            <X size={15} />
          </button>
        </div>

        <ul className="sheetList">
          {KEYS.map((row) => (
            <li key={row.what}>
              <span className="sheetKeys">
                {row.keys.map((k) => (
                  <kbd key={k}>{k}</kbd>
                ))}
              </span>
              <span>{row.what}</span>
            </li>
          ))}
        </ul>

        <p className="sheetNote">
          The queue is meant to be worked without the mouse. Signing is not:
          that one is a deliberate act, and it keeps its button.
        </p>
      </div>
    </div>
  );
}
