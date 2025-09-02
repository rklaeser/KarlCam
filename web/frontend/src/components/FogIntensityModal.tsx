import React from 'react';
import './FogIntensityModal.css';

interface FogIntensityModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const FogIntensityModal: React.FC<FogIntensityModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  const fogLevels = [
    {
      level: 'Clear',
      range: '0-20',
      color: '#28a745',
      description: 'No fog visible, clear visibility',
      exampleImage: '/images/fog-clear.jpg'
    },
    {
      level: 'Light Fog',
      range: '20-40',
      color: '#ffc107',
      description: 'Slight haze, visibility slightly reduced',
      exampleImage: '/images/fog-light.jpg'
    },
    {
      level: 'Moderate Fog',
      range: '40-60',
      color: '#fd7e14',
      description: 'Noticeable fog, landmarks partially obscured',
      exampleImage: '/images/fog-moderate.jpg'
    },
    {
      level: 'Heavy Fog',
      range: '60-80',
      color: '#dc3545',
      description: 'Dense fog, visibility significantly reduced',
      exampleImage: '/images/fog-heavy.jpg'
    },
    {
      level: 'Very Heavy Fog',
      range: '80+',
      color: '#6f42c1',
      description: 'Extremely dense fog, minimal visibility',
      exampleImage: '/images/fog-very-heavy.jpg'
    }
  ];

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="modal-wrapper" onClick={handleBackdropClick}>
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        <div className="modal-content">
          <div className="modal-header">
            <h2>Fog Intensity Levels</h2>
            <button className="modal-close" onClick={onClose}>×</button>
          </div>
          
          <div className="modal-body">
            <p className="modal-description">
              Our AI analyzes webcam images to determine fog intensity on a scale of 0-100. 
              Here are examples of each fog level:
            </p>
            
            <div className="intensity-examples">
              {fogLevels.map((level) => (
                <div key={level.level} className="intensity-card">
                  <div className="intensity-header">
                    <div className="intensity-badge" style={{ backgroundColor: level.color }}>
                      {level.range}
                    </div>
                    <h3>{level.level}</h3>
                  </div>
                  
                  <div className="intensity-image-placeholder">
                    <div className="placeholder-content" style={{ borderColor: level.color }}>
                      <div className="placeholder-icon">🌫️</div>
                      <div className="placeholder-text">
                        Example Image
                        <span className="placeholder-note">{level.level}</span>
                      </div>
                    </div>
                  </div>
                  
                  <p className="intensity-description">{level.description}</p>
                </div>
              ))}
            </div>
            
            <div className="modal-footer-note">
              <p>
                <strong>Note:</strong> Fog scores are determined by analyzing visual features 
                including visibility, contrast, and atmospheric conditions. Weather conditions 
                and time of day can affect accuracy.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FogIntensityModal;