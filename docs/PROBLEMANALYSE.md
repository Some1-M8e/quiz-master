# Problemanalyse: Warum es ständig Fehler gab

## Zusammenfassung der aufgetretenen Probleme

### Problem 1: Backend war nicht gestartet
**Was passiert ist:** Du hast Buttons im Frontend geklickt, aber nichts hat funktioniert. Die E-Mails sagten "Failed to fetch".

**Warum:** Das Backend (der Server-Teil auf Port 8000) war nicht am Laufen. Nur das Frontend war erreichbar.

**Wie es passiert:** Beim Neustart der App wurde nur das Frontend gestartet, das Backend wurde übersehen oder der Start fehlgeschlagen.

---

### Problem 2: Datenbank-Schema-Drift
**Was passiert ist:** "table participants has no column named notifications_enabled"

**Warum:** Der Code wurde geändert (neues Feld `notifications_enabled` hinzugefügt), aber die vorhandene Datenbank-Datei (`quiz_master.db`) hatte diese Spalte nicht. Die Datenbank wurde nur beim allerersten Mal erstellt und nie aktualisiert.

**Wie es passiert:**
1. Woche 1: App wird gebaut, Datenbank erstellt mit `name` und `email` für Teilnehmer
2. Woche 2: Code wird erweitert, `notifications_enabled` wird im Code hinzugefügt
3. Datenbank-Datei bleibt unverändert alt
4. Beim Start versucht der Code, auf ein Feld zuzugreifen, das in der Datenbank nicht existiert

---

### Problem 3: Import-Fehler nach Code-Änderungen
**Was passiert ist:** "cannot import name 'InviteToken' from 'models'"

**Warum:** Ein Modell (`InviteToken`) wurde aus dem Code entfernt, aber an anderer Stelle (in `database.py`) wurde es noch importiert.

**Wie es passiert:** Bei der Bereinigung des Codes wurde `InviteToken` aus `models.py` gelöscht, aber `database.py` wurde vergessen.

---

### Problem 4: Pfad-Probleme (Windows vs. Linux)
**Was passiert ist:** "cd: C:Users...: No such file or directory"

**Warum:** Windows-Pfade mit Backslashes (`C:\Users\...`) wurden in einer Bash-Umgebung verwendet, die Unix-Pfade erwartet (`/c/Users/...`).

---

## Dauerhafte Lösungen

### Lösung 1: Automatisierte Datenbank-Migration
Die `init_db()` Funktion wurde erweitert. Sie prüft jetzt bei jedem Start:
- Existieren alle benötigten Spalten?
- Wenn nein: Füge sie hinzu (ALTER TABLE)
- Wenn nein (Tabelle fehlt): Erstelle sie

**Ergebnis:** Die Datenbank wird automatisch mit dem Code synchronisiert.

### Lösung 2: Start-Skript für beide Teile
Ein einziges Skript, das Backend UND Frontend startet.

### Lösung 3: Konsistenz-Check vor dem Start
Ein Skript, das prüft, ob alle Imports korrekt sind, bevor die App startet.

---

## Was du jetzt wissen musst

### Für den täglichen Betrieb:
1. **Backend zuerst starten**, dann Frontend
2. Bei Code-Änderungen: Datenbank wird automatisch aktualisiert
3. Bei Fehlern: Backend-Logs prüfen (Port 8000)

### Wenn etwas nicht funktioniert:
1. Ist das Backend auf Port 8000 erreichbar? (`curl http://localhost:8000/events`)
2. Ist das Frontend auf Port 5173 erreichbar?
3. Stehen Fehler im Backend-Log?

---

## Vermeidung in Zukunft

| Problemtyp | Wie verhindert |
|------------|----------------|
| Backend nicht gestartet | Start-Skript für beide Teile |
| Datenbank veraltet | Automatische Migration in `init_db()` |
| Import-Fehler | Konsistenz-Check vor Start |
| Pfad-Probleme | Immer relative Pfade oder Unix-Syntax |
