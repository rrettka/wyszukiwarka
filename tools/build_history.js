#!/usr/bin/env node
// Buduje history.json (historia cen) z historii gita plików prices.json i prices_intl.json.
// Jeden punkt na dzień (najniższa cena dnia). Uruchamiać z katalogu repo: node tools/build_history.js
// To samo źródło importuje api/history.php przy pierwszym utworzeniu bazy SQLite.
const {execSync}=require("child_process"); const fs=require("fs");
const sh=c=>execSync(c,{encoding:"utf8",maxBuffer:64<<20,stdio:["ignore","pipe","ignore"]});
const day=ts=>new Date(ts*1000).toLocaleDateString("sv-SE",{timeZone:"Europe/Warsaw"}); // RRRR-MM-DD
const H={pl:{},intl:{}};
const put=(o,id,d,p)=>{ if(!(p>0)) return; const a=(o[id]=o[id]||{}); if(a[d]==null||p<a[d]) a[d]=p; };
function scan(file,fn){
  const revs=sh(`git log --format=%H,%ct -- ${file}`).trim().split("\n").filter(Boolean);
  for(const r of revs){ const [h,ct]=r.split(","); let j; try{ j=JSON.parse(sh(`git show ${h}:${file}`)); }catch(e){ continue; } fn(j,day(+ct)); }
  if(fs.existsSync(file)){ try{ fn(JSON.parse(fs.readFileSync(file,"utf8")),day(fs.statSync(file).mtimeMs/1000)); }catch(e){} }
}
scan("prices.json",(j,d)=>{
  for(const [id,v] of Object.entries(j.prices||{})) put(H.pl,id,d,Array.isArray(v)?v[0]:v);
  for(const a of j.add||[]) if(a&&a.id) put(H.pl,a.id,d,a.p);
});
scan("prices_intl.json",(j,d)=>{
  for(const [id,arr] of Object.entries(j.offers||{})) for(const o of arr||[]){ const k=id+"|"+o.m; put(H.intl,k,d,o.price); }
});
const pack=o=>Object.fromEntries(Object.entries(o).sort().map(([k,v])=>[k,Object.entries(v).sort()]));
const intl={}; for(const [k,v] of Object.entries(pack(H.intl))){ const [id,m]=k.split("|"); (intl[id]=intl[id]||{})[m]=v; }
const out={updated:new Date().toISOString().slice(0,10),note:"Najniższa cena dnia. pl: zł w Polsce; intl: cena lokalna w walucie rynku (bez dostawy).",pl:pack(H.pl),intl};
fs.writeFileSync("history.json",JSON.stringify(out));
const n=Object.values(out.pl).reduce((a,v)=>a+v.length,0);
console.log(`history.json: ${Object.keys(out.pl).length} modeli PL, ${n} punktów, ${Object.keys(intl).length} modeli z cenami zagranicznymi`);
