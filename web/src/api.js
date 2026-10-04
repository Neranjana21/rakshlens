// API client. Base URL can be overridden by the extension / app wrappers.
const BASE = (typeof window !== "undefined" && window.RAKSHALENS_API) || "";

export class ApiError extends Error {
  constructor(code) {
    super(code);
    this.code = code;
  }
}

// Shrink big screenshots before upload: faster on slow networks, same OCR quality.
async function shrink(file, maxSide = 1600) {
  if (!file || file.size < 350 * 1024 || !window.createImageBitmap) return file;
  try {
    const bmp = await createImageBitmap(file);
    const scale = Math.min(1, maxSide / Math.max(bmp.width, bmp.height));
    const w = Math.round(bmp.width * scale);
    const hgt = Math.round(bmp.height * scale);
    const canvas = document.createElement("canvas");
    canvas.width = w;
    canvas.height = hgt;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, w, hgt);
    ctx.drawImage(bmp, 0, 0, w, hgt);
    const blob = await new Promise((res) => canvas.toBlob(res, "image/jpeg", 0.86));
    return blob && blob.size < file.size ? blob : file;
  } catch {
    return file;
  }
}

async function errorCode(res) {
  try {
    const j = await res.json();
    return (j.detail && j.detail.error) || j.error || "generic";
  } catch {
    return res.status === 429 ? "rate_limited" : res.status === 413 ? "too_large" : "generic";
  }
}

export async function getConfig() {
  try {
    const r = await fetch(`${BASE}/api/config`);
    return r.ok ? await r.json() : { cloud_available: false };
  } catch {
    return { cloud_available: false };
  }
}

export async function analyze({ text, file, lang, allowCloud }) {
  const fd = new FormData();
  fd.set("text", text || "");
  fd.set("lang", lang);
  fd.set("allow_cloud", allowCloud ? "true" : "false");
  if (file) fd.set("image", await shrink(file), "screenshot.jpg");
  let res;
  try {
    res = await fetch(`${BASE}/api/analyze`, { method: "POST", body: fd });
  } catch {
    throw new ApiError("offline");
  }
  if (!res.ok) throw new ApiError(await errorCode(res));
  return res.json();
}

export async function downloadReport(result, lang) {
  let res;
  try {
    res = await fetch(`${BASE}/api/report`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ result, lang }),
    });
  } catch {
    throw new ApiError("offline");
  }
  if (!res.ok) throw new ApiError("generic");
  const blob = new Blob([await res.text()], { type: "text/html" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "rakshalens-report.html";
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 5000);
}
