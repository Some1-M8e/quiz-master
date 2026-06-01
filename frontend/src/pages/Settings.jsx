import { useEffect, useState } from "react";
import { api } from "../api";

export default function Settings({ onNavigate }) {
  const [providers, setProviders] = useState([]);
  const [participants, setParticipants] = useState([]);
  const [events, setEvents] = useState([]);
  const [newProvider, setNewProvider] = useState({ name: "", url: "" });
  const [newParticipant, setNewParticipant] = useState({ name: "", email: "" });
  const [newEvent, setNewEvent] = useState({ title: "", event_date: "", capacity: 5, description: "", detail_url: "" });
  const [prüfMsg, setPrüfMsg] = useState("");
  const [inviteLink, setInviteLink] = useState("");
  const [copied, setCopied] = useState(false);
  const [editingEventId, setEditingEventId] = useState(null);

  const loadAll = () => {
    api.get("/providers").then(setProviders);
    api.get("/participants").then(setParticipants);
    api.get("/events").then(setEvents);
  };

  useEffect(() => { loadAll(); }, []);

  const addProvider = async () => {
    if (!newProvider.name || !newProvider.url) return;
    await api.post("/providers", newProvider);
    setNewProvider({ name: "", url: "" });
    loadAll();
  };

  const addParticipant = async () => {
    if (!newParticipant.name || !newParticipant.email) return;
    await api.post("/participants", newParticipant);
    setNewParticipant({ name: "", email: "" });
    loadAll();
  };

  const createEvent = async () => {
    if (!newEvent.title || !newEvent.event_date) return;
    await api.post("/events", newEvent);
    setNewEvent({ title: "", event_date: "", capacity: 5, description: "", detail_url: "" });
    loadAll();
  };

  const updateEvent = async (id) => {
    const event = events.find(e => e.id === id);
    if (!event) return;
    await api.put(`/events/${id}`, event);
    setEditingEventId(null);
    loadAll();
  };

  const deleteEvent = async (id) => {
    await api.delete(`/events/${id}`);
    loadAll();
  };

  const updateEventStatus = async (id, status) => {
    await api.put(`/events/${id}/status`, null, { status });
    loadAll();
  };

  const generateInvite = async () => {
    const res = await api.post("/admin/invite", {});
    const link = `${window.location.origin}/register/${res.token}`;
    setInviteLink(link);
    setCopied(false);
  };

  const copyLink = () => {
    navigator.clipboard.writeText(inviteLink);
    setCopied(true);
  };

  const runScraper = async () => {
    setPrüfMsg("Wird geprüft...");
    await api.post("/admin/scraper/run", {});
    setPrüfMsg("Fertig! Neue Termine wurden geprüft.");
    loadAll();
    setTimeout(() => onNavigate("events"), 2000);
  };

  return (
    <div>
      <Section title="Anbieter-Websites">
        {providers.map((p) => (
          <Row key={p.id} label={p.name} sub={p.url} onDelete={() => api.delete(`/providers/${p.id}`).then(loadAll)} />
        ))}
        <AddRow fields={[
          { placeholder: "Name (z.B. Pub Quiz Köln)", value: newProvider.name, onChange: (v) => setNewProvider({ ...newProvider, name: v }) },
          { placeholder: "URL der Website", value: newProvider.url, onChange: (v) => setNewProvider({ ...newProvider, url: v }) },
        ]} onAdd={addProvider} />
      </Section>

      <Section title="Quiz-Interessierte">
        {participants.map((p) => (
          <Row key={p.id} label={p.name} sub={p.email} onDelete={() => api.delete(`/participants/${p.id}`).then(loadAll)} />
        ))}
        <AddRow fields={[
          { placeholder: "Name", value: newParticipant.name, onChange: (v) => setNewParticipant({ ...newParticipant, name: v }) },
          { placeholder: "E-Mail", value: newParticipant.email, onChange: (v) => setNewParticipant({ ...newParticipant, email: v }) },
        ]} onAdd={addParticipant} />
      </Section>

      <Section title="Events (manuell erstellen)">
        {events.filter(e => e.source === "manual").map((e) => (
          <div key={e.id} style={{ border: "1px solid #e5e7eb", borderRadius: 8, padding: "0.75rem", marginBottom: "0.75rem" }}>
            {editingEventId === e.id ? (
              <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                <input placeholder="Titel" value={e.title} onChange={(v) => setEvents(events.map(x => x.id === e.id ? {...x, title: v} : x))} style={{ flex: 1, minWidth: 120, padding: "0.4rem" }} />
                <input type="datetime-local" value={e.event_date.slice(0, 16)} onChange={(v) => setEvents(events.map(x => x.id === e.id ? {...x, event_date: v + ":00"} : x))} style={{ flex: 1, minWidth: 150, padding: "0.4rem" }} />
                <input type="number" placeholder="Kapazität" value={e.capacity} onChange={(v) => setEvents(events.map(x => x.id === e.id ? {...x, capacity: parseInt(v)} : x))} style={{ width: 80, padding: "0.4rem" }} />
                <button onClick={() => updateEvent(e.id)} style={{ padding: "0.4rem 0.8rem", background: "#22c55e", color: "white", border: "none", borderRadius: 4, cursor: "pointer" }}>Speichern</button>
                <button onClick={() => setEditingEventId(null)} style={{ padding: "0.4rem 0.8rem", background: "#e5e7eb", border: "none", borderRadius: 4, cursor: "pointer" }}>Abbrechen</button>
              </div>
            ) : (
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <strong>{e.title}</strong>
                  <div style={{ color: "#6b7280", fontSize: "0.85rem" }}>{new Date(e.event_date).toLocaleDateString("de-DE")}</div>
                </div>
                <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                  <select value={e.status} onChange={(v) => updateEventStatus(e.id, v.target.value)} style={{ padding: "0.4rem", borderRadius: 4, border: "1px solid #d1d5db" }}>
                    <option value="neu">Neu</option>
                    <option value="gebucht">Gebucht</option>
                    <option value="abgesagt">Abgesagt</option>
                  </select>
                  <button onClick={() => setEditingEventId(e.id)} style={{ background: "none", border: "none", color: "#6366f1", cursor: "pointer", fontSize: "0.9rem" }}>Bearbeiten</button>
                  <button onClick={() => deleteEvent(e.id)} style={{ background: "none", border: "none", color: "#ef4444", cursor: "pointer", fontSize: "1.2rem" }}>×</button>
                </div>
              </div>
            )}
          </div>
        ))}
        <AddRow fields={[
          { placeholder: "Titel", value: newEvent.title, onChange: (v) => setNewEvent({ ...newEvent, title: v }) },
          { placeholder: "Datum & Zeit", value: newEvent.event_date, onChange: (v) => setNewEvent({ ...newEvent, event_date: v }) },
        ]} onAdd={createEvent} />
      </Section>

      <Section title="Einladungslink">
        <p style={{ color: "#6b7280", fontSize: "0.9rem", margin: "0 0 0.75rem 0" }}>
          Generiere einen Link, den du teilen kannst. Wer ihn öffnet, kann sich selbst eintragen.
          Ein neuer Link macht den alten ungültig.
        </p>
        <button onClick={generateInvite} style={{ padding: "0.6rem 1.2rem", background: "#6366f1", color: "white", border: "none", borderRadius: 8, cursor: "pointer" }}>
          Neuen Einladungslink generieren
        </button>
        {inviteLink && (
          <div style={{ marginTop: "0.75rem", display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
            <input readOnly value={inviteLink} style={{ flex: 1, padding: "0.4rem 0.6rem", border: "1px solid #d1d5db", borderRadius: 6, fontSize: "0.85rem", minWidth: 0 }} />
            <button onClick={copyLink} style={{ padding: "0.4rem 0.8rem", background: copied ? "#22c55e" : "#e5e7eb", color: copied ? "white" : "#374151", border: "none", borderRadius: 6, cursor: "pointer", whiteSpace: "nowrap" }}>
              {copied ? "Kopiert!" : "Kopieren"}
            </button>
          </div>
        )}
      </Section>

      <Section title="Aktionen">
        <button onClick={runScraper} style={{ padding: "0.6rem 1.2rem", background: "#6366f1", color: "white", border: "none", borderRadius: 8, cursor: "pointer" }}>
          Websites jetzt auf neue Termine prüfen
        </button>
        {prüfMsg && <p style={{ color: "#22c55e", marginTop: 8 }}>{prüfMsg}</p>}
      </Section>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div style={{ marginBottom: "2rem" }}>
      <h3 style={{ borderBottom: "2px solid #e5e7eb", paddingBottom: 4 }}>{title}</h3>
      {children}
    </div>
  );
}

function Row({ label, sub, onDelete }) {
  const [confirming, setConfirming] = useState(false);
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.5rem 0", borderBottom: "1px solid #f3f4f6" }}>
      <div><strong>{label}</strong><div style={{ color: "#6b7280", fontSize: "0.85rem" }}>{sub}</div></div>
      {confirming ? (
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
          <span style={{ fontSize: "0.85rem", color: "#374151" }}>Wirklich löschen?</span>
          <button onClick={() => { onDelete(); setConfirming(false); }}
            style={{ background: "#ef4444", color: "white", border: "none", borderRadius: 4, padding: "3px 10px", cursor: "pointer", fontSize: "0.85rem" }}>Ja</button>
          <button onClick={() => setConfirming(false)}
            style={{ background: "#e5e7eb", color: "#374151", border: "none", borderRadius: 4, padding: "3px 10px", cursor: "pointer", fontSize: "0.85rem" }}>Nein</button>
        </div>
      ) : (
        <button onClick={() => setConfirming(true)} style={{ background: "none", border: "none", color: "#ef4444", cursor: "pointer", fontSize: "1.2rem" }}>×</button>
      )}
    </div>
  );
}

function AddRow({ fields, onAdd }) {
  return (
    <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.75rem" }}>
      {fields.map((f, i) => (
        <input key={i} placeholder={f.placeholder} value={f.value} onChange={(e) => f.onChange(e.target.value)}
          style={{ flex: 1, padding: "0.4rem 0.6rem", border: "1px solid #d1d5db", borderRadius: 6 }} />
      ))}
      <button onClick={onAdd} style={{ padding: "0.4rem 1rem", background: "#6366f1", color: "white", border: "none", borderRadius: 6, cursor: "pointer" }}>+</button>
    </div>
  );
}
