const BASE = "http://localhost:8000";

export const api = {
  get: (path) => fetch(`${BASE}${path}`).then((r) => r.json()),
  post: (path, body) => fetch(`${BASE}${path}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }).then((r) => r.json()),
  delete: (path) => fetch(`${BASE}${path}`, { method: "DELETE" }),
};
