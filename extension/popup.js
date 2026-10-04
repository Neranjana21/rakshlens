// All text is inserted with textContent; nothing from a message is parsed as HTML.
const DEFAULT_API = "http://localhost:8000";
const $ = (id) => document.getElementById(id);

async function apiBase() {
  const { api } = await chrome.storage.local.get("api");
  return (api || DEFAULT_API).replace(/\/+$/, "");
}

function el(tag, text, cls) {
  const e = document.createElement(tag);
  if (text != null) e.textContent = text;
  if (cls) e.className = cls;
  return e;
}

async function check() {
  const out = $("out");
  out.replaceChildren(el("p", "Checking…"));
  try {
    const res = await fetch(`${await apiBase()}/api/analyze/text`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: $("msg").value, lang: $("lang").value, allow_cloud: false }),
    });
    if (!res.ok) throw new Error(res.status === 422 ? "Please paste a longer message." : "Could not check right now.");
    const r = await res.json();
    const ul = el("ul");
    r.findings.slice(0, 4).forEach((f) => ul.append(el("li", f.title)));
    const acts = el("ul");
    r.actions.slice(0, 3).forEach((a) => acts.append(el("li", a.text)));
    out.replaceChildren(el("div", r.band_label, `band ${r.band}`), el("p", r.headline), ul, acts, el("small", r.disclaimer));
  } catch (e) {
    out.replaceChildren(el("p", e.message === "Failed to fetch" ? "Cannot reach the RakshaLens server. Check the server address below." : e.message, "err"));
  }
}

(async function init() {
  $("check").addEventListener("click", check);
  $("saveapi").addEventListener("click", async () => {
    await chrome.storage.local.set({ api: $("api").value.trim() });
  });
  $("api").value = (await chrome.storage.local.get("api")).api || "";
  if (new URLSearchParams(location.search).has("pending")) {
    const { pending } = await chrome.storage.session.get("pending");
    await chrome.storage.session.remove("pending"); // cleared as soon as it is read
    if (pending) {
      $("msg").value = pending;
      check();
    }
  }
})();
