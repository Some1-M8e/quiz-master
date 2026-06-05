# Quiz-Master Prozess-Diagramme (Mermaid-Code)

Kopiere die Code-Blöcke und füge sie ein unter:
- **Mermaid Live Editor:** https://mermaid.live/
- **GitHub README:** Mit ```mermaid ... ``` umschließen
- **Notion:** Code-Block mit "Mermaid" wählen
- **VS Code:** Extension "Markdown Preview Mermaid Support"

---

## 1. Anmeldungsprozess (Event Booking)

```mermaid
flowchart TD
    Start([Start]) --> Scraper[Scraper findet neuen Termin]
    Scraper --> Save[Event in Datenbank speichern]
    Save --> Email[Einladungs-E-Mails an alle Teilnehmer senden]
    Email --> Wait[Warten auf Antworten]
    
    Wait --> Decision1{Teilnehmer<br/>antwortet?}
    Decision1 -->|Ja| SaveRSVP[RSVP speichern<br/>yes / no / maybe]
    Decision1 -->|Nein| Wait
    
    SaveRSVP --> Check7{7 Tage vergangen?}
    Check7 -->|Nein| Decision2{≥4 Ja-Antworten?}
    Check7 -->|Ja| Decision2
    
    Decision2 -->|Ja| Book[Event buchen<br/>erste 5 Personen]
    Decision2 -->|Nein| Wait
    
    Book --> Confirm[Bestätigungs-E-Mail senden]
    Confirm --> Reminder[Wöchentliche Reminder<br/>an Maybe + Keine Antwort]
    Reminder --> End1([Ende])
    
    Wait --> CheckCancel{Zu viele Absagen?}
    CheckCancel -->|Ja| Cancel[Event stornieren]
    CheckCancel -->|Nein| Wait
    Cancel --> End2([Ende])
```

---

## 2. Scraper-Prozess (Termin-Suche)

```mermaid
flowchart TD
    Start([Start - Täglich 6:00 Uhr]) --> LoadConfig[Provider-Konfiguration laden]
    LoadConfig --> LoopProviders{Nächster Provider?}
    
    LoopProviders -->|Ja| OpenURL[Website aufrufen]
    LoopProviders -->|Nein| CheckNew{Neue Termine?}
    
    OpenURL --> Extract[Termin-Daten extrahieren:<br/>Datum, Titel, Link]
    Extract --> Exists{Termin existiert?}
    
    Exists -->|Ja| LoopProviders
    Exists -->|Nein| CreateEvent[Event in DB speichern<br/>source=scraper, status=neu]
    CreateEvent --> SendInvite[Einladungs-E-Mail senden]
    SendInvite --> LoopProviders
    
    CheckNew -->|Ja| End1([Ende])
    CheckNew -->|Nein| End2([Ende])
```

---

## 3. RSVP-Prozess (Teilnahme-Bestätigung)

```mermaid
flowchart TD
    Start([Start]) --> Receive[Teilnehmer erhält Einladungs-Mail]
    Receive --> Click[Link klicken]
    Click --> Page[RsvPage öffnen]
    Page --> Choice{Antwort wählen}
    
    Choice -->|Ja| Yes[Ja + Begleitung angeben]
    Choice -->|Nein| Nein[Nein]
    Choice -->|Maybe| Maybe[Maybe]
    
    Yes --> SaveRSVP[RSVP speichern<br/>response=yes, companions=X]
    Nein --> SaveRSVP2[RSVP speichern<br/>response=no]
    Maybe --> SaveRSVP3[RSVP speichern<br/>response=maybe]
    
    SaveRSVP --> SendConfirm[Bestätigungs-Mail senden]
    SaveRSVP2 --> End1([Ende])
    SaveRSVP3 --> SendConfirm
    
    SendConfirm --> End2([Ende])
```

---

## 4. E-Mail-Versand-Prozess

```mermaid
flowchart TD
    Start([Start]) --> Trigger{Auslöser}
    
    Trigger -->|Neues RSVP| Type1[Bestätigungs-Mail]
    Trigger -->|Event gebucht| Type2[Buchungs-Bestätigung]
    Trigger -->|Event abgesagt| Type3[Stornierung-Mail]
    Trigger -->|1 Woche vorher| Type4[Erinnerung-Mail]
    Trigger -->|Donnerstag 8:00| Type5[Wöchentlicher Reminder]
    Trigger -->|Maybe nach 24h| Type6[Maybe-Konvertierung]
    
    Type1 --> CheckEnabled{Benachrichtigungen<br/>aktiviert?}
    Type2 --> CheckEnabled
    Type3 --> CheckEnabled
    Type4 --> CheckEnabled
    Type5 --> CheckEnabled
    Type6 --> CheckEnabled
    
    CheckEnabled -->|Ja| Send[E-Mail versenden]
    CheckEnabled -->|Nein| Skip[Überspringen]
    
    Send --> Log[Versand-Log speichern]
    Skip --> End([Ende])
    Log --> End
```

---

## 5. Admin-Event-Management

```mermaid
flowchart TD
    Start([Start]) --> Admin[Admin öffnet Settings]
    Admin --> Section[Event-Management Section]
    Section --> List[Manuelle Events auflisten]
    
    List --> Action{Aktion}
    
    Action -->|Bearbeiten| Edit[Event-Daten ändern<br/>Titel, Datum, Kapazität]
    Edit --> Save[Speichern]
    
    Action -->|Status ändern| Status[Status wählen:<br/>neu / gebucht / abgesagt]
    Status --> Save
    
    Action -->|Löschen| Delete[Event löschen<br/>nur manuelle Events]
    Delete --> Confirm{Bestätigen?}
    Confirm -->|Ja| Delete2[Löschen]
    Confirm -->|Nein| List
    Delete2 --> List
    
    Action -->|Neues Event| Create[Event erstellen]
    Create --> Save
    
    Save --> List
    List --> End([Ende])
```

---

## 6. Vollständiger System-Überblick

```mermaid
flowchart TD
    subgraph Scraper[Scraper - Täglich 6:00 Uhr]
        S1[Website prüfen] --> S2{Neuer Termin?}
        S2 -->|Ja| S3[Event speichern]
        S2 -->|Nein| S4[Beenden]
        S3 --> S5[Einladungs-Mails senden]
    end
    
    subgraph RSVP[RSVP-System]
        R1[Teilnehmer erhält Mail] --> R2[Antwort: Ja/Nein/Maybe]
        R2 --> R3[RSVP speichern]
        R3 --> R4{Benachrichtigungen<br/>aktiviert?}
        R4 -->|Ja| R5[Bestätigung-Mail]
        R4 -->|Nein| R6[Keine Mail]
    end
    
    subgraph Booking[Booking-System]
        B1{≥4 Ja-Antworten?} -->|Ja| B2[Event buchen<br/>erste 5 Personen]
        B1 -->|Nein| B3[Warten]
        B2 --> B4[Bestätigung senden]
        B3 --> B5{7 Tage vergangen?}
        B5 -->|Ja| B6[Event stornieren]
        B5 -->|Nein| B1
    end
    
    subgraph Reminder[Reminder-System]
        M1[Donnerstag 8:00] --> M2[Reminder an:<br/>Maybe + Keine Antwort]
        M3[1 Woche vorher] --> M4[Letzte Erinnerung]
    end
    
    Scraper --> RSVP
    RSVP --> Booking
    Reminder --> RSVP
```

---

## Quick-Start Anleitung

1. **Gehe zu:** https://mermaid.live/
2. **Kopiere** einen der Code-Blöcke oben
3. **Einfügen** in das linke Textfeld
4. **Diagramm erscheint automatisch** rechts
5. **Download:** Klick auf "Actions" → "Download PNG" oder "SVG"
