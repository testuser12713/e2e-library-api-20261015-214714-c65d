# Stadtbibliothek – Ausleih-API

Eine REST-API in Python für die Ausleihe einer kleinen Stadtbibliothek. Sie
verwaltet Bücher, Mitglieder und Ausleihen samt der fachlichen Regeln (höchstens
drei offene Ausleihen pro Mitglied, nur freie Exemplare sind ausleihbar, eine
Rückgabe schließt die Ausleihe, 14 Tage Leihfrist). Dazu kommen CRUD-Endpunkte,
eine Buchsuche mit Paginierung, eine Überfälligkeitsliste, einheitliche
Fehlerantworten und ein API-Key-Schutz für alle schreibenden Endpunkte.

## Technologie-Stack

- Python 3.13
- FastAPI mit Uvicorn als ASGI-Server
- Pydantic v2 für Validierung und Schemas
- SQLAlchemy 2.0 (typed Declarative) über SQLite
- pytest mit dem FastAPI-TestClient (httpx) gegen eine eigene Test-Datenbank

## Installation

Abhängigkeiten installieren:

```bash
python -m pip install -r requirements.txt
```

## Starten

Die Anwendung benötigt die Umgebungsvariable `LIBRARY_API_KEY`. Die
Datenbankdatei wird über die optionale Variable `LIBRARY_DB_PATH` gesetzt; ohne
Angabe wird `library.db` im Arbeitsverzeichnis verwendet. Das Schema wird beim
Start automatisch angelegt.

```bash
LIBRARY_API_KEY=<Schlüssel> LIBRARY_DB_PATH=library.db \
  python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Für die Entwicklungsumgebung können die Variablen aus `.env.example` übernommen
werden. Dort steht nur der Name `LIBRARY_API_KEY`, niemals ein Wert.

## Umgebungsvariablen

| Name | Pflicht | Beschreibung |
| --- | --- | --- |
| `LIBRARY_API_KEY` | ja | Schlüssel für alle schreibenden Aufrufe; ohne ihn startet die Anwendung nicht. |
| `LIBRARY_DB_PATH` | nein | Pfad zur SQLite-Datei, Standard `library.db`. |

## Verwendung

Interaktive Dokumentation: `/docs`. Die OpenAPI-Beschreibung liegt unter
`/openapi.json`. Der Endpunkt `/health` liefert `{"status": "ok"}` und
benötigt keinen Schlüssel.

Alle schreibenden Aufrufe – also jeder Aufruf mit den Methoden POST, PUT oder
DELETE – benötigen den HTTP-Header `X-API-Key`. Sein Wert ist der Inhalt der
Umgebungsvariablen `LIBRARY_API_KEY`. Lesende Aufrufe (GET) benötigen keinen
Schlüssel.

### Endpunkte

| Methode | Pfad | API-Key nötig |
| --- | --- | --- |
| POST | `/books` | ja |
| GET | `/books` | nein |
| GET | `/books/{book_id}` | nein |
| PUT | `/books/{book_id}` | ja |
| DELETE | `/books/{book_id}` | ja |
| POST | `/members` | ja |
| GET | `/members` | nein |
| GET | `/members/{member_id}` | nein |
| PUT | `/members/{member_id}` | ja |
| DELETE | `/members/{member_id}` | ja |
| POST | `/loans` | ja |
| POST | `/loans/{loan_id}/return` | ja |
| GET | `/loans/overdue` | nein |
| GET | `/health` | nein |

### Fehlerformat

Jede Fehlerantwort hat dieselbe Struktur: ein Objekt unter dem Schlüssel `error`
mit einem maschinenlesbaren `code`, einer Meldung `message` und optionalen
`details`. Validierungsfehler tragen die betroffenen Felder in `details`.

## Funktionen

- Bücher anlegen, lesen, ändern und löschen (nur ohne Ausleihbezug).
- Buchsuche mit case-insensitiver Teilstring-Suche in Titel und Autor, inklusive
  Paginierung und Gesamttrefferzahl.
- Mitglieder anlegen, lesen, ändern und löschen (nur ohne Ausleihbezug).
- Ausleihen mit 14 Tagen Leihfrist, höchstens drei offene Ausleihen pro Mitglied
  und nur bei freiem Exemplar.
- Rückgabe einer Ausleihe.
- Überfälligkeitsliste mit Buch- und Mitgliedsdaten.
- Einheitliches Fehlerformat für alle Fehlerfälle.
- API-Key-Schutz für alle schreibenden Endpunkte.

## Tests

```bash
python -m pytest -q
```

Die Tests laufen mit dem FastAPI-TestClient gegen eine eigene Test-Datenbank und
benötigen weder Netzwerk noch einen externen Server.
