import React, { useState, useEffect } from 'react';
import FogMap from '../components/FogMap';
import Sidebar from '../components/Sidebar';
import api, { API_BASE_URL } from '../services/api';

interface CameraConditions {
  id: string;
  name: string;
  lat: number;
  lon: number;
  timestamp: string;
  fog_score: number;
  fog_level: string;
  confidence: number;
  active: boolean;
}

interface Webcam {
  id: string;
  name: string;
  lat: number;
  lon: number;
  url: string;
  description: string;
  active: boolean;
}

const Home: React.FC = () => {
  const [webcams, setWebcams] = useState<Webcam[]>([]);
  const [cameras, setCameras] = useState<CameraConditions[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [systemStatus, setSystemStatus] = useState<{karlcam_mode: number} | null>(null);
  
  // Check if we're in night mode based on system status
  const isNightMode = () => {
    return systemStatus?.karlcam_mode === 1;
  };


  useEffect(() => {
    // Load map immediately, then load camera data
    loadMapAndCameras();
    // Refresh data every 5 minutes
    const interval = setInterval(loadCamerasOnly, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const loadMapAndCameras = async () => {
    try {
      setError(null);
      
      // Load system status and webcam locations in parallel
      const [statusRes, webcamsRes] = await Promise.all([
        api.get('/api/system/status'),
        api.get('/api/public/webcams')
      ]);
      
      setSystemStatus(statusRes.data);
      setWebcams(webcamsRes.data.webcams || []);
      
      // Load camera conditions only if not in night mode
      if (statusRes.data.karlcam_mode !== 1) {
        loadCamerasOnly();
      }
      
    } catch (err) {
      console.error('Error loading data:', err);
      setError('Failed to load data. The service may be starting up.');
    }
  };

  const loadCamerasOnly = async () => {
    try {
      const camerasRes = await api.get('/api/public/cameras');
      setCameras(camerasRes.data.cameras || []);
    } catch (err) {
      console.error('Error loading camera conditions:', err);
      // Don't show error for camera conditions - just log it
    }
  };

  const refreshData = () => {
    loadMapAndCameras();
  };


  return (
    <div className="h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex flex-col overflow-hidden">
      {/* Hamburger Menu Button */}
      <button
        onClick={() => setSidebarOpen(true)}
        className="fixed top-6 right-6 bg-white/90 backdrop-blur-sm text-gray-800 p-3 rounded-full shadow-lg hover:bg-white hover:shadow-xl transition-all duration-300"
        style={{ zIndex: 9999 }}
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      {/* Sidebar */}
      <Sidebar 
        isOpen={sidebarOpen} 
        onClose={() => setSidebarOpen(false)} 
      />

      {/* Full-width Map - takes full viewport */}
      <div className="flex-1 relative">
        <FogMap 
          webcams={webcams}
          cameras={cameras}
          apiBase={API_BASE_URL}
        />
        
        
        {/* Error overlay */}
        {error && webcams.length === 0 && (
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center" style={{ zIndex: 1000 }}>
            <div className="text-center text-white">
              <h2 className="text-2xl font-bold mb-4">Unable to Load Fog Data</h2>
              <p className="text-blue-100 mb-6">{error}</p>
              <button 
                onClick={refreshData} 
                className="bg-white text-blue-600 px-6 py-3 rounded-lg font-semibold hover:bg-blue-50 transition-colors"
              >
                Try Again
              </button>
            </div>
          </div>
        )}

        {/* Night mode overlay - shown when system status indicates night mode */}
        {!error && isNightMode() && (
          <div className="absolute inset-0 bg-gradient-to-br from-gray-900 to-blue-900 flex items-center justify-center" style={{ zIndex: 1000 }}>
            <div className="text-center text-white max-w-md mx-auto px-6">
              <div className="text-6xl mb-6">🌙</div>
              <h2 className="text-3xl font-bold mb-4">KarlCam is Sleeping</h2>
              <p className="text-blue-100 mb-6 leading-relaxed">
                Fog tracking is currently offline. We collect images and analyze conditions daily from 9 AM to 5 PM PT.
              </p>
              <p className="text-sm text-blue-200 mb-8">
                Check back tomorrow at 9 AM for fresh fog data!
              </p>
              <button 
                onClick={refreshData} 
                className="bg-white/20 backdrop-blur-sm text-white border border-white/30 px-6 py-3 rounded-lg font-semibold hover:bg-white/30 transition-all duration-300"
              >
                Check Again
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Home;