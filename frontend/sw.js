const CACHE_NAME = "opera-territorial-v3";
const CORE = ["./", "./index.html", "./css/main.css", "./css/theme-dark.css", "./js/main.js", "./js/mapa.js", "./js/kpis.js", "./js/graficos.js", "./js/tabela.js", "./js/upload.js", "./js/apmo.js", "./js/data/sample.js", "./vendor/leaflet/leaflet.css", "./vendor/leaflet/leaflet.js"];

self.addEventListener("install", (event) => { event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(CORE)).then(() => self.skipWaiting())); });
self.addEventListener("activate", (event) => { event.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET" || new URL(event.request.url).origin !== self.location.origin) return;
  event.respondWith(fetch(event.request).then((response) => { if (response.ok) { const copy = response.clone(); caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy)); } return response; }).catch(() => caches.match(event.request).then((cached) => cached || caches.match("./index.html"))));
});
