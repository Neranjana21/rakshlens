// Voice in (speech recognition) and out (speech synthesis), both done by the
// phone/browser. Production path: Bhashini ASR/TTS for better Indian-language
// coverage; the interface here is deliberately the same shape.
const Rec = typeof window !== "undefined" && (window.SpeechRecognition || window.webkitSpeechRecognition);

export const canListen = !!Rec;
export const canSpeak = typeof window !== "undefined" && "speechSynthesis" in window;

let rec = null;

export function startListening(lang, { onText, onEnd, onError }) {
  if (!Rec) return false;
  rec = new Rec();
  rec.lang = lang;
  rec.interimResults = false;
  rec.continuous = true;
  rec.onresult = (e) => {
    let out = "";
    for (let i = e.resultIndex; i < e.results.length; i++) if (e.results[i].isFinal) out += e.results[i][0].transcript + " ";
    if (out) onText(out.trim());
  };
  rec.onerror = (e) => onError && onError(e.error);
  rec.onend = () => onEnd && onEnd();
  try {
    rec.start();
  } catch (e) {
    onError && onError(String(e));
    return false;
  }
  return true;
}

export function stopListening() {
  try {
    rec && rec.stop();
  } catch {
    /* already stopped */
  }
}

export function hasVoice(lang) {
  if (!canSpeak) return false;
  const base = lang.slice(0, 2).toLowerCase();
  return speechSynthesis.getVoices().some((v) => v.lang.toLowerCase().startsWith(base));
}

export function speak(text, lang, onEnd) {
  if (!canSpeak) return false;
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = lang;
  u.rate = 0.92;
  u.onend = () => onEnd && onEnd();
  u.onerror = () => onEnd && onEnd();
  speechSynthesis.speak(u);
  return true;
}

export function stopSpeaking() {
  if (canSpeak) speechSynthesis.cancel();
}
