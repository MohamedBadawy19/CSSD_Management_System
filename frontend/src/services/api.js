import axios from "axios";

// Change this to your backend URL
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

const api = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// Attach token to every request automatically
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 globally (auto-logout)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.clear();
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// ─── Auth ───────────────────────────────────────────────
export async function login(username, password) {
  try {
    const { data } = await api.post("/auth/login", { username, password });
    // Expected response: { token, role, username }
    return data;
  } catch (err) {
    throw new Error(err.response?.data?.message || "Login failed");
  }
}

export async function logout() {
  try {
    await api.post("/auth/logout");
  } finally {
    localStorage.clear();
  }
}

// ─── Requests ────────────────────────────────────────────
export async function getRequests(params = {}) {
  const { data } = await api.get("/requests", { params });
  return data;
}

export async function createRequest(payload) {
  const { data } = await api.post("/requests", payload);
  return data;
}

export async function updateRequestStatus(id, status) {
  const { data } = await api.patch(`/requests/${id}/status`, { status });
  return data;
}

// ─── Inventory ───────────────────────────────────────────
export async function getInventory() {
  const { data } = await api.get("/inventory");
  return data;
}

export default api;
