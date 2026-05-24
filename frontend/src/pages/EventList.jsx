import { useEffect, useState } from "react";
import { api } from "../api";

const STATUS_LABEL = { pending: "Offen", booked: "Gebucht", cancelled: "Storniert" };
const STATUS_COLOR = { pending: "#f59e0b", booked: "#22c55e", cancelled: "#ef4444" };

export default function EventList({ onSelect }) {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/events").then((data) => { setEvents(data); setLoading(false); });
  }, []);

  if (loading) return <p>Lade Termine...</p>;
  if (events.length === 0) return <p style={{ color: "#6b7280" }}>Noch keine Termine. Scraper starten oder Anbieter konfigurieren.</p>;

  return (
    <div>
      <h3>Bevorstehende Quiz-Abende</h3>
      {events.map((e) => (
        <div key={e.id} onClick={() => onSelect(e)}
          style={{ border: "1px solid #e5e7eb", borderRadius: 8, padding: "1rem", marginBottom: "0.75rem", cursor: "pointer", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <strong>{e.title}</strong>
            <div style={{ color: "#6b7280", fontSize: "0.9rem" }}>{new Date(e.event_date).toLocaleDateString("de-DE", { weekday: "long", day: "2-digit", month: "long", year: "numeric" })}</div>
          </div>
          <div style={{ textAlign: "right" }}>
            <span style={{ background: STATUS_COLOR[e.status], color: "white", padding: "2px 10px", borderRadius: 12, fontSize: "0.8rem" }}>{STATUS_LABEL[e.status]}</span>
            <div style={{ marginTop: 4, fontSize: "0.85rem", color: "#374151" }}>{e.total_attendees} Personen</div>
          </div>
        </div>
      ))}
    </div>
  );
}
