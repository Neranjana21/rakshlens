import en from "./en.js";
import ta from "./ta.js";
import hi from "./hi.js";

export const STR = { en, ta, hi };
export const LANGS = [
  { code: "en", name: "English" },
  { code: "ta", name: "தமிழ்" },
  { code: "hi", name: "हिन्दी" },
];
export const SPEECH = { en: "en-IN", ta: "ta-IN", hi: "hi-IN" };

export function guessLang() {
  const l = (navigator.language || "en").slice(0, 2).toLowerCase();
  return STR[l] ? l : "en";
}
