import { useEffect, useState } from "react";
import { api } from "../api";

export default function Settings({ onNavigate }) {
  const [participants, setParticipants] = useState([]);
  const [newParticipant, setNewParticipant] = useState({ name: "", email: "" });
  const [copied, setCopied] = useState(false);

  const loadAll = () => {
    api.get("/participants").then(setParticipants).catch((err) => {
      console.error("Failed to load participants:", err);
    });
  };

  useEffect(() => { loadAll(); }, []);

  const copyLink = async () => {
    const link = `${window.location.origin}/register/quizmaster`;
    await navigator.clipboard.writeText(link);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div>
      <Section title="Anbieter-Websites">
        <p style={{ color: "#6b7280", fontSize: "0.9rem", margin: "0 0 1rem 0" }}>
          Momentan wird die automatische Suche nur für die Pension Schmidt durchgeführt. Weitere Event Anbieter können später hinzugefügt werden.
        </p>
      </Section>

      <Section title="Quiz-Interessierte">
        {participants.map((p) => (
          <Row key={p.id} label={p.name} sub={p.email || "Keine E-Mail"} onDelete={() => api.delete(`/participants/${p.id}`).then(loadAll)} />
        ))}
        <AddRow fields={[
          { placeholder: "Name", value: newParticipant.name, onChange: (v) => setNewParticipant({ ...newParticipant, name: v }) },
          { placeholder: "E-Mail (optional)", value: newParticipant.email, onChange: (v) => setNewParticipant({ ...newParticipant, email: v }) },
        ]} onAdd={async () => {
          if (!newParticipant.name.trim()) return;
          try {
            await api.post("/participants", newParticipant);
            setNewParticipant({ name: "", email: "" });
            loadAll();
          } catch (err) {
            console.error("Failed to add participant:", err);
            if (err.message.includes("409")) {
              alert("Diese E-Mail-Adresse ist bereits registriert.");
            } else {
              alert("Fehler beim Hinzufügen des Teilnehmers: " + err.message);
            }
          }
        }} />
      </Section>

      <Section title="Einladungslink">
        <p style={{ color: "#6b7280", fontSize: "0.9rem", margin: "0 0 0.75rem 0" }}>
          Dieser Link kannst du teilen. Wer ihn öffnet, kann sich selbst eintragen.
        </p>
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
          <input readOnly value={`${window.location.origin}/register/quizmaster`} style={{ flex: 1, padding: "0.4rem 0.6rem", border: "1px solid #d1d5db", borderRadius: 6, fontSize: "0.85rem", minWidth: 0 }} />
          <button onClick={copyLink} style={{ padding: "0.4rem 1rem", background: copied ? "#22c55e" : "#6366f1", color: "white", border: "none", borderRadius: 6, cursor: "pointer", whiteSpace: "nowrap" }}>
            {copied ? "Kopiert!" : "Kopieren"}
          </button>
        </div>
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
