const BASE = "http://localhost:8000";

async function handleResponse(r) {
  const text = await r.text();
  const data = text ? JSON.parse(text) : {};
  if (!r.ok) {
    const msg = data.detail || data.message || `HTTP ${r.status}`;
    throw new Error(`${r.status}: ${msg}`);
  }
  return data;
}

export const api = {
  get: async (path) => {
    const r = await fetch(`${BASE}${path}`);
    return handleResponse(r);
  },
  post: async (path, body) => {
    const r = await fetch(`${BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return handleResponse(r);
  },
  delete: async (path) => {
    const r = await fetch(`${BASE}${path}`, { method: "DELETE" });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
  },
};
