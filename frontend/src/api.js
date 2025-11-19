const API_BASE = "http://localhost:8000";

async function handleResponse(res) {
  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
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


function authHeaders() {
  const token = localStorage.getItem("access_token");
  const type = localStorage.getItem("token_type") || "Bearer";

  if (!token) {
    throw new Error("Not authenticated");
  }

  return {
    Authorization: `${type} ${token}`,
    "Content-Type": "application/json",
  };
}


export async function createGoal({ title, description }) {
  const res = await fetch(`${API_BASE}/goals`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ title, description }),
  });

  return handleResponse(res);
}


export async function generateGoalPlan(goalId) {
  const res = await fetch(`${API_BASE}/goals/${goalId}/generate`, {
    method: "POST",
    headers: authHeaders(),
  });

  return handleResponse(res);
}


export async function getGoals() {
  const res = await fetch(`${API_BASE}/goals`, {
    method: "GET",
    headers: authHeaders(),
  });

  return handleResponse(res);
}

export async function confirmGoalPlan(goalId) {
  const res = await fetch(`${API_BASE}/goals/${goalId}/confirm`, {
    method: "POST",
    headers: authHeaders(),
  });

  return handleResponse(res);
}


export async function regenerateGoalPlan(goalId) {
  const res = await fetch(`${API_BASE}/goals/${goalId}/regenerate`, {
    method: "POST",
    headers: authHeaders(),
  });

  return handleResponse(res);
}


export async function getUserProgress() {
  const res = await fetch(`${API_BASE}/user/progress`, {
    method: "GET",
    headers: authHeaders(),
  });

  return handleResponse(res);
}