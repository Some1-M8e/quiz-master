import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";
import Layout from "../components/Layout";

export default function RsvpPage() {
  const { token } = useParams();
  const [data, setData] = useState(null);
  const [companions, setCompanions] = useState(0);
  const [done, setDone] = useState(null);
  const [daysUntil, setDaysUntil] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get(`/rsvp/${token}`)
      .then((res) => {
        setData(res);
        const eventDate = new Date(res.event_date);
        const now = new Date();
        const days = Math.ceil((eventDate - now) / (1000 * 60 * 60 * 24));
        setDaysUntil(days);
      })
      .catch((err) => {
        setError("RSVP nicht gefunden oder Link ungültig.");
      })
      .finally(() => setLoading(false));
  }, [token]);

  const respond = async (response) => {
    const params = response === "yes" ? `?companions=${companions}` : "";
    try {
      await api.get(`/rsvp/${token}/${response}` + params);
      setDone(response);
    } catch (err) {
      setError("Fehler beim Speichern der Antwort. Bitte versuche es erneut.");
    }
  };

  if (error) return <Layout><p style={{ color: "#ef4444" }}>{error}</p></Layout>;
  if (loading) return <Layout><p>Lade...</p></Layout>;
  if (!data) return <Layout><p style={{ color: "#ef4444" }}>Daten konnten nicht geladen werden.</p></Layout>;

  if (done) {
    const messages = {
      yes: { title: "Zusage gespeichert!", text: "Wir freuen uns auf dich!" },
      maybe: { title: "Vielleicht gespeichert.", text: "Sag uns gerne Bescheid, sobald du es weißt." },
      no: { title: "Absage gespeichert.", text: "Schade, vielleicht beim nächsten Mal." },
    };
    const m = messages[done];
    return (
      <Layout>
        <h2>{m.title}</h2>
        <p>{m.text}</p>
      </Layout>
    );
  }

  return (
    <div style={{ maxWidth: 500, margin: "2rem auto", padding: "1.5rem", fontFamily: "sans-serif", border: "1px solid #e5e7eb", borderRadius: 12, background: "white" }}>
      <h2>Quiz-Master</h2>
      <p>Hallo <strong>{data.participant_name}</strong>,</p>
      <p>möchtest du am Quiz-Abend <strong>{data.event_title}</strong> am <strong>{data.event_date}</strong> teilnehmen?</p>

      <div style={{ margin: "1.5rem 0" }}>
        <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: "bold" }}>Begleitungen:</label>
        <select value={companions} onChange={(e) => setCompanions(Number(e.target.value))}
          style={{ padding: "0.4rem", borderRadius: 6, border: "1px solid #d1d5db", width: "100%" }}>
          {[0, 1].map((n) => (
            <option key={n} value={n}>{n === 0 ? "Keine Begleitung" : `+${n}`}</option>
          ))}
        </select>
      </div>

      {data.detail_url && (
        <p style={{ marginBottom: "1.5rem" }}>
          <a href={data.detail_url} target="_blank" rel="noreferrer" style={{ color: "#6366f1" }}>
            Zur Veranstaltungsseite
          </a>
        </p>
      )}

      <div style={{ display: "flex", gap: "1rem" }}>
        <button onClick={() => respond("yes")}
          style={{ flex: 1, padding: "0.75rem", background: "#22c55e", color: "white", border: "none", borderRadius: 8, cursor: "pointer", fontSize: "1rem", fontWeight: "bold" }}>
          Zusagen
        </button>
        <button onClick={() => respond("maybe")}
          disabled={daysUntil !== null && daysUntil <= 7}
          style={{ flex: 1, padding: "0.75rem", background: daysUntil !== null && daysUntil <= 7 ? "#d1d5db" : "#f59e0b", color: daysUntil !== null && daysUntil <= 7 ? "#6b7280" : "white", border: "none", borderRadius: 8, cursor: daysUntil !== null && daysUntil <= 7 ? "not-allowed" : "pointer", fontSize: "1rem", fontWeight: "bold" }}>
          Vielleicht
        </button>
        <button onClick={() => respond("no")}
          style={{ flex: 1, padding: "0.75rem", background: "#ef4444", color: "white", border: "none", borderRadius: 8, cursor: "pointer", fontSize: "1rem", fontWeight: "bold" }}>
          Absagen
        </button>
      </div>
      {daysUntil !== null && daysUntil <= 7 && (
        <p style={{ marginTop: "1rem", color: "#6b7280", fontSize: "0.9rem" }}>
          Ab einer Woche vor der Veranstaltung müssen Sie sich definitiv anmelden oder absagen (48h Frist).
        </p>
      )}
      <p style={{ marginTop: "2rem", paddingTop: "1rem", borderTop: "1px solid #e5e7eb", fontSize: "0.85rem", color: "#9ca3af" }}>
        Du erhältst diese E-Mail weil du als Quiz-Interessierter eingetragen bist.{" "}
        <a href={`/unsubscribe/${encodeURIComponent(data.participant_email || "")}`} style={{ color: "#6366f1" }}>
          Benachrichtigungen abbestellen
        </a>
      </p>
    </div>
  );
}
