/**
 * Central export for all TypeScript types used in KarlCam frontend
 */

// API types
export type {
  CameraConditions,
  Webcam,
  SystemStatus,
  PublicConfig,
  CamerasListResponse,
  WebcamsListResponse,
  SystemStatsResponse,
  HistoryItem,
  CameraDetailResponse
} from './api';

// State management types
export type {
  LoadingState,
  ErrorState,
  AppState,
  LoadingAction,
  CamerasSuccessAction,
  WebcamsSuccessAction,
  SystemStatusSuccessAction,
  ConfigSuccessAction,
  ErrorAction,
  ClearErrorsAction,
  ResetStateAction,
  AppAction
} from './state';

export { ActionType } from './state';