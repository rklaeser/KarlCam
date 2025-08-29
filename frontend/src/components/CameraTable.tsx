import React from 'react';

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

interface CameraTableProps {
  cameras: CameraConditions[];
  loading: boolean;
}

const CameraTable: React.FC<CameraTableProps> = ({ cameras, loading }) => {
  if (loading) {
    return (
      <div className="camera-table loading">
        <div className="loading-placeholder">
          <div className="skeleton-text"></div>
          <div className="skeleton-text"></div>
          <div className="skeleton-text"></div>
        </div>
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

  const getFogDescription = (fogScore: number): string => {
    const score = fogScore || 0;
    if (score < 20) {
      return 'Crystal clear visibility with blue skies';
    } else if (score < 40) {
      return 'Light haze or mist in the air';
    } else if (score < 60) {
      return 'Moderate fog reducing visibility';
    } else if (score < 80) {
      return 'Heavy fog with limited visibility';
    } else {
      return 'Very dense fog, visibility severely limited';
    }
  };

  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 80) return '#28a745'; // Green
    if (confidence >= 60) return '#ffc107'; // Yellow
    return '#dc3545'; // Red
  };

  return (
    <div className="camera-table">
      <div className="table-container">
        <table className="cameras-table">
          <thead>
            <tr>
              <th>Camera</th>
              <th>Conditions</th>
              <th>Fog Score</th>
              <th>AI Confidence</th>
              <th>Last Updated</th>
            </tr>
          </thead>
          <tbody>
            {cameras.map((camera) => (
              <tr key={camera.id} className={`camera-row ${!camera.active ? 'inactive' : ''}`}>
                <td className="camera-info">
                  <div className="camera-name">
                    📹 {camera.name}
                  </div>
                  <div className="camera-location">
                    📍 {camera.lat?.toFixed(3) || '0.000'}, {camera.lon?.toFixed(3) || '0.000'}
                  </div>
                </td>
                
                <td className="fog-status">
                  <div className="fog-display">
                    <div className="fog-emoji">
                      {getFogEmoji(camera.fog_level)}
                    </div>
                    <div className="fog-details">
                      <div className="fog-level">{camera.fog_level}</div>
                      <div className="fog-description">
                        {getFogDescription(camera.fog_score)}
                      </div>
                    </div>
                  </div>
                </td>
                
                <td className="fog-score">
                  <div className="metric-value">
                    <span className="score">{camera.fog_score?.toFixed(1) || '0.0'}</span>
                    <span className="score-max">/100</span>
                  </div>
                  <div className="score-bar">
                    <div 
                      className="score-fill" 
                      style={{ 
                        width: `${camera.fog_score || 0}%`,
                        backgroundColor: (camera.fog_score || 0) > 50 ? '#dc3545' : '#28a745'
                      }}
                    ></div>
                  </div>
                </td>
                
                <td className="ai-confidence">
                  <span 
                    className="confidence"
                    style={{ color: getConfidenceColor(camera.confidence || 0) }}
                  >
                    {camera.confidence?.toFixed(1) || '0.0'}%
                  </span>
                </td>
                
                
                <td className="timestamp">
                  🕐 {formatTimestamp(camera.timestamp)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {cameras.length === 0 && (
        <div className="no-data">
          <p>No camera data available.</p>
          <p>Cameras will appear as data becomes available.</p>
        </div>
      )}

    </div>
  );
};

export default CameraTable;