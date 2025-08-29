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
  weather_detected: boolean;
  weather_confidence: number;
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

  const API_BASE = process.env.NODE_ENV === 'production' ? '' : 'http://localhost:8002';

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
      <div className="app">
        <div className="loading-screen">
          <div className="loading-spinner"></div>
          <h2>Loading San Francisco Fog Data...</h2>
          <p>Loading webcam locations...</p>
        </div>
      </div>
    );
  }

  if (error && webcams.length === 0) {
    return (
      <div className="app">
        <div className="error-screen">
          <h2>Unable to Load Fog Data</h2>
          <p>{error}</p>
          <button onClick={refreshData} className="retry-btn">
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="title-section">
            <h1>🌫️ KarlCam</h1>
            <p>The San Francisco Fog is named Karl</p>
          </div>
          
          <div className="update-section">
            {lastUpdated && (
              <div className="last-updated">
                Last updated: {lastUpdated.toLocaleTimeString()}
              </div>
            )}
            <button 
              onClick={refreshData} 
              className="refresh-btn"
              disabled={loading}
            >
              {loading ? '🔄' : '↻'} Refresh
            </button>
          </div>
        </div>
      </header>

      <main className="main-content">
        {/* Map Panel */}
        <section className="map-panel">
          <h2>San Francisco Fog Map</h2>
          <FogMap 
            webcams={webcams}
            cameras={cameras}
          />
        </section>

        {/* Camera Table Panel */}
        <section className="camera-table-panel">
          <h2>Camera Conditions</h2>
          <CameraTable 
            cameras={cameras}
            loading={loading}
          />
        </section>

        <section>
          <AboutCreator />
        </section>

        <section>
          <HowItWorks />
        </section>
      </main>

      <footer className="app-footer">
        <div className="footer-content">
          <div className="tech-info">
            <p>
              Webcams
            </p>
          </div>
          
          <div className="webcam-info">
            {webcams.map(webcam => (
              <div key={webcam.id} className="webcam-credit">
                📹 {webcam.name}
              </div>
            ))}
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;