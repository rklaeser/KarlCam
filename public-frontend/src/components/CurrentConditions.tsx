import React from 'react';

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

interface CurrentConditionsProps {
  conditions: CurrentConditionsData | null;
  loading: boolean;
}

const CurrentConditions: React.FC<CurrentConditionsProps> = ({ conditions, loading }) => {
  if (loading) {
    return (
      <div className="current-conditions loading">
        <h2>Current Conditions</h2>
        <div className="loading-placeholder">
          <div className="skeleton-text"></div>
          <div className="skeleton-text"></div>
          <div className="skeleton-text"></div>
        </div>
      </div>
    );
  }

  if (!conditions) {
    return (
      <div className="current-conditions error">
        <h2>Current Conditions</h2>
        <p>Unable to load current fog conditions</p>
      </div>
    );
  }

  const getFogEmoji = (fogLevel: string): string => {
    switch (fogLevel.toLowerCase()) {
      case 'clear': return '☀️';
      case 'light fog': return '🌤️';
      case 'moderate fog': return '🌫️';
      case 'heavy fog': return '🌁';
      case 'very heavy fog': return '🌁';
      default: return '❓';
    }
  };

  const getFogDescription = (fogLevel: string, fogScore: number): string => {
    if (fogScore < 20) {
      return 'Crystal clear visibility with blue skies';
    } else if (fogScore < 40) {
      return 'Light haze or mist in the air';
    } else if (fogScore < 60) {
      return 'Moderate fog reducing visibility';
    } else if (fogScore < 80) {
      return 'Heavy fog with limited visibility';
    } else {
      return 'Very dense fog, visibility severely limited';
    }
  };

  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 80) return '#28a745'; // Green
    if (confidence >= 60) return '#ffc107'; // Yellow
    return '#dc3545'; // Red
  };

  return (
    <div className="current-conditions">
      <h2>Current Conditions</h2>
      
      <div className="condition-card">
        <div className="fog-status">
          <div className="fog-emoji">
            {getFogEmoji(conditions.fog_level)}
          </div>
          <div className="fog-info">
            <h3>{conditions.fog_level}</h3>
            <p className="fog-description">
              {getFogDescription(conditions.fog_level, conditions.fog_score)}
            </p>
          </div>
        </div>

        <div className="metrics">
          <div className="metric">
            <div className="metric-label">Fog Score</div>
            <div className="metric-value">
              <span className="score">{conditions.fog_score.toFixed(1)}</span>
              <span className="score-max">/100</span>
            </div>
            <div className="score-bar">
              <div 
                className="score-fill" 
                style={{ 
                  width: `${conditions.fog_score}%`,
                  backgroundColor: conditions.fog_score > 50 ? '#dc3545' : '#28a745'
                }}
              ></div>
            </div>
          </div>

          <div className="metric">
            <div className="metric-label">AI Confidence</div>
            <div className="metric-value">
              <span 
                className="confidence"
                style={{ color: getConfidenceColor(conditions.confidence) }}
              >
                {conditions.confidence.toFixed(1)}%
              </span>
            </div>
          </div>

          <div className="metric">
            <div className="metric-label">Weather Analysis</div>
            <div className="metric-value">
              <span className={`weather-status ${conditions.weather_detected ? 'fog-detected' : 'clear-detected'}`}>
                {conditions.weather_detected ? '🌫️ Fog Detected' : '☀️ Clear Skies'}
              </span>
            </div>
            <div className="weather-confidence">
              {conditions.weather_confidence.toFixed(1)}% confident
            </div>
          </div>
        </div>

        <div className="location-info">
          <div className="location">
            📍 {conditions.location.name}
          </div>
          <div className="timestamp">
            🕐 {formatTimestamp(conditions.timestamp)}
          </div>
        </div>
      </div>

      <div className="analysis-note">
        <p>
          <strong>How it works:</strong> AI analyzes the live webcam image using CLIP 
          (Contrastive Language-Image Pre-training) to detect fog conditions in real-time.
        </p>
      </div>
    </div>
  );
};

export default CurrentConditions;