/**
 * Centralized data fetching service for KarlCam API
 * Handles all API calls with consistent error handling and response processing
 */

import api from './api';
import {
  CamerasListResponse,
  WebcamsListResponse,
  SystemStatus,
  PublicConfig,
  SystemStatsResponse,
  CameraDetailResponse,
  CameraLatestResponse
} from '../types';

/**
 * Service class for all KarlCam API interactions
 */
export class DataService {
  /**
   * Fetch all cameras with current fog conditions
   */
  async getCameras(): Promise<CamerasListResponse> {
    try {
      const response = await api.get<CamerasListResponse>('/api/public/cameras');
      return response.data;
    } catch (error) {
      console.error('Error fetching cameras:', error);
      throw new Error('Failed to load camera conditions. The service may be starting up.');
    }
  }

  /**
   * Fetch all webcam locations (for map display)
   */
  async getWebcams(): Promise<WebcamsListResponse> {
    try {
      const response = await api.get<WebcamsListResponse>('/api/public/webcams');
      return response.data;
    } catch (error) {
      console.error('Error fetching webcams:', error);
      throw new Error('Failed to load webcam locations. The service may be starting up.');
    }
  }

  /**
   * Fetch system status (including karlcam_mode for night mode detection)
   */
  async getSystemStatus(): Promise<SystemStatus> {
    try {
      const response = await api.get<SystemStatus>('/api/system/status');
      return response.data;
    } catch (error) {
      console.error('Error fetching system status:', error);
      throw new Error('Failed to load system status.');
    }
  }

  /**
   * Fetch public configuration settings
   */
  async getPublicConfig(): Promise<PublicConfig> {
    try {
      const response = await api.get<PublicConfig>('/api/config/public');
      return response.data;
    } catch (error) {
      console.error('Error fetching config:', error);
      throw new Error('Failed to load configuration.');
    }
  }

  /**
   * Fetch system-wide fog statistics
   */
  async getSystemStats(): Promise<SystemStatsResponse> {
    try {
      const response = await api.get<SystemStatsResponse>('/api/system/stats');
      return response.data;
    } catch (error) {
      console.error('Error fetching system stats:', error);
      throw new Error('Failed to load system statistics.');
    }
  }

  /**
   * Fetch detailed information for a specific camera
   * @param cameraId - The camera identifier
   * @param hours - Hours of historical data to include (optional)
   */
  async getCameraDetail(cameraId: string, hours?: number): Promise<CameraDetailResponse> {
    try {
      const params = hours ? { hours } : {};
      const response = await api.get<CameraDetailResponse>(
        `/api/public/cameras/${cameraId}`, 
        { params }
      );
      return response.data;
    } catch (error) {
      console.error(`Error fetching camera detail for ${cameraId}:`, error);
      throw new Error(`Failed to load details for camera ${cameraId}.`);
    }
  }

  /**
   * Get the latest camera data with on-demand refresh
   * Fetches fresh image and analysis if data is stale (>30 minutes)
   * @param cameraId - The camera identifier
   */
  async getCameraLatest(cameraId: string): Promise<CameraLatestResponse> {
    try {
      const response = await api.get<CameraLatestResponse>(
        `/api/public/cameras/${cameraId}/latest`
      );
      return response.data;
    } catch (error) {
      console.error(`Error fetching latest data for ${cameraId}:`, error);
      throw new Error(`Failed to load latest data for camera ${cameraId}.`);
    }
  }

  /**
   * Get the latest image URL for a specific camera
   * @param cameraId - The camera identifier
   * @deprecated Use getCameraLatest() instead for full data with on-demand refresh
   */
  async getLatestImageUrl(cameraId: string): Promise<string> {
    try {
      const data = await this.getCameraLatest(cameraId);
      return data.image_url;
    } catch (error) {
      console.error(`Error fetching latest image for ${cameraId}:`, error);
      throw new Error(`Failed to load latest image for camera ${cameraId}.`);
    }
  }
}

// Create and export a singleton instance
export const dataService = new DataService();

// Export individual methods for convenience
export const {
  getCameras,
  getWebcams,
  getSystemStatus,
  getPublicConfig,
  getSystemStats,
  getCameraDetail,
  getCameraLatest,
  getLatestImageUrl
} = dataService;