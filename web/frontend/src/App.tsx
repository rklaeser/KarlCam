import React, { useState, useEffect } from 'react';
import axios from 'axios';
import FogMap from './components/FogMap';
import CameraTable from './components/CameraTable';
import AboutCreator from './components/AboutCreator';
import HowItWorks from './components/HowItWorks';
import './App.css';

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

const App: React.FC = () => {
  const [webcams, setWebcams] = useState<Webcam[]>([]);
  const [cameras, setCameras] = useState<CameraConditions[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const API_BASE = process.env.NODE_ENV === 'production' ? 'https://api.karl.cam' : 'http://localhost:8002';

  useEffect(() => {
    loadData();
    // Refresh data every 5 minutes
    const interval = setInterval(loadData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      setError(null);
      
      // Load webcam locations and current conditions for each camera
      const [webcamsRes, camerasRes] = await Promise.all([
        axios.get(`${API_BASE}/api/public/webcams`),
        axios.get(`${API_BASE}/api/public/cameras`)
      ]);
      
      setWebcams(webcamsRes.data.webcams || []);
      setCameras(camerasRes.data.cameras || []);
      setLastUpdated(new Date());
      setLoading(false);

    } catch (err) {
      console.error('Error loading data:', err);
      setError('Failed to load fog data. The service may be starting up.');
      setLoading(false);
    }
  };

  const refreshData = () => {
    setLoading(true);
    loadData();
  };

  if (loading && webcams.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex flex-col">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center text-white">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-white mx-auto mb-6"></div>
            <h2 className="text-2xl font-bold mb-2">Loading San Francisco Fog Data...</h2>
            <p className="text-blue-100">Loading webcam locations...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error && webcams.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex flex-col">
        <div className="flex-1 flex items-center justify-center">
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
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex flex-col">
      <header className="bg-white/10 backdrop-blur-md border-b border-white/20">
        <div className="container mx-auto px-6 py-4 flex justify-between items-center">
          <div className="text-white">
            <h1 className="text-3xl font-bold flex items-center gap-2">
              🌫️ KarlCam
            </h1>
            <p className="text-blue-100">Live fog tracking for San Francisco</p>
          </div>
          
          <div className="text-white">
            <p className="text-sm">
              Who is{' '}
              <a 
                href="https://x.com/KarlTheFog" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-yellow-300 hover:text-yellow-200 underline"
              >
                Karl the Fog
              </a>
              ?
            </p>
          </div>
        </div>
      </header>

      <main className="flex-1 container mx-auto px-6 py-8 space-y-8">
        {/* Map Panel */}
        <section className="bg-white/95 backdrop-blur-sm rounded-lg shadow-lg p-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">San Francisco Fog Map</h2>
          <FogMap 
            webcams={webcams}
            cameras={cameras}
          />
        </section>

        {/* Camera Table Panel */}
        <section className="bg-white/95 backdrop-blur-sm rounded-lg shadow-lg p-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Camera Conditions</h2>
          <CameraTable 
            cameras={cameras}
            loading={loading}
          />
        </section>

        <section className="bg-white/95 backdrop-blur-sm rounded-lg shadow-lg">
          <AboutCreator />
        </section>

        <section className="bg-white/95 backdrop-blur-sm rounded-lg shadow-lg">
          <HowItWorks />
        </section>
      </main>

      <footer className="bg-white/10 backdrop-blur-md border-t border-white/20 text-white py-6">
        <div className="container mx-auto px-6">
          <div className="text-center">
            <p className="text-blue-100 mb-4 font-semibold">Webcam Sources</p>
            <div className="flex flex-wrap justify-center gap-4">
              {webcams.map(webcam => (
                <div key={webcam.id} className="text-sm bg-white/20 px-3 py-1 rounded-full">
                  📹 {webcam.name}
                </div>
              ))}
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;