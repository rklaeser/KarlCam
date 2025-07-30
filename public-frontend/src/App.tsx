import React, { useState, useEffect } from 'react';
import axios from 'axios';
import FogMap from './components/FogMap';
import CurrentConditionsComponent from './components/CurrentConditions';
import FogChart from './components/FogChart';
import './App.css';

interface CurrentConditionsData {
  timestamp: string;
  location: {
    name: string;
    lat: number;
    lon: number;
  };
  fog_score: number;
  fog_level: string;
  confidence: number;
  weather_detected: boolean;
  weather_confidence: number;
}

interface HistoryEntry {
  timestamp: string;
  sf_time: string;
  fog_score: number;
  fog_level: string;
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
  const [currentConditions, setCurrentConditions] = useState<CurrentConditionsData | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [webcams, setWebcams] = useState<Webcam[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const API_BASE = process.env.NODE_ENV === 'production' ? '' : 'http://localhost:8000';

  useEffect(() => {
    loadData();
    // Refresh data every 5 minutes
    const interval = setInterval(loadData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      setError(null);
      
      // Load all data in parallel
      const [currentRes, historyRes, webcamsRes] = await Promise.all([
        axios.get(`${API_BASE}/api/public/current`),
        axios.get(`${API_BASE}/api/public/history?hours=24`),
        axios.get(`${API_BASE}/api/public/webcams`)
      ]);

      setCurrentConditions(currentRes.data);
      setHistory(historyRes.data.history || []);
      setWebcams(webcamsRes.data.webcams || []);
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

  if (loading && !currentConditions) {
    return (
      <div className="app">
        <div className="loading-screen">
          <div className="loading-spinner"></div>
          <h2>Loading San Francisco Fog Data...</h2>
          <p>Analyzing current conditions with AI</p>
        </div>
      </div>
    );
  }

  if (error && !currentConditions) {
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
            <h1>🌫️ San Francisco Fog Tracker</h1>
            <p>Real-time fog detection powered by AI</p>
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
        <div className="content-grid">
          {/* Current Conditions Panel */}
          <section className="conditions-panel">
            <CurrentConditionsComponent 
              conditions={currentConditions} 
              loading={loading}
            />
          </section>

          {/* Map Panel */}
          <section className="map-panel">
            <h2>San Francisco Fog Map</h2>
            <FogMap 
              webcams={webcams}
              currentConditions={currentConditions}
            />
          </section>

          {/* Chart Panel */}
          <section className="chart-panel">
            <h2>24-Hour Fog History</h2>
            <FogChart history={history} />
            {history.length === 0 && (
              <div className="no-data">
                <p>No historical data available yet.</p>
                <p>Data will appear as the collector runs throughout the day.</p>
              </div>
            )}
          </section>
        </div>
      </main>

      <footer className="app-footer">
        <div className="footer-content">
          <div className="tech-info">
            <p>
              Powered by <strong>CLIP AI</strong> for fog detection • 
              Data from <a href="https://www.fogcam.org" target="_blank" rel="noopener noreferrer">FogCam</a> • 
              Updates every hour during daylight
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