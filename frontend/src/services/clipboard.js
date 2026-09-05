// Copying a hash or the wording a student was sent.
//
// navigator.clipboard is unavailable on plain-HTTP origins, which is exactly
// where a university deployment often sits, so the fallback is not academic:
// without it the copy buttons would be dead on the one deployment that needs
// them most.
export async function copyText(text) {
  if (!text) return false;

  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {
    // Fall through: a rejected permission is not a reason to give up.
  }

  try {
    const area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    const ok = document.execCommand("copy");
    document.body.removeChild(area);
    return ok;
  } catch {
    return false;
  }
}
