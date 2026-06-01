import { useEffect, useState } from "react";
import { api } from "../api";
import { displayTitle } from "../utils";

const STATUS_LABEL = { pending: "Offen", booked: "Gebucht", cancelled: "Storniert" };
const STATUS_COLOR = { pending: "#f59e0b", booked: "#22c55e", cancelled: "#ef4444" };

export default function EventList({ onSelect }) {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ name: "", email: "" });
  const [subscribeState, setSubscribeState] = useState("idle"); // idle | loading | success | error

  useEffect(() => {
    api.get("/events").then((data) => { setEvents(data); setLoading(false); });
  }, []);

  const subscribe = async () => {
    if (!form.name.trim() || !form.email.trim()) return;
    setSubscribeState("loading");
    try {
      await api.post("/participants", form);
      setSubscribeState("success");
      setForm({ name: "", email: "" });
    } catch {
      setSubscribeState("error");
    }
  };

  return (
    <div>
      <h3>Bevorstehende Quiz-Abende</h3>
      {loading && <p>Lade Termine...</p>}
      {!loading && events.length === 0 && (
        <p style={{ color: "#6b7280" }}>Noch keine Termine. Websites jetzt prüfen oder zuerst einen Anbieter konfigurieren.</p>
      )}
      {events.map((e) => (
        <div key={e.id} onClick={() => onSelect(e)}
          style={{ border: "1px solid #e5e7eb", borderRadius: 8, padding: "1rem", marginBottom: "0.75rem", cursor: "pointer", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <strong>{displayTitle(e.title)}</strong>
            <div style={{ color: "#6b7280", fontSize: "0.9rem" }}>{new Date(e.event_date).toLocaleDateString("de-DE", { weekday: "long", day: "2-digit", month: "long", year: "numeric" })}</div>
          </div>
          <div style={{ textAlign: "right" }}>
            <span style={{ background: STATUS_COLOR[e.status], color: "white", padding: "2px 10px", borderRadius: 12, fontSize: "0.8rem" }}>{STATUS_LABEL[e.status]}</span>
            <div style={{ marginTop: 4, fontSize: "0.85rem", color: "#374151" }}>{e.total_attendees} Personen</div>
          </div>
        </div>
      ))}

      <div style={{ marginTop: "2rem", border: "1px solid #e5e7eb", borderRadius: 10, padding: "1.25rem", background: "#f9fafb" }}>
        <h4 style={{ margin: "0 0 0.25rem 0", fontSize: "1rem" }}>Neue Termine erhalten?</h4>
        <p style={{ margin: "0 0 1rem 0", color: "#6b7280", fontSize: "0.9rem" }}>
          Trag dich ein und wir benachrichtigen dich, sobald ein neuer Quiz-Abend geplant wird.
        </p>
        {subscribeState === "success" ? (
          <p style={{ color: "#22c55e", fontWeight: "bold" }}>✓ Du bist eingetragen!</p>
        ) : (
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            <input
              placeholder="Dein Name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              style={{ flex: 1, minWidth: 120, padding: "0.45rem 0.7rem", border: "1px solid #d1d5db", borderRadius: 6 }}
            />
            <input
              placeholder="E-Mail-Adresse"
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              style={{ flex: 2, minWidth: 180, padding: "0.45rem 0.7rem", border: "1px solid #d1d5db", borderRadius: 6 }}
            />
            <button
              onClick={subscribe}
              disabled={subscribeState === "loading"}
              style={{ padding: "0.45rem 1.1rem", background: "#6366f1", color: "white", border: "none", borderRadius: 6, cursor: "pointer", whiteSpace: "nowrap" }}
            >
              Eintragen
            </button>
          </div>
        )}
        {subscribeState === "error" && (
          <p style={{ color: "#ef4444", fontSize: "0.85rem", marginTop: 6 }}>Etwas hat nicht geklappt. Bitte versuche es erneut.</p>
        )}
      </div>
    </div>
  );
}
