/**
 * KarlCam Application Context
 * Provides centralized state management for the entire application
 */

import React, { createContext, useContext, useReducer, useCallback, useEffect, useRef } from 'react';
import { appReducer, initialState } from './AppReducer';
import { dataService } from '../services/dataService';
import { AppState, ActionType } from '../types';

/**
 * Context interface defining available methods and state
 */
interface AppContextType {
  // State
  state: AppState;
  
  // Data fetching methods
  fetchCameras: () => Promise<void>;
  fetchWebcams: () => Promise<void>;
  fetchSystemStatus: () => Promise<void>;
  fetchConfig: () => Promise<void>;
  fetchAllData: () => Promise<void>;
  
  // Utility methods
  clearErrors: () => void;
  resetState: () => void;
  refreshData: () => Promise<void>;
  
  // Computed values
  isNightMode: boolean;
  hasAnyError: boolean;
  isInitialLoading: boolean;
}

/**
 * React Context for app state
 */
const AppContext = createContext<AppContextType | undefined>(undefined);

/**
 * Props for AppProvider component
 */
interface AppProviderProps {
  children: React.ReactNode;
  autoRefresh?: boolean;
  refreshInterval?: number; // in milliseconds
}

/**
 * AppProvider component that wraps the app with context state
 */
export const AppProvider: React.FC<AppProviderProps> = ({ 
  children, 
  autoRefresh = true,
  refreshInterval = 5 * 60 * 1000 // 5 minutes default
}) => {
  const [state, dispatch] = useReducer(appReducer, initialState);
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Clear any existing interval when component unmounts or interval changes
  useEffect(() => {
    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, []);

  /**
   * Fetch cameras data
   */
  const fetchCameras = useCallback(async () => {
    dispatch({ type: ActionType.SET_CAMERAS_LOADING, payload: true });
    
    try {
      const response = await dataService.getCameras();
      dispatch({ type: ActionType.SET_CAMERAS_SUCCESS, payload: response.cameras });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error occurred';
      dispatch({ type: ActionType.SET_CAMERAS_ERROR, payload: message });
    }
  }, []);

  /**
   * Fetch webcams data
   */
  const fetchWebcams = useCallback(async () => {
    dispatch({ type: ActionType.SET_WEBCAMS_LOADING, payload: true });
    
    try {
      const response = await dataService.getWebcams();
      dispatch({ type: ActionType.SET_WEBCAMS_SUCCESS, payload: response.webcams });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error occurred';
      dispatch({ type: ActionType.SET_WEBCAMS_ERROR, payload: message });
    }
  }, []);

  /**
   * Fetch system status
   */
  const fetchSystemStatus = useCallback(async () => {
    dispatch({ type: ActionType.SET_SYSTEM_STATUS_LOADING, payload: true });
    
    try {
      const status = await dataService.getSystemStatus();
      dispatch({ type: ActionType.SET_SYSTEM_STATUS_SUCCESS, payload: status });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error occurred';
      dispatch({ type: ActionType.SET_SYSTEM_STATUS_ERROR, payload: message });
    }
  }, []);

  /**
   * Fetch configuration
   */
  const fetchConfig = useCallback(async () => {
    dispatch({ type: ActionType.SET_CONFIG_LOADING, payload: true });
    
    try {
      const config = await dataService.getPublicConfig();
      dispatch({ type: ActionType.SET_CONFIG_SUCCESS, payload: config });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error occurred';
      dispatch({ type: ActionType.SET_CONFIG_ERROR, payload: message });
    }
  }, []);

  /**
   * Fetch all data at once (for initial load)
   */
  const fetchAllData = useCallback(async () => {
    try {
      // Start system status and webcams in parallel
      await Promise.allSettled([
        fetchSystemStatus(),
        fetchWebcams(),
      ]);
      
      // Note: Camera fetching will be handled by the auto-refresh logic
      // which checks night mode status automatically
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to load application data';
      dispatch({ type: ActionType.SET_GLOBAL_ERROR, payload: message });
    }
  }, [fetchSystemStatus, fetchWebcams]);

  /**
   * Refresh data (used by refresh buttons)
   */
  const refreshData = useCallback(async () => {
    await fetchAllData();
  }, [fetchAllData]);

  /**
   * Clear all errors
   */
  const clearErrors = useCallback(() => {
    dispatch({ type: ActionType.CLEAR_ERRORS });
  }, []);

  /**
   * Reset entire state
   */
  const resetState = useCallback(() => {
    dispatch({ type: ActionType.RESET_STATE });
  }, []);

  // Computed values
  const isNightMode = state.systemStatus?.karlcam_mode === 1;
  const hasAnyError = !!(
    state.errors.cameras || 
    state.errors.webcams || 
    state.errors.systemStatus || 
    state.errors.config || 
    state.errors.global
  );
  const isInitialLoading = 
    (state.loading.systemStatus || state.loading.webcams) && 
    !state.systemStatus && 
    state.webcams.length === 0;

  // Set up auto-refresh interval
  useEffect(() => {
    if (autoRefresh && refreshInterval > 0) {
      // Initial load
      fetchAllData();
      
      // Set up periodic refresh (but only for cameras, not webcams/status)
      refreshIntervalRef.current = setInterval(() => {
        if (!isNightMode) {
          fetchCameras(); // Only refresh cameras data, not static webcam locations
        }
      }, refreshInterval);
    } else {
      // Load once if auto-refresh is disabled
      fetchAllData();
    }

    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, [autoRefresh, refreshInterval, fetchAllData, fetchCameras, isNightMode]);

  // Fetch cameras once system status is loaded (if not in night mode)
  useEffect(() => {
    if (state.systemStatus && !isNightMode && state.cameras.length === 0) {
      fetchCameras();
    }
  }, [state.systemStatus, isNightMode, state.cameras.length, fetchCameras]);

  const contextValue: AppContextType = {
    state,
    fetchCameras,
    fetchWebcams,
    fetchSystemStatus,
    fetchConfig,
    fetchAllData,
    clearErrors,
    resetState,
    refreshData,
    isNightMode,
    hasAnyError,
    isInitialLoading,
  };

  return <AppContext.Provider value={contextValue}>{children}</AppContext.Provider>;
};

/**
 * Custom hook to use the app context
 */
export const useAppContext = (): AppContextType => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};

/**
 * Convenience hooks for specific data
 */
export const useAppData = () => {
  const { state, isNightMode, hasAnyError, isInitialLoading } = useAppContext();
  
  return {
    cameras: state.cameras,
    webcams: state.webcams,
    systemStatus: state.systemStatus,
    config: state.config,
    loading: state.loading,
    errors: state.errors,
    lastUpdated: state.lastUpdated,
    isNightMode,
    hasAnyError,
    isInitialLoading,
  };
};

export const useAppActions = () => {
  const { 
    fetchCameras, 
    fetchWebcams, 
    fetchSystemStatus, 
    fetchConfig,
    fetchAllData,
    clearErrors, 
    resetState, 
    refreshData 
  } = useAppContext();
  
  return {
    fetchCameras,
    fetchWebcams,
    fetchSystemStatus,
    fetchConfig,
    fetchAllData,
    clearErrors,
    resetState,
    refreshData,
  };
};