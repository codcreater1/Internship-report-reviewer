import { useEffect, useRef, useState } from "react";
import { Check, Copy } from "lucide-react";

import { copyText } from "../services/clipboard";

/**
 * Copy one value, and say so.
 *
 * The confirmation is the whole point: a copy button that looks identical
 * before and after the click leaves you pressing it twice and pasting into a
 * document to find out whether it worked.
 */
export default function CopyButton({ value, label = "Copy", className = "" }) {
  const [state, setState] = useState("idle");
  const timer = useRef(null);

  useEffect(() => () => clearTimeout(timer.current), []);

  async function onClick(e) {
    // These sit inside rows and links; copying must not also open the file.
    e.preventDefault();
    e.stopPropagation();

    const ok = await copyText(value);
    setState(ok ? "done" : "failed");
    clearTimeout(timer.current);
    timer.current = setTimeout(() => setState("idle"), 1600);
  }

  return (
    <button
      type="button"
      className={`copyButton ${state} ${className}`.trim()}
      onClick={onClick}
      title={state === "failed" ? "Could not copy" : label}
      aria-label={label}
    >
      {state === "done" ? <Check size={13} /> : <Copy size={13} />}
    </button>
  );
}
