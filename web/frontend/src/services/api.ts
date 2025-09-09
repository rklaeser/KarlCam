import axios from 'axios';

const getApiUrl = (environment: string | undefined): string => {
  switch(environment) {
    case 'staging':
      return 'https://api.staging.karl.cam';
    case 'production':
      return 'https://api.karl.cam';
    case 'development':
    default:
      return 'http://localhost:8002';
  }
};

const BASE_URL = getApiUrl(process.env.REACT_APP_ENVIRONMENT);

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