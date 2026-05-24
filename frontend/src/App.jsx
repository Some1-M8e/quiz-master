import { useState } from "react";
import EventList from "./pages/EventList";
import EventDetail from "./pages/EventDetail";
import RsvpPage from "./pages/RsvpPage";
import Settings from "./pages/Settings";

export default function App() {
  const path = window.location.pathname;

  if (path.startsWith("/rsvp/")) {
    const token = path.split("/")[2];
    return <RsvpPage token={token} />;
  }

  const [page, setPage] = useState("events");
  const [selectedEvent, setSelectedEvent] = useState(null);

  const nav = (p, extra = null) => {
    setPage(p);
    if (extra !== null) setSelectedEvent(extra);
  };

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: "1rem", fontFamily: "sans-serif" }}>
      <header style={{ display: "flex", gap: "1rem", borderBottom: "2px solid #e5e7eb", paddingBottom: "0.5rem", marginBottom: "1.5rem" }}>
        <h2 style={{ margin: 0, flex: 1 }}>Quiz-Master</h2>
        <button onClick={() => nav("events")} style={btnStyle(page === "events")}>Termine</button>
        <button onClick={() => nav("settings")} style={btnStyle(page === "settings")}>Einstellungen</button>
      </header>
      {page === "events" && !selectedEvent && <EventList onSelect={(e) => nav("detail", e)} />}
      {page === "detail" && selectedEvent && <EventDetail event={selectedEvent} onBack={() => nav("events")} />}
      {page === "settings" && <Settings />}
    </div>
  );
}

const btnStyle = (active) => ({
  padding: "0.4rem 1rem",
  background: active ? "#6366f1" : "#f3f4f6",
  color: active ? "white" : "#374151",
  border: "none",
  borderRadius: "6px",
  cursor: "pointer",
  fontWeight: active ? "bold" : "normal",
});
