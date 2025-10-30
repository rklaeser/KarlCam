/**
 * TypeScript interfaces for application state management
 */

import { CameraConditions, Webcam, SystemStatus, PublicConfig } from './api';

// Loading states for different data types
export interface LoadingState {
  cameras: boolean;
  webcams: boolean;
  systemStatus: boolean;
  config: boolean;
}

// Error states for different data types  
export interface ErrorState {
  cameras: string | null;
  webcams: string | null;
  systemStatus: string | null;
  config: string | null;
  global: string | null;
}

// Main application state interface
export interface AppState {
  // Data
  cameras: CameraConditions[];
  webcams: Webcam[];
  systemStatus: SystemStatus | null;
  config: PublicConfig | null;
  
  // UI State
  loading: LoadingState;
  errors: ErrorState;
  
  // Metadata
  lastUpdated: {
    cameras: Date | null;
    webcams: Date | null;
    systemStatus: Date | null;
    config: Date | null;
  };
}

// Action types for state updates
export enum ActionType {
  // Loading actions
  SET_CAMERAS_LOADING = 'SET_CAMERAS_LOADING',
  SET_WEBCAMS_LOADING = 'SET_WEBCAMS_LOADING',
  SET_SYSTEM_STATUS_LOADING = 'SET_SYSTEM_STATUS_LOADING',
  SET_CONFIG_LOADING = 'SET_CONFIG_LOADING',
  
  // Success actions
  SET_CAMERAS_SUCCESS = 'SET_CAMERAS_SUCCESS',
  SET_WEBCAMS_SUCCESS = 'SET_WEBCAMS_SUCCESS',
  SET_SYSTEM_STATUS_SUCCESS = 'SET_SYSTEM_STATUS_SUCCESS',
  SET_CONFIG_SUCCESS = 'SET_CONFIG_SUCCESS',
  
  // Error actions
  SET_CAMERAS_ERROR = 'SET_CAMERAS_ERROR',
  SET_WEBCAMS_ERROR = 'SET_WEBCAMS_ERROR',
  SET_SYSTEM_STATUS_ERROR = 'SET_SYSTEM_STATUS_ERROR',
  SET_CONFIG_ERROR = 'SET_CONFIG_ERROR',
  SET_GLOBAL_ERROR = 'SET_GLOBAL_ERROR',
  
  // Clear actions
  CLEAR_ERRORS = 'CLEAR_ERRORS',
  RESET_STATE = 'RESET_STATE'
}

// Action interfaces
export interface LoadingAction {
  type: ActionType.SET_CAMERAS_LOADING | ActionType.SET_WEBCAMS_LOADING | 
        ActionType.SET_SYSTEM_STATUS_LOADING | ActionType.SET_CONFIG_LOADING;
  payload: boolean;
}

export interface CamerasSuccessAction {
  type: ActionType.SET_CAMERAS_SUCCESS;
  payload: CameraConditions[];
}

export interface WebcamsSuccessAction {
  type: ActionType.SET_WEBCAMS_SUCCESS;
  payload: Webcam[];
}

export interface SystemStatusSuccessAction {
  type: ActionType.SET_SYSTEM_STATUS_SUCCESS;
  payload: SystemStatus;
}

export interface ConfigSuccessAction {
  type: ActionType.SET_CONFIG_SUCCESS;
  payload: PublicConfig;
}

export interface ErrorAction {
  type: ActionType.SET_CAMERAS_ERROR | ActionType.SET_WEBCAMS_ERROR | 
        ActionType.SET_SYSTEM_STATUS_ERROR | ActionType.SET_CONFIG_ERROR | 
        ActionType.SET_GLOBAL_ERROR;
  payload: string;
}

export interface ClearErrorsAction {
  type: ActionType.CLEAR_ERRORS;
}

export interface ResetStateAction {
  type: ActionType.RESET_STATE;
}

// Union type for all possible actions
export type AppAction = 
  | LoadingAction
  | CamerasSuccessAction
  | WebcamsSuccessAction  
  | SystemStatusSuccessAction
  | ConfigSuccessAction
  | ErrorAction
  | ClearErrorsAction
  | ResetStateAction;