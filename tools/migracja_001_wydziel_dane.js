// Migracja 001: wydziela dane modeli z index.html (wersja z danymi w kodzie) do data/*.json.
// Użycie: node tools/migracja_001_wydziel_dane.js <stary_index.html> <katalog_data>
// Wycofanie: git checkout etap0 -- index.html && usuń data/ i data.js (index.html z etap0 ma dane w sobie).
"use strict";
const fs = require("fs"), vm = require("vm"), path = require("path");
const [src, outDir] = process.argv.slice(2);
const lines = fs.readFileSync(src, "utf8").split("\n");
const a = lines.findIndex(l => l.startsWith("const TV = ["));
const b = lines.findIndex(l => l.startsWith("const NIT=1300;"));
const e0 = lines.findIndex(l => l.startsWith("const EXCL=["));
const e1 = lines.findIndex((l, i) => i > e0 && l.startsWith("];"));
if (a < 0 || b < 0 || e0 < 0 || e1 < 0) throw new Error("nie znaleziono bloku danych");
const code = lines.slice(a, b).join("\n") + "\n" + lines.slice(e0, e1 + 1).join("\n") +
  "\n;({TV,TK,YT,TESTS,EXCL,ALIAS,SERWZ})";
const R = vm.runInNewContext(code, {}, { filename: "dane.js" });

const OFFER = ["p", "ps", "pu", "pv"], OWN = ["id", "n", "s", "est"];
const same = (x, y) => JSON.stringify(x) === JSON.stringify(y);
const root = id => (R.ALIAS[id] ? root(R.ALIAS[id]) : id);
const slugOf = d => d.wz ? d.wz.replace(/.*\//, "") : null;

// seria = test wybierz.tv (ta sama linia i panel); bez testu = model źródłowy klonu
const groups = new Map();
R.TV.forEach(d => { const k = slugOf(d) || "m:" + root(d.id); if (!groups.has(k)) groups.set(k, []); groups.get(k).push(d); });
const series = {}, sidOf = {}, used = new Set();
for (const [k, ms] of groups) {
  let sid = k.startsWith("m:") ? k.slice(2) : k.replace(/_[A-Z0-9]{3}$/, "");
  if (used.has(sid)) sid = k.replace(/^m:/, ""); used.add(sid);
  const keys = Object.keys(ms[0]).filter(x => !OFFER.includes(x) && !OWN.includes(x) &&
    ms.every(m => Object.prototype.hasOwnProperty.call(m, x) && same(m[x], ms[0][x])));
  const attrs = {}; keys.forEach(x => attrs[x] = ms[0][x]);
  series[sid] = attrs; ms.forEach(m => sidOf[m.id] = sid);
}
const models = R.TV.map(d => {
  const o = { id: d.id, sr: sidOf[d.id] };
  Object.keys(d).forEach(x => { if (x !== "id" && !OFFER.includes(x) && !(x in series[sidOf[d.id]])) o[x] = d[x]; });
  return o;
});
const offers = {};
R.TV.forEach(d => { const o = {}; OFFER.forEach(x => { if (Object.prototype.hasOwnProperty.call(d, x)) o[x] = d[x]; }); offers[d.id] = o; });
const tables = { TK: R.TK, YT: R.YT, TESTS: R.TESTS, EXCL: R.EXCL };

const line = arr => "[\n" + arr.map(x => JSON.stringify(x)).join(",\n") + "\n]\n";
const obj = o => "{\n" + Object.entries(o).map(([k, v]) => JSON.stringify(k) + ":" + JSON.stringify(v)).join(",\n") + "\n}\n";
fs.mkdirSync(outDir, { recursive: true });
fs.writeFileSync(path.join(outDir, "series.json"), obj(series));
fs.writeFileSync(path.join(outDir, "models.json"), line(models));
fs.writeFileSync(path.join(outDir, "offers.json"), obj(offers));
fs.writeFileSync(path.join(outDir, "tables.json"), JSON.stringify(tables, null, 1) + "\n");
console.log(`modele: ${models.length}, serie: ${Object.keys(series).length}, oferty: ${Object.keys(offers).length}`);
