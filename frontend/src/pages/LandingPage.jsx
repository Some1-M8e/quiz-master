import { useState } from "react";
import { useNavigate } from "react-router-dom";

const apps = [
  {
    name: "Quiz-Master",
    description: "Team-Events & Quizzes planen",
    path: "/quiz-master",
    emoji: "🎯",
    color: "#6366f1",
  },
  // Hier kannst du später einfach weitere Apps einfügen:
  // {
  //   name: "Todo-Liste",
  //   description: "Aufgaben verwalten",
  //   path: "/todo",
  //   emoji: "✅",
  //   color: "#10b981",
  // },
];

export default function LandingPage() {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [unlocked, setUnlocked] = useState(false);
  const navigate = useNavigate();

  const handleLogin = (e) => {
    e.preventDefault();
    if (password === "takkatukkaland") {
      setUnlocked(true);
      setError("");
    } else {
      setError("Falsches Passwort");
      setPassword("");
    }
  };

  if (!unlocked) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
          fontFamily: "sans-serif",
          padding: "1rem",
        }}
      >
        <div
          style={{
            background: "white",
            borderRadius: 20,
            padding: "3rem 2.5rem",
            boxShadow: "0 24px 64px rgba(0,0,0,0.3)",
            maxWidth: 400,
            width: "100%",
            textAlign: "center",
          }}
        >
          <div style={{ fontSize: 48, marginBottom: 8 }}>🔐</div>
          <h2 style={{ marginTop: 0, color: "#1f2937", fontSize: "1.5rem" }}>
            Meine App-Sammlung
          </h2>
          <p style={{ color: "#6b7280", marginBottom: "1.5rem" }}>
            Bitte Passwort eingeben
          </p>
          <form onSubmit={handleLogin}>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Passwort"
              autoFocus
              style={{
                width: "100%",
                padding: "0.75rem 1rem",
                border: "2px solid #e5e7eb",
                borderRadius: 8,
                fontSize: "16px",
                marginBottom: "1rem",
                boxSizing: "border-box",
              }}
            />
            {error && (
              <p style={{ color: "#ef4444", fontSize: "0.875rem", marginBottom: "1rem" }}>
                {error}
              </p>
            )}
            <button
              type="submit"
              style={{
                width: "100%",
                padding: "0.75rem",
                background: "#6366f1",
                color: "white",
                border: "none",
                borderRadius: 8,
                fontSize: "16px",
                cursor: "pointer",
                fontWeight: "bold",
              }}
            >
              Rein
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        fontFamily: "sans-serif",
        padding: "2rem 1rem",
      }}
    >
      <div style={{ maxWidth: 900, margin: "0 auto" }}>
        <h1
          style={{
            color: "white",
            textAlign: "center",
            fontSize: "2.5rem",
            marginTop: 0,
            marginBottom: "2rem",
            textShadow: "0 2px 8px rgba(0,0,0,0.2)",
          }}
        >
          Meine App-Sammlung
        </h1>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
            gap: "1.5rem",
          }}
        >
          {apps.map((app) => (
            <button
              key={app.path}
              onClick={() => navigate(app.path)}
              style={{
                background: "white",
                border: "none",
                borderRadius: 16,
                padding: "2rem 1.5rem",
                cursor: "pointer",
                boxShadow: "0 8px 24px rgba(0,0,0,0.15)",
                transition: "transform 0.2s, box-shadow 0.2s",
                textAlign: "center",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = "translateY(-4px)";
                e.currentTarget.style.boxShadow = "0 12px 32px rgba(0,0,0,0.25)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = "translateY(0)";
                e.currentTarget.style.boxShadow = "0 8px 24px rgba(0,0,0,0.15)";
              }}
            >
              <div
                style={{
                  width: 64,
                  height: 64,
                  borderRadius: 16,
                  background: app.color + "20",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 32,
                  marginBottom: 16,
                }}
              >
                {app.emoji}
              </div>
              <h3 style={{ margin: 0, color: "#1f2937", fontSize: "1.2rem" }}>
                {app.name}
              </h3>
              <p style={{ margin: "0.5rem 0 0", color: "#6b7280", fontSize: "0.875rem" }}>
                {app.description}
              </p>
            </button>
          ))}
        </div>

        <p
          style={{
            color: "rgba(255,255,255,0.5)",
            textAlign: "center",
            marginTop: "3rem",
            fontSize: "0.8rem",
          }}
        >
          Weitere Apps folgen...
        </p>
      </div>
    </div>
  );
}
