const API_BASE = "http://localhost:8000";

async function handleResponse(res) {
  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    // Our backend returns either {message} or {detail}
    const msg = data.message || data.detail || "Something went wrong";
    throw new Error(msg);
  }

  return data;
}

export async function signup({ email, password, displayName }) {
  const res = await fetch(`${API_BASE}/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email,
      password,
      display_name: displayName,
    }),
  });

  return handleResponse(res);
}

export async function login({ email, password }) {
  const res = await fetch(`${API_BASE}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  return handleResponse(res);
}
