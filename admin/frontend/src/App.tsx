import React, { useState, useEffect } from 'react';
import axios from 'axios';
import CameraManager from './CameraManager';
import './App.css';

// Simplified types for the new architecture
interface GeminiLabel {
  fog_score: number;
  fog_level: string;
  confidence: number;
  reasoning?: string;
  visibility_estimate?: string;
  weather_conditions?: string[];
}

interface WebcamInfo {
  id: string;
  name: string;
  description?: string;
}

interface ImageForView {
  id: string;
  filename: string;
  timestamp?: string;
  webcam_info: WebcamInfo;
  gemini_label: GeminiLabel;
  image_url: string;
  status: string;
}

interface FilterState {
  cameras: string[];
  timeRange: string;
  confidenceLevels: string[];
  fogLevels: string[];
}

const getFogLevelColor = (fogLevel: string): string => {
  switch (fogLevel.toLowerCase()) {
    case 'clear': return '#28a745';
    case 'light fog': return '#ffc107';
    case 'moderate fog': return '#fd7e14';
    case 'heavy fog': return '#dc3545';
    case 'very heavy fog': return '#6f42c1';
    default: return '#6c757d';
  }
};

const getConfidenceColor = (confidence: number): string => {
  if (confidence >= 0.9) return '#28a745';
  if (confidence >= 0.7) return '#ffc107';
  return '#dc3545';
};

const App: React.FC = () => {
  const [images, setImages] = useState<ImageForView[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedImage, setSelectedImage] = useState<ImageForView | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<FilterState>({
    cameras: [],
    timeRange: '24h',
    confidenceLevels: [],
    fogLevels: []
  });
  const [availableCameras, setAvailableCameras] = useState<string[]>([]);
  const [showCameraManager, setShowCameraManager] = useState(false);

  const API_BASE = process.env.NODE_ENV === 'production' ? 'https://admin-api.karl.cam' : 'http://localhost:8001';

  useEffect(() => {
    loadImages(true); // true = reset/initial load
    loadAvailableCameras();
  }, [filters]);

  const loadImages = async (reset: boolean = false) => {
    try {
      setLoading(true);
      
      // Build query parameters
      const params: any = {
        limit: 50,
        offset: reset ? 0 : (page - 1) * 50
      };

      // Add filters
      if (filters.cameras.length > 0) {
        params.cameras = filters.cameras.join(',');
      }
      if (filters.timeRange !== 'all') {
        params.time_range = filters.timeRange;
      }
      if (filters.confidenceLevels.length > 0) {
        params.confidence_filter = filters.confidenceLevels.join(',');
      }
      if (filters.fogLevels.length > 0) {
        params.fog_levels = filters.fogLevels.join(',');
      }

      const response = await axios.get(`${API_BASE}/api/images`, { params });
      const newImages = response.data;

      if (reset) {
        setImages(newImages);
        setPage(2);
      } else {
        setImages(prev => [...prev, ...newImages]);
        setPage(prev => prev + 1);
      }

      setHasMore(newImages.length === 50); // If we got less than 50, no more pages
      setLoading(false);
    } catch (error) {
      console.error('Error loading images:', error);
      setLoading(false);
    }
  };

  const loadAvailableCameras = async () => {
    try {
      // Load cameras from database for filtering
      const response = await axios.get(`${API_BASE}/api/cameras`);
      const cameraNames = response.data.map((cam: any) => cam.name);
      setAvailableCameras(cameraNames);
    } catch (error) {
      console.error('Error loading cameras:', error);
      // If cameras endpoint fails, just show empty list
      setAvailableCameras([]);
    }
  };

  const loadMore = () => {
    if (!loading && hasMore) {
      loadImages(false);
    }
  };

  const openImageDetails = (image: ImageForView) => {
    setSelectedImage(image);
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setSelectedImage(null);
  };

  const updateFilter = (filterType: keyof FilterState, value: string, checked: boolean) => {
    setFilters(prev => {
      const newFilters = { ...prev };
      
      if (filterType === 'timeRange') {
        newFilters.timeRange = value;
      } else {
        const currentArray = newFilters[filterType] as string[];
        if (checked) {
          newFilters[filterType] = [...currentArray, value];
        } else {
          newFilters[filterType] = currentArray.filter(item => item !== value);
        }
      }
      
      return newFilters;
    });
  };

  if (loading && images.length === 0) {
    return <div className="loading">Loading images...</div>;
  }

  return (
    <div className="app">
      <header className="header">
        <h1>KarlCam Image Browser</h1>
        <div className="stats">
          Total Images: {images.length}
          {hasMore && <span> (+ more available)</span>}
        </div>
      </header>

      <div className="main-content">
        {/* Sidebar Filters */}
        <div className="sidebar">
          {/* Config Section */}
          <div className="config-section">
            <h3>Config</h3>
            <button 
              className="config-btn"
              onClick={() => setShowCameraManager(true)}
            >
              📷 Cameras
            </button>
          </div>

          <h3>Filters</h3>

          {/* Camera Filter */}
          <div className="filter-section">
            <h4>Cameras</h4>
            {availableCameras.map(camera => (
              <label key={camera} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={filters.cameras.includes(camera)}
                  onChange={(e) => updateFilter('cameras', camera, e.target.checked)}
                />
                {camera}
              </label>
            ))}
          </div>

          {/* Time Range Filter */}
          <div className="filter-section">
            <h4>Time Range</h4>
            <select 
              value={filters.timeRange} 
              onChange={(e) => updateFilter('timeRange', e.target.value, true)}
            >
              <option value="1h">Last Hour</option>
              <option value="24h">Last 24 Hours</option>
              <option value="3d">Last 3 Days</option>
              <option value="7d">Last Week</option>
              <option value="30d">Last Month</option>
              <option value="all">All Time</option>
            </select>
          </div>

          {/* Confidence Filter */}
          <div className="filter-section">
            <h4>Confidence</h4>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={filters.confidenceLevels.includes('high')}
                onChange={(e) => updateFilter('confidenceLevels', 'high', e.target.checked)}
              />
              High (≥90%)
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={filters.confidenceLevels.includes('medium')}
                onChange={(e) => updateFilter('confidenceLevels', 'medium', e.target.checked)}
              />
              Medium (70-90%)
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={filters.confidenceLevels.includes('low')}
                onChange={(e) => updateFilter('confidenceLevels', 'low', e.target.checked)}
              />
              Low (&lt;70%)
            </label>
          </div>

          {/* Fog Level Filter */}
          <div className="filter-section">
            <h4>Fog Level</h4>
            {['Clear', 'Light Fog', 'Moderate Fog', 'Heavy Fog', 'Very Heavy Fog'].map(level => (
              <label key={level} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={filters.fogLevels.includes(level)}
                  onChange={(e) => updateFilter('fogLevels', level, e.target.checked)}
                />
                <span style={{ color: getFogLevelColor(level) }}>●</span> {level}
              </label>
            ))}
          </div>
        </div>

        {/* Image Grid */}
        <div className="image-grid-container">
          {images.length === 0 ? (
            <div className="no-images">No images found with current filters</div>
          ) : (
            <>
              <div className="image-grid">
                {images.map(image => (
                  <div 
                    key={image.id} 
                    className="image-card"
                    onClick={() => openImageDetails(image)}
                  >
                    <div className="image-thumbnail">
                      <img 
                        src={`${API_BASE}${image.image_url}`} 
                        alt={image.filename}
                        loading="lazy"
                      />
                    </div>
                    <div className="image-info">
                      <div className="camera-name">{image.webcam_info.name}</div>
                      <div className="timestamp">
                        {image.timestamp ? new Date(image.timestamp).toLocaleString() : 'Unknown'}
                      </div>
                      <div className="fog-score">
                        <span 
                          className="score-badge"
                          style={{ 
                            backgroundColor: getFogLevelColor(image.gemini_label.fog_level),
                            color: 'white'
                          }}
                        >
                          {Math.round(image.gemini_label.fog_score)}
                        </span>
                        <span className="fog-level">{image.gemini_label.fog_level}</span>
                      </div>
                      <div className="confidence">
                        <span 
                          style={{ color: getConfidenceColor(image.gemini_label.confidence) }}
                        >
                          {Math.round(image.gemini_label.confidence * 100)}% confident
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {hasMore && (
                <div className="load-more">
                  <button 
                    onClick={loadMore} 
                    disabled={loading}
                    className="load-more-btn"
                  >
                    {loading ? 'Loading...' : 'Load More Images'}
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Image Detail Modal */}
      {showModal && selectedImage && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="close-btn" onClick={closeModal}>×</button>
            
            <div className="modal-body">
              <div className="modal-image">
                <img 
                  src={`${API_BASE}${selectedImage.image_url}`} 
                  alt={selectedImage.filename}
                />
              </div>
              
              <div className="modal-details">
                <h3>{selectedImage.webcam_info.name}</h3>
                <p><strong>Collected:</strong> {selectedImage.timestamp ? new Date(selectedImage.timestamp).toLocaleString() : 'Unknown'}</p>
                
                <div className="analysis-section">
                  <h4>Gemini Analysis</h4>
                  <div className="analysis-grid">
                    <div>
                      <strong>Fog Score:</strong> 
                      <span 
                        style={{ 
                          color: getFogLevelColor(selectedImage.gemini_label.fog_level),
                          fontWeight: 'bold',
                          marginLeft: '5px'
                        }}
                      >
                        {selectedImage.gemini_label.fog_score.toFixed(1)}/100
                      </span>
                    </div>
                    <div>
                      <strong>Fog Level:</strong> 
                      <span 
                        style={{ 
                          color: getFogLevelColor(selectedImage.gemini_label.fog_level),
                          fontWeight: 'bold'
                        }}
                      >
                        {selectedImage.gemini_label.fog_level}
                      </span>
                    </div>
                    <div>
                      <strong>Confidence:</strong> 
                      <span style={{ color: getConfidenceColor(selectedImage.gemini_label.confidence) }}>
                        {(selectedImage.gemini_label.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  
                  {selectedImage.gemini_label.visibility_estimate && (
                    <div><strong>Visibility:</strong> {selectedImage.gemini_label.visibility_estimate}</div>
                  )}
                  
                  {selectedImage.gemini_label.reasoning && (
                    <div className="reasoning">
                      <strong>AI Reasoning:</strong>
                      <p>{selectedImage.gemini_label.reasoning}</p>
                    </div>
                  )}
                  
                  {selectedImage.gemini_label.weather_conditions && selectedImage.gemini_label.weather_conditions.length > 0 && (
                    <div className="weather-conditions">
                      <strong>Weather Conditions:</strong>
                      <ul>
                        {selectedImage.gemini_label.weather_conditions.map((condition, idx) => (
                          <li key={idx}>{condition}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Placeholder for future editing */}
                <div className="edit-section">
                  <button className="edit-btn" disabled title="Coming soon">
                    ✏️ Edit Labels (Coming Soon)
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Camera Manager Modal */}
      <CameraManager
        isOpen={showCameraManager}
        onClose={() => setShowCameraManager(false)}
        apiBase={API_BASE}
      />
    </div>
  );
};

export default App;