// API service functions for labeler management

import axios from 'axios';
import {
  LabelerConfig,
  LabelerPerformance,
  LabelerDetailedPerformance,
  LabelerComparison,
  DailyPerformance
} from '../types/labeler';

// Use environment variable for API base URL, fallback to localhost for development
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    throw error;
  }
);

export const labelerApi = {
  // ============= CONFIGURATION (READ-ONLY) =============
  
  async getAllLabelers(): Promise<LabelerConfig[]> {
    const response = await api.get('/api/labelers');
    return response.data;
  },

  async getLabeler(name: string): Promise<LabelerConfig> {
    const response = await api.get(`/api/labelers/${name}`);
    return response.data;
  },

  // ============= PERFORMANCE MONITORING =============

  async getPerformanceSummary(): Promise<LabelerPerformance[]> {
    const response = await api.get('/api/labelers/performance/summary');
    return response.data;
  },

  async getLabelerPerformance(name: string): Promise<LabelerDetailedPerformance> {
    const response = await api.get(`/api/labelers/${name}/performance`);
    return response.data;
  },

  async getLabelerComparison(days: number = 7, limit: number = 100): Promise<LabelerComparison[]> {
    const response = await api.get('/api/labelers/performance/comparison', {
      params: { days, limit }
    });
    return response.data;
  },

  async getDailyPerformance(days: number = 30, labelerName?: string): Promise<DailyPerformance[]> {
    const params: any = { days };
    if (labelerName) {
      params.labeler_name = labelerName;
    }
    
    const response = await api.get('/api/labelers/performance/daily', { params });
    return response.data;
  },

  // ============= UTILITY FUNCTIONS =============

  async testConnection(): Promise<boolean> {
    try {
      await api.get('/api/health');
      return true;
    } catch {
      return false;
    }
  },

  // Format cost in cents to dollars
  formatCost(cents: number | null): string {
    if (cents === null || cents === undefined) return 'N/A';
    return `$${(cents / 100).toFixed(3)}`;
  },

  // Format execution time
  formatExecutionTime(ms: number | null): string {
    if (ms === null || ms === undefined) return 'N/A';
    if (ms < 1000) return `${Math.round(ms)}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  },

  // Format confidence as percentage
  formatConfidence(confidence: number | null): string {
    if (confidence === null || confidence === undefined) return 'N/A';
    return `${Math.round(confidence * 100)}%`;
  },

  // Get status badge color
  getStatusColor(enabled: boolean): string {
    return enabled ? '#28a745' : '#dc3545';
  }
};

export default labelerApi;