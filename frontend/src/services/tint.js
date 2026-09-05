// A per-student tint for the initials block.
//
// Working a list of thirty names, the shape you actually navigate by is
// colour: you remember that the case you were on was the teal one long before
// you remember the spelling of the surname. The hue is derived from the name
// itself, so it is stable across reloads, across machines, and across the
// queue — the same student is the same colour everywhere, without storing
// anything.
//
// Saturation and lightness are fixed and deliberately low: this has to sit
// under bronze without competing with it, and has to stay legible in both
// themes. It carries no meaning — status has its own colour, and a tint that
// looked like a verdict would be worse than no tint at all.
export function tintFor(name = "") {
  let hash = 0;
  for (let i = 0; i < name.length; i += 1) {
    hash = (hash * 31 + name.charCodeAt(i)) % 360;
  }
  return hash;
}
