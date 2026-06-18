# Sicherung für neuen Laptop

## Was hier gesichert wurde

Diese Dateien **müssen** auf deinen neuen Laptop, bevor du die App starten kannst:

### 1. `.env` Datei (WICHTIG!)
- Enthält alle Geheimnisse: E-Mail-Passwort, GitLab-Token, Datenbank-URL
- Ohne diese Datei funktioniert die App nicht
- **Achtung:** Diese Datei darf NIEMALS in Git hochgeladen werden

### 2. `quiz_master.db` (optional)
- Deine Datenbank mit allen Events, Teilnehmern, RSVPs
- Wenn du diese nicht sicherst, ist die App leer auf dem neuen Laptop

---

## Was du auf dem neuen Laptop tun musst

1. **Repository clonen:**
   ```bash
   git clone https://gitlab.adesso-group.com/miriam.wassmann/miriam-test.git
   cd miriam-test
   ```

2. **`.env` Datei kopieren:**
   - Kopiere `.env` aus diesem Sicherungsordner nach `backend/.env`

3. **Datenbank kopieren (optional):**
   - Kopiere `quiz_master.db` aus diesem Sicherungsordner nach `backend/`
   - Oder lass die App eine neue Datenbank erstellen

4. **Dependencies installieren:**
   ```bash
   # Backend
   cd backend
   pip install -r requirements.txt
   
   # Frontend
   cd ../frontend
   npm install
   ```

5. **App starten:**
   ```bash
   # Terminal 1 - Backend
   cd backend
   python main.py
   
   # Terminal 2 - Frontend
   cd frontend
   npm run dev
   ```

---

## Was NICHT gesichert werden muss

Diese Dateien werden automatisch erstellt oder aus Git geladen:
- `__pycache__/` (Python Cache)
- `venv/` oder `.venv/` (Python Virtual Environment)
- `node_modules/` (Frontend Dependencies)
- `screenshots/` (Test-Screenshots)

---

## Sicherheitshinweis

Die `.env` Datei enthält **sensibile Daten** (Passwörter, Tokens):
- Sichere diese Datei nur auf vertrauenswürdigen Geräten
- Nicht teilen oder per E-Mail versenden
- Nach der Migration vom alten Laptop: sicher löschen

---

Erstellt am: 2026-06-18
Für: Miriam Waßmann - Laptop-Migration
