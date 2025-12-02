const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";



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


export async function getGoal(goalId) {
  const res = await fetch(`${API_BASE}/goals/${goalId}`, {
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


export async function startStep(goalId, stepId) {
  const res = await fetch(`${API_BASE}/goals/${goalId}/steps/${stepId}/start`, {
    method: "POST",
    headers: authHeaders(),
  });
  return handleResponse(res);
}


export async function completeStep(goalId, stepId) {
  const res = await fetch(`${API_BASE}/goals/${goalId}/steps/${stepId}/complete`, {
    method: "POST",
    headers: authHeaders(),
  });
  return handleResponse(res);
}


export async function reflectOnStep(goalId, stepId, text) {
  const res = await fetch(
    `${API_BASE}/goals/${goalId}/steps/${stepId}/reflect`,
    {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ text }),
    }
  );
  return handleResponse(res);
}


export async function getXpSummary() {
  const res = await fetch(`${API_BASE}/xp/summary`, {
    method: "GET",
    headers: authHeaders(),
  });

  return handleResponse(res);
}


export async function deleteGoal(goalId) {
  const res = await fetch(`${API_BASE}/goals/${goalId}`, {
    method: "DELETE",
    headers: authHeaders(),
  });

  // 204 has no body, but handleResponse can still be used if needed
  if (res.status === 204) return;
  return handleResponse(res);
}


export async function finishGoal(goalId) {
  const res = await fetch(`${API_BASE}/goals/${goalId}/finish`, {
    method: "POST",
    headers: authHeaders(),
  });
  return handleResponse(res);
}


export async function getCompletedGoals() {
  const res = await fetch(`${API_BASE}/goals/completed`, {
    method: "GET",
    headers: authHeaders(),
  });

  return handleResponse(res);
}

export async function getXpLogs() {
  const res = await fetch(`${API_BASE}/xp/logs`, {
    method: "GET",
    headers: authHeaders(),
  });

  return handleResponse(res);
}

async function apiRequest(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: options.method || "GET",
    headers: {
      ...authHeaders(),
      ...(options.headers || {}),
    },
    body: options.body,
  });

  return handleResponse(res);
}

export async function getMe() {
  return apiRequest("/me");
}

// Update profile (display_name, avatar_url)
export async function updateProfile(data) {
  return apiRequest("/me", {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

// Change password
export async function changePassword(data) {
  return apiRequest("/me/change-password", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
