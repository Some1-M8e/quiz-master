export default function Layout({ children, title = "Quiz-Master" }) {
  return (
    <div style={{ maxWidth: 820, margin: "0 auto", padding: "1.5rem 2rem", fontFamily: "sans-serif", background: "white", borderRadius: 16, boxShadow: "0 24px 64px rgba(0,0,0,0.45)" }}>
      <h2 style={{ marginTop: 0 }}>{title}</h2>
      {children}
    </div>
  );
}
