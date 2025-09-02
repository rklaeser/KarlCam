import React from 'react';

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
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={handleBackdropClick}
    >
      <div 
        className="bg-white rounded-lg max-w-4xl max-h-[90vh] overflow-y-auto shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-800">Fog Intensity Levels</h2>
          <button 
            className="w-8 h-8 flex items-center justify-center text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-full text-2xl font-light"
            onClick={onClose}
          >
            ×
          </button>
        </div>
        
        <div className="p-6">
          <p className="text-gray-600 text-lg mb-8 leading-relaxed">
            Our AI analyzes webcam images to determine fog intensity on a scale of 0-100. 
            Here are examples of each fog level:
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {fogLevels.map((level) => (
              <div key={level.level} className="border border-gray-200 rounded-lg overflow-hidden">
                <div className="p-4 bg-gray-50">
                  <div className="flex items-center gap-3 mb-2">
                    <div 
                      className="px-3 py-1 rounded-full text-white text-sm font-semibold"
                      style={{ backgroundColor: level.color }}
                    >
                      {level.range}
                    </div>
                    <h3 className="text-lg font-semibold text-gray-800">{level.level}</h3>
                  </div>
                </div>
                
                <div className="p-4">
                  <div className="aspect-video bg-gray-100 rounded-lg border-2 border-dashed flex flex-col items-center justify-center mb-4" style={{ borderColor: level.color }}>
                    <div className="text-4xl mb-2">🌫️</div>
                    <div className="text-center">
                      <div className="text-sm font-medium text-gray-600">Example Image</div>
                      <div className="text-xs text-gray-500">{level.level}</div>
                    </div>
                  </div>
                  
                  <p className="text-sm text-gray-600 leading-relaxed">{level.description}</p>
                </div>
              </div>
            ))}
          </div>
          
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-gray-700 leading-relaxed">
              <strong>Note:</strong> Fog scores are determined by analyzing visual features 
              including visibility, contrast, and atmospheric conditions. Weather conditions 
              and time of day can affect accuracy.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FogIntensityModal;