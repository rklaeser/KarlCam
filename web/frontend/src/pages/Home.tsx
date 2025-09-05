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
  const [mapLoading, setMapLoading] = useState(true);
  const [camerasLoading, setCamerasLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);


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
      
      // First, load webcam locations to show the map quickly
      const webcamsRes = await api.get('/api/public/webcams');
      setWebcams(webcamsRes.data.webcams || []);
      setMapLoading(false);
      
      // Then load camera conditions asynchronously
      loadCamerasOnly();
      
    } catch (err) {
      console.error('Error loading webcams:', err);
      setError('Failed to load webcam locations. The service may be starting up.');
      setMapLoading(false);
      setCamerasLoading(false);
    }
  };

  const loadCamerasOnly = async () => {
    try {
      setCamerasLoading(true);
      const camerasRes = await api.get('/api/public/cameras');
      setCameras(camerasRes.data.cameras || []);
      setCamerasLoading(false);
    } catch (err) {
      console.error('Error loading camera conditions:', err);
      // Don't show error for camera conditions - just log it
      setCamerasLoading(false);
    }
  };

  const refreshData = () => {
    setMapLoading(true);
    setCamerasLoading(true);
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
        
        {/* Loading overlay - only show before map loads */}
        {mapLoading && (
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center" style={{ zIndex: 1000 }}>
            <div className="text-center text-white">
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-white mx-auto mb-6"></div>
              <h2 className="text-2xl font-bold mb-2">Loading Map...</h2>
              <p className="text-blue-100">Initializing San Francisco fog tracker</p>
            </div>
          </div>
        )}
        
        {/* Camera loading indicator - small overlay when map is visible but cameras are loading */}
        {!mapLoading && camerasLoading && (
          <div className="absolute top-20 left-1/2 transform -translate-x-1/2 bg-white/90 backdrop-blur-sm rounded-lg shadow-lg px-4 py-2 flex items-center gap-2" style={{ zIndex: 1000 }}>
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
            <span className="text-sm text-gray-700">Loading camera conditions...</span>
          </div>
        )}
        
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
      </div>
    </div>
  );
};

export default Home;