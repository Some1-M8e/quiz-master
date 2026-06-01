import { useEffect, useState } from "react";
import { api } from "../api";

export default function Settings({ onNavigate }) {
  const [providers, setProviders] = useState([]);
  const [participants, setParticipants] = useState([]);
  const [newProvider, setNewProvider] = useState({ name: "", url: "" });
  const [newParticipant, setNewParticipant] = useState({ name: "", email: "" });
  const [prüfMsg, setPrüfMsg] = useState("");

  const loadAll = () => {
    api.get("/providers").then(setProviders);
    api.get("/participants").then(setParticipants);
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
