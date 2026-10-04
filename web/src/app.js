import { h, icon } from "./dom.js";
import { STR, LANGS, SPEECH, guessLang } from "./i18n/index.js";
import { analyze, downloadReport, getConfig, ApiError } from "./api.js";
import { canListen, canSpeak, hasVoice, speak, stopSpeaking, startListening, stopListening } from "./voice.js";

const root = document.getElementById("app");

// Preferences only (language, text size). Message content is never persisted.
const pref = {
  get(k) { try { return localStorage.getItem("rl_" + k); } catch { return null; } },
  set(k, v) { try { localStorage.setItem("rl_" + k, v); } catch { /* storage blocked */ } },
};

const state = {
  lang: STR[pref.get("lang")] ? pref.get("lang") : guessLang(),
  big: pref.get("big") === "1",
  text: "",
  file: null,
  cloud: false,
  busy: false,
  error: null,
  result: null,
  listening: false,
  speaking: false,
  voiceMsg: null,
  config: { cloud_available: false },
  view: "check",
  trustMsg: null,
};

const t = () => STR[state.lang];
const BAND = {
  low: { icon: "ok", idx: 0 },
  verify: { icon: "question", idx: 1 },
  high: { icon: "alert", idx: 2 },
  critical: { icon: "stop", idx: 3 },
};

/* ---------------------------------------------------------------- actions */
async function check() {
  if (state.busy) return;
  stopSpeaking();
  state.speaking = false;
  state.busy = true;
  state.error = null;
  render();
  try {
    state.result = await analyze({ text: state.text, file: state.file, lang: state.lang, allowCloud: state.cloud });
    if (state.result.input && state.result.input.extracted_text && !state.text) state.text = "";
  } catch (e) {
    state.result = null;
    state.error = e instanceof ApiError ? e.code : "generic";
  }
  state.busy = false;
  render();
  const target = document.getElementById("result-heading") || document.getElementById("error-box");
  if (target) { target.focus({ preventScroll: true }); target.scrollIntoView({ behavior: "smooth", block: "start" }); }
}

function reset() {
  stopSpeaking(); stopListening();
  Object.assign(state, { view: "check", trustMsg: null, text: "", file: null, result: null, error: null, speaking: false, listening: false, voiceMsg: null });
  render();
  window.scrollTo({ top: 0 });
}

// Back to the input with the message kept, so the user can edit and re-check.
function back() {
  stopSpeaking();
  Object.assign(state, { result: null, error: null, speaking: false, voiceMsg: null, trustMsg: null });
  render();
  window.scrollTo({ top: 0 });
}

function setLang(code) {
  if (code === state.lang) return;
  stopSpeaking(); stopListening();
  state.lang = code;
  state.speaking = false; state.listening = false; state.voiceMsg = null;
  pref.set("lang", code);
  document.documentElement.lang = code;
  if (state.result && (state.text || state.file)) check(); else render();
}

function toggleSpeak() {
  const r = state.result;
  if (!r) return;
  if (state.speaking) { stopSpeaking(); state.speaking = false; render(); return; }
  if (!hasVoice(r.speech_lang)) { state.voiceMsg = t().noVoice; render(); return; }
  state.voiceMsg = null;
  const first = r.actions && r.actions[0] ? r.actions[0].text : "";
  state.speaking = speak(`${r.summary} ${first}`, r.speech_lang, () => { state.speaking = false; render(); });
  render();
}

function toggleMic() {
  if (state.listening) { stopListening(); return; }
  state.voiceMsg = null;
  state.listening = startListening(SPEECH[state.lang], {
    onText: (txt) => { state.text = (state.text ? state.text + " " : "") + txt; const ta = document.getElementById("msg"); if (ta) ta.value = state.text; },
    onEnd: () => { state.listening = false; render(); },
    onError: () => { state.listening = false; render(); },
  });
  render();
}

async function shareTrust() {
  const r = state.result, s = t();
  if (!r) return;
  const reasons = (r.seen_in_message || []).slice(0, 3).map((f) => "- " + f.title).join("\n");
  const note = `${s.trustHello}\n${r.band_label}\n${reasons}\n\n${s.trustAsk}`;
  try {
    if (navigator.share) { await navigator.share({ text: note }); return; }
  } catch (e) { if (e && e.name === "AbortError") return; }
  try { await navigator.clipboard.writeText(note); state.trustMsg = s.trustCopied; } catch { state.trustMsg = note; }
  render();
}

function learnView() {
  const s = t();
  return h("section", { "aria-labelledby": "learn-h" },
    h("h2", { id: "learn-h", class: "mt16", text: s.learnTitle }),
    h("p", { class: "muted", text: s.learnIntro }),
    h("ul", { class: "learn-list" }, s.learnItems.map(([title, body]) => h("li", {}, h("strong", { text: title }), h("p", { text: body })))),
    h("button", { class: "btn btn-primary", type: "button", onclick: () => { state.view = "check"; render(); window.scrollTo({ top: 0 }); }, text: s.learnBack }));
}

/* ------------------------------------------------------------- components */
function header() {
  const s = t();
  const compact = state.view === "check" && !!state.result && !state.busy; // result screen: keep the actions near the top
  return h("header", {},
    h("div", { class: "top" },
      h("div", { class: "brand" },
        h("div", { class: "logo" }, icon("shield", 24)),
        h("div", {}, h("h1", { text: "RakshaLens" }), h("p", { class: "tagline", text: s.tagline }))),
    ),
    h("div", { class: "controls", role: "group", "aria-label": s.language },
      LANGS.map((l) => h("button", { class: "chip", type: "button", lang: l.code, "aria-pressed": String(l.code === state.lang), onclick: () => setLang(l.code), text: l.name })),
      h("button", { class: "chip", type: "button", "aria-pressed": String(state.big), onclick: () => { state.big = !state.big; pref.set("big", state.big ? "1" : "0"); render(); }, text: "A+  " + s.textSize }),
    ),
    compact ? null : h("div", { class: "info-row" },
      h("div", { class: "banner", role: "note" }, icon("shield", 20), h("span", { text: s.privacy })),
      state.view === "check" ? h("button", { class: "chip", type: "button", onclick: () => { state.view = "learn"; render(); window.scrollTo({ top: 0 }); }, text: s.learnLink }) : null),
  );
}

// Sample screenshots (made-up messages, fake numbers) so the screenshot flow can be tried without a real scam.
const SAMPLES = [
  { id: "praveen", file: "samples/praveen-vip-calls.png" },
  { id: "praveenMid", file: "samples/praveen-analyst-sebi-number.png" },
  { id: "disguise", file: "samples/disguised-letters-and-digits.png" },
  { id: "kavitaHi", file: "samples/kavita-hindi-ipo-doubling.png", lang: "hi" },
  { id: "hiMid", file: "samples/hindi-analyst-sebi-number.png", lang: "hi" },
  { id: "hiOk", file: "samples/hindi-genuine-sip-reminder.png", lang: "hi" },
  { id: "taMid", file: "samples/tamil-analyst-sebi-number.png", lang: "ta" },
  { id: "taOk", file: "samples/tamil-genuine-bank-credit.png", lang: "ta" },
  { id: "kavita", file: "samples/kavita-investment-club.png" },
  { id: "kavitaTa", file: "samples/kavita-tamil-double.png", lang: "ta" },
  { id: "babulal", file: "samples/babulal-nominee-phishing.png" },
  { id: "babulalOk", file: "samples/babulal-genuine-reminder.png" },
];

async function loadSample(sample) {
  try {
    const res = await fetch(sample.file);
    if (!res.ok) throw new Error("sample");
    const blob = await res.blob();
    state.file = new File([blob], sample.file.split("/").pop(), { type: blob.type || "image/png" });
    // A Tamil or Hindi sample switches the app to that language, so the result reads back in it.
    if (sample.lang && STR[sample.lang] && sample.lang !== state.lang) { state.lang = sample.lang; pref.set("lang", sample.lang); }
    state.text = "";
    state.error = null;
  } catch {
    state.error = "offline";
  }
  render();
}

function samplesPanel() {
  const s = t();
  return h("details", { class: "samples" },
    h("summary", {}, icon("camera", 18), s.samplesTitle),
    h("p", { class: "muted", text: s.samplesHelp }),
    h("div", { class: "sample-list" }, SAMPLES.map((x) =>
      h("button", { class: "btn btn-quiet", type: "button", onclick: () => loadSample(x), text: s.samples[x.id] }))));
}

// Home screen, under the input: where to report or get help, and the phone-call prototype.
function homeExtras() {
  const s = t();
  const helplines = (state.config.helplines && state.config.helplines.length) ? state.config.helplines : FALLBACK_HELPLINES;
  return h("div", { class: "home-extras" },
    h("section", { "aria-labelledby": "help-h" },
      h("h2", { id: "help-h", text: s.helplinesTitle }),
      helplinesGrid(helplines)),
    h("section", { class: "call-card", "aria-labelledby": "call-h" },
      h("div", { class: "call-ic" }, icon("phone", 26)),
      h("div", { class: "call-txt" },
        h("h2", { id: "call-h", class: "m0", text: s.callTitle }),
        h("p", { text: s.callBody }),
        h("a", { class: "btn", href: "call.html" }, icon("phone", 20), s.callButton))));
}

function inputPanel() {
  const s = t();
  const fileInput = h("input", { type: "file", accept: "image/*", class: "sr", id: "file", tabindex: "-1",
    onchange: (e) => { state.file = e.target.files[0] || null; render(); } });
  return h("section", { class: "single", "aria-labelledby": "in-h" },
    h("h2", { id: "in-h", text: s.inputTitle }),
    h("div", { class: "card" },
      h("label", { class: "lbl", for: "msg", text: s.pasteLabel }),
      h("textarea", { id: "msg", placeholder: s.pastePlaceholder, value: state.text, oninput: (e) => { state.text = e.target.value; } }),
      state.file ? h("div", { class: "file-pill" },
        h("span", {}, icon("camera", 20), " ", s.uploadChosen, " · ", state.file.name || ""),
        h("button", { class: "chip", type: "button", onclick: () => { state.file = null; render(); }, text: s.removeImage })) : null,
      fileInput,
      h("div", { class: "btn-row" },
        h("button", { class: "btn", type: "button", onclick: () => fileInput.click() }, icon("camera"), s.upload),
        canListen ? h("button", { class: "btn", type: "button", "aria-pressed": String(state.listening), onclick: toggleMic }, icon("mic"), state.listening ? s.listening : s.speak) : null),
      canListen ? h("p", { class: "muted", text: s.voiceNote }) : null,
      state.voiceMsg ? h("p", { class: "error", role: "alert", text: state.voiceMsg }) : null,
      state.config.cloud_available ? h("div", { class: "row" },
        h("input", { type: "checkbox", id: "cloud", checked: state.cloud ? "" : null, onchange: (e) => { state.cloud = e.target.checked; } }),
        h("label", { for: "cloud" }, h("strong", { text: s.cloudLabel }), h("br"), h("span", { class: "muted", text: s.cloudHelp }))) : null,
      state.error ? h("div", { class: "error", id: "error-box", role: "alert", tabindex: "-1", text: s.errors[state.error] || s.errors.generic }) : null,
      h("button", { class: "btn btn-primary", type: "button", disabled: state.busy ? "" : null, onclick: check },
        state.busy ? h("span", { class: "spinner", "aria-hidden": "true" }) : null, state.busy ? s.checking : s.check),
    ),
    samplesPanel(),
    homeExtras(),
  );
}

function bandCard(r) {
  const s = t();
  const b = BAND[r.band];
  return h("section", { class: `band ${r.band}`, "aria-live": "polite" },
    h("div", { class: "head" },
      h("div", { class: "ic" }, icon(b.icon, 26)),
      h("div", {},
        h("div", { class: "sub", text: s.riskLevel }),
        h("h2", { class: "label m0", id: "result-heading", tabindex: "-1", text: r.band_label }),
        h("div", { class: "sub", text: `${s.stage}: ${r.stage_label}` }))),
    h("p", { class: "summary", text: r.summary }),
    h("div", { class: "meter", "aria-hidden": "true" }, [0, 1, 2, 3].map((i) => h("span", { class: i <= b.idx ? "on" : "" }))),
    h("div", { class: "meter-labels", "aria-hidden": "true" }, s.severityScale.map((x) => h("span", { text: x }))),
    canSpeak ? h("button", { class: "btn listen", type: "button", "aria-pressed": String(state.speaking), onclick: toggleSpeak },
      icon("speaker"), state.speaking ? s.stopListening : s.listen) : null,
    state.voiceMsg ? h("p", { role: "alert", text: state.voiceMsg }) : null,
  );
}

function finding(f, open) {
  const s = t();
  return h("details", { class: "finding", open: open ? "" : null },
    h("summary", {}, h("span", { text: f.title }), h("span", { class: `tag ${f.severity}`, text: f.severity_label })),
    h("div", { class: "body" },
      h("p", { text: f.detail }),
      f.evidence && f.evidence.length ? h("div", { class: "quote" }, s.evidence + " ", f.evidence.map((e) => `“${e}”`).join("  ")) : null));
}

function whyPanel(r) {
  const s = t();
  const list = (items, render) => items.length ? h("ul", {}, items.map(render)) : h("p", { class: "muted", text: s.none });
  return h("section", { class: "why", "aria-labelledby": "why-h" },
    h("h2", { id: "why-h", class: "mt14", text: s.whyNot }),
    h("h3", { text: s.seenIn }), list(r.seen_in_message, (f) => h("li", { text: f.title })),
    h("h3", { text: s.unverified }), list(r.unverified_claims, (f) => h("li", { text: f.title })),
    h("h3", { text: s.couldNot }), list(r.could_not_check, (x) => h("li", { text: x })),
    (r.notes || []).length ? h("div", {}, r.notes.map((n) => h("p", {}, h("strong", { text: n.title + ". " }), n.detail))) : null);
}

function entitiesPanel(r) {
  const s = t(), e = r.entities || {};
  const rows = [];
  const add = (label, arr) => arr && arr.length && rows.push(h("div", { class: "kv" }, h("strong", { text: label }), arr.map((x) => h("span", { text: x }))));
  add(s.links, e.links); add(s.phones, e.phones); add(s.upi, e.upi_ids); add(s.handles, e.handles);
  add(s.sebiNums, (e.sebi_numbers || []).map((n) => `${n.value} (${n.format_ok ? s.formatOk : s.formatBad})`));
  if (!rows.length) return null;
  return h("details", { class: "finding" }, h("summary", {}, h("span", { text: s.details })), h("div", { class: "body" }, rows));
}

function sebiPanel(r) {
  const s = t(), nums = (r.entities && r.entities.sebi_numbers) || [];
  const claimed = [...(r.seen_in_message || []), ...(r.unverified_claims || [])].some((f) => String(f.id).startsWith("SEBI_"));
  if (!nums.length && !claimed) return null;
  const row = (label, value) => h("div", { class: "kv" }, h("strong", { text: label }), h("span", { text: value }));
  return h("section", { class: "card mt16", "aria-labelledby": "sebi-h" },
    h("h2", { id: "sebi-h", class: "m0", text: s.sebiTitle }),
    nums.length ? nums.map((n) => row(s.sebiFormatLabel, `${n.value}: ${n.format_ok ? s.formatOk : s.formatBad}`)) : row(s.sebiFormatLabel, s.sebiNoNumber),
    row(s.sebiOfficialLabel, s.sebiNotChecked),
    h("p", { class: "muted", text: s.sebiHow }),
    h("a", { class: "btn", href: "https://www.sebi.gov.in/intermediaries.html", target: "_blank", rel: "noopener noreferrer" }, icon("link", 20), s.sebiButton));
}

// Where the message seems to come from. Always a guess; the server says "unknown" when unsure.
function sourcePanel(r) {
  const src = r.source;
  if (!src) return null;
  const known = src.id !== "unknown";
  return h("section", { class: `source ${known ? "known" : "unknown"}`, "aria-labelledby": "src-h" },
    h("h2", { id: "src-h", class: "m0", text: src.title }),
    h("p", { class: "src-label", text: src.label }),
    known ? h("p", { class: "muted m0", text: `${src.basis_label} ${src.note}` }) : null,
    known ? h("p", { class: "src-tip", text: src.tip }) : null);
}

// Used if /api/config could not be fetched, so the help list still shows on the home screen.
const FALLBACK_HELPLINES = [
  { id: "cyber1930", value: "1930", href: "tel:1930" },
  { id: "cybercrime", value: "cybercrime.gov.in", href: "https://cybercrime.gov.in" },
  { id: "scores", value: "scores.sebi.gov.in", href: "https://scores.sebi.gov.in" },
  { id: "sebi", value: "sebi.gov.in", href: "https://www.sebi.gov.in" },
];

function helplinesGrid(list) {
  const s = t();
  return h("div", { class: "helplines" }, list.map((x) =>
    h("a", { class: "help-card", href: x.href, ...(x.href.startsWith("http") ? { target: "_blank", rel: "noopener noreferrer" } : {}) },
      h("span", { class: "help-ic" }, icon(x.href.startsWith("tel") ? "phone" : "link", 20)),
      h("span", { class: "help-txt" }, h("strong", { text: s.helplines[x.id] || x.id }), h("span", { text: x.value })))));
}

// Shows what was undone before checking (spaced letters, look-alike letters, native digits ...).
function normalizationPanel(r) {
  const nz = r.normalization;
  if (!nz) return null;
  return h("details", { class: "finding norm", open: "" },
    h("summary", {}, h("span", { text: nz.title })),
    h("div", { class: "body" },
      h("p", { class: "muted", text: nz.intro }),
      h("ul", { class: "norm-steps" }, nz.steps.map((x) => h("li", {},
        h("span", { text: x.label }),
        x.before || x.after ? h("span", { class: "norm-ex" }, h("code", { text: x.before }), " → ", h("code", { text: x.after })) : null))),
      h("div", { class: "norm-compare" },
        h("div", {}, h("strong", { text: nz.original_label }), h("pre", { class: "extracted", text: nz.original })),
        h("div", {}, h("strong", { text: nz.cleaned_label }), h("pre", { class: "extracted", text: nz.cleaned })))));
}

function resultView() {
  const s = t(), r = state.result;
  const inp = r.input || {};
  const urgent = (r.band === "high" || r.band === "critical") && (r.stage === "payment_request" || r.stage === "recovery");
  const doReport = async () => { try { await downloadReport(r, state.lang); } catch (e) { state.error = e.code || "generic"; render(); } };
  return h("section", { class: "result-page", "aria-label": s.resultTitle },
    h("div", { class: "result-bar" },
      h("button", { class: "btn btn-quiet back", type: "button", onclick: back }, icon("back", 20), s.back),
      h("div", { class: "bar-actions" },
        h("button", { class: "btn", type: "button", onclick: doReport }, icon("download", 20), s.report),
        h("button", { class: "btn btn-solid", type: "button", onclick: reset }, icon("refresh", 20), s.another))),
    bandCard(r),
    urgent ? h("section", { class: "pause", role: "note" }, h("h2", { text: s.pauseTitle }), h("p", { text: s.pauseBody })) : null,
    h("div", { class: "split result" },
      h("div", { class: "col-main" },
        h("h2", { text: s.doNow }),
        h("ol", { class: "actions-list" }, r.actions.map((a) => h("li", { text: a.text }))),
        h("h2", { text: s.helplinesTitle }),
        helplinesGrid(r.helplines),
        h("div", { class: "stack mt16" },
          h("button", { class: "btn", type: "button", onclick: shareTrust }, icon("link", 20), s.trustButton),
          h("p", { class: "muted", text: s.trustHelp }),
          state.trustMsg ? h("p", { role: "status", class: "muted", text: state.trustMsg }) : null,
          h("p", { class: "muted", text: s.reportHelp }))),
      h("div", { class: "col-side" },
        sourcePanel(r),
        r.seen_in_message.length ? [h("h2", { text: s.found }), r.seen_in_message.map((f, i) => finding(f, i < 3))] : null,
        r.unverified_claims.length ? r.unverified_claims.map((f) => finding(f, true)) : null,
        normalizationPanel(r),
        whyPanel(r),
        sebiPanel(r),
        entitiesPanel(r),
        inp.extracted_text ? h("details", { class: "finding mt10" },
          h("summary", {}, h("span", { text: s.extracted })),
          h("div", { class: "body" }, h("pre", { class: "extracted", text: inp.extracted_text }), h("p", { class: "muted", text: s.extractedHelp }))) : null)),
    h("p", { class: "muted mt16", text: inp.cloud_used ? s.cloudUsed : s.localOnly }),
    h("p", { class: "muted", text: r.disclaimer }),
  );
}

/* ---------------------------------------------------------------- render */
function render() {
  document.documentElement.lang = state.lang;
  if (state.big) document.documentElement.dataset.text = "large"; else delete document.documentElement.dataset.text;
  const keepScroll = window.scrollY;
  const s = t();
  root.replaceChildren(
    header(),
    state.view === "learn" ? learnView() : state.result && !state.busy ? resultView() : inputPanel(),
    h("p", { class: "muted footer", text: s.footer }),
  );
  if (state.busy) window.scrollTo({ top: keepScroll });
}

/* ------------------------------------------------------------ boot / PWA */
async function readSharedInbox() {
  if (!new URLSearchParams(location.search).has("shared") || !("caches" in window)) return;
  try {
    const inbox = await caches.open("rakshalens-share-inbox");
    const tx = await inbox.match("text");
    if (tx) state.text = (await tx.text()).slice(0, 8000);
    const im = await inbox.match("image");
    if (im) state.file = new File([await im.blob()], "shared.png", { type: im.headers.get("Content-Type") || "image/png" });
    await caches.delete("rakshalens-share-inbox"); // never kept
    history.replaceState({}, "", location.pathname);
  } catch { /* ignore */ }
}

(async function boot() {
  render();
  state.config = await getConfig();
  await readSharedInbox();
  render();
  if (state.text || state.file) { /* a shared message: let the user press Check */ }
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});
})();
