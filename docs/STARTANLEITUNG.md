# Quiz-Master starten - Einfach erklärt

## Der sichere Weg (empfohlen)

Doppelklick auf: **`start.bat`**

Das Skript startet automatisch:
1. Das Backend (Server)
2. Prüft ob es läuft
3. Das Frontend (Benutzeroberfläche)

---

## Manueller Weg (falls Skript nicht funktioniert)

### Schritt 1: Backend starten
1. Öffne eine Eingabeaufforderung (cmd oder PowerShell)
2. Gehe zum Backend-Ordner:
   ```
   cd C:\Users\mwassmann\Projects\quiz-master\backend
   ```
3. Starte das Backend:
   ```
   python -m uvicorn main:app --host 0.0.0.0 --port 8000
   ```
4. Warte bis du "Uvicorn running on..." siehst

### Schritt 2: Frontend starten (in einem neuen Fenster)
1. Öffne ein neues Terminal-Fenster
2. Gehe zum Frontend-Ordner:
   ```
   cd C:\Users\mwassmann\Projects\quiz-master\frontend
   ```
3. Starte das Frontend:
   ```
   npm run dev
   ```
4. Warte bis du "Local: http://localhost:5173" siehst

### Schritt 3: App öffnen
- Öffne deinen Browser
- Gehe zu: http://localhost:5173

---

## Was tun wenn etwas nicht geht?

### Fehler: "Backend nicht erreichbar"
**Ursache:** Backend ist nicht gestartet oder Python fehlt

**Lösung:**
1. Prüfe ob Python installiert ist: `python --version`
2. Starte das Backend manuell (siehe Schritt 1 oben)
3. Schau in die Fehlermeldung im Backend-Fenster

### Fehler: "Datenbank-Fehler"
**Ursache:** Datenbank-Struktur ist veraltet

**Lösung:**
Die Datenbank wird jetzt automatisch aktualisiert. Wenn doch ein Fehler kommt:
1. Backend stoppen (Strg+C im Backend-Fenster)
2. Datenbank löschen: `del backend\quiz_master.db`
3. Backend neu starten (Datenbank wird neu erstellt)

### Fehler: "npm nicht gefunden"
**Ursache:** Node.js ist nicht installiert

**Lösung:**
Node.js installieren von: https://nodejs.org/

---

## Die wichtigsten URLs

| Was | Adresse |
|-----|---------|
| App (Frontend) | http://localhost:5173 |
| API (Backend) | http://localhost:8000 |
| API-Dokumentation | http://localhost:8000/docs |

---

## Wie die App funktioniert (einfach erklärt)

```
┌─────────────────┐      ┌─────────────────┐
│   Frontend      │─────▶│    Backend      │
│  (Browser)      │◄─────│    (Server)     │
│  Port 5173      │      │    Port 8000    │
└─────────────────┘      └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │   Datenbank     │
                         │  (SQLite-Datei) │
                         └─────────────────┘
```

1. **Frontend** zeigt die Oberfläche im Browser
2. **Backend** verarbeitet alle Anfragen (Teilnehmer hinzufügen, Events speichern, etc.)
3. **Datenbank** speichert alle Daten dauerhaft

Beide Teile müssen laufen damit die App funktioniert!
