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

## Wiarygodność danych (Etap 2)

- `data/tests_wz.json` – testy wybierz.tv: przekątne objęte testem, przekątne z inną matrycą, rozmiar testowanego egzemplarza (null = test go nie podaje), input lag SDR/HDR/Dolby Vision 60/120 Hz.
- `specs/build_specs.py` buduje `specs.json` z `specs/wz_data.py`, `data/tests_wz.json`, `specs/me_data.json`, `specs/ce_data.py`; pole `fs` = źródło każdej wartości, `konf` = rozbieżności sklepów.
- Poziomy na stronie: A pomiar tego rozmiaru · B producent / wyposażenie z testu · C pomiar z innego rozmiaru tej samej matrycy · D sklep lub deklaracja · X test innej matrycy. Brak danych nigdy nie jest liczony jako zero.

## Rynki i ceny (Etap 5)

- `data/markets.json` – rynki, stawki VAT, cło (CH/NO), szacowany transport do PL wg klasy rozmiaru, kursy NBP awaryjne (na żywo strona pobiera tabelę A z api.nbp.pl).
- `prices_intl.json` – oferty z UE/Schengen (cena brutto z lokalnym VAT) i z Kanady (CAD bez podatku), z linkiem, oznaczeniem modelu na rynku i informacją o wysyłce do PL; aktualizuje go zadanie codzienne.
- Tryby na stronie: Polska · Z dostawą do Polski (PL + UE + Schengen) · Kanada (cena lokalna). Nie mieszamy ceny lokalnej z ceną z dostawą do PL w jednym rankingu.

## Etap 6 – historia cen, zalety, porównanie w linku

- `api/history.php` – historia cen w SQLite (jeden plik, bez użytkownika i hasła). Baza leży poza katalogiem strony
  (`../tvdb_wyszukiwarka/ceny.sqlite`), a gdy się nie da – w `api/_db/` z blokadą dostępu. Nie ma zapisu z zewnątrz:
  przy zapytaniu skrypt sprawdza daty zmian `prices.json`, `prices_intl.json`, `history.json` i dopisuje najniższą cenę dnia.
  Przy pierwszym uruchomieniu importuje `history.json`.
- `history.json` – historia z gita: `node tools/build_history.js` (uruchamiać po każdej aktualizacji cen).
  Strona najpierw pyta `api/history.php`, a gdy go nie ma (artefakt na claude.ai) – czyta `history.json`.
- Szczegóły modelu: „Na tle klasy” (górne/dolne 20% w klasie rozmiaru) i „Historia ceny” (wykres, minimum, zmiana).
- Porównanie: „Słabsze strony”, „Zalety w swojej klasie rozmiaru”, „Najniższa cena w historii” i przycisk
  „Kopiuj link do tego porównania” (`#porownaj=id1,id2&profil=…&rynek=pl,eu`, przy własnych wagach także `&wagi=…`).
