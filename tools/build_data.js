// Buduje data.js (paczka ładowana przez index.html) z plików źródłowych data/*.json.
// Użycie: node tools/build_data.js   (uruchamiać po każdej zmianie w data/)
"use strict";
const fs = require("fs"), path = require("path");
const dir = path.join(__dirname, "..", "data");
const rd = f => JSON.parse(fs.readFileSync(path.join(dir, f), "utf8"));
const wzt = rd("tests_wz.json"); delete wzt._opis;
const D = { series: rd("series.json"), models: rd("models.json"), offers: rd("offers.json"), tables: rd("tables.json"), wzt };
// kontrola spójności: każdy model ma serię i ofertę, identyfikatory są unikalne
const ids = new Set();
D.models.forEach(m => {
  if (ids.has(m.id)) throw new Error("powtórzone id: " + m.id); ids.add(m.id);
  if (!D.series[m.sr]) throw new Error("brak serii " + m.sr + " dla " + m.id);
  if (!D.offers[m.id]) throw new Error("brak oferty dla " + m.id);
});
Object.keys(D.offers).forEach(id => { if (!ids.has(id)) throw new Error("oferta bez modelu: " + id); });
const head = "/* Plik generowany przez tools/build_data.js z data/*.json – nie edytuj ręcznie. */\n";
fs.writeFileSync(path.join(__dirname, "..", "data.js"), head + "window.TVDATA=" + JSON.stringify(D) + ";\n");
// wersja w adresie pliku (skrót treści), żeby przeglądarki nie trzymały starej paczki
const out = head + "window.TVDATA=" + JSON.stringify(D) + ";\n";
const ver = require("crypto").createHash("sha1").update(out).digest("hex").slice(0, 10);
const ip = path.join(__dirname, "..", "index.html"), html = fs.readFileSync(ip, "utf8");
const html2 = html.replace(/<script src="data\.js(\?v=[^"]*)?"><\/script>/, `<script src="data.js?v=${ver}"></script>`);
if (html2 === html && !html.includes(`data.js?v=${ver}`)) throw new Error("nie znaleziono <script src=data.js> w index.html");
fs.writeFileSync(ip, html2);
console.log(`data.js: ${D.models.length} modeli, ${Object.keys(D.series).length} serii`);
