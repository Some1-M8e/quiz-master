import { useEffect, useState } from "react";
import { api } from "../api";

export default function RsvpPage({ token }) {
  const [data, setData] = useState(null);
  const [companions, setCompanions] = useState(0);
  const [done, setDone] = useState(null);

  useEffect(() => {
    api.get(`/rsvp/${token}`).then(setData);
  }, [token]);

  const respond = async (response) => {
    const params = response === "yes" ? `?companions=${companions}` : "";
    await fetch(`http://localhost:8000/rsvp/${token}/${response}${params}`);
    setDone(response);
  };

  if (!data) return <p style={{ padding: "2rem" }}>Lade...</p>;
  if (done) return (
    <div style={{ padding: "2rem", textAlign: "center" }}>
      <h2>{done === "yes" ? "Zusage gespeichert!" : "Absage gespeichert."}</h2>
      <p>{done === "yes" ? "Wir freuen uns auf dich!" : "Schade, vielleicht beim nächsten Mal."}</p>
    </div>
  );

  return (
    <div style={{ maxWidth: 500, margin: "2rem auto", padding: "1.5rem", fontFamily: "sans-serif", border: "1px solid #e5e7eb", borderRadius: 12 }}>
      <h2>Quiz-Master</h2>
      <p>Hallo <strong>{data.participant_name}</strong>,</p>
      <p>möchtest du am Quiz-Abend <strong>{data.event_title}</strong> am <strong>{data.event_date}</strong> teilnehmen?</p>

      <div style={{ margin: "1.5rem 0" }}>
        <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: "bold" }}>Begleitungen:</label>
        <select value={companions} onChange={(e) => setCompanions(Number(e.target.value))}
          style={{ padding: "0.4rem", borderRadius: 6, border: "1px solid #d1d5db", width: "100%" }}>
          {[0, 1, 2, 3, 4].map((n) => (
            <option key={n} value={n}>{n === 0 ? "Keine Begleitung" : `+${n}`}</option>
          ))}
        </select>
      </div>

      <div style={{ display: "flex", gap: "1rem" }}>
        <button onClick={() => respond("yes")}
          style={{ flex: 1, padding: "0.75rem", background: "#22c55e", color: "white", border: "none", borderRadius: 8, cursor: "pointer", fontSize: "1rem", fontWeight: "bold" }}>
          Zusagen
        </button>
        <button onClick={() => respond("no")}
          style={{ flex: 1, padding: "0.75rem", background: "#ef4444", color: "white", border: "none", borderRadius: 8, cursor: "pointer", fontSize: "1rem", fontWeight: "bold" }}>
          Absagen
        </button>
      </div>
    </div>
  );
}
