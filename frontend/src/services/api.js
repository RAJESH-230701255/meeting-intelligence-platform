import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const auth = {
  forgotPassword: (email) => api.post('/api/auth/forgot-password', { email }),
  resetPassword: (token, new_password) => api.post('/api/auth/reset-password', { token, new_password }),
};

export const notifications = {
  getNotifications: () => api.get('/api/notifications'),
  markRead: (id) => api.put(`/api/notifications/${id}/read`),
  markAllRead: () => api.put('/api/notifications/read-all'),
};

export default api;
