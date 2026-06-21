import { useEffect, useState } from "react";
import { api } from "../api";
import { displayTitle } from "../utils";

const STATUS_LABEL = { pending: "Offen", booked: "Gebucht, für 5 Personen reserviert", cancelled: "Storniert", ausverkauft: "Ausverkauft", teilweise_ausverkauft: "Begrenzt" };

function isSelfBookableEvent(title) {
  const t = title.toLowerCase();
  return t.includes("wer wird pensionär") || t.includes("wer wird pensionar");
}

export default function EventDetail({ event, onBack }) {
  const [detail, setDetail] = useState(null);
  const [adminDetail, setAdminDetail] = useState(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    api.get(`/events/${event.id}`).then((d) => {
      setDetail(d);
      setAdminDetail(d);
    });
  }, [event.id]);

  const handleBook = async (enable) => {
    setSaving(true);
    setMessage(null);
    try {
      await api.put(`/events/${event.id}/force-keep`, {
        force_keep: enable,
      });
      setMessage({ type: "success", text: enable ? "Buchung gesichert! Das Event bleibt auch mit weniger als 4 Teilnehmern bestehen." : "Buchungsentlastung entfernt." });
      api.get(`/events/${event.id}`).then((d) => { setDetail(d); setAdminDetail(d); });
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
  const selfBookable = isSelfBookableEvent(detail.title);

  return (
    <div>
      <button onClick={onBack} style={{ marginBottom: "1rem", background: "none", border: "none", cursor: "pointer", color: "#6366f1" }}>← Zurück</button>
      <h3 style={{ margin: 0 }}>{displayTitle(detail.title)}</h3>
      <p style={{ color: "#6b7280" }}>{new Date(detail.event_date).toLocaleDateString("de-DE", { weekday: "long", day: "2-digit", month: "long", year: "numeric" })}</p>

      {selfBookable ? (
        <div style={{ background: "#fef3c7", padding: "1rem", borderRadius: 8, border: "1px solid #fcd34d", margin: "0.75rem 0" }}>
          <p style={{ margin: "0 0 0.5rem 0", fontWeight: "bold", color: "#92400e" }}>💡 Dieser Termin wird NICHT automatisch gebucht!</p>
          <p style={{ margin: 0, color: "#92400e", fontSize: "0.9rem" }}>
            Wenn du teilnehmen möchtest, bitte selbst über das Buchungstool reservieren.
          </p>
          {detail.detail_url && (
            <a href={detail.detail_url} target="_blank" rel="noopener noreferrer"
              style={{ display: "inline-block", marginTop: "0.75rem", padding: "8px 16px", background: "#2563eb", color: "white", textDecoration: "none", borderRadius: 6, fontWeight: "bold" }}>
              Zum Buchungstool →
            </a>
          )}
        </div>
      ) : (
        <>
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

            {/* Buchung sichern */}
            {adminDetail.force_keep ? (
              <div style={{ marginTop: "0.75rem", padding: "0.5rem", background: "#dcfce7", borderRadius: 6, border: "1px solid #86efac" }}>
                <div style={{ color: "#166534", fontWeight: "bold" }}>✓ Buchung gesichert!</div>
                {adminDetail.force_keep_note && (
                  <div style={{ color: "#15803d", fontSize: "0.85rem", marginTop: 4 }}>{adminDetail.force_keep_note}</div>
                )}
                <button
                  onClick={() => handleBook(false)}
                  disabled={saving}
                  style={{ marginTop: "0.5rem", padding: "0.35rem 0.75rem", background: "#ef4444", color: "white", border: "none", borderRadius: 4, cursor: "pointer", fontSize: "0.85rem" }}
                >
                  Buchung nicht mehr sichern
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
                          return <span>In {adminDetail.days_until - 3} Tagen ({fmt(day3)}): Wenn bis dahin weniger als 4 Personen zugesagt haben storniert das Tool den Termin automatisch. Jeder kann die Buchung aber auf "Beibehalten" stellen – egal wie viele Teilnehmer es gibt.</span>;
                        } else {
                          return <span>Heute oder in {adminDetail.days_until} Tagen ({fmt(day3)}): Wenn bis dahin weniger als 4 Personen zugesagt haben storniert das Tool den Termin automatisch. Jeder kann die Buchung aber auf "Beibehalten" stellen – egal wie viele Teilnehmer es gibt.</span>;
                        }
                      })()}
                    </div>
                  </div>
                  <button
                    onClick={() => handleBook(true)}
                    disabled={saving}
                    style={{ width: "100%", padding: "0.5rem 1rem", background: "#22c55e", color: "white", border: "none", borderRadius: 4, cursor: "pointer", fontSize: "0.9rem" }}
                  >
                    {saving ? "Speichere..." : "Buchung sichern"}
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
        </>
      )}
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
