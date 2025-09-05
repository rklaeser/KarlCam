import axios from 'axios';

const BASE_URL = process.env.NODE_ENV === 'production' ? 'https://api.karl.cam' : 'http://localhost:8002';

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add a response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Export the base URL for use in non-axios calls (like fetch in HTML strings)
export const API_BASE_URL = BASE_URL;

export default api;