import { useEffect, useState } from "react";
import { api } from "../api";

export default function RegisterPage({ token }) {
  const [valid, setValid] = useState(null);
  const [form, setForm] = useState({ name: "", email: "" });
  const [status, setStatus] = useState(null);

  useEffect(() => {
    api.get(`/invite/${token}`)
      .then(() => setValid(true))
      .catch(() => setValid(false));
  }, [token]);

  const submit = async () => {
    if (!form.name || !form.email) return;
    setStatus("loading");
    const res = await fetch(`http://localhost:8000/invite/${token}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });
    if (res.status === 201) {
      setStatus("success");
    } else if (res.status === 409) {
      setStatus("duplicate");
    } else {
      setStatus("error");
    }
  };

  if (valid === null) return <Wrapper><p>Prüfe Einladungslink…</p></Wrapper>;
  if (valid === false) return <Wrapper><p style={{ color: "#ef4444" }}>Dieser Einladungslink ist ungültig oder abgelaufen.</p></Wrapper>;

  if (status === "success") return (
    <Wrapper>
      <p style={{ color: "#22c55e", fontWeight: "bold" }}>Willkommen, {form.name}!</p>
      <p>Du bist jetzt in der Quiz-Gruppe und wirst über neue Termine informiert.</p>
    </Wrapper>
  );

  return (
    <Wrapper>
      <h3 style={{ marginTop: 0 }}>Quiz-Master beitreten</h3>
      <p style={{ color: "#6b7280" }}>Du wurdest eingeladen! Trag dich ein, um über Quiz-Abende informiert zu werden.</p>
      <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", maxWidth: 360 }}>
        <input
          placeholder="Dein Name"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          style={inputStyle}
        />
        <input
          placeholder="Deine E-Mail-Adresse"
          type="email"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          style={inputStyle}
        />
        <button onClick={submit} disabled={status === "loading"} style={btnStyle}>
          {status === "loading" ? "Wird eingetragen…" : "Registrieren"}
        </button>
        {status === "duplicate" && <p style={{ color: "#ef4444", margin: 0 }}>Diese E-Mail ist bereits registriert.</p>}
        {status === "error" && <p style={{ color: "#ef4444", margin: 0 }}>Ein Fehler ist aufgetreten. Bitte versuche es erneut.</p>}
      </div>
    </Wrapper>
  );
}

function Wrapper({ children }) {
  return (
    <div style={{ maxWidth: 820, margin: "0 auto", padding: "1.5rem 2rem", fontFamily: "sans-serif", background: "white", borderRadius: 16, boxShadow: "0 24px 64px rgba(0,0,0,0.45)" }}>
      <h2 style={{ marginTop: 0 }}>Quiz-Master</h2>
      {children}
    </div>
  );
}

const inputStyle = { padding: "0.5rem 0.75rem", border: "1px solid #d1d5db", borderRadius: 6, fontSize: "1rem" };
const btnStyle = { padding: "0.6rem 1.2rem", background: "#6366f1", color: "white", border: "none", borderRadius: 8, cursor: "pointer", fontSize: "1rem" };
