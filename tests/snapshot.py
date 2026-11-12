"""Zrzut stanu strony do porównania przed/po zmianie (test regresji).

Użycie: python3 tests/snapshot.py <katalog_ze_stroną> <plik_wyjściowy.json>
Serwuje katalog lokalnie, ładuje index.html w Chrome (bez internetu),
zapisuje: komplet danych modeli po załadowaniu, tabele pomocnicze,
wynik każdego zapytania z tests/zapytania.txt, typowe sortowania,
polecane modele i porównanie.
"""
import json, subprocess, sys, time, os, socket
from playwright.sync_api import sync_playwright

root, out = sys.argv[1], sys.argv[2]
here = os.path.dirname(os.path.abspath(__file__))
queries = [l.strip() for l in open(os.path.join(here, "zapytania.txt"), encoding="utf-8") if l.strip()]

s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
srv = subprocess.Popen(["python3", "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=root,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(0.7)
res = {"errors": []}
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/usr/bin/google-chrome")
        pg = b.new_page(viewport={"width": 1400, "height": 900})
        pg.on("pageerror", lambda e: res["errors"].append(str(e)))
        pg.route("**/*", lambda r: r.continue_() if r.request.url.startswith(f"http://127.0.0.1:{port}") else r.abort())
        pg.goto(f"http://127.0.0.1:{port}/index.html")
        pg.wait_for_load_state("networkidle"); pg.wait_for_timeout(500)
        res["models"] = pg.evaluate("""()=>{const o={}; TV.forEach(d=>{const c={}; Object.keys(d).sort().forEach(k=>{ if(k!=="_hay") c[k]=d[k]; }); o[d.id]=c;}); return o;}""")
        res["order"] = pg.evaluate("TV.map(d=>d.id)")
        res["tables"] = pg.evaluate("({TK,YT,TESTS,EXCL,BRANDS})")
        res["calc"] = pg.evaluate("Object.fromEntries(TV.map(d=>[d.id,[score(d),val(d),vmv(d)]]))")
        res["default_rows"] = pg.evaluate("sorted(filtered()).map(d=>d.id)")
        res["picks"] = pg.inner_text("#picks")
        res["details"] = pg.evaluate("Object.fromEntries(TV.map(d=>[d.id,detailRow(d)]))")
        res["all_columns"] = pg.evaluate("""()=>{ const keep=[...HID]; HID.clear(); renderHead(); renderBody();
            const t=document.getElementById('tbody').innerText; keep.forEach(k=>HID.add(k)); renderHead(); renderBody(); return t; }""")
        res["body_text"] = pg.inner_text("#tbody")[:20000]
        sorts = {}
        for k in ["value", "vmv", "p", "cr", "il", "en", "dims", "s", "name"]:
            sorts[k] = pg.evaluate(f"(()=>{{const keep=st.sorts; st.sorts=[{{k:'{k}',dir:defDir('{k}')}}]; const r=sorted(filtered()).map(d=>d.id); st.sorts=keep; return r;}})()")
        res["sorts"] = sorts
        q = {}
        for t in queries:
            pg.fill("#q", t); pg.wait_for_timeout(300)
            q[t] = {"spec": pg.evaluate("q=>parseNL(q)", t),
                    "rows": pg.evaluate("sorted(filtered()).map(d=>d.id)"),
                    "box": pg.inner_text("#nlBox"),
                    "picks": pg.inner_text("#picks")}
        res["queries"] = q
        pg.fill("#q", ""); pg.wait_for_timeout(300)
        ids = pg.eval_on_selector_all("[data-cmp]", "x=>x.slice(0,4).map(e=>e.dataset.cmp)")
        for i in ids:
            pg.evaluate(f"document.querySelector('[data-cmp=\"{i}\"]').click()")
        pg.wait_for_timeout(200)
        res["compare"] = pg.inner_text("#cmpSec")
        b.close()
finally:
    srv.terminate()
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
print(f"modele: {len(res['models'])}, zapytania: {len(res['queries'])}, błędy JS: {len(res['errors'])}")
