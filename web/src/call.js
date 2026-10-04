// Call simulator: plays a phone call against this server's real /api/ivr/* endpoints.
// The server answers with TwiML (the instructions a phone provider would speak). We read it,
// speak the <Say> lines with the browser's voices, and send back the key press or the message,
// exactly as a provider's webhook would. Nothing is stored.
import { h } from "./dom.js";

const $ = (s) => document.querySelector(s);
const token = new URLSearchParams(location.search).get("token");
const LANG_NAME = { en: "English", hi: "Hindi", ta: "Tamil" };

// Messages the "caller" can read out. Hindi and Tamil are written as speech-to-text would return them.
const EXAMPLES = {
  en: [
    ["Scam-style message", "Guaranteed 30 percent returns, pay 5000 fee to ravi at okaxis"],
    ["Ordinary message", "Your SIP of 3000 rupees will be debited on 7 October, please keep enough balance"],
  ],
  hi: [
    ["Scam-style message", "गारंटीड मुनाफ़ा, पहले 1000 रुपये जमा करें और टेलीग्राम ग्रुप से जुड़ें"],
    ["Ordinary message", "आपकी SIP की किस्त 3000 रुपये 7 अक्टूबर को आपके बैंक खाते से कटेगी"],
  ],
  ta: [
    ["Scam-style message", "உத்தரவாத லாபம், முதலில் 2000 ரூபாய் செலுத்துங்கள், டெலிகிராம் குழுவில் சேருங்கள்"],
    ["Ordinary message", "உங்கள் வங்கிக் கணக்கில் ரூ 12,000 வரவு வைக்கப்பட்டுள்ளது"],
  ],
};

const WHY = [
  [/\/start/, "The phone provider tells us a call has started. We reply with the language menu to speak."],
  [/\/lang/, "The caller pressed a key. We reply with the prompt in the chosen language."],
  [/\/result/, "The provider turned the caller's speech into text and sent it. We ran the same rules as the app and reply with the verdict to speak."],
];

let callId = 0;          // bumped on every call and hang-up, so an old flow stops quietly
let pendingKey = null;   // resolver while we wait for a key press
let pendingSay = null;   // resolver while we wait for the spoken message
let timer = null;
let seconds = 0;
const noVoice = new Set();

/* ------------------------------------------------------------------ voices */
function pickVoice(lang) {
  if (!("speechSynthesis" in window)) return null;
  const l = lang.toLowerCase();
  const voices = speechSynthesis.getVoices();
  return voices.find((v) => v.lang.toLowerCase().replace("_", "-") === l)
    || voices.find((v) => v.lang.toLowerCase().startsWith(l.slice(0, 2))) || null;
}

function updateVoiceNote() {
  const missing = ["hi", "ta"].filter((c) => !pickVoice(c));
  const note = $("#voice-note");
  note.textContent = !("speechSynthesis" in window)
    ? "This browser cannot speak, so the answers are shown as text only."
    : missing.length
      ? `No ${missing.map((c) => LANG_NAME[c]).join(" or ")} voice found on this device, so those answers are shown as text only. Chrome on Android and Edge on Windows usually have them.`
      : "Voices are the browser's own, not a phone line. A real line uses the provider's voices.";
}

function speak(text, lang, id) {
  return new Promise((resolve) => {
    const estimate = Math.max(1300, text.length * 55);
    const v = pickVoice(lang);
    if (!v || id !== callId) { noVoice.add(lang.slice(0, 2)); setTimeout(resolve, id === callId ? estimate : 0); return; }
    const u = new SpeechSynthesisUtterance(text);
    u.voice = v; u.lang = v.lang; u.rate = 0.95;
    let done = false;
    const finish = () => { if (!done) { done = true; resolve(); } };
    u.onend = finish; u.onerror = finish;
    setTimeout(finish, estimate * 3 + 4000); // some browsers never fire onend
    speechSynthesis.speak(u);
  });
}

/* -------------------------------------------------------------- transcript */
function scrollDown() { const t = $("#transcript"); t.scrollTop = t.scrollHeight; }

function addBubble(kind, text, label) {
  const b = h("div", { class: `bubble ${kind}` }, label ? h("small", { text: label }) : null, text);
  $("#transcript").append(b);
  scrollDown();
  return b;
}

async function say({ text, lang }, id) {
  if (id !== callId) return;
  const code = lang.slice(0, 2);
  const b = addBubble("sys speaking", text, `RakshaLens · ${LANG_NAME[code] || code}`);
  await speak(text, lang, id);
  b.classList.remove("speaking");
}

/* ------------------------------------------------------------ behind the scenes */
function addLog(url, form, status, xml) {
  $("#log-empty").classList.add("hidden");
  const why = (WHY.find(([rx]) => rx.test(url)) || [, ""])[1];
  const fields = Object.entries(form);
  $("#log").append(h("li", {},
    h("div", { class: "req" },
      h("span", { class: "method", text: "POST" }),
      h("code", { text: url.replace(/token=[^&]+/, "token=…") }),
      h("span", { class: "code", text: String(status) })),
    fields.length ? h("p", { class: "sent" }, h("strong", { text: "Sent: " }), fields.map(([k, v]) => `${k} = ${v}`).join("   ")) : null,
    h("p", { class: "why", text: why }),
    h("details", {}, h("summary", { text: "What the server replied (TwiML)" }), h("pre", { text: xml.replace(/token=[^&"<]+/g, "token=…").replace(/></g, ">\n<") }))));
  $("#log li:last-child").scrollIntoView({ block: "nearest", behavior: "smooth" });
}

async function post(url, form) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams(form),
  });
  const text = await res.text();
  addLog(url, form, res.status, text);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return new DOMParser().parseFromString(text, "text/xml");
}

/* ------------------------------------------------------------------- input */
function askKey(id) {
  return new Promise((resolve) => {
    if (id !== callId) return resolve(null);
    const pad = $("#keypad");
    pad.classList.remove("disabled");
    pad.classList.add("waiting");
    pendingKey = (d) => { pad.classList.add("disabled"); pad.classList.remove("waiting"); pendingKey = null; resolve(d); };
  });
}

function askSpeech(lang, id) {
  return new Promise((resolve) => {
    if (id !== callId) return resolve(null);
    const code = lang.slice(0, 2);
    const panel = $("#say-panel");
    const box = $("#said");
    box.value = "";
    const row = $("#examples");
    row.replaceChildren(...(EXAMPLES[code] || EXAMPLES.en).map(([label, text]) =>
      h("button", { type: "button", onclick: () => { box.value = text; box.focus(); }, text: label })));
    panel.classList.remove("hidden");
    $("#keypad").classList.add("hidden");
    $("#mic").classList.toggle("hidden", !Recognition);
    $("#mic").dataset.lang = lang;
    box.focus();
    pendingSay = () => {
      const text = box.value.trim();
      if (!text) { box.focus(); return; }
      panel.classList.add("hidden");
      $("#keypad").classList.remove("hidden");
      pendingSay = null;
      resolve(text);
    };
  });
}

const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition || null;
let recognising = null;
function toggleMic() {
  const btn = $("#mic");
  if (recognising) { recognising.stop(); return; }
  const r = new Recognition();
  r.lang = btn.dataset.lang || "en-IN";
  r.interimResults = false;
  r.onresult = (e) => { $("#said").value = e.results[0][0].transcript; };
  r.onend = () => { recognising = null; btn.textContent = "Speak"; };
  r.onerror = () => { recognising = null; btn.textContent = "Speak"; };
  recognising = r;
  btn.textContent = "Listening… tap to stop";
  r.start();
}

/* ---------------------------------------------------------------- the call */
function tick() {
  seconds += 1;
  $("#timer").textContent = `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
}

function setStatus(text, live = false) {
  const s = $("#status");
  s.textContent = text;
  s.classList.toggle("live", live);
}

function endCall(message) {
  clearInterval(timer);
  callId += 1;
  if ("speechSynthesis" in window) speechSynthesis.cancel();
  if (recognising) recognising.stop();
  if (pendingKey) { const k = pendingKey; pendingKey = null; k(null); }
  if (pendingSay) pendingSay = null;
  $("#keypad").classList.add("disabled");
  $("#keypad").classList.remove("waiting");
  $("#say-panel").classList.add("hidden");
  $("#keypad").classList.remove("hidden");
  $("#end").classList.add("hidden");
  $("#call").classList.remove("hidden");
  $("#call").textContent = "Call again";
  setStatus("Call ended");
  if (message) addBubble("note", message);
}

async function turn(url, form, id) {
  const doc = await post(url, form);
  if (id !== callId) return;
  const kids = [...doc.documentElement.children];
  const sayOf = (n) => ({ text: n.textContent.trim(), lang: n.getAttribute("language") || "en-IN" });
  const gather = kids.find((k) => k.tagName === "Gather");

  if (gather) {
    for (const s of [...gather.children].filter((c) => c.tagName === "Say")) await say(sayOf(s), id);
    if (id !== callId) return;
    const action = gather.getAttribute("action");
    const lang = gather.getAttribute("language") || "en-IN";
    if ((gather.getAttribute("input") || "dtmf").includes("speech")) {
      const text = await askSpeech(lang, id);
      if (text == null || id !== callId) return;
      addBubble("me", text, "Caller says");
      await turn(action, { SpeechResult: text }, id);
    } else {
      const digit = await askKey(id);
      if (digit == null || id !== callId) return;
      addBubble("me", `Pressed ${digit}`, "Caller");
      await turn(action, { Digits: digit }, id);
    }
    return;
  }
  for (const n of kids) {
    if (id !== callId) return;
    if (n.tagName === "Say") await say(sayOf(n), id);
    else if (n.tagName === "Redirect") { await turn(n.textContent.trim(), {}, id); return; }
    else if (n.tagName === "Hangup") { endCall("RakshaLens ended the call."); return; }
  }
  if (id === callId) endCall("The call ended.");
}

async function startCall() {
  callId += 1;
  const id = callId;
  clearInterval(timer);
  seconds = 0;
  $("#timer").textContent = "00:00";
  $("#transcript").replaceChildren();
  $("#log").replaceChildren();
  $("#log-empty").classList.remove("hidden");
  $("#call").classList.add("hidden");
  $("#end").classList.remove("hidden");
  setStatus("Dialling…");
  await new Promise((r) => setTimeout(r, 700));
  if (id !== callId) return;
  setStatus("Connected", true);
  timer = setInterval(tick, 1000);
  try {
    await turn("/api/ivr/start" + (token ? `?token=${encodeURIComponent(token)}` : ""), {}, id);
  } catch (e) {
    if (id === callId) endCall("Could not reach the server (or the token is wrong). Is the app running?");
  }
}

/* -------------------------------------------------------------------- boot */
$("#call").addEventListener("click", startCall);
$("#end").addEventListener("click", () => endCall("You hung up."));
$("#send").addEventListener("click", () => pendingSay && pendingSay());
$("#mic").addEventListener("click", toggleMic);
$("#keypad").addEventListener("click", (e) => {
  const key = e.target.closest("button")?.dataset.key;
  if (key && pendingKey) pendingKey(key);
});
document.addEventListener("keydown", (e) => {
  if (pendingKey && /^[0-9*#]$/.test(e.key) && document.activeElement?.tagName !== "TEXTAREA") pendingKey(e.key);
});
if ("speechSynthesis" in window) speechSynthesis.addEventListener("voiceschanged", updateVoiceNote);
updateVoiceNote();
