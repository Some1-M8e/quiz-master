import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";
import { participantSchema } from "../schemas";
import Layout from "../components/Layout";

export default function RegisterPage() {
  const { token } = useParams();
  const [valid, setValid] = useState(null);
  const [form, setForm] = useState({ name: "", email: "" });
  const [status, setStatus] = useState(null);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    api.get(`/invite/${token}`)
      .then(() => setValid(true))
      .catch(() => setValid(false));
  }, [token]);

  const submit = async () => {
    setErrors({});
    try {
      participantSchema.parse(form);
    } catch (err) {
      const fieldErrors = {};
      err.errors.forEach(e => {
        fieldErrors[e.path[0]] = e.message;
      });
      setErrors(fieldErrors);
      return;
    }

    setStatus("loading");
    try {
      await api.post(`/invite/${token}`, form);
      setStatus("success");
    } catch (err) {
      if (err.message?.includes("409")) {
        setStatus("duplicate");
      } else {
        setStatus("error");
      }
    }
  };

  if (valid === null) return <Layout title="Quiz-Master"><p>Prüfe Einladungslink…</p></Layout>;
  if (valid === false) return <Layout title="Quiz-Master"><p style={{ color: "#ef4444" }}>Dieser Einladungslink ist ungültig oder abgelaufen.</p></Layout>;

  if (status === "success") return (
    <Layout title="Quiz-Master">
      <p style={{ color: "#22c55e", fontWeight: "bold" }}>Willkommen, {form.name}!</p>
      <p>Du bist jetzt in der Quiz-Gruppe und wirst über neue Termine informiert.</p>
    </Layout>
  );

  return (
    <Layout title="Quiz-Master">
      <h3 style={{ marginTop: 0 }}>Quiz-Master beitreten</h3>
      <p style={{ color: "#6b7280" }}>Du wurdest eingeladen! Trag dich ein, um über Quiz-Abende informiert zu werden.</p>
      <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", maxWidth: 360 }}>
        <input
          placeholder="Dein Name"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          style={inputStyle(errors.name)}
        />
        {errors.name && <p style={{ color: "#ef4444", margin: "0 0 0.5rem 0", fontSize: "0.85rem" }}>{errors.name}</p>}

        <input
          placeholder="Deine E-Mail-Adresse"
          type="email"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          style={inputStyle(errors.email)}
        />
        {errors.email && <p style={{ color: "#ef4444", margin: "0 0 0.5rem 0", fontSize: "0.85rem" }}>{errors.email}</p>}

        <button onClick={submit} disabled={status === "loading"} style={btnStyle}>
          {status === "loading" ? "Wird eingetragen…" : "Registrieren"}
        </button>
        {status === "duplicate" && <p style={{ color: "#ef4444", margin: 0 }}>Diese E-Mail ist bereits registriert.</p>}
        {status === "error" && <p style={{ color: "#ef4444", margin: 0 }}>Ein Fehler ist aufgetreten. Bitte versuche es erneut.</p>}
      </div>
    </Layout>
  );
}

const inputStyle = (hasError) => ({
  padding: "0.5rem 0.75rem",
  border: `1px solid ${hasError ? "#ef4444" : "#d1d5db"}`,
  borderRadius: 6,
  fontSize: "1rem",
});
const btnStyle = { padding: "0.6rem 1.2rem", background: "#6366f1", color: "white", border: "none", borderRadius: 8, cursor: "pointer", fontSize: "1rem" };
