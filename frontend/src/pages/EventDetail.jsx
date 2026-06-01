import { useEffect, useState } from "react";
import { api } from "../api";
import { displayTitle } from "../utils";

export default function EventDetail({ event, onBack }) {
  const [detail, setDetail] = useState(null);

  useEffect(() => {
    api.get(`/events/${event.id}`).then(setDetail);
  }, [event.id]);

  if (!detail) return <p>Lade...</p>;

  const yes = detail.rsvps.filter((r) => r.response === "yes");
  const maybe = detail.rsvps.filter((r) => r.response === "maybe");
  const no = detail.rsvps.filter((r) => r.response === "no");
  const pending = detail.rsvps.filter((r) => !r.response);

  return (
    <div>
      <button onClick={onBack} style={{ marginBottom: "1rem", background: "none", border: "none", cursor: "pointer", color: "#6366f1" }}>← Zurück</button>
      <h3>{displayTitle(detail.title)}</h3>
      <p style={{ color: "#6b7280" }}>{new Date(detail.event_date).toLocaleDateString("de-DE", { weekday: "long", day: "2-digit", month: "long", year: "numeric" })}</p>
      {detail.detail_url && (
        <p style={{ marginTop: "0.4rem" }}>
          <a href={detail.detail_url} target="_blank" rel="noopener noreferrer"
            style={{ color: "#6366f1", fontSize: "0.9rem", textDecoration: "none" }}>
            Veranstaltung bei Pension Schmidt ansehen →
          </a>
        </p>
      )}
      <p style={{ marginTop: "0.75rem" }}><strong>Gesamt Teilnehmer:</strong> {detail.total_attendees}</p>

      <Section title="Zugesagt" color="#22c55e" items={yes} showCompanions />
      <Section title="Vielleicht" color="#f59e0b" items={maybe} />
      <Section title="Abgesagt" color="#ef4444" items={no} />
      <Section title="Ausstehend" color="#9ca3af" items={pending} />
    </div>
  );
}

function Section({ title, color, items, showCompanions }) {
  if (items.length === 0) return null;
  return (
    <div style={{ marginBottom: "1rem" }}>
      <h4 style={{ color, borderBottom: `2px solid ${color}`, paddingBottom: 4 }}>{title} ({items.length})</h4>
      {items.map((r, i) => (
        <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "0.4rem 0", borderBottom: "1px solid #f3f4f6" }}>
          <span>{r.participant_name}</span>
          {showCompanions && r.companions > 0 && <span style={{ color: "#6b7280", fontSize: "0.85rem" }}>+{r.companions} Begleitung{r.companions > 1 ? "en" : ""}</span>}
        </div>
      ))}
    </div>
  );
}
