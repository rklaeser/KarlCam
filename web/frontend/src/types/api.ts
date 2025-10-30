/**
 * TypeScript interfaces for KarlCam API responses
 * These match the API response schemas defined in the backend
 */

// Camera data interfaces
export interface CameraConditions {
  id: string;
  name: string;
  lat: number;
  lon: number;
  description: string;
  fog_score: number;
  fog_level: string;
  confidence: number;
  weather_detected: boolean;
  weather_confidence: number;
  timestamp: string | null;
  active: boolean;
}

export interface Webcam {
  id: string;
  name: string;
  lat: number;
  lon: number;
  url: string;
  video_url: string;
  description: string;
  active: boolean;
}

export interface SystemStatus {
  karlcam_mode: number;
  description: string;
  updated_at: string | null;
  updated_by: string | null;
}

export interface PublicConfig {
  app_name: string;
  version: string;
  environment: string;
  fog_detection_threshold: number;
  foggy_conditions_threshold: number;
  default_location: {
    name: string;
    latitude: number;
    longitude: number;
  };
  default_history_hours: number;
  stats_period_hours: number;
  api_prefix: string;
}

// API Response wrapper interfaces
export interface CamerasListResponse {
  cameras: CameraConditions[];
  timestamp: string;
  count: number;
}

export interface WebcamsListResponse {
  webcams: Webcam[];
  timestamp: string;
  count: number;
}

export interface SystemStatsResponse {
  total_assessments: number;
  active_cameras: number;
  avg_fog_score: number;
  avg_confidence: number;
  foggy_conditions: number;
  last_update: string | null;
  period: string;
  error?: string;
}

// Historical data interfaces
export interface HistoryItem {
  fog_score: number;
  fog_level: string;
  confidence: number;
  timestamp: string | null;
  reasoning: string;
}

export interface CameraDetailResponse {
  camera: CameraConditions;
  history: HistoryItem[];
  history_hours: number;
  history_count: number;
}

// On-demand camera data with fresh analysis
export interface CameraLatestResponse {
  camera_id: string;
  camera_name: string;
  latitude: number;
  longitude: number;
  description: string;
  image_url: string;
  timestamp: string;
  age_minutes: number;
  fog_score: number | null;
  fog_level: string;
  confidence: number;
  reasoning: string;
  visibility_estimate: string;
  weather_conditions: string[];
}