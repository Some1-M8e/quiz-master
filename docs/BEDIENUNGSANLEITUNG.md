# Quiz-Master – Bedienungsanleitung

## Was ist Quiz-Master?

Quiz-Master ist eine App, die dich automatisch über neue Quiz-Abende informiert und deine Teilnahme verwaltet. Du musst nicht mehr selbst nach Quiz-Terminen suchen – die App macht das für dich.

---

## Hauptfunktionen

### 1. **Automatische Termin-Erkennung**
- Die App prüft alle 2 Stunden automatisch nach neuen Quiz-Abenden auf ausgewählten Websites
- **Termine werden sofort gebucht:** Sobald ein Termin bei der Pension Schmidt verfügbar ist, wird er automatisch für 5 Personen reserviert
- **Alle Termine werden angezeigt**: offene, ausverkaufte und abgesagte Events

### 2. **Einladung und RSVP**
- Alle eingetragenen Quiz-Interessierten erhalten eine **Einladungsmail** mit allen Details
- Du kannst direkt in der Mail oder in der App mit **Ja**, **Vielleicht** oder **Nein** antworten
- Du kannst angeben, ob du mit einer Begleitung kommst
- **Bestätigung-E-Mail** erhältst du sofort nach deiner Antwort

### 3. **Automatische Buchung und Stornierung**
- **Sofortige Buchung:** Wenn ein Termin bei der Pension verfügbar wird, wird er direkt für 5 Personen gebucht
- **Erste Prüfung (7 Tage vor Event):** Das System prüft, ob mindestens 4 feste Zusagen (Ja) vorliegen
  - **Bei ≥4 Ja:** Buchung bleibt bestehen → Buchungsbestätigung an alle
  - **Bei <4 Ja:** Buchung wird sofort storniert
- **Vielleicht-Erinnerung (7 Tage vor Event):** Vielleicht-Teilnehmer erhalten eine Erinnerung mit 48 Stunden Frist
- **Warn-E-Mail an Ja-Teilnehmer:** Wenn es Vielleicht-Stimmen gibt, die bei Nichtantwort zu einer Stornierung führen könnten
- **Zweite Prüfung (5 Tage vor Event / 48h nach Erinnerung):** Vielleicht-Antworten werden automatisch zu "Nein" umgewandelt
  - **Bei ≥4 Ja nach Umwandlung:** Buchung bleibt bestehen
  - **Bei <4 Ja nach Umwandlung:** Buchung wird storniert

### 4. **Erinnerungen**
- **Bei "Vielleicht":** Erinnerung 7 Tage vor dem Event mit 48 Stunden Frist zur finalen Entscheidung (automatische Umwandlung zu "Nein" bei ausbleibender Antwort)
- **1 Tag vorher:** Finale Erinnerung an den Quiz-Abend
- **Wöchentlich** (jeden Donnerstag): Erinnerung, falls du noch nicht geantwortet hast

### 5. **Abbestellen**
- Jeder E-Mail liegt ein Abbestell-Link bei
- Damit wirst du aus der Teilnehmerliste entfernt

---

## E-Mails, die du erhalten kannst

| E-Mail-Typ | Wann erhältst du sie? |
|------------|----------------------|
| **Einladung** | Bei neuem Quiz-Termin (automatisch gebucht) |
| **RSVP-Bestätigung** | Nach deiner Antwort (Ja/Vielleicht/Nein) |
| **Buchungs-Bestätigung** | 7 Tage vor dem Event (wenn ≥4 Ja-Stimmen) |
| **Warn-E-Mail** | 7 Tage vor dem Event (an Ja-Teilnehmer, wenn Maybe kritisch sind) |
| **Vielleicht-Erinnerung** | 7 Tage vor dem Event (mit 48h Frist) |
| **Stornierung** | Wenn der Termin abgesagt werden musste |
| **Willkommens-Mail** | Bei erster Registrierung |
| **Erinnerung** | 1 Tag vor dem Event |
| **Wöchentlicher Reminder** | Jeden Donnerstag (bei ausstehender Antwort) |

**Hinweis zur Event-Liste:** Alle Termine werden angezeigt – mit farbigem Status-Label:
- 🟡 **Offen** (gelb) – Termin ist noch buchbar / wenige Plätze verfügbar
- 🟢 **Gebucht** (grün) – Termin wurde erfolgreich gebucht
- 🔴 **Abgesagt** (rot) – Termin wurde storniert
- ⚫ **Ausverkauft** (grau) – Keine Plätze mehr verfügbar

**Hinweis:** Du kannst dich aus allen Benachrichtigungen abbestellen, indem du auf den Link am Ende einer E-Mail klickst.

---

## Für Admins (manuelle Event-Erstellung)

Falls du Events manuell erstellen möchtest:

1. Öffne die **Einstellungen** in der App
2. Scrolle zum Bereich **Event-Management**
3. Hier kannst du:
   - Neue Events erstellen
   - Bestehende Events bearbeiten
   - Status ändern (neu / gebucht / abgesagt)
   - Events löschen (nur manuell erstellte)
   - RSVPs von Teilnehmern bearbeiten

---

## Technische Details

- **Backend:** FastAPI (Python)
- **Frontend:** React/Vite
- **Datenbank:** SQLite
- **E-Mail-Versand:** SMTP (konfigurierbar)
- **Scheduler:** Automatisierte Jobs für Scraper, Booking, Reminders

---

## Starten der App

### Backend starten:
```bash
cd backend
python main.py
```
→ Läuft auf http://localhost:8000

### Frontend starten:
```bash
cd frontend
npm run dev
```
→ Läuft auf http://localhost:5173

---

## Häufige Fragen

**Q: Wie funktioniert die Buchung?**  
A: Sobald ein Termin bei der Pension Schmidt verfügbar wird, wird er automatisch für 5 Personen gebucht. Du musst nichts weiter tun – du erhältst einfach eine Einladungsmail.

**Q: Warum wird ein Event storniert?**  
A: Es gibt zwei Prüfungspunkte:
1. **7 Tage vor Event:** Wenn weniger als 4 feste Zusagen (Ja) vorliegen → sofortige Stornierung
2. **5 Tage vor Event (48h nach Maybe-Erinnerung):** Vielleicht-Antworten werden zu "Nein" umgewandelt. Wenn dann weniger als 4 Ja vorliegen → Stornierung

**Q: Was passiert bei "Vielleicht"?**  
A: Du erhältst sofort eine Bestätigung. 7 Tage vor dem Event bekommst du eine Erinnerung mit 48 Stunden Frist zur finalen Entscheidung. Ohne Antwort wird "Vielleicht" automatisch zu "Nein" konvertiert (5 Tage vor dem Event).

**Q: Kann ich mich abmelden?**  
A: Ja, jeder E-Mail liegt ein Abbestell-Link bei.

**Q: Warum steht in meiner RSVP-Bestätigung, dass die Buchung "schon" erfolgt ist?**  
A: Weil der Termin automatisch für 5 Personen gebucht wird, sobald er verfügbar ist – noch bevor jemand geantwortet hat.

**Q: Was ist eine Warn-E-Mail und wann erhalte ich sie?**  
A: Wenn du mit "Ja" geantwortet hast und es noch Vielleicht-Antworten gibt, die bei Nichtantwort zu einer Stornierung führen könnten, erhältst du eine Warn-E-Mail 7 Tage vor dem Event. Diese informiert dich über die aktuelle Situation und dass die Buchung gefährdet sein könnte.

---

## Version

Aktuelle Version: 1.0.0  
Letzte Aktualisierung: 05. Juni 2026
