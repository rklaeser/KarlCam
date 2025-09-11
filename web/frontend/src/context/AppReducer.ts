/**
 * Reducer for KarlCam application state management
 * Handles all state updates in a predictable, centralized way
 */

import { AppState, AppAction, ActionType } from '../types';

/**
 * Initial state for the application
 */
export const initialState: AppState = {
  // Data
  cameras: [],
  webcams: [],
  systemStatus: null,
  config: null,
  
  // UI State
  loading: {
    cameras: false,
    webcams: false,
    systemStatus: false,
    config: false,
  },
  
  errors: {
    cameras: null,
    webcams: null,
    systemStatus: null,
    config: null,
    global: null,
  },
  
  // Metadata
  lastUpdated: {
    cameras: null,
    webcams: null,
    systemStatus: null,
    config: null,
  },
};

/**
 * Application state reducer
 * Handles all state updates based on dispatched actions
 */
export function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    // Loading states
    case ActionType.SET_CAMERAS_LOADING:
      return {
        ...state,
        loading: { ...state.loading, cameras: action.payload },
        errors: { ...state.errors, cameras: null }, // Clear previous errors when starting to load
      };
      
    case ActionType.SET_WEBCAMS_LOADING:
      return {
        ...state,
        loading: { ...state.loading, webcams: action.payload },
        errors: { ...state.errors, webcams: null },
      };
      
    case ActionType.SET_SYSTEM_STATUS_LOADING:
      return {
        ...state,
        loading: { ...state.loading, systemStatus: action.payload },
        errors: { ...state.errors, systemStatus: null },
      };
      
    case ActionType.SET_CONFIG_LOADING:
      return {
        ...state,
        loading: { ...state.loading, config: action.payload },
        errors: { ...state.errors, config: null },
      };

    // Success states
    case ActionType.SET_CAMERAS_SUCCESS:
      return {
        ...state,
        cameras: action.payload,
        loading: { ...state.loading, cameras: false },
        errors: { ...state.errors, cameras: null },
        lastUpdated: { ...state.lastUpdated, cameras: new Date() },
      };
      
    case ActionType.SET_WEBCAMS_SUCCESS:
      return {
        ...state,
        webcams: action.payload,
        loading: { ...state.loading, webcams: false },
        errors: { ...state.errors, webcams: null },
        lastUpdated: { ...state.lastUpdated, webcams: new Date() },
      };
      
    case ActionType.SET_SYSTEM_STATUS_SUCCESS:
      return {
        ...state,
        systemStatus: action.payload,
        loading: { ...state.loading, systemStatus: false },
        errors: { ...state.errors, systemStatus: null },
        lastUpdated: { ...state.lastUpdated, systemStatus: new Date() },
      };
      
    case ActionType.SET_CONFIG_SUCCESS:
      return {
        ...state,
        config: action.payload,
        loading: { ...state.loading, config: false },
        errors: { ...state.errors, config: null },
        lastUpdated: { ...state.lastUpdated, config: new Date() },
      };

    // Error states
    case ActionType.SET_CAMERAS_ERROR:
      return {
        ...state,
        loading: { ...state.loading, cameras: false },
        errors: { ...state.errors, cameras: action.payload },
      };
      
    case ActionType.SET_WEBCAMS_ERROR:
      return {
        ...state,
        loading: { ...state.loading, webcams: false },
        errors: { ...state.errors, webcams: action.payload },
      };
      
    case ActionType.SET_SYSTEM_STATUS_ERROR:
      return {
        ...state,
        loading: { ...state.loading, systemStatus: false },
        errors: { ...state.errors, systemStatus: action.payload },
      };
      
    case ActionType.SET_CONFIG_ERROR:
      return {
        ...state,
        loading: { ...state.loading, config: false },
        errors: { ...state.errors, config: action.payload },
      };
      
    case ActionType.SET_GLOBAL_ERROR:
      return {
        ...state,
        errors: { ...state.errors, global: action.payload },
      };

    // Utility actions
    case ActionType.CLEAR_ERRORS:
      return {
        ...state,
        errors: {
          cameras: null,
          webcams: null,
          systemStatus: null,
          config: null,
          global: null,
        },
      };
      
    case ActionType.RESET_STATE:
      return initialState;

    default:
      return state;
  }
}