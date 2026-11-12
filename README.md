# Wyszukiwarka

Na razie: **Porównywarka TV 65″+** (strona główna).

Hosting: OVH Web Hosting (subdomena z HTTPS), wdrożenie przez funkcję Git w panelu OVH z gałęzi `main`.
Kolejne wyszukiwarki trafią do podkatalogów (np. `/auta`).

## Pliki

| Plik | Co zawiera | Kto zmienia |
| --- | --- | --- |
| `index.html` | strona (wygląd, wyszukiwanie, punktacja) | ręcznie |
| `data/series.json` | serie: cechy i pomiary wspólne dla wszystkich przekątnych serii | ręcznie |
| `data/models.json` | modele (warianty): seria, przekątna, nazwa i to, czym różnią się od serii | ręcznie |
| `data/offers.json` | bazowe oferty: cena, sklepy, link, status ceny | ręcznie |
| `data/tables.json` | linki do testów i recenzji, lista pominiętych modeli | ręcznie |
| `data.js` | paczka z `data/*.json` ładowana przez stronę | **generowany**: `node tools/build_data.js` |
| `prices.json` | codzienne ceny, poprawki i nowe modele (nadpisują dane bazowe) | zadanie codzienne |
| `specs.json` | dodatkowe parametry (kontrast, input lag, złącza, wymiary, pobór mocy…) | `specs/build_specs.py` |

Model na stronie = cechy serii + cechy własne modelu + oferta, potem poprawki z `prices.json` i parametry z `specs.json`.

## Zmiana danych

1. Edytuj `data/*.json`.
2. `node tools/build_data.js` (sprawdza spójność, buduje `data.js`, aktualizuje wersję w `index.html`).
3. Test regresji (niżej).

## Testy

```
python3 tests/snapshot.py <katalog_starej_wersji> /tmp/przed.json
python3 tests/snapshot.py . /tmp/po.json
python3 tests/porownaj.py /tmp/przed.json /tmp/po.json
```

Zrzut obejmuje wszystkie modele po załadowaniu, widok szczegółów każdego modelu, wszystkie kolumny, sortowania i 56 zapytań z `tests/zapytania.txt`. Każda różnica musi być zamierzona.

## Migracje i wycofanie

- `tools/migracja_001_wydziel_dane.js` – wydzielenie danych z `index.html` do `data/` (Etap 1).
- Wycofanie: `git checkout 024eded -- index.html` (ostatni commit przed Etapem 1) (wersja z danymi w kodzie strony działa bez `data/` i `data.js`).
