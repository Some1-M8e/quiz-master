import { useEffect, useState } from "react";
import { api } from "../api";
import { displayTitle } from "../utils";

const STATUS_LABEL = { pending: "Offen", booked: "Gebucht", cancelled: "Storniert", ausverkauft: "Ausverkauft", teilweise_ausverkauft: "Begrenzt" };
const STATUS_COLOR = { pending: "#f59e0b", booked: "#22c55e", cancelled: "#ef4444", ausverkauft: "#6b7280", teilweise_ausverkauft: "#f59e0b" };

const TOOLTIP_FIRST_LINE = "Dieser Status zeigt euch, ob wir beim Anbieter bereits Plätze reserviert haben.";
const TOOLTIP_SECOND_PART = "Die Reservierung erfolgt auch, wenn noch keiner von euch zugesagt hat. So können wir verhindern, dass wir keine Plätze mehr bekommen.";

function Tooltip() {
  const [show, setShow] = useState(false);
  return (
    <div style={{ position: "relative", display: "inline-block" }} onMouseEnter={() => setShow(true)} onMouseLeave={() => setShow(false)}>
      <span style={{ background: "#9ca3af", color: "white", width: 16, height: 16, borderRadius: "50%", display: "inline-flex", alignItems: "center", justifyContent: "center", fontSize: "0.7rem", cursor: "help", fontWeight: "bold" }}>i</span>
      {show && (
        <div style={{ position: "absolute", top: "calc(100% + 5px)", left: 0, background: "#1f2937", color: "white", padding: "0.75rem", borderRadius: 6, fontSize: "0.75rem", width: "280px", zIndex: 1000, boxShadow: "0 4px 6px rgba(0,0,0,0.1)" }}>
          <div>{TOOLTIP_FIRST_LINE}</div>
          <div style={{ marginTop: "0.5rem" }}>{TOOLTIP_SECOND_PART}</div>
        </div>
      )}
    </div>
  );
}

function isSelfBookableEvent(title) {
  const t = title.toLowerCase();
  return t.includes("wer wird pensionär") || t.includes("wer wird pensionar");
}

export default function EventList({ onSelect }) {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastRun, setLastRun] = useState("");
  const [scraperRunning, setScraperRunning] = useState(false);
  const [form, setForm] = useState({ name: "", email: "" });
  const [subscribeState, setSubscribeState] = useState("idle"); // idle | loading | success | error

  const loadEvents = () => {
    Promise.all([
      api.get("/events").then((data) => { setEvents(data); setLoading(false); }).catch(() => { setLoading(false); }),
      api.get("/settings/last-scraper-run").then((data) => { setLastRun(data.last_run || ""); }).catch(() => {})
    ]);
  };

  useEffect(() => { loadEvents(); }, []);

  const runScraper = async () => {
    if (scraperRunning) return;
    setScraperRunning(true);
    try {
      await api.post("/admin/scraper/run");
      setTimeout(() => { loadEvents(); setScraperRunning(false); }, 3000);
    } catch (err) {
      console.error("Scraper error:", err);
      setScraperRunning(false);
    }
  };

  const subscribe = async () => {
    if (!form.name.trim() || !form.email.trim()) return;
    setSubscribeState("loading");
    try {
      await api.post("/participants", form);
      setSubscribeState("success");
      setForm({ name: "", email: "" });
    } catch (err) {
      console.error("Subscribe error:", err);
      setSubscribeState("error");
    }
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.75rem" }}>
        <h3 style={{ margin: 0 }}>Bevorstehende Quiz-Abende</h3>
        <button
          onClick={runScraper}
          disabled={scraperRunning}
          style={{
            padding: "0.5rem 1rem",
            background: scraperRunning ? "#9ca3af" : "#6366f1",
            color: "white",
            border: "none",
            borderRadius: 6,
            cursor: scraperRunning ? "not-allowed" : "pointer",
            whiteSpace: "nowrap",
            fontSize: "0.9rem"
          }}
        >
          {scraperRunning ? "Prüfe..." : "Jetzt prüfen"}
        </button>
      </div>
      {!loading && <p style={{ fontSize: "0.85rem", color: "#6b7280", margin: "0.5rem 0" }}>
        Automatische Prüfung auf neue Termine läuft alle 2 Stunden. Zuletzt aktualisiert: {lastRun}
      </p>}
      {!loading && (
        <div style={{ margin: "0.75rem 0 0.5rem 0", display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <strong style={{ fontSize: "0.85rem", color: "#374151" }}>Reservierungsstatus beim Anbieter:</strong>
          <Tooltip />
        </div>
      )}
      {!loading && (
        <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", margin: "0 0 1.5rem 0", fontSize: "0.85rem" }}>
          <span style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
            <span style={{ width: 12, height: 12, background: "#f59e0b", borderRadius: 3 }}></span> Offen / Wenige Plätze
          </span>
          <span style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
            <span style={{ width: 12, height: 12, background: "#22c55e", borderRadius: 3 }}></span> Gebucht
          </span>
          <span style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
            <span style={{ width: 12, height: 12, background: "#ef4444", borderRadius: 3 }}></span> Abgesagt
          </span>
          <span style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
            <span style={{ width: 12, height: 12, background: "#6b7280", borderRadius: 3 }}></span> Ausverkauft (0 Plätze)
          </span>
        </div>
      )}
      {loading && <p>Lade Termine...</p>}
      {!loading && events.length === 0 && (
        <p style={{ color: "#6b7280" }}>Noch keine Termine. Websites jetzt prüfen oder zuerst einen Anbieter konfigurieren.</p>
      )}
      {events.map((e) => {
        const selfBookable = isSelfBookableEvent(e.title);
        return (
          <div key={e.id} onClick={() => onSelect(e)}
            style={{ border: "1px solid #e5e7eb", borderRadius: 8, padding: "1rem", marginBottom: "0.75rem", cursor: "pointer", display: "flex", justifyContent: "space-between", alignItems: "center", background: selfBookable ? "#fefce8" : "white" }}>
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <strong>{displayTitle(e.title)}</strong>
              </div>
              <div style={{ color: "#6b7280", fontSize: "0.9rem" }}>{new Date(e.event_date).toLocaleDateString("de-DE", { weekday: "long", day: "2-digit", month: "long", year: "numeric" })}</div>
              {selfBookable ? (
                <div style={{ color: "#92400e", fontSize: "0.8rem", marginTop: 2 }}>💡 Bitte selbst über das Buchungstool reservieren</div>
              ) : (
                <div style={{ color: "#6366f1", fontSize: "0.8rem", marginTop: 2 }}>Klicke für mehr Details</div>
              )}
            </div>
            {!selfBookable && (
              <div style={{ textAlign: "right" }}>
                <span style={{ background: STATUS_COLOR[e.status], color: "white", padding: "2px 10px", borderRadius: 12, fontSize: "0.8rem" }}>{STATUS_LABEL[e.status]}</span>
                <div style={{ marginTop: 4, fontSize: "0.85rem", color: "#374151" }}>{e.total_attendees} Personen</div>
              </div>
            )}
          </div>
        );
      })}

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
