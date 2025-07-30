import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

interface ImageInfo {
  filename: string;
  labeled: boolean;
  url: string;
  current_label?: string;
  confidence?: number;
  clip_prediction?: string;
  clip_score?: number;
}

interface CLIPAnalysis {
  fog_score: number;
  fog_level: string;
  confidence: number;
  top_prediction: string;
  all_predictions: Array<{ label: string; score: number }>;
}

interface PredictionResult {
  clip_analysis: CLIPAnalysis;
  weather_analysis: any;
  suggested_label: string;
}

interface Stats {
  total_labeled: number;
  fog_count: number;
  clear_count: number;
  fog_percentage?: number;
  clip_agreement_rate?: number;
}

const App: React.FC = () => {
  const [images, setImages] = useState<ImageInfo[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [predicting, setPredicting] = useState(false);
  const [prediction, setPrediction] = useState<PredictionResult | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [message, setMessage] = useState('');

  const API_BASE = process.env.NODE_ENV === 'production' ? '' : 'http://localhost:8000';

  useEffect(() => {
    loadImages();
    loadStats();
  }, []);

  const loadImages = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/images`);
      setImages(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error loading images:', error);
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const getCurrentImage = (): ImageInfo | null => {
    return images.length > 0 ? images[currentIndex] : null;
  };

  const getPrediction = async (filename: string) => {
    setPredicting(true);
    try {
      const response = await axios.get(`${API_BASE}/api/predict/${filename}`);
      setPrediction(response.data);
    } catch (error) {
      console.error('Error getting prediction:', error);
      setMessage('Error getting CLIP prediction');
    } finally {
      setPredicting(false);
    }
  };

  const saveLabel = async (label: string) => {
    const currentImage = getCurrentImage();
    if (!currentImage) return;

    try {
      await axios.post(`${API_BASE}/api/label`, {
        filename: currentImage.filename,
        label: label,
        confidence: 1.0,
        clip_prediction: prediction?.clip_analysis.top_prediction,
        clip_score: prediction?.clip_analysis.fog_score
      });

      // Update local state
      const updatedImages = [...images];
      updatedImages[currentIndex] = {
        ...currentImage,
        labeled: true,
        current_label: label
      };
      setImages(updatedImages);

      setMessage(`Labeled as ${label}`);
      loadStats(); // Refresh stats

      // Move to next image
      if (currentIndex < images.length - 1) {
        setCurrentIndex(currentIndex + 1);
        setPrediction(null);
      }
    } catch (error) {
      console.error('Error saving label:', error);
      setMessage('Error saving label');
    }
  };

  const exportData = async () => {
    try {
      setMessage('Exporting data...');
      await axios.post(`${API_BASE}/api/export`);
      setMessage('Data exported successfully!');
    } catch (error) {
      console.error('Error exporting data:', error);
      setMessage('Error exporting data');
    }
  };

  const nextImage = () => {
    if (currentIndex < images.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setPrediction(null);
    }
  };

  const prevImage = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
      setPrediction(null);
    }
  };

  const currentImage = getCurrentImage();

  if (loading) {
    return <div className="loading">Loading images...</div>;
  }

  if (images.length === 0) {
    return <div className="no-images">No images found to label</div>;
  }

  return (
    <div className="app">
      <header className="header">
        <h1>FogCam Image Labeling</h1>
        {stats && (
          <div className="stats">
            <span>Labeled: {stats.total_labeled}</span>
            <span>Fog: {stats.fog_count}</span>
            <span>Clear: {stats.clear_count}</span>
            {stats.fog_percentage && <span>Fog Rate: {stats.fog_percentage}%</span>}
          </div>
        )}
      </header>

      <div className="main-content">
        <div className="image-section">
          <div className="image-header">
            <h2>{currentImage?.filename}</h2>
            <div className="progress">
              {currentIndex + 1} / {images.length}
            </div>
          </div>

          <div className="image-container">
            {currentImage && (
              <img
                src={`${API_BASE}${currentImage.url}`}
                alt={currentImage.filename}
                className="main-image"
              />
            )}
          </div>

          <div className="navigation">
            <button onClick={prevImage} disabled={currentIndex === 0}>
              Previous
            </button>
            <button onClick={nextImage} disabled={currentIndex === images.length - 1}>
              Next
            </button>
          </div>
        </div>

        <div className="control-section">
          <div className="current-status">
            {currentImage?.labeled ? (
              <div className="labeled">
                ✅ Labeled as: <strong>{currentImage.current_label}</strong>
              </div>
            ) : (
              <div className="unlabeled">❌ Not labeled</div>
            )}
          </div>

          <div className="prediction-section">
            <button
              onClick={() => currentImage && getPrediction(currentImage.filename)}
              disabled={predicting}
              className="predict-btn"
            >
              {predicting ? 'Getting CLIP Prediction...' : 'Get CLIP Prediction'}
            </button>

            {prediction && (
              <div className="prediction-results">
                <h3>CLIP Analysis</h3>
                <div className="clip-result">
                  <div><strong>Fog Score:</strong> {prediction.clip_analysis.fog_score}</div>
                  <div><strong>Level:</strong> {prediction.clip_analysis.fog_level}</div>
                  <div><strong>Top Prediction:</strong> {prediction.clip_analysis.top_prediction}</div>
                  <div><strong>Suggested Label:</strong> {prediction.suggested_label}</div>
                </div>

                <div className="top-predictions">
                  <h4>Top Predictions:</h4>
                  {prediction.clip_analysis.all_predictions.slice(0, 3).map((pred, idx) => (
                    <div key={idx} className="prediction-item">
                      {pred.label}: {pred.score}%
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="labeling-section">
            <h3>Label this image:</h3>
            <div className="label-buttons">
              <button
                onClick={() => saveLabel('fog')}
                className="label-btn fog-btn"
              >
                🌫️ Fog
              </button>
              <button
                onClick={() => saveLabel('clear')}
                className="label-btn clear-btn"
              >
                ☀️ Clear
              </button>
            </div>
          </div>

          <div className="export-section">
            <button onClick={exportData} className="export-btn">
              Export Labeled Data
            </button>
          </div>

          {message && (
            <div className="message">
              {message}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default App;