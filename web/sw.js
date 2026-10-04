// App-shell cache so the page opens instantly on slow networks.
// API calls are NEVER cached: nothing a user submits is stored by the worker.
const CACHE = "rakshalens-shell-v16";
const SHELL = [
  "./", "index.html", "manifest.webmanifest", "icon.svg",
  "src/app.js", "src/dom.js", "src/api.js", "src/voice.js",
  "src/i18n/index.js", "src/i18n/en.js", "src/i18n/ta.js", "src/i18n/hi.js",
  "src/styles/tokens.css", "src/styles/base.css",
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim())
  );
});

// Web Share Target: the phone's Share menu POSTs a message/screenshot to /share.
// We park it in a throw-away cache for the few milliseconds it takes the page to
// read it, then the page deletes it. Nothing is sent to the server by this step.
async function handleShare(request) {
  const form = await request.formData();
  const inbox = await caches.open("rakshalens-share-inbox");
  await inbox.put("text", new Response([form.get("title"), form.get("text"), form.get("url")].filter(Boolean).join("\n")));
  const img = form.get("image");
  if (img && img.size) await inbox.put("image", new Response(img, { headers: { "Content-Type": img.type || "image/png" } }));
  return Response.redirect("./?shared=1", 303);
}

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method === "POST" && url.origin === location.origin && url.pathname.endsWith("/share")) {
    e.respondWith(handleShare(e.request));
    return;
  }
  if (e.request.method !== "GET" || url.origin !== location.origin || url.pathname.startsWith("/api/")) return;
  // stale-while-revalidate for the shell
  e.respondWith(
    caches.match(e.request).then((hit) => {
      const net = fetch(e.request)
        .then((res) => {
          if (res.ok) caches.open(CACHE).then((c) => c.put(e.request, res.clone()));
          return res;
        })
        .catch(() => hit);
      return hit || net;
    })
  );
});
