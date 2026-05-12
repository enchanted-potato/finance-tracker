import axios from 'axios';
import { getIdToken } from 'firebase/auth';
import { auth } from '@/lib/firebase';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000',
});

// Request interceptor — call getIdToken() at request time, NEVER store the token string
apiClient.interceptors.request.use(async (config) => {
  // Read auth.currentUser inside the interceptor body (not in module scope)
  // to prevent stale-closure issues if the user object changes after interceptor setup
  const user = auth.currentUser;
  if (user) {
    const token = await getIdToken(user);
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor — 401 means expired/revoked token, force re-login
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Hard redirect clears React state cleanly — required after auth invalidation
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
