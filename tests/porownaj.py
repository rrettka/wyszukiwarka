"""Porównuje dwa zrzuty z tests/snapshot.py i wypisuje każdą różnicę.
Użycie: python3 tests/porownaj.py przed.json po.json   (kod wyjścia 1 = są różnice)"""
import json, sys, difflib
A, B = (json.load(open(f, encoding="utf-8")) for f in sys.argv[1:3])
n = 0
def walk(a, b, p=""):
    global n
    if type(a) != type(b): n += 1; print("≠", p); return
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)): walk(a.get(k), b.get(k), p + "/" + str(k)[:50])
    elif isinstance(a, list):
        if len(a) != len(b): n += 1; print("≠ długość", p, len(a), "→", len(b)); return
        for i, (x, y) in enumerate(zip(a, b)): walk(x, y, f"{p}[{i}]")
    elif a != b:
        n += 1
        if isinstance(a, str) and len(a) > 120:
            d = [l[:160] for l in difflib.unified_diff(a.split("\n"), b.split("\n"), lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")]
            print("≠", p, *d[:6], sep="\n   ")
        else:
            print("≠", p, repr(a)[:80], "→", repr(b)[:80])
walk(A, B)
print(f"różnic: {n}; błędy JS przed/po: {len(A.get('errors', []))}/{len(B.get('errors', []))}")
sys.exit(1 if n or B.get("errors") else 0)
