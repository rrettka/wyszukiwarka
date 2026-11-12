"""Buduje specs.json: dodatkowe parametry modeli z zapisanych źródeł.

Użycie: python3 specs/build_specs.py   (z katalogu głównego repozytorium)

Źródła (priorytet od najwyższego):
  1. wz   – test serii w wybierz.tv (specs/wz_data.py, data/tests_wz.json): pomiary i wyposażenie
  2. me   – karta produktu Media Expert (specs/me_data.json): wymiary, waga, VESA, pobór mocy, głośniki
  3. ce   – karta produktu Ceneo (specs/ce_data.py): tylko pola, których brak z wyższego źródła
Pole „fs” w rekordzie modelu zapisuje, z którego źródła pochodzi każda wartość (używa go strona
do poziomów wiarygodności A–D). Rozbieżności między sklepami trafiają do pola „konf”.
"""
import json, os, re, sys

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R, "specs"))
from wz_data import WZ  # noqa: E402
from ce_data import CE  # noqa: E402

rd = lambda p: json.load(open(os.path.join(R, p), encoding="utf-8"))
series, models, tests = rd("data/series.json"), rd("data/models.json"), rd("data/tests_wz.json")
prices = rd("prices.json")
tv = [{**series[m["sr"]], **m} for m in models] + list(prices.get("add", []))

out = {}
def put(x, k, v, src):
    x[k] = v; x.setdefault("fs", {})[k] = src

for d in tv:
    if not d.get("wz"):
        continue
    code = d["wz"].split("_")[-1]
    w, t = WZ.get(code), tests.get(code)
    if not w and not t:
        continue
    x = {}
    w = w or {}
    if "cr" in w: put(x, "cr", w["cr"], "wz")
    if "bf" in w:
        put(x, "de", f"{str(w['bf']).replace('.', ',')}/10", "wz"); put(x, "den", w["bf"], "wz")
    lag = (t or {}).get("lag") or {}
    il = lag.get("sdr60", lag.get("hdr60"))
    if il is not None: put(x, "il", il, "wz")
    if lag.get("hdr60") is not None: put(x, "ilh", lag["hdr60"], "wz")
    il120 = lag.get("sdr120", lag.get("hdr120"))
    if il120 is not None: put(x, "il120", il120, "wz")
    if lag.get("dv60") is not None: put(x, "ildv", lag["dv60"], "wz")
    if not lag:  # test bez tabeli input lagu – zostaje dawna wartość z wz_data
        if "il" in w: put(x, "il", w["il"], "wz")
        if "il120" in w: put(x, "il120", w["il120"], "wz")
    if w.get("vrr"):
        v = "VRR " + w["vrrz"].replace(" - ", "–").replace("Hz", " Hz") if w.get("vrrz") else "VRR"
        if w.get("gs"): v += ", G-Sync"
        put(x, "vrr", v, "wz")
    elif w.get("vrr") == 0:
        put(x, "vrr", "brak VRR", "wz")
    if "allm" in w: put(x, "allm", bool(w["allm"]), "wz")
    if "earc" in w: put(x, "earc", bool(w["earc"]), "wz")
    if w.get("opt"): put(x, "opt", True, "wz")
    if w.get("net"):
        put(x, "wifi", "tak", "wz"); put(x, "lan", True, "wz"); put(x, "btv", "tak", "wz")
    tt = w.get("tv")
    if tt:
        if tt == "ALL": put(x, "tun", "T2/C/S2", "wz")
        else: put(x, "tun", "/".join(p for p in ("T2", "C", "S2") if re.search(r"DVB-" + p + r"(,|$)", tt)), "wz")
    if w.get("ci"): put(x, "ci", True, "wz")
    if "atm" in w: put(x, "atm", bool(w["atm"]), "wz")
    if w.get("dtsx"): put(x, "dts", "DTS:X", "wz")
    s = w.get("stand")
    if s:
        st = {"Centralna": "centralna", "Nogi": "nóżki"}.get(s, s.lower())
        adj = w.get("standAdj")
        if adj and adj != "Stała": st += " (" + adj.lower() + ")"
        put(x, "st", st, "wz")
    x["src"] = "pomiary i wyposażenie: test serii w wybierz.tv; rodzaj podstawy wg testowanego rozmiaru"
    out[d["id"]] = x

ME = rd("specs/me_data.json")
vz = lambda v: re.sub(r"\s*x\s*", "×", v.strip()) if v else None
for i, m in ME.items():
    x = out.setdefault(i, {})
    if m.get("dim"): put(x, "dim", m["dim"], "me")
    if m.get("hs"): put(x, "hs", round(m["hs"] * 10), "me")
    if m.get("wt") is not None: put(x, "wt", m["wt"], "me")
    if m.get("wts") is not None and (m.get("wt") is None or m["wts"] >= m["wt"]): put(x, "wts", m["wts"], "me")
    if m.get("vesa"): put(x, "vesa", vz(m["vesa"]), "me")
    if m.get("ec"): put(x, "ec", m["ec"], "me")
    if m.get("pw") is not None: put(x, "pw", m["pw"], "me")
    if m.get("kh") is not None: put(x, "pwh", m["kh"], "me")
    if m.get("rms") is not None and m["rms"] >= 5: put(x, "rms", m["rms"], "me")
    if m.get("ch"): put(x, "ch", m["ch"].replace(" CH", "").replace("CH", ""), "me")
    if m.get("usb") is not None: put(x, "usb", int(m["usb"]), "me")
    x["src"] = (x.get("src", "") + "; " if x.get("src") else "") + "wymiary, waga, VESA, pobór mocy, głośniki: karta produktu Media Expert"

konf = 0
for i, v in CE.items():
    rms, ec, pw, vesa, usb, pid = v
    x = out.setdefault(i, {})
    used = False
    for k, val in (("rms", rms if rms is not None and rms >= 5 else None), ("ec", ec), ("pw", pw), ("vesa", vz(vesa) if vesa else None), ("usb", int(usb) if usb is not None else None)):
        if val is None or val == "": continue
        if k not in x:
            put(x, k, val, "ce"); used = True
        elif x[k] != val and x.get("fs", {}).get(k) == "me":
            x.setdefault("konf", {})[k] = f"Ceneo: {val}"; konf += 1
    if used:
        x["src"] = (x.get("src", "") + "; " if x.get("src") else "") + f"głośniki, pobór mocy, klasa, VESA: karta Ceneo ({pid})"

spec = {"updated": "12.11.2026",
        "note": "Dodatkowe parametry. Pomiary (kontrast, input lag, VRR/ALLM, eARC, Atmos, ocena barw) z testów wybierz.tv; wymiary, podstawa, VESA, złącza, dźwięk, energia z kart producentów – uzupełniane stopniowo. Tylko sprawdzone wartości; brak = brak pola. fs = źródło każdego pola (wz = test wybierz.tv, me = Media Expert, ce = Ceneo); konf = rozbieżne wartości z innego źródła.",
        "models": out}
json.dump(spec, open(os.path.join(R, "specs.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
cnt = lambda k: sum(1 for m in out.values() if k in m)
print(len(out), "modeli;", {k: cnt(k) for k in ["il", "ilh", "il120", "ildv", "dim", "wt", "vesa", "pw", "rms"]}, "rozbieżności sklepów:", konf)
