import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://178.104.229.67:8000/api/v1';

const api = axios.create({
  baseURL: API_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
