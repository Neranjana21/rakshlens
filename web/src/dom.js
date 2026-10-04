// Tiny DOM helper. Text is only ever set through textContent / text nodes,
// never innerHTML, so nothing from a scam message can inject markup.
export function h(tag, props = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(props || {})) {
    if (v == null || v === false) continue;
    if (k === "class") el.className = v;
    else if (k === "text") el.textContent = v;
    else if (k.startsWith("on") && typeof v === "function") el.addEventListener(k.slice(2).toLowerCase(), v);
    else if (k === "value") el.value = v;
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat(Infinity)) {
    if (kid == null || kid === false) continue;
    el.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  }
  return el;
}

// Trusted constant SVG paths only (24x24 viewBox, stroke icons).
const PATHS = {
  ok: "M5 13l4 4L19 7",
  question: "M9.5 9a2.5 2.5 0 114 2c-.9.7-1.5 1.2-1.5 2.5M12 17.5v.01",
  alert: "M12 7v6M12 17v.01",
  stop: "M7 7l10 10M17 7L7 17",
  camera: "M4 8h3l2-2h6l2 2h3v10H4zM12 16a3 3 0 100-6 3 3 0 000 6z",
  mic: "M12 15a3 3 0 003-3V7a3 3 0 00-6 0v5a3 3 0 003 3zM6 11a6 6 0 0012 0M12 17v3",
  speaker: "M5 10v4h3l5 4V6l-5 4zM16 9a4 4 0 010 6",
  download: "M12 4v11M8 11l4 4 4-4M5 19h14",
  phone: "M6 4h3l1.5 4-2 1.5a10 10 0 005 5L15 12.5l4 1.5v3a2 2 0 01-2 2A13 13 0 014 6a2 2 0 012-2z",
  link: "M10 14a4 4 0 005.7 0l3-3a4 4 0 00-5.7-5.7l-1 1M14 10a4 4 0 00-5.7 0l-3 3a4 4 0 005.7 5.7l1-1",
  shield: "M12 3l7 3v5c0 5-3 8-7 10-4-2-7-5-7-10V6z",
  refresh: "M4 12a8 8 0 0114-5l2 2M20 4v5h-5M20 12a8 8 0 01-14 5l-2-2M4 20v-5h5",
  chevron: "M8 10l4 4 4-4",
  x: "M6 6l12 12M18 6L6 18",
  back: "M15 6l-6 6 6 6",
};

export function icon(name, size = 22) {
  const ns = "http://www.w3.org/2000/svg";
  const s = document.createElementNS(ns, "svg");
  s.setAttribute("viewBox", "0 0 24 24");
  s.setAttribute("width", size);
  s.setAttribute("height", size);
  s.setAttribute("fill", "none");
  s.setAttribute("stroke", "currentColor");
  s.setAttribute("stroke-width", "2.2");
  s.setAttribute("stroke-linecap", "round");
  s.setAttribute("stroke-linejoin", "round");
  s.setAttribute("aria-hidden", "true");
  const p = document.createElementNS(ns, "path");
  p.setAttribute("d", PATHS[name] || "");
  s.append(p);
  return s;
}
