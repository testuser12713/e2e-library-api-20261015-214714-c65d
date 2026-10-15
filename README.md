# Stadtbibliothek — Buchausleih-REST-API

Diese REST-API verwaltet den Ausleihbetrieb einer kleinen Stadtbibliothek: Bücher,
Mitglieder und Ausleihen. Sie bietet vollständiges CRUD für Bücher und Mitglieder,
eine Buchsuche mit Paginierung, eine Überfälligkeitsliste sowie die fachlichen
Regeln (maximal drei offene Ausleihen pro Mitglied, nur freie Exemplare sind
ausleihbar, eine Rückgabe schließt die Ausleihe, 14 Tage Leihfrist). Alle
schreibenden Endpunkte sind mit einem API-Key geschützt; alle Fehlerantworten haben
dieselbe Struktur. Der Start legt das Datenbankschema automatisch an, sodass keine
manuelle Einrichtung nötig ist.

## Tech-Stack

- **Sprache:** Python 3.13
- **Webframework:** FastAPI mit Uvicorn als Server
- **Validierung:** Pydantic v2
- **ORM:** SQLAlchemy 2.0 (typed Declarative)
- **Datenbank:** SQLite (Datei)
- **Tests:** pytest mit dem FastAPI-TestClient (httpx)

## Installation

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## Starten (Entwicklung)

Der API-Key ist Pflicht. Ohne `LIBRARY_API_KEY` bricht der Start mit einer Meldung ab,
die den Variablennamen nennt.

```bash
export LIBRARY_API_KEY="mein-geheimer-schluessel"
export LIBRARY_DB_PATH="library.db"   # optional, Standard: library.db
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Starten (Produktion)

Es gibt keinen separaten Build-Schritt. Für den produktiven Betrieb denselben
Server ohne `--reload` hinter einem Prozessmanager starten:

```bash
export LIBRARY_API_KEY="mein-geheimer-schluessel"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Umgebungsvariablen

| Variable          | Pflicht | Standard      | Beschreibung                                   |
| ----------------- | ------- | ------------- | ---------------------------------------------- |
| `LIBRARY_API_KEY` | ja      | —             | Schlüssel für alle schreibenden Endpunkte.     |
| `LIBRARY_DB_PATH` | nein    | `library.db`  | Pfad der SQLite-Datei.                         |

Die Beispieldatei `.env.example` nennt nur `LIBRARY_API_KEY` ohne Wert.

## Verwendung

Die API ist unter `http://127.0.0.1:8000` erreichbar. Die interaktive Dokumentation
liegt unter `/docs`, das OpenAPI-Schema unter `/openapi.json`. GET-Endpunkte sind
ohne Schlüssel erreichbar; für POST, PUT und DELETE ist der Header
`X-API-Key: <LIBRARY_API_KEY>` nötig. Fehlerantworten haben immer die Form
`{"error": {"code": "...", "message": "...", "details": [...] }}`.

### Endpunkte

| Methode  | Pfad                       | Body / Query                                                | Erfolg                                                       |
| -------- | -------------------------- | ----------------------------------------------------------- | ------------------------------------------------------------ |
| `POST`   | `/books`                   | `{title, author, isbn, year, copies_total}`                 | `201` Buch                                                   |
| `GET`    | `/books`                   | `q`, `limit` (Standard 20, 1–100), `offset`                 | `200` `{items, total, limit, offset}`                        |
| `GET`    | `/books/{book_id}`         | —                                                           | `200` Buch                                                   |
| `PUT`    | `/books/{book_id}`         | `{title?, author?, isbn?, year?, copies_total?}`            | `200` Buch                                                   |
| `DELETE` | `/books/{book_id}`         | —                                                           | `200` `{id}`                                                 |
| `POST`   | `/members`                 | `{name, email, member_since?}`                              | `201` Mitglied                                               |
| `GET`    | `/members`                 | `limit`, `offset`                                           | `200` `{items, total, limit, offset}`                        |
| `GET`    | `/members/{member_id}`     | —                                                           | `200` Mitglied                                               |
| `PUT`    | `/members/{member_id}`     | `{name?, email?, member_since?}`                            | `200` Mitglied                                               |
| `DELETE` | `/members/{member_id}`     | —                                                           | `200` `{id}`                                                 |
| `POST`   | `/loans`                   | `{book_id, member_id}`                                      | `201` Ausleihe (`due_at` = `loaned_at` + 14 Tage)            |
| `POST`   | `/loans/{loan_id}/return`  | —                                                           | `200` Ausleihe mit gesetztem `returned_at`                   |
| `GET`    | `/loans/overdue`           | `limit`, `offset`                                           | `200` `{items, total, limit, offset}` mit Buch und Mitglied  |
| `GET`    | `/health`                  | —                                                           | `200` `{"status": "ok"}`                                     |

Beispiel für ein Buch:

```json
{
  "id": 1,
  "title": "Harry Potter",
  "author": "J. K. Rowling",
  "isbn": "978-0747532699",
  "year": 1997,
  "copies_total": 3,
  "copies_available": 2
}
```

Beispiel für eine schreibende Anfrage:

```bash
curl -X POST http://127.0.0.1:8000/books \
  -H "X-API-Key: mein-geheimer-schluessel" \
  -H "Content-Type: application/json" \
  -d '{"title":"Harry Potter","author":"J. K. Rowling","isbn":"978-0747532699","year":1997,"copies_total":3}'
```

### Fehlercodes

| HTTP | Code                | Bedeutung                                       |
| ---- | ------------------- | ----------------------------------------------- |
| 401  | `unauthorized`      | Fehlender oder falscher `X-API-Key`.            |
| 404  | `not_found`         | Unbekannte ID.                                  |
| 409  | `conflict`          | Doppelte ISBN/E-Mail oder Regelverletzung.      |
| 422  | `validation_error`  | Ungültiger Body (mit Feldangaben in `details`). |

## Tests

```bash
LIBRARY_API_KEY=test-key python -m pytest -q
```

Die Tests laufen gegen eine eigene temporäre Test-Datenbank und benötigen weder
Netzwerk noch einen externen Server.

## Funktionen

- CRUD für Bücher und Mitglieder inklusive Suche und Paginierung
- ISBN und E-Mail sind eindeutig (409 bei Dopplung)
- Ausleihe mit 14-tägiger Leihfrist und den Regeln zu freien Exemplaren und offenen Ausleihen
- Rückgabe setzt `returned_at` und gibt das Exemplar wieder frei
- Überfälligkeitsliste mit Buch- und Mitgliedsdaten
- Einheitliche Fehlerantworten mit maschinenlesbarem Code
- API-Key-Schutz für alle schreibenden Endpunkte
- Automatische Schema-Anlage beim Start
