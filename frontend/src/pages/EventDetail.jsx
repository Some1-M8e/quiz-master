import { useEffect, useState } from "react";
import { api } from "../api";
import { displayTitle } from "../utils";

const STATUS_LABEL = { pending: "Offen", booked: "Gebucht, für 5 Personen reserviert", cancelled: "Storniert", ausverkauft: "Ausverkauft", teilweise_ausverkauft: "Begrenzt" };

export default function EventDetail({ event, onBack }) {
  const [detail, setDetail] = useState(null);
  const [adminDetail, setAdminDetail] = useState(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    api.get(`/events/${event.id}`).then(setDetail);
    api.get(`/admin/events/${event.id}`).then(setAdminDetail);
  }, [event.id]);

  const handleForceKeep = async (enable) => {
    setSaving(true);
    setMessage(null);
    try {
      await api.put(`/admin/events/${event.id}/force-keep`, {
        force_keep: enable,
      });
      setMessage({ type: "success", text: enable ? "Event zum Behalten markiert!" : "Force Keep entfernt!" });
      // Admin-Details neu laden
      api.get(`/admin/events/${event.id}`).then(setAdminDetail);
    } catch (err) {
      setMessage({ type: "error", text: `Fehler: ${err.message}` });
    } finally {
      setSaving(false);
    }
  };

  if (!detail || !adminDetail) return <p>Lade...</p>;

  const yes = adminDetail.rsvps.filter((r) => r.response === "yes");
  const maybe = adminDetail.rsvps.filter((r) => r.response === "maybe");
  const no = adminDetail.rsvps.filter((r) => r.response === "no");
  const pending = adminDetail.rsvps.filter((r) => !r.response);

  const isBooked = detail.status === "booked";

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

      {/* Admin-Info Block */}
      <div style={{ marginTop: "1rem", padding: "0.75rem", background: "#f0f9ff", borderRadius: 8, border: "1px solid #bae6fd" }}>
        <div style={{ fontSize: "0.85rem", color: "#0c4a6e" }}>
          <div><strong>Status:</strong> {STATUS_LABEL[detail.status] || detail.status}</div>
          <div><strong>Ja-Stimmen:</strong> {adminDetail.yes_count} (benötigt mind. 4)</div>
          <div><strong>Vielleicht:</strong> {adminDetail.maybe_count}</div>
          <div><strong>Tage bis Event:</strong> {adminDetail.days_until}</div>
        </div>

        {/* Force Keep Button / Status */}
        {adminDetail.force_keep ? (
          <div style={{ marginTop: "0.75rem", padding: "0.5rem", background: "#dcfce7", borderRadius: 6, border: "1px solid #86efac" }}>
            <div style={{ color: "#166534", fontWeight: "bold" }}>✓ Event zum Behalten markiert</div>
            {adminDetail.force_keep_note && (
              <div style={{ color: "#15803d", fontSize: "0.85rem", marginTop: 4 }}>{adminDetail.force_keep_note}</div>
            )}
            <button
              onClick={() => handleForceKeep(false)}
              disabled={saving}
              style={{ marginTop: "0.5rem", padding: "0.35rem 0.75rem", background: "#ef4444", color: "white", border: "none", borderRadius: 4, cursor: "pointer", fontSize: "0.85rem" }}
            >
              Force Keep entfernen
            </button>
          </div>
        ) : (
          isBooked && (
            <div style={{ marginTop: "0.75rem" }}>
              <div style={{ padding: "0.5rem", background: "#fef3c7", borderRadius: 6, border: "1px solid #fcd34d", color: "#92400e", fontSize: "0.85rem", marginBottom: "0.5rem" }}>
                <div style={{ fontWeight: "bold", marginBottom: "0.25rem" }}>Automatische Stornierung:</div>
                <div>
                  {(() => {
                    const eventDate = new Date(adminDetail.event_date);
                    const day3 = new Date(eventDate); day3.setDate(day3.getDate() - 3);
                    const fmt = d => d.toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit" });
                    if (adminDetail.days_until > 3) {
                      return <span>In {adminDetail.days_until - 3} Tagen ({fmt(day3)}): Wenn bis dahin weniger als 4 Personen zugesagt haben storniert das Tool den Termin automatisch. Wenn du die Buchung trotzdem beibehalten willst, dann klicke auf "Trotzdem beibehalten".</span>;
                    } else {
                      return <span>Heute oder in {adminDetail.days_until} Tagen ({fmt(day3)}): Wenn bis dahin weniger als 4 Personen zugesagt haben storniert das Tool den Termin automatisch. Wenn du die Buchung trotzdem beibehalten willst, dann klicke auf "Trotzdem beibehalten".</span>;
                    }
                  })()}
                </div>
              </div>
              <button
                onClick={() => handleForceKeep(true)}
                disabled={saving}
                style={{ width: "100%", padding: "0.5rem 1rem", background: "#22c55e", color: "white", border: "none", borderRadius: 4, cursor: "pointer", fontSize: "0.9rem" }}
              >
                {saving ? "Speichere..." : "Trotzdem beibehalten"}
              </button>
            </div>
          )
        )}

        {/* Status Message */}
        {message && (
          <div style={{ marginTop: "0.5rem", padding: "0.5rem", background: message.type === "success" ? "#dcfce7" : "#fee2e2", borderRadius: 6, color: message.type === "success" ? "#166534" : "#991b1b", fontSize: "0.85rem" }}>
            {message.text}
          </div>
        )}
      </div>

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
