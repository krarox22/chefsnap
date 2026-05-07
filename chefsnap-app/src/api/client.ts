import axios from "axios";

const API_BASE = process.env.EXPO_PUBLIC_API_BASE ?? "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 30_000,
});

// Set by TokenBridge in _layout.tsx once ClerkProvider is mounted.
// Interceptor calls this on every request so the token stays fresh.
let _getToken: (() => Promise<string | null>) | null = null;

export function setTokenProvider(fn: () => Promise<string | null>): void {
  _getToken = fn;
}

apiClient.interceptors.request.use(async (config) => {
  if (_getToken) {
    const token = await _getToken();
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
